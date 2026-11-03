"""Offline tests for the skill source tree. Standard library only.

Run: python3 -B -m unittest discover -s tests

This module holds the SHARED FIXTURES and reference helpers for the suite and
defines no test cases itself. The cases live in its peer modules in this
directory: test_checker.py (the structural checker: positive control plus
mutations that must be caught), test_gcode.py (the two G-code analysers),
test_paint_helpers.py and test_paint_structure.py (the two 3MF paint helpers),
test_contracts.py (reference contracts and documentation guards) and
test_migration_preservation.py (documentary migration-preservation checks). Suite-wide,
they use visibly synthetic inputs generated into a temporary directory. What the
suite does not cover: whether any client loads a skill, skill behaviour, real
slicer or printer behaviour, or real 3MF/G-code files.

Network denial: an audit hook raises on socket use, so these tests fail
loudly if code under test tried to connect. It is a tripwire inside this
Python process, not operating-system containment.
"""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import runpy
import shutil
import socket
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
CAD_SCRIPTS = ROOT / "cad-modeling-and-reverse-engineering" / "scripts"
PRINT_SCRIPTS = ROOT / "3d-printing-workflows" / "scripts"

_DENIED = {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.bind", "socket.sendto"}


def _deny_network(event, args):
    if event in _DENIED:
        raise RuntimeError(f"network use denied in tests: {event}")


sys.addaudithook(_deny_network)

_spec = importlib.util.spec_from_file_location("check_skills", ROOT / "scripts" / "check_skills.py")
check_skills = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_skills)


def run_script(path, argv):
    """Run a script in-process as __main__ (so the audit hook applies).

    Returns (exit, stdout, stderr). exit is 0, an int, or the SystemExit
    message string for a refusal. Other exceptions propagate to the caller
    as the 'exc' element via the 4-tuple form of run_script_exc.
    """
    code, out, err, exc = _run(path, argv)
    if exc is not None:
        raise exc
    return code, out, err


def _run(path, argv):
    out, err = io.StringIO(), io.StringIO()
    old = sys.argv
    sys.argv = [str(path)] + [str(a) for a in argv]
    code, exc = 0, None
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            runpy.run_path(str(path), run_name="__main__")
    except SystemExit as e:
        code = 0 if e.code is None else e.code
    except Exception as e:  # noqa: BLE001 - reported to the test
        exc = e
    finally:
        sys.argv = old
    return code, out.getvalue(), err.getvalue(), exc


_DELETE = object()  # marker: remove this field from a manifest change record


def make_symlink(link, target, directory=False, _os_name=None):
    """Create a real symlink with os.symlink (no mock filesystem).

    On POSIX any failure is a real error. Only on Windows, where creating a symlink needs a privilege
    or developer mode that the test account may lack, an OSError is reported as an explicit skip that
    says the symlink behaviour is NOT QUALIFIED on that host; it is never a pass. _os_name exists so the
    helper's own behaviour can be tested.
    """
    try:
        os.symlink(str(target), str(link), target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        if (_os_name or os.name) == "nt":
            raise unittest.SkipTest(f"NOT QUALIFIED on this Windows account: cannot create a symlink ({type(exc).__name__}); symlink behaviour was not exercised")
        raise


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class TmpCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="skilltest-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)




# --------------------------------------------------------------------------
# G-code analysers (synthetic input)
# --------------------------------------------------------------------------
# Supported contract of both analysers: absolute XY (G90, also the default),
# relative extrusion declared with M83 before any E word.
SEAM = """G90
M83
;LAYER_CHANGE
;Z:0.2
;TYPE:Outer wall
G1 X10 Y10 F3000
G1 X20 Y10 E1.0
G1 X20 Y20 E1.0
G1 X10 Y20 E1.0
G1 X10 Y10.04 E1.0
G1 E-0.8
G1 X10.5 Y10.5
G1 E0.8
G1 X20.5 Y10.5 E1.0
"""

SPARSE = """G90
M83
;LAYER_CHANGE
;Z:0.2
;TYPE:Sparse infill
G1 X1 Y0 F6000
G1 X11 Y10 E1.0 F3000
G1 X11 Y0 F6000
G1 X1 Y10 F6000
"""




# Controller-supplied valid counterexample, reproduced here as visibly synthetic
# data: the arc has equal start/end radii (10 mm about (1, 0)), runs clockwise
# through 270 degrees, and its actual path does not cross the earlier infill
# segment although its straight chord does.
VALID_ARC = """G90
M83
;LAYER_CHANGE
;Z:0.2
;TYPE:Sparse infill
G1 X1 Y0 F6000
G1 X11 Y10 E1.0 F3000
G1 X11 Y0 F6000
G2 X1 Y10 I-10 J0 F6000
"""




# --------------------------------------------------------------------------
# 3MF paint helpers (synthetic archives)
# --------------------------------------------------------------------------
MODEL = (
    '<?xml version="1.0"?><model><resources><object id="1"><mesh>'
    '<vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/>'
    '<vertex x="1" y="1" z="0"/><vertex x="0" y="1" z="0"/></vertices>'
    "<triangles>"
    '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'
    '<triangle v1="0" v2="2" v3="3" paint_color="8"/>'
    '<triangle v1="0" v2="3" v3="1" paint_color="0C"/>'
    '<triangle v1="1" v2="2" v3="3"/>'  # unpainted: inherits an unknown base extruder
    "</triangles></mesh></object></resources></model>"
)
CONFIG = "synthetic_setting = 1\n"


def make_3mf(path, model=MODEL, config=CONFIG, second_model=False):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("3D/Objects/object_1.model", model)
        if second_model:
            z.writestr("3D/Objects/object_2.model", model)
        z.writestr("Metadata/project_settings.config", config)


def repack(src, dst, transforms=None, reverse=False, comment=None):
    transforms = transforms or {}
    with zipfile.ZipFile(src) as s:
        infos = s.infolist()
        if reverse:
            infos = list(reversed(infos))
        with zipfile.ZipFile(dst, "w") as d:
            if comment is not None:
                d.comment = comment  # changes the archive bytes, not any member payload
            for info in infos:
                data = s.read(info.filename)
                if info.filename in transforms:
                    data = transforms[info.filename](data)
                d.writestr(info, data)


def model_text(path):
    with zipfile.ZipFile(path) as z:
        return z.read("3D/Objects/object_1.model").decode()




# --------------------------------------------------------------------------
# Structural checker
# --------------------------------------------------------------------------
GOOD_SKILL = (
    '---\nname: demo-skill\ndescription: "Use when demoing: a sample, with punctuation."\n'
    'license: MIT\nmetadata:\n  scope: "demo"\n---\n\n# Demo\n\nSee `references/guide.md` and [guide](references/guide.md).\n'
    "Outputs such as `report.md` are produced by the procedure, not shipped.\nDocs: [site](https://example.org/x).\n"
)


def make_repo(root, skill=GOOD_SKILL, guide="# Guide\n\nBack to [skill](../SKILL.md).\n", readme="demo-skill is listed\n"):
    root = Path(root)
    (root / "README.md").write_text(readme)
    (root / "INSTALLATION.md").write_text("install demo-skill by copying its folder\n")
    d = root / "demo-skill"
    (d / "references").mkdir(parents=True)
    (d / "SKILL.md").write_text(skill)
    (d / "references" / "guide.md").write_text(guide)
    return root


def codes(findings):
    return {c for _, c, _ in findings}




















# --------------------------------------------------------------------------
# Vision-review contract: one response schema, one verdict vocabulary
# --------------------------------------------------------------------------
CAD_DOCS = ROOT / "cad-modeling-and-reverse-engineering"
SCHEMA_ANCHOR_DOC = "Response schema (one JSON object per call):"
SCHEMA_ANCHOR_TEMPLATE = "Return exactly one JSON object, for the one region named above, matching this schema:"
SCHEMA_KEYS = {"schema_version", "region_id", "status", "observed_object", "defects", "views_consistent", "next_view", "reason"}
DEFECT_KEYS = {"type", "panel_id", "normalized_points", "confidence", "visible_evidence"}
TEMPLATE_PLACEHOLDERS = {"SEMANTIC_CONTRACT", "DISPLAY_ROLE_MAPPING", "PANEL_LEGEND", "PANEL_DIMENSIONS", "REGION_ID", "OBJECT_VOCABULARY"}


def schema_after(text, anchor):
    """Parse the JSON example that follows an anchor sentence; fail loudly if absent."""
    at = text.index(anchor)
    start = text.index("{", at)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def enum(value):
    return {part.strip() for part in value.split("|")}


def _is_number(value):
    """A JSON number. Python's bool is an int subclass, but JSON true/false are not numbers."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_response(resp, schema, known_regions, known_panels):
    """Reference check of the documented contract (not a runtime shipped to users).

    Returns a list of violations; empty means the response honours the contract.
    """
    bad = []
    if not isinstance(resp, dict) or set(resp) != set(schema):
        return ["response must be exactly one object with the schema keys"]
    status_values, type_values, view_values = enum(schema["status"]), enum(schema["defects"][0]["type"]), enum(schema["next_view"])
    # Shape admission first: an identifier or vocabulary field must be a string BEFORE any membership test (a list or object
    # is unhashable), and containers must be the right container BEFORE they are iterated. Malformed ordinary JSON becomes a
    # violation, never an exception. (Reference fixture only; not a shipped validator.)
    if resp["schema_version"] != schema["schema_version"]:
        bad.append("schema_version")
    for key in ("observed_object", "reason"):  # documented free-text fields: non-empty strings (never None, a list, a number, ...)
        if not isinstance(resp[key], str):
            bad.append(f"{key} must be a string")
        elif not resp[key].strip():
            bad.append(f"{key} must not be empty")
    if not isinstance(resp["region_id"], str):
        bad.append("region_id must be a string")
    elif resp["region_id"] not in known_regions:
        bad.append("unknown region_id")
    status = resp["status"]
    if not isinstance(status, str):
        bad.append("status must be a string")
    elif status not in status_values:
        bad.append("status outside the vocabulary")
    if not isinstance(resp["next_view"], str):
        bad.append("next_view must be a string")
    elif resp["next_view"] not in view_values:
        bad.append("next_view outside the vocabulary")
    if not isinstance(resp["views_consistent"], bool):
        bad.append("views_consistent must be boolean")
    defects = resp["defects"]
    if not isinstance(defects, list):
        bad.append("defects must be a list")
        return bad
    # Cross-field matrix: disagreeing views imply `uncertain`; `clean` also needs next_view "none" (and views_consistent true, which the
    # first rule enforces together with the boolean check). A concrete defect MAY still request another view and `uncertain` MAY carry
    # possible defects, so neither is prohibited here.
    if resp["views_consistent"] is False and status != "uncertain":
        bad.append("views_consistent false requires status uncertain")
    if status == "clean" and resp["next_view"] != "none":
        bad.append("clean requires next_view none")
    if status == "clean" and defects:
        bad.append("clean must not carry defects")
    if status == "defect" and not defects:
        bad.append("defect needs at least one concrete defect")
    for d in defects:
        if not isinstance(d, dict):
            bad.append("defect must be an object")
            continue
        if set(d) != set(schema["defects"][0]):
            bad.append("defect keys")
            continue
        if not isinstance(d["type"], str):
            bad.append("defect type must be a string")
        elif d["type"] not in type_values:
            bad.append("defect type outside the vocabulary")
        if not isinstance(d["visible_evidence"], str):
            bad.append("visible_evidence must be a string")
        elif not d["visible_evidence"].strip():
            bad.append("visible_evidence must not be empty")
        if not isinstance(d["panel_id"], str):
            bad.append("panel_id must be a string")
        elif d["panel_id"] not in known_panels:
            bad.append("unknown panel_id")
        pts = d["normalized_points"]
        if not isinstance(pts, list) or not pts:
            bad.append("point outside [0,1]" if isinstance(pts, list) else "normalized_points must be a list")
        elif any(not isinstance(p, list) or len(p) != 2 or not all(_is_number(c) and 0 <= c <= 1 for c in p) for p in pts):
            bad.append("point outside [0,1]")
        elif ([0, 0] in [list(map(float, p)) for p in pts] and [1, 1] in [list(map(float, p)) for p in pts]) or (
            [0, 1] in [list(map(float, p)) for p in pts] and [1, 0] in [list(map(float, p)) for p in pts]
        ):  # either pair of opposite corners, in any order and with any extra points, covers the whole panel
            bad.append("whole-panel placeholder")
        if not _is_number(d["confidence"]) or not 0 <= d["confidence"] <= 1:
            bad.append("confidence")
    return bad




# --------------------------------------------------------------------------
# STL T-junction repair: directed-edge pairing (tiny synthetic fixture)
# --------------------------------------------------------------------------








if __name__ == "__main__":
    raise SystemExit("Shared fixtures only; run python -m unittest discover -s tests -v")
