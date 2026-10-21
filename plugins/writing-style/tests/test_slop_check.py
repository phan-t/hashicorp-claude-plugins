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
        self.assertEqual(kinds[1], ("cell", 1))
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
