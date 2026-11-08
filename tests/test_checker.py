"""Standard-library synthetic tests; shared fixtures are not production validators."""
from test_skill_packages import (
    GOOD_SKILL,
    Path,
    ROOT,
    TmpCase,
    check_skills,
    codes,
    hashlib,
    io,
    json,
    make_repo,
    make_symlink,
    mock,
    os,
    re,
    run_script,
    sha,
    shutil,
    tempfile,
    unittest,
)


class FrontmatterParserTest(unittest.TestCase):
    def test_valid_forms(self):
        fm, err = check_skills.parse_frontmatter(GOOD_SKILL)
        self.assertIsNone(err)
        self.assertEqual(fm["name"], "demo-skill")
        self.assertEqual(fm["metadata"], {"scope": "demo"})
        fm, err = check_skills.parse_frontmatter("---\nname: a\ndescription: Plain text; with semicolons.\n---\nbody")
        self.assertIsNone(err)
        self.assertEqual(fm["description"], "Plain text; with semicolons.")

    def test_rejected_forms(self):
        bad = {
            "no frontmatter": "# just a heading\n",
            "unclosed": "---\nname: a\n",
            "list value": "---\nname: a\ndescription: x\nmetadata:\n  tags: [a, b]\n---\n",
            "block scalar": "---\nname: a\ndescription: >\n  folded\n---\n",
            "duplicate": "---\nname: a\nname: b\n---\n",
            "unterminated quote": '---\nname: a\ndescription: "oops\n---\n',
        }
        for label, text in bad.items():
            with self.subTest(label):
                _, err = check_skills.parse_frontmatter(text)
                self.assertIsNotNone(err)



class NestedMetadataDuplicateKeyTest(TmpCase):
    HEAD = "---\nname: a\ndescription: x\nmetadata:\n"

    def test_duplicate_nested_metadata_keys_are_refused_not_overwritten(self):
        _, err = check_skills.parse_frontmatter(self.HEAD + "  scope: one\n  scope: two\n---\n")
        self.assertIsNotNone(err)
        self.assertIn("duplicate", err)
        self.assertIn("scope", err)

    def test_a_nested_key_that_only_shares_a_top_level_name_is_not_a_duplicate(self):
        fm, err = check_skills.parse_frontmatter(self.HEAD + "  name: other\n---\n")
        self.assertIsNone(err)
        self.assertEqual(fm["metadata"], {"name": "other"})

    def test_parser_stays_bounded_on_many_keys_and_still_finds_a_late_duplicate(self):
        many = "".join(f"  k{i}: v\n" for i in range(5000))
        fm, err = check_skills.parse_frontmatter(self.HEAD + many + "---\n")
        self.assertIsNone(err)
        self.assertEqual(len(fm["metadata"]), 5000)
        _, err = check_skills.parse_frontmatter(self.HEAD + many + "  k4999: again\n---\n")
        self.assertIn("duplicate", err)

    def test_checker_reports_the_duplicate_as_a_frontmatter_finding(self):
        make_repo(self.tmp, skill=GOOD_SKILL.replace('  scope: "demo"\n', '  scope: "demo"\n  scope: "again"\n'))
        self.assertIn("FRONTMATTER", codes(check_skills.check(self.tmp)))



class FrontmatterSubsetTest(unittest.TestCase):
    """The documented subset: flat top-level keys, one level of string metadata, plain or quoted strings.

    Anything outside it is refused with a named reason instead of being read in a way that could differ
    from what a real YAML consumer sees. This is not a YAML implementation and not a native-client check.
    """

    HEAD = "---\nname: demo\ndescription: \"demo\"\nmetadata:\n"

    def meta(self, body):
        return check_skills.parse_frontmatter(self.HEAD + body + "---\n")

    def top(self, line):
        return check_skills.parse_frontmatter(f"---\nname: demo\n{line}\n---\n")

    # -- indentation ----------------------------------------------------------
    def test_control_empty_nested_mapping_value_was_already_refused(self):
        # SAFE CONTROL, not product RED: the reviewer's example was refused before this correction too.
        _, err = self.meta("  scope:\n    nested: value\n")
        self.assertIsNotNone(err)

    def test_a_deeper_line_after_a_scalar_is_refused_not_flattened_into_metadata(self):
        # product RED: this used to be accepted as {'scope': 'demo', 'nested': 'value'}
        fm, err = self.meta("  scope: demo\n    nested: value\n")
        self.assertIsNotNone(err, fm)
        self.assertIn("nested mappings", err)

    def test_inconsistent_indentation_is_refused_with_a_named_error(self):
        for label, body in {"shallower": "  a: x\n b: y\n", "wider": "  a: x\n   b: y\n", "back out": "    a: x\n  b: y\n"}.items():
            with self.subTest(label):
                fm, err = self.meta(body)
                self.assertIsNotNone(err, fm)
                self.assertIn("indentation", err)

    def test_tab_indentation_is_refused(self):
        fm, err = self.meta("\tscope: x\n")
        self.assertIsNotNone(err, fm)
        self.assertIn("tab", err)

    def test_one_consistent_indentation_level_of_any_width_is_accepted(self):
        for width in (1, 2, 4):
            with self.subTest(width=width):
                pad = " " * width
                fm, err = self.meta(f"{pad}scope: demo\n{pad}other: \"x\"\n")
                self.assertIsNone(err)
                self.assertEqual(fm["metadata"], {"scope": "demo", "other": "x"})

    # -- bare scalars that a real YAML consumer reads as another type ----------
    def test_bare_values_that_yaml_reads_as_bool_null_number_or_date_are_refused(self):
        for bare in ("true", "False", "yes", "No", "ON", "off", "null", "Null", "~", "123", "-4", "1.5", "1e3", "0x1F", "0755", ".inf", ".NaN", "2024-01-31", "1_000", "12:30"):
            for where in ("top", "metadata"):
                with self.subTest(bare=bare, where=where):
                    fm, err = self.top(f"license: {bare}") if where == "top" else self.meta(f"  scope: {bare}\n")
                    self.assertIsNotNone(err, fm)
                    self.assertIn("quote", err)

    def test_quoted_forms_of_the_same_words_and_ordinary_plain_strings_are_accepted(self):
        for text, expected in {'"true"': "true", '"123"': "123", "'null'": "null", "MIT": "MIT", "Apache-2.0": "Apache-2.0", "3d-printing-workflows": "3d-printing-workflows", "1.2.3": "1.2.3", "yes-please": "yes-please", "nullable": "nullable", "v1": "v1"}.items():
            with self.subTest(text):
                fm, err = self.top(f"license: {text}")
                self.assertIsNone(err)
                self.assertEqual(fm["license"], expected)

    def test_through_the_checker_a_bare_boolean_name_and_an_escape_only_description_are_findings(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d, skill=GOOD_SKILL.replace("name: demo-skill", "name: true"))
            self.assertIn("FRONTMATTER", codes(check_skills.check(d)))
        for desc in ('"\\n"', '"\\t"', '"\\x20"', '"\\u0020"', '"\\ "'):
            with self.subTest(desc), tempfile.TemporaryDirectory() as d:
                make_repo(d, skill=GOOD_SKILL.replace('description: "Use when demoing: a sample, with punctuation."', f"description: {desc}"))
                self.assertIn("FRONTMATTER", codes(check_skills.check(d)))

    # -- quoted scalars --------------------------------------------------------
    def test_double_quoted_escapes_other_than_quote_and_backslash_are_refused(self):
        for text in ('"\\n"', '"\\t"', '"\\x20"', '"\\u0020"', '"a\\nb"', '"\\ "', '"\\0"'):
            with self.subTest(text):
                fm, err = self.top(f"description: {text}")
                self.assertIsNotNone(err, fm)
                self.assertIn("escape", err)

    def test_double_quoted_quote_and_backslash_escapes_decode_as_yaml_does(self):
        fm, err = self.top('description: "say \\"hi\\" \\\\ done"')
        self.assertIsNone(err)
        self.assertEqual(fm["description"], 'say "hi" \\ done')

    def test_single_quoted_doubled_quote_decodes_and_backslashes_stay_literal(self):
        fm, err = self.top("description: 'it''s \\n fine'")
        self.assertIsNone(err)
        self.assertEqual(fm["description"], "it's \\n fine")

    def test_an_escaped_closing_quote_does_not_close_the_scalar(self):
        _, err = self.top('description: "abc\\"')
        self.assertIsNotNone(err)
        self.assertIn("unterminated", err)

    def test_text_or_comment_after_a_closing_quote_is_refused(self):
        for text in ('"x" y', '"x" # note', "'x' # note", '"x""y"'):
            with self.subTest(text):
                fm, err = self.top(f"description: {text}")
                self.assertIsNotNone(err, fm)

    # -- plain scalars whose real YAML meaning differs ----------------------------
    def test_plain_values_with_comment_mapping_or_indicator_ambiguity_are_refused(self):
        for text in ("foo # bar", "# nothing", "a: b", "*alias", "&anchor x", "!tag x", "%directive", "@reserved", "`reserved", "- item", "? key", ", x", "x:"):
            with self.subTest(text):
                fm, err = self.top(f"description: {text}")
                self.assertIsNotNone(err, fm)
                self.assertIn("quote", err)

    def test_plain_values_that_only_look_special_are_accepted_unchanged(self):
        for text in ("C# is fine", "a:b", "-x", "it's fine", "50% sure", "a, b; c", "Use when designing scope. Coach tradeoffs; prevent drift."):
            with self.subTest(text):
                fm, err = self.top(f"description: {text}")
                self.assertIsNone(err)
                self.assertEqual(fm["description"], text)



class FrontmatterGrammarCorrectionTest(unittest.TestCase):
    """Corrections to the explicit small grammar: YAML separation whitespace includes tabs, y/n and signed
    based numbers read as other types, and indentation or values are never reinterpreted (only ASCII
    space/tab count as whitespace). Custom-parser tests only: no native-client compatibility is claimed."""

    def top(self, line):
        return check_skills.parse_frontmatter(f"---\nname: demo\n{line}\n---\n")

    def meta(self, body):
        return check_skills.parse_frontmatter("---\nname: demo\ndescription: \"demo\"\nmetadata:\n" + body + "---\n")

    def test_tab_separated_comment_mapping_and_indicator_forms_are_refused_like_the_space_forms(self):
        for text in ("value\t# comment", "value \t# comment", "a:\tb", "-\titem", "?\tkey", ":\tx", "a\t#b"):
            with self.subTest(repr(text)):
                fm, err = self.top(f"description: {text}")
                self.assertIsNotNone(err, fm)
                self.assertIn("quote", err)

    def test_a_tab_inside_a_plain_value_and_a_hash_without_separation_stay_literal(self):
        for text in ("a\tb", "a#b", "C#\tmajor"):
            with self.subTest(repr(text)):
                fm, err = self.top(f"description: {text}")
                self.assertIsNone(err)
                self.assertEqual(fm["description"], text)

    def test_y_and_n_in_either_case_are_refused_as_possible_yaml_booleans(self):
        for bare in ("y", "n", "Y", "N"):
            for where in ("top", "metadata"):
                with self.subTest(bare=bare, where=where):
                    fm, err = self.top(f"license: {bare}") if where == "top" else self.meta(f"  scope: {bare}\n")
                    self.assertIsNotNone(err, fm)
                    self.assertIn("quote", err)

    def test_quoted_or_longer_words_starting_with_y_or_n_stay_strings(self):
        for text, expected in {'"y"': "y", "'n'": "n", "yes-please": "yes-please", "no-op": "no-op", "nope": "nope", "yn": "yn"}.items():
            with self.subTest(text):
                fm, err = self.top(f"license: {text}")
                self.assertIsNone(err)
                self.assertEqual(fm["license"], expected)

    def test_signed_based_integers_are_refused(self):
        for bare in ("-0x10", "+0x10", "-0b10", "+0b1", "-0o7", "+0o7"):
            with self.subTest(bare):
                fm, err = self.top(f"license: {bare}")
                self.assertIsNotNone(err, fm)
                self.assertIn("quote", err)

    def test_non_ascii_indentation_is_refused_not_reinterpreted(self):
        for lead in ("\u00a0\u00a0", "\u3000", " \u00a0", "\u2003"):
            with self.subTest(repr(lead)):
                fm, err = self.meta(f"{lead}scope: x\n")
                self.assertIsNotNone(err, fm)
                self.assertIn("ASCII", err)

    def test_non_ascii_whitespace_inside_values_is_preserved_literally(self):
        fm, err = self.top("description: x\u00a0")
        self.assertIsNone(err)
        self.assertEqual(fm["description"], "x\u00a0")
        fm, err = self.top("description:\u00a0x")
        self.assertIsNone(err)
        self.assertEqual(fm["description"], "\u00a0x")
        _, err = self.top('description: "x"\u00a0')
        self.assertIsNotNone(err, "a no-break space after a closing quote is text, not whitespace")

    def test_control_crlf_line_endings_still_parse(self):
        fm, err = check_skills.parse_frontmatter("---\r\nname: demo\r\ndescription: \"d\"\r\nmetadata:\r\n  scope: x\r\n---\r\n")
        self.assertIsNone(err)
        self.assertEqual((fm["name"], fm["description"], fm["metadata"]), ("demo", "d", {"scope": "x"}))



class CheckerSymlinkGateTest(TmpCase):
    """Symlinks (file or directory, live or broken, inside or outside the root) are reported before any
    linked content is read. The 'external' targets are synthetic and live inside the task-owned temp root."""

    def setUp(self):
        super().setUp()
        self.root = self.tmp / "repo"
        self.root.mkdir()
        make_repo(self.root)
        self.external = self.tmp / "external"
        self.external.mkdir()
        (self.external / "secret.txt").write_text("synthetic outside payload\n")
        (self.external / "sub").mkdir()
        (self.external / "sub" / "inner.md").write_text("synthetic inner payload\n")
        self.reads = []

    def tracked_check(self, *args, **kwargs):
        """Run check() while recording every file opened under the external directory."""
        real_open, ext = io.open, os.path.realpath(self.external)

        def tracking(file, *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)) and os.path.realpath(file).startswith(ext):
                self.reads.append(os.fspath(file))
            return real_open(file, *a, **k)

        with mock.patch("io.open", tracking):
            return check_skills.check(self.root, *args, **kwargs)

    def test_instrument_control_a_read_of_the_external_target_is_observed(self):
        real_open, ext = io.open, os.path.realpath(self.external)
        seen = []

        def tracking(file, *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)) and os.path.realpath(file).startswith(ext):
                seen.append(file)
            return real_open(file, *a, **k)

        with mock.patch("io.open", tracking):
            (self.external / "secret.txt").read_bytes()
        self.assertEqual(len(seen), 1)

    def test_a_regular_tree_has_no_findings_and_never_touches_the_external_directory(self):
        self.assertEqual(self.tracked_check(), [])
        self.assertEqual(self.reads, [])

    def test_file_dir_dangling_and_inside_links_are_reported_and_nothing_external_is_read(self):
        make_symlink(self.root / "external.txt", self.external / "secret.txt")
        make_symlink(self.root / "linked-dir", self.external, directory=True)
        make_symlink(self.root / "dangling.txt", self.external / "does-not-exist")
        make_symlink(self.root / "inside.md", self.root / "README.md")
        make_symlink(self.root / "demo-skill" / "references" / "pointer.md", self.external / "sub" / "inner.md")
        found = self.tracked_check()
        got = {(p, c) for p, c, _ in found}
        for rel in ("external.txt", "linked-dir", "dangling.txt", "inside.md", "demo-skill/references/pointer.md"):
            self.assertIn((rel, "UNSUPPORTED_SYMLINK"), got, rel)
        self.assertEqual(self.reads, [], "no linked content may be read")
        self.assertFalse(any(str(self.external) in (p + m) for p, _, m in found), "link targets are not echoed")

    def test_a_root_document_or_skill_folder_that_is_a_link_is_reported_not_read(self):
        (self.external / "SKILL.md").write_text('---\nname: demo-skill\ndescription: "outside"\n---\n')
        (self.root / "README.md").unlink()
        make_symlink(self.root / "README.md", self.external / "secret.txt")
        found = self.tracked_check()
        self.assertIn(("README.md", "UNSUPPORTED_SYMLINK"), {(p, c) for p, c, _ in found})
        self.assertEqual(self.reads, [])
        # a skill folder that is a link: skill discovery must not look through it
        (self.root / "README.md").unlink()
        (self.root / "README.md").write_text("demo-skill\n")
        shutil.rmtree(self.root / "demo-skill")
        make_symlink(self.root / "demo-skill", self.external, directory=True)
        found = self.tracked_check()
        self.assertIn(("demo-skill", "UNSUPPORTED_SYMLINK"), {(p, c) for p, c, _ in found})
        self.assertEqual(self.reads, [])

    def test_the_cli_reports_the_symlink_with_exit_1_and_without_the_target_path(self):
        make_symlink(self.root / "external.txt", self.external / "secret.txt")
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [self.root])
        self.assertEqual(code, 1)
        self.assertIn("UNSUPPORTED_SYMLINK", out)
        self.assertNotIn("external", (out + err).replace("external.txt", ""))
        self.assertNotIn("synthetic outside payload", out + err)



class CheckerRootSymlinkTest(TmpCase):
    """A symlink supplied as the root LEAF is rejected before resolve() or any target content is read.
    The alias target is a synthetic task-owned directory. Aliased ancestors of the root are not rejected."""

    def reads_under(self, directory, function):
        """Run function() while recording every open() of a file under directory; returns (result, reads)."""
        real_open, base, reads = io.open, os.path.realpath(directory), []

        def tracking(file, *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)) and os.path.realpath(file).startswith(base):
                reads.append(os.fspath(file))
            return real_open(file, *a, **k)

        with mock.patch("io.open", tracking):
            return function(), reads

    def setUp(self):
        super().setUp()
        self.actual = self.tmp / "actual"
        self.actual.mkdir()
        make_repo(self.actual)

    def test_control_a_direct_regular_root_is_clean_and_the_observer_sees_its_reads(self):
        found, reads = self.reads_under(self.actual, lambda: check_skills.check(self.actual))
        self.assertEqual(found, [])
        self.assertTrue(reads, "the observer must see ordinary reads, otherwise 'no reads' below proves nothing")

    def test_a_live_root_alias_is_reported_and_its_target_is_never_read(self):
        alias = self.tmp / "alias"
        make_symlink(alias, self.actual, directory=True)
        for label, supplied in {"plain": alias, "trailing slash": str(alias) + "/"}.items():
            with self.subTest(label):
                found, reads = self.reads_under(self.actual, lambda: check_skills.check(supplied))
                self.assertEqual([c for _, c, _ in found], ["UNSUPPORTED_SYMLINK"], found)
                self.assertEqual(reads, [], "no content behind the alias may be read")
                self.assertFalse(any(str(self.actual) in (p + m) for p, _, m in found), "the target path is not echoed")

    def test_a_broken_root_alias_is_reported_not_silently_scanned_as_empty(self):
        broken = self.tmp / "broken"
        make_symlink(broken, self.tmp / "does-not-exist", directory=True)
        found = check_skills.check(broken)
        self.assertIn("UNSUPPORTED_SYMLINK", {c for _, c, _ in found})
        self.assertNotIn("NO_SKILLS", {c for _, c, _ in found}, "a broken alias must not be treated as an empty tree")

    def test_the_cli_rejects_a_root_alias_with_exit_1_without_the_target(self):
        alias = self.tmp / "alias"
        make_symlink(alias, self.actual, directory=True)
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [alias])
        self.assertEqual(code, 1)
        self.assertIn("UNSUPPORTED_SYMLINK", out)
        self.assertNotIn("actual", out + err)

    def test_control_an_aliased_ancestor_of_the_root_is_not_rejected(self):
        parent_real = self.tmp / "parent-real"
        parent_real.mkdir()
        (parent_real / "repo").mkdir()
        make_repo(parent_real / "repo")
        parent_alias = self.tmp / "parent-alias"
        make_symlink(parent_alias, parent_real, directory=True)
        self.assertEqual(check_skills.check(parent_alias / "repo"), [])



class FrontmatterEmptyValueTest(unittest.TestCase):
    """Unsupported empty values fail instead of becoming {}: YAML reads an empty value as null. Mapping form is
    for `metadata` only, with real one-level string children. Custom-parser tests only."""

    HEAD = '---\nname: demo\ndescription: "d"\n'

    def parse(self, tail):
        return check_skills.parse_frontmatter(self.HEAD + tail + "---\n")

    def test_metadata_without_child_fields_is_refused_not_turned_into_an_empty_mapping(self):
        for label, tail in {"at the end": "metadata:\n", "before another key": "metadata:\nlicense: MIT\n"}.items():
            with self.subTest(label):
                fm, err = self.parse(tail)
                self.assertIsNotNone(err, fm)
                self.assertIn("metadata", err)
                self.assertIn("no child", err)

    def test_empty_allowed_tools_and_other_empty_top_level_values_are_refused(self):
        for key in ("allowed-tools", "license", "compatibility", "name", "description"):
            with self.subTest(key):
                fm, err = check_skills.parse_frontmatter(f"---\nname: demo\n{key}:\n---\n" if key != "name" else "---\nname:\n---\n")
                self.assertIsNotNone(err, fm)
                self.assertIn("empty value", err)

    def test_a_mapping_under_a_key_other_than_metadata_is_not_accepted(self):
        fm, err = self.parse("allowed-tools:\n  Read: x\n")
        self.assertIsNotNone(err, fm)

    def test_through_the_checker_empty_metadata_and_empty_allowed_tools_are_frontmatter_findings(self):
        skills = {
            "empty metadata": GOOD_SKILL.replace('metadata:\n  scope: "demo"\n', "metadata:\n"),
            "empty allowed-tools": GOOD_SKILL.replace("license: MIT\n", "license: MIT\nallowed-tools:\n"),
        }
        for label, skill in skills.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                make_repo(d, skill=skill)
                self.assertIn("FRONTMATTER", codes(check_skills.check(d)))

    def test_allowed_tools_when_supplied_must_be_a_string(self):
        with tempfile.TemporaryDirectory() as d:
            make_repo(d)
            with mock.patch.object(check_skills, "parse_frontmatter", return_value=({"name": "demo-skill", "description": "d", "allowed-tools": {}}, None)):
                found = check_skills.check(d)
        self.assertTrue(any(c == "FRONTMATTER" and "allowed-tools" in m for _, c, m in found), found)

    def test_nonempty_absent_and_genuinely_quoted_empty_values_are_unchanged(self):
        fm, err = self.parse('metadata:\n  scope: "demo"\n  note: ""\nallowed-tools: Read Write\nlicense: ""\n')
        self.assertIsNone(err)
        self.assertEqual(fm["metadata"], {"scope": "demo", "note": ""})
        self.assertEqual((fm["allowed-tools"], fm["license"]), ("Read Write", ""))
        fm, err = self.parse("")
        self.assertIsNone(err)
        self.assertEqual(set(fm), {"name", "description"})



class CheckerSyntheticTest(TmpCase):
    # Private IPv6 samples are assembled at run time so this scanned source stays clean.
    PRIVATE_V6 = {
        "unique-local fd": "fd" + "12:3456:789a::1",
        "unique-local fc": "fc" + "00::1",
        "unique-local upper-case": "FD" + "00::BEEF",
        "unique-local full form": "fd00" + ":0:0:0:0:0:0:1",
        "link-local": "fe80" + "::1",
        "link-local upper end": "febf" + "::2",
        "link-local with zone id": "fe80" + "::1%eth0",
        "inside a URL": "http://[fd00" + "::1]:8080/x",
        "followed by a colon": "see fd00" + "::1: next",
    }
    NOT_PRIVATE_V6 = [
        "2001:db8::1",  # documentation range
        "::1",  # loopback
        "::",  # unspecified
        "2606:4700:4700::1111",  # ordinary public address
        "::ffff:8.8.8.8",  # mapped public IPv4
        "fe00::1",  # just outside link-local
        "fb00::1",  # just outside unique-local
        "fd::",  # first group 00fd, not unique-local
        "12:30:45",  # a time
        "a:b:c",  # arbitrary colons
        "00:11:22:33:44:55",  # a MAC address
        "std::string and ab::cd",  # code
    ]

    def test_private_ipv6_is_flagged_without_echoing_the_address(self):
        self.assertIn("IPv6", check_skills.__doc__)
        for label, addr in self.PRIVATE_V6.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\nhost {addr}\n")
                    found = check_skills.check(d)
                    hit = [f for f in found if f[1] == "PRIVATE_IP"]
                    self.assertTrue(hit, found)
                    self.assertTrue(all("line 3" in m for _, _, m in hit), hit)
                    bare = re.search(r"[0-9A-Fa-f]{2,4}:[0-9A-Fa-f:]*", addr).group(0).rstrip(":")
                    self.assertGreaterEqual(len(bare), 6)
                    self.assertFalse(any(bare in m or bare in p for p, _, m in found), found)

    def test_public_loopback_documentation_and_arbitrary_colons_are_not_flagged(self):
        for text in self.NOT_PRIVATE_V6:
            with self.subTest(text):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
                    self.assertEqual(check_skills.check(d), [])

    def test_cli_does_not_echo_a_private_ipv6_address(self):
        addr = "fd00" + "::1234"
        make_repo(self.tmp, guide=f"# Guide\n\nhost {addr}\n")
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [self.tmp])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_IP", out)
        self.assertNotIn("1234", out + err)

    def test_valid_repo_has_no_findings(self):
        make_repo(self.tmp)
        self.assertEqual(check_skills.check(self.tmp), [])

    def test_frontmatter_and_name_mutations(self):
        cases = {
            "NAME": GOOD_SKILL.replace("name: demo-skill", "name: Demo_Skill"),
            "FRONTMATTER": GOOD_SKILL.replace("license: MIT", "version: 1.0.0"),
            "DESCRIPTION": GOOD_SKILL.replace('description: "Use when demoing: a sample, with punctuation."', 'description: ""'),
        }
        for code, skill in cases.items():
            with self.subTest(code):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, skill=skill)
                    self.assertIn(code, codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, skill=GOOD_SKILL.replace("name: demo-skill", "name: other-name"))
            self.assertIn("NAME", codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, skill=GOOD_SKILL.replace("scope", "tags").replace('"demo"', "[a]"))
            self.assertIn("FRONTMATTER", codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, skill="# no frontmatter\n")
            self.assertIn("FRONTMATTER", codes(check_skills.check(d)))

    def test_reference_mutations(self):
        cases = {
            "MISSING_REF": (dict(skill=GOOD_SKILL + "\nAlso `references/missing.md`.\n"), None),
            "ESCAPES_PACKAGE": (dict(skill=GOOD_SKILL + "\n[up](../README.md)\n"), None),
            "SKILL_NOT_LISTED": (dict(readme="nothing here\n"), None),
        }
        for code, (kw, _) in cases.items():
            with self.subTest(code):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, **kw)
                    self.assertIn(code, codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, readme="demo-skill [broken](nope.md)\n")
            self.assertIn("BROKEN_LINK", codes(check_skills.check(d)))

    def test_orphan_artifact_syntax_and_cross_package(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d)
            (Path(d) / "demo-skill" / "references" / "unlinked.md").write_text("# nobody links here\n")
            self.assertIn("ORPHAN", codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d)
            cache = Path(d) / "demo-skill" / "references" / "__pycache__"
            cache.mkdir()
            (cache / "x.pyc").write_bytes(b"\0")
            self.assertIn("ARTIFACT", codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, skill=GOOD_SKILL + "\nRun `scripts/bad.py`.\n")
            (Path(d) / "demo-skill" / "scripts").mkdir()
            (Path(d) / "demo-skill" / "scripts" / "bad.py").write_text("def (:\n")
            self.assertIn("SYNTAX", codes(check_skills.check(d)))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, readme="demo-skill other-skill\n", guide="# Guide\n\nSee `other-skill/references/a.md`.\n")
            other = Path(d) / "other-skill"
            (other / "references").mkdir(parents=True)
            (other / "SKILL.md").write_text('---\nname: other-skill\ndescription: "Another."\n---\n\nSee `references/a.md`.\n')
            (other / "references" / "a.md").write_text("# a\n")
            (Path(d) / "INSTALLATION.md").write_text("demo-skill other-skill\n")
            self.assertIn("CROSS_PACKAGE_PATH", codes(check_skills.check(d)))

    def test_privacy_mutations(self):
        samples = {
            "PRIVATE_PATH": "see /home/" + "alice/notes",
            "PRIVATE_IP": "host 192.168." + "1.20",
            "PRODUCT_ID": "listing B0" + "ABCDEFGH",
            "SECRET": "token ghp_" + "a" * 30,
            "EMAIL": "mail someone" + "@example.org",
        }
        fragments = {"PRIVATE_PATH": "alice", "PRIVATE_IP": "192.168", "PRODUCT_ID": "ABCDEFGH", "SECRET": "ghp_", "EMAIL": "example.org"}
        for code, text in samples.items():
            with self.subTest(code):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\n{text}\n")
                    found = check_skills.check(d)
                    self.assertIn(code, codes(found))
                    hit = [f for f in found if f[1] == code]
                    # location only (path, code, line): the matched value is never echoed
                    self.assertTrue(all("line 3" in m for _, _, m in hit), hit)
                    self.assertFalse(any(fragments[code] in m or fragments[code] in p for p, _, m in hit), hit)

    def test_denied_terms_and_cli_output_never_echo_matched_values(self):
        secret = "ghp_" + "b" * 30
        make_repo(self.tmp, guide=f"# Guide\n\nkey {secret} and ZZ-SYNTHETIC-DENIED\n")
        found = check_skills.check(self.tmp, deny_terms=["ZZ-SYNTHETIC-DENIED"])
        self.assertTrue({"SECRET", "DENIED_TERM"} <= codes(found))
        self.assertFalse(any(secret in m or "ZZ-SYNTHETIC-DENIED" in m for _, _, m in found), found)
        deny = self.tmp.parent / (self.tmp.name + "-deny2.txt")
        deny.write_text("ZZ-SYNTHETIC-DENIED\n")
        self.addCleanup(lambda: deny.unlink(missing_ok=True))
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [self.tmp, "--deny-file", deny])
        self.assertEqual(code, 1)
        self.assertNotIn(secret, out + err)
        self.assertNotIn("ZZ-SYNTHETIC-DENIED", out + err)
        self.assertIn("SECRET", out)
        self.assertIn("DENIED_TERM", out)

    def test_every_utf8_text_file_is_scanned_whatever_its_suffix(self):
        for name in ("tool.toml", "run.sh", "data.xml", "Makefile", "notes.cfg", "setup.ps1", "page.htm", "x.env"):
            with self.subTest(name):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d)
                    (Path(d) / "extra").mkdir()
                    (Path(d) / "extra" / name).write_text("path /home/" + "alice/x\n")
                    self.assertIn((f"extra/{name}", "PRIVATE_PATH"), {(p, c) for p, c, _ in check_skills.check(d)})

    def test_files_that_cannot_be_scanned_as_text_are_reported_not_skipped(self):
        make_repo(self.tmp)
        extra = self.tmp / "extra"
        extra.mkdir()
        (extra / "blob.bin").write_bytes(b"\x00\x01\x02 /home/" + b"alice/x")
        (extra / "latin1.txt").write_bytes(b"caf\xe9 /home/" + b"alice/x")
        (extra / "ok.txt").write_text("café – plain UTF-8 text\n", encoding="utf8")
        (extra / "empty.txt").write_bytes(b"")
        got = {(p, c) for p, c, _ in check_skills.check(self.tmp)}
        self.assertIn(("extra/blob.bin", "UNSCANNED_BINARY"), got)
        self.assertIn(("extra/latin1.txt", "UNSCANNED_BINARY"), got)
        self.assertFalse({p for p, _ in got} & {"extra/ok.txt", "extra/empty.txt"}, "valid UTF-8 and empty files are clean")

    def test_former_vendor_paths_get_no_privacy_exemption(self):
        make_repo(self.tmp)
        d = self.tmp / "skill-creator"
        (d / "scripts").mkdir(parents=True)
        bodies = {"LICENSE.txt": "license /home/" + "alice/x\n", "scripts/run_eval.py": "# /home/" + "alice/x\n"}
        for rel, body in bodies.items():
            (d / rel).write_text(body)
        manifest = self.tmp / "vendor.json"
        manifest.write_text(json.dumps({"files": {rel: {"sha256": hashlib.sha256(b.encode()).hexdigest()} for rel, b in bodies.items()}}))
        for use_manifest in (None, manifest):  # binding bytes by hash is not a privacy exemption
            got = {(p, c) for p, c, _ in check_skills.check(self.tmp, use_manifest)}
            self.assertIn(("skill-creator/LICENSE.txt", "PRIVATE_PATH"), got)
            self.assertIn(("skill-creator/scripts/run_eval.py", "PRIVATE_PATH"), got)

    def test_vendor_manifest_checks_each_declared_shipping_entry(self):
        make_repo(self.tmp)
        d = self.tmp / "skill-creator"
        d.mkdir()
        (d / "LICENSE.txt").write_bytes(b"license text")
        h = hashlib.sha256(b"license text").hexdigest()
        manifest = self.tmp / "vendor.json"
        manifest.write_text(json.dumps({"files": {"LICENSE.txt": {"sha256": h}}}))
        self.assertEqual([f for f in check_skills.check(self.tmp, manifest) if f[1].startswith("VENDOR")], [])
        # a manifest declaring more than ships (e.g. the historical 18-file list) is reported, not tolerated
        manifest.write_text(json.dumps({"files": {"LICENSE.txt": {"sha256": h}, "scripts/run_eval.py": {"sha256": h}}}))
        got = {(p, c) for p, c, _ in check_skills.check(self.tmp, manifest)}
        self.assertIn(("skill-creator/scripts/run_eval.py", "VENDOR_MISSING"), got)

    def test_invalid_vendor_manifests_are_findings_not_crashes(self):
        make_repo(self.tmp)
        manifest = self.tmp.parent / (self.tmp.name + "-vendor.json")
        self.addCleanup(lambda: manifest.unlink(missing_ok=True))
        bad_bodies = [
            "not json",
            "{}",
            '{"files": []}',
            '{"files": {}}',
            '{"files": {"../outside.txt": {"sha256": "00"}}}',
            '{"files": {"LICENSE.txt": {}}}',
        ]
        for body in bad_bodies:
            with self.subTest(body):
                manifest.write_text(body)
                self.assertIn("VENDOR_MANIFEST_INVALID", codes(check_skills.check(self.tmp, manifest)))

    def test_cli_does_not_leak_a_secret_through_invalid_name_diagnostics(self):
        secret = "ghp_" + "z" * 30
        make_repo(self.tmp, skill=GOOD_SKILL.replace("name: demo-skill", "name: " + secret))
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [self.tmp])
        self.assertEqual(code, 1)
        self.assertIn("NAME", out)
        self.assertNotIn(secret, out + err)

    def test_cli_does_not_leak_a_secret_through_manifest_path_errors(self):
        secret = "ghp_" + "z" * 30
        make_repo(self.tmp)
        manifest = self.tmp.parent / (self.tmp.name + "-invalid-vendor.json")
        manifest.write_text(json.dumps({"files": {"../" + secret: {"sha256": "0" * 64}}}))
        self.addCleanup(lambda: manifest.unlink(missing_ok=True))
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [self.tmp, "--vendor-manifest", manifest])
        self.assertEqual(code, 1)
        self.assertIn("VENDOR_MANIFEST_INVALID", out)
        self.assertNotIn(secret, out + err)

    def test_public_product_names_are_allowed(self):
        make_repo(self.tmp, guide="# Guide\n\nOrcaSlicer, ScanRuler, CadQuery and Ezopek are public names.\n")
        self.assertEqual(check_skills.check(self.tmp), [])

    def test_external_deny_terms_are_supplied_by_the_caller_not_shipped(self):
        # ZZ-SYNTHETIC-DENIED is a visibly synthetic stand-in for an org-specific term
        make_repo(self.tmp, guide="# Guide\n\nmentions ZZ-SYNTHETIC-DENIED here\n")
        self.assertEqual(check_skills.check(self.tmp), [], "no org-specific term is built in")
        found = check_skills.check(self.tmp, deny_terms=["ZZ-SYNTHETIC-DENIED"])
        self.assertIn("DENIED_TERM", codes(found))

    def test_deny_terms_match_whole_words_only(self):
        make_repo(self.tmp, guide="# Guide\n\nxZZ-SYNTHETIC-DENIEDy and ZZ-SYNTHETIC-DENIEDsuffix\n")
        self.assertNotIn("DENIED_TERM", codes(check_skills.check(self.tmp, deny_terms=["ZZ-SYNTHETIC-DENIED"])))

    def test_root_scripts_and_tests_are_scanned_with_no_blanket_skip(self):
        make_repo(self.tmp)
        (self.tmp / "scripts").mkdir()
        (self.tmp / "tests").mkdir()
        (self.tmp / "scripts" / "tool.py").write_text("# ZZ-SYNTHETIC-DENIED\n")
        (self.tmp / "tests" / "test_x.py").write_text("X = 'see /home/" + "someone/x'\n")
        found = check_skills.check(self.tmp, deny_terms=["ZZ-SYNTHETIC-DENIED"])
        self.assertIn(("scripts/tool.py", "DENIED_TERM"), {(p, c) for p, c, _ in found})
        self.assertIn(("tests/test_x.py", "PRIVATE_PATH"), {(p, c) for p, c, _ in found})

    def test_cli_deny_file(self):
        make_repo(self.tmp, guide="# Guide\n\nmentions ZZ-SYNTHETIC-DENIED here\n")
        deny = self.tmp.parent / (self.tmp.name + "-deny.txt")
        deny.write_text("# comment\n\nZZ-SYNTHETIC-DENIED\n")
        self.addCleanup(lambda: deny.unlink(missing_ok=True))
        checker = ROOT / "scripts" / "check_skills.py"
        code, out, _ = run_script(checker, [self.tmp, "--deny-file", deny])
        self.assertEqual(code, 1)
        self.assertIn("DENIED_TERM", out)
        code, _, _ = run_script(checker, [self.tmp, "--deny-file", self.tmp / "missing.txt"])
        self.assertEqual(code, 2)

    def test_vendor_manifest_detects_modified_file(self):
        make_repo(self.tmp)
        d = self.tmp / "skill-creator"
        d.mkdir()
        (d / "LICENSE.txt").write_bytes(b"license text")
        manifest = self.tmp / "vendor.json"
        manifest.write_text(json.dumps({"files": {"LICENSE.txt": {"sha256": hashlib.sha256(b"license text").hexdigest()}}}))
        self.assertNotIn("VENDOR_MODIFIED", codes(check_skills.check(self.tmp, manifest)))
        (d / "LICENSE.txt").write_bytes(b"license texT")
        self.assertIn("VENDOR_MODIFIED", codes(check_skills.check(self.tmp, manifest)))
        (d / "LICENSE.txt").unlink()
        self.assertIn("VENDOR_MISSING", codes(check_skills.check(self.tmp, manifest)))

    def test_cli_exit_codes(self):
        make_repo(self.tmp)
        checker = ROOT / "scripts" / "check_skills.py"
        code, out, _ = run_script(checker, [self.tmp])
        self.assertEqual(code, 0)
        self.assertIn("0 finding(s)", out)
        (self.tmp / "demo-skill" / "references" / "guide.md").write_text("see /home/" + "x/y\n")
        code, out, _ = run_script(checker, [self.tmp])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_PATH", out)
        code, _, err = run_script(checker, ["--bogus"])
        self.assertEqual(code, 2)



class CheckerOnRealTreeTest(TmpCase):
    PACKAGES = ["scope-discipline", "cad-modeling-and-reverse-engineering", "3d-printing-workflows", "skill-creator", "project-coordination"]

    def test_real_tree_is_clean(self):
        self.assertEqual(check_skills.check(ROOT), [])

    def test_all_packages_present(self):
        for name in self.PACKAGES:
            self.assertTrue((ROOT / name / "SKILL.md").is_file(), name)

    def copy_tree(self):
        dest = Path(tempfile.mkdtemp(prefix="copy-", dir=self.tmp))
        for name in self.PACKAGES:
            shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        for doc in ("README.md", "INSTALLATION.md"):
            shutil.copy(ROOT / doc, dest / doc)
        (dest / "scripts").mkdir()
        (dest / "tests").mkdir()
        shutil.copy(ROOT / "scripts" / "check_skills.py", dest / "scripts" / "check_skills.py")
        shutil.copy(Path(__file__), dest / "tests" / "test_skill_packages.py")
        return dest

    def test_copy_with_private_path_in_checker_or_tests_is_caught(self):
        for rel in ("scripts/check_skills.py", "tests/test_skill_packages.py"):
            with self.subTest(rel):
                dest = self.copy_tree()
                self.assertEqual(check_skills.check(dest), [], "positive control")
                f = dest / rel
                f.write_text(f.read_text() + "\n# see /home/" + "someone/files\n")
                self.assertIn((rel, "PRIVATE_PATH"), {(p, c) for p, c, _ in check_skills.check(dest)})

    def test_copy_with_denied_term_in_checker_or_tests_is_caught(self):
        for rel in ("scripts/check_skills.py", "tests/test_skill_packages.py"):
            with self.subTest(rel):
                dest = self.copy_tree()
                f = dest / rel
                f.write_text(f.read_text() + "\n# ZZ-SYNTHETIC-DENIED\n")
                found = check_skills.check(dest, deny_terms=["ZZ-SYNTHETIC-DENIED"])
                self.assertIn((rel, "DENIED_TERM"), {(p, c) for p, c, _ in found})

    @unittest.skipUnless(__import__("os").environ.get("SKILLS_DENY_FILE"), "set SKILLS_DENY_FILE to a private deny list")
    def test_real_tree_is_clean_against_external_deny_file(self):
        terms = [l.strip() for l in Path(__import__("os").environ["SKILLS_DENY_FILE"]).read_text().splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(check_skills.check(ROOT, deny_terms=terms), [])

    def test_copy_is_clean_then_missing_reference_is_caught(self):
        dest = self.copy_tree()
        self.assertEqual(check_skills.check(dest), [], "positive control")
        (dest / "3d-printing-workflows" / "references" / "video-and-tip-intake.md").unlink()
        found = check_skills.check(dest)
        self.assertIn("MISSING_REF", codes(found))
        self.assertTrue(any("video-and-tip-intake.md" in m for _, c, m in found if c == "MISSING_REF"))

    def test_copy_with_private_path_injected_is_caught(self):
        dest = self.copy_tree()
        ref = dest / "cad-modeling-and-reverse-engineering" / "references" / "design-and-fit-gates.md"
        ref.write_text(ref.read_text() + "\nsee /home/" + "someone/files\n")
        self.assertIn("PRIVATE_PATH", codes(check_skills.check(dest)))

    def test_copy_with_deleted_helper_script_is_caught(self):
        dest = self.copy_tree()
        (dest / "3d-printing-workflows" / "scripts" / "analyze_orca_sparse_scrape.py").unlink()
        self.assertIn("MISSING_REF", codes(check_skills.check(dest)))

    # -- skill-creator public shipping set: pinned LICENSE + adapted method documents only ----
    SC = ROOT / "skill-creator"
    SC_SHIPPED = [
        "LICENSE.txt",
        "SKILL.md",
        "UPSTREAM.md",
        "references/claude-code-evaluation.md",
        "references/portable-evaluation.md",
    ]
    SC_REMOVED = [
        "references/upstream-workflow.md", "agents/analyzer.md", "agents/comparator.md", "agents/grader.md",
        "assets/eval_review.html", "eval-viewer/generate_review.py", "eval-viewer/viewer.html", "references/schemas.md",
        "scripts/__init__.py", "scripts/aggregate_benchmark.py", "scripts/generate_report.py", "scripts/improve_description.py",
        "scripts/package_skill.py", "scripts/quick_validate.py", "scripts/run_eval.py", "scripts/run_loop.py", "scripts/utils.py",
    ]
    PINNED_LICENSE_SHA256 = "bc6b3af2f331cbc7fb0da1344efb2cbe5877a31498b4d70dbc7000f3405a1362"
    PINNED_COMMIT = "ca45fc496a3436251f191354091d557da31c15b5"

    def sc_docs(self):
        return {rel: (self.SC / rel).read_text(encoding="utf8") for rel in self.SC_SHIPPED if rel.endswith(".md")}

    def test_skill_creator_ships_only_the_license_and_the_adapted_documents(self):
        found = sorted(p.relative_to(self.SC).as_posix() for p in self.SC.rglob("*") if p.is_file())
        self.assertEqual(found, sorted(self.SC_SHIPPED))

    def test_license_is_the_pinned_upstream_apache_text_byte_for_byte(self):
        self.assertEqual(sha(self.SC / "LICENSE.txt"), self.PINNED_LICENSE_SHA256)
        self.assertIn(self.PINNED_COMMIT, self.sc_docs()["UPSTREAM.md"])

    def test_skill_creator_docs_do_not_point_at_removed_files_or_claim_bundled_automation(self):
        for rel, text in self.sc_docs().items():
            for gone in self.SC_REMOVED:
                self.assertIsNone(re.search(r"(?<![\w/.-])" + re.escape(gone), text), f"{rel} still points at removed {gone}")
            for phrase in ("kept unmodified", "Eighteen files", "bundled upstream", "unmodified upstream package"):
                self.assertNotIn(phrase.lower(), text.lower(), f"{rel}: {phrase}")

    def test_skill_creator_states_optional_automation_is_not_supplied_or_qualified_and_does_not_prescribe_it(self):
        docs = self.sc_docs()
        for rel in ("UPSTREAM.md", "references/claude-code-evaluation.md"):
            low = docs[rel].lower()
            self.assertIn("not supplied", low, rel)
            self.assertIn("not qualified", low, rel)
        for rel, text in docs.items():
            for cmd in ("git clone", "pip install", "curl ", "wget ", "npx "):
                self.assertNotIn(cmd, text, f"{rel} must not prescribe fetching/running upstream tooling: {cmd}")

    def test_adapted_documents_carry_a_prominent_change_and_attribution_notice_near_the_top(self):
        docs = self.sc_docs()

        def head(rel):
            return "\n".join(docs[rel].splitlines()[:10])

        for rel in ("references/claude-code-evaluation.md", "references/portable-evaluation.md"):
            for needle in ("Anthropic", "Apache-2.0", "UPSTREAM.md"):
                self.assertIn(needle, head(rel), f"{rel}: {needle}")
        low = head("references/claude-code-evaluation.md").lower()
        for needle in (self.PINNED_COMMIT, "adapted", "changed", "not supplied", "not qualified"):
            self.assertIn(needle, low, f"claude-code-evaluation.md notice lacks {needle}")

    def test_real_tree_is_clean_against_a_manifest_that_binds_exactly_the_shipped_license(self):
        manifest = self.tmp / "public-vendor.json"
        manifest.write_text(json.dumps({"files": {"LICENSE.txt": {"sha256": self.PINNED_LICENSE_SHA256}}}))
        self.assertEqual(check_skills.check(ROOT, manifest), [])
        dest = self.copy_tree()
        lic = dest / "skill-creator" / "LICENSE.txt"
        lic.write_bytes(lic.read_bytes() + b"\n")
        self.assertIn("VENDOR_MODIFIED", codes(check_skills.check(dest, manifest)))

    @unittest.skipUnless(__import__("os").environ.get("PUBLIC_VENDOR_MANIFEST"), "set PUBLIC_VENDOR_MANIFEST to the acceptance manifest")
    def test_real_tree_is_clean_against_the_acceptance_public_vendor_manifest(self):
        self.assertEqual(check_skills.check(ROOT, __import__("os").environ["PUBLIC_VENDOR_MANIFEST"]), [])

    def test_skill_frontmatter_has_no_client_specific_keys(self):
        for name in self.PACKAGES:
            fm, err = check_skills.parse_frontmatter((ROOT / name / "SKILL.md").read_text())
            self.assertIsNone(err, name)
            self.assertLessEqual(set(fm), check_skills.ALLOWED_KEYS, name)


class GithubTokenSecretTest(TmpCase):
    """Correction 18: the SECRET heuristic also covers the other common GitHub token shapes. It stays a heuristic,
    never a complete credential detector. Every fixture is assembled at run time from synthetic pieces (never a
    real token), so this scanned source stays clean."""

    BODY = "AbCdEf0123456789" + "GhIjKl0123456789"  # 32 synthetic characters
    FORMATS = {
        "gho": "gho" + "_" + BODY,
        "ghu": "ghu" + "_" + BODY,
        "ghs": "ghs" + "_" + BODY,
        "ghr": "ghr" + "_" + BODY,
        "github_pat": "github" + "_pat_" + BODY + "_" + "Zz9" * 8,
    }

    def test_control_the_already_covered_ghp_format_is_still_flagged(self):
        token = "ghp" + "_" + self.BODY
        make_repo(self.tmp, guide=f"# Guide\n\ntoken {token}\n")
        found = check_skills.check(self.tmp)
        self.assertIn("SECRET", codes(found))

    def test_other_github_token_formats_are_flagged_with_the_line_and_without_the_value(self):
        for label, token in self.FORMATS.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\ntoken {token}\n")
                    found = check_skills.check(d)
                    hit = [f for f in found if f[1] == "SECRET"]
                    self.assertTrue(hit, f"{label} was not flagged: {found}")
                    self.assertTrue(all("line 3" in m for _, _, m in hit), hit)
                    self.assertFalse(any(self.BODY in m or self.BODY in p for p, _, m in found), "the value must be redacted")

    def test_the_root_cli_flags_each_format_and_never_echoes_any_part_of_the_value(self):
        for label, token in self.FORMATS.items():
            with self.subTest(label):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\ntoken {token}\n")
                    code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
                    self.assertEqual(code, 1, (out, err))
                    self.assertIn("SECRET", out)
                    self.assertNotIn(self.BODY, out + err)
                    self.assertNotIn(self.BODY[:12], out + err)
                    self.assertNotIn(token.split("_")[0] + "_", out.replace("SECRET", "") + err)

    def test_control_short_look_alikes_and_plain_words_are_not_flagged(self):
        samples = ["gho" + "_short", "github" + "_pat_", "github" + "_pat_abc", "ghost_story_of_a_long_name_here_okay", "the gho word", "ghp" + "_"]
        for text in samples:
            with self.subTest(text):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
                    self.assertNotIn("SECRET", codes(check_skills.check(d)))


class WindowsUsersPrefixTest(TmpCase):
    """Correction 33 (synthetic): ONE drive-qualified Windows Users-prefix rule: any ASCII drive letter, `Users` in any letter case (no global
    ignore-case flag), either slash spelling at either separator. POSIX rules are unchanged and case-sensitive. Tokens are assembled at run
    time from visibly synthetic pieces so this scanned source holds no matching literal."""

    BACK, FWD = "\\", "/"

    def prefix(self, drive, word, first, second):
        return f"{drive}:{first}{word}{second}"

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nsee {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_every_drive_case_and_slash_spelling_of_the_users_prefix_is_flagged(self):
        words = {"canonical": "Us" + "ers", "lower": "us" + "ers", "upper": "US" + "ERS", "mixed": "uS" + "eRs"}
        for drive in ("C", "c", "D", "z"):
            for word_label, word in words.items():
                for first, second in ((self.BACK, self.BACK), (self.FWD, self.FWD), (self.BACK, self.FWD), (self.FWD, self.BACK)):
                    text = self.prefix(drive, word, first, second) + "alice" + first + "x"
                    with self.subTest(f"{drive} {word_label} {first}{second}"):
                        self.assertEqual(self.codes_for(text), ["PRIVATE_PATH"])

    def test_numeric_and_service_style_components_and_a_bare_prefix_are_flagged_too(self):
        for text in (self.prefix("C", "us" + "ers", self.FWD, self.FWD) + "1234/Documents", self.prefix("E", "US" + "ERS", self.BACK, self.BACK) + "_svc$\\x",
                     self.prefix("d", "Us" + "ers", self.FWD, self.FWD)):
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), ["PRIVATE_PATH"])

    def test_control_near_misses_posix_case_and_non_drive_forms_are_not_flagged(self):
        cases = {
            "a longer directory name": self.prefix("C", "Us" + "ersx", self.BACK, self.BACK) + "alice",
            "a different directory": "C:\\Program Files\\Tool",
            "no trailing separator": "C:" + "\\Us" + "ers",
            "a digit is not a drive": "1:" + "\\Us" + "ers\\x",
            "a URL with a double slash": "https://" + "us" + "ers.example.test/x",
            "POSIX lower-case users stays case-sensitive": "/us" + "ers/" + "alice/x",
            "POSIX upper-case home stays case-sensitive": "/HO" + "ME/" + "alice/x",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), [])

    def test_the_posix_rules_are_unchanged(self):
        for text in ("/ho" + "me/" + "alice/x", "/Us" + "ers/" + "4711/x", "/ro" + "ot/.ssh"):
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), ["PRIVATE_PATH"])

    def test_the_real_cli_reports_a_lower_case_forward_slash_drive_path_without_echoing_the_component(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nsee " + self.prefix("d", "us" + "ers", self.FWD, self.FWD) + "qz8161/x\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_PATH", out)
        self.assertNotIn("qz8161", out + err)

    def test_the_private_deny_hook_and_the_tree_stay_clean_and_nothing_matches_itself(self):
        rx = next(rx for code, rx in check_skills.PRIVACY if code == "PRIVATE_PATH")
        for path in (ROOT / "scripts" / "check_skills.py", ROOT / "tests" / "test_checker.py"):
            self.assertIsNone(rx.search(path.read_text(encoding="utf8")), f"{path.name} would flag itself")
        self.assertEqual(check_skills.check(ROOT), [])


class RootLinkRegularFileTest(TmpCase):
    """Correction 33: the module's own promise is that README/INSTALLATION local links resolve to existing FILES inside the root. A directory
    that merely has a file-like name, or a plain folder, is not a file; the one deliberate exception is a skill folder (a directory holding
    SKILL.md), which is what the shipped README links to. Containment is still decided before any probe, and an escaped target is never echoed."""

    MARK = "rootlink-marker-7d2b"
    DOCS = ("README.md", "INSTALLATION.md")

    def build(self):
        base = Path(tempfile.mkdtemp(dir=self.tmp))
        root = base / "repo"
        root.mkdir()
        make_repo(root)
        (root / "fixture.md").write_text("# fixture\n")
        (root / "dirfixture.md").mkdir()
        (root / "docs-dir").mkdir()
        (base / f"{self.MARK}-file.md").write_text("outside\n")
        (base / f"{self.MARK}-dir.md").mkdir()
        return root

    def codes(self, doc, link):
        root = self.build()
        path = root / doc
        path.write_text(path.read_text() + f"\n[x]({link})\n")
        found = check_skills.check(root)
        self.assertNotIn(self.MARK, " ".join(f"{p} {c} {m}" for p, c, m in found), "an escaped target must never be echoed")
        return [c for p, c, _ in found if p == doc]

    def test_a_directory_is_not_an_existing_file_in_either_root_document(self):
        for doc in self.DOCS:
            for label, link in {
                "a directory with a file-like name": "dirfixture.md",
                "the same with a trailing slash": "dirfixture.md/",
                "a plain folder without SKILL.md": "docs-dir/",
                "the references folder of a skill": "demo-skill/references/",
            }.items():
                with self.subTest(f"{doc}: {label}"):
                    self.assertEqual(self.codes(doc, link), ["BROKEN_LINK"])

    def test_control_regular_files_and_skill_folders_are_accepted_and_missing_or_escaping_targets_keep_their_codes(self):
        for doc in self.DOCS:
            cases = {
                "an existing regular file": ("fixture.md", []),
                "an existing regular file inside a skill": ("demo-skill/references/guide.md", []),
                "a skill folder (directory holding SKILL.md)": ("demo-skill/", []),
                "a skill folder without a trailing slash": ("demo-skill", []),
                "a missing target": ("missing-fixture.md", ["BROKEN_LINK"]),
                "an existing outside file": (f"../{self.MARK}-file.md", ["ESCAPES_ROOT"]),
                "an existing outside directory": (f"../{self.MARK}-dir.md", ["ESCAPES_ROOT"]),
                "a missing outside target": (f"../{self.MARK}-absent.md", ["ESCAPES_ROOT"]),
                "an external URL": ("https://example.test/x", []),
                "a fragment only": ("#top", []),
            }
            for label, (link, expected) in cases.items():
                with self.subTest(f"{doc}: {label}"):
                    self.assertEqual(self.codes(doc, link), expected)

    def test_the_real_cli_reports_the_directory_link_as_broken_and_the_module_states_the_contract(self):
        root = self.build()
        (root / "README.md").write_text((root / "README.md").read_text() + "\n[x](dirfixture.md)\n")
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [root])
        self.assertEqual(code, 1, (out, err))
        self.assertIn("BROKEN_LINK", out)
        doc = " ".join(check_skills.__doc__.lower().split())
        for needle in ("regular files", "skill folder", "inside the supplied root"):
            self.assertIn(needle, doc, needle)

    def test_control_package_references_to_directories_keep_their_existing_behaviour(self):
        root = self.build()
        skill = root / "demo-skill" / "SKILL.md"
        skill.write_text(skill.read_text() + "\nSee [dir](references/).\n")
        self.assertNotIn("MISSING_REF", [c for _, c, _ in check_skills.check(root)])


class PrivateHomeComponentTest(TmpCase):
    """Correction 31 (synthetic): PRIVATE_PATH covers a COMPLETE nonempty home-user component (letters, digits, underscore-led service
    accounts, hidden or hyphenated names) under the standard POSIX, macOS and Windows home prefixes and the conventional privileged home,
    not only a letter-initial name. It is standard-directory coverage, not discovery of real homes, custom roots or a filesystem service.
    Every path is assembled at run time from clearly synthetic pieces, so this scanned source holds no private identifier or home prefix."""

    POSIX = "/ho" + "me/"
    MAC = "/Us" + "ers/"
    PRIVILEGED = "/ro" + "ot"
    WINDOWS = "C:" + "\\Us" + "ers\\"
    COMPONENTS = {
        "letters": "alice",
        "digits only": "1000",
        "digit-initial": "9lives",
        "underscore-led service account": "_service",
        "hidden name": ".svc",
        "hyphenated": "svc-user",
        "dollar-suffixed": "svc$",
    }

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nsee {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_every_nonempty_home_user_component_is_flagged_under_the_standard_prefixes(self):
        for prefix_label, prefix in (("POSIX home", self.POSIX), ("macOS users", self.MAC)):
            for label, component in self.COMPONENTS.items():
                with self.subTest(f"{prefix_label}: {label}"):
                    self.assertEqual(self.codes_for(f"{prefix}{component}/notes"), ["PRIVATE_PATH"])

    def test_the_privileged_home_and_windows_users_components_are_flagged(self):
        cases = {
            "privileged home with a subpath": f"{self.PRIVILEGED}/.ssh/config",
            "privileged home on its own": f"{self.PRIVILEGED}",
            "privileged home in a sentence": f"in {self.PRIVILEGED}.",
            "windows letter component": f"{self.WINDOWS}alice\\Documents",
            "windows numeric component": f"{self.WINDOWS}1234\\Documents",
            "windows underscore component": f"{self.WINDOWS}_svc$\\x",
            "windows prefix alone (existing behaviour kept)": f"{self.WINDOWS}",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), ["PRIVATE_PATH"])

    def test_control_placeholders_empty_components_and_ordinary_words_are_not_flagged(self):
        cases = {
            "angle-bracket placeholder": f"{self.POSIX}<user>/x",
            "environment-variable placeholder": f"{self.POSIX}$USER/x",
            "brace placeholder": f"{self.MAC}{{user}}/x",
            "tilde": "~/notes",
            "windows environment variable": "%USERPROFILE%\\Documents",
            "bare directory with no user": f"the {self.POSIX} directory",
            "bare macOS users directory": f"the {self.MAC} directory",
            "dot-only components": f"{self.POSIX}../x and {self.POSIX}./y",
            "root as a word": "the root directory and a root cause",
            "a longer name that merely starts like the privileged home": f"{self.PRIVILEGED}ed/path and {self.PRIVILEGED}-cause",
            "root inside a longer path": "src/root/x and https://host.example/root/y",
            "clean prose": "nothing private here",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), [])

    def test_the_real_cli_reports_a_numeric_home_without_echoing_the_component(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nsee {self.POSIX}4711/notes\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_PATH", out)
        self.assertNotIn("4711", out + err)

    def test_the_pattern_source_and_these_tests_do_not_match_themselves_and_there_are_no_source_exemptions(self):
        rx = next(rx for code, rx in check_skills.PRIVACY if code == "PRIVATE_PATH")
        for path in (ROOT / "scripts" / "check_skills.py", ROOT / "tests" / "test_checker.py"):
            self.assertIsNone(rx.search(path.read_text(encoding="utf8")), f"{path.name} would flag itself")
        self.assertEqual(check_skills.check(ROOT), [], "the real tree, including the checker and its tests, stays clean (no suffix or source exemption)")


class ExternalUriClassificationTest(TmpCase):
    """Correction 29 (synthetic): a link is EXTERNAL, not a local file, when it carries a scheme (case-insensitive, RFC 3986 section 3.1) or
    is a network-path reference starting with two slashes (section 4.2). External references are never fetched, probed, rewritten or
    credential-handled. One slash is still an absolute LOCAL path and `../` still escapes; in-bound missing links keep their classification."""

    EXTERNAL = {
        "network-path": "//example.test/guide.md",
        "network-path with a fragment": "//example.test/guide.md#frag",
        "network-path with dot-dot segments": "//example.test/a/../b.md",
        "network-path host only": "//example.test",
        "lower-case scheme": "https://example.test/a.md",
        "upper-case scheme": "HTTPS://example.test/a.md",
        "mixed-case scheme": "Https://example.test/a.md",
        "upper-case ftp scheme": "FTP://example.test/x",
    }
    MARK = "uri-marker-5c1e"

    def doc_codes(self, doc, token):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d)
            path = Path(d) / doc
            path.write_text(path.read_text() + f"\n[x]({token})\n")
            return [c for p, c, _ in check_skills.check(d) if p == doc]

    def package_codes(self, where, token):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            if where == "SKILL.md":
                make_repo(d, skill=GOOD_SKILL + f"\n[x]({token})\n")
            else:
                make_repo(d, guide=f"# Guide\n\nBack to [skill](../SKILL.md). [x]({token})\n")
            return [c for p, c, _ in check_skills.check(d) if p == f"demo-skill/{where}"]

    def test_external_references_produce_no_finding_in_root_documents_and_in_package_files(self):
        for label, token in self.EXTERNAL.items():
            for doc in ("README.md", "INSTALLATION.md"):
                with self.subTest(f"{doc}: {label}"):
                    self.assertEqual(self.doc_codes(doc, token), [])
            for where in ("SKILL.md", "references/guide.md"):
                with self.subTest(f"{where}: {label}"):
                    self.assertEqual(self.package_codes(where, token), [])

    def test_external_references_are_never_probed_on_the_filesystem(self):
        seen = []
        real_stat, real_lstat = os.stat, os.lstat

        def recording(real):
            def wrapper(path, *args, **kwargs):
                seen.append(os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else "")
                return real(path, *args, **kwargs)
            return wrapper

        links = " ".join(f"[{i}]({token})" for i, token in enumerate(self.EXTERNAL.values()))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, readme=f"demo-skill {links}\n", skill=GOOD_SKILL + "\n" + links + "\n")
            with mock.patch.object(os, "stat", side_effect=recording(real_stat)), mock.patch.object(os, "lstat", side_effect=recording(real_lstat)):
                found = check_skills.check(d)
        self.assertTrue(seen, "fixture sanity: the observer sees ordinary stat calls")
        self.assertEqual([p for p in seen if "example.test" in str(p)], [], "an external reference must never be resolved against the filesystem")
        self.assertEqual(found, [])

    def test_control_single_slash_and_dot_dot_stay_local_and_in_bound_missing_links_keep_their_classification(self):
        for doc in ("README.md", "INSTALLATION.md"):
            with self.subTest(f"{doc}: absolute-path reference"):
                self.assertEqual(self.doc_codes(doc, f"/{self.MARK}/a.md"), ["ESCAPES_ROOT"])
            with self.subTest(f"{doc}: parent-directory reference"):
                self.assertEqual(self.doc_codes(doc, f"../{self.MARK}/a.md"), ["ESCAPES_ROOT"])
            with self.subTest(f"{doc}: in-bound missing link"):
                self.assertEqual(self.doc_codes(doc, f"{self.MARK}-missing.md"), ["BROKEN_LINK"])
        for where in ("SKILL.md", "references/guide.md"):
            with self.subTest(f"{where}: absolute-path reference"):
                self.assertIn("ESCAPES_PACKAGE", self.package_codes(where, f"/{self.MARK}/a.md"))
            with self.subTest(f"{where}: in-bound missing reference"):
                self.assertIn("MISSING_REF", self.package_codes(where, f"references/{self.MARK}-missing.md"))
        self.assertEqual(self.doc_codes("README.md", "demo-skill/references/guide.md"), [], "a valid inside link stays clean")


class PrivateIPv4AtomTest(TmpCase):
    """Correction 29: a candidate is a COMPLETE dotted-decimal atom (not a substring of a longer one), validated by the stdlib `ipaddress`
    module, and only then tested against the three RFC1918 ranges. Documentation, reserved, loopback and link-local ranges stay allowed.
    All strings are assembled at run time so this scanned source stays clean."""

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_a_complete_valid_address_is_flagged_in_ordinary_punctuation_and_port_contexts(self):
        ips = ["10" + ".1.2.3", "10" + ".255.255.255", "172" + ".16.0.1", "172" + ".31.255.254", "192" + ".168.0.254"]
        contexts = ["{}", "{}.", "{},", "({})", "'{}'", "{}:8080", "http://{}/x", "{}/24", "a={};", "host-{}"]
        for ip in ips:
            for context in contexts:
                with self.subTest(context.format(ip)):
                    self.assertEqual(self.codes_for(context.format(ip)), ["PRIVATE_IP"])

    def test_a_substring_of_a_longer_dotted_atom_or_an_invalid_candidate_is_not_an_address(self):
        cases = {
            "five components": "10" + ".1.2.3.4",
            "five components, 172 class": "172" + ".16.0.1.9",
            "five components, 192 class": "192" + ".168.1.1.1",
            "preceded by a dotted atom": "1." + "10" + ".1.2.3",
            "preceded by two dotted atoms": "9.9." + "10" + ".1.2.3",
            "last octet out of range": "10" + ".1.2.256",
            "last octet far out of range": "10" + ".1.2.999",
            "middle octet out of range": "10" + ".256.1.1",
            "172 class out of range": "172" + ".16.0.300",
            "192 class out of range": "192" + ".168.1.999",
            "four-digit octet": "10" + ".1.2.3000",
            "leading zero in an octet": "10" + ".01.2.3",
            "two components": "10" + ".1",
            "three components": "10" + ".1.2",
            "trailing letter": "10" + ".1.2.3x",
            "leading letter": "v10" + ".1.2.3",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), [])

    def test_control_non_rfc1918_ranges_stay_allowed_even_when_the_stdlib_calls_them_private(self):
        allowed = ["172" + ".15.0.1", "172" + ".32.0.1", "11" + ".1.2.3", "193" + ".168.1.1", "127" + ".0.0.1", "0" + ".0.0.0",
                   "169" + ".254.1.1", "100" + ".64.0.1", "198" + ".51.100.7", "203" + ".0.113.9", "255" + ".255.255.255", "8" + ".8.8.8"]
        for text in allowed:
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), [])

    def test_control_the_existing_ipv6_policy_is_unchanged(self):
        self.assertEqual(self.codes_for("fd00" + "::1"), ["PRIVATE_IP"])
        self.assertEqual(self.codes_for("2001:db8::1"), [])

    def test_the_cli_reports_a_complete_address_without_echoing_it_and_ignores_a_five_component_number(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + "172" + ".20.7.9\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_IP", out)
        self.assertNotIn(".20.7.9", out + err)
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + "172" + ".20.7.9.1\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 0, (out, err))


class VisionServerStartRemovalWordingTest(unittest.TestCase):
    """Correction 29: DOCUMENTARY guard only. The geometry-side vision reference must not carry a recipe that starts a server or an application
    in an operator session (the entry's hard safeguards forbid services and the operator's desktop during geometry work). It checks readiness
    read-only, leaves unavailable validation pending, and sends any start or restart to a separately scoped environment task."""

    def doc(self):
        return " ".join((ROOT / "cad-modeling-and-reverse-engineering" / "references" / "vision-model-review.md").read_text(encoding="utf8").lower().split())

    def test_the_optional_start_recipe_is_gone_and_unavailable_validation_stays_pending(self):
        text = self.doc()
        for removed in ("start the verified application inside that existing session", "instead of inventing a new display"):
            self.assertNotIn(removed, text, removed)
        for needle in ("read-only readiness check", "leave the model and gui validation pending", "separately scoped", "not part of this geometry reference",
                       "different actions", "a timeout grants no authority"):
            self.assertIn(needle, text, needle)

    def test_the_entry_hard_safeguard_is_not_widened(self):
        entry = " ".join((ROOT / "cad-modeling-and-reverse-engineering" / "SKILL.md").read_text(encoding="utf8").lower().split())
        self.assertIn("do not touch printers, firmware, services or the operator's real desktop as part of geometry work", entry)


class ResolverContainmentOrderingTest(TmpCase):
    """Correction 27 (synthetic): containment is classified on the NORMALISED candidate BEFORE any existence probe, in root documents
    (ESCAPES_ROOT) and in skill/package references (ESCAPES_PACKAGE), for existing AND nonexistent relative/absolute/anchored targets.
    An escaped target is never echoed, never stat'ed and never re-rooted to another package location. In-bound missing references keep
    their MISSING_REF/BROKEN_LINK classification, and normal inside references, fallback bases, external URLs and fragments are unchanged."""

    MARK = "escape-marker-9f3a"  # a neutral token: not a secret/privacy shape, so only the resolver can decide how it is reported
    DOCS = ("README.md", "INSTALLATION.md")

    def build(self, other=False, **kwargs):
        base = Path(tempfile.mkdtemp(dir=self.tmp))
        root = base / "repo"
        root.mkdir()
        make_repo(root, **kwargs)
        (base / f"{self.MARK}-existing.md").write_text("outside\n")  # an EXISTING outside file next to the repo root
        if other:  # a second inside reference target; only referenced (hence reachable, not an orphan) by the cases that ask for it
            (root / "demo-skill" / "references" / "other.md").write_text("# other\n")
        return root

    def everything(self, findings):
        return " ".join(f"{p} {c} {m}" for p, c, m in findings)

    def test_nonexistent_and_existing_escaping_links_in_root_documents_are_escape_findings_and_never_echoed(self):
        links = {
            "relative nonexistent": f"[x](../{self.MARK}/missing.md)",
            "relative nonexistent with an anchor": f"[x](../{self.MARK}/missing.md#top)",
            "absolute nonexistent": f"[x](/{self.MARK}-abs/missing.md)",
            "dot-dot through an inside folder": f"[x](demo-skill/../../{self.MARK}.md)",
            "relative existing": f"[x](../{self.MARK}-existing.md)",
        }
        for doc in self.DOCS:
            for label, link in links.items():
                with self.subTest(f"{doc}: {label}"):
                    root = self.build()
                    (root / doc).write_text((root / doc).read_text() + "\n" + link + "\n")
                    found = check_skills.check(root)
                    self.assertEqual([c for p, c, _ in found if p == doc], ["ESCAPES_ROOT"], found)
                    self.assertNotIn(self.MARK, self.everything(found), "an escaped target must never be echoed")

    def test_nonexistent_and_existing_escaping_references_in_a_skill_and_its_references_are_package_escapes_never_missing(self):
        skill_cases = {
            "link, nonexistent": f"\n[x](../{self.MARK}/missing.md)\n",
            "link, nonexistent, absolute": f"\n[x](/{self.MARK}-abs/missing.md)\n",
            "link, nonexistent, with an anchor": f"\n[x](../{self.MARK}/missing.md#top)\n",
            "prefixed path, nonexistent": f"\nSee `../../references/{self.MARK}.md`.\n",
            "prefixed path one level up, nonexistent": f"\nSee `../references/{self.MARK}.md`.\n",
        }
        for label, extra in skill_cases.items():
            with self.subTest(f"SKILL.md: {label}"):
                root = self.build(skill=GOOD_SKILL + extra)
                found = check_skills.check(root)
                skill_codes = [c for p, c, _ in found if p == "demo-skill/SKILL.md"]
                self.assertIn("ESCAPES_PACKAGE", skill_codes, found)
                self.assertNotIn("MISSING_REF", skill_codes, found)
                self.assertNotIn(self.MARK, self.everything(found))
        with self.subTest("references/guide.md: link, nonexistent"):
            root = self.build(guide=f"# Guide\n\nBack to [skill](../SKILL.md). [x](../../{self.MARK}/missing.md)\n")
            found = check_skills.check(root)
            guide_codes = [c for p, c, _ in found if p == "demo-skill/references/guide.md"]
            self.assertIn("ESCAPES_PACKAGE", guide_codes, found)
            self.assertNotIn("MISSING_REF", guide_codes, found)
            self.assertNotIn(self.MARK, self.everything(found))
        with self.subTest("SKILL.md: link, EXISTING outside the package"):  # before the fix this code echoed the escaped target
            root = self.build(skill=GOOD_SKILL + f"\n[x](../{self.MARK}-existing.md)\n")
            found = check_skills.check(root)
            self.assertIn("ESCAPES_PACKAGE", [c for _, c, _ in found], found)
            self.assertNotIn(self.MARK, self.everything(found))

    def test_control_inside_references_keep_their_classification_and_fallback_bases_external_urls_and_fragments_still_work(self):
        root = self.build(skill=GOOD_SKILL + "\nAlso `references/missing-marker.md`.\n")
        found = check_skills.check(root)
        self.assertIn(("demo-skill/SKILL.md", "MISSING_REF", "references/missing-marker.md"), found, "a genuinely in-package missing reference keeps its classification")
        root = self.build(readme="demo-skill [m](missing-marker.md)\n")
        self.assertIn(("README.md", "BROKEN_LINK", "missing-marker.md"), check_skills.check(root))
        clean = {
            "an inside reference resolved through the fallback base": dict(other=True, guide="# Guide\n\nBack to [skill](../SKILL.md). See `references/other.md`.\n"),
            "an external URL and a fragment-only link": dict(guide="# Guide\n\nBack to [skill](../SKILL.md). [e](https://example.org/x) [f](#top)\n"),
            "an inside dot-dot link": dict(other=True, guide="# Guide\n\nBack to [skill](../SKILL.md). [s](../references/other.md)\n"),
        }
        for label, kwargs in clean.items():
            with self.subTest(label):
                self.assertEqual(check_skills.check(self.build(**kwargs)), [])

    def test_the_real_cli_reports_the_escape_codes_without_echoing_the_target(self):
        root = self.build(readme=f"demo-skill [x](../{self.MARK}/missing.md)\n")
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [root])
        self.assertEqual(code, 1, (out, err))
        self.assertIn("ESCAPES_ROOT", out)
        self.assertNotIn("BROKEN_LINK", out)
        self.assertNotIn(self.MARK, out + err)
        root = self.build(skill=GOOD_SKILL + f"\n[x](../{self.MARK}/missing.md)\n")
        code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [root])
        self.assertEqual(code, 1, (out, err))
        self.assertIn("ESCAPES_PACKAGE", out)
        self.assertNotIn("MISSING_REF", out)
        self.assertNotIn(self.MARK, out + err)

    def test_an_escaping_target_is_never_stat_ed_before_containment_is_decided(self):
        seen = []
        real_stat, real_lstat = os.stat, os.lstat

        def recording(real):
            def wrapper(path, *args, **kwargs):
                seen.append(os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else "")
                return real(path, *args, **kwargs)
            return wrapper

        root = self.build(readme=f"demo-skill [x](../{self.MARK}/missing.md) [y](../{self.MARK}-existing.md)\n",
                          skill=GOOD_SKILL + f"\n[z](../{self.MARK}/missing.md)\n")
        with mock.patch.object(os, "stat", side_effect=recording(real_stat)), mock.patch.object(os, "lstat", side_effect=recording(real_lstat)):
            found = check_skills.check(root)
        self.assertTrue(seen, "fixture sanity: the observer sees ordinary stat calls")
        self.assertEqual([p for p in seen if self.MARK in str(p)], [], "no path of an escaping target may be probed")
        self.assertEqual(sorted(c for _, c, _ in found if c.startswith("ESCAPES_")), ["ESCAPES_PACKAGE", "ESCAPES_ROOT", "ESCAPES_ROOT"])


class PrivateIPv4PrecisionTest(TmpCase):
    """Correction 27: the RFC1918 heuristic needs the FOUR-octet shape. Strings are assembled at run time so this scanned source stays clean.
    Only range detection is kept; this does not widen to every reserved range and is not a network scanner."""

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
            return [code for _, code, _ in check_skills.check(d)]

    def test_ordinary_four_octet_addresses_in_the_three_private_classes_are_still_flagged(self):
        for text in ("10" + ".1.2.3", "10" + ".255.255.255", "172" + ".16.0.1", "172" + ".31.255.254", "192" + ".168.1.1", "192" + ".168.0.254"):
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), ["PRIVATE_IP"])

    def test_three_component_numbers_in_the_same_classes_are_not_addresses(self):
        for text in ("10" + ".1.2", "10" + ".255.1", "version 10" + ".2.3", "172" + ".16.0", "172" + ".31.7", "192" + ".168.1"):
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), [])

    def test_control_neighbouring_public_ranges_and_other_shapes_stay_unflagged(self):
        for text in ("172" + ".15.0.1", "172" + ".32.0.1", "11" + ".1.2.3", "193" + ".168.1.1", "9" + ".1.2.3", "1.2.3"):
            with self.subTest(text):
                self.assertEqual(self.codes_for(text), [])

    def test_the_cli_still_reports_a_four_octet_address_without_echoing_it(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + "10" + ".4.5.6\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_IP", out)
        self.assertNotIn(".4.5.6", out + err)


class PrivateIPv4MaximalAtomTest(TmpCase):
    """Correction 55 (synthetic): the candidate is the WHOLE maximal digits-and-dots atom. A valid private address followed by a repeated dot
    or a dot-led remainder (`addr..2`, `addr..`, `addr...`, `addr..word`) is a malformed atom, not an address with trailing punctuation: it is
    consumed or refused as a whole instead of backtracking to the shorter valid prefix. One trailing sentence period still ends a valid address.
    Addresses are generated at run time from synthetic pieces, so this scanned source holds no private address literal."""

    ADDRESSES = ("10" + ".1.2.3", "172" + ".16.0.1", "192" + ".168.0.254")

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_a_valid_prefix_of_a_malformed_repeated_dot_atom_is_not_an_address(self):
        for ip in self.ADDRESSES:
            for suffix in ("..2", "..", "...", "..word", "...2", ".." + "9" * 3):
                with self.subTest(f"{ip}{suffix}"):
                    self.assertEqual(self.codes_for(ip + suffix), [])

    def test_control_the_same_valid_addresses_are_still_flagged_with_ordinary_endings(self):
        for ip in self.ADDRESSES:
            for ending in ("", ".", ",", ";", ")", ":8080", "/24", " and more"):
                with self.subTest(f"{ip}{ending}"):
                    self.assertEqual(self.codes_for(ip + ending), ["PRIVATE_IP"])

    def test_control_five_component_and_glued_atoms_stay_unflagged(self):
        for ip in self.ADDRESSES:
            for text in (ip + ".4", ip + "x", "v" + ip, "1." + ip):
                with self.subTest(text):
                    self.assertEqual(self.codes_for(text), [])

    def test_the_search_contract_returns_a_match_for_the_whole_valid_atom_only(self):
        detector = next(rx for code, rx in check_skills.PRIVACY if code == "PRIVATE_IP" and isinstance(rx, check_skills._PrivateIPv4))
        ip = self.ADDRESSES[0]
        self.assertEqual(detector.search("see " + ip + " now").group(0), ip)
        self.assertIsNone(detector.search("see " + ip + "..2 now"))
        self.assertIsNone(detector.search("see " + ip + ".. now"))

    def test_the_cli_reports_a_valid_address_and_ignores_a_malformed_repeated_dot_atom(self):
        ip = self.ADDRESSES[1]
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + ip + "..2\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 0, (out, err))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + ip + ".\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_IP", out)
        self.assertNotIn(ip[3:], out + err)


class PrivateIPv4DotWordBoundaryTest(TmpCase):
    """Correction 58 (synthetic): a single period directly followed by a word character (letter, digit, underscore or a Unicode letter) is
    not sentence punctuation, so `addr.word` is a glued atom and not an address, exactly like `addrword`. One period before whitespace, the
    end of the text or other punctuation still ends a valid address, and the returned match span excludes that sentence period. Addresses are
    generated at run time from synthetic pieces; no private address literal appears in this scanned source."""

    ADDRESSES = ("10" + ".2.4.6", "172" + ".17.1.1", "192" + ".168.7.8")

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nvalue {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_a_single_period_followed_by_a_word_character_is_a_glued_atom_not_an_address(self):
        for ip in self.ADDRESSES:
            for suffix in (".word", ".w", "._x", ".9a", ".été", ".example.test", "." + "x" * 5):
                with self.subTest(f"{ip}{suffix}"):
                    self.assertEqual(self.codes_for(ip + suffix), [])

    def test_control_a_single_sentence_period_before_whitespace_or_punctuation_still_ends_a_valid_address(self):
        for ip in self.ADDRESSES:
            for ending in (".", ". Next", ".)", ".,", ".;", ".\"", ".'", ".]"):
                with self.subTest(f"{ip}{ending}"):
                    self.assertEqual(self.codes_for(ip + ending), ["PRIVATE_IP"])

    def test_control_the_older_boundaries_still_hold(self):
        for ip in self.ADDRESSES:
            for text, expected in ((ip, ["PRIVATE_IP"]), (ip + "x", []), ("v" + ip, []), (ip + ".4", []), (ip + "..2", []), (ip + "..", []), ("1." + ip, [])):
                with self.subTest(text):
                    self.assertEqual(self.codes_for(text), expected)

    def test_the_search_match_excludes_the_sentence_period_and_rejects_dot_word(self):
        detector = next(rx for code, rx in check_skills.PRIVACY if code == "PRIVATE_IP" and isinstance(rx, check_skills._PrivateIPv4))
        for ip in self.ADDRESSES:
            for ending in ("", ".", ". Next", ".)"):
                with self.subTest(f"{ip}{ending}"):
                    prefix = "see "
                    match = detector.search(prefix + ip + ending)
                    self.assertIsNotNone(match)
                    self.assertEqual(match.group(0), ip, "the matched text must not include a sentence period")
                    self.assertEqual(match.span(), (len(prefix), len(prefix) + len(ip)))
            self.assertIsNone(detector.search("see " + ip + ".word now"))
            self.assertIsNone(detector.search("see " + ip + ".9a now"))

    def test_the_cli_ignores_a_dot_word_atom_and_reports_a_sentence_period_without_echoing_the_address(self):
        ip = self.ADDRESSES[2]
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + ip + ".example\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 0, (out, err))
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide="# Guide\n\nhost " + ip + ". Next line\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE_IP", out)
        self.assertNotIn(ip[3:], out + err)


class RootDocumentLinkContainmentTest(TmpCase):
    """Correction 23 (synthetic): local Markdown links in README.md and INSTALLATION.md must resolve INSIDE the supplied root.
    External URLs stay external (never fetched); the existing Markdown-link contract is used, not a documentation parser."""

    DOCS = ("README.md", "INSTALLATION.md")

    def found(self, doc, link, outside_text="outside\n"):
        """Codes reported for `doc` when it carries one extra link. The repo root is base/repo; base/outside.md exists."""
        with tempfile.TemporaryDirectory(dir=self.tmp) as base:
            base = Path(base)
            root = base / "repo"
            root.mkdir()
            make_repo(root)
            (base / "outside.md").write_text(outside_text)
            target = (root / doc)
            target.write_text(target.read_text() + "\n" + link.replace("OUTSIDE_ABSOLUTE", str(base / "outside.md")) + "\n")
            return [code for path, code, _ in check_skills.check(root) if path == doc]

    def test_a_local_link_that_resolves_outside_the_root_is_a_finding_in_both_documents(self):
        for doc in self.DOCS:
            for label, link in {
                "parent directory": "[x](../outside.md)",
                "absolute path": "[x](OUTSIDE_ABSOLUTE)",
                "parent directory with an anchor": "[x](../outside.md#top)",
                "dot-dot through an inside folder": "[x](demo-skill/../../outside.md)",
            }.items():
                with self.subTest(f"{doc}: {label}"):
                    found = self.found(doc, link)
                    if label == "absolute path":  # the temporary directory itself sits under a private home path, which is a second, unrelated finding
                        self.assertIn("ESCAPES_ROOT", found)
                    else:
                        self.assertEqual(found, ["ESCAPES_ROOT"])

    def test_control_valid_missing_inside_external_and_anchor_links_keep_their_existing_results(self):
        for doc in self.DOCS:
            cases = {
                "valid inside link": ("[g](demo-skill/references/guide.md)", []),
                "inside link written with dot-dot": ("[g](demo-skill/../demo-skill/references/guide.md)", []),
                "missing link": ("[m](nope.md)", ["BROKEN_LINK"]),
                "external URL is not fetched or resolved": ("[e](https://example.org/x)", []),
                "anchor only": ("[a](#section)", []),
            }
            for label, (link, expected) in cases.items():
                with self.subTest(f"{doc}: {label}"):
                    self.assertEqual(self.found(doc, link), expected)

    def test_the_cli_exits_1_for_an_escaping_link_without_echoing_the_target_path(self):
        with tempfile.TemporaryDirectory(dir=self.tmp) as base:
            base = Path(base)
            root = base / "repo"
            root.mkdir()
            make_repo(root)
            (base / "outside.md").write_text("outside\n")
            (root / "README.md").write_text((root / "README.md").read_text() + "\n[x](../outside.md)\n")
            code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [root])
            self.assertEqual(code, 1, (out, err))
            self.assertIn("ESCAPES_ROOT", out)
            self.assertNotIn("outside.md", out + err)


class UnicodeHomeComponentTest(TmpCase):
    """Correction 35 (synthetic): the standard POSIX and macOS home prefixes flag ANY complete nonempty user component, including accented,
    non-Latin, combining-leading and punctuation-led (for example hyphen-led) names, not only an ASCII-initial one. The prefix literal stays
    case-sensitive; the privileged-home and Windows rules are unchanged; empty and dot-only components, complete placeholders and prose stay
    clean; there is no account lookup. Every path is assembled at run time from synthetic pieces so this scanned source holds no home prefix."""

    POSIX = "/ho" + "me/"
    MAC = "/Us" + "ers/"
    PRIVILEGED = "/ro" + "ot"
    WINDOWS = "C:" + "\\Us" + "ers\\"
    COMPONENTS = {
        "accented Latin": "élise",
        "accent after an ASCII start": "zéno",
        "Cyrillic": "алиса",
        "CJK": "用户",
        "Arabic": "مستخدم",
        "combining-mark-leading": "́abc",
        "hyphen-led": "-svc",
        "hyphen-led numeric": "-1000",
        "ASCII control (letters)": "alice",
        "ASCII control (digits)": "1000",
        "ASCII control (hidden)": ".svc",
        "ASCII control (underscore-led)": "_service",
    }

    def codes_for(self, text):
        with tempfile.TemporaryDirectory(dir=self.tmp) as d:
            make_repo(d, guide=f"# Guide\n\nsee {text} here\n")
            return [c for _, c, _ in check_skills.check(d)]

    def test_every_nonempty_unicode_or_punctuation_led_component_is_flagged_under_both_prefixes(self):
        for prefix_label, prefix in (("POSIX home", self.POSIX), ("macOS users", self.MAC)):
            for label, component in self.COMPONENTS.items():
                with self.subTest(f"{prefix_label}: {label}"):
                    self.assertEqual(self.codes_for(f"{prefix}{component}/notes"), ["PRIVATE_PATH"])
                with self.subTest(f"{prefix_label}: {label} as the last component"):
                    self.assertEqual(self.codes_for(f"{prefix}{component}"), ["PRIVATE_PATH"])

    def test_control_empty_dot_only_placeholder_and_prose_components_stay_clean(self):
        cases = {
            "angle-bracket placeholder": f"{self.POSIX}<user>/x",
            "environment-variable placeholder": f"{self.POSIX}$USER/x",
            "brace placeholder": f"{self.MAC}{{user}}/x",
            "angle-bracket placeholder under macOS": f"{self.MAC}<user>/x",
            "empty component": f"{self.POSIX}/x and {self.MAC}/y",
            "bare directory with no user": f"the {self.POSIX} directory and the {self.MAC} directory",
            "single dot component": f"{self.POSIX}./x",
            "double dot component": f"{self.MAC}../x",
            "dot-only component at the end": f"{self.POSIX}..",
            "ellipsis component": f"{self.POSIX}.../x",
            "prefix at the end of the text": f"under {self.POSIX}",
            "tilde": "~/notes",
            "clean prose": "nothing private here, café – ñ and 用户",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), [])

    def test_control_the_prefix_literal_stays_case_sensitive(self):
        for label, text in {
            "upper-case POSIX prefix": f"{self.POSIX.upper()}alice/x",
            "lower-case macOS prefix": f"{self.MAC.lower()}alice/x",
            "Unicode component under a wrong-case prefix": f"{self.MAC.upper()}élise/x",
        }.items():
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), [])

    def test_control_the_privileged_home_and_windows_rules_are_unchanged(self):
        for label, text, expected in (
            ("privileged home", f"{self.PRIVILEGED}/.ssh", ["PRIVATE_PATH"]),
            ("a longer name that merely starts like it", f"{self.PRIVILEGED}ed/path", []),
            ("windows letter component", f"{self.WINDOWS}alice\\x", ["PRIVATE_PATH"]),
            ("windows prefix with a Unicode component", f"{self.WINDOWS}élise\\x", ["PRIVATE_PATH"]),
            ("windows environment variable", "%USERPROFILE%\\Documents", []),
        ):
            with self.subTest(label):
                self.assertEqual(self.codes_for(text), expected)

    def test_the_real_cli_redacts_a_unicode_and_a_hyphen_led_component(self):
        for label, component in (("accented", "élise"), ("hyphen-led", "-svcuser"), ("combining-leading", "́zed")):
            with self.subTest(label):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d, guide=f"# Guide\n\nsee {self.POSIX}{component}/notes\n")
                    code, out, err = run_script(ROOT / "scripts" / "check_skills.py", [d])
                self.assertEqual(code, 1, (out, err))
                self.assertIn("PRIVATE_PATH", out)
                self.assertNotIn(component.lstrip("́-"), out + err, "the component must not be echoed")

    def test_the_pattern_source_and_these_tests_do_not_match_themselves_and_there_are_no_exemptions(self):
        rx = next(rx for code, rx in check_skills.PRIVACY if code == "PRIVATE_PATH")
        for path in (ROOT / "scripts" / "check_skills.py", ROOT / "tests" / "test_checker.py"):
            self.assertIsNone(rx.search(path.read_text(encoding="utf8")), f"{path.name} would flag itself")
        self.assertEqual(check_skills.check(ROOT), [], "the real tree stays clean (no suffix, source or fragment exemption)")


class LocalMarkdownQueryTest(TmpCase):
    """Link query/fragment metadata is not a filename; existing non-link extraction stays unchanged."""

    def test_package_link_queries_resolve_the_existing_path(self):
        for suffix in ("?view=print", "?view=print#section", "?"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory(dir=self.tmp) as d:
                skill = GOOD_SKILL.replace("[guide](references/guide.md)", f"[guide](references/guide.md{suffix})")
                self.assertEqual(check_skills.check(make_repo(d, skill=skill)), [])

    def test_root_document_queries_resolve_the_existing_path(self):
        for doc in ("README.md", "INSTALLATION.md"):
            with self.subTest(doc=doc), tempfile.TemporaryDirectory(dir=self.tmp) as d:
                root = make_repo(d)
                (root / doc).write_text("demo-skill\n[guide](demo-skill/references/guide.md?view=print#section)\n")
                self.assertEqual(check_skills.check(root), [])

    def test_query_only_links_and_external_links_are_not_file_targets(self):
        text = "[current](?view=print#section) [anchor](#section) [external](https://example.org/guide.md?view=print)"
        self.assertEqual(list(check_skills._refs(text, self.tmp, self.tmp)), [])

    def test_backtick_path_tokens_and_encoded_characters_stay_literal(self):
        refs = list(check_skills._refs("`references/guide.md?literal=1` [link](references/a%3Fb.md?view=print)", self.tmp, self.tmp))
        self.assertIn(("references/guide.md", "path"), refs, "preserve the existing extension-bounded backtick extraction")
        self.assertIn(("references/a%3Fb.md", "link"), refs)


class RootEntryAndFrontmatterBoundaryTest(TmpCase):
    """Correction 21 (synthetic): public CLI root ordering, undecodable root documents and the ASCII-only structural
    boundary of the frontmatter subset. Values keep their Unicode; only structure is ASCII."""

    CHECKER = ROOT / "scripts" / "check_skills.py"
    NBSP = " "

    def test_the_cli_reports_a_broken_or_non_directory_root_symlink_as_a_finding_without_reading_the_target(self):
        regular = self.tmp / "regular-file-target"
        regular.write_text("never read\n")
        for label, target, directory in (("broken", self.tmp / "nowhere-target", True), ("to a regular file", regular, False)):
            with self.subTest(label):
                link = self.tmp / f"root-{label.replace(' ', '-')}"
                make_symlink(link, target, directory=directory)
                code, out, err = run_script(self.CHECKER, [link])
                self.assertEqual(code, 1, (out, err))
                self.assertIn("UNSUPPORTED_SYMLINK", out)
                self.assertNotIn(target.name, out + err, "the target must not be echoed")

    def test_control_an_ordinary_missing_root_is_still_an_invalid_root(self):
        code, out, err = run_script(self.CHECKER, [self.tmp / "absent"])
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)

    def test_invalid_utf8_root_documents_are_unscanned_findings_not_crashes(self):
        for doc in ("README.md", "INSTALLATION.md"):
            with self.subTest(doc):
                with tempfile.TemporaryDirectory(dir=self.tmp) as d:
                    make_repo(d)
                    (Path(d) / doc).write_bytes(b"demo-skill \xff\xfe is not utf-8\n")
                    try:
                        found = check_skills.check(d)
                    except UnicodeDecodeError:
                        self.fail(f"{doc}: an undecodable root document crashed the checker instead of producing a finding")
                    mine = [(path, code) for path, code, _ in found if path == doc]
                    self.assertEqual(mine, [(doc, "UNSCANNED_BINARY")], found)
                    code, out, err = run_script(self.CHECKER, [d])
                    self.assertEqual(code, 1, (out, err))
                    self.assertIn("UNSCANNED_BINARY", out)
                    self.assertNotIn("Traceback", err)

    def test_control_valid_non_ascii_utf8_root_documents_are_still_read_and_scanned(self):
        make_repo(self.tmp, readme="demo-skill — café\n")
        self.assertEqual(check_skills.check(self.tmp), [])

    def test_a_unicode_padded_delimiter_or_a_unicode_only_blank_or_comment_line_is_not_frontmatter_structure(self):
        n = self.NBSP
        cases = {
            "opening delimiter padded with NBSP": f"{n}---\nname: x\n---\n",
            "closing delimiter padded with NBSP": f"---\nname: x\n{n}---\nbody\n",
            "NBSP-only line inside": f"---\nname: x\n{n}\ndescription: plain text\n---\n",
            "ideographic-space-only line inside": "---\nname: x\n　\ndescription: plain text\n---\n",
            "comment padded with NBSP": f"---\nname: x\n{n}# note\n---\n",
        }
        for label, text in cases.items():
            with self.subTest(label):
                data, err = check_skills.parse_frontmatter(text)
                self.assertIsNone(data, f"{label} was accepted as structure")
                self.assertIsNotNone(err)

    def test_through_the_checker_a_unicode_padded_opening_delimiter_is_a_frontmatter_finding(self):
        make_repo(self.tmp, skill=self.NBSP + GOOD_SKILL)
        self.assertIn("FRONTMATTER", codes(check_skills.check(self.tmp)))

    def test_control_ascii_separation_crlf_and_unicode_values_still_parse(self):
        text = '---  \t\r\nname: demo\r\n   \t\r\n  # an ASCII comment\r\ndescription: "café – ñ x y"\r\n---\t \r\nbody\r\n'
        data, err = check_skills.parse_frontmatter(text)
        self.assertIsNone(err)
        self.assertEqual(data, {"name": "demo", "description": "café – ñ x y"})

