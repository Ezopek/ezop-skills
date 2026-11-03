"""Standard-library synthetic tests; shared fixtures are not production validators."""
from test_skill_packages import (
    PRINT_SCRIPTS,
    Path,
    SEAM,
    SPARSE,
    TmpCase,
    VALID_ARC,
    json,
    make_symlink,
    mock,
    os,
    run_script,
    socket,
    tempfile,
    unittest,
)
from test_skill_packages import ast  # added for the correction-18 documentation pins
import collections  # added for the correction-21 bounded lookup spy
from test_skill_packages import _run, contextlib, importlib, io, sys  # added for the correction-21 work-budget witnesses


class NetworkTripwireTest(unittest.TestCase):
    def test_socket_use_is_denied(self):
        s = socket.socket()
        self.addCleanup(s.close)
        with self.assertRaises(RuntimeError):
            s.connect(("127.0.0.1", 9))



class SeamAnalyserTest(TmpCase):
    script = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"

    def run_seam(self, text, *args):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        return run_script(self.script, [g, *args])

    def test_counts_on_synthetic_gcode(self):
        code, out, _ = self.run_seam(SEAM, "--target-gap-mm", "0.04", "--expected-retraction-mm", "0.8")
        self.assertEqual(code, 0)
        self.assertIn("all_paths=2 layers=1", out)
        self.assertIn("paths=2 closed=1 (50.0%)", out)
        self.assertIn("paths_near_target_gap_0.04mm=1/2", out)
        self.assertIn("paths_with_retract=1/2", out)
        self.assertIn("full_retract_deretract_near_0.8mm=1/2", out)
        self.assertIn("prev_direct_travel_below_2mm=1/1", out)

    def test_mutation_without_retraction_changes_result(self):
        mutated = SEAM.replace("G1 E-0.8\n", "").replace("G1 E0.8\n", "")
        _, out, _ = self.run_seam(mutated)
        self.assertIn("paths_with_retract=0/2", out)
        self.assertNotIn("paths_with_retract=1/2", out)

    def test_target_gap_miss_is_reported(self):
        _, out, _ = self.run_seam(SEAM, "--target-gap-mm", "0.5")
        self.assertIn("paths_near_target_gap_0.5mm=0/2", out)

    def test_absolute_extrusion_is_refused(self):
        code, _, _ = self.run_seam(SEAM.replace("M83", "M82"))
        self.assertIsInstance(code, str)
        self.assertIn("Unsupported active M82", code)

    def assert_refused(self, text, needle, *args):
        code, out, _ = self.run_seam(text, *args)
        self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
        self.assertIn(needle, code)

    def test_extrusion_before_m83_is_refused(self):
        self.assert_refused(SEAM.replace("M83\n", ""), "M83")

    def test_mode_commands_are_parsed_exactly_not_by_text(self):
        # M82 with an attached comment is still M82
        self.assert_refused(SEAM.replace("M83", "M82;absolute"), "M82")
        # mode words inside comments change nothing
        commented = SEAM.replace(";LAYER_CHANGE", ";M82 and G91 are only mentioned here\n; G91\n;LAYER_CHANGE")
        _, out, _ = self.run_seam(commented)
        self.assertIn("all_paths=2 layers=1", out)
        # an inline comment with axis words must not be read as parameters
        inline = SEAM.replace("G1 X20 Y20 E1.0", "G1 X20 Y20 E1.0 ; E-9 X99")
        _, out, _ = self.run_seam(inline, "--target-gap-mm", "0.04")
        self.assertIn("all_paths=2 layers=1", out)
        self.assertIn("paths_near_target_gap_0.04mm=1/2", out)

    def test_relative_xy_motion_is_refused_but_empty_g91_block_is_fine(self):
        self.assert_refused(SEAM.replace("G1 X20 Y10 E1.0", "G91\nG1 X20 Y10 E1.0"), "G91")
        _, out, _ = self.run_seam(SEAM.replace("G1 X10 Y10 F3000", "G91\nG90\nG1 X10 Y10 F3000"))
        self.assertIn("all_paths=2 layers=1", out)

    def test_non_extruding_arc_is_refused_extruding_arc_is_endpoint_exact(self):
        self.assert_refused(SEAM.replace("G1 X10.5 Y10.5\n", "G2 X10.5 Y10.5 I0.25 J0\n"), "arc")
        arc_extrusion = SEAM.replace("G1 X20.5 Y10.5 E1.0", "G2 X20.5 Y10.5 I5 J0 E1.0")
        _, out, _ = self.run_seam(arc_extrusion, "--target-gap-mm", "0.04")
        self.assertIn("all_paths=2 layers=1", out)
        self.assertIn("paths_near_target_gap_0.04mm=1/2", out)



class SparseScrapeTest(TmpCase):
    script = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"

    def run_sparse(self, text):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        report = self.tmp / "report.json"
        code, out, _ = run_script(self.script, [g, report])
        self.assertEqual(code, 0)
        return json.loads(report.read_text())["counts"]

    def test_no_hop_crossing_is_counted(self):
        c = self.run_sparse(SPARSE)
        self.assertEqual(c["sparse_xy_travels"], 3)
        self.assertEqual(c["sparse_straight_extrusions"], 1)
        self.assertEqual(c["sparse_travels_cross_prior_sparse"], 1)
        self.assertEqual(c["no_hop_travels_cross_prior_sparse"], 1)
        self.assertNotIn("sparse_travels_hopped", c)

    def test_mutation_with_z_hop_removes_no_hop_crossing(self):
        mutated = SPARSE.replace("G1 X1 Y10 F6000", "G1 Z0.8 F1000\nG1 X1 Y10 F6000")
        c = self.run_sparse(mutated)
        self.assertEqual(c["sparse_travels_hopped"], 1)
        self.assertEqual(c["sparse_travels_cross_prior_sparse"], 1)
        self.assertNotIn("no_hop_travels_cross_prior_sparse", c)

    def test_bad_usage_is_refused(self):
        code, _, _ = run_script(self.script, [])
        self.assertIsInstance(code, str)
        self.assertIn("usage", code)

    def refused(self, text, needle):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        code, _, _ = run_script(self.script, [g, self.tmp / "report.json"])
        self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
        self.assertIn(needle, code)
        self.assertFalse((self.tmp / "report.json").exists(), "no report may be written on refusal")

    def test_extrusion_before_m83_and_m82_are_refused(self):
        self.refused(SPARSE.replace("M83\n", ""), "M83")
        self.refused(SPARSE.replace("M83", "M82;absolute"), "M82")

    def test_relative_xy_motion_is_refused_but_empty_g91_block_is_fine(self):
        self.refused(SPARSE.replace("G1 X11 Y0 F6000", "G91\nG1 X11 Y0 F6000"), "G91")
        c = self.run_sparse(SPARSE.replace("G1 X1 Y0 F6000", "G91\nG90\nG1 X1 Y0 F6000"))
        self.assertEqual(c["sparse_travels_cross_prior_sparse"], 1)

    def test_commands_are_parsed_exactly_not_by_text(self):
        commented = SPARSE.replace(";LAYER_CHANGE", "; G91 and M82 appear only in this comment\n;LAYER_CHANGE")
        self.assertEqual(self.run_sparse(commented)["sparse_travels_cross_prior_sparse"], 1)
        inline = SPARSE.replace("G1 X11 Y10 E1.0 F3000", "G1 X11 Y10 E1.0 F3000 ; E-2 X99")
        c = self.run_sparse(inline)
        self.assertEqual(c["sparse_straight_extrusions"], 1)
        self.assertEqual(c["sparse_travels_cross_prior_sparse"], 1)

    def test_valid_arc_fixture_really_has_no_crossing_on_its_sweep(self):
        # Fixture validity, independent of the analyser: arc from (11,0) to (1,10)
        # about centre (1,0) (I=-10, J=0), clockwise; earlier segment (1,0)->(11,10).
        import math

        cx, cy = 11 - 10, 0 + 0
        self.assertAlmostEqual(math.hypot(11 - cx, 0 - cy), math.hypot(1 - cx, 10 - cy))
        r = math.hypot(11 - cx, 0 - cy)
        sweep = (math.degrees(math.atan2(0 - cy, 11 - cx)) - math.degrees(math.atan2(10 - cy, 1 - cx))) % 360
        self.assertAlmostEqual(sweep, 270)
        s = r / math.hypot(10, 10)  # where segment (1,0)+s*(10,10) meets the circle
        hit = math.degrees(math.atan2(10 * s, 1 + 10 * s - cx)) % 360
        start = math.degrees(math.atan2(0 - cy, 11 - cx)) % 360
        on_sweep = (start - hit) % 360 <= sweep  # clockwise travel from the start angle
        self.assertFalse(on_sweep)
        # the straight chord (11,0)->(1,10) does cross the earlier segment
        self.assertIn("G2 X1 Y10 I-10 J0", VALID_ARC)

    def test_arc_travel_in_sparse_infill_is_refused_not_chord_approximated(self):
        self.refused(VALID_ARC, "arc")

    def test_arc_travel_outside_sparse_infill_is_not_refused(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(VALID_ARC.replace(";TYPE:Sparse infill", ";TYPE:Outer wall"))
        code, _, _ = run_script(self.script, [g, self.tmp / "report.json"])
        self.assertEqual(code, 0)



class SymlinkHelperTest(unittest.TestCase):
    def test_posix_failures_are_real_errors_not_skips(self):
        with mock.patch.object(os, "symlink", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                make_symlink("link", "target", _os_name="posix")

    def test_windows_privilege_failure_is_an_explicit_not_qualified_skip_never_a_pass(self):
        with mock.patch.object(os, "symlink", side_effect=OSError("A required privilege is not held by the client")):
            with self.assertRaises(unittest.SkipTest) as caught:
                make_symlink("link", "target", _os_name="nt")
        self.assertIn("NOT QUALIFIED", str(caught.exception))

    def test_a_real_symlink_is_created_with_os_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            target, link = Path(d) / "t.txt", Path(d) / "l.txt"
            target.write_text("x")
            make_symlink(link, target)
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), str(target))


class GcodeNumericAndArcGuardTest(TmpCase):
    """Correction 18 (bounded, synthetic): malformed/nonfinite motion words and unqualified full-circle arcs are refused
    by both analysers, and the sparse analyser refuses a report path that aliases its source. This is not a G-code
    interpreter: only the X/Y/Z/E/F/I/J/R words of G0-G3 are checked, and no arc geometry is computed."""

    seam = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"
    sparse = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"
    # (admitted letter, appended raw word, raw value that the message must never echo)
    BAD_WORDS = {
        "malformed E": ("E", "Ezzq", "zzq"),
        "NaN X": ("X", "Xnan", "nan"),
        "NaN Y mixed case": ("Y", "YNaN", "nan"),
        "infinite Z": ("Z", "Zinf", "inf"),
        "negative infinity X": ("X", "X-infinity", "infinity"),
        "overflowing X": ("X", "X1e999", "1e999"),
        "malformed F": ("F", "Fqq", "qq"),
        "malformed number X": ("X", "X1.2.3", "1.2.3"),
        "empty E value": ("E", "E", None),
        "underscore digit separator X": ("X", "X1_0", "1_0"),  # float() would accept this; G-code does not
    }

    def seam_text(self, text):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        return run_script(self.seam, [g])

    def sparse_text(self, text, report=None):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        report = report or self.tmp / "report.json"
        report.unlink(missing_ok=True)  # clean slate: a report written by an earlier (wrongly accepted) subcase must not mask this one
        return run_script(self.sparse, [g, report]), report

    SEAM_LINE = "G1 X20 Y20 E1.0"  # line 8 of the shared SEAM fixture
    SPARSE_LINE = "G1 X11 Y10 E1.0 F3000"  # line 7 of the shared SPARSE fixture

    def test_seam_refuses_malformed_and_nonfinite_motion_words_by_line_and_field_without_echo(self):
        for label, (letter, word, raw) in self.BAD_WORDS.items():
            with self.subTest(label):
                code, out, _ = self.seam_text(SEAM.replace(self.SEAM_LINE, f"{self.SEAM_LINE} {word}"))
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("line 8", code)
                self.assertIn(f"{letter} word", code)
                if raw:
                    self.assertNotIn(raw, code.lower(), "the raw input must not be echoed")
                self.assertNotIn("all_paths", out, "no success output may be produced")

    def test_sparse_refuses_malformed_and_nonfinite_motion_words_by_line_and_field_without_echo(self):
        for label, (letter, word, raw) in self.BAD_WORDS.items():
            with self.subTest(label):
                (code, out, _), report = self.sparse_text(SPARSE.replace(self.SPARSE_LINE, f"{self.SPARSE_LINE} {word}"))
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("line 7", code)
                self.assertIn(f"{letter} word", code)
                if raw:
                    self.assertNotIn(raw, code.lower(), "the raw input must not be echoed")
                self.assertFalse(report.exists(), "no report may be written on refusal")
                self.assertEqual(out, "")

    def test_control_comments_unadmitted_letters_and_valid_numbers_are_still_accepted(self):
        for label, line in {
            "bad words only inside a comment": f"{self.SEAM_LINE} ; Ebad Xnan",
            "an unadmitted letter is not a motion number": f"{self.SEAM_LINE} Pzz",
            "signed exponent numbers": "G1 X2.0e1 Y+20 E+1.0e0",
        }.items():
            with self.subTest(label):
                code, out, _ = self.seam_text(SEAM.replace(self.SEAM_LINE, line))
                self.assertEqual(code, 0)
                self.assertIn("all_paths=2 layers=1", out)
        (code, _, _), report = self.sparse_text(SPARSE.replace(self.SPARSE_LINE, f"{self.SPARSE_LINE} ; Ebad Xnan"))
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())

    # -- unqualified full-circle arcs: refused, never interpreted ------------------------------------
    CIRCLES = {
        "extruding, no end point": "G2 I5 J0 E1.0",
        "extruding, explicit start as end point": "G3 X{x} Y{y} I5 J0 E1.0",
        "extruding, radius form": "G2 R5 E1.0",
        "travel, no end point": "G3 I5 J0",
        "travel, J only": "G2 J5",
    }

    def test_seam_refuses_full_circle_arcs_before_they_can_look_like_a_no_op(self):
        base = "G1 X20.5 Y10.5 E1.0"  # last line of SEAM; the pen is at (10.5, 10.5) before it
        for label, arc in self.CIRCLES.items():
            for variant, text in {
                "replacing the last move": SEAM.replace(base, arc.format(x="10.5", y="10.5")),
                "inserted before the de-retract": SEAM.replace("G1 E0.8\n", arc.format(x="10.5", y="10.5") + "\nG1 E0.8\n"),
            }.items():
                with self.subTest(f"{label} / {variant}"):
                    code, out, _ = self.seam_text(text)
                    self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}: {out[:60]}")
                    self.assertIn("full circle", code)
                    self.assertIn("line ", code)

    def test_sparse_refuses_full_circle_arcs_in_any_role_before_they_count_as_deretraction(self):
        for role in ("Sparse infill", "Outer wall"):
            for label, arc in self.CIRCLES.items():
                with self.subTest(f"{role} / {label}"):
                    text = SPARSE.replace(";TYPE:Sparse infill", f";TYPE:{role}") + arc.format(x="1", y="10") + "\n"
                    (code, out, _), report = self.sparse_text(text)
                    self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                    if role == "Outer wall" or any(word.startswith("E") for word in arc.split()):  # a sparse-infill TRAVEL circle was already refused (with older wording)
                        self.assertIn("full circle", code)
                    self.assertFalse(report.exists(), "no report may be written on refusal")
                    self.assertEqual(out, "")

    def test_control_a_non_extruding_circle_under_sparse_infill_was_already_refused(self):
        (code, _, _), report = self.sparse_text(SPARSE + "G3 I5 J0\n")
        self.assertIsInstance(code, str)
        self.assertIn("arc", code)
        self.assertFalse(report.exists())

    def test_control_arcs_with_a_distinct_end_point_and_straight_moves_still_work(self):
        code, out, _ = self.seam_text(SEAM.replace("G1 X20.5 Y10.5 E1.0", "G2 X20.5 Y10.5 I5 J0 E1.0"), )
        self.assertEqual(code, 0)
        self.assertIn("all_paths=2 layers=1", out)
        (code, _, _), report = self.sparse_text(VALID_ARC.replace(";TYPE:Sparse infill", ";TYPE:Outer wall"))
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())

    # -- sparse report path must not alias the source -------------------------------------------------
    def test_sparse_refuses_a_report_path_that_aliases_the_source_before_writing_anything(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        before = g.read_bytes()
        (self.tmp / "sub").mkdir()
        symlink, hardlink = self.tmp / "sym.json", self.tmp / "hard.json"
        make_symlink(symlink, g)
        os.link(g, hardlink)
        entries = {p.name for p in self.tmp.iterdir()}
        aliases = {
            "the same path": g,
            "a normalised path": self.tmp / "sub" / ".." / "synthetic.gcode",
            "a symlink": symlink,
            "a hardlink": hardlink,
        }
        for label, target in aliases.items():
            with self.subTest(label):
                code, out, _ = run_script(self.sparse, [g, target])
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("same file", code)
                self.assertEqual(g.read_bytes(), before, "the source must stay unchanged")
                self.assertEqual({p.name for p in self.tmp.iterdir()}, entries, "no stray output")
                self.assertEqual(out, "")

    def test_control_a_distinct_sibling_report_still_works_and_the_source_is_untouched(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        before = g.read_bytes()
        report = self.tmp / "sibling-report.json"
        code, _, _ = run_script(self.sparse, [g, report])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(report.read_text())["counts"]["sparse_travels_cross_prior_sparse"], 1)
        self.assertEqual(g.read_bytes(), before)

    def test_scripts_and_references_state_the_new_refusals_without_claiming_a_full_interpreter(self):
        for script in (self.seam, self.sparse):
            doc = " ".join(ast.get_docstring(ast.parse(script.read_text(encoding="utf8"))).lower().split())  # line wrapping must not matter
            for needle in ("finite", "full-circle", "not echoed", "not a g-code interpreter"):
                self.assertIn(needle, doc, f"{script.name}: {needle}")
        self.assertIn("alias", " ".join(ast.get_docstring(ast.parse(self.sparse.read_text(encoding="utf8"))).lower().split()))
        refs = PRINT_SCRIPTS.parent / "references"
        tooling = (refs / "orca-audit-tooling.md").read_text(encoding="utf8").lower()
        for needle in ("malformed", "nonfinite", "full-circle", "alias", "not detected"):
            self.assertIn(needle, tooling, f"orca-audit-tooling.md: {needle}")
        for name in ("orca-seam-retraction-and-scrape.md",):
            text = (refs / name).read_text(encoding="utf8").lower()
            for needle in ("malformed", "full-circle", "alias"):
                self.assertIn(needle, text, f"{name}: {needle}")


class LayerZMetadataAndIdentityFaultTest(TmpCase):
    """Correction 23 (synthetic): declared layer-Z metadata (`;Z:`) must be a finite decimal number, in the sparse report path and
    in the seam helper; the sparse report is serialised strictly (no NaN/Infinity); and when the report destination exists but its
    identity cannot be compared with the source, the sparse helper refuses instead of writing. The identity cases are explicit
    I/O fault injection at the public entry point, not a demonstrated real-filesystem exploit; no locks or TOCTOU guarantees."""

    sparse = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"
    seam = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"
    # (label, raw ;Z: payload, fragment of it that the message must never echo)
    BAD_Z = {
        "nan": ("nan", "nan"),
        "NaN mixed case": ("NaN", "nan"),
        "positive infinity": ("inf", "inf"),
        "negative infinity": ("-inf", "inf"),
        "signed infinity word": ("+Infinity", "infinity"),
        "overflowing exponent": ("1e999", "1e999"),
        "malformed text": ("abc", "abc"),
        "number followed by text": ("0.2x", "0.2x"),
        "empty": ("", None),
    }

    def strict_json(self, path):
        def refuse(name):
            raise AssertionError(f"nonstandard JSON constant {name} in the report")
        return json.loads(Path(path).read_text(), parse_constant=refuse)

    def test_sparse_refuses_malformed_or_nonfinite_layer_z_before_writing_any_report(self):
        for label, (payload, raw) in self.BAD_Z.items():
            with self.subTest(label):
                g = self.tmp / "synthetic.gcode"
                g.write_text(SPARSE.replace(";Z:0.2", f";Z:{payload}"))
                self.assertIn(f";Z:{payload}", g.read_text())
                report = self.tmp / "report.json"
                report.unlink(missing_ok=True)
                code, out, _ = run_script(PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py", [g, report])
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("line 4", code)
                self.assertIn(";Z:", code)
                if raw:
                    self.assertNotIn(raw, code.lower(), "the raw metadata must not be echoed")
                self.assertFalse(report.exists(), "no report may be written")
                self.assertEqual(out, "")

    def test_seam_refuses_malformed_or_nonfinite_layer_z(self):
        for label, (payload, raw) in self.BAD_Z.items():
            with self.subTest(label):
                g = self.tmp / "synthetic.gcode"
                g.write_text(SEAM.replace(";Z:0.2", f";Z:{payload}"))
                code, out, _ = run_script(self.seam, [g])
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("line 4", code)
                self.assertIn(";Z:", code)
                if raw:
                    self.assertNotIn(raw, code.lower())
                self.assertEqual(out, "")

    def test_control_finite_layer_z_in_ordinary_forms_is_still_accepted_and_the_report_is_strict_json(self):
        for payload in ("0.2", "+0.2", ".2", "2e-1", " 0.2"):
            with self.subTest(payload):
                g = self.tmp / "synthetic.gcode"
                g.write_text(SPARSE.replace(";Z:0.2", f";Z:{payload}"))
                report = self.tmp / "report.json"
                report.unlink(missing_ok=True)
                code, _, _ = run_script(self.sparse, [g, report])
                self.assertEqual(code, 0)
                data = self.strict_json(report)
                self.assertAlmostEqual(data["travel_crossing_examples"][0]["nominal_z"], 0.2)
        g = self.tmp / "seam.gcode"
        g.write_text(SEAM.replace(";Z:0.2", ";Z:2e-1"))
        code, out, _ = run_script(self.seam, [g])
        self.assertEqual(code, 0)
        self.assertIn("all_paths=2", out)

    def test_the_sparse_report_is_serialised_strictly_and_a_nonfinite_value_writes_nothing(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        report = self.tmp / "report.json"
        with mock.patch.object(__import__("statistics"), "median", return_value=float("nan")):
            code, out, _ = run_script(self.sparse, [g, report])
        self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
        self.assertFalse(report.exists(), "no report may be written")
        self.assertEqual(out, "")

    # -- identity cannot be determined: fail closed -----------------------------------------------------------
    def prepared(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        report = self.tmp / "existing-report.json"
        report.write_text("SENTINEL: a different file that must survive a refusal\n")
        return g, report

    def test_an_existing_report_whose_identity_cannot_be_compared_is_refused_and_left_untouched(self):
        for label, fault in {
            "PermissionError": PermissionError("synthetic permission fault"),
            "generic OSError": OSError(5, "synthetic I/O fault"),
        }.items():
            with self.subTest(label):
                g, report = self.prepared()
                source_before, report_before = g.read_bytes(), report.read_bytes()
                with mock.patch.object(os.path, "samefile", side_effect=fault):
                    code, out, _ = run_script(self.sparse, [g, report])
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("identity", code)
                self.assertEqual(g.read_bytes(), source_before, "the source stays unchanged")
                self.assertEqual(report.read_bytes(), report_before, "the existing destination must not be overwritten")
                self.assertEqual(out, "")

    def test_control_a_confirmed_missing_destination_proceeds_even_if_the_identity_check_is_unavailable(self):
        g, _ = self.prepared()
        report = self.tmp / "brand-new-report.json"
        with mock.patch.object(os.path, "samefile", side_effect=PermissionError("synthetic permission fault")):
            code, _, _ = run_script(self.sparse, [g, report])
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())

    def test_control_an_existing_distinct_report_is_still_replaced_and_real_aliases_are_still_refused(self):
        g, report = self.prepared()
        code, _, _ = run_script(self.sparse, [g, report])
        self.assertEqual(code, 0)
        self.assertNotIn("SENTINEL", report.read_text())
        link, hard = self.tmp / "sym.json", self.tmp / "hard.json"
        make_symlink(link, g)
        os.link(g, hard)
        before = g.read_bytes()
        for alias in (g, link, hard):
            code, _, _ = run_script(self.sparse, [g, alias])
            self.assertIsInstance(code, str)
            self.assertIn("same file", code)
        self.assertEqual(g.read_bytes(), before)

    def test_the_seam_reference_states_the_metadata_and_identity_rules(self):
        refs = PRINT_SCRIPTS.parent / "references"
        text = " ".join((refs / "orca-seam-retraction-and-scrape.md").read_text(encoding="utf8").lower().split())
        for needle in ("layer-z", "finite", "identity cannot be determined", "strict json"):
            self.assertIn(needle, text, needle)
        for script in (self.sparse, self.seam):
            doc = " ".join(ast.get_docstring(ast.parse(script.read_text(encoding="utf8"))).lower().split())
            self.assertIn("layer-z", doc, script.name)
        sparse_doc = " ".join(ast.get_docstring(ast.parse(self.sparse.read_text(encoding="utf8"))).lower().split())
        for needle in ("identity cannot be determined", "strict json"):
            self.assertIn(needle, sparse_doc, needle)


class SeamFiniteDerivedMetricsTest(TmpCase):
    """Correction 29 (tiny synthetic files only, no workload): individually finite words can still overflow a DERIVED value (a coordinate
    difference, a hypot, an accumulated travel/E total, an even-length median). The seam helper must refuse a nonfinite tracked or reported
    metric clearly and produce NO stdout at all; ordinary results stay byte-for-byte unchanged and large but representable values still work.
    The numeric CLI options feed the same report, so they must be finite too. No physical coordinate cap and no new G-code feature."""

    seam = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"
    HEADER = "G90\nM83\n;LAYER_CHANGE\n;Z:0.2\n;TYPE:Outer wall\n"
    # Captured from the helper BEFORE this correction on the shared SEAM fixture; "{gcode}" stands for the input path.
    GOLDEN = (
        "gcode={gcode}\nall_paths=2 layers=1\n\n[Outer wall]\npaths=2 closed=1 (50.0%)\n"
        "gap_mm min/p10/median/p90/max=0.04000/0.04000/5.02000/10.00000/10.00000\ncommon_gap_buckets={{0.04: 1, 10.0: 1}}\n"
        "prev_direct_travel_below_2mm=1/1 (100.0%)\npaths_with_retract=1/2 (50.0%)\n\n[Inner wall]\npaths=0 closed=0 (0.0%)\n"
        "paths_with_retract=0/0 (0.0%)\n\n[Representative short-hop outer paths with retraction]\n"
        "layer=0 z=0.20 gap=10.00000 prev_direct=0.6794 actual_nonextrude=0.679 retract=0.800 deretract=0.800 start=(10.5, 10.5) end=(20.5, 10.5)\n"
    )
    OVERFLOWS = {
        "a coordinate difference overflows": "G1 X-1e308 Y0 F3000\nG1 X1e308 Y0 E1.0\n",
        "each difference is finite but the hypot overflows": "G1 X1.3e308 Y1.3e308 E1.0 F3000\n",
        "two finite gaps give an overflowing even median": "G1 X0 Y0 F3000\nG1 X1e308 Y0 E1.0\nG1 X0 Y0\nG1 X1e308 Y0 E1.0\n",
        "the accumulated positive E of a path overflows": "G1 X1 Y0 F3000\nG1 X2 Y0 E1e308\nG1 X3 Y0 E1e308\n",
        "a non-extruding move's own distance overflows": "G1 X-1e308 Y0 F3000\nG1 X1e308 Y0\n",
        "the accumulated non-extruding travel sums overflow": "G1 X-1e308 Y0 F3000\nG1 X0 Y0\nG1 X1e308 Y0\n",
        "the accumulated retraction overflows": "G1 E-1e308\nG1 E-1e308\n",
        "the accumulated de-retraction overflows": "G1 E1e308\nG1 E1e308\n",
    }

    def run_text(self, body, *args):
        g = self.tmp / "synthetic.gcode"
        g.write_text(self.HEADER + body)
        return run_script(self.seam, [g, *args])

    def test_a_nonfinite_derived_metric_is_refused_with_no_stdout_at_all(self):
        for label, body in self.OVERFLOWS.items():
            with self.subTest(label):
                code, out, _ = self.run_text(body)
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("finite", code)
                self.assertIn("line", code)
                self.assertEqual(out, "", "no partial or successful report may be printed")
                for raw in ("inf", "nan"):
                    self.assertNotIn(raw, code.lower().replace("finite", ""), "the message must not echo a nonfinite value")

    def test_control_large_but_representable_values_still_work_and_print_finite_numbers(self):
        cases = {
            "two large finite gaps and their median": "G1 X0 Y0 F3000\nG1 X1e300 Y0 E1.0\nG1 X0 Y0\nG1 X1e300 Y0 E1.0\n",
            "a large finite coordinate span": "G1 X-1e300 Y0 F3000\nG1 X1e300 Y0 E1.0\n",
            "large finite E totals": "G1 X1 Y0 F3000\nG1 X2 Y0 E1e300\nG1 X3 Y0 E1e300\n",
            "large finite retraction totals": "G1 E-1e300\nG1 E-1e300\nG1 X1 Y0 F3000\nG1 X2 Y0 E1.0\n",
        }
        for label, body in cases.items():
            with self.subTest(label):
                code, out, _ = self.run_text(body)
                self.assertEqual(code, 0)
                self.assertIn("all_paths=", out)
                report = out.split("\n", 1)[1]  # skip the gcode=<path> line: a random temp-dir name must not decide this check
                self.assertNotIn("inf", report.lower())
                self.assertNotIn("nan", report.lower())

    def test_control_the_ordinary_default_output_is_byte_for_byte_unchanged(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SEAM)
        code, out, _ = run_script(self.seam, [g])
        self.assertEqual(code, 0)
        self.assertEqual(out, self.GOLDEN.format(gcode=g))

    def test_every_numeric_cli_option_must_be_finite(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SEAM)
        for option in ("--short-travel-mm", "--closed-loop-max-gap-mm", "--target-gap-mm", "--target-gap-tolerance-mm",
                       "--expected-retraction-mm", "--retraction-tolerance-mm"):
            for value in ("nan", "inf", "-inf", "1e999"):
                with self.subTest(f"{option} {value}"):
                    code, out, err = run_script(self.seam, [g, f"{option}={value}"])  # `=` form: argparse would read a bare -inf as an option flag
                    self.assertEqual(code, 2, (out, err))
                    self.assertIn("finite", err)
                    self.assertEqual(out, "")

    def test_control_large_finite_cli_values_and_ordinary_values_are_accepted(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SEAM)
        code, out, _ = run_script(self.seam, [g, "--short-travel-mm", "1e300", "--target-gap-mm", "0.04", "--target-gap-tolerance-mm", "1e300",
                                              "--expected-retraction-mm", "0.8", "--retraction-tolerance-mm", "1e300", "--closed-loop-max-gap-mm", "1e300"])
        self.assertEqual(code, 0)
        report = out.split("\n", 1)[1]  # skip the gcode=<path> line
        self.assertNotIn("nan", report.lower())
        self.assertNotIn("inf", report.lower())

    def test_the_docstring_and_reference_state_the_finite_boundary(self):
        doc = " ".join(ast.get_docstring(ast.parse(self.seam.read_text(encoding="utf8"))).lower().split())
        for needle in ("derived", "overflow", "no output is printed", "finite"):
            self.assertIn(needle, doc, needle)
        refs = PRINT_SCRIPTS.parent / "references"
        for name in ("orca-audit-tooling.md", "orca-seam-retraction-and-scrape.md"):
            text = " ".join((refs / name).read_text(encoding="utf8").lower().split())
            for needle in ("derived", "overflow", "numeric command-line options"):
                self.assertIn(needle, text, f"{name}: {needle}")


class NearFullCircleToleranceTest(TmpCase):
    """Correction 29: the near-full-circle equivalence is documented as it really is. The sparse helper treats an arc end point as equal to its
    start when each of X and Y is within 1e-9 mm; the seam helper compares the end point to the start EXACTLY (no tolerance). Neither algorithm
    changed and no arc geometry is computed; only the documentation and the refusal texts say so."""

    sparse = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"
    seam = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"

    def sparse_run(self, arc):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE + arc + "\n")  # SPARSE ends at (1, 10)
        report = self.tmp / "report.json"
        report.unlink(missing_ok=True)
        return run_script(self.sparse, [g, report]), report

    def test_sparse_refusal_text_qualifies_the_tolerance_and_a_near_boundary_endpoint_is_still_refused(self):
        for label, arc in {
            "end point 5e-10 from the start in X": "G2 X1.0000000005 Y10 I5 J0 E1.0",
            "end point 5e-10 from the start in X and Y": "G3 X1.0000000005 Y10.0000000005 I5 J0 E1.0",
            "end point exactly the start": "G2 X1 Y10 I5 J0 E1.0",
        }.items():
            with self.subTest(label):
                (code, out, _), report = self.sparse_run(arc)
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("full circle", code)
                self.assertIn("within 1e-9 mm per X and per Y", code)
                self.assertFalse(report.exists())
                self.assertEqual(out, "")

    def test_control_sparse_arcs_clearly_outside_the_tolerance_are_still_accepted(self):
        for label, arc in {
            "end point 2e-9 from the start": "G2 X1.000000002 Y10 I5 J0 E1.0",
            "ordinary extruding arc with a distinct end point": "G2 X6 Y10 I5 J0 E1.0",
        }.items():
            with self.subTest(label):
                (code, _, _), report = self.sparse_run(arc)
                self.assertEqual(code, 0)
                self.assertTrue(report.exists())

    def seam_text(self, arc):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SEAM.replace("G1 X20.5 Y10.5 E1.0", arc))  # the pen is at (10.5, 10.5) before the replaced line
        return run_script(self.seam, [g])

    def test_the_seam_helper_compares_exactly_and_its_refusal_says_so(self):
        code, out, _ = self.seam_text("G2 X10.5 Y10.5 I5 J0 E1.0")
        self.assertIsInstance(code, str)
        self.assertIn("full circle", code)
        self.assertIn("exactly", code)
        self.assertIn("no tolerance", code)
        self.assertEqual(out, "")
        # a distinct end point is not a full circle, however close: accepted as an end-point-only arc (documented, unchanged)
        code, out, _ = self.seam_text("G2 X10.5000000005 Y10.5 I5 J0 E1.0")
        self.assertEqual(code, 0)
        self.assertIn("all_paths=", out)

    def test_docstrings_and_both_references_document_the_actual_equivalence_rule(self):
        sparse_doc = " ".join(ast.get_docstring(ast.parse(self.sparse.read_text(encoding="utf8"))).lower().split())
        for needle in ("1e-9 mm", "per x and per y", "not exact equality"):
            self.assertIn(needle, sparse_doc, f"sparse docstring: {needle}")
        seam_doc = " ".join(ast.get_docstring(ast.parse(self.seam.read_text(encoding="utf8"))).lower().split())
        for needle in ("exactly", "no tolerance"):
            self.assertIn(needle, seam_doc, f"seam docstring: {needle}")
        refs = PRINT_SCRIPTS.parent / "references"
        for name in ("orca-audit-tooling.md", "orca-seam-retraction-and-scrape.md"):
            text = " ".join((refs / name).read_text(encoding="utf8").lower().split())
            for needle in ("1e-9 mm per x and per y", "compares its end point to the start exactly"):
                self.assertIn(needle, text, f"{name}: {needle}")


class SeamCliTruthfulnessTest(TmpCase):
    """Correction 27: `--travel-histogram-mm` was parsed and advertised but never used (two different thresholds gave byte-identical output),
    so it is REMOVED rather than given an unrequested feature. The documented ordinary options and the actual output are unchanged."""

    seam = PRINT_SCRIPTS / "analyze_orca_seam_gcode.py"

    def gcode(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SEAM)
        return g

    def test_the_obsolete_option_is_no_longer_accepted(self):
        g = self.gcode()
        for args in (["--travel-histogram-mm", "0.5", "1.0"], ["--travel-histogram-mm", "3"], ["--travel-histogram-mm=0.7"]):
            with self.subTest(args):
                code, out, err = run_script(self.seam, [g, *args])
                self.assertEqual(code, 2, (out, err))
                self.assertIn("unrecognized arguments", err)
                self.assertEqual(out, "")

    def test_the_help_text_no_longer_advertises_it_and_still_lists_the_documented_options(self):
        code, out, _ = run_script(self.seam, ["--help"])
        self.assertEqual(code, 0)
        self.assertNotIn("histogram", out.lower())
        for option in ("--short-travel-mm", "--closed-loop-max-gap-mm", "--target-gap-mm", "--target-gap-tolerance-mm",
                       "--expected-retraction-mm", "--retraction-tolerance-mm", "--examples"):
            self.assertIn(option, out, option)

    def test_control_the_documented_ordinary_cli_and_its_output_are_unchanged(self):
        g = self.gcode()
        code, default_out, _ = run_script(self.seam, [g])
        self.assertEqual(code, 0)
        for expected in ("all_paths=2 layers=1", "paths=2 closed=1 (50.0%)", "paths_with_retract=1/2", "prev_direct_travel_below_2mm=1/1"):
            self.assertIn(expected, default_out)
        self.assertNotIn("histogram", default_out.lower())
        code, explicit_out, _ = run_script(self.seam, [g, "--short-travel-mm", "2.0", "--examples", "10"])
        self.assertEqual(code, 0)
        self.assertEqual(explicit_out, default_out, "explicitly passing the default values changes nothing")
        code, other_out, _ = run_script(self.seam, [g, "--short-travel-mm", "0.1", "--target-gap-mm", "0.04", "--expected-retraction-mm", "0.8"])
        self.assertEqual(code, 0)
        self.assertIn("prev_direct_travel_below_0.1mm=", other_out)
        self.assertIn("paths_near_target_gap_0.04mm=1/2", other_out)


class ReportDestinationProbeFaultTest(TmpCase):
    """Correction 25 (synthetic fault injection, not a real filesystem incident): the sparse helper must tell a CONFIRMED missing
    report destination (an explicit lstat raising FileNotFoundError) from an UNDETERMINED one (any other OSError from the probe).
    An undetermined destination refuses before any write, with the source and the report untouched. The fault is injected at the
    `os.lstat` edge for the report path ONLY; no locks, TOCTOU or concurrent-rewrite guarantee is implied."""

    sparse = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"
    FAULTS = {
        "PermissionError": lambda: PermissionError(13, "synthetic permission fault"),
        "generic OSError": lambda: OSError("synthetic I/O fault"),
        "OSError with an errno": lambda: OSError(5, "synthetic I/O fault"),
        "NotADirectoryError": lambda: NotADirectoryError(20, "synthetic path-component fault"),
        "TimeoutError": lambda: TimeoutError("synthetic timeout fault"),
    }

    def lstat_fault(self, target, error):
        """An os.lstat replacement that raises `error` for exactly `target` and behaves normally for every other path."""
        real, target_text = os.lstat, os.fspath(target)

        def lstat(path, *args, **kwargs):
            if os.fspath(path) == target_text:
                raise error
            return real(path, *args, **kwargs)

        return mock.patch.object(os, "lstat", side_effect=lstat)

    def run_with_fault(self, source, report, error):
        with self.lstat_fault(report, error):
            return run_script(self.sparse, [source, report])

    def assert_refused_untouched(self, result, *files_and_bytes):
        code, out, _ = result
        self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
        self.assertIn("identity", code)
        self.assertEqual(out, "", "no success output may be produced")
        for path, before in files_and_bytes:
            self.assertEqual(Path(path).read_bytes(), before, f"{Path(path).name} must be untouched")

    def source(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        return g

    def test_an_undetermined_report_destination_that_is_the_source_itself_is_refused_and_the_source_survives(self):
        for label, make_error in self.FAULTS.items():
            with self.subTest(label):
                g = self.source()
                before = g.read_bytes()
                self.assert_refused_untouched(self.run_with_fault(g, g, make_error()), (g, before))

    def test_an_undetermined_distinct_existing_report_is_refused_and_both_files_survive(self):
        for label, make_error in self.FAULTS.items():
            with self.subTest(label):
                g = self.source()
                report = self.tmp / "existing-report.json"
                report.write_text("SENTINEL: a different file that must survive a refusal\n")
                self.assert_refused_untouched(self.run_with_fault(g, report, make_error()), (g, g.read_bytes()), (report, report.read_bytes()))

    def test_an_undetermined_report_path_that_is_a_symlink_to_the_source_is_refused_and_the_source_survives(self):
        for label, make_error in self.FAULTS.items():
            with self.subTest(label):
                g = self.source()
                link = self.tmp / "alias-report.json"
                link.unlink(missing_ok=True)
                make_symlink(link, g)
                before = g.read_bytes()
                self.assert_refused_untouched(self.run_with_fault(g, link, make_error()), (g, before))
                self.assertTrue(link.is_symlink())

    def test_a_missing_destination_is_written_only_when_the_probe_confirms_it_with_file_not_found(self):
        for label, error in {
            "a real missing path (no fault injected)": None,
            "an explicit FileNotFoundError from the probe": FileNotFoundError(2, "synthetic confirmed-missing"),
        }.items():
            with self.subTest(label):
                g = self.source()
                report = self.tmp / "brand-new-report.json"
                report.unlink(missing_ok=True)
                before = g.read_bytes()
                if error is None:
                    code, _, _ = run_script(self.sparse, [g, report])
                else:
                    code, _, _ = self.run_with_fault(g, report, error)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(report.read_text())["counts"]["sparse_travels_cross_prior_sparse"], 1)
                self.assertEqual(g.read_bytes(), before, "the source stays unchanged")

    def test_control_an_existing_distinct_report_is_replaced_and_real_aliases_are_still_refused(self):
        g = self.source()
        report = self.tmp / "existing-report.json"
        report.write_text("SENTINEL\n")
        code, _, _ = run_script(self.sparse, [g, report])
        self.assertEqual(code, 0)
        self.assertNotIn("SENTINEL", report.read_text())
        link, hard = self.tmp / "sym.json", self.tmp / "hard.json"
        make_symlink(link, g)
        os.link(g, hard)
        before = g.read_bytes()
        for alias in (g, link, hard):
            code, _, _ = run_script(self.sparse, [g, alias])
            self.assertIsInstance(code, str)
            self.assertIn("same file", code)
        self.assertEqual(g.read_bytes(), before)

    def test_control_a_samefile_fault_on_an_existing_report_still_refuses(self):
        g = self.source()
        report = self.tmp / "existing-report.json"
        report.write_text("SENTINEL\n")
        with mock.patch.object(os.path, "samefile", side_effect=PermissionError(13, "synthetic permission fault")):
            code, out, _ = run_script(self.sparse, [g, report])
        self.assertIsInstance(code, str)
        self.assertIn("identity", code)
        self.assertEqual(report.read_text(), "SENTINEL\n")

    def test_the_probe_is_an_explicit_lstat_and_not_a_boolean_that_collapses_io_errors(self):
        text = self.sparse.read_text(encoding="utf8")
        self.assertNotIn("os.path.lexists(target)", text, "lexists swallows every OSError and returns False")
        self.assertNotIn("target.exists()", text)
        self.assertIn("os.lstat(target)", text)
        self.assertIn("except FileNotFoundError", text)
        doc = " ".join(ast.get_docstring(ast.parse(text)).lower().split())
        for needle in ("lstat", "filenotfounderror", "confirmed missing"):
            self.assertIn(needle, doc, needle)


class LookupSentinel(RuntimeError):
    """Raised by the bounded spy so an unbounded grid enumeration is interrupted safely instead of run."""


class SparseWorkBudgetTest(TmpCase):
    """Correction 21 (synthetic, bounded): the sparse analyser charges a fixed per-invocation spatial work budget BEFORE any
    large bounding-box range, bucket traversal, candidate check or grid insertion. Heavy workloads are never run: huge
    coordinates are protected by a lookup spy that interrupts after a few lookups, and the accounting is checked on tiny
    inputs with a lowered module constant. The budget is an implementation guard, not OS containment or benchmarking."""

    sparse = PRINT_SCRIPTS / "analyze_orca_sparse_scrape.py"
    HEADER = "G90\nM83\n;LAYER_CHANGE\n;Z:0.2\n;TYPE:Sparse infill\n"
    SENTINEL_AFTER = 1000

    def spy_class(self):
        original = collections.defaultdict

        class Spy(original):
            lookups = 0

            def get(self, key, default=None):
                Spy.lookups += 1
                if Spy.lookups > SparseWorkBudgetTest.SENTINEL_AFTER:
                    raise LookupSentinel("bounded sentinel: grid enumeration interrupted")
                return super().get(key, default)

        return Spy

    def test_huge_coordinates_are_refused_before_any_grid_lookup_and_nothing_is_written(self):
        for label, move in {
            "an extrusion": "G1 X1000000000 Y1000000000 E1.0 F3000\n",
            "a travel": "G1 X1000000000 Y1000000000 F6000\n",
        }.items():
            with self.subTest(label):
                g = self.tmp / "synthetic.gcode"
                g.write_text(self.HEADER + move)
                before = g.read_bytes()
                report = self.tmp / "report.json"
                report.unlink(missing_ok=True)
                spy = self.spy_class()
                with mock.patch.object(collections, "defaultdict", spy):
                    code, out, _, exc = _run(self.sparse, [g, report])
                self.assertNotIsInstance(exc, LookupSentinel, "the run started enumerating grid cells and was interrupted by the bounded sentinel")
                self.assertIsNone(exc, repr(exc))
                self.assertIsInstance(code, str, f"expected a refusal, got exit {code!r}")
                self.assertIn("budget", code)
                self.assertIn("NOT DONE", code)
                self.assertEqual(spy.lookups, 0, "the refusal must come before any grid lookup")
                self.assertFalse(report.exists(), "no report may be written")
                self.assertEqual(g.read_bytes(), before, "the source stays unchanged")
                self.assertEqual(out, "")

    def run_limited(self, text, limit):
        g = self.tmp / "synthetic.gcode"
        g.write_text(text)
        report = self.tmp / "limited-report.json"
        report.unlink(missing_ok=True)
        spec = importlib.util.spec_from_file_location("sparse_budget_probe", self.sparse)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # __name__ is not "__main__", so nothing runs yet
        module.WORK_LIMIT = limit
        old_argv, code = sys.argv, 0
        sys.argv = [str(self.sparse), str(g), str(report)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                module.main()
        except SystemExit as exc:
            code = 0 if exc.code is None else exc.code
        finally:
            sys.argv = old_argv
        return code, report

    def test_an_ordinary_tiny_input_is_refused_under_a_lowered_budget_and_accepted_under_the_default(self):
        code, report = self.run_limited(SPARSE, 3)
        self.assertIsInstance(code, str, f"expected a refusal under a budget of 3, got exit {code!r}")
        self.assertIn("budget", code)
        self.assertFalse(report.exists())
        code, report = self.run_limited(SPARSE, 1_000_000)
        self.assertEqual(code, 0)
        self.assertTrue(report.exists())

    @staticmethod
    def simulated_units(moves):
        """Independent model of the documented accounting for absolute G1 moves in sparse infill: every grid call charges its
        bounding-box cell count; every candidate lookup charges each bucket's length (repeated entries included) and then the
        distinct candidate count; an extrusion also charges its insertion visits (its cell count again)."""
        cell = 5.0
        grid, total, (x, y), index = {}, 0, (0.0, 0.0), 0
        for nx, ny, extrudes in moves:
            if abs(nx - x) > 1e-9 or abs(ny - y) > 1e-9:
                if ((nx - x) ** 2 + (ny - y) ** 2) ** 0.5 > 1e-6:
                    x0, x1 = sorted((int(x // cell), int(nx // cell)))
                    y0, y1 = sorted((int(y // cell), int(ny // cell)))
                    keys = [(i, j) for i in range(x0, x1 + 1) for j in range(y0, y1 + 1)]
                    total += len(keys)
                    seen = set()
                    for key in keys:
                        total += len(grid.get(key, ()))
                        seen.update(grid.get(key, ()))
                    total += len(seen)
                    if extrudes:
                        total += len(keys)
                        for key in keys:
                            grid.setdefault(key, []).append(index)
                        index += 1
            x, y = nx, ny
        return total

    def test_the_budget_counts_cells_repeated_bucket_entries_candidate_checks_and_insertions_exactly(self):
        moves, lines = [], []
        for i in range(10):  # ten long parallel extrusions: each index sits in every cell of its row, so buckets repeat entries
            moves += [(0.0, float(i), False), (40.0, float(i), True)]
            lines += [f"G1 X0 Y{i} F6000", f"G1 X40 Y{i} E1.0 F3000"]
        moves.append((20.0, -1.0, False))  # a final travel that crosses every row
        lines.append("G1 X20 Y-1 F6000")
        text = self.HEADER + "\n".join(lines) + "\n"
        exact = self.simulated_units(moves)
        self.assertGreater(exact, 400, "fixture sanity: repeated traversal must dominate")
        code, report = self.run_limited(text, exact)
        self.assertEqual(code, 0, "the exact modelled total must fit its own budget")
        self.assertTrue(report.exists())
        code, report = self.run_limited(text, exact - 1)
        self.assertIsInstance(code, str, "one unit less than the modelled total must be refused (a charge is missing)")
        self.assertIn("budget", code)
        self.assertFalse(report.exists())

    def test_control_the_default_budget_leaves_the_existing_positive_fixtures_and_cli_alone(self):
        g = self.tmp / "synthetic.gcode"
        g.write_text(SPARSE)
        code, _, _ = run_script(self.sparse, [g, self.tmp / "sibling.json"])
        self.assertEqual(code, 0)

    def test_the_scripts_and_references_state_the_exact_budget_scope_without_overclaiming(self):
        doc = " ".join(ast.get_docstring(ast.parse(self.sparse.read_text(encoding="utf8"))).lower().split())
        for needle in ("1,000,000", "per invocation", "not done", "separately qualified bounded backend", "not os containment"):
            self.assertIn(needle, doc, f"sparse docstring: {needle}")
        refs = PRINT_SCRIPTS.parent / "references"
        for name in ("orca-audit-tooling.md", "orca-seam-retraction-and-scrape.md"):
            text = " ".join((refs / name).read_text(encoding="utf8").lower().split())
            for needle in ("1,000,000", "not done", "separately qualified bounded backend", "not os containment"):
                self.assertIn(needle, text, f"{name}: {needle}")

