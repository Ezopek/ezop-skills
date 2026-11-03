#!/usr/bin/env python3
"""Offline structural checks for the skill packages in this repository.

Standard library only; reads files, never executes them, never uses the network.
Symlinks (file or directory, live or broken, inside or outside the root) are
unsupported: they are reported as UNSUPPORTED_SYMLINK (name only, never the
target) before any file content, root document or skill folder is read, and no
other check runs until they are removed; nothing outside the root is scanned.
Checks per top-level folder that contains SKILL.md:

* frontmatter: a small YAML subset (name, description, optional license,
  compatibility, allowed-tools, string-valued one-level metadata), name rules;
* links and file references resolve inside the package (markdown links,
  `references/...`-style paths, bare `*.md` names), no cross-package paths;
* dependency closure: every shipped file is reachable from SKILL.md;
* public-data boundary: generic checks for private home paths, private network
  addresses (IPv4 private ranges, and IPv6 unique-local addresses, i.e. prefix
  length 7 with first byte fc or fd, and link-local addresses, i.e. prefix length
  10 starting fe80; loopback, documentation and public IPv6 are not flagged),
  marketplace product IDs, secrets (a heuristic for a few common shapes such
  as sk-, GitHub gh*_ and github_pat_ tokens, AWS key ids and private-key
  headers; never a complete credential detector) and e-mail addresses, applied to
  EVERY file in the tree (except .git and bytecode caches), including this
  checker, the tests and any retained licence text. There is no vendor
  exemption and no suffix whitelist: a file is scanned if it is valid UTF-8
  text without NUL bytes; any other file is reported as UNSCANNED_BINARY
  instead of being silently skipped;
* optionally, organisation-specific terms supplied by the caller with
  --deny-file (one term per line, whole-word, '#' comments). No such term is
  built in, so none can leak from this file;
* findings give the path, a code and a line number only: matched secrets,
  private values and deny terms are never echoed;
* README.md and INSTALLATION.md mention every skill, and their local Markdown links
  resolve to existing regular files INSIDE the supplied root (or to a skill folder,
  a directory holding SKILL.md, which is what the shipped README links to; any other
  directory is not a file). External URLs are never fetched;
* Python files parse (syntax only; this is not a behaviour test);
* optionally, --vendor-manifest names caller-declared upstream provenance
  entries under skill-creator/ (path -> sha256): each must be present and
  byte-identical. The manifest only adds checks; it exempts nothing from the
  scans above. A closed release inventory and source review establish shipping
  completeness; this checker cannot infer a file's origin from its name.

The tests build their synthetic leak samples at run time, so the scanned source
stays clean; a visibly synthetic false positive would be reported, not silently
skipped.

This is a format and structure check. It does not show that any client loads a
skill or that a skill changes behaviour.

Usage: python3 -B scripts/check_skills.py [ROOT] [--vendor-manifest FILE] [--deny-file FILE]
Exit status: 0 no findings, 1 findings, 2 usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKIP_DIRS = {".git"}
ORPHAN_OK = {"LICENSE.txt"}  # a retained licence text is shipped, not linked
# Names of files that references describe as outputs of a procedure, not shipped files.
OUTPUT_NAMES = {"report.md", "print-feedback.md", "notes.md", "REPORT.md", "PROGRESS.md", "README.md"}

class _PrivateIPv6:
    """Finds IPv6 unique-local and link-local addresses; same search() contract as a compiled regex.

    A loose candidate pattern proposes colon-separated hex runs and ipaddress validates each one, so
    times, MAC addresses, code like a scope operator and other arbitrary colons are not flagged, and
    neither are loopback, documentation or public addresses. The prefix tests use bit shifts so this
    source holds no address-like literal of its own.
    """

    _CANDIDATE = re.compile(r"(?<![0-9A-Fa-f:.])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])")

    @staticmethod
    def _private(text: str) -> bool:
        try:
            value = int(ipaddress.IPv6Address(text))
        except ValueError:
            return False
        return value >> 121 == 0x7E or value >> 118 == 0x3FA  # 7-bit unique-local, 10-bit link-local prefixes

    def search(self, text: str):
        for m in self._CANDIDATE.finditer(text):
            token = m.group(0)
            trimmed = token[:-1] if token.endswith(":") and not token.endswith("::") else None  # "addr: next"
            if self._private(token) or (trimmed and self._private(trimmed)):
                return m
        return None


class _PrivateIPv4:
    """Finds IPv4 addresses in the three RFC1918 ranges; same search() contract as a compiled regex.

    A candidate is a COMPLETE dotted-decimal atom: a maximal run of ASCII digits and dots that is not glued to a word character or to a
    longer dotted atom on either side. It must have exactly four components and pass the stdlib ``ipaddress`` validation (so octets above
    255, leading zeros and other malformed counts are rejected, not normalised) before the range test. Only the three RFC1918 ranges are
    reported: documentation, reserved, loopback, link-local and shared-address ranges stay allowed, which ``is_private`` would not do.
    The prefix tests use bit shifts so this source holds no address-like literal of its own.
    """

    _ATOM = re.compile(r"(?<![\w.])[0-9][0-9.]*")  # the whole maximal run of digits and dots: repeated dots stay inside the atom

    @staticmethod
    def _private(token: str) -> bool:
        if token.count(".") != 3:
            return False
        try:
            value = int(ipaddress.IPv4Address(token))
        except ValueError:
            return False
        return value >> 24 == 0xA or value >> 20 == 0xAC1 or value >> 16 == 0xC0A8  # 8-, 12- and 16-bit private prefixes

    def search(self, text: str):
        for m in self._ATOM.finditer(text):
            atom = m.group(0)
            core = atom[:-1] if atom.endswith(".") and not atom.endswith("..") else atom  # exactly ONE trailing period is sentence punctuation
            following = text[m.end() : m.end() + 1]
            if following and re.match(r"\w", following):  # glued to a word character, also after a single period (addr.word): not a whole atom
                continue
            if self._private(core):  # a repeated or dot-led remainder (addr..2, addr..) makes the whole atom malformed, never a shorter prefix
                return m if core == atom else self._ATOM.match(text, m.start(), m.start() + len(core))  # the span excludes a sentence period
        return None


PRIVACY = [
    # Standard home directories: a COMPLETE nonempty user component under the literal, case-sensitive POSIX and macOS prefixes. Its first
    # character may be anything except whitespace, a path separator or a placeholder/terminator introducer (< > { } ( ) [ ] $ % ~ * ? ! , ; : ' " ` | & = + @ # ^),
    # so accented, non-Latin, combining-leading, hyphen-led, digit, underscore and hidden names are all covered without an enumerated
    # alphabet; a dot-only component and a complete placeholder such as <user>, $USER or {user} stay clean. No account lookup. Then the
    # conventional privileged home and the Windows Users directory. Written with groups so this pattern source cannot match itself.
    ("PRIVATE_PATH", re.compile(
        r"(?:/(?:home|Users)/(?!\.+(?:[/\s]|$))[^\s/\\<>{}()\[\]$%~*?!,;:'\"`|&=+@#^]"
        r"|(?<![\w/.-])/(?:r)oot(?![\w-])"
        r"|[A-Za-z]:[\\/](?i:Users)[\\/])"  # drive-qualified: `Users` in any letter case (scoped flag, not global), either slash spelling
    )),
    ("PRIVATE_IP", _PrivateIPv4()),
    ("PRIVATE_IP", _PrivateIPv6()),
    ("PRODUCT_ID", re.compile(r"\bB0[0-9A-Z]{8}\b")),
    ("SECRET", re.compile(r"(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY)")),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z][\w.-]*")),
]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
# A link target is EXTERNAL (never resolved, probed, fetched or rewritten) when it starts with a URI scheme (case-insensitive, RFC 3986
# section 3.1) or is a network-path reference beginning with two slashes (section 4.2). One leading slash is an absolute LOCAL path.
EXTERNAL_RE = re.compile(r"(?:[a-z][a-z0-9+.-]*:|//)", re.I)
PREFIXED_RE = re.compile(r"(?<![\w/.<-])((?:\.\./|\./)*(?:references|scripts|templates|assets|agents|eval-viewer)/[A-Za-z0-9_./-]+\.(?:md|py|json|html|txt))")
BARE_MD_RE = re.compile(r"`([A-Za-z0-9_-]+\.md)`")


def parse_frontmatter(text: str):
    """Return (dict, error). Supports flat keys and one-level string metadata."""
    lines = text.split("\n")
    # Structure is ASCII-only: delimiters, blank lines and comments are separated by space, tab and the CR of CRLF.
    # Unicode whitespace (for example NBSP) is never structure; it stays part of a value or is refused below.
    if not lines or lines[0].strip(" \t\r") != "---":
        return None, "no frontmatter (file must start with ---)"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip(" \t\r") == "---")
    except StopIteration:
        return None, "frontmatter is not closed"
    data: dict = {}
    current = None
    nested_indent = None  # width of the first nested line under `current`; every nested line must match it
    for raw in lines[1:end]:
        if raw.endswith("\r"):  # CRLF files: drop the one line-ending carriage return, nothing else
            raw = raw[:-1]
        if not raw.strip(" \t") or raw.lstrip(" \t").startswith("#"):  # ASCII blank / comment lines only
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            return None, "tab indentation is not supported"
        if lead.strip(" "):
            return None, "indentation must use ASCII spaces only (other whitespace characters are not reinterpreted)"
        indented = bool(lead)
        # Only ASCII space and tab separate tokens; other Unicode whitespace is part of a value, never trimmed.
        m = re.match(r"^ *([A-Za-z0-9_-]+):[ \t]*(.*)$", raw)
        if not m:
            return None, f"unsupported frontmatter line: {raw!r}"
        key, value = m.group(1), m.group(2).strip(" \t")
        if indented:
            if current is None or not isinstance(data.get(current), dict):
                return None, f"unexpected indentation: {raw!r}"
            if nested_indent is None:
                nested_indent = len(lead)
            elif len(lead) > nested_indent:
                return None, f"deeper indentation under {current}: nested mappings are not supported (one level of string values only)"
            elif len(lead) < nested_indent:
                return None, f"inconsistent indentation under {current}"
            val, err = _scalar(value)
            if err:
                return None, f"metadata.{key}: {err}"
            if key in data[current]:
                return None, f"duplicate key {current}.{key}"
            data[current][key] = val
        else:
            if key in data:
                return None, f"duplicate key {key}"
            nested_indent = None
            if value == "":
                if key != "metadata":
                    # YAML reads an empty value as null; the only mapping form in this subset is metadata's one-level strings.
                    return None, f"{key}: empty value is not supported (YAML reads it as null); quote \"\" for an empty string or remove the key"
                data[key] = {}
                current = key
            else:
                val, err = _scalar(value)
                if err:
                    return None, f"{key}: {err}"
                data[key] = val
                current = None
    for key, val in data.items():
        if isinstance(val, dict) and not val:
            return None, f"{key} has no child fields (YAML reads it as null, not an empty mapping); add one-level string entries or remove the key"
    return data, None


# Bare (unquoted) words and numbers that a YAML consumer reads as bool, null, number or date rather than a string.
_BARE_WORDS = {"true", "false", "yes", "no", "on", "off", "y", "n", "null", "~"}  # y/n: YAML 1.1 booleans some clients read
_TYPED_BARE = re.compile(
    r"""^(?:
        [-+]?(?:\d[\d_]*\.?\d*|\.\d+)(?:[eE][-+]?\d+)?   # integer / float (incl. legacy octal, underscores)
      | [-+]?0[xX][0-9a-fA-F_]+ | [-+]?0[oO][0-7_]+ | [-+]?0[bB][01_]+   # based integers, optionally signed
      | [-+]?\d+(?::[0-5]?\d)+(?:\.\d*)?                 # sexagesimal
      | [-+]?\.(?:inf|Inf|INF|nan|NaN|NAN)               # infinity / not-a-number
      | \d{4}-\d{1,2}-\d{1,2}(?:[Tt\s].*)?               # timestamp
    )$""",
    re.X,
)


def _quoted(value: str):
    """Decode one quoted scalar. Double quotes: only \\" and \\\\ may be escaped. Single quotes: '' is a quote."""
    q, out, i = value[0], [], 1
    while i < len(value):
        ch = value[i]
        if q == '"' and ch == "\\":
            if value[i + 1 : i + 2] not in ('"', "\\"):
                return None, "unsupported escape in a double-quoted value (only a quote and a backslash can be escaped); use a plain or single-quoted value"
            out.append(value[i + 1])
            i += 2
        elif ch == q:
            if q == "'" and value[i + 1 : i + 2] == "'":
                out.append("'")
                i += 2
                continue
            if value[i + 1 :].strip(" \t"):
                return None, "text or a comment after the closing quote is not supported; quote the whole value"
            return "".join(out), None
        else:
            out.append(ch)
            i += 1
    return None, "unterminated quote"


def _scalar(value: str):
    """One string value of the supported subset, or (None, reason).

    Plain values that YAML would read differently (another type, a comment, a mapping, an alias, an
    anchor, a tag) are refused with a request to quote them, instead of being passed through as text.
    """
    if value == "":
        return None, "empty value (nested mappings are not supported)"
    if value[0] in "|>":
        return None, "block scalars are not supported"
    if value[0] in "[{":
        return None, "lists and maps are not supported (values must be strings)"
    if value[0] in "\"'":
        return _quoted(value)
    # YAML separation whitespace is space OR tab, so every ambiguity test below treats both alike.
    if value[0] in ",]}#&*!%@`" or re.match(r"[-?:](?:[ \t]|$)", value):
        return None, "starts with a YAML indicator (comment, alias, anchor, tag or reserved character); quote the value"
    if re.search(r"[ \t]#", value):
        return None, "contains whitespace followed by '#', which YAML reads as the start of a comment; quote the value"
    if re.search(r":(?:[ \t]|$)", value):
        return None, "contains a colon followed by whitespace or at the end, which is YAML mapping syntax; quote the value"
    if value.lower() in _BARE_WORDS or _TYPED_BARE.match(value):
        return None, "a bare value like this reads as a YAML boolean, null, number or date, not a string; quote the value"
    return value, None


def _files(pkg: Path):
    for p in sorted(pkg.rglob("*")):
        if p.is_file() and not (set(p.relative_to(pkg).parts) & SKIP_DIRS):
            yield p


def _refs(text: str, file_dir: Path, pkg: Path):
    """Yield (token, kind) for file references found in text."""
    for m in LINK_RE.finditer(text):
        t = m.group(1).split("#", 1)[0].split("?", 1)[0]
        if t and not EXTERNAL_RE.match(t):
            yield t, "link"
    for m in PREFIXED_RE.finditer(text):
        yield m.group(1), "path"
    for m in BARE_MD_RE.finditer(text):
        if m.group(1) not in OUTPUT_NAMES:
            yield m.group(1), "bare"


def _inside(candidate: Path, boundary: Path) -> bool:
    try:
        candidate.relative_to(boundary)
        return True
    except ValueError:
        return False


def _resolve(token: str, kind: str, file_dir: Path, pkg: Path, boundary: Path, files_only: bool = False):
    """Return ("ok", resolved path), ("missing", None) or ("escapes", None) for one reference token.

    Containment is decided on the NORMALISED candidate (pure path arithmetic, no filesystem access) BEFORE anything is probed: an
    explicit path whose document-relative form leaves ``boundary`` is "escapes" whether or not the target exists, is never stat'ed,
    and is never re-rooted onto another base. Fallback bases are only probed when their candidate is inside the boundary. The tree
    holds no symlinks (the early gate refuses them) and ``boundary`` is already resolved, so lexical containment is exact."""
    bases = [file_dir] if kind == "link" else [file_dir, pkg, pkg / "references"]
    for index, base in enumerate(bases):
        candidate = Path(os.path.normpath(base / token))
        if not _inside(candidate, boundary):
            if index == 0:
                return "escapes", None
            continue
        # files_only (root documents): an existing REGULAR file, or a skill folder (a directory holding SKILL.md); any other directory is
        # not a file. Package references keep the older "exists" meaning.
        found = (candidate.is_file() or (candidate.is_dir() and (candidate / "SKILL.md").is_file())) if files_only else candidate.exists()
        if found:
            return "ok", candidate.resolve()
    return "missing", None


def _symlinks(root: Path):
    """Relative paths of every symlink (file or directory, live or broken) under root, found without
    following any link or reading any file; .git is skipped by name like everywhere else."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                found.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return sorted(found)


def check(root, vendor_manifest=None, deny_terms=None):
    supplied = Path(root)  # not resolved yet: resolve() would follow a root alias before the gate below can see it
    deny = [_deny_regex(t) for t in (deny_terms or []) if t.strip()]
    findings: list[tuple[str, str, str]] = []

    def safe_detail(value):
        text = str(value)
        # Structural/parser errors can echo candidate values too, not only
        # privacy findings. Withhold the whole detail instead of partially
        # replacing a detector's prefix match (for example a home path).
        if any(rx.search(text) for _, rx in PRIVACY) or any(rx.search(text) for _, rx in deny):
            return "[REDACTED]"
        return text

    def add(path, code, msg):
        findings.append((safe_detail(path), code, safe_detail(msg)))

    # Early gate: symlinks are unsupported. Report them (names only, never targets) and stop before any
    # file content, root document or skill folder is read, so nothing outside the caller's root is scanned.
    # The supplied root LEAF is checked first, before resolve(); aliased ancestors of the root are allowed.
    if supplied.is_symlink():
        add(".", "UNSUPPORTED_SYMLINK", "the supplied root is itself a symlink (live or broken); it was not resolved, followed or read")
        return findings
    root = supplied.resolve()
    links = _symlinks(root)
    if links:
        for rel in links:
            add(rel, "UNSUPPORTED_SYMLINK", "symlinks (file or directory, live or broken) are not supported in the source tree; it was not followed or read")
        return findings

    skills = sorted(p.parent for p in root.glob("*/SKILL.md"))
    names = [s.name for s in skills]
    if not skills:
        add(".", "NO_SKILLS", "no top-level folder with SKILL.md found")
    for doc in ("README.md", "INSTALLATION.md"):
        if not (root / doc).is_file():
            add(doc, "MISSING_DOC", "file not found")
            continue
        text = _utf8_text(root / doc)
        if text is None:
            # Undecodable data is never replaced and treated as scanned: the privacy pass below reports this file as
            # UNSCANNED_BINARY (once), and the structural checks that need its text are skipped.
            continue
        for n in names:
            if n not in text:
                add(doc, "SKILL_NOT_LISTED", f"does not mention skill {n}")
        for token, kind in _refs(text, root, root):
            if kind != "link":
                continue
            status, _target = _resolve(token, kind, root, root, root, files_only=True)  # `root` is already resolved
            if status == "escapes":
                add(doc, "ESCAPES_ROOT", "a local link resolves outside the supplied root (the target is not echoed)")
            elif status == "missing":
                add(doc, "BROKEN_LINK", token)

    for pkg in skills:
        rel_pkg = pkg.name
        skill_md = pkg / "SKILL.md"
        fm, err = parse_frontmatter(skill_md.read_text(encoding="utf8", errors="replace"))
        if err:
            add(f"{rel_pkg}/SKILL.md", "FRONTMATTER", err)
        else:
            extra = set(fm) - ALLOWED_KEYS
            if extra:
                add(f"{rel_pkg}/SKILL.md", "FRONTMATTER", f"unsupported top-level keys: {sorted(extra)}")
            name = fm.get("name")
            if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
                add(f"{rel_pkg}/SKILL.md", "NAME", f"invalid name {name!r}")
            elif name != pkg.name:
                add(f"{rel_pkg}/SKILL.md", "NAME", f"name {name!r} does not match folder {pkg.name!r}")
            desc = fm.get("description")
            if not isinstance(desc, str) or not desc.strip():
                add(f"{rel_pkg}/SKILL.md", "DESCRIPTION", "missing or empty")
            elif len(desc) > 1024:
                add(f"{rel_pkg}/SKILL.md", "DESCRIPTION", "longer than 1024 characters")
            comp = fm.get("compatibility")
            if comp is not None and (not isinstance(comp, str) or len(comp) > 500):
                add(f"{rel_pkg}/SKILL.md", "COMPATIBILITY", "must be a string of at most 500 characters")
            for key in ("license", "allowed-tools"):
                if key in fm and not isinstance(fm[key], str):
                    add(f"{rel_pkg}/SKILL.md", "FRONTMATTER", f"{key} must be a string")
            if "metadata" in fm and not isinstance(fm["metadata"], dict):
                add(f"{rel_pkg}/SKILL.md", "FRONTMATTER", "metadata must be a mapping of strings")

        files = list(_files(pkg))
        reached = {skill_md.resolve()}
        queue = [skill_md]
        all_files = {p.resolve(): p for p in files}
        while queue:
            f = queue.pop()
            rel = f"{rel_pkg}/{f.relative_to(pkg).as_posix()}"
            if f.suffix != ".md":
                continue
            text = f.read_text(encoding="utf8", errors="replace")
            for token, kind in _refs(text, f.parent, pkg):
                status, target = _resolve(token, kind, f.parent, pkg, pkg)  # `pkg` comes from the resolved root
                if status == "escapes":
                    add(rel, "ESCAPES_PACKAGE", "a reference resolves outside the package (the target is not echoed)")
                    continue
                if status == "missing":
                    add(rel, "MISSING_REF", token)
                    continue
                if target.is_file() and target not in reached:
                    reached.add(target)
                    queue.append(target)
            for other in names:
                if other != pkg.name and re.search(rf"(?<![\w/.-]){re.escape(other)}/[A-Za-z0-9_./-]+\.(?:md|py|json)", text):
                    add(rel, "CROSS_PACKAGE_PATH", f"file path into sibling skill {other}")
        for resolved, p in all_files.items():
            rel_in = p.relative_to(pkg).as_posix()
            if resolved not in reached and rel_in not in ORPHAN_OK:
                add(f"{rel_pkg}/{rel_in}", "ORPHAN", "not reachable from SKILL.md")

        for p in files:
            rel = f"{rel_pkg}/{p.relative_to(pkg).as_posix()}"
            if "__pycache__" in p.parts or p.suffix == ".pyc":
                add(rel, "ARTIFACT", "bytecode or cache file shipped")
                continue
            if p.suffix == ".py":
                try:
                    compile(p.read_text(encoding="utf8", errors="replace"), str(p), "exec")  # syntax only
                except SyntaxError as exc:
                    add(rel, "SYNTAX", f"{exc.msg} (line {exc.lineno})")
    # public-data boundary: every file in the tree, including this checker, the
    # tests and retained licence text (no blanket self/test skip, no vendor exemption)
    _privacy(
        root,
        (p for p in sorted(root.rglob("*")) if p.is_file() and not (set(p.relative_to(root).parts) & (SKIP_DIRS | {"__pycache__"}))),
        add,
        deny,
    )

    if vendor_manifest:
        _vendor_manifest(root, vendor_manifest, add)
    return findings


def _vendor_manifest(root: Path, vendor_manifest, add):
    """Check every caller-declared upstream provenance entry; do not infer provenance/completeness."""
    base = (root / "skill-creator").resolve()
    try:
        files = json.loads(Path(vendor_manifest).read_text(encoding="utf8"))["files"]
        if not isinstance(files, dict) or not files:
            raise ValueError("'files' must be a non-empty mapping of path -> {sha256}")
        for dest, info in files.items():
            if not isinstance(info, dict) or not isinstance(info.get("sha256"), str):
                raise ValueError("every entry needs a string sha256")
            (base / dest).resolve().relative_to(base)  # a declared path must stay inside skill-creator/
    except (OSError, ValueError, KeyError, TypeError) as exc:
        add("vendor-manifest", "VENDOR_MANIFEST_INVALID", f"{type(exc).__name__}: {exc}")
        return
    for dest, info in files.items():
        p = base / dest
        if not p.is_file():
            add(f"skill-creator/{dest}", "VENDOR_MISSING", "declared file not found")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != info["sha256"]:
            add(f"skill-creator/{dest}", "VENDOR_MODIFIED", "sha256 differs from the vendor manifest")


def _deny_regex(term: str):
    """Whole-word regex for a literal term (word boundaries only at word-character edges)."""
    term = term.strip()
    head = r"(?<!\w)" if re.match(r"\w", term[0]) else ""
    tail = r"(?!\w)" if re.match(r"\w", term[-1]) else ""
    return term, re.compile(head + re.escape(term) + tail)


def _utf8_text(path: Path):
    """Return the file's text, or None if it is not valid UTF-8 text (NUL bytes or bad UTF-8)."""
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf8")
    except UnicodeDecodeError:
        return None


def _privacy(root: Path, paths, add, deny=()):
    """Scan every given file. Findings carry path, code and line only; matched values are never echoed."""
    for p in paths:
        rel = p.relative_to(root).as_posix()
        text = _utf8_text(p)
        if text is None:
            add(rel, "UNSCANNED_BINARY", "not valid UTF-8 text (NUL bytes or invalid UTF-8): not scanned; opaque files should not ship in the public tree")
            continue
        for code, rx in PRIVACY:
            m = rx.search(text)
            if m:
                add(rel, code, f"match at line {text.count(chr(10), 0, m.start()) + 1} (value redacted)")
        for _term, rx in deny:
            m = rx.search(text)
            if m:
                add(rel, "DENIED_TERM", f"externally supplied term at line {text.count(chr(10), 0, m.start()) + 1} (term redacted)")


def main(argv) -> int:
    parser = argparse.ArgumentParser(description="Offline structural checks for skill packages.")
    parser.add_argument("root", nargs="?", help="repository root (default: parent of scripts/)")
    parser.add_argument("--vendor-manifest", help="JSON manifest binding the vendored upstream files")
    parser.add_argument("--deny-file", help="file with one organisation-specific term per line ('#' comments)")
    args = parser.parse_args(list(argv))  # exits with status 2 on a usage error
    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    # A symlink root (live, broken, or pointing at a non-directory) is NOT an invalid-root usage error: check() owns it and
    # reports UNSUPPORTED_SYMLINK without resolving or reading the target. Only a non-link non-directory is exit 2.
    if not root.is_symlink() and not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    terms = None
    if args.deny_file:
        deny_path = Path(args.deny_file)
        if not deny_path.is_file():
            print(f"deny file not found: {deny_path}", file=sys.stderr)
            return 2
        terms = [l.strip() for l in deny_path.read_text(encoding="utf8").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    findings = check(root, args.vendor_manifest, terms)
    for path, code, msg in findings:
        print(f"{path}: {code}: {msg}")
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
