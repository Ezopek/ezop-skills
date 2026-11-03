#!/usr/bin/env python3
"""Apply reviewed whole-face paint relabels to a sibling Bambu/Orca 3MF.

The analysis JSON must contain a ``candidates`` list. Each candidate carries
``component``, ``source_label``, ``target_label`` and exact ``face_ids``.
Request identifiers must be JSON integers exactly as supplied: ``face_ids``
(zero-based) and ``component`` nonnegative, labels 1..4. Fractions, booleans,
strings and null are refused, never truncated or repaired.
This script never overwrites the source, validates the source hash when one is
given, checks every requested source label, preserves ZIP members, builds the
archive in a temporary file that is then renamed into place, and emits a
face-level provenance manifest.

Caller preconditions (stated, not enforced): the source 3MF is frozen
(immutable for the whole run) and the output location is a private workspace
with exactly one writer. This script does not enforce locking, concurrency
safety or transactions; it makes no defence against another process changing
the source or the output location while it runs.

A symlink at the output path or at the sidecar path (even a dangling one) is
refused before anything is written, and is never followed: the output path is
checked before it is resolved, and the sidecar is created exclusively. Ordinary
symlinks elsewhere (the source file, parent directories) are not prohibited.

The sidecar manifest records the absolute source and output paths. Treat those
paths as private evidence (they can reveal user names and project locations) and
redact them before sharing the sidecar. On POSIX the sidecar is created
owner-only (mode 0600, exclusive create, no later chmod); that permission claim
is not made for other platforms.

The analysis JSON must be unambiguous: duplicate object keys at any depth and
the non-finite constants NaN and Infinity are refused rather than resolved.

Paint token mapping is the common four-tool whole-face Bambu/Orca mapping
(1->"4", 2->"8", 3->"0C", 4->"1C"). A requested face whose current token is not
one of these (for example a split-triangle token) is refused; faces that are not
requested keep their original bytes. Split tokens need a dedicated decoder/solver.
For a relabelled face only the bytes of the paint_color value change; the
whitespace before the attribute, its name and its quotes are kept exactly as
written. A requested face without a paint_color attribute is refused: it inherits the base
extruder, which this tool does not know.

Which bytes are the paint attribute is decided by a small quote-aware start-tag
scanner (it is not an XML parser: no entity, namespace, encoding or schema
handling). Within a face, the paint is the attribute whose raw name is exactly
``paint_color`` (a prefixed, hyphenated or differently cased name is a different
attribute). Text that merely looks like a
paint attribute inside another attribute's quoted value, such as a note that
contains paint_color="4", is never selected, and a ``>`` inside a quoted value does
not end a tag. Single- or double-quoted values and whitespace around ``=`` are
accepted. Element and attribute names must be qualified ASCII lexical names
([prefix:]local, each part a letter or underscore followed by letters, digits, ".",
"-" or "_"); values may hold any Unicode. This is a lexical guard, not an XML
engine, namespace resolver or 3MF-schema check. Unsupported XML syntax anywhere in
the model (a name outside that grammar such as @bad, a digit-initial or non-ASCII
name, a ``<`` inside a quoted value, an unquoted value, no whitespace between attributes, a duplicate attribute
name, an unterminated or malformed tag) is refused by name before anything is
written; nothing is guessed or repaired. The scan is linear in the model size and
the whole model member is held in memory.

Face identity is structural, not a raw element name. A face is a ``triangle``
element on the structural path model/resources/object/mesh/triangles/triangle with
ONE consistent namespace (default or prefixed, the same for every step), counted in
document order across all objects. Elements that merely carry the name triangle
elsewhere (metadata or extension elements, nested or out-of-mesh ones, or ones in a
different namespace) are not faces: only the mesh faces are indexed, requested and
counted (``triangle_count``), and every other triangle keeps its bytes. The path is
decoded by a small read-only pass of the standard-library expat parser, which
supplies each real mesh face's raw byte offset; nothing is reserialised and every
edit stays a raw value-span edit. A model that is not well-formed XML, or whose
lexical scan and structural decode disagree, is refused before anything is written.
This is a read-only structural decode, not a schema or 3MF-validity check, a
namespace service or an XML rewriter.

Identity requests (source label equal to
target label) are refused; an empty candidate list is a valid no-op. The output
and its ``<output>.cleanup.json`` sidecar must both be absent when it starts; the
archive and the sidecar are written one after the other, not as one atomic
transaction.
The 3MF must hold exactly one 3D/Objects/*.model member.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import NamedTuple
from xml.parsers import expat
import zipfile

TOKEN_BY_LABEL = {1: b"4", 2: b"8", 3: b"0C", 4: b"1C"}
LABEL_BY_TOKEN = {value: key for key, value in TOKEN_BY_LABEL.items()}

# Quote-aware start-tag scanner (a tiny duplicate of the one in verify_3mf_paint_cleanup.py on purpose: the two
# scripts stay standalone). XML whitespace only; a quoted value may hold anything except its own quote and '<'.
# Names are qualified ASCII lexical XML names, [prefix:]local, each part a letter or underscore followed by letters, digits,
# '.', '-' or '_'. Anything else (a leading digit or punctuation, '@', a second colon, non-ASCII) fails closed.
_PART = rb"[A-Za-z_][A-Za-z0-9_.-]*"
_NAME = _PART + rb"(?::" + _PART + rb")?"
_SPACE = rb"[ \t\r\n]"
DECLARATION_RE = re.compile(rb"\s*(?:\xef\xbb\xbf)?<\?xml\b[^?]*\?>")
START_TAG_RE = re.compile(rb"<(" + _NAME + rb")")
END_TAG_RE = re.compile(rb"</" + _NAME + _SPACE + rb"*>")
ATTRIBUTE_RE = re.compile(_SPACE + rb"+(" + _NAME + rb")" + _SPACE + rb"*=" + _SPACE + rb"*(?:\"([^\"<]*)\"|'([^'<]*)')")
TAG_END_RE = re.compile(_SPACE + rb"*/?>")


class Tag(NamedTuple):
    raw: bytes  # the whole start tag
    value: tuple[int, int] | None  # span (inside raw) of the paint_color VALUE, or None when the tag has no paint_color attribute
    attribute: tuple[int, int] | None  # span (inside raw) of the whole attribute including its leading whitespace


def _unsupported(position: int, reason: str):
    raise SystemExit(f"Unsupported XML syntax at model byte {position}: {reason}; refusing to guess which bytes are the paint_color attribute")


MESH_PATH = ("model", "resources", "object", "mesh", "triangles", "triangle")


def mesh_face_starts(model: bytes) -> set[int]:
    """Raw byte offsets of the '<' of every real mesh face start tag, from a read-only structural pass (stdlib expat).

    A face is a ``triangle`` element on the path model/resources/object/mesh/triangles/triangle whose six steps share ONE
    namespace. Namespace scopes are tracked by hand (declarations on the element itself apply to it); an unbound prefix resolves
    to no namespace, so such an element is simply not a face. Nothing is rewritten and no schema is consulted.
    """
    parser = expat.ParserCreate()
    scopes: list[dict] = [{}]
    path: list[tuple] = []
    starts: set[int] = set()

    def started(qname, attrs):
        scope = scopes[-1]
        declared = {key: value for key, value in attrs.items() if key == "xmlns" or key.startswith("xmlns:")}
        if declared:
            scope = dict(scope)
            for key, value in declared.items():
                if key != "xmlns" and not value:  # xmlns:p="" is not a binding (XML Namespaces 1.0): the prefix is unbound, not the empty namespace
                    scope.pop(key[6:], None)
                else:
                    scope["" if key == "xmlns" else key[6:]] = value
        scopes.append(scope)
        prefix, colon, local_name = qname.partition(":")
        path.append((scope.get(prefix) if colon else scope.get("", ""), local_name if colon else qname))
        if len(path) == len(MESH_PATH) and tuple(name for _, name in path) == MESH_PATH:
            if path[0][0] is not None and all(ns == path[0][0] for ns, _ in path):
                starts.add(parser.CurrentByteIndex)

    def ended(qname):
        scopes.pop()
        path.pop()

    parser.StartElementHandler = started
    parser.EndElementHandler = ended
    try:
        parser.Parse(model, True)
    except expat.ExpatError as exc:
        raise SystemExit(f"Model XML is not well-formed ({exc}); refusing to guess which elements are mesh faces") from None
    return starts


def split_triangles(model: bytes) -> tuple[list[bytes], list[Tag]]:
    """Scan every start tag of the model; return (the bytes around the real mesh-face start tags, those tags).

    ``outside`` has one more piece than there are tags: outside[0] + tags[0].raw + outside[1] + ... is the model.
    A face is chosen structurally (see ``mesh_face_starts``), never by raw element name; only an attribute named exactly
    ``paint_color`` is its paint. Triangle-named elements that are not mesh faces stay inside the outside pieces.
    """
    declaration = DECLARATION_RE.match(model)
    position = declaration.end() if declaration else 0
    candidates: list[tuple[int, int, Tag]] = []  # every triangle-named start tag: (start, end, tag)
    while True:
        start = model.find(b"<", position)
        if start < 0:
            break
        if model.startswith(b"</", start):
            end_tag = END_TAG_RE.match(model, start)
            if end_tag is None:
                _unsupported(start, "malformed end tag")
            position = end_tag.end()
            continue
        opening = START_TAG_RE.match(model, start)
        if opening is None:
            _unsupported(start, "a '<' that does not start a well-formed tag")
        position = opening.end()
        seen: set[bytes] = set()
        value = attribute = None
        while True:
            found = ATTRIBUTE_RE.match(model, position)
            if found is None:
                break
            name = found.group(1)
            if name in seen:
                _unsupported(found.start(1), "duplicate attribute name")
            seen.add(name)
            if name == b"paint_color":
                group = 2 if found.group(2) is not None else 3
                value = (found.start(group) - start, found.end(group) - start)
                attribute = (found.start() - start, found.end() - start)
            position = found.end()
        closing = TAG_END_RE.match(model, position)
        if closing is None:
            _unsupported(position, "an attribute that is not name=\"value\" or name='value', or an unterminated tag")
        position = closing.end()
        if opening.group(1).rpartition(b":")[2] == b"triangle":  # any prefix: the structural pass decides which of these are faces
            candidates.append((start, position, Tag(model[start:position], value, attribute)))
    starts = mesh_face_starts(model)
    chosen = [item for item in candidates if item[0] in starts]
    if len(chosen) != len(starts):
        raise SystemExit("Model XML: the lexical scan and the structural decode disagree about the mesh faces; refusing to guess")
    outside: list[bytes] = []
    tags: list[Tag] = []
    last = 0
    for start, end, tag in chosen:
        outside.append(model[last:start])
        tags.append(tag)
        last = end
    outside.append(model[last:])
    return outside, tags


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _no_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise SystemExit(f"Duplicate JSON object key {key[:40]!r}; refusing to pick one of the values")
        seen[key] = value
    return seen


def _no_constant(name):
    raise SystemExit(f"Non-finite JSON constant {name} is not allowed")


def load_strict_json(path: Path):
    """Parse JSON that must be unambiguous: no duplicate object keys at any depth, no NaN/Infinity."""
    return json.loads(path.read_text(), object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)


def json_int(value: object, what: str, *, nonnegative: bool) -> int:
    """Return value only if it is a real JSON integer (a bool is not one); never convert."""
    if type(value) is not int:
        kind = "nonnegative JSON integer" if nonnegative else "JSON integer (labels are 1..4)"
        raise SystemExit(f"{what} must be a {kind}, got {type(value).__name__}")
    if nonnegative and value < 0:
        raise SystemExit(f"{what} must be a nonnegative JSON integer, got a negative number")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-input-sha256")
    args = parser.parse_args()

    # Check the output leaf BEFORE resolving it: resolve() would follow a (possibly dangling) link and
    # the later checks would then look at the link's target instead of the entry the caller named.
    if args.output.is_symlink():
        raise SystemExit(f"Refusing a symlink at the output path (not followed, target untouched): {args.output}")
    source = args.input.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("Refusing to overwrite the source 3MF")
    if os.path.lexists(output):
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    manifest_path = output.with_suffix(output.suffix + ".cleanup.json")
    if os.path.lexists(manifest_path):  # lexists: a dangling sidecar symlink counts as present
        raise SystemExit(f"Refusing to overwrite or follow an existing manifest sidecar entry: {manifest_path}")

    source_hash = sha256(source)
    if args.expected_input_sha256 and source_hash != args.expected_input_sha256:
        raise SystemExit(f"Input hash mismatch: expected {args.expected_input_sha256}, got {source_hash}")

    analysis = load_strict_json(args.analysis)
    requested: dict[int, dict[str, object]] = {}
    candidates = analysis.get("candidates") if isinstance(analysis, dict) else None
    if not isinstance(candidates, list):
        raise SystemExit("The analysis JSON must hold a 'candidates' list")
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise SystemExit(f"candidate {index} must be an object")
        for key in ("component", "source_label", "target_label", "face_ids"):
            if key not in candidate:
                raise SystemExit(f"candidate {index} is missing required key {key!r}")
        source_label = json_int(candidate["source_label"], f"candidate {index} source_label", nonnegative=False)
        target_label = json_int(candidate["target_label"], f"candidate {index} target_label", nonnegative=False)
        component = json_int(candidate["component"], f"candidate {index} component", nonnegative=True)
        if not isinstance(candidate["face_ids"], list):
            raise SystemExit(f"candidate {index} face_ids must be a list of nonnegative JSON integers")
        if source_label not in TOKEN_BY_LABEL or target_label not in TOKEN_BY_LABEL:
            raise SystemExit(f"Unsupported label mapping {source_label}->{target_label}")
        if source_label == target_label:
            raise SystemExit(f"Identity relabel {source_label}->{target_label} is not a change; remove it from the analysis")
        for position, face_id in enumerate(candidate["face_ids"]):
            face_id = json_int(face_id, f"candidate {index} face_ids[{position}]", nonnegative=True)
            row = {
                "source_label": source_label,
                "target_label": target_label,
                "component": component,
            }
            prior = requested.get(face_id)
            if prior is not None and prior != row:
                raise SystemExit(f"Conflicting relabel requests for face {face_id}: {prior} vs {row}")
            requested[face_id] = row

    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("Duplicate ZIP member names are unsupported; refusing ambiguous archive lookup")
        model_members = [name for name in archive.namelist() if name.startswith("3D/Objects/") and name.endswith(".model")]
        if len(model_members) != 1:
            raise SystemExit(f"Expected exactly one object model, got {model_members}")
        model_member = model_members[0]
        model_data = archive.read(model_member)
        without_declaration = re.sub(rb'^\s*(?:\xef\xbb\xbf)?<\?xml\b[^?]*\?>', b'', model_data, count=1)
        if b'<!' in model_data or b'<?' in without_declaration:
            raise SystemExit("Unsupported XML markup: comments, CDATA, DTD or processing instructions need an XML-aware workflow")

    seen_changes: dict[int, dict[str, object]] = {}
    outside, tags = split_triangles(model_data)  # refuses unsupported XML syntax before anything is written
    pieces = [outside[0]]
    for triangle_index, tag in enumerate(tags):
        request = requested.get(triangle_index)
        raw = tag.raw
        if request is not None:
            if tag.value is None:
                # A missing paint_color inherits the base extruder, which this tool cannot know.
                raise SystemExit(
                    f"Face {triangle_index} has no paint_color; its inherited base-extruder label is unknown, refusing to relabel it"
                )
            value_start, value_end = tag.value
            before_token = raw[value_start:value_end]
            before_label = LABEL_BY_TOKEN.get(before_token)
            if before_label != request["source_label"]:
                raise RuntimeError(
                    f"Face {triangle_index} source mismatch: analysis={request['source_label']} token={before_token!r}"
                )
            after_token = TOKEN_BY_LABEL[int(request["target_label"])]
            # Replace ONLY the bytes of the value: the whitespace before the attribute, its name and its quotes stay as written.
            raw = raw[:value_start] + after_token + raw[value_end:]
            seen_changes[triangle_index] = {
                **request,
                "before_token": before_token.decode(),
                "after_token": after_token.decode(),
            }
        pieces.append(raw)
        pieces.append(outside[triangle_index + 1])
    rewritten = b"".join(pieces)
    triangle_count = len(tags)
    missing = sorted(set(requested) - set(seen_changes))
    if missing:
        raise SystemExit(f"Requested face IDs not found: {missing[:20]}")
    if len(seen_changes) != len(requested):
        raise SystemExit(f"Applied {len(seen_changes)} changes, expected {len(requested)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=output.parent)
    try:
        # The archive is written through the descriptor mkstemp opened (no close/unlink/re-create by name);
        # os.fdopen takes ownership of the descriptor and closes it when the block ends.
        with os.fdopen(fd, "wb") as handle, zipfile.ZipFile(source) as src, zipfile.ZipFile(handle, "w", allowZip64=True) as dst:
            dst.comment = src.comment
            for info in src.infolist():
                payload = rewritten if info.filename == model_member else src.read(info.filename)
                dst.writestr(info, payload)
        with zipfile.ZipFile(temp_name) as verify, zipfile.ZipFile(source) as original:
            bad_member = verify.testzip()
            if bad_member is not None:
                raise RuntimeError(f"ZIP CRC failure in {bad_member}")
            if verify.namelist() != original.namelist():
                raise RuntimeError("ZIP member list/order changed")
        Path(temp_name).replace(output)
    finally:
        Path(temp_name).unlink(missing_ok=True)

    output_hash = sha256(output)
    component_ids = sorted({int(row["component"]) for row in requested.values()})
    summary: dict[str, dict[str, int]] = {}
    for row in seen_changes.values():
        mapping = f"{row['source_label']}->{row['target_label']}"
        bucket = summary.setdefault(mapping, {"faces": 0})
        bucket["faces"] += 1

    manifest = {
        "source": str(source),
        "source_sha256": source_hash,
        "output": str(output),
        "output_sha256": output_hash,
        "model_member": model_member,
        "triangle_count": triangle_count,
        "changed_components": len(component_ids),
        "changed_faces": len(seen_changes),
        "mapping_face_counts": summary,
        "component_ids": component_ids,
        "changes": {str(face_id): row for face_id, row in sorted(seen_changes.items())},
    }
    try:
        # O_CREAT|O_EXCL never follows a symlink and never reuses an existing entry; mode 0600 makes the sidecar
        # owner-only from the moment it exists (the umask can only narrow it), so no later chmod is needed.
        fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(f"Refusing to overwrite or follow an existing manifest sidecar entry: {manifest_path} (the archive {output} was already written; it has no sidecar)")
    with os.fdopen(fd, "w", encoding="utf8") as sidecar:  # takes ownership of fd and closes it
        sidecar.write(json.dumps(manifest, indent=2, allow_nan=False))
    print(json.dumps({key: manifest[key] for key in (
        "source_sha256", "output_sha256", "triangle_count", "changed_components", "changed_faces", "mapping_face_counts"
    )}, indent=2))
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
