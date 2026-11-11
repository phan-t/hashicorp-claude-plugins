#!/usr/bin/env python3
"""Build an IBM solution brief or data sheet as an editable .docx.

    from ibm_brief import Brief

    b = Brief("Certificate lifecycle management",
              subtitle="Automate certificates with HashiCorp Vault and Red Hat Ansible",
              date="April 2026")
    b.cover(highlights=["Cut certificate outages to zero", "Rotate in minutes"])
    b.body("Digital certificates are foundational to enterprise security ...")
    b.heading("The challenge")
    b.body("...")
    b.stats([("↑", "40%", "of enterprises had a certificate outage last year")])
    b.body("...")
    b.back_page(sources=["Title, Publisher, 12 March 2026."],
                attributions=["HashiCorp and Vault are trademarks ..."])
    b.save("brief.docx")

Everything visual comes from ibm-brief-template.docx, which build_template.py
generates from measurements of IBM's InDesign template. This module picks styles
from it and never sets a font, a size or a colour of its own.

Pages are laid out as the template lays them out: a side column at the left
margin and a main column from 246.5pt. In Word that is an invisible two-cell
table ("IBM Layout"). Side elements (highlights, stats, callouts, standalone
headings, side quotes) each start a row; main-column content flows into the
current row's main cell. Full-width tables and images sit between layout tables.

Inline markup, accepted anywhere text is: **bold**, *italic*, [text](url), and
[^1] for a superscript source reference.
"""

from __future__ import annotations

import copy
import datetime
import os
import re
from typing import Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml.ns import qn
from docx.oxml.parser import parse_xml
from docx.shared import Pt, Twips

import font_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "ibm-brief-template.docx")
MEDIA = os.path.join(HERE, "media")

# Geometry, in twips, matching build_template.py.
TEXT_W, SIDE_W, MAIN_W = 10960, 4290, 6670
MAIN_PT = MAIN_W / 20                       # 333.5pt
# The cover's title block is a row of fixed height, so the highlights and the
# first body paragraph start on the template's y=296pt baseline whatever the
# title's length. Calibrated by rendering through Word; see design-system.md.
COVER_ROW_H = 4720                          # 236pt, from the 32pt top margin
MARKER_H_PT = 18                            # the blue marker's line plus its space after
TITLE_SIZES = (("Title", 32, 40), ("Title Medium", 28, 36), ("Title Small", 24, 30))
SUBTITLE_PT, SUBTITLE_LEAD, SUBTITLE_GAP = 14, 20, 14
TITLE_LINES_MAX, SUBTITLE_LINES_MAX = 3, 3
BUTTON_PAD = (9.5, 17, 8, 11)               # left pad, label to arrow, arrow, right pad
LOGO_W_PT = 58.5                            # the 8-bar, as the template sets it
HERO_LOGOTYPES = {"Consulting", "iX", "Research", "Security", "Cloud", "Watson"}

_NSDECL = (
    ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
)

_INLINE = re.compile(
    r"\[\^(?P<ref>\d+)\]"
    r"|\[(?P<link>[^\]]+)\]\((?P<href>[^)]+)\)"
    r"|\*\*(?P<bold>[^*]+)\*\*"
    r"|(?<!\*)\*(?P<italic>[^*]+)\*(?!\*)"
)

LEGAL = [
    "This document is current as of the initial date of publication and may be changed by IBM "
    "at any time. Not all offerings are available in every country in which IBM operates.",
    "Examples presented are illustrative only. Actual results will vary based on client "
    "configurations and conditions and, therefore, generally expected results cannot be provided.",
    "It is the user’s responsibility to verify the operation of any non-IBM products or programs "
    "with IBM products and programs. IBM is not responsible for non-IBM products and programs.",
    "THE INFORMATION IN THIS DOCUMENT IS PROVIDED “AS IS” WITHOUT ANY WARRANTY, EXPRESS OR "
    "IMPLIED, INCLUDING WITHOUT ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE "
    "AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM products are warranted according to the "
    "terms and conditions of the agreements under which they are provided.",
    "No IT system or product should be considered completely secure, and no single product, service, "
    "or security measure can be completely effective in preventing improper use or access. IBM does "
    "not warrant that any systems, products, or services are immune from, or will make your "
    "enterprise immune from, the malicious or illegal conduct of any party.",
    "The client is responsible for ensuring compliance with all applicable laws and regulations. "
    "IBM does not provide legal advice nor represent or warrant that its services or products will "
    "ensure that the client is compliant with any law or regulation.",
]


def _xml(fragment: str):
    return parse_xml(f"<ibm{_NSDECL}>{fragment}</ibm>")[0]


def text_width(text: str, size: float, face: str = "regular") -> float:
    """How wide text sets, in points, from the shipped font's advance widths."""
    table = getattr(font_metrics, face.upper())
    fallback = table.get("n", 560)
    return sum(table.get(c, fallback) for c in text) * size / font_metrics.UNITS_PER_EM


def wrap(text: str, size: float, width: float, face: str = "regular") -> list[str]:
    """Greedy word wrap, as Word does it, to count the lines a string takes."""
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}" if line else word
        if line and text_width(trial, size, face) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def _plain(text: str) -> str:
    """Text as it will set, with the inline markup removed."""
    return _INLINE.sub(lambda m: m.group("link") or m.group("bold") or m.group("italic")
                       or m.group("ref") or "", text or "")


class Brief:
    """One solution brief. Methods append in reading order."""

    def __init__(self, title: str, subtitle: str | None = None, date: str | None = None,
                 footer_title: str | None = None, template: str | None = None):
        self.doc = Document(template or TEMPLATE)
        self.title = title
        self.subtitle = subtitle
        self.date = date or datetime.date.today().strftime("%B %Y")
        self.footer_title = footer_title or title
        self.warnings: list[str] = []
        self._table = None          # the layout table rows are being added to
        self._main = None           # the main cell content is flowing into
        self._fresh: set = set()    # cells still holding their one empty paragraph
        self._pending_break = False
        self._covered = False
        self._backed = False
        self._pic_id = 100
        body = self.doc.element.body
        for p in body.findall(qn("w:p")):
            body.remove(p)

    # ------------------------------------------------------------------ cover

    def cover(self, highlights: Sequence[str] = (), highlights_title: str = "Highlights",
              business_unit: str | None = None, logotype: str | None = None,
              logos: Sequence[str] = (), logo_height: float = 12):
        """The first page: title block, highlights, and the start of the body.

        business_unit names a unit without its own logotype ("IBM Data and AI"),
        set top left. logotype is a hero unit ("Consulting"), set as "IBM
        Consulting" in place of the 8-bar. logos are partner marks, such as
        HashiCorp and Red Hat on a joint brief, stacked top left at logo_height."""
        if self._covered:
            raise RuntimeError("cover() is called once, first")
        self._covered = True
        style, lines = self._fit_title()
        sub_lines = wrap(self.subtitle, SUBTITLE_PT, MAIN_PT) if self.subtitle else []
        if len(sub_lines) > SUBTITLE_LINES_MAX:
            self.warnings.append(f"! subtitle runs to {len(sub_lines)} lines; the template allows "
                                 f"{SUBTITLE_LINES_MAX}. Shorten it.")
        if logotype and logotype not in HERO_LOGOTYPES:
            self.warnings.append(f"! logotype {logotype!r} is not a hero unit "
                                 f"({', '.join(sorted(HERO_LOGOTYPES))}); pass it as "
                                 "business_unit instead, which keeps the 8-bar.")
            business_unit, logotype = business_unit or f"IBM {logotype}", None
        if len(highlights) > 4:
            self.warnings.append(f"! {len(highlights)} highlights; the template shows three.")

        table = self._new_table()
        top = table.rows[0]
        top.height = Twips(COVER_ROW_H)
        top.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
        side, main = top.cells
        side.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        # A three-line title starts at the top of the page, as the template's
        # three-line covers do; shorter ones sit on the block's bottom edge.
        main.vertical_alignment = (WD_CELL_VERTICAL_ALIGNMENT.TOP if len(lines) >= 3
                                   else WD_CELL_VERTICAL_ALIGNMENT.BOTTOM)
        if business_unit:
            self._runs(self._cell_para(side, "Business Unit"), business_unit)
        for path in logos:
            if not os.path.exists(path):
                self.warnings.append(f"! missing logo: {path}")
                continue
            p = self._cell_para(side, "Business Unit")
            p.paragraph_format.space_before = Pt(6) if p is not side.paragraphs[0] else None
            p.add_run().add_picture(path, height=Pt(logo_height))
        self._runs(self._cell_para(main, style), self.title)
        if self.subtitle:
            self._runs(self._cell_para(main, "Subtitle"), self.subtitle)
        # The subtitle's last line sits 30pt above the block's bottom edge, and
        # so at least 48pt above the first body line, as the template asks.
        main.paragraphs[-1].paragraph_format.space_after = Pt(30)

        row = self._add_row(table)
        side, main = row.cells
        self._table, self._main = table, main
        if highlights:
            self._marker(side)
            self._runs(self._cell_para(side, "Highlights Title"), highlights_title)
            for h in highlights:
                self._runs(self._cell_para(side, "Highlight"), h)
        # The body's first line shares a baseline with "Highlights", so it drops
        # by the marker's height.
        self._first_offset = MARKER_H_PT
        self._footers(logotype)
        return table

    def _fit_title(self) -> tuple[str, list[str]]:
        for style, size, _ in TITLE_SIZES:
            lines = wrap(self.title, size, MAIN_PT, "light")
            if len(lines) <= TITLE_LINES_MAX:
                return style, lines
        self.warnings.append(f"! title runs to {len(lines)} lines even at 24pt; the template "
                             f"allows {TITLE_LINES_MAX}. Shorten it.")
        return style, lines

    # ------------------------------------------------------------ main column

    def heading(self, text: str):
        """A section heading in the main column, 14/20."""
        p = self._main_para("Heading 1")
        if self._opened:
            # First on a page or after a table: the space above a heading
            # separates it from body text, and there is none here.
            p.paragraph_format.space_before = Pt(0)
        return self._runs(p, text)

    def subheading(self, text: str):
        """A subheading in the main column, 9/12 semibold."""
        return self._runs(self._main_para("Heading 2"), text)

    def body(self, *paragraphs: str):
        return [self._runs(self._main_para("Normal"), t) for t in paragraphs]

    def bullets(self, items: Iterable[str | tuple[int, str]]):
        return self._list(items, "List Bullet", 900)

    def numbers(self, items: Iterable[str | tuple[int, str]]):
        return self._list(items, "List Number", self._fresh_num(901))

    def _list(self, items, style: str, num_id: int):
        out = []
        for item in items:
            level, text = item if isinstance(item, tuple) else (0, item)
            p = self._main_para(style)
            ppr = p._p.get_or_add_pPr()
            ppr.insert_element_before(
                _xml(f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="{num_id}"/></w:numPr>'),
                "w:spacing", "w:ind", "w:jc")
            out.append(self._runs(p, text))
        # The last item takes a full grid line before whatever follows.
        out[-1].paragraph_format.space_after = Pt(12)
        return out

    def quote(self, text: str, name: str | None = None, role: str | None = None,
              company: str | None = None, boxed: bool = False):
        """A quote: in the side column by default, or boxed in the main column.

        The template asks for no quotation marks on a boxed quote, and for at most
        one quote or callout of either kind on a page."""
        lines = [x for x in (role, company) if x]
        if boxed:
            first = self._main_para("Quote Box")
            first.paragraph_format.space_before = Pt(24)
            self._runs(first, text.strip("“”\""))
            last = first
            if name:
                last = self._runs(self._main_para("Quote Box Name"), name)
            for x in lines:
                last = self._runs(self._main_para("Quote Box Role"), x)
            last.paragraph_format.space_after = Pt(36)
            return first
        side = self._side_row()
        p = last = self._runs(self._cell_para(side, "Quote"), text)
        if name:
            last = self._runs(self._cell_para(side, "Quote Name"), name)
        for x in lines:
            last = self._runs(self._cell_para(side, "Quote Role"), x)
        # A side quote is often taller than the main text beside it, and then
        # its last line is what the next row starts under.
        last.paragraph_format.space_after = Pt(24)
        return p

    def button(self, label: str, url: str, secondary: bool = False):
        """A call-to-action button in the main column, with its arrow.

        The box is the paragraph's border, sized to the label from the font's
        own widths, so it stays editable text."""
        left, gap, arrow, right = BUTTON_PAD
        width = left + text_width(label, 9) + gap + arrow + right
        p = self._main_para("Button Secondary" if secondary else "Button")
        p.paragraph_format.right_indent = Twips(int((MAIN_PT + left - width) * 20))
        p.paragraph_format.tab_stops.add_tab_stop(Twips(int((width - right) * 20)),
                                                  alignment=2)  # right
        link = self._hyperlink(p, label, url, styled=False)
        link.append(_xml('<w:r><w:tab/><w:t>→</w:t></w:r>'))
        return p

    def image(self, path: str, caption: str | None = None, full: bool = False):
        """A picture across the main column, or across the page with full=True."""
        if not os.path.exists(path):
            self.warnings.append(f"! missing image: {path}")
            return None
        width = Twips(TEXT_W if full else MAIN_W)
        if full:
            self._close_table()
            p = self._top_para("Normal")
        else:
            p = self._main_para("Normal")
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_picture(path, width=width)
        if caption:
            c = self._top_para("Caption") if full else self._main_para("Caption")
            self._runs(c, caption)
        return p

    # ------------------------------------------------------------ side column

    def side_heading(self, text: str, intro: str | None = None):
        """A standalone heading in the side column, starting a new section.

        Use one placement for headings throughout: all standalone, or all in
        the main column."""
        opened = self._table is None
        side = self._side_row()
        p = self._runs(self._cell_para(side, "Side Heading"), text)
        if opened:
            p.paragraph_format.space_before = Pt(0)
        if intro:
            self._runs(self._cell_para(side, "Side Text Wide"), intro)
        return p

    def stats(self, items: Sequence[tuple[str, str] | tuple[str, str, str]]):
        """Big numbers in the side column: (value, text) or (arrow, value, text).

        The arrow is "up", "down", "↑" or "↓", and sets in IBM Blue."""
        side = self._side_row()
        for item in items:
            arrow, value, text = item if len(item) == 3 else (None, *item)
            arrow = {"up": "↑", "down": "↓"}.get(arrow, arrow)
            p = self._cell_para(side, "Stat")
            if arrow:
                p.add_run(arrow, style="Stat Arrow")
            p.add_run(value)
            self._runs(self._cell_para(side, "Stat Text"), text)
        return side

    def callout(self, title: str, text: str):
        """A short callout in the side column under the blue marker."""
        side = self._side_row()
        self._marker(side)
        self._runs(self._cell_para(side, "Callout Title"), title)
        return self._runs(self._cell_para(side, "Side Text"), text)

    # ------------------------------------------------------------ full width

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[str]],
              widths: Sequence[float] | None = None, caption: str | None = None):
        """A data table across the page: rules under the header and every row.

        widths are in points. Two columns default to the side and main columns;
        more share the page equally."""
        n = len(headers)
        if widths:
            cols = [int(w * 20) for w in widths]
            if abs(sum(cols) - TEXT_W) > 40:
                self.warnings.append(f"! table widths sum to {sum(cols) / 20:.0f}pt; "
                                     f"the page is {TEXT_W / 20:.0f}pt")
        elif n == 2:
            cols = [SIDE_W, MAIN_W]
        else:
            cols = [TEXT_W // n] * n
            cols[-1] = TEXT_W - sum(cols[:-1])
        for i, row in enumerate(rows):
            if len(row) != n:
                self.warnings.append(f"! ragged table row {i + 1}: {len(row)} cells for {n} headers")
        self._close_table()
        self._gap("Spacer")
        t = self.doc.add_table(rows=1 + len(rows), cols=n)
        t.style = self.doc.styles["IBM Table"]
        self._fix_table(t, cols)
        for row in t.rows:
            for c in row.cells:
                self._fresh.add(c._tc)
        hdr = t.rows[0]
        hdr._tr.get_or_add_trPr().append(_xml("<w:tblHeader/>"))
        for cell, text in zip(hdr.cells, headers):
            self._runs(self._cell_para(cell, "Table Header"), text)
        for r, row in enumerate(rows, 1):
            t.rows[r]._tr.get_or_add_trPr().append(_xml("<w:cantSplit/>"))
            for cell, text in zip(t.rows[r].cells, row):
                self._runs(self._cell_para(cell, "Table Text"), str(text))
        if caption:
            # Keep the last row with its caption; a caption never starts a page.
            for cell in t.rows[-1].cells:
                for para in cell.paragraphs:
                    para.paragraph_format.keep_with_next = True
            self._runs(self._top_para("Caption"), caption)
        return t

    def pagebreak(self):
        """Start the next block on a new page. Writes nothing on its own, so a
        doubled or trailing pagebreak() never leaves a blank page."""
        self._close_table()
        self._pending_break = True

    # -------------------------------------------------------------- back page

    def back_page(self, sources: Sequence[str] = (), trademarks: Sequence[str] = (),
                  attributions: Sequence[str] = (), extra: Sequence[str] = (),
                  year: int | None = None, produced_in: str = "United States of America",
                  legal: Sequence[str] | None = None):
        """The closing page: numbered sources, then the copyright and legal block.

        trademarks are the IBM marks used in the brief beyond IBM and the IBM logo,
        such as "IBM Cloud Pak". attributions are third-party statements, one
        paragraph each ("Red Hat and OpenShift are trademarks ..."), listing only
        the marks the brief uses. extra paragraphs go after the standard text."""
        if self._backed:
            raise RuntimeError("back_page() is called once, last")
        self._backed = True
        self._close_table()
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        # add_section ends the previous section on a paragraph of its own; set it
        # at 1pt so it can never push a full page onto a blank one.
        prev = self.doc.element.body.findall(qn("w:p"))[-1]
        prev_p = next(p for p in self.doc.paragraphs if p._p is prev)
        prev_p.style = self.doc.styles["Page Break"]
        section.different_first_page_header_footer = True
        for part in (section.header, section.footer, section.first_page_header,
                     section.first_page_footer):
            part.is_linked_to_previous = False
        self._logo(section.first_page_footer.paragraphs[0])

        if sources:
            table = self._new_table()
            main = table.rows[0].cells[1]
            for i, s in enumerate(sources, 1):
                self._runs(self._cell_para(main, "Source"), f"{i}.\t{s}")
            self._gap("Spacer")
        year = year or datetime.date.today().year

        legal_t = self.doc.add_table(rows=1, cols=2)
        legal_t.style = self.doc.styles["IBM Layout"]
        self._fix_table(legal_t, [SIDE_W, MAIN_W])
        # Floated to the bottom margin, where the template sets it.
        legal_t._tbl.tblPr.append(_xml(
            '<w:tblpPr w:leftFromText="0" w:rightFromText="0" w:vertAnchor="margin" '
            'w:horzAnchor="margin" w:tblpY="0" w:tblpYSpec="bottom"/>'))
        self._order_tblpr(legal_t)
        side, main = legal_t.rows[0].cells
        self._fresh.update((side._tc, main._tc))
        self._cell_para(side, "Legal Side").add_run(f"© Copyright IBM Corporation {year}")
        address = self._cell_para(side, "Legal Side")
        for i, line in enumerate(("IBM Corporation", "New Orchard Road", "Armonk, NY 10504")):
            if i:
                address.add_run().add_break()
            address.add_run(line)
        produced = self._cell_para(side, "Legal Side")
        produced.add_run("Produced in the")
        produced.add_run().add_break()
        produced.add_run(produced_in)
        produced.add_run().add_break()
        produced.add_run(self.date)

        marks = ["IBM", "the IBM logo", *trademarks]
        listed = (" and ".join(marks) if len(marks) == 2
                  else ", ".join(marks[:-1]) + ", and " + marks[-1])
        self._cell_para(main, "Legal").add_run(
            f"{listed} are trademarks or registered trademarks of International Business Machines "
            "Corporation, in the United States and/or other countries. Other product and service "
            "names might be trademarks of IBM or other companies. A current list of IBM trademarks "
            "is available on ibm.com/trademark.")
        for text in [*attributions, *(LEGAL if legal is None else legal), *extra]:
            self._runs(self._cell_para(main, "Legal"), text)
        self.warnings.append("  legal text is the template v1.5 boilerplate; check it against "
                             "IBM's current Corporate Disclaimers document before publishing")
        return legal_t

    # ------------------------------------------------------------------- save

    def save(self, path: str) -> str:
        if not self._covered:
            self.warnings.append("! no cover(); the brief has no title page")
        if not self._backed:
            self.warnings.append("! no back_page(); every brief ends on the legal page")
        props = self.doc.core_properties
        props.title = self.title
        props.subject = self.subtitle or ""
        props.category = "IBM solution brief"
        self.doc.save(path)
        return path

    # -------------------------------------------------------------- internals

    def _footers(self, logotype: str | None):
        """Page 1 carries the 8-bar or a hero logotype; later pages the folio and
        the running title."""
        s = self.doc.sections[0]
        s.different_first_page_header_footer = True
        first = s.first_page_footer.paragraphs[0]
        if logotype:
            first.style = self.doc.styles["Logotype"]
            first.add_run("IBM")
            space = first.add_run(" ")
            # The template's -40 kerning between IBM and the unit name.
            space._r.get_or_add_rPr().append(_xml('<w:spacing w:val="-13"/>'))
            first.add_run(logotype).bold = True
        else:
            self._logo(first)
        p = s.footer.paragraphs[0]
        p.style = self.doc.styles["Footer"]
        for fld in ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>',
                    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>',
                    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>',
                    '<w:r><w:t>2</w:t></w:r>',
                    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'):
            p._p.append(_xml(fld))
        p.add_run(f"\t{self.footer_title}  |  {self.date}")

    def _logo(self, paragraph):
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.add_run().add_picture(os.path.join(MEDIA, "ibm-logo.png"), width=Pt(LOGO_W_PT))

    def _marker(self, cell):
        p = self._cell_para(cell, "Marker")
        p.add_run().add_picture(os.path.join(MEDIA, "blue-square.png"), width=Pt(6), height=Pt(6))
        return p

    def _new_table(self):
        """A layout table of one row, preceded by whatever keeps it apart from
        the table before it."""
        body = self.doc.element.body
        last = body[-1] if len(body) else None
        if last is not None and last.tag == qn("w:sectPr"):
            last = last.getprevious()
        if self._pending_break:
            self._gap("Page Break").paragraph_format.page_break_before = True
            self._pending_break = False
        elif last is not None and last.tag == qn("w:tbl"):
            self._gap("Spacer")
        t = self.doc.add_table(rows=1, cols=2)
        t.style = self.doc.styles["IBM Layout"]
        self._fix_table(t, [SIDE_W, MAIN_W])
        for c in t.rows[0].cells:
            self._fresh.add(c._tc)
        return t

    def _add_row(self, table):
        row = table.add_row()
        for c in row.cells:
            self._fresh.add(c._tc)
        return row

    def _side_row(self):
        """A new row for a side element; main content after it flows beside it."""
        if self._table is None:
            self._table = self._new_table()
            row = self._table.rows[0]
        else:
            row = self._add_row(self._table)
        side, self._main = row.cells
        self._first_offset = 0
        return side

    def _close_table(self):
        self._table, self._main = None, None

    def _main_para(self, style: str):
        if self._main is None:
            self._table = self._new_table()
            self._main = self._table.rows[0].cells[1]
            self._first_offset = 0
        fresh = self._main._tc in self._fresh
        # True when this paragraph opens a new layout table, which starts a page
        # or follows a full-width element.
        self._opened = (fresh and len(self._table.rows) == 1
                        and self._main._tc is self._table.rows[0].cells[1]._tc)
        p = self._cell_para(self._main, style)
        if fresh and getattr(self, "_first_offset", 0):
            p.paragraph_format.space_before = Pt(self._first_offset)
            self._first_offset = 0
        return p

    def _cell_para(self, cell, style: str):
        if cell._tc in self._fresh:
            self._fresh.discard(cell._tc)
            p = cell.paragraphs[0]
        else:
            p = cell.add_paragraph()
        p.style = self.doc.styles[style]
        return p

    def _top_para(self, style: str):
        p = self.doc.add_paragraph(style=style)
        if self._pending_break:
            p.paragraph_format.page_break_before = True
            self._pending_break = False
        return p

    def _gap(self, style: str):
        return self.doc.add_paragraph(style=style)

    def _fix_table(self, table, cols: Sequence[int]):
        """Fixed layout at exact column widths, flush with the left margin."""
        tbl = table._tbl
        tblpr = tbl.tblPr
        for tag in ("w:tblW", "w:tblLayout", "w:tblInd"):
            for el in tblpr.findall(qn(tag)):
                tblpr.remove(el)
        tblpr.append(_xml(f'<w:tblW w:w="{sum(cols)}" w:type="dxa"/>'))
        tblpr.append(_xml('<w:tblInd w:w="0" w:type="dxa"/>'))
        tblpr.append(_xml('<w:tblLayout w:type="fixed"/>'))
        tblpr.append(_xml('<w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" '
                          'w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/>'))
        for el in tblpr.findall(qn("w:tblLook"))[:-1]:
            tblpr.remove(el)
        grid = tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), cols):
            gc.set(qn("w:w"), str(w))
        for row in table.rows:
            for cell, w in zip(row.cells, cols):
                cell.width = Twips(w)
        self._order_tblpr(table)

    @staticmethod
    def _order_tblpr(table):
        order = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
                 "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders",
                 "shd", "tblLayout", "tblCellMar", "tblLook"]
        tblpr = table._tbl.tblPr
        kids = list(tblpr)
        for k in kids:
            tblpr.remove(k)
        rank = {qn(f"w:{n}"): i for i, n in enumerate(order)}
        for k in sorted(kids, key=lambda k: rank.get(k.tag, 99)):
            tblpr.append(k)

    def _fresh_num(self, abstract_id: int) -> int:
        """A numbering definition of the list's own, so each list starts at 1."""
        numbering = self.doc.part.numbering_part.element
        source = next(a for a in numbering.findall(qn("w:abstractNum"))
                      if a.get(qn("w:abstractNumId")) == str(abstract_id))
        clone = copy.deepcopy(source)
        new_id = max(int(a.get(qn("w:abstractNumId")))
                     for a in numbering.findall(qn("w:abstractNum"))) + 1
        clone.set(qn("w:abstractNumId"), str(new_id))
        source.addnext(clone)
        return numbering.add_num(new_id).numId

    def _runs(self, paragraph, text: str):
        pos = 0
        for m in _INLINE.finditer(text or ""):
            if m.start() > pos:
                paragraph.add_run(text[pos:m.start()])
            if m.group("ref"):
                paragraph.add_run(m.group("ref"), style="Source Reference")
            elif m.group("link"):
                self._hyperlink(paragraph, m.group("link"), m.group("href"))
            elif m.group("bold"):
                paragraph.add_run(m.group("bold"), style="Strong Semibold")
            elif m.group("italic"):
                paragraph.add_run(m.group("italic")).italic = True
            pos = m.end()
        if pos < len(text or ""):
            paragraph.add_run(text[pos:])
        return paragraph

    def _hyperlink(self, paragraph, text: str, url: str, styled: bool = True):
        rid = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
        link = _xml(f'<w:hyperlink r:id="{rid}"/>')
        run = paragraph.add_run(text, style="Hyperlink" if styled else None)
        paragraph._p.remove(run._r)
        link.append(run._r)
        paragraph._p.append(link)
        return link


__all__ = ["Brief", "text_width", "wrap"]
