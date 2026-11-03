#!/usr/bin/env python3
"""Independently verify the exact mutation scope of a whole-face 3MF cleanup.

The manifest must name the exact supplied artifacts: source_sha256 and
output_sha256 have to equal the SHA-256 of the source and candidate files given
on the command line, otherwise nothing else is checked. (Exact archive bytes are
bound; a repacked archive with identical member payloads needs its own manifest.)

The manifest JSON must be unambiguous: duplicate object keys at any depth and
the constants NaN and Infinity are refused, and face keys in "changes" must be
canonical nonnegative decimal strings (aliases such as "00" or "+0" are refused,
not normalised). source_label / target_label are optional; when a record has them
they must be JSON integers 1..4 that agree with its before_token / after_token
(four-tool mapping 4, 8, 0C, 1C). Token-only records remain valid, but every record must carry BOTH
before_token and after_token as strings that are exactly 4, 8, 0C or 1C: a missing or other value is refused by field name, before
any comparison, without normalising or echoing it. This is a
consistency check, not authentication or signing of the manifest.

Independently of any labels, every changed face must have a supported whole-face
token (4, 8, 0C or 1C) on BOTH sides, regardless of what the manifest records:
a change to or from any other token (for example 44 or a split-triangle token)
is refused without echoing it. The optional summary fields (triangle_count,
changed_faces, changed_components, component_ids, mapping_face_counts,
model_member) are checked against the verified artifacts only when they are
supplied; a bare token-only manifest needs none of them. The per-change
"component" values are caller-declared identifiers: they are checked for type
and for agreement with component_ids / changed_components, and are not geometric,
topological or authenticated provenance.

Only the VALUE of a paint_color attribute inside a <triangle> tag may differ: the
whitespace before the attribute, its name, its quotes and every other byte of the
tag must match exactly, even when the candidate's hash and manifest are rebound; every other model
byte and every other ZIP member must be identical. A changed face that is
unpainted (no paint_color) in the source or the candidate is refused, because it
inherits a base extruder this tool cannot know.

Which bytes are the paint attribute is decided by a small quote-aware start-tag
scanner (it is not an XML parser: no entity, namespace, encoding or schema
handling). Within a face, the paint is the attribute whose raw name is exactly
``paint_color`` (a prefixed, hyphenated
or differently cased name is a different attribute, so editing it is a change
outside the paint value). Text that merely looks like a paint attribute inside
another attribute's quoted value is never read as paint, and a ``>`` inside a
quoted value does not end a tag. Single- or double-quoted values and whitespace
around ``=`` are accepted. Element and attribute names must be qualified ASCII
lexical names ([prefix:]local, each part a letter or underscore followed by letters,
digits, ".", "-" or "_"); values may hold any Unicode. This is a lexical guard, not
an XML engine, namespace resolver or 3MF-schema check. Unsupported XML syntax
anywhere in either model (a name outside that grammar such as @bad, a digit-initial
or non-ASCII name, a ``<`` inside a quoted value, an unquoted value, no whitespace between attributes, a
duplicate attribute name, an unterminated or malformed tag) is refused by name;
nothing is guessed. The scan is linear in the model size and the whole model
member is held in memory.

Face identity is structural, not a raw element name. A face is a ``triangle``
element on the structural path model/resources/object/mesh/triangles/triangle with
ONE consistent namespace (default or prefixed, the same for every step), counted in
document order across all objects, in the source and in the candidate independently.
Elements that merely carry the name triangle elsewhere (metadata or extension
elements, nested or out-of-mesh ones, or ones in a different namespace) are not
faces: only the mesh faces are compared as faces, and every other triangle is
ordinary model bytes that must stay identical, so a rebound candidate that edits the
wrong element is refused. The path is decoded by a small read-only pass of the
standard-library expat parser, which supplies each real mesh face's raw byte offset;
nothing is reserialised. A model that is not well-formed XML, or whose lexical scan
and structural decode disagree, is refused. This is a read-only structural decode,
not a schema or 3MF-validity check, a namespace service or an XML rewriter.

Caller preconditions (stated, not enforced): the source and candidate files are
frozen (not modified) for the whole run and live in a private workspace with one
writer. This script does not enforce locking, snapshots, concurrency safety or
transactions, and it makes no defence against another process changing either
file while it runs. The artifact hashes are computed by streaming rather than by
reading each whole file into memory; individual ZIP members and the model XML are
still read into memory for the comparison. The applier
writes the archive and then the sidecar manifest as two separate steps: they are
not one atomic transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import NamedTuple
from xml.parsers import expat
import zipfile

# Quote-aware start-tag scanner (a tiny duplicate of the one in apply_reviewed_paint_cleanup.py on purpose: the two
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
CANONICAL_FACE_KEY = re.compile(r"(?:0|[1-9][0-9]*)")  # ASCII digits only, no sign, spaces, underscores or leading zeros
LABEL_BY_TOKEN = {"4": 1, "8": 2, "0C": 3, "1C": 4}  # the same four-tool whole-face mapping the applier writes


def _no_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise SystemExit(f"Duplicate JSON object key {key[:40]!r}; refusing to pick one of the values")
        seen[key] = value
    return seen


def _no_constant(name):
    raise SystemExit(f"Non-finite JSON constant {name} is not allowed")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    """SHA-256 of a file, streamed in 1 MiB blocks (never the whole file in memory)."""
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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


def token(tag: Tag) -> str | None:
    """Return the triangle's paint_color value, or None when absent (inherits an unknown base extruder)."""
    return tag.raw[tag.value[0] : tag.value[1]].decode() if tag.value else None


def same_outside_paint_value(before: Tag, after: Tag) -> bool:
    """Compare two <triangle> tags everywhere except the paint_color VALUE.

    When both tags are painted, the whitespace before the attribute, its name, its quotes and every other
    byte of the tag must match exactly (nothing is normalised). When exactly one is painted the whole
    attribute is dropped from both before comparing, so the unpainted-lineage guard further down can refuse
    that change by name.
    """
    if before.value and after.value:
        return before.raw[: before.value[0]] + before.raw[before.value[1] :] == after.raw[: after.value[0]] + after.raw[after.value[1] :]
    return _without_attribute(before) == _without_attribute(after)


def _without_attribute(tag: Tag) -> bytes:
    return tag.raw[: tag.attribute[0]] + tag.raw[tag.attribute[1] :] if tag.attribute else tag.raw


def _nonnegative_int(value: object, what: str) -> int:
    if type(value) is not int or value < 0:  # a bool is not a JSON integer here
        raise SystemExit(f"Manifest {what} must be a nonnegative JSON integer (the value is not echoed)")
    return value


def check_optional_summaries(manifest: dict, expected: dict, actual: dict, triangle_count: int, model_member: str) -> None:
    """Check the optional summary fields and per-change components, but only when they are supplied.

    A bare token-only manifest stays valid. Component values are labels the CALLER declared; they are checked for
    type and for agreement with the summaries, never against geometry or topology. Messages name the field, not the value.
    """
    declared: dict[int, int] = {}
    for face_id, record in expected.items():
        if "component" in record:
            declared[face_id] = _nonnegative_int(record["component"], f"change for face {face_id}: component")
    for field, value in (("triangle_count", triangle_count), ("changed_faces", len(actual))):
        if field in manifest and _nonnegative_int(manifest[field], field) != value:
            raise SystemExit(f"Manifest {field} contradicts the verified artifacts")
    if "model_member" in manifest and manifest["model_member"] != model_member:
        raise SystemExit("Manifest model_member contradicts the verified artifacts")
    if "component_ids" in manifest or "changed_components" in manifest:
        if set(declared) != set(actual):
            raise SystemExit("Manifest component_ids/changed_components cannot be checked: every changed face must declare its component")
        ids = sorted(set(declared.values()))
        if "component_ids" in manifest:
            listed = manifest["component_ids"]
            if not isinstance(listed, list) or [_nonnegative_int(item, "component_ids entry") for item in listed] != ids:
                raise SystemExit("Manifest component_ids contradicts the caller-declared components of the changes")
        if "changed_components" in manifest and _nonnegative_int(manifest["changed_components"], "changed_components") != len(ids):
            raise SystemExit("Manifest changed_components contradicts the caller-declared components of the changes")
    if "mapping_face_counts" in manifest:
        derived: dict[str, dict[str, int]] = {}
        for change in actual.values():
            key = f"{LABEL_BY_TOKEN[change['before_token']]}->{LABEL_BY_TOKEN[change['after_token']]}"
            derived.setdefault(key, {"faces": 0})["faces"] += 1
        supplied_counts = manifest["mapping_face_counts"]
        if isinstance(supplied_counts, dict):
            for row in supplied_counts.values():
                if isinstance(row, dict) and "faces" in row:
                    _nonnegative_int(row["faces"], "mapping_face_counts faces")
        if supplied_counts != derived:
            raise SystemExit("Manifest mapping_face_counts contradicts the verified changes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(), object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("changes"), dict):
        raise SystemExit("The manifest must be an object with a 'changes' object")
    # Bind the manifest to the exact artifacts supplied, before any scope comparison.
    for field, path, label in (("source_sha256", args.source, "Source"), ("output_sha256", args.candidate, "Candidate")):
        if not isinstance(manifest.get(field), str):
            raise SystemExit(f"Manifest has no {field}; refusing to verify artifacts it does not name")
        if file_digest(path) != manifest[field]:
            raise SystemExit(f"{label} hash mismatch: the supplied file is not the one the manifest names ({field})")
    expected_changes = {}
    for key, record in manifest["changes"].items():
        if not CANONICAL_FACE_KEY.fullmatch(key):
            raise SystemExit(f"Manifest face key {key[:40]!r} is not a canonical nonnegative decimal (aliases are not normalised)")
        if not isinstance(record, dict):
            raise SystemExit(f"Manifest change for face {key} must be an object")
        for field in ("before_token", "after_token"):
            # Admission before any indexing or comparison: required, a string, exactly a whole-face token; never normalised or echoed.
            if not isinstance(record.get(field), str) or record[field] not in LABEL_BY_TOKEN:
                raise SystemExit(
                    f"Manifest change for face {key}: {field} is required and must be exactly one of the whole-face tokens 4, 8, 0C or 1C (the value is not echoed)"
                )
        expected_changes[int(key)] = record
    with zipfile.ZipFile(args.source) as source_zip, zipfile.ZipFile(args.candidate) as candidate_zip:
        if any(len(z.namelist()) != len(set(z.namelist())) for z in (source_zip, candidate_zip)):
            raise SystemExit("Duplicate ZIP member names are unsupported; refusing ambiguous archive lookup")
        if source_zip.testzip() is not None or candidate_zip.testzip() is not None:
            raise SystemExit("ZIP CRC validation failed")
        source_names = source_zip.namelist()
        candidate_names = candidate_zip.namelist()
        if source_names != candidate_names:
            raise SystemExit("ZIP member list/order differs")
        model_members = [name for name in source_names if name.startswith("3D/Objects/") and name.endswith(".model")]
        if len(model_members) != 1:
            raise SystemExit(f"Expected one object model, got {model_members}")
        model_member = model_members[0]
        unchanged = {}
        for name in source_names:
            if name == model_member:
                continue
            before = source_zip.read(name)
            after = candidate_zip.read(name)
            if before != after:
                raise SystemExit(f"Unexpected changed ZIP member: {name}")
            unchanged[name] = digest(before)
        source_model = source_zip.read(model_member)
        candidate_model = candidate_zip.read(model_member)

    for model in (source_model, candidate_model):
        without_declaration = re.sub(rb'^\s*(?:\xef\xbb\xbf)?<\?xml\b[^?]*\?>', b'', model, count=1)
        if b'<!' in model or b'<?' in without_declaration:
            raise SystemExit("Unsupported XML markup: comments, CDATA, DTD or processing instructions need an XML-aware workflow")

    source_outside, source_tags = split_triangles(source_model)  # refuses unsupported XML syntax by name
    candidate_outside, candidate_tags = split_triangles(candidate_model)
    if (
        source_outside != candidate_outside  # every byte outside the <triangle> tags
        or len(source_tags) != len(candidate_tags)
        or not all(same_outside_paint_value(a, b) for a, b in zip(source_tags, candidate_tags))
    ):
        raise SystemExit("Model XML differs outside paint_color attributes")
    if len(source_tags) != len(candidate_tags):
        raise SystemExit("Triangle count differs")
    actual_changes = {}
    for face_id, (before_tag, after_tag) in enumerate(zip(source_tags, candidate_tags, strict=True)):
        before = token(before_tag)
        after = token(after_tag)
        if before != after:
            if before is None or after is None:
                raise SystemExit(
                    f"Face {face_id} is unpainted in the source or the candidate; its inherited base-extruder label is unknown, refusing to verify the change"
                )
            if before not in LABEL_BY_TOKEN or after not in LABEL_BY_TOKEN:
                # Unconditional: a changed token must be a known whole-face token on BOTH sides, with or without labels.
                raise SystemExit(
                    f"Face {face_id} changed to or from a token outside the supported whole-face mapping (4, 8, 0C, 1C); refusing to verify the change (the token is not echoed)"
                )
            actual_changes[face_id] = {"before_token": before, "after_token": after}

    if set(actual_changes) != set(expected_changes):
        missing = sorted(set(expected_changes) - set(actual_changes))
        extra = sorted(set(actual_changes) - set(expected_changes))
        raise SystemExit(f"Changed face set mismatch: missing={missing[:20]} extra={extra[:20]}")
    for face_id, actual in actual_changes.items():
        expected = expected_changes[face_id]
        if actual["before_token"] != expected["before_token"] or actual["after_token"] != expected["after_token"]:
            raise SystemExit(f"Token mismatch at face {face_id}: actual={actual} expected={expected}")
        # Optional label fields are checked only when present (token-only records stay supported), against
        # the actual recorded tokens that were just matched.
        for field, token_key in (("source_label", "before_token"), ("target_label", "after_token")):
            if field not in expected:
                continue
            label = expected[field]
            if type(label) is not int:
                raise SystemExit(f"Manifest change for face {face_id}: {field} must be a JSON integer 1..4, got {type(label).__name__}")
            if label not in (1, 2, 3, 4):
                raise SystemExit(f"Manifest change for face {face_id}: {field} must be a JSON integer 1..4, got {label}")
            if LABEL_BY_TOKEN.get(actual[token_key]) != label:
                raise SystemExit(f"Manifest change for face {face_id}: {field} {label} contradicts the recorded {token_key}")

    check_optional_summaries(manifest, expected_changes, actual_changes, len(source_tags), model_member)

    print(json.dumps({
        "zip_members": len(source_names),
        "unchanged_members_verified": len(unchanged),
        "model_member": model_member,
        "triangle_count": len(source_tags),
        "changed_faces_verified": len(actual_changes),
        "xml_outside_paint_attributes_identical": True,
        "changed_face_ids_match_manifest": True,
        "zip_crc_ok": True,
        "source_sha256_verified": True,
        "output_sha256_verified": True,
    }, indent=2))


if __name__ == "__main__":
    main()
