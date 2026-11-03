"""Standard-library synthetic tests; shared fixtures are not production validators.

Correction 23: face identity in the two 3MF paint helpers is STRUCTURAL. A face is a `triangle` element on the path
model/resources/object/mesh/triangles/triangle with one consistent namespace; a metadata, extension, nested or out-of-mesh element that
merely carries the name `triangle` is not a face. ElementTree is only the independent TEST oracle (it reads real element paths and
attributes); the helpers use a small read-only pyexpat pass for byte offsets and keep their raw byte edits. These are synthetic
archives, not real 3MF/slicer validation and not a schema check.

This module composes the shared fixtures; it does not import or inherit any other test class, so no old test is collected twice.
"""
from test_skill_packages import (
    CAD_DOCS,
    CAD_SCRIPTS,
    ET,
    MODEL,
    Path,
    TmpCase,
    _run,
    ast,
    json,
    make_3mf,
    model_text,
    re,
    sha,
    unittest,
)

APPLY_PY = CAD_SCRIPTS / "apply_reviewed_paint_cleanup.py"
VERIFY_PY = CAD_SCRIPTS / "verify_3mf_paint_cleanup.py"
CORE = "http://schemas.microsoft.com/" + "3dmanufacturing/core/2015/02"  # the public 3MF core namespace URI, assembled to keep one literal
VERTS = '<{p}vertices><{p}vertex x="0" y="0" z="0"/><{p}vertex x="1" y="0" z="0"/><{p}vertex x="1" y="1" z="0"/><{p}vertex x="0" y="1" z="0"/></{p}vertices>'
DECOY = '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'


def tri(paint, tag="triangle", extra=""):
    attr = f' paint_color="{paint}"' if paint is not None else ""
    return f'<{tag} v1="0" v2="1" v3="2"{extra}{attr}/>'


def build(objects, *, root_open="<model>", root_close="</model>", p="", head="", in_object="", in_mesh="", in_triangles="", in_build="", bom="", eol="\n", declaration=True):
    """A synthetic model document. `objects` is a list of paint-token lists, one list of mesh faces per object."""
    parts = [bom, ('<?xml version="1.0" encoding="UTF-8"?>' + eol) if declaration else "", root_open, eol, head, f"<{p}resources>"]
    for index, paints in enumerate(objects, 1):
        faces = "".join(tri(paint, tag=f"{p}triangle") for paint in paints)
        parts.append(
            f'<{p}object id="{index}" type="model">{in_object}<{p}mesh>{in_mesh}{VERTS.format(p=p)}'
            f"<{p}triangles>{in_triangles}{faces}</{p}triangles></{p}mesh></{p}object>"
        )
    parts += [f"</{p}resources>", in_build, eol, root_close, eol]
    return "".join(parts)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def space(tag):
    return tag[1:].split("}")[0] if tag.startswith("{") else ""


def parse(document):
    return ET.fromstring(document if isinstance(document, bytes) else document.encode("utf8"))


def faces_in(root):
    """Elements on the path model/resources/object/mesh/triangles/triangle in ONE consistent namespace, found by ElementTree."""
    if local(root.tag) != "model":
        return []
    ns = space(root.tag)
    nodes = [root]
    for name in ("resources", "object", "mesh", "triangles", "triangle"):
        nodes = [child for node in nodes for child in node if local(child.tag) == name and space(child.tag) == ns]
    return nodes


def real_faces(document):
    return faces_in(parse(document))


def all_triangles(document):
    """(is a real mesh face, attributes) for every element whose local name is `triangle`, in document order (one parse tree)."""
    root = parse(document)
    faces = {id(e) for e in faces_in(root)}
    return [(id(e) in faces, dict(e.attrib)) for e in root.iter() if local(e.tag) == "triangle"]


class MeshFaceIdentityTest(TmpCase):
    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        self.out = self.tmp / "synthetic_out.3mf"
        self.manifest = Path(str(self.out) + ".cleanup.json")

    # -- helpers -----------------------------------------------------------------------------------------
    def apply(self, *requests):
        analysis = self.tmp / "analysis.json"
        analysis.write_text(json.dumps({"candidates": [
            {"component": 1, "source_label": s, "target_label": t, "face_ids": ids} for ids, s, t in requests
        ]}))
        return _run(APPLY_PY, [self.src, analysis, self.out])

    def verify(self, candidate=None, manifest=None):
        return _run(VERIFY_PY, [self.src, candidate or self.out, manifest or self.manifest])

    def rebound(self, candidate, changes):
        path = self.tmp / f"rebound-{Path(candidate).stem}.json"
        path.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate), "changes": changes}))
        return path

    def clean_slate(self):
        for leftover in (self.out, self.manifest):
            leftover.unlink(missing_ok=True)

    def refusal(self, result):
        code, _, _, exc = result
        self.assertTrue(isinstance(code, str) or exc is not None, f"expected a refusal, got exit {code!r}")
        return code if isinstance(code, str) else str(exc)

    def assert_applies_exactly(self, before, after, requests, changed_faces):
        """Apply, then require: output text == the expected document, the oracle's mesh faces changed exactly as expected, every
        non-face triangle unchanged, and an independent verification pass."""
        make_3mf(self.src, model=before)
        source_hash = sha(self.src)
        code, _, err, exc = self.apply(*requests)
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0, "a supported structure must be edited, not refused")
        produced = model_text(self.out)
        self.assertEqual(produced, after, "only the requested mesh-face value bytes may differ")
        before_faces, after_faces = real_faces(before), real_faces(produced)
        self.assertEqual(len(before_faces), len(after_faces))
        for index, (x, y) in enumerate(zip(before_faces, after_faces)):
            expected = dict(x.attrib)
            if index in changed_faces:
                expected["paint_color"] = changed_faces[index]
            self.assertEqual(dict(y.attrib), expected, f"mesh face {index}")
        self.assertEqual([a for is_face, a in all_triangles(before) if not is_face], [a for is_face, a in all_triangles(produced) if not is_face], "non-face triangles must be untouched")
        self.assertEqual(sha(self.src), source_hash)
        self.assertEqual(json.loads(self.manifest.read_text())["triangle_count"], len(before_faces), "the count is the number of real mesh faces")
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn(f'"changed_faces_verified": {len(changed_faces)}', out)

    # -- the reproduced defect ------------------------------------------------------------------------------
    def test_a_metadata_triangle_before_resources_is_not_mesh_face_zero(self):
        head = f"<extras>{DECOY}</extras>"
        before = build([["4", "8", "0C"]], head=head)
        after = build([["8", "8", "0C"]], head=head)
        self.assertEqual(len(real_faces(before)), 3, "fixture: the oracle sees three mesh faces")
        self.assertEqual(len(all_triangles(before)), 4)
        self.assert_applies_exactly(before, after, [([0], 1, 2)], {0: "8"})

    def test_a_rebound_candidate_that_edits_the_wrong_element_is_refused_by_the_independent_verifier(self):
        head = f"<extras>{DECOY}</extras>"
        before = build([["4", "8", "0C"]], head=head)
        make_3mf(self.src, model=before)
        claim = {"0": {"before_token": "4", "after_token": "8"}}
        wrong_only = self.tmp / "wrong-element-only.3mf"
        make_3mf(wrong_only, model=build([["4", "8", "0C"]], head=f"<extras>{DECOY.replace(chr(34) + '4' + chr(34), chr(34) + '8' + chr(34))}</extras>"))
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=wrong_only, manifest=self.rebound(wrong_only, claim))))
        both = self.tmp / "wrong-and-right.3mf"
        make_3mf(both, model=build([["8", "8", "0C"]], head=f"<extras>{DECOY.replace(chr(34) + '4' + chr(34), chr(34) + '8' + chr(34))}</extras>"))
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=both, manifest=self.rebound(both, claim))))
        right = self.tmp / "right-only.3mf"  # control: the real mesh face alone is accepted
        make_3mf(right, model=build([["8", "8", "0C"]], head=f"<extras>{DECOY}</extras>"))
        code, out, _, exc = self.verify(candidate=right, manifest=self.rebound(right, claim))
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 1', out)

    # -- namespaces -------------------------------------------------------------------------------------------
    def test_canonical_core_namespace_schema_shaped_document_applies_and_verifies(self):
        root = f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE}">'
        head = '<metadata name="Title">synthetic</metadata>' + f"<extras>{DECOY}</extras>"
        build_part = '<build><item objectid="1"/></build>'
        before = build([["4", "8", "0C"]], root_open=root, head=head, in_build=build_part)
        after = build([["8", "8", "0C"]], root_open=root, head=head, in_build=build_part)
        self.assertEqual(len(real_faces(before)), 3)
        self.assert_applies_exactly(before, after, [([0], 1, 2)], {0: "8"})

    def test_prefixed_namespace_document_applies_and_verifies_and_ignores_a_prefixed_decoy(self):
        root = f'<m:model xmlns:m="{CORE}">'
        head = f'<m:extras>{tri("4", tag="m:triangle")}</m:extras>'
        kwargs = dict(root_open=root, root_close="</m:model>", p="m:", head=head)
        before, after = build([["4", "8"]], **kwargs), build([["8", "8"]], **kwargs)
        self.assertEqual(len(real_faces(before)), 2)
        self.assert_applies_exactly(before, after, [([0], 1, 2)], {0: "8"})

    def test_consistent_default_namespaces_are_accepted_including_the_original_empty_namespace(self):
        for label, root in {"empty namespace": "<model>", "synthetic default namespace": '<model xmlns="urn:synthetic-default">'}.items():
            with self.subTest(label):
                self.clean_slate()
                before, after = build([["4", "8"]], root_open=root), build([["8", "8"]], root_open=root)
                self.assert_applies_exactly(before, after, [([0], 1, 2)], {0: "8"})

    def test_a_namespace_rebinding_inside_the_path_means_those_triangles_are_not_mesh_faces(self):
        # `triangles` and the triangles below it live in a different default namespace than `model`: no consistent mesh path.
        before = build([["4", "8"]], root_open="<model>").replace("<triangles>", '<triangles xmlns="urn:other-ext">')
        self.assertEqual(real_faces(before), [], "fixture: the oracle also finds no consistent mesh path")
        self.assertEqual(len(all_triangles(before)), 2)
        make_3mf(self.src, model=before)
        source_hash = sha(self.src)
        message = self.refusal(self.apply(([0], 1, 2)))
        self.assertIn("not found", message)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.manifest.exists())
        self.assertEqual(sha(self.src), source_hash)

    def test_an_extension_triangle_in_another_default_namespace_is_skipped_by_the_face_index(self):
        ext = '<triangle xmlns="urn:other-ext" v1="0" v2="1" v3="2" paint_color="4"/>'
        before = build([["4"]], in_triangles="").replace("</triangles>", ext + tri("8") + "</triangles>")
        after = build([["4"]], in_triangles="").replace("</triangles>", ext + tri("4") + "</triangles>")
        self.assertEqual(len(real_faces(before)), 2, "fixture: the oracle sees the first and the last triangle as mesh faces")
        self.assert_applies_exactly(before, after, [([1], 2, 1)], {1: "4"})  # mesh face 1 is the LAST triangle, not the extension one

    # -- nested, out-of-mesh and multi-object structures ----------------------------------------------------
    def test_nested_and_out_of_mesh_triangles_are_not_faces_and_a_second_object_continues_the_index(self):
        decoys = dict(
            head=f"<extras>{DECOY}</extras>",
            in_object=DECOY,
            in_mesh=DECOY,
            in_build=f"<build>{DECOY}</build>",
        )
        nested = '<triangle v1="0" v2="1" v3="2" paint_color="4">' + DECOY + "</triangle>"
        before = build([["4", "8"], ["0C", "4"]], **decoys).replace("</triangles>", nested + "</triangles>", 1)
        after = build([["8", "8"], ["0C", "8"]], **decoys).replace("</triangles>", nested + "</triangles>", 1)
        faces = real_faces(before)
        self.assertEqual(len(faces), 5, "fixture: 2 + 1 nested-parent + 2 real mesh faces (the nested child is not a face)")
        # mesh faces in document order: object 1 -> [4, 8, nested parent 4], object 2 -> [0C, 4]; request faces 0 and 4
        self.assert_applies_exactly(before, after, [([0, 4], 1, 2)], {0: "8", 4: "8"})

    # -- byte positions after BOM / CRLF / multibyte text -----------------------------------------------------
    def test_byte_offsets_stay_correct_after_a_bom_crlf_and_multibyte_text_before_the_mesh(self):
        head = '<metadata name="Title">café ☃ \U0001F600 ünï</metadata>\r\n' + f"<extras>{DECOY}</extras>\r\n"
        for bom_label, bom in (("without a BOM", ""), ("with a BOM", "﻿")):
            for eol_label, eol in (("LF", "\n"), ("CRLF", "\r\n")):
                with self.subTest(f"{bom_label}, {eol_label}"):
                    self.clean_slate()
                    before = build([["4", "8", "0C"]], head=head, bom=bom, eol=eol)
                    after = build([["8", "8", "0C"]], head=head, bom=bom, eol=eol)
                    self.assertEqual(len(real_faces(before.encode("utf8"))), 3)
                    self.assert_applies_exactly(before, after, [([0], 1, 2)], {0: "8"})

    # -- unsupported or ambiguous structures: refuse before writing ------------------------------------------------
    def test_a_model_that_is_not_well_formed_is_refused_by_name_before_anything_is_written(self):
        before = build([["4", "8"]]).replace("</mesh>", "</mess>")
        make_3mf(self.src, model=before)
        source_hash = sha(self.src)
        message = self.refusal(self.apply(([0], 1, 2)))
        self.assertIn("not well-formed", message)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.manifest.exists())
        self.assertEqual(sha(self.src), source_hash)

    def test_structures_without_a_resolvable_mesh_path_have_no_faces_and_requests_are_refused(self):
        cases = {
            "root is not model": build([["4", "8"]], root_open="<notmodel>", root_close="</notmodel>"),
            "unbound prefix on the path": build([["4", "8"]], root_open="<x:model>", root_close="</x:model>", p="x:"),
            "an object that holds no mesh": '<model><resources><object id="1">' + DECOY + "</object></resources></model>",
        }
        for label, document in cases.items():
            with self.subTest(label):
                self.clean_slate()
                make_3mf(self.src, model=document)
                message = self.refusal(self.apply(([0], 1, 2)))
                self.assertIn("not found", message)
                self.assertFalse(self.out.exists())

    def test_the_verifier_refuses_a_rebound_candidate_that_is_not_well_formed(self):
        before = build([["4", "8"]])
        make_3mf(self.src, model=before)
        broken = self.tmp / "broken.3mf"
        make_3mf(broken, model=build([["8", "8"]]).replace("</mesh>", "</mess>"))
        message = self.refusal(self.verify(candidate=broken, manifest=self.rebound(broken, {"0": {"before_token": "4", "after_token": "8"}})))
        self.assertIn("not well-formed", message)

    def test_an_empty_request_list_is_still_a_valid_no_op_on_a_document_with_no_mesh_faces(self):
        make_3mf(self.src, model=build([["4"]], root_open="<notmodel>", root_close="</notmodel>"))
        code, _, err, exc = self.apply()
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)

    def test_the_originals_default_fixture_still_works_end_to_end(self):
        make_3mf(self.src, model=MODEL)
        code, _, err, exc = self.apply(([0], 1, 2), ([2], 3, 1))
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        text = model_text(self.out)
        self.assertIn('v3="2" paint_color="8"/>', text)
        self.assertIn('v3="1" paint_color="4"/>', text)
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)

    # -- documentation -----------------------------------------------------------------------------------------------
    def test_scripts_and_reference_state_structural_face_identity_and_its_limits(self):
        for script in (APPLY_PY, VERIFY_PY):
            doc = " ".join(ast.get_docstring(ast.parse(script.read_text(encoding="utf8"))).lower().split())
            for needle in ("structural path", "mesh faces", "not faces", "well-formed", "read-only", "not a schema"):
                self.assertIn(needle, doc, f"{script.name}: {needle}")
        text = " ".join((CAD_DOCS / "references" / "paint-label-repair.md").read_text(encoding="utf8").lower().split())
        for needle in ("structural path", "mesh faces", "not faces", "well-formed", "document order"):
            self.assertIn(needle, text, f"paint-label-repair.md: {needle}")


class EmptyPrefixedNamespaceTest(TmpCase):
    """Correction 55 (synthetic): a prefix declared with an EMPTY URI (`xmlns:p=""`) is not a namespace binding; XML Namespaces 1.0 forbids it
    and the independent ElementTree oracle rejects such a document. Both helpers' public `mesh_face_starts` must therefore treat a prefixed
    element whose prefix was declared empty as unbound (not a mesh face), exactly like an undeclared prefix, instead of equating it with the
    empty (unqualified) namespace. Valid unprefixed, explicit-empty-default and declared-URI documents keep working. Each public API is
    exercised independently; the verifier negative uses a hand-made candidate and a hash-bound token-only manifest, so it does not depend on the
    applier. Not a general XML validator."""

    BAD = {
        "prefix declared empty on a prefixed root": dict(root_open='<p:model xmlns:p="">', root_close="</p:model>", p="p:"),
        "prefix declared empty on an unprefixed root": dict(root_open='<model xmlns:p="">', p="p:"),
        "empty prefix shadowing a valid outer declaration": dict(root_open='<model xmlns:p="urn:synthetic-outer">', p="p:"),
    }
    GOOD = {
        "unprefixed model (original empty namespace)": dict(),
        "explicit empty default namespace": dict(root_open='<model xmlns="">'),
        "prefix declared with a real URI": dict(root_open=f'<p:model xmlns:p="{CORE}">', root_close="</p:model>", p="p:"),
    }

    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        self.out = self.tmp / "synthetic_out.3mf"
        self.manifest = Path(str(self.out) + ".cleanup.json")

    @staticmethod
    def document(label, paints):
        kwargs = dict(EmptyPrefixedNamespaceTest.BAD.get(label) or EmptyPrefixedNamespaceTest.GOOD[label])
        if label == "empty prefix shadowing a valid outer declaration":  # the shadowing declaration sits on the prefixed `resources` element
            text = build([paints], **kwargs)
            return text.replace("<p:resources>", '<p:resources xmlns:p="">', 1)
        return build([paints], **kwargs)

    def helper_functions(self):
        import runpy  # the helpers are scripts; run_name keeps main() from running
        return {path.name: runpy.run_path(str(path), run_name="helper")["mesh_face_starts"] for path in (APPLY_PY, VERIFY_PY)}

    def test_fixtures_are_what_they_claim_the_oracle_rejects_bad_documents_and_accepts_good_ones(self):
        for label in self.BAD:
            with self.subTest(label):
                with self.assertRaises(ET.ParseError):
                    parse(self.document(label, ["4", "8", "0C"]))
        for label in self.GOOD:
            with self.subTest(label):
                self.assertEqual(len(real_faces(self.document(label, ["4", "8", "0C"]))), 3)

    def test_both_public_mesh_face_starts_functions_treat_an_empty_prefix_uri_as_unbound(self):
        for name, mesh_face_starts in self.helper_functions().items():
            for label in self.BAD:
                with self.subTest(f"{name}: {label}"):
                    self.assertEqual(mesh_face_starts(self.document(label, ["4", "8", "0C"]).encode("utf8")), set())
            for label in self.GOOD:
                with self.subTest(f"{name}: {label}"):
                    self.assertEqual(len(mesh_face_starts(self.document(label, ["4", "8", "0C"]).encode("utf8"))), 3)

    def test_the_applier_cli_refuses_a_document_whose_prefix_was_declared_empty_without_output_and_keeps_the_source(self):
        analysis = self.tmp / "analysis.json"
        analysis.write_text(json.dumps({"candidates": [{"component": 1, "source_label": 1, "target_label": 2, "face_ids": [0]}]}))
        for label in self.BAD:
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                make_3mf(self.src, model=self.document(label, ["4", "8", "0C"]))
                source_hash = sha(self.src)
                code, out, err, exc = _run(APPLY_PY, [self.src, analysis, self.out])
                self.assertIsNone(exc, f"an uncaught {type(exc).__name__} is not an intentional refusal")
                self.assertIsInstance(code, str, f"expected an intentional refusal, got exit {code!r}")
                self.assertFalse(self.out.exists())
                self.assertFalse(self.manifest.exists())
                self.assertEqual(sha(self.src), source_hash)
        for label in self.GOOD:
            with self.subTest(f"control: {label}"):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                make_3mf(self.src, model=self.document(label, ["4", "8", "0C"]))
                code, out, err, exc = _run(APPLY_PY, [self.src, analysis, self.out])
                self.assertIsNone(exc, err)
                self.assertEqual(code, 0)
                self.assertTrue(self.out.exists())

    def test_the_independent_verifier_refuses_a_hand_made_candidate_for_such_a_document_and_accepts_the_valid_controls(self):
        for label in list(self.BAD) + list(self.GOOD):
            with self.subTest(label):
                make_3mf(self.src, model=self.document(label, ["4", "8", "0C"]))
                candidate = self.tmp / "hand-candidate.3mf"
                make_3mf(candidate, model=self.document(label, ["8", "8", "0C"]))  # face 0 relabelled 4 -> 8 by hand, no applier involved
                manifest = self.tmp / "hand-manifest.json"
                manifest.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate),
                                                "changes": {"0": {"before_token": "4", "after_token": "8"}}}))
                before = [Path(p).read_bytes() for p in (self.src, candidate, manifest)]
                code, out, err, exc = _run(VERIFY_PY, [self.src, candidate, manifest])
                self.assertEqual(before, [Path(p).read_bytes() for p in (self.src, candidate, manifest)], "the verifier must not modify its inputs")
                self.assertIsNone(exc, f"an uncaught {type(exc).__name__} is not an intentional refusal")
                if label in self.BAD:
                    self.assertIsInstance(code, str, f"expected an intentional refusal, got exit {code!r}")
                    self.assertEqual(out, "", "nothing may be reported as verified")
                else:
                    self.assertEqual(code, 0, err)
                    self.assertIn('"changed_faces_verified": 1', out)


if __name__ == "__main__":
    unittest.main()
