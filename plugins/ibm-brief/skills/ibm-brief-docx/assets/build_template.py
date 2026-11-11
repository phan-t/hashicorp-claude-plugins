#!/usr/bin/env python3
"""Regenerate ibm-brief-template.docx.

The template is built on python-docx's own empty package and then restyled, so it
carries no content from any real brief. Every measurement here was read off IBM's
solution brief and data sheet InDesign template, v1.5, by measuring its PDF proof;
references/design-system.md records each one and where it came from.

    pip install python-docx fonttools
    python3 build_template.py [-o ibm-brief-template.docx]

Run this after changing a style or the page geometry. Nothing else in the skill
sets a font, a size or a colour; ibm_brief.py only picks styles defined here.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import zipfile

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml.parser import parse_xml
from docx.shared import Pt, RGBColor, Twips

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

# --- Page geometry, in twips (1/20 pt) ---------------------------------------
# US Letter. The template's content runs from x=32pt to x=580pt, with the main
# column starting at x=246.5pt, and stops at the "content should not cross this
# line" guide near y=700pt. The folio and the 8-bar sit on y=760pt.
PG_W, PG_H = 12240, 15840
MAR_LEFT = MAR_RIGHT = 640          # 32pt
MAR_TOP = 640                       # 32pt
MAR_BOT = 1840                      # 92pt: the guide at y=700pt
HDR_DIST = 640
FTR_DIST = 600                      # puts the 7pt folio's baseline on y=760pt
TEXT_W = PG_W - MAR_LEFT - MAR_RIGHT    # 10960 twips = 548pt
SIDE_W = 4290                       # 214.5pt: margin to the main column
MAIN_W = TEXT_W - SIDE_W            # 6670 twips = 333.5pt
# The side column's text measures. Highlights, stats and callouts wrap at about
# 122pt; a standalone heading's intro and a side quote run to about 194pt.
SIDE_NARROW_INDENT = SIDE_W - 2440  # right indent leaving 122pt
SIDE_WIDE_INDENT = SIDE_W - 3880    # right indent leaving 194pt

# --- Colour ------------------------------------------------------------------
BLACK = RGBColor(0, 0, 0)
BLUE = RGBColor(0x0F, 0x62, 0xFE)   # IBM Blue 60: links, buttons, stat arrows
QUOTE_FILL = "E5F6FF"               # the template's quote box
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# --- Type --------------------------------------------------------------------
# Word names a face by its legacy family name (name ID 1), which for Plex's
# weights is not "IBM Plex Sans SemiBold" but "IBM Plex Sans SmBld". These are the
# names in both the shipped TTFs and IBM's installable OTFs, version 3.005.
SANS = "IBM Plex Sans"
LIGHT = "IBM Plex Sans Light"
SEMIBOLD = "IBM Plex Sans SmBld"
SERIF = "IBM Plex Serif"

# (family, embed slot, file). Word embeds per family, in four slots.
EMBEDDED = [
    (SANS, "w:embedRegular", "IBMPlexSans-Regular.ttf"),
    (SANS, "w:embedBold", "IBMPlexSans-Bold.ttf"),
    (SANS, "w:embedItalic", "IBMPlexSans-Italic.ttf"),
    (SANS, "w:embedBoldItalic", "IBMPlexSans-BoldItalic.ttf"),
    (LIGHT, "w:embedRegular", "IBMPlexSans-Light.ttf"),
    (SEMIBOLD, "w:embedRegular", "IBMPlexSans-SemiBold.ttf"),
    (SERIF, "w:embedRegular", "IBMPlexSerif-Regular.ttf"),
]

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _xml(fragment: str):
    return parse_xml(fragment)


def _rfonts(name: str) -> str:
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}" w:cs="{name}"/>'


def pt(v: float) -> int:
    """Points to twips."""
    return int(round(v * 20))


def set_doc_defaults(doc) -> None:
    styles = doc.styles.element
    for old in styles.findall(qn("w:docDefaults")):
        styles.remove(old)
    styles.insert(0, _xml(
        f'<w:docDefaults {W}>'
        f'<w:rPrDefault><w:rPr>{_rfonts(SANS)}<w:color w:val="000000"/>'
        f'<w:sz w:val="18"/><w:szCs w:val="18"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
        f'<w:pPrDefault><w:pPr>'
        f'<w:widowControl/>'
        f'<w:spacing w:before="0" w:after="{pt(12)}" w:line="{pt(12)}" w:lineRule="exact"/>'
        f'</w:pPr></w:pPrDefault>'
        f'</w:docDefaults>'))


def add(doc, name: str, kind=WD_STYLE_TYPE.PARAGRAPH):
    try:
        return doc.styles[name]
    except KeyError:
        return doc.styles.add_style(name, kind)


def restyle(style, *, size=None, font=None, bold=None, italic=None, color=None,
            before=None, after=None, line=None, left=None, right=None, hanging=None,
            keep_next=False, keep_together=False, base=None):
    """Clear a style and set only what is meant. Sizes and spacing in points.

    Word's stock styles carry theme fonts and accent colours; dropping their rPr
    and pPr first is what keeps those out of an IBM document."""
    el = style.element
    for tag in ("w:rPr", "w:pPr"):
        for node in el.findall(qn(tag)):
            el.remove(node)
    if base is not None:
        style.base_style = base
    f = style.font
    if font:
        f.name = font
        rpr = el.get_or_add_rPr()
        rpr.get_or_add_rFonts().set(qn("w:cs"), font)
        rpr.get_or_add_rFonts().set(qn("w:eastAsia"), font)
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    if style.type == WD_STYLE_TYPE.CHARACTER:
        return style
    pf = style.paragraph_format
    if before is not None:
        pf.space_before = Twips(pt(before))
    if after is not None:
        pf.space_after = Twips(pt(after))
    if line is not None:
        spacing = el.get_or_add_pPr().get_or_add_spacing()
        spacing.set(qn("w:line"), str(pt(line)))
        spacing.set(qn("w:lineRule"), "exact")
    if left is not None:
        pf.left_indent = Twips(left)
    if right is not None:
        pf.right_indent = Twips(right)
    if hanging is not None:
        pf.first_line_indent = Twips(-hanging)
    if keep_next:
        pf.keep_with_next = True
    if keep_together:
        pf.keep_together = True
    return style


def box(style, fill: str | None, line: str | None, pad_tb: float, pad_lr: float,
        line_sz: int = 4) -> None:
    """Draw a box round a run of paragraphs with paragraph borders.

    Consecutive paragraphs with the same borders share one box, and the border's
    space is the box's padding, so a quote or a button stays in the text flow and
    needs no table or text box. With no visible line the border is drawn in the
    fill colour."""
    colour = line or fill
    sz = line_sz if line else 4
    edges = "".join(
        f'<w:{side} w:val="single" w:sz="{sz}" w:space="{int(pad)}" w:color="{colour}"/>'
        for side, pad in (("top", pad_tb), ("left", pad_lr), ("bottom", pad_tb),
                          ("right", pad_lr)))
    ppr = style.element.get_or_add_pPr()
    ppr.append(_xml(f'<w:pBdr {W}>{edges}</w:pBdr>'))
    if fill:
        ppr.append(_xml(f'<w:shd {W} w:val="clear" w:color="auto" w:fill="{fill}"/>'))
    _order_ppr(ppr)


# The schema fixes the order of pPr children; Word rejects or ignores a file that
# breaks it. python-docx appends, so anything added by hand is re-sorted here.
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
             "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
             "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
             "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
             "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
             "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]


def _order_ppr(ppr) -> None:
    children = list(ppr)
    rank = {f"{{{ppr.nsmap.get('w', '')}}}{n}": i for i, n in enumerate(PPR_ORDER)}
    for c in children:
        ppr.remove(c)
    for c in sorted(children, key=lambda c: rank.get(c.tag, 999)):
        ppr.append(c)


def tabs(style, *stops: tuple[str, int]) -> None:
    t = style.element.get_or_add_pPr().get_or_add_tabs()
    for kind, pos in stops:
        t.append(_xml(f'<w:tab {W} w:val="{kind}" w:pos="{pos}"/>'))
    _order_ppr(style.element.get_or_add_pPr())


def build_styles(doc) -> None:
    normal = restyle(doc.styles["Normal"])

    def para(name, **kw):
        s = restyle(add(doc, name), base=normal, **kw)
        s.next_paragraph_style = normal
        return s

    # Cover. Three title sizes, all Light, each on its own leading; the builder
    # picks the largest that sets the title in three lines.
    for name, size, lead in (("Title", 32, 40), ("Title Medium", 28, 36), ("Title Small", 24, 30)):
        para(name, font=LIGHT, size=size, line=lead, after=0)
    # No style here sets keep-with-next or keep-together. Almost everything in a
    # brief sits in a layout-table cell, and there Word reads either flag as
    # "keep this row whole and with the next row": a cover whose highlights
    # title kept with next pushed the entire body to page 2. A heading can
    # therefore end a page; the SKILL.md checklist asks for a look at that.
    para("Subtitle", size=14, line=20, before=14, after=0)
    para("Business Unit", font=SEMIBOLD, after=0)
    para("Highlights Title", font=SEMIBOLD, after=0, right=SIDE_NARROW_INDENT)
    para("Highlight", right=SIDE_NARROW_INDENT)
    para("Marker", line=14, after=4)

    # Body. 9/12 on a 12pt grid, 12pt between paragraphs.
    para("Heading 1", size=14, line=20, before=34, after=10)
    para("Heading 2", font=SEMIBOLD, after=0)
    para("Side Heading", size=14, line=20, before=36, after=12, right=SIDE_WIDE_INDENT)
    para("Side Text", right=SIDE_NARROW_INDENT)
    para("Side Text Wide", right=SIDE_WIDE_INDENT)
    para("Callout Title", font=SEMIBOLD, after=0, right=SIDE_NARROW_INDENT)
    para("Stat", font=LIGHT, size=30, line=30, after=8.5)
    para("Stat Text", after=36, right=SIDE_NARROW_INDENT)
    para("Caption", size=7, line=9, before=8, after=12)

    # Lists: an en dash for bullets, as IBM sets them.
    para("List Bullet", after=6, left=280, hanging=280)
    para("List Number", after=6, left=360, hanging=360)

    # Quotes. Plex Serif 12/16. The side quote sits in the side column; the box
    # quote fills the main column on the template's light blue.
    para("Quote", font=SERIF, size=12, line=16, after=3, right=SIDE_WIDE_INDENT)
    para("Quote Name", font=SEMIBOLD, after=0, right=SIDE_WIDE_INDENT)
    para("Quote Role", after=0, right=SIDE_WIDE_INDENT)
    for name, font, size, lead, after in (("Quote Box", SERIF, 12, 16, 3),
                                          ("Quote Box Name", SEMIBOLD, 9, 12, 0),
                                          ("Quote Box Role", SANS, 9, 12, 0)):
        s = para(name, font=font, size=size, line=lead, after=after, left=pt(15.5),
                 right=pt(15.5), )
        box(s, QUOTE_FILL, None, pad_tb=14, pad_lr=14)

    # Buttons. A filled primary and an outlined secondary, 24pt tall, the arrow
    # set on a right tab. ibm_brief.py sets the right indent per button so the
    # box hugs its label.
    for name, fill, line, colour in (("Button", "0F62FE", None, WHITE),
                                     ("Button Secondary", None, "0F62FE", BLACK)):
        s = para(name, color=colour, before=12, after=12, left=pt(9.5))
        box(s, fill, line, pad_tb=6, pad_lr=9.5)

    # Tables, the footer and the back page.
    para("Table Text", after=0)
    para("Table Header", font=SEMIBOLD, after=0)
    footer = para("Footer", size=7, line=9, after=0)
    tabs(footer, ("left", SIDE_W))
    para("Logotype", size=16, line=20, after=0)
    para("Source", size=7, line=9, after=0, left=240, hanging=240)
    para("Legal", size=7, line=9, after=9)
    para("Legal Side", size=7, line=9, after=9, right=SIDE_NARROW_INDENT)

    # Word merges two tables that touch, so a paragraph always sits between them.
    # "Spacer" is one 12pt grid line; "Page Break" is the 1pt paragraph that
    # carries a page break, because Word ignores pageBreakBefore inside a table.
    para("Spacer", after=0)
    para("Page Break", size=1, line=1, after=0)

    # Character styles.
    link = add(doc, "Hyperlink", WD_STYLE_TYPE.CHARACTER)
    restyle(link, color=BLUE)
    link.font.underline = True
    restyle(add(doc, "Stat Arrow", WD_STYLE_TYPE.CHARACTER), color=BLUE)
    restyle(add(doc, "Strong Semibold", WD_STYLE_TYPE.CHARACTER), font=SEMIBOLD)
    ref = restyle(add(doc, "Source Reference", WD_STYLE_TYPE.CHARACTER))
    ref.font.superscript = True

    build_table_styles(doc)

    # The stock styles python-docx ships (Heading 3 to 9, Title's relatives and
    # others) carry keep flags too. Strip them all, so a style someone applies
    # by hand in Word cannot reintroduce the page-2 problem either.
    for tag in ("w:keepNext", "w:keepLines"):
        for node in list(doc.styles.element.iter(qn(tag))):
            node.getparent().remove(node)


def build_table_styles(doc) -> None:
    """Two table styles.

    "IBM Layout" is invisible: no borders, no cell padding. Every page is a run of
    its rows, a side cell and a main cell, which is how the template's side column
    and main column sit together in Word.

    "IBM Table" is the template's data table: 0.25pt black rules under the header
    and under every row, no verticals, no fills."""
    styles = doc.styles.element
    for s in styles.findall(qn("w:style")):
        if s.get(qn("w:styleId")) in ("IBMLayout", "IBMTable"):
            styles.remove(s)
    styles.append(_xml(f'''<w:style {W} w:type="table" w:styleId="IBMLayout">
<w:name w:val="IBM Layout"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="60"/>
<w:tblPr><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/>
  <w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>
  <w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="0" w:type="dxa"/>
  <w:bottom w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>
</w:style>'''))
    rule = '<w:bottom w:val="single" w:sz="2" w:space="0" w:color="000000"/>'
    styles.append(_xml(f'''<w:style {W} w:type="table" w:styleId="IBMTable">
<w:name w:val="IBM Table"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/>
<w:tblPr><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/>{rule}
  <w:right w:val="nil"/><w:insideH w:val="single" w:sz="2" w:space="0" w:color="000000"/>
  <w:insideV w:val="nil"/></w:tblBorders>
  <w:tblCellMar><w:top w:w="{pt(5)}" w:type="dxa"/><w:left w:w="0" w:type="dxa"/>
  <w:bottom w:w="{pt(8)}" w:type="dxa"/><w:right w:w="{pt(12)}" w:type="dxa"/></w:tblCellMar></w:tblPr>
<w:tblStylePr w:type="firstRow"><w:rPr>{_rfonts(SEMIBOLD)}</w:rPr></w:tblStylePr>
</w:style>'''))


def build_numbering(doc) -> None:
    """An en-dash bullet and a decimal list, defined here rather than inherited.

    Each level names Plex for its marker; without it Word sets the tab after the
    number in Arial, the one non-Plex run a rendered brief would otherwise have."""
    numbering = doc.part.numbering_part.element
    bullet = "".join(
        f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
        f'<w:lvlText w:val="–"/><w:lvlJc w:val="left"/>'
        f'<w:pPr><w:ind w:left="{280 * (i + 1)}" w:hanging="280"/></w:pPr>'
        f'<w:rPr>{_rfonts(SANS)}</w:rPr></w:lvl>'
        for i in range(3))
    decimal = "".join(
        f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/>'
        f'<w:lvlText w:val="%{i + 1}."/><w:lvlJc w:val="left"/>'
        f'<w:pPr><w:ind w:left="{360 * (i + 1)}" w:hanging="360"/></w:pPr>'
        f'<w:rPr>{_rfonts(SANS)}</w:rPr></w:lvl>'
        for i, fmt in enumerate(("decimal", "lowerLetter", "lowerRoman")))
    for aid, lvls in ((900, bullet), (901, decimal)):
        numbering.append(_xml(
            f'<w:abstractNum {W} w:abstractNumId="{aid}">'
            f'<w:multiLevelType w:val="hybridMultilevel"/>{lvls}</w:abstractNum>'))
    numbering.append(_xml(f'<w:num {W} w:numId="900"><w:abstractNumId w:val="900"/></w:num>'))


def build_page(doc) -> None:
    s = doc.sections[0]
    s.page_width, s.page_height = Twips(PG_W), Twips(PG_H)
    s.top_margin, s.bottom_margin = Twips(MAR_TOP), Twips(MAR_BOT)
    s.left_margin, s.right_margin = Twips(MAR_LEFT), Twips(MAR_RIGHT)
    s.header_distance, s.footer_distance = Twips(HDR_DIST), Twips(FTR_DIST)


def _font_signature(path: str) -> str:
    """The fontTable metadata Word measures a family by: panose, charset, family,
    pitch and the Unicode and code-page ranges. Without it Word guesses the
    family's widths and sets it wider than it is."""
    from fontTools.ttLib import TTFont
    os2 = TTFont(path)["OS/2"]
    p = os2.panose
    panose = "".join(f"{v:02X}" for v in (p.bFamilyType, p.bSerifStyle, p.bWeight, p.bProportion,
                                          p.bContrast, p.bStrokeVariation, p.bArmStyle,
                                          p.bLetterForm, p.bMidline, p.bXHeight))
    family = "roman" if p.bSerifStyle not in (0, 1, 11, 12, 13) else "swiss"
    return (f'<w:panose1 w:val="{panose}"/><w:charset w:val="00"/>'
            f'<w:family w:val="{family}"/><w:pitch w:val="variable"/>'
            f'<w:sig w:usb0="{os2.ulUnicodeRange1:08X}" w:usb1="{os2.ulUnicodeRange2:08X}"'
            f' w:usb2="{os2.ulUnicodeRange3:08X}" w:usb3="{os2.ulUnicodeRange4:08X}"'
            f' w:csb0="{os2.ulCodePageRange1:08X}" w:csb1="{os2.ulCodePageRange2:08X}"/>')


def embed_fonts(path: str) -> None:
    """Embed the Plex faces into the saved package.

    A reader on Windows almost certainly lacks Plex, and Word substitutes another
    face for one it cannot resolve. The embedded copies are what make the brief
    arrive in Plex. Plex is OFL 1.1, which permits embedding; the licence travels
    in fonts/OFL.txt. Word for Mac ignores embedded fonts and resolves by name, so
    on a Mac the brief needs Plex installed to render as designed.

    python-docx has no API for font parts, so this reopens the zip and adds the
    TTFs, a relationship each from fontTable.xml, the w:font entries that point at
    them, and w:embedTrueTypeFonts in settings.xml."""
    if not all(os.path.exists(os.path.join(FONTS, f)) for _, _, f in EMBEDDED):
        print("  fonts/ incomplete, skipping embed")
        return
    families: dict[str, list[tuple[int, str, str]]] = {}
    for i, (family, slot, filename) in enumerate(EMBEDDED, 1):
        families.setdefault(family, []).append((i, slot, filename))

    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "[Content_Types].xml":
                text = data.decode("utf-8")
                if 'Extension="ttf"' not in text:
                    text = text.replace("</Types>", '<Default Extension="ttf" ContentType='
                                        '"application/x-font-ttf"/></Types>')
                data = text.encode("utf-8")
            elif item.filename == "word/fontTable.xml":
                text = data.decode("utf-8")
                for family, faces in families.items():
                    regular = os.path.join(FONTS, faces[0][2])
                    rels = "".join(
                        f'<{slot} r:id="rIdFont{i}" w:fontKey='
                        f'"{{00000000-0000-0000-0000-000000000000}}" w:subsetted="0"/>'
                        for i, slot, _ in faces)
                    el = f'<w:font w:name="{family}">{_font_signature(regular)}{rels}</w:font>'
                    pattern = re.compile(rf'<w:font w:name="{re.escape(family)}"\s*/>'
                                         rf'|<w:font w:name="{re.escape(family)}">.*?</w:font>', re.S)
                    text = (pattern.sub(el, text) if pattern.search(text)
                            else text.replace("</w:fonts>", el + "</w:fonts>"))
                data = text.encode("utf-8")
            elif item.filename == "word/theme/theme1.xml":
                # Anything that falls through to the theme font lands in Plex
                # rather than Calibri or Cambria.
                text = re.sub(r'(<a:(?:major|minor)Font>\s*<a:latin[^>]*?typeface=")[^"]*"',
                              lambda m: m.group(1) + SANS + '"', data.decode("utf-8"))
                data = text.encode("utf-8")
            elif item.filename == "word/settings.xml":
                text = data.decode("utf-8")
                if "<w:embedTrueTypeFonts" not in text:
                    text = re.sub(r"(<w:settings[^>]*>)", r"\1<w:embedTrueTypeFonts/>", text, count=1)
                data = text.encode("utf-8")
            dst.writestr(item, data)

        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
        for i, (_, _, filename) in enumerate(EMBEDDED, 1):
            rels.append(f'<Relationship Id="rIdFont{i}" Type="http://schemas.openxmlformats.org'
                        f'/officeDocument/2006/relationships/font" Target="fonts/{filename}"/>')
            dst.write(os.path.join(FONTS, filename), f"word/fonts/{filename}")
        rels.append("</Relationships>")
        dst.writestr("word/_rels/fontTable.xml.rels", "".join(rels))
    shutil.move(tmp, path)


def write_metrics() -> None:
    """Emit font_metrics.py: advance widths for the faces the builder has to fit.

    The cover title's size, the line count of a subtitle and the width of a
    button all depend on how wide the text sets, so they are computed from the
    shipped fonts rather than guessed."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("  fonttools not installed, keeping existing font_metrics.py")
        return
    faces = {"light": "IBMPlexSans-Light.ttf", "regular": "IBMPlexSans-Regular.ttf",
             "semibold": "IBMPlexSans-SemiBold.ttf", "serif": "IBMPlexSerif-Regular.ttf"}
    chars = [chr(c) for c in range(32, 127)] + list("–—‘’“”…"
                                                     "↑→↓®™© ")
    lines = ['"""Advance widths for the faces the brief is set in, in font units.', "",
             "Generated by build_template.py; do not edit. Regenerate after refreshing fonts/.",
             '"""', "", "UNITS_PER_EM = 1000", ""]
    for key, filename in faces.items():
        font = TTFont(os.path.join(FONTS, filename))
        assert font["head"].unitsPerEm == 1000, filename
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        lines.append(f"{key.upper()} = {{")
        for c in chars:
            if ord(c) in cmap:
                lines.append(f"    {c!r}: {hmtx[cmap[ord(c)]][0]},")
        lines += ["}", ""]
    with open(os.path.join(HERE, "font_metrics.py"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"  wrote font_metrics.py ({len(faces)} faces)")


def build(out_path: str) -> str:
    doc = Document()
    set_doc_defaults(doc)
    build_styles(doc)
    build_numbering(doc)
    build_page(doc)
    props = doc.core_properties
    props.title = ""
    props.author = "IBM"
    props.last_modified_by = "IBM"
    props.category = "IBM solution brief template"
    props.comments = "Built by ibm-brief-docx/assets/build_template.py"
    doc.save(out_path)
    embed_fonts(out_path)
    write_metrics()
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=os.path.join(HERE, "ibm-brief-template.docx"))
    path = build(ap.parse_args().out)
    print(f"wrote {path} ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    main()
