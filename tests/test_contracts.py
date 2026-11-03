"""Standard-library synthetic tests; shared fixtures are not production validators."""
from test_skill_packages import (
    CAD_DOCS,
    DEFECT_KEYS,
    SCHEMA_ANCHOR_DOC,
    SCHEMA_ANCHOR_TEMPLATE,
    SCHEMA_KEYS,
    TEMPLATE_PLACEHOLDERS,
    enum,
    re,
    schema_after,
    unittest,
    validate_response,
)
from test_skill_packages import ROOT  # added for the correction-18 wording guards
from test_skill_packages import socket, sys  # added for the correction-33 deny-hook self-test and docstring check


class VisionContractTest(unittest.TestCase):
    doc = (CAD_DOCS / "references" / "vision-model-review.md").read_text(encoding="utf8")
    tpl = (CAD_DOCS / "templates" / "boundary-critic-prompt.md").read_text(encoding="utf8")

    def schemas(self):
        return schema_after(self.doc, SCHEMA_ANCHOR_DOC), schema_after(self.tpl, SCHEMA_ANCHOR_TEMPLATE)

    def test_procedure_and_template_carry_the_identical_single_region_schema(self):
        a, b = self.schemas()
        self.assertEqual(a, b)
        self.assertEqual(set(a), SCHEMA_KEYS)
        self.assertEqual(set(a["defects"][0]), DEFECT_KEYS)

    def test_one_verdict_vocabulary_and_no_leftover_old_one(self):
        a, _ = self.schemas()
        self.assertEqual(enum(a["status"]), {"clean", "defect", "uncertain"})
        for name, text in (("procedure", self.doc), ("template", self.tpl)):
            for old in ("needs_closeup", '"verdict"', "global_status", '"regions"', "accept|reject", "REGION_IDS", "proposed_color", "boundary_quality"):
                self.assertNotIn(old, text, f"{name} still uses the old divergent contract: {old}")

    def test_template_placeholders_are_exactly_the_documented_set(self):
        self.assertEqual(set(re.findall(r"\{\{([A-Z_]+)\}\}", self.tpl)), TEMPLATE_PLACEHOLDERS)

    def test_qualification_and_abstention_checks_use_the_same_words(self):
        for name, text in (("procedure", self.doc), ("template", self.tpl)):
            low = text.lower()
            for needle in ("uncertain", "hard negatives", "display-hue", "both"):
                self.assertIn(needle, low, f"{name} lacks {needle}")
        self.assertIn("one region", self.tpl.lower())
        self.assertIn("never invent", self.tpl.lower())

    def test_reference_validator_accepts_valid_and_refuses_each_contract_violation(self):
        schema, _ = self.schemas()
        regions, panels = {"A1"}, {"P1", "P2"}
        good = {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }
        self.assertEqual(validate_response(good, schema, regions, panels), [])
        clean = dict(good, status="clean", defects=[])
        self.assertEqual(validate_response(clean, schema, regions, panels), [])
        uncertain = dict(good, status="uncertain", defects=[], next_view="closer")
        self.assertEqual(validate_response(uncertain, schema, regions, panels), [], "abstention is a valid, conservative answer")
        mutations = {
            "old regions-array wrapper": {"regions": [good], "global_status": "defect"},
            "old verdict vocabulary": dict(good, status="accept"),
            "unknown region": dict(good, region_id="Z9"),
            "clean carrying a defect": dict(good, status="clean"),
            "defect without defects": dict(good, defects=[]),
            "unknown panel": dict(good, defects=[dict(good["defects"][0], panel_id="P9")]),
            "point out of bounds": dict(good, defects=[dict(good["defects"][0], normalized_points=[[1.2, 0.5]])]),
            "whole-panel placeholder": dict(good, defects=[dict(good["defects"][0], normalized_points=[[0, 0], [1, 1]])]),
            "defect type outside vocabulary": dict(good, defects=[dict(good["defects"][0], type="spill")]),
            "next_view outside vocabulary": dict(good, next_view="whatever"),
            "extra key": dict(good, global_status="clean"),
        }
        for label, resp in mutations.items():
            with self.subTest(label):
                self.assertTrue(validate_response(resp, schema, regions, panels), label)



class ValidatorBooleanNumberTest(unittest.TestCase):
    """validate_response is a reference fixture for the documented contract, not a shipped validator."""

    def good(self):
        schema = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC)
        return schema, {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }

    def check(self, resp, schema):
        return validate_response(resp, schema, {"A1"}, {"P1"})

    def test_integer_and_float_numbers_are_valid_coordinates_and_confidence(self):
        schema, good = self.good()
        for points, confidence in (([[0, 1]], 1), ([[0.0, 0.5]], 0), ([[1, 0.25]], 0.75)):
            with self.subTest(points=points, confidence=confidence):
                resp = dict(good, defects=[dict(good["defects"][0], normalized_points=points, confidence=confidence)])
                self.assertEqual(self.check(resp, schema), [])

    def test_json_booleans_are_not_numbers_for_coordinates_or_confidence(self):
        schema, good = self.good()
        for label, change in {
            "true coordinate": {"normalized_points": [[True, 0.5]]},
            "false coordinate": {"normalized_points": [[0.5, False]]},
            "true confidence": {"confidence": True},
            "false confidence": {"confidence": False},
        }.items():
            with self.subTest(label):
                resp = dict(good, defects=[dict(good["defects"][0], **change)])
                self.assertTrue(self.check(resp, schema), label)



class BoreWallSharedVertexTest(unittest.TestCase):
    """The bore-wall ring is shared with the rim and the bottom cap, so moving it moves those boundaries too."""

    text = (CAD_DOCS / "references" / "stl-feature-audit-and-edit.md").read_text(encoding="utf8")

    def test_reference_admits_the_connected_transition_and_no_longer_claims_rim_and_cap_stay_unchanged(self):
        self.assertNotIn("This preserves the rim, surrounding shell", self.text)
        low = " ".join(self.text.lower().split())
        for needle in ("belong to the rim", "connected transition", "outside that admitted set", "remeasure", "change silently"):
            self.assertIn(needle, low, needle)

    @staticmethod
    def mesh(radius):
        import math

        def ring(r, z, tag):
            return {f"{tag}{i}": (round(r * math.cos(i * math.pi / 2), 9), round(r * math.sin(i * math.pi / 2), 9), z) for i in range(4)}

        verts = {}
        verts.update(ring(radius, 0, "Ti"))  # top inner ring: bore wall top edge, shared with the rim
        verts.update(ring(5, 0, "To"))  # rim outer edge
        verts.update(ring(radius, -3, "Bi"))  # bore wall bottom edge, shared with the cap
        verts.update(ring(5, -3, "Bo"))  # outer shell bottom
        verts["C"] = (0.0, 0.0, -3.0)
        tris = {"rim": [], "wall": [], "cap": [], "shell": []}
        for i in range(4):
            j = (i + 1) % 4
            tris["rim"] += [(f"To{i}", f"To{j}", f"Ti{i}"), (f"To{j}", f"Ti{j}", f"Ti{i}")]
            tris["wall"] += [(f"Ti{i}", f"Ti{j}", f"Bi{i}"), (f"Ti{j}", f"Bi{j}", f"Bi{i}")]
            tris["cap"] += [(f"Bi{i}", f"Bi{j}", "C")]
            tris["shell"] += [(f"To{i}", f"Bo{i}", f"To{j}"), (f"To{j}", f"Bo{i}", f"Bo{j}")]
        return verts, tris

    @staticmethod
    def area(verts, tri):
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = (verts[n] for n in tri)
        ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
        return 0.5 * ((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2) ** 0.5

    def test_moving_the_shared_ring_changes_rim_and_cap_geometry_but_not_connectivity_depth_or_shell(self):
        before, tris = self.mesh(2.0)
        after, tris_after = self.mesh(2.5)  # same topology, bore diameter 4 -> 5
        self.assertEqual(tris, tris_after, "connectivity is unchanged")
        moved = {n for n in before if before[n] != after[n]}
        self.assertEqual(moved, {f"{t}{i}" for t in ("Ti", "Bi") for i in range(4)})
        touched = {kind: any(n in moved for t in ts for n in t) for kind, ts in tris.items()}
        # the old claim ("rim and cap stay unchanged") is false: they share the moved vertices
        self.assertEqual(touched, {"rim": True, "wall": True, "cap": True, "shell": False})
        for kind in ("rim", "cap"):
            self.assertNotAlmostEqual(sum(self.area(before, t) for t in tris[kind]), sum(self.area(after, t) for t in tris[kind]), msg=kind)
        # outside the admitted set nothing moves, and the depth is unchanged
        for n in before:
            if n not in moved:
                self.assertEqual(before[n], after[n], n)
        self.assertEqual(before["Ti0"][2] - before["Bi0"][2], after["Ti0"][2] - after["Bi0"][2])
        self.assertAlmostEqual(2 * max(abs(after["Ti0"][0]), abs(after["Ti1"][1])), 5.0)



class StlTJunctionDirectionTest(unittest.TestCase):
    A, B, M, C, D = (0, 0, 0), (2, 0, 0), (1, 0, 0), (1, 1, 0), (1, -1, 0)

    @staticmethod
    def edges(tris):
        return {e for t in tris for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))}

    @staticmethod
    def area_z(t):
        (ax, ay, _), (bx, by, _), (cx, cy, _) = t
        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

    def test_split_edges_pair_oppositely_with_the_neighbouring_surface(self):
        A, B, M, C, D = self.A, self.B, self.M, self.C, self.D
        original = [(A, B, C)]  # long edge A->B with the T-junction vertex M on it
        neighbour = [(B, M, D), (M, A, D)]  # the other surface already carries B->M and M->A
        repaired = [(A, M, C), (M, B, C)]
        self.assertIn((A, B), self.edges(original))
        new_edges, old_side = {(A, M), (M, B)}, {(B, M), (M, A)}
        self.assertTrue(new_edges <= self.edges(repaired))
        self.assertTrue(old_side <= self.edges(neighbour))
        for u, v in new_edges:
            self.assertIn((v, u), self.edges(neighbour), "each new sub-edge must pair with its reverse on the neighbour")
        self.assertFalse(new_edges & self.edges(neighbour), "no same-directed duplicate edges")
        signs = {self.area_z(t) > 0 for t in repaired + neighbour}
        self.assertEqual(signs, {True}, "consistent winding, no zero-area facet")

    def test_the_old_wording_would_pair_same_directed_edges(self):
        A, B, M, D = self.A, self.B, self.M, self.D
        wrong_neighbour = [(A, M, D), (M, B, D)]  # "opposing surface uses A->M and M->B"
        self.assertTrue({(A, M), (M, B)} <= self.edges(wrong_neighbour), "that surface would duplicate the repaired directed edges")

    def test_reference_states_the_corrected_directions(self):
        text = (CAD_DOCS / "references" / "stl-feature-audit-and-edit.md").read_text(encoding="utf8")
        self.assertIn("B→M", text)
        self.assertIn("M→A", text)
        self.assertNotIn("opposing surface uses `A→M` and `M→B`", text)


class ManualSafetyWordingTest(unittest.TestCase):
    """Correction 18: TEXTUAL guards only. They show that the reference wording carries the intended gates; they are not
    a native isolation, device, pressure or SVG-rendering test, and they implement none of those procedures."""

    @staticmethod
    def doc(*parts):
        return ROOT.joinpath(*parts).read_text(encoding="utf8")

    def test_wifi_compatibility_weakening_is_conditioned_on_verified_isolation(self):
        text = self.doc("3d-printing-workflows", "references", "snapmaker-u1-network-and-firmware.md")
        low = text.lower()
        for needle in ("isolated iot vlan", "isolation is not verified", "never lower the security of the main", "does not prescribe a network change"):
            self.assertIn(needle, low, needle)
        # the weakening advice (WPA2-only, PMF off) must come after the isolation condition
        self.assertLess(low.index("isolation is not verified"), low.index("wpa2-personal with aes only"))

    def test_usb_removable_flag_is_advisory_and_positive_identification_and_refusal_stay(self):
        text = self.doc("3d-printing-workflows", "references", "snapmaker-u1-network-and-firmware.md")
        low = text.lower()
        self.assertNotIn("require `tran=usb`, `rm=1`", low)
        for needle in ("advisory hint", "positively", "refuse on any ambiguity", "internal or system disk", "capacity"):
            self.assertIn(needle, low, needle)

    def test_unrated_pressure_prototypes_get_only_a_depressurised_fit_check(self):
        text = self.doc("cad-modeling-and-reverse-engineering", "references", "physical-reverse-engineering.md")
        low = text.lower()
        self.assertNotIn("a leak or air-ingress test before normal operation", low)
        for needle in ("depressurised", "unrated prototype", "no operating-pressure test", "rated for that duty", "competent"):
            self.assertIn(needle, low, needle)

    def test_svg_paths_are_combined_only_when_effective_rules_and_compound_semantics_are_preserved(self):
        text = self.doc("cad-modeling-and-reverse-engineering", "references", "logo-artwork-to-geometry.md")
        low = text.lower()
        self.assertNotIn("keeping `viewbox`, useful physical size, fill colour and the source `fill-rule`", low)
        for needle in ("effective fill rule", "overlap", "cancel", "semantics-preserving", "fail closed", "compare"):
            self.assertIn(needle, low, needle)


class CrossFieldMatrixTest(unittest.TestCase):
    """Correction 33: the REFERENCE fixture (not a production validator, not a semantic engine) states one coherent cross-field matrix:
    `views_consistent` false implies `uncertain`; `clean` requires `views_consistent` true, empty defects and `next_view` `none`. A concrete
    `defect` may still request another view and an `uncertain` answer may carry possible defects. Vocabularies, keys and schema are unchanged."""

    def good(self):
        schema = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC)
        return schema, {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }

    def violations(self, **change):
        schema, good = self.good()
        try:
            return validate_response(dict(good, **change), schema, {"A1"}, {"P1"})
        except Exception as exc:  # noqa: BLE001 - no exception may escape
            self.fail(f"raised {type(exc).__name__} for {change!r}")

    def test_disagreeing_views_require_uncertain_and_clean_requires_consistency_and_no_next_view(self):
        cases = {
            "clean with disagreeing views": (dict(status="clean", defects=[], views_consistent=False), "views_consistent false requires status uncertain"),
            "defect with disagreeing views": (dict(views_consistent=False), "views_consistent false requires status uncertain"),
            "clean asking for a closer view": (dict(status="clean", defects=[], next_view="closer"), "clean requires next_view none"),
            "clean asking for a slicer preview": (dict(status="clean", defects=[], next_view="slicer_preview"), "clean requires next_view none"),
            "clean with both problems": (dict(status="clean", defects=[], views_consistent=False, next_view="closer"), "clean requires next_view none"),
        }
        for label, (change, expected) in cases.items():
            with self.subTest(label):
                self.assertIn(expected, self.violations(**change))
        self.assertIn("views_consistent false requires status uncertain", self.violations(status="clean", defects=[], views_consistent=False, next_view="closer"))

    def test_control_the_permitted_combinations_stay_valid(self):
        cases = {
            "an ordinary clean answer": dict(status="clean", defects=[]),
            "a concrete defect requesting another view": dict(next_view="closer"),
            "a concrete defect requesting a slicer preview": dict(next_view="slicer_preview"),
            "uncertain, views disagree, no defects, another view": dict(status="uncertain", defects=[], views_consistent=False, next_view="closer"),
            "uncertain, views disagree, possible defects carried": dict(status="uncertain", views_consistent=False, next_view="opposite"),
            "uncertain, views agree, possible defects carried": dict(status="uncertain", next_view="none"),
            "uncertain with nothing else": dict(status="uncertain", defects=[], next_view="closer"),
        }
        for label, change in cases.items():
            with self.subTest(label):
                self.assertEqual(self.violations(**change), [])

    def test_control_malformed_cross_field_values_are_violations_not_exceptions_and_old_rules_still_fire(self):
        for label, change in {
            "views_consistent as a list": dict(views_consistent=[False]),
            "views_consistent as a string": dict(views_consistent="false"),
            "status as a list with views disagreeing": dict(status=["clean"], views_consistent=False),
            "next_view as an object on a clean answer": dict(status="clean", defects=[], next_view={"a": 1}),
            "clean carrying a defect": dict(status="clean"),
            "defect without defects": dict(defects=[]),
        }.items():
            with self.subTest(label):
                self.assertTrue(self.violations(**change), label)

    def test_reference_checklist_and_template_state_the_same_matrix_with_the_schema_unchanged(self):
        ref = " ".join(VisionContractTest.doc.lower().split())
        tpl = " ".join(VisionContractTest.tpl.lower().split())
        for needle in ("`views_consistent` false means `uncertain`", "`clean` also requires `views_consistent` true and `next_view` `none`",
                       "a `defect` may still request another view", "`uncertain` may carry possible defects"):
            self.assertIn(needle, ref, needle)
        checklist = ref.split("validator that checks", 1)[1].split("## 6.", 1)[0]
        self.assertIn("`views_consistent` false means `uncertain`", checklist, "the consuming-validator checklist must carry the matrix itself")
        for needle in ('"clean" also requires "views_consistent": true and "next_view": "none"', '"views_consistent": false means "uncertain"',
                       'a "defect" may still request another view', '"uncertain" may carry possible defects'):
            self.assertIn(needle, tpl, needle)
        a, b = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC), schema_after(VisionContractTest.tpl, SCHEMA_ANCHOR_TEMPLATE)
        self.assertEqual(a, b)
        self.assertEqual(set(a), SCHEMA_KEYS)


class SharedFixtureDocstringAndDenyHookTest(unittest.TestCase):
    """Correction 33: the shared module holds FIXTURES, not test cases; the cases run from its peer modules, so its docstring must describe
    suite-wide coverage with those locations instead of a per-file claim. Also a deliberate self-test of its already-installed socket-denial
    hook: a name-resolution call is rejected by the hook before any resolution (a numeric host is used, so no lookup could happen even if
    the hook were missing). This is a Python audit tripwire inside this process, NOT operating-system isolation and not a real network call."""

    def shared(self):
        return sys.modules["test_skill_packages"]

    def test_the_docstring_describes_shared_fixtures_and_names_the_peer_modules_that_hold_the_cases(self):
        doc = " ".join(self.shared().__doc__.lower().split())
        for needle in ("shared fixtures", "peer modules", "test_checker.py", "test_gcode.py", "test_paint_helpers.py", "test_paint_structure.py",
                       "test_contracts.py", "suite-wide", "not operating-system containment"):
            self.assertIn(needle, doc, needle)
        self.assertNotIn("what this covers: the structural checker", doc, "no per-file coverage claim")
        tests_dir = ROOT / "tests"
        for name in ("test_checker.py", "test_gcode.py", "test_paint_helpers.py", "test_paint_structure.py", "test_contracts.py"):
            self.assertTrue((tests_dir / name).is_file(), name)

    def test_the_shared_module_defines_no_test_cases(self):
        module = self.shared()
        for name, obj in vars(module).items():
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj.__module__ == module.__name__:
                self.assertEqual([m for m in dir(obj) if m.startswith("test_")], [], f"{name} defines a test case in the shared fixture module")

    def test_the_installed_hook_rejects_name_resolution_before_any_lookup(self):
        with self.assertRaises(RuntimeError) as caught:
            socket.getaddrinfo("127.0.0.1", 0)  # numeric host: nothing could be resolved over a network even without the hook
        self.assertIn("network use denied in tests: socket.getaddrinfo", str(caught.exception))

    def test_the_hook_function_denies_each_listed_event_and_ignores_others(self):
        deny = self.shared()._deny_network
        for event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.bind", "socket.sendto"):
            with self.subTest(event):
                with self.assertRaises(RuntimeError):
                    deny(event, ())
        self.assertIsNone(deny("open", ()))


class RealDesktopCaptureWordingTest(unittest.TestCase):
    """Correction 33: DOCUMENTARY guard only (no GUI, desktop, capture or environment action). The entry requires a prior warning AND approval
    for capturing a real desktop; the vision reference must say the same instead of only announcing. Offscreen synthetic renders and an
    isolated virtual display need no such approval, and no global permission object is introduced."""

    def text(self, *parts):
        return " ".join(ROOT.joinpath(*parts).read_text(encoding="utf8").lower().split())

    def test_real_desktop_or_window_capture_waits_for_the_operators_approval_not_just_an_announcement(self):
        text = self.text("cad-modeling-and-reverse-engineering", "references", "vision-model-review.md")
        for needle in ("real desktop or a real window", "must wait for the operator's approval", "an announcement alone is not approval",
                       "does not apply to an isolated virtual display or an offscreen synthetic render"):
            self.assertIn(needle, text, needle)
        for kept in ("announce before any operation that may show a screen-sharing or capture indicator", "prefer a fresh isolated virtual display",
                     "do not close an existing profile or settings editor", "is `blocked`, not permission to escalate silently",
                     "record it as pending and ask the user to open the file manually", "prefer per-window capture over monitor or root-window capture"):
            self.assertIn(kept, text, kept)
        # Representative negative guard (known forbidden literal variants, not a semantic validator): an announcement never permits, allows or
        # authorises real-desktop or real-window capture, with or without a trailing "no approval needed".
        for forbidden in (r"announce(?:ment|d|ing)?\b[^.]{0,60}\b(?:permits?|allows?|authori[sz]es?|suffices|is enough|is sufficient)\b[^.]{0,80}\b(?:desktop|window)",
                          r"\b(?:real|desktop|window)\b[^.]{0,60}capture[^.]{0,60}\b(?:no|without) (?:operator )?approval(?: is)? (?:needed|required)",
                          # capture-before-target: "Capture the real desktop without operator approval" / "...: no operator approval is required"
                          r"\bcapture\b[^.]{0,40}\b(?:real|desktop|window)\b[^.]{0,60}\b(?:without|no) (?:the )?(?:operator(?:'s)? )?approval"):
            self.assertNotRegex(text, forbidden)
        entry = self.text("cad-modeling-and-reverse-engineering", "SKILL.md")
        self.assertIn("capturing a real desktop needs prior warning and approval", entry)


class PanelCornerPlaceholderTest(unittest.TestCase):
    """Correction 31: validate_response is a REFERENCE fixture, not a production validator and not a polygon or semantic detector. The
    existing invariant "a whole-panel placeholder is not localisation" now covers BOTH diagonals of opposite corners, in either order and
    with any extra points; single corners, adjacent corners, localised points and narrow lines stay valid."""

    def good(self):
        schema = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC)
        return schema, {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }

    def violations(self, points):
        schema, good = self.good()
        response = dict(good, defects=[dict(good["defects"][0], normalized_points=points)])
        try:
            return validate_response(response, schema, {"A1"}, {"P1"})
        except Exception as exc:  # noqa: BLE001 - no exception may escape
            self.fail(f"raised {type(exc).__name__} for {points!r}")

    def test_both_diagonals_of_opposite_corners_are_a_placeholder_in_any_order(self):
        cases = {
            "first diagonal": [[0, 0], [1, 1]],
            "first diagonal reversed": [[1, 1], [0, 0]],
            "opposite diagonal": [[0, 1], [1, 0]],
            "opposite diagonal reversed": [[1, 0], [0, 1]],
            "opposite diagonal as floats": [[0.0, 1.0], [1.0, 0.0]],
            "opposite diagonal, mixed int and float": [[0, 1.0], [1, 0.0]],
            "opposite diagonal with an interior point between": [[0, 1], [0.5, 0.5], [1, 0]],
            "opposite diagonal with a point before": [[0.3, 0.3], [1, 0], [0, 1]],
            "all four corners": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "all four corners, other order": [[1, 0], [0, 1], [0, 0], [1, 1]],
        }
        for label, points in cases.items():
            with self.subTest(label):
                self.assertIn("whole-panel placeholder", self.violations(points))

    def test_control_single_corners_adjacent_corners_localised_points_and_narrow_lines_stay_valid(self):
        cases = {
            "single corner (0,0)": [[0, 0]],
            "single corner (1,1)": [[1, 1]],
            "single corner (0,1)": [[0, 1]],
            "single corner (1,0)": [[1, 0]],
            "adjacent corners along the top edge": [[0, 0], [1, 0]],
            "adjacent corners along the left edge": [[0, 0], [0, 1]],
            "a corner and an interior point": [[0, 0], [0.5, 0.5]],
            "a localised point": [[0.25, 0.5]],
            "a narrow line": [[0.1, 0.2], [0.12, 0.9]],
            "two adjacent corners and an interior point": [[0, 0], [1, 0], [0.4, 0.6]],
        }
        for label, points in cases.items():
            with self.subTest(label):
                self.assertEqual(self.violations(points), [])

    def test_control_malformed_coordinates_and_other_rules_still_fire(self):
        for label, points in {"out of range": [[1.2, 0.5]], "boolean coordinate": [[True, 0.5]], "three coordinates": [[0.1, 0.2, 0.3]],
                              "null point": [None], "empty list": []}.items():
            with self.subTest(label):
                self.assertTrue(self.violations(points), label)

    def test_the_localisation_rule_is_stated_in_the_reference_and_the_template_without_touching_the_schema(self):
        ref = " ".join(VisionContractTest.doc.lower().split())
        tpl = " ".join(VisionContractTest.tpl.lower().split())
        for name, text in (("reference", ref), ("template", tpl)):
            for needle in ("opposite corners", "either diagonal", "any order"):
                self.assertIn(needle, text, f"{name}: {needle}")
        a, b = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC), schema_after(VisionContractTest.tpl, SCHEMA_ANCHOR_TEMPLATE)
        self.assertEqual(a, b)
        self.assertEqual(set(a), SCHEMA_KEYS)


class SupportRhAndMemoryWordingTest(unittest.TestCase):
    """Correction 31: DOCUMENTARY guards only (no slice, print, hygrometer, model load or memory probe is performed or implied)."""

    @staticmethod
    def doc(*parts):
        return " ".join(ROOT.joinpath(*parts).read_text(encoding="utf8").lower().split())

    def test_support_interface_counts_are_separate_controls_and_both_nonzero_is_scoped_to_dual_sided_isolation(self):
        text = self.doc("3d-printing-workflows", "references", "orca-support-interfaces-and-first-layer.md")
        self.assertNotIn("both top and bottom interface layers must be nonzero", text)
        for needle in ("separate controls", "zero is allowed", "different material", "zero-gap model-facing contacts", "does not force both",
                       "top-only technique", "normal detachable gap", "verify the exact version"):
            self.assertIn(needle, text, needle)
        for kept in ("set zero z distances only after validating the material pair", "never disable the bottom interface while leaving same-material support at zero bottom gap",
                     "bottom interface layers = 0", "high-value **top-interface technique**"):
            self.assertIn(kept, text, kept)

    def test_the_humidity_formula_states_fractions_and_cubic_metres(self):
        text = self.doc("3d-printing-workflows", "references", "filament-storage-and-desiccant.md")
        for needle in ("dimensionless fractions", "between 0 and 1", "not percentages", "m³", "0.004", "0.40", "0.10", "0.0276", "about 0.03 g"):
            self.assertIn(needle, text, needle)
        self.assertNotIn("(rh_initial − rh_target)`; for 4 l and 40 % to 10 % that is about 0.03 g", text, "the unit-less statement must be replaced")

    def test_a_same_model_retry_requires_controlled_failure_without_kill_or_pressure_and_positive_evidence(self):
        text = self.doc("cad-modeling-and-reverse-engineering", "references", "vision-model-review.md")
        for needle in ("controlled load failure", "without an out-of-memory kill", "elevated memory pressure", "positive read-only evidence",
                       "unknown or missing evidence is not permission", "sufficient context", "bounded partial offload",
                       "operator's explicit approval", "adds no monitor"):
            self.assertIn(needle, text, needle)
        for kept in ("one bounded retry of the **same** model", "configuration correction"):
            self.assertIn(kept, text, kept)
        self.assertNotIn("start the verified application inside that existing session", text, "no start recipe may return")
        entry = self.doc("cad-modeling-and-reverse-engineering", "SKILL.md")
        self.assertIn("an out-of-memory kill or heavy memory pressure is a hard stop", entry)


class ReferenceTextFieldShapeTest(unittest.TestCase):
    """Correction 27: validate_response is a REFERENCE fixture, not a production response validator. The documented free-text fields
    (`observed_object`, `reason`, and each defect's `visible_evidence`) must be non-empty strings; malformed ordinary JSON there yields
    violations, never an exception. Ids, clean/defect consistency, booleans-vs-numbers, coordinates and abstention are unchanged."""

    def good(self):
        schema = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC)
        return schema, {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }

    def violations(self, response, schema):
        try:
            return validate_response(response, schema, {"A1"}, {"P1"})
        except Exception as exc:  # noqa: BLE001 - the point of the test: no exception may escape
            self.fail(f"raised {type(exc).__name__} instead of returning violations")

    BAD_TEXT = {"null": None, "list": ["x"], "object": {"a": 1}, "number": 3, "boolean": True, "empty string": "", "whitespace only": "  \t"}

    def test_malformed_text_fields_yield_violations_not_exceptions(self):
        schema, good = self.good()
        for label, value in self.BAD_TEXT.items():
            for field in ("observed_object", "reason"):
                with self.subTest(f"{field} is {label}"):
                    self.assertTrue(self.violations(dict(good, **{field: value}), schema), f"{field} = {value!r} was accepted")
            with self.subTest(f"visible_evidence is {label}"):
                bad = dict(good, defects=[dict(good["defects"][0], visible_evidence=value)])
                self.assertTrue(self.violations(bad, schema), f"visible_evidence = {value!r} was accepted")

    def test_control_valid_text_unclear_abstention_and_unicode_are_still_accepted_and_other_rules_still_fire(self):
        schema, good = self.good()
        self.assertEqual(self.violations(good, schema), [])
        self.assertEqual(self.violations(dict(good, observed_object="the rim of the cap", reason="café edge visible — ok"), schema), [])
        self.assertEqual(self.violations(dict(good, status="uncertain", defects=[], next_view="closer"), schema), [])
        self.assertEqual(self.violations(dict(good, status="clean", defects=[]), schema), [])
        self.assertTrue(self.violations(dict(good, status="clean"), schema), "clean must still not carry defects")
        self.assertTrue(self.violations(dict(good, status="defect", defects=[]), schema), "defect must still carry a concrete defect")
        self.assertTrue(self.violations(dict(good, defects=[dict(good["defects"][0], confidence=True)]), schema))


class VisionGuiAuthorisationWordingTest(unittest.TestCase):
    """Correction 27: DOCUMENTARY guard only. The vision reference already calls an existing-session start an operator-environment action;
    this makes explicit that a timeout grants no authority and that starting the server and validating the viewer are different actions.
    No runtime, GUI, model or service action is performed or implied, and no new approval protocol is introduced."""

    def test_the_existing_session_start_requires_an_explicit_named_approval_and_a_timeout_grants_none(self):
        text = " ".join(VisionContractTest.doc.lower().split())
        for needle in ("not something to attempt silently", "timeout grants no authority", "explicitly approved that named action",
                       "different actions", "otherwise leave the verification pending", "defines no approval protocol"):
            self.assertIn(needle, text, needle)
        # the earlier GUI-verification gate is untouched
        for kept in ("gui verification without surprises", "if a clean isolated gui gate cannot be obtained, record it as pending"):
            self.assertIn(kept, text, kept)


class VisionValidatorChecklistTest(unittest.TestCase):
    """Correction 23: DOCUMENTARY guard only. The vision reference states the cross-field rules; its consuming-validator checklist must
    name BOTH of them directly instead of forwarding to a section that omits one. No production validator is supplied or implied."""

    def test_the_validator_checklist_names_both_cross_field_rules_and_keeps_the_uncertainty_gate(self):
        doc = VisionContractTest.doc
        paragraph = next(p for p in doc.split("\n") if "the consuming implementation must supply and qualify a validator that checks" in p)
        checklist = " ".join(paragraph.split("validator that checks", 1)[1].lower().split())
        for needle in ("`clean` carries no defects", "`defect` carries at least one concrete defect", "exactly these keys", "known `region_id` and `panel_id`", "section 6"):
            self.assertIn(needle, checklist, needle)
        low = " ".join(doc.lower().split())
        for kept in ("no production response validator is supplied", "`uncertain` is the conservative abstention", "not qualified"):
            self.assertIn(kept, low, kept)


class ReferenceValidatorShapeTest(unittest.TestCase):
    """Correction 21: validate_response is a REFERENCE FIXTURE for the documented contract, not a shipped validator and not
    native vision proof. Malformed nested ordinary JSON must come back as violations, never as an exception."""

    def good(self):
        schema = schema_after(VisionContractTest.doc, SCHEMA_ANCHOR_DOC)
        return schema, {
            "schema_version": schema["schema_version"], "region_id": "A1", "status": "defect", "observed_object": "unclear",
            "defects": [{"type": "A_into_B", "panel_id": "P1", "normalized_points": [[0.25, 0.5]], "confidence": 0.5, "visible_evidence": "wedge"}],
            "views_consistent": True, "next_view": "none", "reason": "synthetic",
        }

    def test_malformed_nested_shapes_return_violations_instead_of_raising(self):
        schema, good = self.good()

        def with_defect(**change):
            return dict(good, defects=[dict(good["defects"][0], **change)])

        cases = {
            "status is a list": dict(good, status=["clean"]),
            "status is an object": dict(good, status={"a": 1}),
            "region_id is a list": dict(good, region_id=["A1"]),
            "region_id is null": dict(good, region_id=None),
            "next_view is a list": dict(good, next_view=["none"]),
            "next_view is an object": dict(good, next_view={"a": 1}),
            "views_consistent is a list": dict(good, views_consistent=[True]),
            "defects is null": dict(good, defects=None),
            "defects is a string": dict(good, defects="abc"),
            "defects is an object": dict(good, defects={"a": 1}),
            "a defect is null": dict(good, defects=[None]),
            "a defect is a string": dict(good, defects=["abc"]),
            "a defect is a list": dict(good, defects=[[1, 2]]),
            "panel_id is a list": with_defect(panel_id=["P1"]),
            "type is a list": with_defect(type=["A_into_B"]),
            "points is null": with_defect(normalized_points=None),
            "points is a string": with_defect(normalized_points="ab"),
            "points is an object": with_defect(normalized_points={"a": 1}),
            "a point is null": with_defect(normalized_points=[None]),
            "a point is a string": with_defect(normalized_points=["ab"]),
            "a point has three coordinates": with_defect(normalized_points=[[0.1, 0.2, 0.3]]),
            "a coordinate is a list": with_defect(normalized_points=[[[0.1], 0.2]]),
            "a coordinate is null": with_defect(normalized_points=[[None, 0.2]]),
            "confidence is a list": with_defect(confidence=[0.5]),
            "confidence is null": with_defect(confidence=None),
            "points is empty": with_defect(normalized_points=[]),
        }
        for label, response in cases.items():
            with self.subTest(label):
                try:
                    violations = validate_response(response, schema, {"A1"}, {"P1"})
                except Exception as exc:  # noqa: BLE001 - the point of the test: no exception may escape
                    self.fail(f"{label}: raised {type(exc).__name__} instead of returning violations")
                self.assertTrue(violations, label)

    def test_non_object_responses_and_normal_cases_are_unchanged(self):
        schema, good = self.good()
        for response in (None, [], "x", 3, [good]):
            self.assertTrue(validate_response(response, schema, {"A1"}, {"P1"}), repr(response)[:30])
        self.assertEqual(validate_response(good, schema, {"A1"}, {"P1"}), [])
        self.assertEqual(validate_response(dict(good, status="clean", defects=[]), schema, {"A1"}, {"P1"}), [])
        for points, confidence in (([[0, 1]], 1), ([[0.0, 0.5]], 0), ([[1, 0.25]], 0.75)):
            ok = dict(good, defects=[dict(good["defects"][0], normalized_points=points, confidence=confidence)])
            self.assertEqual(validate_response(ok, schema, {"A1"}, {"P1"}), [])
        for change in ({"normalized_points": [[True, 0.5]]}, {"confidence": True}):  # JSON booleans are not numbers
            bad = dict(good, defects=[dict(good["defects"][0], **change)])
            self.assertTrue(validate_response(bad, schema, {"A1"}, {"P1"}))


class ScopeRoutingAndInsertionWordingTest(unittest.TestCase):
    """Correction 21: TEXTUAL guards only (not native rendering, geometry, slicing or fit proof)."""

    @staticmethod
    def doc(*parts):
        return " ".join(ROOT.joinpath(*parts).read_text(encoding="utf8").lower().split())

    def test_both_entries_keep_slicer_ui_painting_with_printing_and_send_geometry_to_cad(self):
        printing = self.doc("3d-printing-workflows", "SKILL.md")
        cad = self.doc("cad-modeling-and-reverse-engineering", "SKILL.md")
        self.assertNotIn("(including painted-3mf edits and repair)", printing)
        for name, text, extra in (("printing", printing, ("standalone",)), ("cad", cad, ("standalone", "new-solid"))):
            for needle in ("slicer ui", "print-side tool assignment") + extra:
                self.assertIn(needle, text, f"{name} entry: {needle}")

    def test_support_reference_names_the_ui_painting_scope_and_routes_solid_building_to_geometry(self):
        text = self.doc("3d-printing-workflows", "references", "orca-support-interfaces-and-first-layer.md")
        first, rest = text.split("## 2.", 1)
        self.assertIn("slicer ui", first)
        six = rest.split("## 6.", 1)[1].split("## 7.", 1)[0]
        for needle in ("geometry workflow", "not a finished geometry repair", "decides opacity and material intent", "verifies the resulting slice", "align to the local normal"):
            self.assertIn(needle, six, needle)
        self.assertNotIn("this is a slicer-level repair, not a cad boolean", six)

    def test_fit_reference_does_not_call_discrete_samples_a_complete_collision_free_path(self):
        text = self.doc("cad-modeling-and-reverse-engineering", "references", "fit-clearance-and-retention.md")
        for old in ("across a sampled sweep", "along a sampled continuous sweep"):
            self.assertNotIn(old, text)
        for needle in ("swept-volume", "inter-sample", "provisional", "exceeds the maximum", "exact target mesh", "every orientation"):
            self.assertIn(needle, text, needle)

