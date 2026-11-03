"""Documentary migration-preservation checks: essential action/condition/key families that must stay in the shipped references.
Literal API keys, source basenames, SHA and version qualifiers only; no runtime, device or physical claim is tested."""
import re

from test_skill_packages import ROOT, unittest

CAD = ROOT / "cad-modeling-and-reverse-engineering" / "references"
PRINT = ROOT / "3d-printing-workflows" / "references"


def section(path, heading):
    """Collapsed, lower-cased text of the '## <heading>...' section (to the next '## ')."""
    text = path.read_text(encoding="utf8")
    start = text.index("\n## " + heading)
    end = text.find("\n## ", start + 4)
    return re.sub(r"\s+", " ", text[start:end if end > 0 else len(text)]).lower()


def remote_screen_problems(text):
    """Exact key/value code spans tied to their file and section (text is collapsed and lower-cased). A small walk over closed backtick spans
    tracks the current config file (`extended/...cfg`) and section (`[...]`); a `key: value` span is recorded under that pair. A bare
    substring such as `stream_url: /screen/` inside `stream_url: /screen/snapshot` never counts, a directive after another section is
    misplaced, and a required key with a second, different value in its section is a conflict. Not a general config or Markdown parser."""
    want = {("extended/extended2.cfg", "[web]"): {"remote_screen": "true"},
            ("extended/moonraker/04_remote_screen.cfg", "[webcam gui]"): {"enabled": "true", "service": "iframe", "stream_url": "/screen/",
                                                                          "snapshot_url": "/screen/snapshot", "aspect_ratio": "480:320"}}
    home = {key: ctx for ctx, pairs in want.items() for key in pairs}
    path = section_name = None
    seen = []
    for span in re.findall(r"`([^`\n]*)`", text):
        if re.fullmatch(r"extended/[\w/.]+\.cfg", span):
            path, section_name = span, None
        elif re.fullmatch(r"\[[^\]]+\]", span):
            section_name = span
        elif (pair := re.fullmatch(r"(\w+): (\S+)", span)):
            seen.append(((path, section_name), pair.group(1), pair.group(2)))
    problems = []
    for ctx, pairs in want.items():
        for key, value in pairs.items():
            values = {v for c, k, v in seen if c == ctx and k == key}
            if value not in values:
                problems.append(f"{key} missing under {ctx}")
            elif values != {value}:
                problems.append(f"{key} has conflicting values under {ctx}")
    return problems + [f"{key} misplaced under {ctx}" for ctx, key, _ in seen if key in home and ctx != home[key]]


class MigrationPreservationTest(unittest.TestCase):
    def has(self, text, *needles):
        for needle in needles:
            self.assertIn(needle.lower(), text, needle)

    def test_painted_project_replaces_source_vendor_filament_presets_after_the_printer_switch(self):
        self.has(section(CAD / "painted-3mf-editing.md", "A."), "source-vendor filament presets", "target-compatible material profiles", "tool/colour")

    def test_opt_in_persistent_corpus_is_durable_and_independent_of_the_workstation_without_a_default_target(self):
        text = section(CAD / "paint-label-repair.md", "7.")
        self.has(text, "durable", "independent of the workstation", "append-only", "content-addressed", "before", "pending", "never claim")
        self.has(text, "no default", "ordinary")
        self.assertNotIn("archive_paint_repair_case", text, "the deployment-specific helper must not become portable infrastructure")

    def test_support_opacity_gate_requires_zero_validation_failures(self):
        self.has(section(PRINT / "orca-support-interfaces-and-first-layer.md", "6."), "`FAIL: 0`", "solver crash")

    def test_orca_support_source_and_test_starting_pointers_are_kept_and_version_qualified(self):
        text = section(PRINT / "orca-support-interfaces-and-first-layer.md", "7.")
        self.has(text, "SupportCommon.cpp", "SupportMaterial.cpp", "TreeSupport3D.cpp", "TreeSupport.cpp", "area-group", "PrintConfig.hpp",
                 "Preset.cpp", "PrintObject.cpp", "src/slic3r/GUI/Tab.cpp", "ConfigManipulation.cpp", "tests/libslic3r",
                 "tests/fff_print/test_support_material.cpp", "revision", "checkout")

    def test_seam_gap_is_a_physical_loop_end_gap_that_needs_the_active_process_and_emitted_gcode(self):
        self.has(section(PRINT / "slicer-forks-builds-and-runtime.md", "1."), "seam_gap", "loop-end gap", "positive", "active process", "emitted g-code")

    def test_sensor_offset_characterisation_and_open_area_occlusion_are_kept(self):
        storage = PRINT / "filament-storage-and-desiccant.md"
        self.has(section(storage, "5."), "side by side", "two hours", "offset", "known trend sensor", "10–20", "lower clamp", "active")
        self.has(section(storage, "4."), "rails", "support posts", "occlu", "open-area")

    def test_remote_screen_needs_both_effective_controls_through_the_firmware_config_surface(self):
        text = section(PRINT / "snapmaker-u1-operations.md", "2.")
        self.has(text, "extended/extended2.cfg", "[web]", "remote_screen", "extended/moonraker/04_remote_screen.cfg", "[webcam gui]",
                 "service: iframe", "stream_url", "/screen/snapshot", "aspect_ratio", "480:320", "S99fb-http", "8092", "firmware-config")
        self.has(text, "remote_screen: true", "enabled: true", "explicitly authorised", "private network", "no wan exposure")
        self.assertEqual(remote_screen_problems(text), [])

    def test_afc_lite_requires_both_a_changer_and_a_deliberate_fluidd_mainsail_setup(self):
        text = section(PRINT / "snapmaker-u1-operations.md", "2.")
        self.assertRegex(text, r"keep afc lite disabled unless both a compatible external .*changer exists and a deliberate fluidd/mainsail setup")

    def test_timelapse_release_check_names_the_full_merge_commit(self):
        self.has(section(PRINT / "snapmaker-u1-operations.md", "6."), "15c081380a9302617b40bb6e01a307d5945eb1f2", "#806", "compare")

    def test_optional_release_watcher_is_conditional_and_not_a_default(self):
        owner = section(PRINT / "printer-control-and-safety.md", "7.")
        self.has(owner, "only when the operator asks", "semantic versions", "build numbers", "last notified tag", "transient", "changelog", "known-bug")
        operations = section(PRINT / "snapmaker-u1-operations.md", "2.")
        self.has(operations, "printer-control-and-safety.md", "section 7")
        self.assertNotIn("notify once per persisted tag", operations, "route to the existing owner instead of duplicating its procedure")

    def test_magnet_dry_fit_polarity_minimal_adhesive_and_full_cure(self):
        self.has(section(PRINT / "snapmaker-u1-multicolor-tuning.md", "4."), "dry-fit", "polarity", "before glu", "minimal adhesive", "cure")

    def test_ssh_scope_does_not_enable_vpn_or_cloud_and_controller_warnings_are_reported(self):
        safety = PRINT / "printer-control-and-safety.md"
        self.has(section(safety, "3."), "vpn", "cloud", "side effect")
        self.has(section(safety, "4."), "warnings", "failed components")

    def test_confirmed_region_override_keeps_identical_face_id_mappings(self):
        self.has(section(CAD / "paint-label-repair.md", "3."), "identical face-id mappings", "frozen baseline")

    def test_renderer_archive_names_the_production_wrapper_tests_and_commit_without_claiming_qualification(self):
        self.has(section(CAD / "vision-model-review.md", "3."), "production renderer wrapper", "commit", "does not claim")

    def test_manual_acrylic_cutting_is_a_conditional_case_specific_alternative_with_a_supplier_default(self):
        self.has(section(PRINT / "snapmaker-u1-multicolor-tuning.md", "4."), "straightedge", "score", "snap", "deburr", "manufacturer's instructions",
                 "eye protection", "case-specific", "supplier", "nominal")

    def test_support_interface_guards_side_aware_gap_negative_control_and_disabled_compatibility(self):
        text = section(PRINT / "orca-support-interfaces-and-first-layer.md", "7.")
        self.has(text, "nonzero same-material gap", "side-aware", "negative control", "live-vs-retired", "fail", "config-metadata", "not byte identity")

    def test_public_provenance_links_are_kept_without_the_unsupported_claim(self):
        storage = PRINT / "filament-storage-and-desiccant.md"
        self.has(section(storage, "2."), "technical bulletin 33", "silica-gel-relative-humidity.html", "ge0042_tds_en.pdf", "~800 kg/m", "youtu.be/8kIDLIXILKo",
                 "reported example", "not reproduced")
        self.has(section(storage, "4."), "engineeringtoolbox.com/air-diffusion-coefficient-gas-mixture-temperature-d_2010.html", "pub_id=957163", "background")
        self.has(section(storage, "6."), "job", "callback", "private test log")

    def test_nozzle_volume_advice_is_scoped_to_the_same_hotend_and_nozzle_family_and_version_qualified(self):
        self.has(section(PRINT / "slicer-semantics-and-evidence.md", "4."), "same hotend and the same nozzle family", "orca source", "verify the exact fork and version")

    def test_remote_workstation_staging_verifies_the_destination_before_the_usb_copy(self):
        self.has(section(PRINT / "snapmaker-u1-network-and-firmware.md", "3."), "remote-workstation", "operator-designated", ".part", "atomic", "path, size, hash", "exit status", "usb root")

    def test_touch_claim_needs_process_identity_and_input_permission_evidence(self):
        text = section(PRINT / "snapmaker-u1-operations.md", "2.")
        self.assertNotIn("(or an appropriately authorised functional check)", text, "a functional check does not waive the identity/permission prerequisite")
        self.has(text, "process identity", "uid", "input-device", "unverified", "identity/permission evidence")

    def test_remote_screen_pair_check_rejects_swapped_prefix_only_and_misplaced_mappings(self):
        good = ("`extended/extended2.cfg` `[web]` `remote_screen: true` and `extended/moonraker/04_remote_screen.cfg` `[webcam gui]` "
                "`enabled: true` `service: iframe` `stream_url: /screen/` `snapshot_url: /screen/snapshot` `aspect_ratio: 480:320`")
        self.assertEqual(remote_screen_problems(good), [])
        for label, bad in {
            "swapped stream and snapshot values": good.replace("`stream_url: /screen/`", "`stream_url: /screen/snapshot`").replace("`snapshot_url: /screen/snapshot`", "`snapshot_url: /screen/`"),
            "prefix-only stream_url": good.replace("`stream_url: /screen/` ", ""),
            "wrong aspect ratio": good.replace("480:320", "320:480"),
            "disabled front end": good.replace("`enabled: true`", "`enabled: false`"),
            "remote_screen false": good.replace("`remote_screen: true`", "`remote_screen: false`"),
            "remote_screen under the wrong file": good.replace("`[web]` `remote_screen: true` ", "`[web]` ").replace("`aspect_ratio: 480:320`", "`aspect_ratio: 480:320` `remote_screen: true`"),
            "front-end key under the wrong file": good.replace("`[web]` ", "`[web]` `service: iframe` "),
            "bare words without code spans": good.replace("`", ""),
        }.items():
            with self.subTest(label):
                self.assertNotEqual(remote_screen_problems(bad), [])

    def test_remote_screen_pair_check_ties_each_directive_to_its_section_and_rejects_conflicting_duplicates(self):
        good = ("`extended/extended2.cfg` `[web]` `remote_screen: true` and `extended/moonraker/04_remote_screen.cfg` `[webcam gui]` "
                "`enabled: true` `service: iframe` `stream_url: /screen/` `snapshot_url: /screen/snapshot` `aspect_ratio: 480:320`")
        self.assertEqual(remote_screen_problems(good), [])
        for span, section_token in (("remote_screen: true", "[web]"), ("enabled: true", "[webcam gui]"), ("service: iframe", "[webcam gui]"),
                                    ("stream_url: /screen/", "[webcam gui]"), ("snapshot_url: /screen/snapshot", "[webcam gui]"),
                                    ("aspect_ratio: 480:320", "[webcam gui]")):
            with self.subTest(f"{span} under an unrelated section"):
                bad = good.replace(f"`{span}`", f"`[unrelated]` `{span}` `{section_token}`")
                self.assertNotEqual(bad, good)
                self.assertNotEqual(remote_screen_problems(bad), [])
        for label, bad in {
            "conflicting duplicate front end": good + " `enabled: false`",
            "conflicting duplicate framebuffer": good.replace("`remote_screen: true`", "`remote_screen: true` `remote_screen: false`"),
            "right value masked under the wrong section": good.replace("`enabled: true`", "`enabled: false` `[unrelated]` `enabled: true` `[webcam gui]`"),
        }.items():
            with self.subTest(label):
                self.assertNotEqual(remote_screen_problems(bad), [])

    def test_the_actual_legacy_privacy_method_rejects_capture_before_target_forms_and_keeps_its_exemptions(self):
        from test_contracts import RealDesktopCaptureWordingTest as Legacy  # imported here so discovery does not collect it twice
        name = "test_real_desktop_or_window_capture_waits_for_the_operators_approval_not_just_an_announcement"

        def run(extra):
            case = Legacy(name)
            original = case.text
            # same normalisation as the class's own text() reader (lower-cased, whitespace collapsed)
            case.text = lambda *parts: original(*parts) + (" " + " ".join(extra.lower().split()) if extra and parts[-1] == "vision-model-review.md" else "")
            result = unittest.TestResult()
            case.run(result)
            self.assertEqual((result.testsRun, len(result.errors)), (1, 0), "the ACTUAL method must execute without a harness error")
            return result.wasSuccessful()

        self.assertTrue(run(None), "the unmodified vision doc must pass the real method")
        for extra in ("Capture the real desktop without operator approval.", "Capture the real desktop: no operator approval is required.",
                      "Capture a window without the operator's approval."):
            with self.subTest(extra):
                self.assertFalse(run(extra), "the actual method must reject a capture-before-target permission")
        for extra in ("An isolated virtual display or an offscreen synthetic render needs no approval.",
                      "Capture only after the operator's approval; an announcement alone is not approval."):
            with self.subTest(extra):
                self.assertTrue(run(extra), "valid exemptions and approval wording must still pass")

    def test_cross_fork_forensics_evidence_gate_requires_active_json_before_claiming_a_remembered_ui_setting(self):
        self.has(section(PRINT / "slicer-forks-builds-and-runtime.md", "1."), "saved custom", "genuine system bundle", "transient ui edits", "never assert",
                 "remembered ui setting", "active json")

    def test_audit_feedback_template_names_its_outcome_fields(self):
        self.has(section(PRINT / "orca-audit-tooling.md", "1."), "print-feedback.md", "physical outcome", "affected layer/z/xy", "photos", "material state",
                 "post-audit setting changes")

    def test_paint_label_repair_separates_two_allowed_target_repair_from_conservative_automatic_cleanup(self):
        text = section(CAD / "paint-label-repair.md", "2.")
        self.has(text, "leave components with mixed boundaries untouched", "two allowed target", "boundary-seeded graph cut", "fixed outside-edge",
                 "majority", "split", "audited again", "explicit", "not a blanket permission")
        self.has(text, "spatial band", "underside", "abstain", "cluster", "recorded threshold")

    def test_fork_profile_edit_starts_with_a_recoverable_copy_of_user_filament_directory_and_app_config(self):
        text = section(PRINT / "slicer-forks-builds-and-runtime.md", "1.")
        self.has(text, "before editing", "close the fork", "recoverable", "user filament directory", "app config", "restore")

    def test_ulimit_v_is_a_per_process_address_space_limit_not_aggregate_containment(self):
        text = section(PRINT / "slicer-forks-builds-and-runtime.md", "3.")
        self.has(text, "rlimit_as", "one process", "not aggregate", "cgroup", "memory.max", "memory.swap.max", "operator-approved", "pid", "not isolated",
                 "https://man7.org/linux/man-pages/man2/getrlimit.2.html", "https://docs.kernel.org/admin-guide/cgroup-v2.html")
        self.assertNotIn("`ulimit -v` or an isolated scope", text)
        self.assertNotIn("no scope means zero host risk", text)
        self.assertIn("no isolation scope guarantees zero host risk", text)

    def test_fullspectrum_vendor_and_community_are_distinct_and_the_cut_route_asks_for_a_dimensioned_drawing(self):
        tuning = PRINT / "snapmaker-u1-multicolor-tuning.md"
        self.has(section(tuning, "1."), "v2.3.3", "ratdoux/orcaslicer-fullspectrum", "historical", "verify the exact fork and version", "do not attribute", "four")
        text = section(tuning, "4.")
        self.has(text, "dimensioned drawing of the intended contour", "nominal finished sizes")
        self.assertNotIn("nominal drawing above", text)
        self.assertNotIn("vertex coordinates above", text)
        self.assertIn("specifying the nominal finished sizes and vertex coordinates", text)

    def test_orca_audit_keeps_the_broad_release_matrix_as_an_optional_unbundled_contract(self):
        text = section(PRINT / "orca-audit-tooling.md", "6.")
        self.has(text, "release matrix", "optional", "nothing here is bundled", "markerless", "m82/m83", "exact and malformed arcs", "redaction before disk",
                 "partial report", "clean-home", "lint", "representative multi-tool 3mf", "actual slice", "png signatures", "no g-code in the zip",
                 "independent bounded review", "source 3mf hash unchanged")

    def test_support_plan_audit_keeps_interface_parity_live_angles_and_the_downstream_consumer_gate(self):
        self.has(section(PRINT / "orca-support-interfaces-and-first-layer.md", "7."), "even and odd interface-id parities", "same slice", "supportparameters",
                 "live angles", "perpendicular to the hatch axis", "downstream", "hole and roof consumers", "regression-tested", "proven legal expansion path")

    def test_critical_fit_prints_a_small_coupon_or_ring_before_the_full_size_part_and_routes_to_the_fit_owner(self):
        text = section(CAD / "physical-reverse-engineering.md", "1.")
        self.has(text, "critical fit", "small fit coupon or ring", "before the full-size part", "fit-clearance-and-retention.md", "design-and-fit-gates.md")
        self.has(section(CAD / "physical-reverse-engineering.md", "3."), "0.492")

    def test_logo_artwork_imports_into_the_intended_cad_and_checks_closed_profiles_and_holes_before_3d_conversion(self):
        self.has(section(CAD / "logo-artwork-to-geometry.md", "6."), "import the svg into the intended cad", "closed profiles", "holes", "before the 3d conversion",
                 "no new software dependency")

    def test_audit_names_the_three_metadata_entries_and_warns_that_markerless_layer_components_may_be_merged(self):
        audit = PRINT / "orca-audit-tooling.md"
        self.has(section(audit, "2."), "metadata/project_settings.config", "metadata/model_settings.config", "metadata/slice_info.config", "plate metadata",
                 "previews", "bound metadata entry sizes", "namespaced", "inherit")
        self.has(section(audit, "3."), "markerless analysis synthetic", "per-layer components may be merged")
        self.assertEqual(section(audit, "3.").count("discard synthetic per-layer buffers when the first marker arrives"), 1, "the pre-marker sentence is not duplicated")

    def test_support_merge_or_expand_waits_for_a_per_island_decision_contract_and_an_attribution_boundary(self):
        text = section(PRINT / "orca-support-interfaces-and-first-layer.md", "7.")
        self.has(text, "per-island decision contract", "attribution boundary", "not island identity", "first vertical slice", "settings and plumbing",
                 "merge case is reproduced", "normal and organic", "own discovery", "tree hybrid")
        self.assertNotRegex(text, r"\be2\b", "a private phase label must not be copied")
        self.has(text, "proven legal expansion path", "finite synthetic sweep", "disabled compatibility")  # the existing gates stay

    def test_logo_flattening_applies_the_effective_fill_rule_to_the_output_path_and_fails_closed(self):
        text = section(CAD / "logo-artwork-to-geometry.md", "5.")
        self.has(text, "apply the effective", "output compound path", "explicit attribute or style", "evenodd", "fail closed", "qualification render",
                 "counters", "https://www.w3.org/TR/SVG2/painting.html#FillRuleProperty", "inherited")
        self.has(text, "do not concatenate", "overlap or cancellation", "render")  # the existing conditions stay

    def test_audit_proves_tool_and_material_mapping_from_emitted_paths_without_claiming_the_physical_spool(self):
        text = section(PRINT / "orca-audit-tooling.md", "3.")
        self.has(text, "tool and material mapping", "not from config alone", "resolved artifact", "material slots", "per-tool inheritance",
                 "declared material identity", "not proof of the physical filament", "segments, tool, material")
        self.assertEqual(text.count("discard synthetic per-layer buffers when the first marker arrives"), 1, "the pre-marker sentence is not duplicated")

    def test_experimental_interface_checks_use_random_order_multiple_seeds_and_local_preview_before_physical_requests(self):
        text = section(PRINT / "orca-support-interfaces-and-first-layer.md", "7.")
        self.has(text, "focused fff tests", "random order", "multiple seeds", "local sliced-preview proof", "before requesting physical a/b prints")
        self.assertRegex(text, r"before requesting physical a/b prints,\s*run focused fff tests in random order with multiple seeds and obtain local sliced-preview proof")

    def test_experimental_interface_falsification_sweep_keeps_inputs_families_measurements_and_witness_meaning(self):
        text = section(PRINT / "orca-support-interfaces-and-first-layer.md", "7.")
        self.has(text, "slices its own fixture", "top and bottom records separate", "no shared state", "thin scanline strips", "narrow-neck dumbbells", "holes/annuli", "high-aspect slabs", "phase-sensitive/comb", "full perimeter including holes", "angle/parity", "phase", "emitted polyline length", "candidate ratio", "observed falsification", "overestimate witness", "not a proof")

    def test_control_source_resolved_contexts_remain_without_new_edits(self):
        """Presence-only control: these source-resolved contexts are still mentioned. It is not a byte-immutability or golden-hash proof."""
        self.has(section(CAD / "paint-label-repair.md", "0."), "parent and output hashes")
        self.assertIn("ai-assist", (CAD / "parametric-prototyping-and-release.md").read_text(encoding="utf8").lower())
        self.has(section(PRINT / "orca-audit-tooling.md", "3."), "discard synthetic per-layer buffers when the first marker arrives")


if __name__ == "__main__":
    unittest.main()
