#!/usr/bin/env python3
"""Tests for ibm_brief.py and the template build_template.py makes.

    python3 plugins/ibm-brief/tests/test_ibm_brief.py

Needs python-docx. Rendering is checked by hand through Word (see the skill's
references/design-system.md); these tests pin the structure that rendering
showed to matter, so a later change cannot quietly undo it.
"""

import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "skills", "ibm-brief-docx", "assets")
sys.path.insert(0, ASSETS)

from docx.oxml.ns import qn  # noqa: E402

from ibm_brief import Brief, text_width, wrap  # noqa: E402

TEMPLATE = os.path.join(ASSETS, "ibm-brief-template.docx")


def brief(**cover):
    b = Brief("Certificate lifecycle management", subtitle="Automate certificates end to end",
              date="November 2026")
    b.cover(highlights=["One", "Two", "Three"], **cover)
    return b


def body_children(b):
    return [el.tag.split("}")[1] for el in b.doc.element.body]


class Template(unittest.TestCase):
    def setUp(self):
        with zipfile.ZipFile(TEMPLATE) as z:
            self.names = set(z.namelist())
            self.styles = z.read("word/styles.xml").decode()
            self.fonts = z.read("word/fontTable.xml").decode()
            self.numbering = z.read("word/numbering.xml").decode()

    def test_no_style_keeps_with_next(self):
        # In a table cell Word reads either flag as "keep this row whole", which
        # pushed the cover's whole body to page 2.
        self.assertNotIn("<w:keepNext/>", self.styles)
        self.assertNotIn("<w:keepLines/>", self.styles)

    def test_plex_is_embedded(self):
        self.assertEqual(len([n for n in self.names if n.startswith("word/fonts/")]), 7)
        for family in ("IBM Plex Sans", "IBM Plex Sans Light", "IBM Plex Sans SmBld",
                       "IBM Plex Serif"):
            self.assertIn(f'<w:font w:name="{family}"><w:panose1', self.fonts)

    def test_list_markers_name_plex(self):
        # Without it Word sets the tab after a list number in Arial.
        self.assertEqual(self.numbering.count('<w:rFonts w:ascii="IBM Plex Sans"'), 6)

    def test_widow_control_is_on(self):
        self.assertIn("<w:widowControl/>", self.styles)


class Fitting(unittest.TestCase):
    def test_widths_come_from_the_font(self):
        from fontTools.ttLib import TTFont
        font = TTFont(os.path.join(ASSETS, "fonts", "IBMPlexSans-Light.ttf"))
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        expected = sum(hmtx[cmap[ord(c)]][0] for c in "Plex") * 32 / 1000
        self.assertAlmostEqual(text_width("Plex", 32, "light"), expected)

    def test_wrap_counts_lines(self):
        self.assertEqual(len(wrap("Certificate lifecycle management", 32, 333.5, "light")), 2)

    def test_title_drops_a_size_to_fit_three_lines(self):
        b = Brief("Secure every machine identity across the hybrid cloud estate today")
        self.assertEqual(b._fit_title()[0], "Title Medium")

    def test_overlong_title_warns(self):
        b = Brief("Secure every machine identity across hybrid cloud with one platform "
                  "for secrets and certificates")
        b.cover()
        self.assertTrue(any("title runs to 4 lines" in w for w in b.warnings))


class Cover(unittest.TestCase):
    def test_title_block_is_a_fixed_row(self):
        b = brief()
        tr = b.doc.tables[0].rows[0]._tr
        height = tr.trPr.find(qn("w:trHeight"))
        self.assertEqual((height.get(qn("w:val")), height.get(qn("w:hRule"))), ("4720", "exact"))

    def test_body_shares_the_highlights_baseline(self):
        b = brief()
        first = b.body("Intro.")[0]
        self.assertEqual(first.paragraph_format.space_before.pt, 18)
        self.assertEqual(b.body("Next.")[0].paragraph_format.space_before, None)

    def test_page_one_has_the_logo_and_later_pages_the_folio(self):
        b = brief()
        s = b.doc.sections[0]
        self.assertTrue(s.different_first_page_header_footer)
        self.assertIn("graphicData", s.first_page_footer._element.xml)
        self.assertIn(" PAGE ", s.footer._element.xml)
        self.assertIn("Certificate lifecycle management  |  November 2026", s.footer._element.xml)

    def test_hero_logotype_replaces_the_8_bar(self):
        b = brief(logotype="Consulting")
        footer = b.doc.sections[0].first_page_footer._element.xml
        self.assertNotIn("graphicData", footer)
        self.assertIn("Consulting", footer)

    def test_other_units_keep_the_8_bar(self):
        b = brief(logotype="Data and AI")
        self.assertTrue(any("not a hero unit" in w for w in b.warnings))
        self.assertIn("graphicData", b.doc.sections[0].first_page_footer._element.xml)


class Flow(unittest.TestCase):
    def test_side_elements_start_rows(self):
        b = brief()
        b.body("Beside the highlights.")
        b.stats([("up", "40%", "of enterprises")])
        b.body("Beside the stats.")
        b.callout("What changes", "Renewal is a job.")
        self.assertEqual(len(b.doc.tables), 1)
        self.assertEqual(len(b.doc.tables[0].rows), 4)

    def test_tables_never_touch(self):
        # Word merges two adjacent tables into one.
        b = brief()
        b.body("Text.")
        b.table(["A", "B"], [["1", "2"]])
        b.body("More text.")
        b.back_page(sources=["A source."])
        kids = body_children(b)
        for a, c in zip(kids, kids[1:]):
            self.assertFalse(a == c == "tbl", kids)

    def test_two_column_table_follows_the_grid(self):
        b = brief()
        t = b.table(["Need", "Answer"], [["x", "y"]])
        grid = [int(g.get(qn("w:w"))) for g in t._tbl.tblGrid.findall(qn("w:gridCol"))]
        self.assertEqual(grid, [4290, 6670])

    def test_ragged_row_warns(self):
        b = brief()
        b.table(["A", "B", "C"], [["1", "2"]])
        self.assertTrue(any("ragged" in w for w in b.warnings))

    def test_table_cells_hold_one_paragraph(self):
        b = brief()
        t = b.table(["A", "B"], [["1", "2"]])
        self.assertTrue(all(len(c.paragraphs) == 1 for r in t.rows for c in r.cells))

    def test_caption_keeps_with_its_table(self):
        b = brief()
        t = b.table(["A", "B"], [["1", "2"]], caption="Table 1. Example.")
        self.assertTrue(t.rows[-1].cells[0].paragraphs[0].paragraph_format.keep_with_next)

    def test_pagebreak_writes_one_break(self):
        b = brief()
        b.body("Page one.")
        b.pagebreak()
        b.pagebreak()
        h = b.heading("Page two")
        breaks = [p for p in b.doc.paragraphs if p.paragraph_format.page_break_before]
        self.assertEqual(len(breaks), 1)
        self.assertEqual(breaks[0].style.name, "Page Break")
        self.assertEqual(h.paragraph_format.space_before.pt, 0)

    def test_heading_after_body_keeps_its_space(self):
        b = brief()
        b.body("Text.")
        self.assertIsNone(b.heading("Next").paragraph_format.space_before)

    def test_lists_restart(self):
        b = brief()
        first = b.numbers(["a", "b"])[0]
        second = b.numbers(["c"])[0]
        num = lambda p: p._p.pPr.numPr.numId.val
        self.assertNotEqual(num(first), num(second))


class Inline(unittest.TestCase):
    def test_reference_link_and_bold(self):
        b = brief()
        p = b.body("Approved in 2025.[^1] See the [overview](https://ibm.com) and **this**.")[0]
        xml = p._p.xml
        self.assertIn('w:val="SourceReference"', xml)
        self.assertIn("<w:hyperlink", xml)
        self.assertIn('w:val="StrongSemibold"', xml)

    def test_button_hugs_its_label(self):
        b = brief()
        p = b.button("Learn more about IBM", "https://ibm.com")
        # The template's own button for this label is 135.8pt wide.
        width = 333.5 + 9.5 - p.paragraph_format.right_indent.pt
        self.assertAlmostEqual(width, 135.8, delta=1.5)
        self.assertIn("→", p._p.xml)


class BackPage(unittest.TestCase):
    def build(self, **kw):
        b = brief()
        b.body("Text.")
        b.back_page(**kw)
        return b

    def legal_text(self, b):
        return "\n".join(p.text for p in b.doc.tables[-1].rows[0].cells[1].paragraphs)

    def test_trademarks_take_a_serial_comma(self):
        text = self.legal_text(self.build(trademarks=["IBM Cloud Pak", "watsonx"]))
        self.assertIn("IBM, the IBM logo, IBM Cloud Pak, and watsonx are trademarks", text)

    def test_two_marks_take_and(self):
        self.assertIn("IBM and the IBM logo are trademarks", self.legal_text(self.build()))

    def test_attributions_come_before_the_boilerplate(self):
        text = self.legal_text(self.build(attributions=["Red Hat is a trademark of Red Hat, Inc."]))
        self.assertLess(text.index("Red Hat is"), text.index("This document is current"))

    def test_legal_floats_to_the_bottom_on_its_own_page(self):
        b = self.build()
        self.assertIn('w:tblpYSpec="bottom"', b.doc.tables[-1]._tbl.xml)
        last = b.doc.sections[-1]
        self.assertTrue(last.different_first_page_header_footer)
        self.assertIn("graphicData", last.first_page_footer._element.xml)

    def test_always_warns_to_check_the_disclaimers(self):
        self.assertTrue(any("Corporate Disclaimers" in w for w in self.build().warnings))

    def test_missing_back_page_warns(self):
        b = brief()
        with tempfile.TemporaryDirectory() as d:
            b.save(os.path.join(d, "x.docx"))
        self.assertTrue(any("no back_page()" in w for w in b.warnings))

    def test_saves_a_readable_package(self):
        b = self.build(sources=["[Ballot SC-081v3](https://cabforum.org), CA/Browser Forum, 2025."])
        with tempfile.TemporaryDirectory() as d:
            path = b.save(os.path.join(d, "brief.docx"))
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                self.assertIn("word/fonts/IBMPlexSans-Light.ttf", z.namelist())


if __name__ == "__main__":
    unittest.main()
