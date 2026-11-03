"""Standard-library synthetic tests; shared fixtures are not production validators."""
from test_skill_packages import (
    CAD_DOCS,
    CAD_SCRIPTS,
    ET,
    MODEL,
    Path,
    TmpCase,
    _DELETE,
    _run,
    ast,
    json,
    make_3mf,
    make_symlink,
    mock,
    model_text,
    os,
    re,
    repack,
    sha,
    unittest,
    zipfile,
)


class PaintHelperTest(TmpCase):
    apply_py = CAD_SCRIPTS / "apply_reviewed_paint_cleanup.py"
    verify_py = CAD_SCRIPTS / "verify_3mf_paint_cleanup.py"

    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        make_3mf(self.src)
        self.out = self.tmp / "synthetic_out.3mf"
        self.manifest = Path(str(self.out) + ".cleanup.json")

    def analysis(self, candidates):
        p = self.tmp / "analysis.json"
        p.write_text(json.dumps({"candidates": candidates}))
        return p

    def apply(self, candidates, *extra, out=None):
        return _run(self.apply_py, [self.src, self.analysis(candidates), out or self.out, *extra])

    def verify(self, candidate=None, manifest=None):
        return _run(self.verify_py, [self.src, candidate or self.out, manifest or self.manifest])

    def cand(self, faces, s, t, component=1):
        return {"component": component, "source_label": s, "target_label": t, "face_ids": faces}

    def bound(self, candidate, manifest=None, source=None):
        """Manifest copy whose artifact hashes match the given (possibly tampered) files.

        Deeper tamper tests use this so the hash binding passes and the test still
        reaches (and exercises) the guard it is about; hash failures have their own tests.
        """
        m = json.loads(Path(manifest or self.manifest).read_text())
        m["source_sha256"] = sha(source or self.src)
        m["output_sha256"] = sha(candidate)
        p = self.tmp / ("bound-" + Path(candidate).name + ".json")
        p.write_text(json.dumps(m))
        return p

    # -- valid paths ---------------------------------------------------
    def test_apply_then_verify_valid(self):
        before = sha(self.src)
        code, out, err, exc = self.apply([self.cand([0], 1, 2), self.cand([2], 3, 1, component=2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        text = model_text(self.out)
        self.assertIn('v3="2" paint_color="8"/>', text)  # face 0: 1 -> 2
        self.assertIn('v3="1" paint_color="4"/>', text)  # face 2: 3 -> 1
        self.assertEqual(sha(self.src), before, "source must stay untouched")
        m = json.loads(self.manifest.read_text())
        self.assertEqual(m["changed_faces"], 2)
        self.assertEqual(m["triangle_count"], 4)
        code, out, err, exc = self.verify()
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertIn('"changed_faces_verified": 2', out)

    def test_noop_candidates_leave_model_identical(self):
        code, _, err, exc = self.apply([])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertEqual(model_text(self.out), MODEL)
        self.assertEqual(json.loads(self.manifest.read_text())["changed_faces"], 0)
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0)
        self.assertIn('"changed_faces_verified": 0', out)

    def test_expected_hash_accepted_when_correct(self):
        code, _, err, exc = self.apply([self.cand([0], 1, 2)], "--expected-input-sha256", sha(self.src))
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)

    # -- intended refusals of the applier -------------------------------
    def assert_refused(self, result, text):
        code, _, _, exc = result
        msg = code if isinstance(code, str) else str(exc)
        self.assertTrue(isinstance(code, str) or exc is not None, "expected a refusal")
        self.assertIn(text, msg)
        self.assertFalse(self.out.exists(), "no output may be written on refusal")

    def test_refuses_to_overwrite_source(self):
        code, _, _, _ = _run(self.apply_py, [self.src, self.analysis([]), self.src])
        self.assertIn("Refusing to overwrite the source", code)

    def test_refuses_existing_output(self):
        self.out.write_bytes(b"existing")
        code, _, _, _ = self.apply([])
        self.assertIn("Refusing to overwrite existing output", code)
        self.assertEqual(self.out.read_bytes(), b"existing")

    def test_refuses_wrong_expected_hash(self):
        self.assert_refused(self.apply([], "--expected-input-sha256", "0" * 64), "Input hash mismatch")

    def test_refuses_unsupported_label(self):
        self.assert_refused(self.apply([self.cand([0], 1, 5)]), "Unsupported label mapping")

    def test_refuses_source_label_mismatch(self):
        self.assert_refused(self.apply([self.cand([1], 1, 2)]), "source mismatch")  # face 1 is label 2

    def test_refuses_split_token_source(self):
        split = MODEL.replace('paint_color="0C"', 'paint_color="0C0"')
        make_3mf(self.src, model=split)
        self.assert_refused(self.apply([self.cand([2], 3, 1)]), "source mismatch")

    def test_refuses_unknown_face(self):
        self.assert_refused(self.apply([self.cand([99], 1, 2)]), "Requested face IDs not found")

    def test_refuses_conflicting_requests(self):
        self.assert_refused(self.apply([self.cand([0], 1, 2), self.cand([0], 1, 3)]), "Conflicting relabel")

    def test_refuses_two_object_models(self):
        make_3mf(self.src, second_model=True)
        self.assert_refused(self.apply([]), "Expected exactly one object model")

    def test_refuses_requested_unpainted_face_whose_inherited_label_is_unknown(self):
        # face 3 has no paint_color: it inherits a base extruder this tool cannot know
        for source_label in (1, 2):
            with self.subTest(claimed_source_label=source_label):
                self.assert_refused(self.apply([self.cand([3], source_label, 3)]), "paint_color")

    def test_unrequested_unpainted_face_keeps_its_exact_bytes(self):
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertIn('<triangle v1="1" v2="2" v3="3"/>', model_text(self.out))
        code, _, _, exc = self.verify()
        self.assertEqual(code, 0)

    def test_refuses_existing_sidecar_and_preserves_it(self):
        self.manifest.write_bytes(b"previous manifest bytes")
        before = sha(self.src)
        self.assert_refused(self.apply([self.cand([0], 1, 2)]), "sidecar")
        self.assertEqual(self.manifest.read_bytes(), b"previous manifest bytes")
        self.assertEqual(sha(self.src), before)
        # control: once the sidecar is gone the same explicit request works
        self.manifest.unlink()
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertTrue(self.manifest.exists())

    @unittest.skipUnless(Path("/proc/self/fd").is_dir(), "needs /proc/self/fd")
    def test_apply_closes_its_temporary_descriptor(self):
        def count():
            return len(list(Path("/proc/self/fd").iterdir()))

        before = count()
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertEqual(count(), before, "a file descriptor leaked")

    def test_refuses_identity_request_before_writing(self):
        self.assert_refused(self.apply([self.cand([0], 1, 1)]), "dentity")
        self.assertFalse(self.manifest.exists())

    # -- request identifiers: nonnegative JSON integers, never normalised ------
    def test_refuses_non_integer_request_identifiers_without_normalising_them(self):
        base = {"component": 1, "source_label": 1, "target_label": 2, "face_ids": [0]}
        cases = [  # (field, supplied literal, reason that must be named)
            ("face_ids", [0.5], "nonnegative JSON integer"),  # int() would truncate this to face 0
            ("face_ids", [1.0], "nonnegative JSON integer"),
            ("face_ids", [True], "nonnegative JSON integer"),  # bool is not an integer here (True == 1)
            ("face_ids", ["0"], "nonnegative JSON integer"),
            ("face_ids", [None], "nonnegative JSON integer"),
            ("face_ids", [-1], "nonnegative JSON integer"),
            ("face_ids", "012", "list"),  # a string would otherwise iterate as the ids 0, 1, 2
            ("source_label", 1.9, "JSON integer"),  # int() would truncate this to label 1
            ("source_label", True, "JSON integer"),
            ("source_label", "1", "JSON integer"),
            ("target_label", 2.5, "JSON integer"),
            ("target_label", True, "JSON integer"),
            ("target_label", "2", "JSON integer"),
            ("component", 1.5, "nonnegative JSON integer"),
            ("component", False, "nonnegative JSON integer"),
            ("component", "1", "nonnegative JSON integer"),
            ("component", -1, "nonnegative JSON integer"),
        ]
        before = sha(self.src)
        for field, value, reason in cases:
            with self.subTest(field=field, value=repr(value)):
                for leftover in (self.out, self.manifest):  # clean slate: a wrongly accepted earlier case must not mask this one
                    leftover.unlink(missing_ok=True)
                msg = self.refusal(self.apply([dict(base, **{field: value})]))
                self.assertIn(field, msg)
                self.assertIn(reason, msg)
                self.assertFalse(self.out.exists(), "no output may be written")
                self.assertFalse(self.manifest.exists(), "no sidecar may be written")
                self.assertEqual(sha(self.src), before)

    def test_refuses_malformed_candidate_structure_with_a_named_reason(self):
        self.assertIn("missing", self.refusal(self.apply([{"source_label": 1, "target_label": 2, "face_ids": [0]}])))
        self.assertFalse(self.out.exists())
        p = self.tmp / "analysis-not-a-list.json"
        p.write_text(json.dumps({"candidates": {"component": 1}}))
        msg = self.refusal(_run(self.apply_py, [self.src, p, self.out]))
        self.assertIn("candidates", msg)
        self.assertIn("list", msg)

    def test_integer_identifiers_apply_and_verify_including_zero_based_face_and_component(self):
        code, _, err, exc = self.apply([self.cand([0], 1, 2, component=0)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        m = json.loads(self.manifest.read_text())
        self.assertEqual(sorted(m["changes"]), ["0"])
        self.assertEqual(m["component_ids"], [0])
        self.assertIn('v3="2" paint_color="8"/>', model_text(self.out))
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 1', out)

    def test_no_temporary_files_remain_after_a_successful_apply(self):
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertFalse([p.name for p in self.tmp.iterdir() if p.name.endswith(".tmp")])

    # -- symlinks at the output and sidecar leaf are refused, never followed ----
    # Everything lives in the task-owned temp root: a work directory (where output/sidecar are
    # asked for) and a separate "unrelated" directory (where a link points). The unrelated
    # directory must stay exactly as it was.
    def link_fixture(self):
        work, other = self.tmp / "workspace", self.tmp / "unrelated"
        work.mkdir()
        other.mkdir()
        return work, other

    def test_refuses_dangling_or_live_output_symlink_without_touching_its_target(self):
        work, other = self.link_fixture()
        live = other / "existing-file"
        live.write_bytes(b"unrelated bytes")
        cases = {"dangling": other / "must-not-be-created", "live": live, "source": self.src}
        before = sha(self.src)
        for label, target in cases.items():
            with self.subTest(label):
                out = work / f"{label}.3mf"
                make_symlink(out, target)
                msg = self.refusal(self.apply([self.cand([0], 1, 2)], out=out))
                self.assertIn("symlink", msg)
                self.assertTrue(out.is_symlink(), "the link itself is left alone")
                self.assertEqual(os.readlink(out), str(target))
                self.assertFalse((work / f"{label}.3mf.cleanup.json").exists() or (work / f"{label}.3mf.cleanup.json").is_symlink())
                self.assertEqual(sha(self.src), before)
        self.assertEqual(live.read_bytes(), b"unrelated bytes")
        self.assertEqual(sorted(p.name for p in other.iterdir()), ["existing-file"], "nothing was created at an unrelated location")

    def test_refuses_dangling_or_live_sidecar_symlink_before_writing_anything(self):
        work, other = self.link_fixture()
        live = other / "existing-file"
        live.write_bytes(b"unrelated bytes")
        before = sha(self.src)
        for label, target in {"dangling": other / "must-not-be-created", "live": live}.items():
            with self.subTest(label):
                out = work / f"{label}.3mf"
                side = work / f"{label}.3mf.cleanup.json"
                make_symlink(side, target)
                msg = self.refusal(self.apply([self.cand([0], 1, 2)], out=out))
                self.assertIn("sidecar", msg)
                self.assertFalse(out.exists() or out.is_symlink(), "no archive may be written when the sidecar is blocked")
                self.assertTrue(side.is_symlink())
                self.assertEqual(os.readlink(side), str(target))
                self.assertEqual(sha(self.src), before)
        self.assertEqual(live.read_bytes(), b"unrelated bytes")
        self.assertEqual(sorted(p.name for p in other.iterdir()), ["existing-file"])

    def test_after_a_symlink_refusal_the_same_fixture_applies_and_verifies_cleanly(self):
        work, other = self.link_fixture()
        out = work / "result.3mf"
        side = work / "result.3mf.cleanup.json"
        make_symlink(out, other / "must-not-be-created")
        self.assertIn("symlink", self.refusal(self.apply([self.cand([0], 1, 2)], out=out)))
        out.unlink()
        make_symlink(side, other / "must-not-be-created")
        self.assertIn("sidecar", self.refusal(self.apply([self.cand([0], 1, 2)], out=out)))
        side.unlink()
        code, _, err, exc = self.apply([self.cand([0], 1, 2)], out=out)  # valid integer request, ordinary files
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertTrue(out.is_file() and not out.is_symlink() and side.is_file() and not side.is_symlink())
        code, _, _, exc = _run(self.verify_py, [self.src, out, side])
        self.assertEqual(code, 0, exc)
        self.assertEqual(list(other.iterdir()), [], "the unrelated directory was never touched")

    def test_sidecar_is_created_exclusively_even_if_the_upfront_check_is_fooled(self):
        # Not a concurrency simulation: the up-front existence check is made to miss a dangling sidecar
        # link, to show that the creation itself refuses to follow or reuse an existing entry.
        work, other = self.link_fixture()
        out = work / "result.3mf"
        side = work / "result.3mf.cleanup.json"
        make_symlink(side, other / "must-not-be-created")
        real = os.path.lexists
        fooled = lambda p: False if str(p).endswith(".cleanup.json") else real(p)
        with mock.patch.object(os.path, "lexists", side_effect=fooled), mock.patch.object(Path, "exists", lambda self_: False if str(self_).endswith(".cleanup.json") else os.path.exists(self_)):
            msg = self.refusal(self.apply([self.cand([0], 1, 2)], out=out))
        self.assertIn("sidecar", msg)
        self.assertTrue(side.is_symlink())
        self.assertEqual(list(other.iterdir()), [], "the link target was not created")

    def test_an_ordinary_symlinked_source_or_parent_directory_is_not_a_new_prohibition(self):
        work, other = self.link_fixture()
        src_link = self.tmp / "source-link.3mf"
        make_symlink(src_link, self.src)
        work_link = self.tmp / "workspace-link"
        make_symlink(work_link, work, directory=True)
        out = work_link / "result.3mf"
        code, _, err, exc = _run(self.apply_py, [src_link, self.analysis([self.cand([0], 1, 2)]), out])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertTrue((work / "result.3mf").is_file() and (work / "result.3mf.cleanup.json").is_file())
        self.assertEqual(list(other.iterdir()), [])

    # -- strict JSON ingestion: duplicate keys and non-finite constants are refused --------
    def raw_analysis(self, text):
        p = self.tmp / "raw-analysis.json"
        p.write_text(text)
        return p

    def test_applier_refuses_duplicate_object_keys_in_the_analysis_instead_of_picking_one(self):
        cases = {
            "duplicate source_label (the controller's repro)": '{"candidates":[{"component":1,"source_label":2,"source_label":1,"target_label":2,"face_ids":[0]}]}',
            "duplicate face_ids": '{"candidates":[{"component":1,"source_label":1,"target_label":2,"face_ids":[0],"face_ids":[3]}]}',
            "duplicate top-level candidates": '{"candidates":[], "candidates":[]}',
        }
        before = sha(self.src)
        for label, text in cases.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                msg = self.refusal(_run(self.apply_py, [self.src, self.raw_analysis(text), self.out]))
                self.assertIn("Duplicate JSON object key", msg)
                self.assertFalse(self.out.exists() or self.manifest.exists(), "nothing is written")
                self.assertEqual(sha(self.src), before)

    def test_applier_refuses_non_finite_json_constants(self):
        for const in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(const):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                msg = self.refusal(_run(self.apply_py, [self.src, self.raw_analysis('{"candidates": [], "note": %s}' % const), self.out]))
                self.assertIn("Non-finite", msg)
                self.assertFalse(self.out.exists() or self.manifest.exists())

    def edited_manifest(self, mutate=None, raw=None):
        """A copy of the apply-written manifest (hash-bound to self.out) with a structural edit."""
        for leftover in (self.out, self.manifest):  # clean slate: a wrongly accepted earlier subcase must not mask this one
            leftover.unlink(missing_ok=True)
        self.make_valid_output()
        if raw is not None:
            text = raw(self.manifest.read_text())
        else:
            m = json.loads(self.manifest.read_text())
            mutate(m)
            text = json.dumps(m)
        p = self.tmp / "edited-manifest.json"
        p.write_text(text)
        return p

    def test_verifier_refuses_duplicate_object_keys_in_the_manifest_including_nested_ones(self):
        cases = {
            "top level": lambda t: t.replace('"changed_faces": 1,', '"changed_faces": 99,\n  "changed_faces": 1,'),
            "inside a change record": lambda t: t.replace('"source_label": 1,', '"source_label": 4,\n      "source_label": 1,'),
            "duplicate face key": lambda t: t.replace('"changes": {', '"changes": {\n    "0": {"before_token": "9"},'),
        }
        for label, raw in cases.items():
            with self.subTest(label):
                p = self.edited_manifest(raw=raw)
                self.assertIn("Duplicate JSON object key", self.refusal(self.verify(manifest=p)))
                self.out.unlink(missing_ok=True)
                self.manifest.unlink(missing_ok=True)

    def test_verifier_refuses_non_finite_json_constants_in_the_manifest(self):
        p = self.edited_manifest(raw=lambda t: t.replace('"changed_faces": 1,', '"changed_faces": NaN,'))
        self.assertIn("Non-finite", self.refusal(self.verify(manifest=p)))

    def test_verifier_requires_canonical_decimal_face_keys_and_does_not_normalise_aliases(self):
        for alias in ("00", "+0", " 0", "0 ", "0_0", "-0", "٠"):
            with self.subTest(alias=repr(alias)):
                p = self.edited_manifest(mutate=lambda m, a=alias: m["changes"].__setitem__(a, m["changes"].pop("0")))
                self.assertIn("canonical", self.refusal(self.verify(manifest=p)))
                self.out.unlink(missing_ok=True)
                self.manifest.unlink(missing_ok=True)

    # -- optional label fields, when present, must agree with the recorded tokens -----------
    def label_manifest(self, **fields):
        def mutate(m):
            for key, value in fields.items():
                if value is _DELETE:
                    m["changes"]["0"].pop(key, None)
                else:
                    m["changes"]["0"][key] = value
        return self.edited_manifest(mutate=mutate)

    def test_verifier_refuses_label_fields_that_contradict_the_recorded_tokens(self):
        # face 0 is relabelled 1 ("4") -> 2 ("8")
        cases = {
            "source_label contradicts before_token": ({"source_label": 4}, "source_label"),
            "target_label contradicts after_token": ({"target_label": 3}, "target_label"),
            "bool is not an integer label": ({"source_label": True}, "JSON integer"),
            "float label": ({"target_label": 2.0}, "JSON integer"),
            "string label": ({"source_label": "1"}, "JSON integer"),
            "null label": ({"target_label": None}, "JSON integer"),
            "label zero": ({"source_label": 0}, "1..4"),
            "label five": ({"target_label": 5}, "1..4"),
        }
        for label, (fields, needle) in cases.items():
            with self.subTest(label):
                p = self.label_manifest(**fields)
                msg = self.refusal(self.verify(manifest=p))
                self.assertIn(needle, msg)
                self.out.unlink(missing_ok=True)
                self.manifest.unlink(missing_ok=True)

    def test_verifier_still_accepts_token_only_records_and_consistent_labels(self):
        for label, fields in {
            "apply-written labels as they are": {},
            "token-only record (no label fields)": {"source_label": _DELETE, "target_label": _DELETE},
            "only a consistent source_label": {"source_label": 1, "target_label": _DELETE},
            "only a consistent target_label": {"source_label": _DELETE, "target_label": 2},
        }.items():
            with self.subTest(label):
                p = self.label_manifest(**fields)
                code, out, _, exc = self.verify(manifest=p)
                self.assertEqual(code, 0, exc)
                self.assertIn('"changed_faces_verified": 1', out)
                self.out.unlink(missing_ok=True)
                self.manifest.unlink(missing_ok=True)

    # -- only the paint VALUE bytes change; spacing, name and quotes around it are preserved -------
    SPACINGS = {
        "several spaces": "   ",
        "a tab": "\t",
        "space tab space": " \t ",
        "newline and indent": "\n      ",
    }

    def spaced_source(self, gap):
        model = MODEL.replace(' paint_color="4"', gap + 'paint_color="4"', 1)
        self.assertNotEqual(model, MODEL)
        make_3mf(self.src, model=model)
        return model

    def test_applier_changes_only_the_paint_value_bytes_and_keeps_arbitrary_spacing(self):
        for label, gap in self.SPACINGS.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                model = self.spaced_source(gap)
                before = sha(self.src)
                code, _, err, exc = self.apply([self.cand([0], 1, 2)])
                self.assertIsNone(exc, err)
                self.assertEqual(code, 0)
                # exactly the requested value changed: the whitespace before the attribute is untouched
                self.assertEqual(model_text(self.out), model.replace('paint_color="4"', 'paint_color="8"', 1))
                self.assertEqual(sha(self.src), before, "the source stays immutable")
                code, out, _, exc = self.verify()  # a real value-only edit with unchanged arbitrary spacing is accepted
                self.assertEqual(code, 0, exc)
                self.assertIn('"changed_faces_verified": 1', out)

    def hand_manifest(self, candidate):
        """A token-only record for face 0 (4 -> 8), hash-bound to the source and the given candidate, written
        by hand so these verifier tests do not depend on how the applier happens to format its output."""
        p = self.tmp / f"hand-{Path(candidate).stem}.json"
        p.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate), "changes": {"0": {"before_token": "4", "after_token": "8"}}}))
        return p

    def test_verifier_rejects_changed_spacing_even_when_the_archive_hash_and_manifest_are_rebound(self):
        for label, gap in self.SPACINGS.items():
            with self.subTest(label):
                self.spaced_source(gap)
                slug = label.replace(" ", "-")
                # control: the same value edit with the source spacing untouched is accepted
                good = self.tmp / f"value-only-{slug}.3mf"
                repack(self.src, good, {"3D/Objects/object_1.model": lambda b, g=gap: b.replace(g.encode() + b'paint_color="4"', g.encode() + b'paint_color="8"', 1)})
                code, _, _, exc = self.verify(candidate=good, manifest=self.hand_manifest(good))
                self.assertEqual(code, 0, exc)
                # tamper: the value edit also changes the spacing before the attribute; hashes and manifest are correct
                bad = self.tmp / f"respaced-{slug}.3mf"
                repack(self.src, bad, {"3D/Objects/object_1.model": lambda b, g=gap: b.replace(g.encode() + b'paint_color="4"', b' paint_color="8"', 1)})
                self.assertNotEqual(sha(bad), sha(good))
                msg = self.refusal(self.verify(candidate=bad, manifest=self.hand_manifest(bad)))  # only the XML guard can speak
                self.assertIn("outside paint_color", msg)
                self.assertNotIn("hash mismatch", msg)

    def test_verifier_rejects_a_value_edit_that_also_moves_other_bytes_in_the_tag(self):
        self.make_valid_output()
        bad = self.tmp / "tag-tail-changed.3mf"
        repack(self.out, bad, {"3D/Objects/object_1.model": lambda b: b.replace(b'v3="2" paint_color="8"/>', b'v3="2" paint_color="8" />', 1)})
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=bad, manifest=self.bound(bad))))

    # -- the REAL paint_color attribute, not paint-looking text (correction 16) ----------------------------
    # ElementTree is only the independent TEST oracle: it reports the attributes a real XML parser sees, so these
    # tests do not rely on the helpers agreeing with each other. Synthetic XML only; not a slicer or 3MF-schema claim.
    NS = "urn:synthetic-probe"
    FACE0_PLAIN = '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'
    FACE3_PLAIN = '<triangle v1="1" v2="2" v3="3"/>'
    FAKE_NOTE = 'a paint_color="4"'  # text that merely LOOKS like a paint attribute

    @staticmethod
    def face(base_attrs, note=None, after=False, paint=None):
        """A <triangle> start tag; the optional probe:note attribute (single-quoted) sits before or after the others."""
        attrs = [base_attrs] + ([paint] if paint else [])
        if note is not None:
            attrs.insert(len(attrs) if after else 0, "probe:note='" + note + "'")
        return "<triangle " + " ".join(attrs) + "/>"

    def face0(self, note=None, after=False, paint='paint_color="@P@"'):
        return self.face('v1="0" v2="1" v3="2"', note, after, paint)

    def face3(self, note=None):
        return self.face('v1="1" v2="2" v3="3"', note)

    def probe_model(self, face0=None, face3=None):
        model = MODEL.replace("<model>", f'<model xmlns:probe="{self.NS}">', 1)
        for old, new in ((self.FACE0_PLAIN, face0), (self.FACE3_PLAIN, face3)):
            if new is not None:
                self.assertIn(old, model)
                model = model.replace(old, new, 1)
        return model

    @staticmethod
    def oracle(text):
        """(attribute dict of every real <triangle> element, [(tag, attributes)] of every other element), as an XML parser sees them."""
        triangles, others = [], []
        for element in ET.fromstring(text).iter():
            if element.tag.rsplit("}", 1)[-1] == "triangle":  # local name, so a default namespace does not hide the faces
                triangles.append(dict(element.attrib))
            else:
                others.append((element.tag, dict(element.attrib)))
        return triangles, others

    def assert_only_paint_values_changed(self, before, after, changes):
        """changes = {real triangle index: (old, new)}: those paint_color attributes changed, nothing else did."""
        triangles_before, others_before = self.oracle(before)
        triangles_after, others_after = self.oracle(after)
        self.assertEqual(others_after, others_before, "no non-triangle element or attribute may change")
        self.assertEqual(len(triangles_after), len(triangles_before))
        for index, (x, y) in enumerate(zip(triangles_before, triangles_after)):
            expected = dict(x)
            if index in changes:
                old, new = changes[index]
                self.assertEqual(x.get("paint_color"), old, f"fixture: face {index} must really carry paint_color {old}")
                expected["paint_color"] = new
            self.assertEqual(y, expected, f"face {index}: every real attribute must be exactly as expected")

    def assert_clean_refusal(self, result, text, source_hash):
        message = self.refusal(result)
        self.assertIn(text, message)
        self.assertFalse(self.out.exists(), "a refusal must not leave an output archive")
        self.assertFalse(self.manifest.exists(), "a refusal must not leave a sidecar")
        self.assertEqual(sha(self.src), source_hash, "the source stays untouched")
        self.assertEqual(list(self.tmp.glob("*.tmp")), [], "no temporary file may remain")
        return message

    def rebound(self, candidate, changes):
        """Hand-written manifest bound to the exact source and candidate bytes (so only the XML guards can speak)."""
        p = self.tmp / f"rebound-{Path(candidate).stem}.json"
        p.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate), "changes": changes}))
        return p

    FACE0_4_TO_8 = {"0": {"before_token": "4", "after_token": "8"}}

    def candidate_from(self, model, name):
        path = self.tmp / name
        make_3mf(path, model=model)
        return path

    @staticmethod
    def slug(text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def apply_and_check_value_only(self, template):
        """Apply face 0 label 1->2 to a source built from the template ('@P@' = paint); the output must equal the
        source with exactly the real value changed (text AND parser view); then the verifier must accept it."""
        before = self.probe_model(face0=template.replace("@P@", "4"))
        make_3mf(self.src, model=before)
        source_hash = sha(self.src)
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0, "a supported form must be edited, not refused")
        after = model_text(self.out)
        self.assert_only_paint_values_changed(before, after, {0: ("4", "8")})
        self.assertEqual(after, self.probe_model(face0=template.replace("@P@", "8")), "only the value bytes may differ")
        self.assertEqual(sha(self.src), source_hash)
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 1', out)

    def test_applier_edits_the_real_paint_attribute_when_paint_looking_text_sits_in_an_earlier_attribute(self):
        notes = {
            "paint-looking note": self.FAKE_NOTE,
            "paint-looking note with tag delimiters": 'x /> y > paint_color="4"',
            "tag delimiters only": "a > b",
        }
        for label, note in notes.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                self.apply_and_check_value_only(self.face0(note))

    def test_control_paint_looking_text_after_the_real_attribute_is_left_alone(self):
        notes = {"paint-looking note": self.FAKE_NOTE, "tag delimiters after the real attribute": 'x /> y > paint_color="4"'}
        for label, note in notes.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                self.apply_and_check_value_only(self.face0(note, after=True))

    def test_a_face_without_a_paint_attribute_is_not_made_painted_by_paint_looking_text(self):
        model = self.probe_model(face3=self.face3(note=self.FAKE_NOTE))
        self.assertNotIn("paint_color", self.oracle(model)[0][3], "fixture: the parser sees an unpainted face")
        make_3mf(self.src, model=model)
        source_hash = sha(self.src)
        self.assert_clean_refusal(self.apply([self.cand([3], 1, 2)]), "no paint_color", source_hash)
        # control: the very same file still relabels the really painted face
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assert_only_paint_values_changed(model, model_text(self.out), {0: ("4", "8")})

    def test_verifier_does_not_treat_an_edited_note_on_an_unpainted_face_as_a_paint_change(self):
        make_3mf(self.src, model=self.probe_model(face3=self.face3(note=self.FAKE_NOTE)))
        self.assertNotIn("paint_color", self.oracle(self.probe_model(face3=self.face3(note=self.FAKE_NOTE)))[0][3], "fixture: the parser sees an unpainted face")
        edited = self.candidate_from(self.probe_model(face3=self.face3(note='a paint_color="8"')), "note-edited.3mf")
        message = self.refusal(self.verify(candidate=edited, manifest=self.rebound(edited, {"3": {"before_token": "4", "after_token": "8"}})))
        self.assertIn("outside paint_color", message)

    def test_verifier_does_not_treat_an_edited_note_as_the_requested_paint_change(self):
        template = self.face0(self.FAKE_NOTE)
        make_3mf(self.src, model=self.probe_model(face0=template.replace("@P@", "4")))
        # only the note moves 4 -> 8; the REAL attribute stays 4, yet the hand-written manifest claims face 0 went 4 -> 8
        note_only = self.candidate_from(self.probe_model(face0=self.face0('a paint_color="8"', paint='paint_color="4"')), "note-only.3mf")
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=note_only, manifest=self.rebound(note_only, self.FACE0_4_TO_8))))

    def test_verifier_accepts_the_real_value_only_edit_in_a_tag_whose_earlier_attribute_looks_like_paint(self):
        make_3mf(self.src, model=self.probe_model(face0=self.face0(self.FAKE_NOTE).replace("@P@", "4")))
        good = self.candidate_from(self.probe_model(face0=self.face0(self.FAKE_NOTE).replace("@P@", "8")), "value-only.3mf")
        code, out, _, exc = self.verify(candidate=good, manifest=self.rebound(good, self.FACE0_4_TO_8))
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 1', out)

    def test_control_verifier_refuses_note_and_other_attribute_edits_in_a_noted_tag(self):
        make_3mf(self.src, model=self.probe_model(face0=self.face0(self.FAKE_NOTE).replace("@P@", "4")))
        both =self.candidate_from(self.probe_model(face0=self.face0('a paint_color="8"', paint='paint_color="8"')), "note-and-value.3mf")
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=both, manifest=self.rebound(both, self.FACE0_4_TO_8))))
        other = self.candidate_from(self.probe_model(face0=self.face0(self.FAKE_NOTE).replace("@P@", "8").replace('v2="1"', 'v2="3"')), "other-attribute.3mf")
        self.assertIn("outside paint_color", self.refusal(self.verify(candidate=other, manifest=self.rebound(other, self.FACE0_4_TO_8))))

    def test_only_elements_named_exactly_triangle_count_as_faces(self):
        extra = '<triangle-extra v1="0" v2="1" v3="2" paint_color="4"/>'
        before = MODEL.replace(self.FACE0_PLAIN, extra + self.FACE0_PLAIN, 1)
        self.assertEqual(len(self.oracle(before)[0]), 4, "fixture: the parser sees four real triangles")
        make_3mf(self.src, model=before)
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        after = model_text(self.out)
        self.assert_only_paint_values_changed(before, after, {0: ("4", "8")})
        self.assertEqual(after, before.replace(self.FACE0_PLAIN, self.FACE0_PLAIN.replace('"4"', '"8"'), 1), "the lookalike element keeps its bytes")
        code, _, _, exc = self.verify()
        self.assertEqual(code, 0, exc)

    def test_control_only_the_exact_attribute_name_paint_color_is_a_paint_attribute(self):
        for name in ("probe:paint_color", "data-paint_color", "xpaint_color", "Paint_Color"):
            with self.subTest(name):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                model = self.probe_model(face3=f'<triangle v1="1" v2="2" v3="3" {name}="4"/>')
                self.assertNotIn("paint_color", self.oracle(model)[0][3], "fixture: the parser sees no paint_color attribute")
                make_3mf(self.src, model=model)
                self.assert_clean_refusal(self.apply([self.cand([3], 1, 2)]), "no paint_color", sha(self.src))
                # the verifier treats the lookalike as ordinary bytes: editing it is not a paint change
                edited = self.candidate_from(model.replace(f'{name}="4"', f'{name}="8"'), f"edited-{self.slug(name)}.3mf")
                self.assertIn("outside paint_color", self.refusal(self.verify(candidate=edited, manifest=self.rebound(edited, {}))))

    def test_value_only_edit_keeps_single_quotes_and_spacing_around_the_equals_sign(self):
        forms = {
            "single-quoted value": "paint_color='@P@'",
            "spaces around the equals sign": 'paint_color = "@P@"',
            "tab and newline around the equals sign": 'paint_color\t=\n"@P@"',
        }
        for label, form in forms.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                self.apply_and_check_value_only(self.face0(paint=form))
                # a rebound candidate that rewrites the quotes/spacing instead of only the value is refused
                normal = self.candidate_from(self.probe_model(face0=self.face0(paint='paint_color="@P@"').replace("@P@", "8")), f"normalised-{self.slug(label)}.3mf")
                self.assertIn("outside paint_color", self.refusal(self.verify(candidate=normal, manifest=self.rebound(normal, self.FACE0_4_TO_8))))

    UNSUPPORTED = {
        "a raw less-than sign inside a quoted value": lambda m: m.replace('<triangle v1="0" v2="1" v3="2" paint_color="4"/>', '<triangle probe:note=\'a < b\' v1="0" v2="1" v3="2" paint_color="4"/>', 1),
        "a start tag hidden inside a quoted value": lambda m: m.replace('<triangle v1="0" v2="1" v3="2" paint_color="4"/>', '<triangle probe:note=\'<triangle v1="9" v2="9" v3="9" paint_color="4"/>\' v1="0" v2="1" v3="2" paint_color="4"/>', 1),
        "a duplicate paint_color attribute": lambda m: m.replace('paint_color="4"/>', 'paint_color="4" paint_color="8"/>', 1),
        "an unquoted attribute value": lambda m: m.replace('<triangle v1="0" v2="1"', "<triangle v1=0 v2=\"1\"", 1),
        "no whitespace between attributes": lambda m: m.replace('<triangle v1="0" v2="1"', '<triangle v1="0"v2="1"', 1),
        "an unterminated start tag": lambda m: m.replace('<triangle v1="0" v2="1" v3="2" paint_color="4"/>', '<triangle v1="0" v2="1" v3="2" paint_color="4"', 1),
        "a malformed tag that is not a triangle": lambda m: m.replace('<vertex x="0" y="0" z="0"/>', '<vertex x="0" y="0" z=0/>', 1),
    }

    def test_applier_refuses_unsupported_xml_syntax_by_name_before_writing_anything(self):
        for label, mutate in self.UNSUPPORTED.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):  # clean slate: an earlier (wrongly accepted) subcase must not mask this one
                    leftover.unlink(missing_ok=True)
                model = mutate(MODEL.replace("<model>", f'<model xmlns:probe="{self.NS}">', 1))
                self.assertNotEqual(model, MODEL)
                make_3mf(self.src, model=model)
                self.assert_clean_refusal(self.apply([self.cand([0], 1, 2)]), "Unsupported XML syntax", sha(self.src))

    def test_verifier_refuses_the_same_unsupported_xml_syntax_even_with_a_rebound_manifest(self):
        for label in ("a raw less-than sign inside a quoted value", "a duplicate paint_color attribute", "an unquoted attribute value"):
            with self.subTest(label):
                model = self.UNSUPPORTED[label](MODEL.replace("<model>", f'<model xmlns:probe="{self.NS}">', 1))
                make_3mf(self.src, model=model)
                edited = self.candidate_from(model.replace('paint_color="4"', 'paint_color="8"', 1), f"unsupported-{self.slug(label)}.3mf")
                self.assertIn("Unsupported XML syntax", self.refusal(self.verify(candidate=edited, manifest=self.rebound(edited, self.FACE0_4_TO_8))))

    def test_control_ordinary_whole_face_relabel_changes_only_the_requested_paint_values(self):
        make_3mf(self.src, model=MODEL)
        code, _, err, exc = self.apply([self.cand([0], 1, 2), self.cand([2], 3, 1, component=2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        after = model_text(self.out)
        self.assert_only_paint_values_changed(MODEL, after, {0: ("4", "8"), 2: ("0C", "4")})
        self.assertEqual(after, MODEL.replace('v3="2" paint_color="4"', 'v3="2" paint_color="8"', 1).replace('v3="1" paint_color="0C"', 'v3="1" paint_color="4"', 1))
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 2', out)

    def test_a_large_quoted_value_with_many_delimiters_and_many_faces_is_handled_exactly(self):
        note = 'a > b /> paint_color="4" ' * 20000
        extra = '<triangle v1="0" v2="1" v3="2" paint_color="8"/>' * 3000
        template = self.face0(note)
        before = self.probe_model(face0=template.replace("@P@", "4")).replace("</triangles>", extra + "</triangles>", 1)
        make_3mf(self.src, model=before)
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        after = model_text(self.out)
        self.assertEqual(after, before.replace('paint_color="4"/>', 'paint_color="8"/>', 1), "the edit is the one real value and nothing else")
        self.assert_only_paint_values_changed(before, after, {0: ("4", "8")})
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 1', out)

    def test_control_a_realistic_shaped_model_with_crlf_namespaces_and_text_content_still_applies_and_verifies(self):
        # Added after the fix as a positive-only control (no RED run): CRLF, an encoding declaration, a default and a prefixed
        # namespace, text content holding escaped delimiters, tabs/newlines inside tags, and a leading byte-order mark.
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>\r\n'
            '<model unit="millimeter" xmlns="urn:synthetic-default" xmlns:ext="urn:synthetic-ext">\r\n'
            ' <metadata name="Title">a &gt; b, 1 &lt; 2 and paint_color="4" as plain text</metadata>\r\n'
            ' <resources>\r\n  <object id="1" type="model">\r\n   <mesh>\r\n    <vertices>\r\n'
            '     <vertex x="0" y="0" z="0"/>\r\n     <vertex x="1" y="0" z="0"/>\r\n     <vertex x="1" y="1" z="0"/>\r\n    </vertices>\r\n'
            "    <triangles>\r\n"
            '     <triangle v1="0" v2="1" v3="2" ext:note="x > y" paint_color="4"/>\r\n'
            '     <triangle\r\n\tv1="0" v2="2" v3="1"\r\n\tpaint_color="1C" />\r\n'
            '     <triangle v1="1" v2="2" v3="0"/>\r\n'
            "    </triangles>\r\n   </mesh>\r\n  </object>\r\n </resources>\r\n</model>\r\n"
        )
        for label, model in (("plain", body), ("with a byte-order mark", "﻿" + body)):
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                make_3mf(self.src, model=model)
                code, _, err, exc = self.apply([self.cand([0], 1, 2), self.cand([1], 4, 3)])
                self.assertIsNone(exc, err)
                self.assertEqual(code, 0)
                after = model_text(self.out)
                self.assertEqual(after, model.replace('x > y" paint_color="4"', 'x > y" paint_color="8"', 1).replace('paint_color="1C"', 'paint_color="0C"', 1))
                if label == "plain":  # the parser oracle (it does not accept a leading BOM character in a str)
                    self.assert_only_paint_values_changed(model, after, {0: ("4", "8"), 1: ("1C", "0C")})
                code, out, _, exc = self.verify()
                self.assertEqual(code, 0, exc)
                self.assertIn('"changed_faces_verified": 2', out)

    def test_helpers_document_the_exact_attribute_scan_and_what_they_refuse(self):
        for script in (self.apply_py, self.verify_py):
            doc = ast.get_docstring(ast.parse(script.read_text(encoding="utf8"))).lower()
            for needle in ("quote-aware", "not an xml parser", "exact", "unsupported xml syntax", "looks like"):
                self.assertIn(needle, doc, f"{script.name}: {needle}")

    # -- the sidecar carries private paths, so it is created owner-only (POSIX) -----------------
    @unittest.skipUnless(os.name == "posix", "owner-only permission bits are a POSIX claim; not qualified elsewhere")
    def test_sidecar_is_owner_only_even_under_a_permissive_umask(self):
        old = os.umask(0)
        try:
            code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        finally:
            os.umask(old)
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)
        self.assertEqual(self.manifest.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(self.manifest.read_text())["changed_faces"], 1)

    def test_applier_documents_the_owner_only_sidecar_and_never_changes_modes_after_the_fact(self):
        text = self.apply_py.read_text(encoding="utf8")
        doc = " ".join(ast.get_docstring(ast.parse(text)).lower().split())
        self.assertIn("owner-only", doc)
        names = {n.attr if isinstance(n, ast.Attribute) else n.id for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.Attribute, ast.Name))}
        self.assertFalse({"chmod", "fchmod", "lchmod"} & names, "a later chmod could follow a pre-existing entry")

    def test_sidecar_paths_are_documented_as_private_evidence_to_redact_before_sharing(self):
        doc = " ".join(ast.get_docstring(ast.parse(self.apply_py.read_text(encoding="utf8"))).lower().split())
        for needle in ("absolute", "private evidence", "redact", "symlink"):
            self.assertIn(needle, doc, needle)

    # -- memory: artifact hashes stream; large archives still verify exactly ---
    def test_verifier_hashes_artifacts_by_streaming_not_whole_file_reads(self):
        self.make_valid_output()
        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read")):
            code, out, _, exc = self.verify()
        self.assertIsNone(exc)
        self.assertEqual(code, 0)
        self.assertIn('"output_sha256_verified": true', out)

    def test_large_artifacts_spanning_many_read_chunks_hash_and_verify_exactly(self):
        big = ("padding = " + "x" * 1000 + "\n") * 2600  # about 2.6 MB: several 1 MiB hashing chunks
        make_3mf(self.src, config=big)
        self.make_valid_output()
        code, _, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        bad = self.tmp / "big-tampered.3mf"
        repack(self.out, bad, {"Metadata/project_settings.config": lambda b: b[:2_000_000] + b"Y" + b[2_000_001:]})
        # re-bound to the tampered bytes: the mutation guard itself catches the one-byte change
        self.assertIn("Unexpected changed ZIP member", self.refusal(self.verify(candidate=bad, manifest=self.bound(bad))))
        # not re-bound: the exact-hash guard speaks first
        self.assertIn("Candidate hash mismatch", self.refusal(self.verify(candidate=bad)))

    # -- caller preconditions are documented, concurrency/transactions are not claimed ----
    def test_helpers_document_caller_preconditions_and_claim_no_concurrency_or_transaction(self):
        for script in (self.apply_py, self.verify_py):
            doc = " ".join(ast.get_docstring(ast.parse(script.read_text(encoding="utf8"))).lower().split())  # docstrings wrap lines
            for needle in ("frozen", "private workspace", "one writer", "does not enforce", "atomic transaction"):
                self.assertIn(needle, doc, f"{script.name}: {needle}")
            self.assertNotIn("atomically", doc, f"{script.name} must not advertise atomic behaviour")
        ref = (CAD_DOCS / "references" / "paint-label-repair.md").read_text(encoding="utf8").lower()
        for needle in ("private workspace", "one writer", "does not enforce", "not one atomic transaction", "nonnegative json integer"):
            self.assertIn(needle, ref, f"paint-label-repair.md: {needle}")

    def test_nontriangle_paint_attribute_is_compared_not_stripped(self):
        make_3mf(self.src, model=MODEL.replace("<model>", '<model paint_color="5">'))
        # positive control: the attribute exists in source and output, unchanged
        self.make_valid_output()
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        bad = self.tmp / "tampered.3mf"
        repack(self.out, bad, {"3D/Objects/object_1.model": lambda b: b.replace(b'<model paint_color="5">', b'<model paint_color="9">')})
        code, _, _, exc = self.verify(candidate=bad, manifest=self.bound(bad))
        self.assertIn("outside paint_color", code if isinstance(code, str) else str(exc))

    def test_verifier_refuses_changed_unpainted_face_with_unknown_lineage(self):
        self.make_valid_output()
        m = json.loads(self.manifest.read_text())
        m["changes"]["3"] = {"before_token": "4", "after_token": "8", "source_label": 1, "target_label": 2, "component": 1}
        listed = self.tmp / "listed.json"
        listed.write_text(json.dumps(m))
        for token in ("8", "4"):  # an unpainted face that gains any paint token has unknown lineage
            with self.subTest(after=token):
                bad = self.tmp / f"unpainted-{token}.3mf"
                repack(self.out, bad, {"3D/Objects/object_1.model": lambda b, t=token: b.replace(b'v3="3"/>', b'v3="3" paint_color="' + t.encode() + b'"/>')})
                code, _, _, exc = self.verify(candidate=bad, manifest=self.bound(bad, listed))
                self.assertIn("unpainted", code if isinstance(code, str) else str(exc))

    def test_applier_refuses_pseudo_triangle_in_xml_comment(self):
        fake = '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'
        make_3mf(self.src, model=MODEL.replace("<triangles>", "<!--" + fake + "--><triangles>"))
        self.assert_refused(self.apply([self.cand([0], 1, 2)]), "Unsupported XML markup")

    def test_verifier_refuses_comment_and_cdata_triangle_mutations(self):
        for opening, closing in (("<!--", "-->"), ("<![CDATA[", "]]>")):
            with self.subTest(markup=opening):
                fake = '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'
                model = MODEL.replace("<triangles>", opening + fake + closing + "<triangles>")
                make_3mf(self.src, model=model)
                changed = model.replace(opening + fake, opening + fake.replace('paint_color="4"', 'paint_color="8"'))
                make_3mf(self.out, model=changed)
                self.manifest.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(self.out), "changes": {"0": {"before_token": "4", "after_token": "8"}}}))
                code, _, _, exc = self.verify()
                msg = code if isinstance(code, str) else str(exc)
                self.assertIn("Unsupported XML markup", msg)

    def test_applier_refuses_duplicate_zip_members_before_writing(self):
        with zipfile.ZipFile(self.src, "a") as z:
            z.writestr("Metadata/project_settings.config", "synthetic duplicate")
        self.assert_refused(self.apply([self.cand([0], 1, 2)]), "Duplicate ZIP member")

    def test_verifier_refuses_changed_earlier_duplicate_member(self):
        for path, first in ((self.src, "synthetic original"), (self.out, "synthetic changed")):
            make_3mf(path)
            with zipfile.ZipFile(path, "a") as z:
                z.writestr("Metadata/duplicate.config", first)
                z.writestr("Metadata/duplicate.config", "synthetic same last payload")
        self.manifest.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(self.out), "changes": {}}))
        code, _, _, exc = self.verify()
        msg = code if isinstance(code, str) else str(exc)
        self.assertIn("Duplicate ZIP member", msg)

    # -- verifier artifact binding (source_sha256 / output_sha256) ----------
    def refusal(self, result):
        code, _, _, exc = result
        self.assertTrue(isinstance(code, str) or exc is not None, "expected a refusal")
        return code if isinstance(code, str) else str(exc)

    def test_verifier_success_reports_both_hashes_verified(self):
        self.make_valid_output()
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"source_sha256_verified": true', out)
        self.assertIn('"output_sha256_verified": true', out)

    def test_verifier_refuses_manifest_without_hash_fields(self):
        self.make_valid_output()
        for key in ("source_sha256", "output_sha256"):
            with self.subTest(missing=key):
                m = json.loads(self.manifest.read_text())
                del m[key]
                p = self.tmp / f"no-{key}.json"
                p.write_text(json.dumps(m))
                self.assertIn(key, self.refusal(self.verify(manifest=p)))

    def test_verifier_refuses_candidate_whose_bytes_differ_from_the_manifest_hash(self):
        # a tampered candidate checked against the unchanged manifest: the hash guard speaks first
        self.make_valid_output()
        bad = self.tmp / "tampered.3mf"
        repack(self.out, bad, {"Metadata/project_settings.config": lambda b: b + b"extra = 1\n"})
        msg = self.refusal(self.verify(candidate=bad))
        self.assertIn("Candidate hash mismatch", msg)
        self.assertNotIn("Unexpected changed ZIP member", msg)

    def test_verifier_binds_exact_candidate_bytes_even_for_identical_payload(self):
        self.make_valid_output()
        again = self.tmp / "repacked.3mf"
        repack(self.out, again, comment=b"repacked")  # same member payloads, different archive bytes
        self.assertNotEqual(sha(again), sha(self.out))
        self.assertIn("Candidate hash mismatch", self.refusal(self.verify(candidate=again)))
        # control: once the manifest names these exact bytes, the identical payload verifies
        code, out, _, exc = self.verify(candidate=again, manifest=self.bound(again))
        self.assertEqual(code, 0, exc)

    def test_verifier_binds_exact_source_bytes_even_for_identical_payload(self):
        self.make_valid_output()
        other = self.tmp / "source-repacked.3mf"
        repack(self.src, other, comment=b"repacked")
        code, _, _, exc = _run(self.verify_py, [other, self.out, self.manifest])
        self.assertIn("Source hash mismatch", code if isinstance(code, str) else str(exc))

    def test_verifier_refuses_a_different_source_whose_payload_also_differs(self):
        self.make_valid_output()
        other = self.tmp / "other-source.3mf"
        make_3mf(other, config="another_setting = 2\n")
        code, _, _, exc = _run(self.verify_py, [other, self.out, self.manifest])
        self.assertIn("Source hash mismatch", code if isinstance(code, str) else str(exc))

    # -- verifier mutation controls --------------------------------------
    def make_valid_output(self):
        code, _, err, exc = self.apply([self.cand([0], 1, 2)])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)

    def verify_mutated(self, transforms, reverse=False):
        self.make_valid_output()
        bad = self.tmp / "tampered.3mf"
        repack(self.out, bad, transforms, reverse=reverse)
        code, _, _, exc = self.verify(candidate=bad, manifest=self.bound(bad))
        return code if isinstance(code, str) else str(exc)

    def test_verifier_catches_unlisted_face_change(self):
        t = {"3D/Objects/object_1.model": lambda b: b.replace(b'v3="3" paint_color="8"', b'v3="3" paint_color="4"')}
        self.assertIn("Changed face set mismatch", self.verify_mutated(t))

    def test_verifier_catches_changed_other_member(self):
        t = {"Metadata/project_settings.config": lambda b: b + b"extra = 1\n"}
        self.assertIn("Unexpected changed ZIP member", self.verify_mutated(t))

    def test_verifier_catches_geometry_change(self):
        t = {"3D/Objects/object_1.model": lambda b: b.replace(b'x="1" y="1"', b'x="9" y="1"', 1)}
        self.assertIn("outside paint_color", self.verify_mutated(t))

    def test_verifier_catches_member_order_change(self):
        self.assertIn("member list/order differs", self.verify_mutated({}, reverse=True))

    def test_verifier_catches_manifest_token_mismatch(self):
        self.make_valid_output()
        m = json.loads(self.manifest.read_text())
        m["changes"]["0"]["after_token"] = "0C"
        bad = self.tmp / "bad_manifest.json"
        bad.write_text(json.dumps(m))
        code, _, _, exc = self.verify(manifest=bad)
        self.assertIn("Token mismatch", code if isinstance(code, str) else str(exc))


class PaintVerifierTokenGateAndSummaryTest(TmpCase):
    """Correction 18 (synthetic): the verifier gates every changed token to the whole-face mapping with or without
    labels, and checks the optional summaries and caller-declared component identities when they are supplied."""

    apply_py = CAD_SCRIPTS / "apply_reviewed_paint_cleanup.py"
    verify_py = CAD_SCRIPTS / "verify_3mf_paint_cleanup.py"

    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        make_3mf(self.src)
        self.out = self.tmp / "synthetic_out.3mf"
        self.manifest = Path(str(self.out) + ".cleanup.json")

    def verify(self, candidate=None, manifest=None):
        return _run(self.verify_py, [self.src, candidate or self.out, manifest or self.manifest])

    def refusal(self, result):
        code, _, _, exc = result
        self.assertTrue(isinstance(code, str) or exc is not None, f"expected a refusal, got exit {code!r}")
        return code if isinstance(code, str) else str(exc)

    @staticmethod
    def model_with(paint):
        return MODEL.replace('v3="2" paint_color="4"', f'v3="2" paint_color="{paint}"', 1)

    def hand(self, candidate, changes):
        path = self.tmp / f"hand-{Path(candidate).stem}.json"
        path.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate), "changes": changes}))
        return path

    def apply_two_components(self):
        analysis = self.tmp / "analysis.json"
        analysis.write_text(json.dumps({"candidates": [
            {"component": 1, "source_label": 1, "target_label": 2, "face_ids": [0]},
            {"component": 2, "source_label": 3, "target_label": 1, "face_ids": [2]},
        ]}))
        code, _, err, exc = _run(self.apply_py, [self.src, analysis, self.out])
        self.assertIsNone(exc, err)
        self.assertEqual(code, 0)

    def edited(self, mutate, name="edited.json"):
        m = json.loads(self.manifest.read_text())
        mutate(m)
        path = self.tmp / name
        path.write_text(json.dumps(m))
        return path

    # -- unconditional whole-face token gate -----------------------------------------------------------
    UNSUPPORTED = {
        "4 to 44": ("4", "44"),
        "4 to a split token": ("4", "0C0"),
        "an unsupported source token": ("44", "8"),
        "split token on both sides": ("0C0", "1C0"),
        "4 to an empty value": ("4", ""),
    }

    def test_verifier_refuses_an_unsupported_changed_token_on_either_side_even_for_a_rebound_token_only_record(self):
        for label, (before, after) in self.UNSUPPORTED.items():
            with self.subTest(label):
                make_3mf(self.src, model=self.model_with(before))
                candidate = self.tmp / "candidate.3mf"
                make_3mf(candidate, model=self.model_with(after))
                message = self.refusal(self.verify(candidate=candidate, manifest=self.hand(candidate, {"0": {"before_token": before, "after_token": after}})))
                self.assertIn("whole-face", message)
                self.assertNotIn("hash mismatch", message)
                for raw in (before, after):
                    if len(raw) > 1:
                        self.assertNotIn(raw, message, "the raw token must not be echoed")

    def test_control_valid_mapped_token_only_records_are_still_accepted(self):
        for before, after in (("4", "8"), ("8", "0C"), ("0C", "1C"), ("1C", "4")):
            with self.subTest(f"{before} to {after}"):
                make_3mf(self.src, model=self.model_with(before))
                candidate = self.tmp / "candidate.3mf"
                make_3mf(candidate, model=self.model_with(after))
                code, out, _, exc = self.verify(candidate=candidate, manifest=self.hand(candidate, {"0": {"before_token": before, "after_token": after}}))
                self.assertEqual(code, 0, exc)
                self.assertIn('"changed_faces_verified": 1', out)

    # -- optional summaries and caller-declared component identities ------------------------------------
    CONTRADICTIONS = {
        "triangle_count": lambda m: m.__setitem__("triangle_count", 999),
        "changed_faces": lambda m: m.__setitem__("changed_faces", 999),
        "changed_components": lambda m: m.__setitem__("changed_components", 999),
        "component_ids": lambda m: m.__setitem__("component_ids", [999]),
        "mapping_face_counts": lambda m: m.__setitem__("mapping_face_counts", {"1->2": {"faces": 999}}),
        "model_member": lambda m: m.__setitem__("model_member", "3D/Objects/another.model"),
        "triangle_count as a boolean": lambda m: m.__setitem__("triangle_count", True),
    }

    def test_verifier_refuses_contradictory_optional_summaries_naming_the_field_but_not_the_value(self):
        self.apply_two_components()
        for label, mutate in self.CONTRADICTIONS.items():
            with self.subTest(label):
                message = self.refusal(self.verify(manifest=self.edited(mutate)))
                self.assertIn(label.split()[0], message)  # the first word of every label is the manifest field it contradicts
                self.assertNotIn("999", message)

    def test_verifier_requires_caller_declared_component_identities_to_be_nonnegative_integers_when_supplied(self):
        self.apply_two_components()
        for label, value in {"negative": -1, "string": "x", "boolean": True, "fraction": 1.5}.items():
            with self.subTest(label):
                message = self.refusal(self.verify(manifest=self.edited(lambda m, v=value: m["changes"]["0"].__setitem__("component", v))))
                self.assertIn("component", message)

    def test_verifier_cannot_check_a_component_summary_against_changes_that_declare_no_component(self):
        self.apply_two_components()
        message = self.refusal(self.verify(manifest=self.edited(lambda m: m["changes"]["0"].pop("component"))))
        self.assertIn("component", message)

    def test_control_the_untouched_summaries_and_summary_free_manifests_are_still_accepted(self):
        self.apply_two_components()
        code, out, _, exc = self.verify()
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 2', out)

        def strip(m):
            for key in ("triangle_count", "changed_faces", "changed_components", "component_ids", "mapping_face_counts", "model_member"):
                m.pop(key, None)
            for record in m["changes"].values():
                record.pop("component", None)

        code, out, _, exc = self.verify(manifest=self.edited(strip, "bare.json"))
        self.assertEqual(code, 0, exc)
        self.assertIn('"changed_faces_verified": 2', out)
        def only_faces_and_triangles(m):
            for key in ("component_ids", "changed_components", "mapping_face_counts", "model_member"):
                m.pop(key)

        code, _, _, exc = self.verify(manifest=self.edited(only_faces_and_triangles, "partial.json"))
        self.assertEqual(code, 0, exc)

    def test_verifier_documents_the_token_gate_and_that_components_are_caller_declared(self):
        doc = ast.get_docstring(ast.parse(self.verify_py.read_text(encoding="utf8"))).lower()
        for needle in ("caller-declared", "not geometric", "whole-face", "regardless", "summary"):
            self.assertIn(needle, doc, needle)


class PaintXmlNameGrammarTest(TmpCase):
    """Correction 21 (synthetic): both helpers admit only qualified ASCII lexical XML names for elements and attributes
    and fail closed otherwise. This is a lexical guard, not an XML engine, a namespace resolver or a 3MF-schema check."""

    apply_py = CAD_SCRIPTS / "apply_reviewed_paint_cleanup.py"
    verify_py = CAD_SCRIPTS / "verify_3mf_paint_cleanup.py"
    FACE0 = '<triangle v1="0" v2="1" v3="2" paint_color="4"/>'
    TO_8 = {"0": {"before_token": "4", "after_token": "8"}}

    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        self.out = self.tmp / "synthetic_out.3mf"
        self.manifest = Path(str(self.out) + ".cleanup.json")

    @staticmethod
    def slug(text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def apply_face0(self):
        analysis = self.tmp / "analysis.json"
        analysis.write_text(json.dumps({"candidates": [{"component": 1, "source_label": 1, "target_label": 2, "face_ids": [0]}]}))
        return _run(self.apply_py, [self.src, analysis, self.out])

    def rebound(self, candidate):
        path = self.tmp / f"rebound-{Path(candidate).stem}.json"
        path.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(candidate), "changes": self.TO_8}))
        return path

    def refusal(self, result):
        code, _, _, exc = result
        self.assertTrue(isinstance(code, str) or exc is not None, f"expected a refusal, got exit {code!r}")
        return code if isinstance(code, str) else str(exc)

    # A malformed or unsupported name placed in face 0's tag (or replacing its element name).
    BAD_FACE0 = {
        "attribute starting with @": '<triangle v1="0" v2="1" v3="2" @bad="1" paint_color="4"/>',
        "attribute starting with a digit": '<triangle v1="0" v2="1" v3="2" 1bad="1" paint_color="4"/>',
        "attribute with punctuation inside": '<triangle v1="0" v2="1" v3="2" b@d="1" paint_color="4"/>',
        "attribute with a leading colon": '<triangle v1="0" v2="1" v3="2" :bad="1" paint_color="4"/>',
        "attribute with two prefixes": '<triangle v1="0" v2="1" v3="2" a:b:c="1" paint_color="4"/>',
        "non-ASCII attribute name": '<triangle v1="0" v2="1" v3="2" é="1" paint_color="4"/>',
        "element starting with a digit": '<1triangle v1="0" v2="1" v3="2" paint_color="4"/>',
        "element with punctuation inside": '<tri@angle v1="0" v2="1" v3="2" paint_color="4"/>',
    }

    def test_applier_refuses_malformed_or_non_ascii_names_by_name_before_writing_anything(self):
        for label, face in self.BAD_FACE0.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                make_3mf(self.src, model=MODEL.replace(self.FACE0, face, 1))
                before = sha(self.src)
                message = self.refusal(self.apply_face0())
                self.assertIn("Unsupported XML syntax", message)
                self.assertFalse(self.out.exists(), "no output may be written")
                self.assertFalse(self.manifest.exists(), "no sidecar may be written")
                self.assertEqual(sha(self.src), before)

    def test_verifier_refuses_the_same_names_in_the_source_even_with_a_rebound_candidate_and_manifest(self):
        for label, face in self.BAD_FACE0.items():
            with self.subTest(label):
                model = MODEL.replace(self.FACE0, face, 1)
                make_3mf(self.src, model=model)
                candidate = self.tmp / f"candidate-{self.slug(label)}.3mf"
                make_3mf(candidate, model=model.replace('paint_color="4"', 'paint_color="8"', 1))
                code, _, _, exc = _run(self.verify_py, [self.src, candidate, self.rebound(candidate)])
                self.assertIn("Unsupported XML syntax", code if isinstance(code, str) else str(exc))

    def test_verifier_refuses_a_malformed_name_that_only_the_candidate_carries(self):
        make_3mf(self.src)
        for label in ("attribute starting with @", "attribute starting with a digit", "non-ASCII attribute name"):
            with self.subTest(label):
                bad_face = self.BAD_FACE0[label].replace('paint_color="4"', 'paint_color="8"')
                candidate = self.tmp / f"cand-only-{self.slug(label)}.3mf"
                make_3mf(candidate, model=MODEL.replace(self.FACE0, bad_face, 1))
                code, _, _, exc = _run(self.verify_py, [self.src, candidate, self.rebound(candidate)])
                self.assertIn("Unsupported XML syntax", code if isinstance(code, str) else str(exc))

    VALID_ATTRS = {
        "prefixed note with quoted Unicode and delimiters": "probe:note='café — ünï \"q\" > x /> paint_color=\"4\"'",
        "hyphen dot and underscore": 'data-x.y_z="1"',
        "xml prefix": 'xml:lang="en"',
        "digit after the first character": 'x1="1"',
        "leading underscore": '_u="1"',
        "namespace declaration": 'xmlns:probe="urn:synthetic-probe"',
    }

    def test_control_valid_ascii_names_with_unicode_quoted_values_still_apply_and_verify_exactly(self):
        for label, attr in self.VALID_ATTRS.items():
            with self.subTest(label):
                for leftover in (self.out, self.manifest):
                    leftover.unlink(missing_ok=True)
                template = f'<triangle {attr} v1="0" v2="1" v3="2" paint_color="@P@"/>'
                before = MODEL.replace(self.FACE0, template.replace("@P@", "4"), 1)
                make_3mf(self.src, model=before)
                code, _, err, exc = self.apply_face0()
                self.assertIsNone(exc, err)
                self.assertEqual(code, 0)
                self.assertEqual(model_text(self.out), MODEL.replace(self.FACE0, template.replace("@P@", "8"), 1), "only the value bytes may change")
                code, out, _, exc = _run(self.verify_py, [self.src, self.out, self.manifest])
                self.assertEqual(code, 0, exc)
                self.assertIn('"changed_faces_verified": 1', out)



class PaintMappingSummaryTypesTest(TmpCase):
    def test_mapping_face_counts_requires_json_integer_counts(self):
        for label, count in (("boolean", True), ("float", 1.0)):
            with self.subTest(label=label):
                case = PaintHelperTest()
                case.setUp()
                try:
                    self.assertEqual(case.apply([case.cand([0], 1, 2)])[0], 0)
                    manifest = json.loads(case.manifest.read_text())
                    manifest["mapping_face_counts"] = {"1->2": {"faces": count}}
                    path = case.tmp / "summary-types.json"
                    path.write_text(json.dumps(manifest))
                    code, _, _, exc = case.verify(manifest=path)
                    self.assertNotEqual(code, 0, "a boolean or float is not a JSON integer count")
                    self.assertIn("mapping_face_counts", str(code) + str(exc))
                finally:
                    case.doCleanups()


class PaintVerifierTokenRecordAdmissionTest(TmpCase):
    """Correction 35 (synthetic): every manifest change record must carry BOTH required token fields as strings that are exactly one of
    4, 8, 0C or 1C. A record that does not is refused cleanly BEFORE any indexing or comparison: a named intentional SystemExit (no
    traceback), empty stdout, unchanged inputs, and the offending value is never echoed. Valid token-only and labelled records stay valid.
    The artifacts are real and the manifest binds their correct hashes, so only the record admission can refuse."""

    verify_py = CAD_SCRIPTS / "verify_3mf_paint_cleanup.py"
    SENTINEL = "ZZsentinel"

    def setUp(self):
        super().setUp()
        self.src = self.tmp / "synthetic.3mf"
        make_3mf(self.src)
        self.cand = self.tmp / "candidate.3mf"
        make_3mf(self.cand, model=MODEL.replace('v3="2" paint_color="4"', 'v3="2" paint_color="8"', 1))

    def bound(self, changes, name="admission.json"):
        path = self.tmp / name
        path.write_text(json.dumps({"source_sha256": sha(self.src), "output_sha256": sha(self.cand), "changes": changes}))
        return path

    def run_verify(self, manifest):
        before = [Path(p).read_bytes() for p in (self.src, self.cand, manifest)]
        result = _run(self.verify_py, [self.src, self.cand, manifest])
        self.assertEqual(before, [Path(p).read_bytes() for p in (self.src, self.cand, manifest)], "the verifier must not modify its inputs")
        return result

    def assert_clean_named_refusal(self, changes, field, label):
        code, out, err, exc = self.run_verify(self.bound(changes))
        self.assertIsNone(exc, f"{label}: an uncaught {type(exc).__name__} instead of an intentional refusal")
        self.assertIsInstance(code, str, f"{label}: expected an intentional SystemExit with a message, got exit {code!r}")
        self.assertEqual(out, "", f"{label}: nothing may be reported as success")
        self.assertIn(field, code, f"{label}: the refusal must name the field")
        self.assertIn("whole-face", code)
        for raw in (self.SENTINEL, "12345"):
            self.assertNotIn(raw, code + err, f"{label}: the offending value must not be echoed")
        return code

    def test_a_record_missing_a_required_token_field_is_a_clean_named_refusal(self):
        for label, record, field in (
            ("missing before_token", {"after_token": "8"}, "before_token"),
            ("missing after_token", {"before_token": "4"}, "after_token"),
            ("empty record", {}, "before_token"),
            ("labels only", {"source_label": 1, "target_label": 2}, "before_token"),
        ):
            with self.subTest(label):
                self.assert_clean_named_refusal({"0": record}, field, label)

    def test_a_non_string_token_is_a_clean_named_refusal_that_does_not_echo_it(self):
        for label, value in (("integer", 12345), ("null", None), ("boolean", True), ("list", [12345]), ("object", {"k": self.SENTINEL})):
            for field in ("before_token", "after_token"):
                with self.subTest(f"{label} {field}"):
                    record = {"before_token": "4", "after_token": "8"}
                    record[field] = value
                    self.assert_clean_named_refusal({"0": record}, field, f"{label} {field}")

    def test_an_unsupported_or_unnormalised_token_string_is_refused_without_normalising_or_echoing(self):
        for label, value in (
            ("unknown string", self.SENTINEL), ("empty", ""), ("lower-case 0c", "0c"), ("lower-case 1c", "1c"), ("zero-padded", "04"),
            ("padded with a space", "4 "), ("split-triangle token", "0C0"), ("two-digit", "44"), ("numeric string", "12345"),
        ):
            for field in ("before_token", "after_token"):
                with self.subTest(f"{label} {field}"):
                    record = {"before_token": "4", "after_token": "8"}
                    record[field] = value
                    code = self.assert_clean_named_refusal({"0": record}, field, f"{label} {field}")
                    self.assertNotIn("Token mismatch", code, "admission happens before any comparison")

    def test_an_invalid_record_is_refused_even_after_valid_records_and_with_matching_labels(self):
        bad = {"before_token": "4", "source_label": 1, "target_label": 2}
        self.assert_clean_named_refusal({"0": {"before_token": "4", "after_token": "8"}, "5": bad}, "after_token", "second record invalid")

    def test_control_valid_token_only_and_labelled_records_are_still_accepted(self):
        for label, record in (
            ("token only", {"before_token": "4", "after_token": "8"}),
            ("labelled", {"before_token": "4", "after_token": "8", "source_label": 1, "target_label": 2}),
            ("with a caller-declared component", {"before_token": "4", "after_token": "8", "component": 7}),
        ):
            with self.subTest(label):
                code, out, err, exc = self.run_verify(self.bound({"0": record}, name=f"ok-{label.replace(' ', '-')}.json"))
                self.assertIsNone(exc, err)
                self.assertEqual(code, 0)
                self.assertIn('"changed_faces_verified": 1', out)

    def test_control_a_valid_record_that_mismatches_the_artifacts_keeps_the_existing_comparison_refusal(self):
        code, out, err, exc = self.run_verify(self.bound({"0": {"before_token": "4", "after_token": "1C"}}, name="mismatch.json"))
        self.assertIsNone(exc)
        self.assertIsInstance(code, str)
        self.assertEqual(out, "")
        self.assertIn("Token mismatch", code)
