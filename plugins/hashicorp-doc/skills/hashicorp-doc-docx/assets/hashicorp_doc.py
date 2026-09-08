#!/usr/bin/env python3
"""Build a HashiCorp-branded .docx assessment or engagement report.

    from hashicorp_doc import Doc

    d = Doc("Vault Assessment", subtitle="Architecture and Workflow", version="1.0")
    d.cover(date="October 2025", meta={"Company Name": "Acme Corp"})
    d.contents()
    d.h1("Introduction")
    d.body("HashiCorp was engaged to ...")
    d.backpage()
    d.save("assessment.docx")

Everything visual comes from `hashicorp-doc-template.docx`: the styles, the page
geometry, the cover footer wordmark. This module fills that template in; it never
sets a font, a size or a colour of its own. `build_template.py` owns those.

Inline markup, accepted anywhere text is: **bold**, *italic*, `code`, [text](url).
"""

from __future__ import annotations

import copy
import os
import re
from typing import Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml.ns import qn
from docx.oxml.parser import parse_xml
from docx.shared import Emu, Pt, Twips

import font_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "hashicorp-doc-template.docx")
MEDIA = os.path.join(HERE, "media")

EMU_PER_IN = 914400
PAGE_W_EMU = 7772400              # 8.5in, for the full-bleed art
TEXT_W_TWIPS = 8641               # 6.00in measure, from the template's margins
COVER_ART_H = 3837623             # 4.20in
BACK_ART_H = 5022913              # 5.49in
BACK_GAP = 4400                   # twips from the back art to the address block

# Cover budget, in twips.
PG_H_TWIPS, MAR_TOP_TWIPS, MAR_BOT_TWIPS = 15840, 1872, 1512
COVER_ART_H_TWIPS = 6043          # 4.20in of art, which the text flows below
# Word adds leading around a paragraph that the font's own ascent and descent do
# not express, and at the Subtitle style's double line spacing it is substantial.
# Measured off a rendered cover: the real block ran 1400 twips taller than the
# sum of its line heights. Held back here so the budget errs toward warning.
COVER_LEADING_ALLOWANCE = 1400
COVER_TEXT_H = (PG_H_TWIPS - MAR_BOT_TWIPS - COVER_ART_H_TWIPS
                - COVER_LEADING_ALLOWANCE)
TITLE_PT, SUBTITLE_PT, META_PT, BODY_PT = 40, 24, 11, 10
SUBTITLE_LINE_SPACING = 2.0       # the Subtitle style's w:line 480 auto
META_LINE = 266                   # 11pt Arial at single spacing; Arial, not the body font
LOGO_BLOCK = 1240                 # a customer logo at 1.1in plus its space after
COVER_GAP = 360                   # 18pt between the date and the metadata block

CELL_MARGINS = 198                # 99 twips either side, from the table style

# Defined by build_template.py, not by python-docx's stock numbering.xml.
BULLET_NUM = 900
DECIMAL_ABSTRACT = 901

# The reference's recommendation table, re-tuned to the 6in measure using the
# body font's real advance widths: every judgement column holds a bold header and
# the word "Medium" without breaking, and Recommendation takes what is left.
REC_HEADERS = ["ID", "Recommendation", "Impact", "Effort", "Priority", "Category"]
REC_WIDTHS = [982, 3434, 1020, 1020, 1020, 1165]

_NSDECL = (
    ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    ' xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
)


def _xml(fragment: str):
    """Parse an OOXML fragment into an element with the w:/r:/wp:/a:/pic:
    prefixes already bound, so callers can write plain OOXML."""
    return parse_xml(f"<hcd{_NSDECL}>{fragment}</hcd>")[0]


_INLINE = re.compile(
    r"\[(?P<link>[^\]]+)\]\((?P<href>[^)]+)\)"
    r"|\*\*(?P<bold>[^*]+)\*\*"
    r"|(?<!\*)\*(?P<italic>[^*]+)\*(?!\*)"
    r"|`(?P<code>[^`]+)`"
)


class Doc:
    """One document. Every method appends and returns the element it made."""

    def __init__(self, title: str, subtitle: str | None = None, version: str = "1.0",
                 template: str | None = None, font: str | None = None):
        self.doc = Document(template or TEMPLATE)
        if font:
            self._set_body_font(font)
        self.title = title
        self.subtitle = subtitle
        self.version = version
        self.warnings: list[str] = []
        self._body_started = False
        self._pending_break = False
        self._next_pic_id = 100
        # The template ships one empty paragraph so Word can open it. Drop it.
        body = self.doc.element.body
        for p in body.findall(qn("w:p")):
            body.remove(p)

    def _para(self, text: str = "", style: str | None = None):
        """Every paragraph goes through here so a pending page break lands on it.

        A break carried by its own empty paragraph -- what `add_page_break` makes
        -- leaves a blank page behind whenever the preceding page was already
        full. `pageBreakBefore` on the next real paragraph never does."""
        p = self.doc.add_paragraph(text, style=style)
        if self._pending_break:
            p.paragraph_format.page_break_before = True
            self._pending_break = False
        return p

    def _set_body_font(self, font: str) -> None:
        """Swap the whole document off Inter.

        Word substitutes a serif for any face it cannot resolve, so this is worth
        using only for a name you have confirmed the reader has:
        `Doc(font="HashiCorp Sans")` for an internal document, `Doc(font="Arial")`
        when the document must render on a machine you know nothing about."""
        rpr = self.doc.styles.element.find(qn("w:docDefaults")) \
            .find(qn("w:rPrDefault")).find(qn("w:rPr"))
        fonts = rpr.find(qn("w:rFonts"))
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            fonts.set(qn(attr), font)
        # The Subtitle style names the Light cut explicitly; keep it in step, at
        # the regular weight since a "<family> Light" name may not resolve.
        self.doc.styles["Subtitle"].font.name = font

    # ---------------------------------------------------------------- cover

    def cover(self, date: str | None = None, meta: dict[str, str] | None = None,
              logo: str | None = None, art: bool = True):
        """Title page: full-bleed art, title, subtitle, date, then the metadata
        block. The HashiCorp wordmark comes from the template's first-page
        footer -- do not add one here.

        The art takes the top 4.2in of the page and the text flows below it, so
        the cover holds far less than a normal page. `_fit_cover` budgets what is
        left and gives back the two spacers it is allowed to spend."""
        title_lines = self._title_lines(self.title)
        spacer, gap = self._fit_cover(title_lines, bool(self.subtitle), bool(date),
                                      len(meta or {}), art, bool(logo))

        p = self._para(style="Title")
        if art:
            self._anchor_page_image(p, os.path.join(MEDIA, "cover-art.png"),
                                    PAGE_W_EMU, COVER_ART_H,
                                    src_rect={"t": 40, "b": 40})
        self._runs(p, self.title)

        if logo:
            lp = self._para()
            lp.paragraph_format.space_after = Pt(12)
            lp.add_run().add_picture(logo, width=Emu(int(1.1 * EMU_PER_IN)))

        self._para(self.subtitle or "", style="Subtitle")
        if spacer:
            self._para("", style="Subtitle")
        if date:
            self._para(date, style="Subtitle")

        blank = self._para("", style="Cover Meta")
        blank.paragraph_format.space_after = Twips(gap)
        for label, value in (meta or {}).items():
            mp = self._para(style="Cover Meta")
            mp.add_run(f"{label}: ").bold = True
            self._runs(mp, str(value))
        return self

    @staticmethod
    def _width(text: str, pt: float, bold: bool = False) -> int:
        """Width of a string in twips, from the body font's own advance widths.

        Exact for the font the template embeds, which is the point: a guess at an
        average character width is a guess about a font the document does not
        use."""
        table = font_metrics.BOLD if bold else font_metrics.REGULAR
        fallback = table.get("n", font_metrics.UNITS_PER_EM // 2)
        units = sum(table.get(c, fallback) for c in text)
        return round(units / font_metrics.UNITS_PER_EM * pt * 20)

    @staticmethod
    def _line_height(pt: float, spacing: float = 1.0) -> int:
        """Height of one line in twips, from the font's own ascent and descent."""
        return round(pt * font_metrics.LINE_RATIO * spacing * 20)

    def _title_lines(self, title: str) -> int:
        """Lines the title wraps to at 40pt bold on the 6in measure."""
        lines, line = 1, ""
        for word in title.split():
            candidate = f"{line} {word}".strip()
            if line and self._width(candidate, TITLE_PT, bold=True) > TEXT_W_TWIPS:
                lines, line = lines + 1, word
            else:
                line = candidate
        return lines

    def _fit_cover(self, title_lines: int, has_subtitle: bool, has_date: bool,
                   meta_lines: int, art: bool, has_logo: bool):
        """Decide the two spacers, and warn if the cover still will not fit.

        Returns (keep the blank subtitle line, twips of gap above the metadata).
        Line heights are measured off rendered output rather than derived: Word
        gives a 40pt line a box nearer 51pt once leading is counted."""
        available = COVER_TEXT_H if art else PG_H_TWIPS - MAR_TOP_TWIPS - MAR_BOT_TWIPS
        title_line = self._line_height(TITLE_PT)
        subtitle_line = self._line_height(SUBTITLE_PT, SUBTITLE_LINE_SPACING)
        fixed = (title_lines * title_line
                 + (subtitle_line if has_subtitle else 0)
                 + (subtitle_line if has_date else 0)
                 + (LOGO_BLOCK if has_logo else 0)
                 + meta_lines * META_LINE)

        # Spend the blank subtitle line first, then the gap: the gap is what
        # separates two blocks, the spacer only pads one of them.
        for spacer, gap in ((True, COVER_GAP), (True, 0), (False, 0)):
            if fixed + (subtitle_line if spacer else 0) + gap <= available:
                return spacer, gap

        over = fixed - available
        self.warnings.append(
            f"! cover overflows onto a second page by about {over / 1440:.2f}in. "
            f"The title takes {title_lines} lines and there are {meta_lines} metadata "
            f"rows; shorten the title, drop a metadata row, or pass art=False.")
        return False, 0

    # ------------------------------------------------------------- contents

    def contents(self, heading: str = "Contents", levels: str = "1-2"):
        """A live Word TOC field over Heading 1 and Heading 2. Word offers to
        update it on open; in LibreOffice it is Tools > Update > Fields."""
        self.pagebreak()
        self._para(heading, style="Contents Heading")

        lo, hi = (levels.split("-") + [levels])[:2]
        instr = f' TOC \\o "{lo}-{hi}" \\h \\z \\u '
        p = self._para(style="toc 1")
        r = p.add_run()._r
        for kind, extra in (("begin", ' w:dirty="true"'), (None, None), ("separate", ""),
                            (None, "placeholder"), ("end", "")):
            if kind:
                r.append(_xml(f'<w:fldChar w:fldCharType="{kind}"{extra or ""}/>'))
            elif extra == "placeholder":
                r.append(_xml("<w:t>Right-click and choose Update Field to build "
                              "the table of contents.</w:t>"))
            else:
                r.append(_xml(f'<w:instrText xml:space="preserve">{instr}</w:instrText>'))
        return self

    def versions(self, rows: Sequence[Sequence[str]], heading: str = "Document Version"):
        """The revision history: version, date, author, changes."""
        self.pagebreak()
        self._para(heading, style="Contents Heading")
        return self.table(["Version", "Date", "Author", "Changes"], rows,
                          widths=[1296, 1728, 2593, 3024])

    # -------------------------------------------------------------- headings

    def h1(self, text: str):
        """A top-level section, always starting a new page -- that is the
        reference's grammar, one h1 per page. The first h1 also opens the body
        section, from which every page carries the running header."""
        if self._body_started:
            self.pagebreak()
        else:
            self._start_body()
        return self._heading(text, 1)

    def h2(self, text: str):
        return self._heading(text, 2)

    def h3(self, text: str):
        return self._heading(text, 3)

    def h4(self, text: str):
        return self._heading(text, 4)

    def _heading(self, text: str, level: int):
        p = self._para(style=f"Heading {level}")
        self._runs(p, text)
        return p

    # ------------------------------------------------------------------ text

    def body(self, *paragraphs: str):
        """One or more body paragraphs."""
        last = None
        for text in paragraphs:
            last = self._para()
            self._runs(last, text)
        return last

    def bullets(self, items: Iterable[str | tuple[int, str]]):
        """A bulleted list. An item may be `(level, text)` to nest it; levels
        are 0-based and the glyphs run round, square, filled square."""
        return self._list(items, num_id=BULLET_NUM)

    def numbers(self, items: Iterable[str | tuple[int, str]]):
        """A numbered list. Each call restarts at 1."""
        return self._list(items, num_id=self._fresh_num(DECIMAL_ABSTRACT))

    def _list(self, items, num_id: int):
        out = []
        for item in items:
            level, text = item if isinstance(item, tuple) else (0, item)
            p = self._para(style="List Paragraph")
            ppr = p._p.get_or_add_pPr()
            ppr.append(_xml(
                f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="{num_id}"/></w:numPr>'))
            p.paragraph_format.left_indent = Emu(int((level + 1) * 720 * 635))
            self._runs(p, text)
            out.append(p)
        if out:
            # List items sit tight against each other, so the last one has to
            # give the space back or whatever follows the list runs into it.
            # contextualSpacing only suppresses this between same-style
            # neighbours, which the paragraph after a list is not.
            out[-1].paragraph_format.space_after = Twips(200)
        return out

    def resources(self, items: Iterable[str | tuple[str, str]], heading: str = "Resources"):
        """A numbered list of links, the shape the reference closes on."""
        if heading:
            self.h1(heading)
        return self.numbers([
            f"[{item[0]}]({item[1]})" if isinstance(item, tuple) else item
            for item in items
        ])

    # ---------------------------------------------------------------- tables

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[str]],
              widths: Sequence[int] | None = None, caption: str | None = None):
        """A rule-and-band table: heavy rule above the header row and below the
        last, no verticals, alternate rows shaded. Widths are in twips and are
        scaled to the 6in measure; omit them for equal columns."""
        n = len(headers)
        for i, row in enumerate(rows):
            if len(row) != n:
                self.warnings.append(
                    f"! table row {i + 1} has {len(row)} cells, header has {n}")

        if self._pending_break:
            # A w:tbl carries no pageBreakBefore, so this one break does need a
            # paragraph of its own to hold it.
            self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            self._pending_break = False

        t = self.doc.add_table(rows=1, cols=n)
        t.style = "HashiCorp Table"
        t.autofit = False
        # python-docx already writes tblW and tblLook; edit those in place rather
        # than appending, or the table properties fall out of schema order.
        tbl_w = t._tbl.tblPr.find(qn("w:tblW"))
        tbl_w.set(qn("w:type"), "dxa")
        tbl_w.set(qn("w:w"), str(TEXT_W_TWIPS))
        # Turn on the last-row rule and the horizontal bands; turn off the
        # first-column emphasis the stock look asks for.
        look = t._tbl.tblPr.find(qn("w:tblLook"))
        for attr, val in (("w:firstRow", "1"), ("w:lastRow", "1"),
                          ("w:firstColumn", "0"), ("w:lastColumn", "0"),
                          ("w:noHBand", "0"), ("w:noVBand", "1")):
            look.set(qn(attr), val)

        cols = self._scale(widths, n)
        for gc, w in zip(t._tbl.findall(qn("w:tblGrid"))[0].findall(qn("w:gridCol")), cols):
            gc.set(qn("w:w"), str(w))

        for cell, text in zip(t.rows[0].cells, headers):
            self._fill(cell, text)
        # Repeat the header when the table breaks across a page.
        t.rows[0]._tr.get_or_add_trPr().append(_xml('<w:tblHeader/>'))

        for row in rows:
            cells = t.add_row().cells
            for cell, text in zip(cells, list(row) + [""] * (n - len(row))):
                self._fill(cell, text)

        for row in t.rows:
            for cell, w in zip(row.cells, cols):
                cell.width = Emu(w * 635)

        self._check_widths(headers, rows, cols)

        if caption:
            self.caption(caption)
        else:
            self._para()
        return t

    def recommendations(self, rows: Sequence[Sequence[str]], caption: str | None = None):
        """The assessment's summary table: ID, Recommendation, Impact, Effort,
        Priority, Category. Keep IDs prefixed by area (ARC-A1, OPS-B) so a
        recommendation can be cited in a meeting."""
        return self.table(REC_HEADERS, rows, widths=REC_WIDTHS, caption=caption)

    def _fill(self, cell, text: str):
        p = cell.paragraphs[0]
        p.style = self.doc.styles["Normal"]
        p.paragraph_format.space_after = Pt(0)
        self._runs(p, str(text))

    def _check_widths(self, headers, rows, cols) -> None:
        """Warn when a column is too narrow for its longest unbreakable word.

        Word does not shrink to fit -- it breaks mid-word, so `Medium` becomes
        `Mediu` over `m` and the table looks broken rather than tight. The header
        row is bold and therefore wider, so it is measured as bold."""
        for i, width in enumerate(cols):
            worst, needed = "", 0
            candidates = [(str(headers[i]), True)] if i < len(headers) else []
            candidates += [(str(row[i]), False) for row in rows if i < len(row)]
            for text, bold in candidates:
                for word in text.split():
                    w = self._width(word, BODY_PT, bold=bold) + CELL_MARGINS
                    if w > needed:
                        worst, needed = word, w
            if worst and needed > width:
                self.warnings.append(
                    f"! table column {i + 1} ({headers[i]!r}) is {width} twips; "
                    f"{worst!r} needs {needed}. Word will break it mid-word — "
                    f"widen the column or shorten the value.")

    @staticmethod
    def _scale(widths: Sequence[int] | None, n: int) -> list[int]:
        if not widths:
            return [TEXT_W_TWIPS // n] * n
        total = sum(widths)
        out = [round(w * TEXT_W_TWIPS / total) for w in widths]
        out[-1] += TEXT_W_TWIPS - sum(out)
        return out

    # ---------------------------------------------------------------- figures

    def image(self, path: str, width_in: float = 6.0, caption: str | None = None):
        """A figure, inline and set to the left margin. 6in fills the measure;
        landscape diagrams want that, portrait ones want less."""
        if not os.path.exists(path):
            self.warnings.append(f"! image not found, skipped: {path}")
            return None
        p = self._para()
        p.add_run().add_picture(path, width=Emu(int(width_in * EMU_PER_IN)))
        if caption:
            self.caption(caption)
        return p

    def caption(self, text: str):
        p = self._para(style="Caption")
        self._runs(p, text)
        return p

    def pagebreak(self):
        """Start the next block on a new page. Nothing is written until that
        block appears, so a trailing pagebreak() cannot leave a blank page."""
        self._pending_break = True
        return self

    # --------------------------------------------------------------- closing

    def backpage(self, lines: Sequence[str] = ("USA Headquarters",
                                               "101 Second St., Suite 700, San Francisco, CA, 94105",
                                               "[www.hashicorp.com](https://www.hashicorp.com)")):
        """The back cover: full-bleed art at the top, address block at the foot,
        and no running header."""
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        section.different_first_page_header_footer = False
        section.header.is_linked_to_previous = False   # blank again
        section.footer.is_linked_to_previous = False

        p = self._para()
        self._anchor_page_image(p, os.path.join(MEDIA, "back-cover.png"),
                                PAGE_W_EMU, BACK_ART_H)
        for i, line in enumerate(lines):
            cp = self._para(style="Colophon")
            if i == 0:
                # Drop the address block to the foot of the page in one measured
                # gap. Blank paragraphs would reflow the moment a line wraps.
                cp.paragraph_format.space_before = Emu(BACK_GAP * 635)
            self._runs(cp, line)
        return self

    def save(self, path: str) -> str:
        props = self.doc.core_properties
        props.title = self.title
        props.subject = self.subtitle or ""
        props.category = "HashiCorp assessment"
        self.doc.save(path)
        return path

    # -------------------------------------------------------------- internals

    def _start_body(self):
        """Open the body section, where the running header lives. Called by the
        first h1(); front matter stays in section 1, which has none."""
        if self._body_started:
            return
        self._body_started = True
        section = self.doc.add_section(WD_SECTION.NEW_PAGE)
        section.different_first_page_header_footer = False
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False

        p = section.header.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.add_run(self.version).bold = True
        p.add_run("   /   ").bold = True
        p.add_run(self.title)

    def _fresh_num(self, abstract_id: int) -> int:
        """A numbering definition of this list's own, so it starts at 1.

        Two lists that share an abstract definition keep counting from each
        other, and a startOverride restarts on every item in Word for Mac. What
        works is what Word itself does: copy the abstract definition."""
        numbering = self.doc.part.numbering_part.element
        source = next(a for a in numbering.findall(qn("w:abstractNum"))
                      if a.get(qn("w:abstractNumId")) == str(abstract_id))
        clone = copy.deepcopy(source)
        taken = {int(a.get(qn("w:abstractNumId")))
                 for a in numbering.findall(qn("w:abstractNum"))}
        new_id = max(taken) + 1
        clone.set(qn("w:abstractNumId"), str(new_id))
        source.addnext(clone)
        return numbering.add_num(new_id).numId

    def _runs(self, paragraph, text: str):
        """Split text on the inline markup and add one run per span."""
        pos = 0
        for m in _INLINE.finditer(text or ""):
            if m.start() > pos:
                paragraph.add_run(text[pos:m.start()])
            if m.group("link"):
                self._hyperlink(paragraph, m.group("link"), m.group("href"))
            elif m.group("bold"):
                paragraph.add_run(m.group("bold")).bold = True
            elif m.group("italic"):
                paragraph.add_run(m.group("italic")).italic = True
            elif m.group("code"):
                paragraph.add_run(m.group("code"), style="Code")
            pos = m.end()
        if pos < len(text or ""):
            paragraph.add_run(text[pos:])
        return paragraph

    def _hyperlink(self, paragraph, text: str, url: str):
        rid = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
        link = _xml(f'<w:hyperlink r:id="{rid}"/>')
        run = paragraph.add_run(text, style="Hyperlink")
        paragraph._p.remove(run._r)
        link.append(run._r)
        paragraph._p.append(link)
        return link

    def _anchor_page_image(self, paragraph, path: str, cx: int, cy: int,
                           src_rect: dict[str, int] | None = None):
        """Full-bleed art pinned to the top of the page. python-docx only makes
        inline pictures, so the anchor is written out here."""
        rid = self._image_rid(path)
        self._next_pic_id += 1
        edges = " ".join(f'{k}="{v}"' for k, v in (src_rect or {}).items())
        crop = f"<a:srcRect {edges}/>" if edges else "<a:srcRect/>"
        paragraph.add_run()._r.append(_xml(f'''<w:drawing>
<wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0"
  behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">
<wp:simplePos x="0" y="0"/>
<wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>
<wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV>
<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:wrapSquare wrapText="bothSides"/>
<wp:docPr id="{self._next_pic_id}" name="art{self._next_pic_id}"/>
<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{os.path.basename(path)}"/>
<pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/>{crop}<a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
</a:graphicData></a:graphic></wp:anchor></w:drawing>'''))
        return paragraph

    def _image_rid(self, path: str) -> str:
        """The relationship id for an image part, added to the document if new."""
        rid, _ = self.doc.part.get_or_add_image(path)
        return rid


__all__ = ["Doc"]
