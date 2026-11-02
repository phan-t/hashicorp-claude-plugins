#!/usr/bin/env python3
"""Tests for slop_check.py. Standard library only.

    python3 plugins/writing-style/tests/test_slop_check.py

Each pattern is tested on the prose it should flag and on prose that obeys the rule, so a
pattern that grows too broad fails here before it fails on a real document.
"""

import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "..", "skills", "writing-style", "assets", "slop_check.py")
sys.path.insert(0, os.path.dirname(CHECKER))

import slop_check  # noqa: E402


def categories(text):
    return [hit[3] for hit in slop_check.check(text, [])]


class PatternCase(unittest.TestCase):
    """Subclasses set CATEGORY, FLAG and PASS."""

    CATEGORY = None
    FLAG = ()
    PASS = ()

    def test_flags(self):
        for text in self.FLAG:
            with self.subTest(text=text):
                self.assertIn(self.CATEGORY, categories(text))

    def test_passes(self):
        for text in self.PASS:
            with self.subTest(text=text):
                self.assertNotIn(self.CATEGORY, categories(text))


class Underscore(PatternCase):
    CATEGORY = "vocabulary"
    FLAG = (
        "This underscores the need for a second cluster.",
        "The outage underscored how fragile it was.",
        "This was underscored by the soak test.",
        "Underscoring our point, the soak failed.",
    )
    PASS = (
        "Prometheus shows the names with underscores.",
        "Replace the underscore that separates words.",
        "Names use a leading underscore.",
        "Use an underscore character.",
        "Underscores are not allowed in hostnames.",
        "Replace underscores with hyphens.",
        "Prometheus converts dots to underscores.",
        "Names are underscore-separated.",
        "The metric names contain underscores.",
    )


class HedgeAdverb(PatternCase):
    CATEGORY = "hedge adverb"
    FLAG = (
        "Effectively none of the 100,000 cached certificates was re-issued.",
        "The two clusters are essentially identical.",
        "This is arguably the safer option.",
        "Virtually every request was served from cache.",
    )
    PASS = (
        "None of the 100,000 cached certificates was re-issued.",
        # A stated expectation with its cause is a finding, so "as expected" stays unflagged.
        "Latency rose as expected, because each voter adds a round trip.",
        "The policy takes effect on the next login.",
    )


class Strawman(PatternCase):
    CATEGORY = "strawman"
    FLAG = (
        "These results don't support the reasoning that more voters slow writes.",
        "Contrary to popular belief, five voters are no slower than three.",
        "It is a common misconception that Raft needs an odd number of nodes.",
    )
    PASS = (
        "The voter count made no measurable difference to write performance.",
        "The team supports the idea and has funded it.",
    )


class StockOpener(PatternCase):
    CATEGORY = "stock opener"
    FLAG = (
        "And it's getting harder. Contractors now use the same paths.",
        "Here's the thing: the keys never rotate.",
        "The reality is that most rules are per subnet.",
    )
    PASS = (
        "Contractors, automation and AI agents now use the same paths.",
        "Rotation is getting harder to schedule as the estate grows.",
    )


class LineStart(PatternCase):
    """Patterns anchored to a sentence start also fire at the start of a line."""

    CATEGORY = "echo"
    FLAG = (
        "# Results\nIn short, it worked.",
        "Region\nOverall, the soak held.",
    )
    PASS = ("# Results\nThe soak held for 72 hours.",)


class NonBreakingSpace(PatternCase):
    CATEGORY = "vocabulary"
    FLAG = ("We dive\u00a0into the logs.",)
    PASS = ("We read the logs.",)


class CurlyApostrophe(PatternCase):
    CATEGORY = "signposting"
    FLAG = ("It’s worth noting that the soak ran for 72 hours.",)
    PASS = ("The soak ran for 72 hours.",)


RESULTS = """| Run | Success | p99 |
|---|---|---|
| Soak | 100% | 41.2 ms |
| Burst 1 | 100% | 88.0 ms |
| Burst 2 | 99.8% | 120.5 ms |
"""


class TableEcho(PatternCase):
    CATEGORY = "table echo"
    FLAG = (
        RESULTS + "\nAgainst the agreed criteria, success was 100% in the soak and both bursts.",
        RESULTS + "\nSuccess was 100% in the soak and 99.8% in burst 2.",
        RESULTS + "\n*Table 2. Results by run.*\n\nComparing the runs shows how much the soak held.",
        "![Latency by layer](latency.png)\n\nThis chart shows the cache absorbing the load.",
    )
    PASS = (
        # One shared number, and it explains rather than restates.
        RESULTS + "\nBurst 2 reached 99.8% because one node restarted during the run.",
        RESULTS + "\n## Next steps\n\nThese results set the baseline for the next soak.",
        "This shows the names Prometheus exports.",
    )


class UnsourcedHedge(PatternCase):
    CATEGORY = "unsourced hedge"
    FLAG = (
        "Hashes sensitive values with HMAC-SHA-256, which is expected to stay secure.",
        "The cipher is expected to be secure until 2035.",
        "Both keys are expected to remain valid.",
    )
    PASS = (
        "NIST expects HMAC-SHA-256 to stay secure.",
        "Latency is expected to remain under 10 ms at that load.",
        "Output is expected to be JSON.",
        "The migration is expected to be complete by March.",
    )


class UnmeasuredSpeed(PatternCase):
    CATEGORY = "unmeasured speed"
    FLAG = (
        "Lets keys move to a new algorithm quickly if the timeline moves earlier.",
        "The cluster rapidly recovers.",
    )
    PASS = (
        "The test ran quickly, in 40 ms.",
        "Rotation finishes within 40 ms.",
        "The market is rapidly evolving.",  # reported as slop vocabulary instead
    )


class VagueStatus(PatternCase):
    CATEGORY = "vague status"
    FLAG = (
        "Planned for an upcoming release.",
        "Planned for a future release.",
        "Currently targeted for version 2.3, planned for March 2027.",
        "This lands in a future version.",
    )
    PASS = (
        "Planned for Vault 2.3, due in March 2027.",
        "No release is assigned yet.",
        "Requires Python 3.10 or a later version.",
        "Upgrade to a later release before enabling it.",
        "Future versions may drop the flag.",
        "The flag is deprecated and will be removed in a future release.",
    )


class OwnerlessCommitment(PatternCase):
    CATEGORY = "ownerless commitment"
    FLAG = (
        "The remaining items can be raised with product management as requirements.",
        "The gap will be escalated with support.",
    )
    PASS = (
        "Tony will raise the remaining items with product management.",
        "Logs can be reviewed with grep.",
        "The call can be followed up with an email.",
    )


class VagueReferent(PatternCase):
    CATEGORY = "vague referent"
    FLAG = (
        "The customer can check the mechanism it uses against this.",
        "Check it against this. Then rotate.",
        "| Key | Check against this. |",
    )
    PASS = (
        "The customer can check the mechanism against FIPS 203.",
        "I agree with this.",
        "Check this against the standard.",
    )


class UnnamedSet(PatternCase):
    CATEGORY = "unnamed set"
    FLAG = (
        "It aligns with the main post-quantum cryptography standards.",
        "It aligns with the main standards.",
    )
    PASS = (
        "The main options are Raft and Consul.",
        "The main standards: FIPS 203, FIPS 204, and FIPS 205.",
        "It aligns with FIPS 203 and FIPS 204.",
    )


class PersonifiedLabel(PatternCase):
    CATEGORY = "personified label"
    FLAG = (
        "| Measure | What it asks | Vault 2.2.0 |",
        "## What it asks",
        "What they want",
    )
    PASS = (
        "| Measure | Recommendation | Vault 2.2.0 |",
        "## What it does",
        "## What this covers",
        "The advisory lists what it asks of operators.",
    )


class Emoji(PatternCase):
    CATEGORY = "emoji"
    FLAG = (
        "Shipped 🚀",
        "- [ ] Ship the note 🚀 📅 2026-11-06",
        "Done ✅ 2026-10-27",  # not a checkbox line
    )
    PASS = (
        "- [ ] Ship the note 📅 2026-11-06",
        "- [x] Draft the note ✅ 2026-10-27",
        "- [ ] Follow up 🔁 every week 📅 2026-11-13",
        "- [ ] Rotate keys ⏫ ⏳ 2026-11-10",
    )


class TitleCase(unittest.TestCase):
    def hits(self, text, titles=frozenset()):
        return [h for h in slop_check.check(text, [], titles=titles) if h[3] == "title case"]

    def test_flags_a_title_case_heading(self):
        self.assertEqual(len(self.hits("## Test Results Summary\n\nSee Test Results Summary.")), 1)

    def test_skips_a_listed_title(self):
        self.assertEqual(self.hits("# The Staff Engineer's Path", {"The Staff Engineer's Path"}), [])

    def test_skips_an_italic_title(self):
        self.assertEqual(self.hits("# *The Staff Engineer's Path*"), [])

    def test_titles_block_is_read(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("```titles\n# a comment\nThe Staff Engineer's Path\n```\n")
        self.addCleanup(os.unlink, f.name)
        self.assertEqual(slop_check.load_profile_titles(f.name), {"The Staff Engineer's Path"})


SPLIT = "| Measure | Vault | Vault capability |\n|---|---|---|\n| A | Yes | Transit |\n"
MERGED = "| Measure | Vault 2.2.0 |\n|---|---|\n| A | Transit |\n"


class HeaderDrift(PatternCase):
    CATEGORY = "header drift"
    FLAG = (SPLIT + "\n" + SPLIT + "\n" + MERGED,)
    PASS = (
        SPLIT + "\n" + SPLIT,
        "| Component | Before |\n|---|---|\n| A | 1 |\n\n| Component | After |\n|---|---|\n| A | 2 |\n",
        "| Region | 2025 cost |\n|---|---|\n| A | 1 |\n\n| Region | 2026 cost |\n|---|---|\n| A | 2 |\n",
        # A word shared with a different column.
        "| Product | Entitled | Used |\n|---|---|---|\n| A | 1 | 1 |\n\n"
        "| Product | Used | Usage / entitled |\n|---|---|---|\n| A | 1 | 1 |\n",
    )

    def test_reports_the_later_table_once(self):
        hits = [h for h in slop_check.check(SPLIT + "\n" + SPLIT + "\n" + MERGED, []) if h[3] == "header drift"]
        self.assertEqual([(h[0], h[4]) for h in hits], [(9, "Vault 2.2.0")])

    def test_docx_header_row(self):
        body = table(["Measure", "Vault"], ["A", "Yes"]) + table(["Measure", "Vault capability"], ["A", "Yes"])
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "drift.docx")
            write_docx(path, body)
            text, _, kinds = slop_check.read_docx(path)
        self.assertEqual([k for k, _ in kinds], ["header", "header", "cell", "cell"] * 2)
        self.assertIn("header drift", [h[3] for h in slop_check.check(text, [], kinds)])


class VersionNaming(PatternCase):
    CATEGORY = "version naming"
    FLAG = (
        "Use Vault Enterprise 2.2.0. Vault 2.2.0 adds it. Deploy a Vault 2.2 Enterprise cluster.",
        "Vault 2.2.0 adds ML-KEM. Upgrade to Vault 2.2 first.",
    )
    PASS = (
        "Vault 2.2.0 adds ML-KEM. Vault 2.2 or later supports it.",
        "Vault 2.2.0 fixed it, and Vault 2.2.1 reverted it. Vault 2.2 is current.",
        "Vault 2.2.0 adds ML-KEM. Vault 2.2.0 is current.",
        "See Table 2.1 and Table 2.1.3.",
    )

    def test_reports_each_variant_after_the_first(self):
        text = "Use Vault Enterprise 2.2.0. Vault 2.2.0 adds it. Deploy a Vault 2.2 Enterprise cluster."
        hits = [h[4] for h in slop_check.check(text, []) if h[3] == "version naming"]
        self.assertEqual(hits, ["Vault 2.2.0", "Vault 2.2 Enterprise"])


CAVEAT = "The results show relative capacity rather than what the hardware will sustain."


def sections(n, sentence):
    return "\n".join(f"## Section {i}\n\nRun {i} used {i * 10} clients. {sentence}\n" for i in range(n))


class Repetition(PatternCase):
    CATEGORY = "repetition"
    FLAG = (sections(4, CAVEAT), sections(7, CAVEAT))
    PASS = (
        sections(3, CAVEAT),
        # Table rows and headings repeat by design.
        "| Impact | High effort and low risk |\n" * 5,
        "\n".join(f"## Capacity of the primary cluster {i}\n\nText {i}.\n" for i in range(5)),
        # Stopwords only, and a phrase that would have to cross a full stop.
        sections(5, "It was one of the most of the runs."),
        sections(5, "Run it again. Capacity held steady."),
    )

    def test_reports_the_whole_phrase(self):
        hits = [h for h in slop_check.check(sections(7, CAVEAT), []) if h[3] == "repetition"]
        self.assertEqual(len(hits), 7)
        self.assertEqual({h[4] for h in hits}, {CAVEAT.lower().rstrip(".")})


# A minimal WordprocessingML package, built by hand so the tests need no python-docx.
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/></Types>'
)


def run(text, rpr=""):
    return f'<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'


def para(*runs, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{''.join(runs)}</w:p>"


def write_docx(path, body, footnotes=None):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("word/document.xml", f"<w:document {NS}><w:body>{body}</w:body></w:document>")
        if footnotes is not None:
            z.writestr("word/footnotes.xml", f"<w:footnotes {NS}>{footnotes}</w:footnotes>")


FIXTURE_BODY = "".join([
    para(run("Test Results Summary Section"), style="Heading1"),                  # ¶1, title case
    para(run("We simply ran the soak.")),                                         # ¶2
    para(),                                                                       # empty, not counted
    para(run("The cache "),
         '<w:del w:id="1" w:author="r"><w:r><w:delText>leverages</w:delText></w:r></w:del>',
         '<w:ins w:id="2" w:author="r">' + run("uses") + "</w:ins>",
         run(" the token.")),                                                     # ¶3, deletion ignored
    para(run("Set "), run("leverage", '<w:rPr><w:rStyle w:val="Code"/></w:rPr>'),
         run(" and "), run("delve", '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr>'),
         run(" first, simply.")),                                                 # ¶4, both code runs masked
    "<w:tbl><w:tr><w:tc>" + para(run("Region")) + "</w:tc><w:tc>"
    + para(run("It is a robust design.")) + "</w:tc></w:tr></w:tbl>",             # ¶5 and ¶6
    para(run("Rates held"), '<w:r><w:footnoteReference w:id="7"/></w:r>', run(".")),  # ¶7
    para(run("vault leverage --delve"), style="HTMLPreformatted"),                # ¶8, code paragraph
    para(run("Test Results Summary Section\t1"), style="TOC1"),                   # ¶9, TOC line
    para(run("We chose Raft rather than Consul.")),                               # ¶10
])
FIXTURE_FOOTNOTES = (
    '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
    '<w:footnote w:id="7">' + para(run("Measured over a truly long window.")) + "</w:footnote>"
)


def table(*rows):
    cells = "".join("<w:tr>" + "".join(f"<w:tc>{para(run(c))}</w:tc>" for c in row) + "</w:tr>" for row in rows)
    return f"<w:tbl>{cells}</w:tbl>"


SEED = os.path.join(HERE, "..", "skills", "writing-style", "references", "seed-profile.md")


class ProfilePatterns(unittest.TestCase):
    def load(self, block):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("```patterns\n" + block + "\n```\n")
        self.addCleanup(os.unlink, f.name)
        return slop_check.load_profile_patterns(f.name)

    def test_lines_default_to_the_profile_level(self):
        [(_, level, hint)] = self.load(r"\bcolor\b => colour (R7)")
        self.assertEqual((level, hint), ("profile", "colour (R7)"))

    def test_anchors_match_each_line(self):
        [(rx, _, _)] = self.load(r"^Note: => cut")
        self.assertTrue(rx.search("First line.\nNote: second line."))

    def test_review_prefix_sets_the_level(self):
        [(rx, level, _)] = self.load(r"review: \bfoo\b => bar")
        self.assertEqual(level, "review")
        self.assertTrue(rx.search("a foo here"))
        levels = [h[2] for h in slop_check.check("a foo here", [(rx, level, "bar")])]
        self.assertEqual(levels, ["review"])


class SerialComma(unittest.TestCase):
    """The seed profile's R4 pattern: a list of three or more missing its serial comma.

    It is a review pattern because a clause before a comma looks like a list item to a regex:
    "If it is offline, say so and inline the fonts" is flagged.
    """

    FLAG = (
        "It uses Inter, the signature glow gradient and HashiCorp's own layouts.",
        "Never set a font, colour, size or border.",
        "Write, edit and review prose.",
        "Asks carry an owner, a cost and a date.",
    )
    PASS = (
        "It uses Inter, the signature glow gradient, and HashiCorp's own layouts.",
        "Never set a font, colour, size, or border.",
        "Vault and Terraform share a module.",
        "Captions use Inter, which the template embeds.",
        "Before writing, whether or not it ships, check it.",
        "No layout map, so the slot map and the list are shared.",
        # An apposition introduces two items, so no serial comma is wanted.
        "The operational cost of Community edition, specifically state and multi-edit collaboration problems.",
        "Three products, including Vault and Boundary, share the module.",
        "Two editions, namely Community and Enterprise, differ here.",
        "Several tools, such as Vault and Consul, use Raft.",
    )

    def setUp(self):
        self.patterns = [p for p in slop_check.load_profile_patterns(SEED) if "(R4)" in p[2]]
        self.assertEqual(len(self.patterns), 1)

    def hits(self, text):
        return [h for h in slop_check.check(text, self.patterns) if h[3] == "profile"]

    def test_flags(self):
        for text in self.FLAG:
            with self.subTest(text=text):
                self.assertEqual([h[2] for h in self.hits(text)], ["review"])

    def test_passes(self):
        for text in self.PASS:
            with self.subTest(text=text):
                self.assertEqual(self.hits(text), [])


class DocxStructure(unittest.TestCase):
    def test_table_echo_after_a_caption(self):
        body = (para(run("Results"), style="Heading1")
                + table(["Run", "Success"], ["Soak", "100%"], ["Burst 2", "99.8%"])
                + para(run("Table 1. Results by run."), style="Caption")
                + para(run("Success was 100% in the soak and 99.8% in burst 2.")))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "echo.docx")
            write_docx(path, body)
            text, _, kinds = slop_check.read_docx(path)
            hits = [h for h in slop_check.check(text, [], kinds) if h[3] == "table echo"]
        self.assertEqual([(h[0], h[3]) for h in hits], [(9, "table echo")])
        self.assertEqual(kinds[1], ("header", 1))
        self.assertEqual(kinds[3], ("cell", 1))
        self.assertEqual(kinds[7], ("caption", None))

    def test_each_paragraph_is_its_own(self):
        # In Word, adjacent paragraphs never merge into one phrase.
        body = "".join(para(run("Capacity held relative")) + para(run("to the hardware.")) for _ in range(5))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "split.docx")
            write_docx(path, body)
            text, _, kinds = slop_check.read_docx(path)
            self.assertNotIn("repetition", [h[3] for h in slop_check.check(text, [], kinds)])


class Docx(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "report.docx")
        write_docx(self.path, FIXTURE_BODY, FIXTURE_FOOTNOTES)

    def tearDown(self):
        self.dir.cleanup()

    def output(self, *paths):
        proc = subprocess.run([sys.executable, CHECKER, "--no-profile", *paths],
                              capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr

    def test_paragraphs_and_cells_become_lines(self):
        text, locations, _ = slop_check.read_docx(self.path)
        lines = text.split("\n")
        self.assertEqual(lines[0], "# Test Results Summary Section")
        self.assertEqual(lines[4:6], ["Region", "It is a robust design."])
        self.assertEqual([label for label, _ in locations],
                         ["¶1", "¶2", "¶3", "¶4", "¶5", "¶6", "¶7", "¶10", "footnote 1"])

    def test_deleted_text_is_skipped(self):
        text, _, _ = slop_check.read_docx(self.path)
        self.assertIn("The cache uses the token.", text)
        self.assertNotIn("leverages", text)

    def test_hits_are_located_by_paragraph(self):
        code, out, _ = self.output(self.path)
        self.assertEqual(code, 0)  # review hits only
        self.assertIn('report.docx:¶1:1: review  [title case]', out)
        self.assertIn('report.docx:¶2:4: review  [condescension] "simply"', out)
        self.assertIn('report.docx:¶6:9: review  [vocabulary] "robust"', out)
        self.assertIn('report.docx:footnote 1:', out)
        self.assertIn('"truly"', out)

    def test_code_is_not_checked(self):
        _, out, _ = self.output(self.path)
        self.assertNotIn("leverage", out)
        self.assertNotIn("delve", out)

    def test_columns_hold_after_code_runs(self):
        _, out, _ = self.output(self.path)
        column = "Set leverage and delve first, simply.".index("simply") + 1
        self.assertIn(f'report.docx:¶4:{column}: review  [condescension] "simply"', out)

    def test_table_of_contents_is_not_checked(self):
        _, out, _ = self.output(self.path)
        self.assertEqual(out.count("[title case]"), 1)

    def test_summary_counts_rather_than(self):
        _, _, err = self.output(self.path)
        self.assertIn('"rather than" x1 in', err)

    def test_unreadable_file_exits_2(self):
        bad = os.path.join(self.dir.name, "notes.docx")
        with open(bad, "w") as f:
            f.write("plain text")
        code, _, err = self.output(bad, self.path)
        self.assertEqual(code, 2)
        self.assertIn("not a Word file", err)

    def test_binary_file_exits_2(self):
        bad = os.path.join(self.dir.name, "old.doc")
        with open(bad, "wb") as f:
            f.write(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\xff\xfe")
        code, _, err = self.output(bad)
        self.assertEqual(code, 2)
        self.assertIn("not UTF-8 text", err)


if __name__ == "__main__":
    unittest.main()
