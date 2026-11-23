"""Offline tests for the operator-pages templates (standard library; one optional Node.js run).

Static checks read the two HTML templates and their example data. The render tests run each template's own
script under Node.js against a tiny DOM stand-in, so they are skipped when `node` is not installed. They show
that the scripts draw the documented data and refuse unsafe input; they do not show how any client or phone
renders the page or whether a client lets the page copy to the clipboard.
"""
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

from test_skill_packages import ROOT, TmpCase

SKILL = ROOT / "operator-pages"
TEMPLATES = SKILL / "templates"
PAGES = {"decision": TEMPLATES / "decision.html", "status": TEMPLATES / "status.html"}
EXAMPLES = {name: TEMPLATES / f"{name}.example.json" for name in PAGES}
PLACEHOLDER = '{"template":"REPLACE_ME"}'


class _Scan(HTMLParser):
    """Collects what the page contract talks about: the title, meta tags and script blocks."""

    def __init__(self):
        super().__init__()
        self.title, self.metas, self.scripts, self.links, self._in = "", [], [], [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag in ("title", "script"):
            self._in = (tag, a, [])

    def handle_data(self, data):
        if self._in:
            self._in[2].append(data)

    def handle_endtag(self, tag):
        if self._in and self._in[0] == tag:
            text = "".join(self._in[2])
            if tag == "title":
                self.title = text
            else:
                self.scripts.append((self._in[1], text))
            self._in = None


def scan(path):
    parser = _Scan()
    parser.feed(path.read_text(encoding="utf8"))
    return parser


def css_vars(text, selector):
    block = re.search(selector + r"\s*\{([^}]*)\}", text)
    assert block, selector
    return set(re.findall(r"(--[a-z-]+)\s*:", block.group(1)))


def keys_of(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from keys_of(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys_of(v)


class TemplateContractTest(unittest.TestCase):
    def test_each_template_follows_the_artifact_page_contract(self):
        for name, path in PAGES.items():
            with self.subTest(name):
                text = path.read_text(encoding="utf8")
                page = scan(path)
                self.assertTrue(2 <= len(page.title.split()) <= 4, page.title)
                self.assertNotIn(":", page.title)
                self.assertIn('lang="pl"', text)
                self.assertTrue(any(m.get("name") == "viewport" and "width=device-width" in m.get("content", "") for m in page.metas))
                # colour tokens on :root, redefined for dark mode under both guarded selectors, with the same token set
                light = css_vars(text, r":root")
                self.assertTrue(light)
                self.assertEqual(css_vars(text, r':root:not\(\[data-theme="light"\]\)'), light)
                self.assertEqual(css_vars(text, r':root\[data-theme="dark"\]'), light)
                self.assertIn("@media (prefers-color-scheme: dark)", text)
                self.assertRegex(text, r"body\s*\{[^}]*background:")
                # phone width: a 16px gutter and long words that wrap instead of widening the page
                self.assertRegex(text, r"main\s*\{[^}]*padding:\s*16px 16px")
                self.assertIn("overflow-wrap: anywhere", text)

    def test_each_template_is_self_contained(self):
        for name, path in PAGES.items():
            with self.subTest(name):
                text = path.read_text(encoding="utf8")
                page = scan(path)
                self.assertEqual(page.links, [])
                self.assertFalse(re.search(r"https?://", text), "no URL may appear in a template")
                self.assertNotIn("@import", text)
                self.assertFalse([a for a, _ in page.scripts if "src" in a], "no external script")
                self.assertEqual(len(re.findall(r"<script\b", text)), 2)

    def test_each_template_holds_one_json_data_block_with_the_placeholder(self):
        for name, path in PAGES.items():
            with self.subTest(name):
                blocks = [(a, t) for a, t in scan(path).scripts if a.get("type") == "application/json"]
                self.assertEqual(len(blocks), 1)
                attrs, body = blocks[0]
                self.assertEqual(attrs.get("id"), "data")
                self.assertEqual(body, PLACEHOLDER)

    def test_scripts_insert_data_as_text_and_links_only_over_https(self):
        for name, path in PAGES.items():
            with self.subTest(name):
                code = [t for a, t in scan(path).scripts if a.get("type") != "application/json"][0]
                for banned in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function", "setTimeout(", "fetch(", "XMLHttpRequest", "localStorage"):
                    self.assertNotIn(banned, code, banned)
                self.assertEqual(len(re.findall(r"\.href\s*=", code)), 1, "one place may set a link target")
                self.assertRegex(code, r"/\^https:\\/\\//i\.test\(url\)")
                self.assertIn("textContent", code)


class ExamplesAndDocsTest(unittest.TestCase):
    def test_examples_are_valid_and_every_key_is_drawn_and_documented(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf8")
        for name, path in EXAMPLES.items():
            with self.subTest(name):
                data = json.loads(path.read_text(encoding="utf8"))
                code = [t for a, t in scan(PAGES[name]).scripts if a.get("type") != "application/json"][0]
                for key in sorted(set(keys_of(data))):
                    self.assertRegex(code, rf"\b{key}\b", f"{key} is not used by the {name} script")
                    self.assertRegex(skill_md, rf"\b{key}\b", f"{key} is not documented in SKILL.md")

    def test_example_links_are_https(self):
        for name, path in EXAMPLES.items():
            with self.subTest(name):
                for url in re.findall(r'"(?:url)"\s*:\s*"([^"]*)"', path.read_text(encoding="utf8")):
                    self.assertTrue(url.startswith("https://"), url)

    def test_skill_documents_every_enumerated_value_the_scripts_know(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf8")
        for value in ("easy", "costly", "none", "done", "doing", "blocked", "waiting", "REPLACE_ME"):
            self.assertIn(value, skill_md, value)

    def test_skill_tells_writers_to_escape_a_less_than_sign_with_the_real_escape(self):
        # The escape is built from a character code so no tool that decodes escapes can turn it into a bare "<".
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf8")
        self.assertIn("write every `<` as `" + chr(92) + "u003c`", skill_md)

    def test_example_decision_one_uses_the_exact_option_names_as_choices(self):
        data = json.loads(EXAMPLES["decision"].read_text(encoding="utf8"))
        self.assertEqual(data["decisions"][0]["choices"], [o["name"] for o in data["options"]])
        for decision in data["decisions"]:
            self.assertIn(decision["advice"], decision["choices"])

    def test_skill_is_listed_in_the_root_documents(self):
        for doc in ("README.md", "INSTALLATION.md"):
            self.assertIn("operator-pages", (ROOT / doc).read_text(encoding="utf8"), doc)


HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const [pagePath, dataPath] = process.argv.slice(2);
class El {
  constructor(tag) { this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {}; this.className = ""; this.value = ""; this.checked = false; }
  appendChild(c) { this.children.push(c); return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  get textContent() { return this.children.map(c => c.textContent).join(""); }
  set textContent(v) { this.children = v === "" ? [] : [{ textContent: String(v) }]; }
  set innerHTML(v) { throw new Error("innerHTML is not allowed"); }
  focus() {} select() {} setSelectionRange() {}
  fire(t) { (this.listeners[t] || []).forEach(f => f()); }
  walk(fn) { fn(this); this.children.forEach(c => c.walk && c.walk(fn)); }
}
const app = new El("main"), dataEl = new El("script");
dataEl.textContent = fs.readFileSync(dataPath, "utf8");
let copied = null;
const document = { getElementById: id => (id === "app" ? app : dataEl), createElement: t => new El(t), execCommand: () => false };
const navigator = { clipboard: { writeText: t => { copied = t; return Promise.resolve(); } } };
vm.runInNewContext(fs.readFileSync(pagePath, "utf8"), { document, navigator });
const found = { a: [], radio: [], textarea: [], button: [] };
app.walk(n => {
  if (n.tag === "a") found.a.push(n.href);
  if (n.tag === "input" && n.type === "radio") found.radio.push(n);
  if (n.tag === "textarea") found.textarea.push(n);
  if (n.tag === "button") found.button.push(n);
});
const box = found.textarea[0];
const out = { text: app.textContent, links: found.a, radios: found.radio.length, sentence: box ? box.value : null };
if (found.radio.length > 1) {
  // choose the first option of the first decision, as a tap on it would
  found.radio[0].checked = true; found.radio[0].fire("change");
  out.afterChange = box.value;
}
if (found.button[0]) found.button[0].fire("click");
setImmediate(() => { out.copied = copied; console.log(JSON.stringify(out)); });
"""


@unittest.skipUnless(shutil.which("node"), "Node.js is not installed: the render tests were not run")
class TemplateRenderTest(TmpCase):
    def render(self, name, data):
        code = [t for a, t in scan(PAGES[name]).scripts if a.get("type") != "application/json"][0]
        (self.tmp / "page.js").write_text(code, encoding="utf8")
        (self.tmp / "harness.cjs").write_text(HARNESS, encoding="utf8")
        payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        (self.tmp / "data.json").write_text(payload, encoding="utf8")
        done = subprocess.run(
            [shutil.which("node"), str(self.tmp / "harness.cjs"), str(self.tmp / "page.js"), str(self.tmp / "data.json")],
            capture_output=True, text=True, encoding="utf8", cwd=self.tmp, timeout=60,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def example(self, name):
        return json.loads(EXAMPLES[name].read_text(encoding="utf8"))

    def test_placeholder_and_broken_json_show_a_message_instead_of_a_page(self):
        for name in PAGES:
            with self.subTest(name):
                self.assertIn("Szablon bez danych", self.render(name, PLACEHOLDER)["text"])
                self.assertIn("Błędne dane JSON", self.render(name, "{not json")["text"])

    def test_decision_page_draws_every_section_and_returns_the_choice_as_a_sentence(self):
        data = self.example("decision")
        out = self.render("decision", data)
        for needle in ("Pytanie", "Rekomendacja", "Opcje", "Decyzje do podjęcia", "Co się stanie po wyborze", "Ryzyka i niewiadome", "Jak odpowiedzieć", "Szczegóły", "Kopiuj", "Twój krok", "Polecana", "Odwracalność", "Łatwo", "Kosztownie", "Nie da się"):
            self.assertIn(needle, out["text"], needle)
        for opt in data["options"]:
            self.assertIn(opt["name"], out["text"])
        for crit in data["criteria"]:
            self.assertIn(crit, out["text"])
        self.assertEqual(out["sentence"], "Kopie zapasowe: 1 Dysk plus chmura, 2 tak, 3 tak")  # the advice is pre-selected
        self.assertEqual(out["afterChange"], "Kopie zapasowe: 1 Tylko drugi dysk, 2 tak, 3 tak")
        self.assertEqual(out["copied"], out["afterChange"], "the button copies what the box shows")
        self.assertEqual(out["links"], ["https://example.org/propozycja"])

    def test_decision_page_without_a_choices_token_still_returns_the_choices(self):
        data = self.example("decision")
        data["reply"] = {"template": "Moja odpowiedź:"}
        self.assertEqual(self.render("decision", data)["sentence"], "Moja odpowiedź: 1 Dysk plus chmura, 2 tak, 3 tak")

    def test_advice_that_matches_no_choice_is_flagged_and_never_replaced_by_another_choice(self):
        data = self.example("decision")
        data["decisions"][1]["advice"] = "Tak"  # choices are "tak" and "nie"
        out = self.render("decision", data)
        self.assertIn("Rada nie pasuje do żadnej opcji", out["text"])
        self.assertEqual(out["sentence"], "Kopie zapasowe: 1 Dysk plus chmura, 2 (wybierz), 3 tak")

    def test_null_entries_in_the_arrays_are_skipped_instead_of_stopping_the_page(self):
        data = self.example("decision")
        for key in ("options", "decisions", "steps", "details"):
            data[key].insert(1, None)
        out = self.render("decision", data)
        self.assertIn("Jak odpowiedzieć", out["text"])
        self.assertIn("Szczegóły", out["text"])
        self.assertEqual(out["sentence"], "Kopie zapasowe: 1 Dysk plus chmura, 2 tak, 3 tak")

    def test_unsafe_values_stay_text_and_only_https_links_are_drawn(self):
        hostile = "<img src=x onerror=alert(1)>"
        decision = self.example("decision")
        decision["title"] = hostile
        decision["link"] = {"label": "x", "url": "javascript:alert(1)"}
        decision["options"][0]["name"] = hostile
        out = self.render("decision", decision)
        self.assertIn(hostile, out["text"])
        self.assertEqual(out["links"], [])
        status = self.example("status")
        status["items"][0]["name"] = hostile
        status["items"][0]["url"] = "http://example.org/plain"
        status["items"][1]["url"] = "javascript:alert(1)"
        out = self.render("status", status)
        self.assertIn(hostile, out["text"])
        self.assertEqual(out["links"], [])

    def test_status_page_puts_waiting_first_and_finished_last(self):
        data = self.example("status")
        out = self.render("status", data)
        text = out["text"]
        self.assertLess(text.index("Czeka na Ciebie"), text.index("Pozycje w toku"))
        self.assertLess(text.index("Pozycje w toku"), text.index("Zakończone (1)"))
        for needle in ("Ostatnia aktualizacja: 2026-11-24 09:30", "Gotowe", "W toku", "Zablokowane", "Zdecyduj, czy wyłączyć stary serwer"):
            self.assertIn(needle, text, needle)
        self.assertEqual(out["links"], ["https://example.org/serwer-plikow", "https://example.org/serwer-plikow"])

    def test_status_page_with_no_waiting_items_says_so_and_caps_the_list_at_three(self):
        data = self.example("status")
        for item in data["items"]:
            item["state"] = "doing"
        self.assertIn("Nic na Ciebie nie czeka.", self.render("status", data)["text"])
        data["items"] = [{"name": f"Pozycja {i}", "state": "waiting", "next": "Zrób to.", "who": "Ty", "changed": "2026-11-24"} for i in range(5)]
        self.assertIn("Jeszcze 2 w tabeli poniżej.", self.render("status", data)["text"])


if __name__ == "__main__":
    unittest.main()
