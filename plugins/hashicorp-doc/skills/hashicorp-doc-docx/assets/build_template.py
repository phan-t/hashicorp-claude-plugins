#!/usr/bin/env python3
"""Regenerate hashicorp-doc-template.docx.

The template is built on python-docx's own empty package and then restyled. It
is not derived from any real document, so it carries no customer content, no
revision ids, no comments and no author names. Every measurement here came off
the reference assessment report; references/design-system.md says what each one
is and why.

    pip install python-docx
    python3 build_template.py [-o hashicorp-doc-template.docx]

Run this after changing a style, a margin or the page geometry. Nothing else in
the skill sets a font, a size or a colour -- they all resolve from here.
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
from docx.shared import Emu, Pt, RGBColor, Twips

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "media")
FONTS = os.path.join(HERE, "fonts")

# Faces embedded in the template, and the fontTable element that declares each.
# Read off Inter-Regular's OS/2 table. Word uses these to resolve and measure the
# family; see embed_fonts().
FONT_METRICS = (
    '<w:panose1 w:val="02000503000000020004"/>'
    '<w:charset w:val="00"/>'
    '<w:family w:val="swiss"/>'
    '<w:pitch w:val="variable"/>'
    '<w:sig w:usb0="E0000AFF" w:usb1="5200A1FF" w:usb2="00000021" w:usb3="00000000"'
    ' w:csb0="0000019F" w:csb1="00000000"/>'
)

EMBEDDED = [
    ("w:embedRegular", "Inter-Regular.ttf"),
    ("w:embedBold", "Inter-Bold.ttf"),
    ("w:embedItalic", "Inter-Italic.ttf"),
    ("w:embedBoldItalic", "Inter-BoldItalic.ttf"),
]

# --- Page geometry, in twips (1/20 pt) ---------------------------------------
PG_W, PG_H = 12240, 15840          # US Letter, portrait
MAR_TOP, MAR_BOT = 1872, 1512
MAR_LEFT, MAR_RIGHT = 1612, 1987   # asymmetric: a 6.00in measure, set left
HDR_DIST, FTR_DIST = 763, 432
TEXT_W = PG_W - MAR_LEFT - MAR_RIGHT   # 8641 twips = 6.00in

# --- Type --------------------------------------------------------------------
# Verified against Word for Mac by rendering a probe document, not assumed.
# "Helvetica Neue" -- the reference's face -- is the one name in this list that
# Word refuses, substituting a serif, even though macOS ships and enables it.
# The reference got away with it by embedding the font; this template does not
# embed, so it names faces Word actually resolves.
BODY_FONT = "Inter"                # HashiCorp CY26; matches deck and page skills
LIGHT_FONT = "Inter Light"         # resolves; "Inter Regular" and "Inter Variable" do not
META_FONT = "Arial"                # the reference's; kept because everyone has it
MONO_FONT = "Consolas"             # Microsoft Office installs it on macOS and Windows

BODY_PT = 10          # w:sz 20
LINE = 1.45           # w:line 348, auto
HEAD_LINE = 1.10      # w:line 264, auto

# Numbering. High ids so nothing in python-docx's stock numbering.xml collides.
BULLET_ABSTRACT, DECIMAL_ABSTRACT = 900, 901
BULLET_NUM = 900

RULE = "000000"                       # table rules
SHADE = "F3F3F3"                      # zebra band
MUTED = RGBColor(0x66, 0x66, 0x66)    # captions and quiet headings
LINK = RGBColor(0x11, 0x55, 0xCC)

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _xml(fragment: str):
    """Parse a w:-namespaced OOXML fragment."""
    return parse_xml(fragment)


def _rfonts(name: str) -> str:
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:eastAsia="{name}" w:cs="{name}"/>'


def set_doc_defaults(doc) -> None:
    """The font, size and paragraph spacing everything else inherits."""
    styles = doc.styles.element
    for old in styles.findall(qn("w:docDefaults")):
        styles.remove(old)
    styles.insert(0, _xml(
        f'<w:docDefaults {W}>'
        f'<w:rPrDefault><w:rPr>{_rfonts(BODY_FONT)}'
        f'<w:sz w:val="{BODY_PT * 2}"/><w:szCs w:val="{BODY_PT * 2}"/></w:rPr></w:rPrDefault>'
        f'<w:pPrDefault><w:pPr>'
        f'<w:spacing w:after="200" w:line="{int(LINE * 240)}" w:lineRule="auto"/>'
        f'</w:pPr></w:pPrDefault>'
        f'</w:docDefaults>'))


def add(doc, name: str, kind=WD_STYLE_TYPE.PARAGRAPH):
    """Fetch a style by name, creating it if the stock template has none."""
    try:
        return doc.styles[name]
    except KeyError:
        return doc.styles.add_style(name, kind)


def restyle(style, *, size_pt=None, bold=None, italic=None, font=None, color=None,
            space_before=None, space_after=None, line=None, left_indent=None,
            right_indent=None, keep_next=False, keep_together=False):
    """Clear a style and set only what we mean.

    Word's stock heading styles carry theme fonts and accent colours. Dropping
    rPr and pPr first is what stops those leaking into a HashiCorp document."""
    el = style.element
    for tag in ("w:rPr", "w:pPr"):
        for node in el.findall(qn(tag)):
            el.remove(node)

    f = style.font
    if font:
        f.name = font
    if size_pt is not None:
        f.size = Pt(size_pt)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color

    if style.type == WD_STYLE_TYPE.CHARACTER:
        return style

    pf = style.paragraph_format
    if space_before is not None:
        pf.space_before = Twips(space_before)
    if space_after is not None:
        pf.space_after = Twips(space_after)
    if line is not None:
        pf.line_spacing = line
    if left_indent is not None:
        pf.left_indent = Twips(left_indent)
    if right_indent is not None:
        pf.right_indent = Twips(right_indent)
    if keep_next:
        pf.keep_with_next = True
    if keep_together:
        pf.keep_together = True
    return style


def build_styles(doc) -> None:
    normal = restyle(doc.styles["Normal"])

    # Headings, at the reference's sizes: 26 / 16 / 12 / 12 / 11 / 10 pt.
    heads = [
        ("Heading 1", 26, 0, 520, True, None),
        ("Heading 2", 16, 600, 240, True, None),
        ("Heading 3", 12, 280, 160, True, None),
        ("Heading 4", 12, 280, 80, True, None),
        ("Heading 5", 11, 240, 80, False, MUTED),
        ("Heading 6", 10, 200, 120, False, MUTED),
    ]
    for name, pt, before, after, bold, color in heads:
        s = restyle(add(doc, name), size_pt=pt, bold=bold, color=color,
                    space_before=before, space_after=after, line=HEAD_LINE,
                    keep_next=True, keep_together=True)
        s.next_paragraph_style = normal

    restyle(add(doc, "Title"), size_pt=40, bold=True, space_after=0, line=1.0,
            right_indent=-90, keep_next=True,
            keep_together=True).next_paragraph_style = normal
    restyle(add(doc, "Subtitle"), size_pt=24, bold=False, font=LIGHT_FONT,
            space_after=0, line=2.0, right_indent=-90, keep_next=True,
            keep_together=True).next_paragraph_style = normal

    restyle(add(doc, "Cover Meta"), font=META_FONT, size_pt=11,
            space_after=0, line=1.0).next_paragraph_style = normal
    restyle(add(doc, "Contents Heading"), size_pt=14, bold=True, space_after=240,
            line=HEAD_LINE, keep_next=True).next_paragraph_style = normal
    restyle(add(doc, "Colophon"), space_after=280, line=1.15).next_paragraph_style = normal
    restyle(add(doc, "Caption"), size_pt=9, color=MUTED, bold=False, italic=False,
            space_before=80, space_after=240, line=1.0).next_paragraph_style = normal

    lp = restyle(add(doc, "List Paragraph"), space_after=0, left_indent=720)
    lp.paragraph_format.first_line_indent = Twips(-360)
    lp.element.get_or_add_pPr().append(_xml(f"<w:contextualSpacing {W}/>"))

    restyle(add(doc, "Code", WD_STYLE_TYPE.CHARACTER), font=MONO_FONT, bold=True)

    link = add(doc, "Hyperlink", WD_STYLE_TYPE.CHARACTER)
    link.font.color.rgb = LINK
    link.font.underline = True

    # Word rebuilds the contents field with these, so they have to look like
    # what the field first rendered: bold at level 1, indented below it.
    for level, (bold, indent) in enumerate([(True, 0), (False, 360), (False, 720)], 1):
        s = restyle(add(doc, f"TOC {level}"), bold=bold, space_before=60,
                    space_after=0, line=1.0, left_indent=indent)
        s.next_paragraph_style = normal
        s.priority = 39
        # get_or_add_tabs places w:tabs where the schema wants it; appending to
        # pPr would put it after w:spacing, which is out of order.
        s.element.get_or_add_pPr().get_or_add_tabs().append(
            _xml(f'<w:tab {W} w:val="right" w:pos="{TEXT_W}"/>'))
        # Word matches TOC levels on the internal name, not the UI one, and it
        # ignores a style flagged w:customStyle when it rebuilds the field.
        s.element.find(qn("w:name")).set(qn("w:val"), f"toc {level}")
        s.element.attrib.pop(qn("w:customStyle"), None)

    build_table_style(doc)


def build_table_style(doc) -> None:
    """The one thing python-docx cannot express: conditional row formatting.

    A heavy rule above the header row and below the last row, no verticals, and
    every other body row banded. Nothing else in the skill draws a border."""
    styles = doc.styles.element
    for s in styles.findall(qn("w:style")):
        if s.get(qn("w:styleId")) == "HashiCorpTable":
            styles.remove(s)
    styles.append(_xml(f'''<w:style {W} w:type="table" w:styleId="HashiCorpTable">
<w:name w:val="HashiCorp Table"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/>
<w:tblPr><w:tblStyleRowBandSize w:val="1"/>
  <w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/>
    <w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>
  <w:tblCellMar><w:top w:w="99" w:type="dxa"/><w:left w:w="99" w:type="dxa"/>
    <w:bottom w:w="99" w:type="dxa"/><w:right w:w="99" w:type="dxa"/></w:tblCellMar></w:tblPr>
<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:bCs/></w:rPr>
  <w:tcPr><w:tcBorders><w:top w:val="single" w:sz="12" w:space="0" w:color="{RULE}"/>
    <w:bottom w:val="nil"/></w:tcBorders></w:tcPr></w:tblStylePr>
<w:tblStylePr w:type="lastRow">
  <w:tcPr><w:tcBorders><w:bottom w:val="single" w:sz="12" w:space="0" w:color="{RULE}"/>
    </w:tcBorders></w:tcPr></w:tblStylePr>
<w:tblStylePr w:type="band1Horz">
  <w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{SHADE}"/></w:tcPr></w:tblStylePr>
</w:style>'''))


def build_numbering(doc) -> None:
    """Bullets and numbers, defined here rather than inherited from whatever
    python-docx's stock numbering.xml happens to hold.

    Bullet glyphs are the reference's: filled round, hollow round, filled square,
    repeating. Every level indents 0.5in with a 0.25in hang."""
    numbering = doc.part.numbering_part.element

    def levels(specs):
        """One w:lvl per entry. `%N` in a label becomes Word's placeholder for
        this level's own counter -- `%1` at ilvl 0, `%2` at ilvl 1, and so on.
        Writing the bare digit instead renders every item as "1."."""
        out = []
        for i, (fmt, label, jc) in enumerate(specs):
            out.append(
                f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/>'
                f'<w:lvlText w:val="{label.replace("%N", f"%{i + 1}")}"/>'
                f'<w:lvlJc w:val="{jc}"/>'
                f'<w:pPr><w:ind w:left="{720 * (i + 1)}" w:hanging="360"/></w:pPr></w:lvl>')
        return "".join(out)

    bullets = levels([("bullet", g, "left") for g in "\u25cf\u25cb\u25a0" * 3])
    numbers = levels([spec for _ in range(3) for spec in (
        ("decimal", "%N.", "left"),
        ("lowerLetter", "%N.", "left"),
        ("lowerRoman", "%N.", "right"))])

    for abstract_id, lvls in ((BULLET_ABSTRACT, bullets), (DECIMAL_ABSTRACT, numbers)):
        numbering.append(_xml(
            f'<w:abstractNum {W} w:abstractNumId="{abstract_id}">'
            f'<w:multiLevelType w:val="hybridMultilevel"/>{lvls}</w:abstractNum>'))
    numbering.append(_xml(
        f'<w:num {W} w:numId="{BULLET_NUM}">'
        f'<w:abstractNumId w:val="{BULLET_ABSTRACT}"/></w:num>'))


def build_page(doc) -> None:
    """Letter portrait, a 6in measure set left, and the cover's wordmark footer."""
    s = doc.sections[0]
    s.page_width, s.page_height = Twips(PG_W), Twips(PG_H)
    s.top_margin, s.bottom_margin = Twips(MAR_TOP), Twips(MAR_BOT)
    s.left_margin, s.right_margin = Twips(MAR_LEFT), Twips(MAR_RIGHT)
    s.header_distance, s.footer_distance = Twips(HDR_DIST), Twips(FTR_DIST)
    s.different_first_page_header_footer = True

    # Page 1 gets the wordmark. The running header starts in the body section,
    # which hashicorp_doc.Doc opens at the first h1().
    footer = s.first_page_footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(0)
    # The source PNG carries ~3.8% padding on its left edge; pull it back so the
    # mark aligns to the left margin instead of floating off it.
    p.paragraph_format.left_indent = Emu(-71000)
    p.add_run().add_picture(os.path.join(MEDIA, "hashicorp-wordmark.png"),
                            width=Emu(1866000))


def embed_fonts(path: str) -> None:
    """Embed Inter into the saved package.

    A Windows reader almost certainly does not have Inter, and Word substitutes a
    serif for a face it cannot resolve. An embedded copy is what stops the
    customer -- the person this document is actually for -- seeing the wrong
    document. Inter is OFL 1.1, which explicitly permits embedding; the licence
    travels in fonts/OFL.txt.

    Word for Mac ignores embedded fonts, so this cannot be verified by rendering
    here; it is for the Windows reader.

    python-docx has no API for font parts, so this reopens the saved zip and adds
    them: four TTFs, a relationship each from fontTable.xml, the w:font entries
    that point at them, and w:embedTrueTypeFonts in settings.xml."""
    if not all(os.path.exists(os.path.join(FONTS, f)) for _, f in EMBEDDED):
        print("  fonts/ incomplete, skipping embed")
        return

    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)

            if item.filename == "[Content_Types].xml":
                text = data.decode("utf-8")
                if 'Extension="ttf"' not in text:
                    text = text.replace(
                        "<Types ", '<Types ', 1).replace(
                        "</Types>",
                        '<Default Extension="ttf" ContentType='
                        '"application/x-font-ttf"/></Types>')
                data = text.encode("utf-8")

            elif item.filename == "word/fontTable.xml":
                rels = "".join(
                    f'<{tag} r:id="rIdFont{i}" w:fontKey='
                    f'"{{00000000-0000-0000-0000-000000000000}}" w:subsetted="0"/>'
                    for i, (tag, _) in enumerate(EMBEDDED, 1))
                # The metadata matters as much as the embed: without panose,
                # charset, family and pitch Word measures the family by guess and
                # sets it wider, which breaks table columns that fitted before.
                font_el = (f'<w:font w:name="{BODY_FONT}">'
                           f'{FONT_METRICS}{rels}</w:font>')
                text = data.decode("utf-8")
                # Replace any existing declaration for this family, else append.
                pattern = re.compile(
                    rf'<w:font w:name="{re.escape(BODY_FONT)}"\s*/>'
                    rf'|<w:font w:name="{re.escape(BODY_FONT)}">.*?</w:font>', re.S)
                text = (pattern.sub(font_el, text) if pattern.search(text)
                        else text.replace("</w:fonts>", font_el + "</w:fonts>"))
                data = text.encode("utf-8")

            elif item.filename == "word/theme/theme1.xml":
                # Word rebuilds the contents field using the theme's fonts, not
                # the TOC styles', so a stock theme sets the contents in Cambria
                # however carefully those styles are defined. Point the theme at
                # the body font and nothing can fall through to a serif.
                text = data.decode("utf-8")
                text = re.sub(
                    r'(<a:(?:major|minor)Font>\s*<a:latin[^>]*?typeface=")[^"]*"',
                    lambda m: m.group(1) + BODY_FONT + '"', text)
                data = text.encode("utf-8")

            elif item.filename == "word/settings.xml":
                text = data.decode("utf-8")
                if "<w:embedTrueTypeFonts" not in text:
                    # First child of w:settings, which is where the schema wants it.
                    text = re.sub(r"(<w:settings[^>]*>)", r"\1<w:embedTrueTypeFonts/>",
                                  text, count=1)
                data = text.encode("utf-8")

            dst.writestr(item, data)

        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/'
                'package/2006/relationships">']
        for i, (_, filename) in enumerate(EMBEDDED, 1):
            rels.append(
                f'<Relationship Id="rIdFont{i}" Type="http://schemas.openxmlformats.org'
                f'/officeDocument/2006/relationships/font" Target="fonts/{filename}"/>')
            dst.write(os.path.join(FONTS, filename), f"word/fonts/{filename}")
        rels.append("</Relationships>")
        dst.writestr("word/_rels/fontTable.xml.rels", "".join(rels))

    shutil.move(tmp, path)


def write_metrics(path: str) -> None:
    """Emit font_metrics.py: real advance widths for the embedded body font.

    Everything that has to predict whether text fits -- a table column, a cover
    title's line count -- was previously guessing with an average character
    width. It guessed against whatever face Word happened to substitute, which
    was never the one in the document. These are the actual numbers, read off the
    files that ship inside the template."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("  fonttools not installed, keeping existing font_metrics.py")
        return

    faces = {"regular": "Inter-Regular.ttf", "bold": "Inter-Bold.ttf"}
    if not all(os.path.exists(os.path.join(FONTS, f)) for f in faces.values()):
        print("  fonts/ incomplete, keeping existing font_metrics.py")
        return

    printable = [chr(c) for c in range(32, 127)]
    tables, line_ratio, upm = {}, None, None
    for key, filename in faces.items():
        font = TTFont(os.path.join(FONTS, filename))
        upm = font["head"].unitsPerEm
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        tables[key] = {c: hmtx[cmap[ord(c)]][0] for c in printable if ord(c) in cmap}
        if key == "regular":
            hhea = font["hhea"]
            line_ratio = (hhea.ascent - hhea.descent + hhea.lineGap) / upm

    lines = [
        '"""Advance widths for the template\'s body font, in font units.',
        "",
        "Generated by build_template.py -- do not edit. Regenerate after changing",
        "BODY_FONT or refreshing the files in fonts/.",
        '"""',
        "",
        f"FONT = {BODY_FONT!r}",
        f"UNITS_PER_EM = {upm}",
        f"# Word's single line height as a multiple of the point size.",
        f"LINE_RATIO = {line_ratio:.4f}",
        "",
    ]
    for key in ("regular", "bold"):
        lines.append(f"{key.upper()} = {{")
        for c in printable:
            if c in tables[key]:
                lines.append(f"    {c!r}: {tables[key][c]},")
        lines.append("}")
        lines.append("")
    out = os.path.join(HERE, "font_metrics.py")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"  wrote font_metrics.py ({len(printable)} glyphs, line ratio {line_ratio:.4f})")


def build(out_path: str) -> str:
    doc = Document()
    set_doc_defaults(doc)
    build_styles(doc)
    build_numbering(doc)
    build_page(doc)

    props = doc.core_properties
    props.title = ""
    props.author = "HashiCorp"
    props.last_modified_by = "HashiCorp"
    props.category = "HashiCorp document template"
    props.comments = "Built by hashicorp-doc-docx/assets/build_template.py"

    doc.save(out_path)
    embed_fonts(out_path)
    write_metrics(out_path)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=os.path.join(HERE, "hashicorp-doc-template.docx"))
    args = ap.parse_args()
    path = build(args.out)
    print(f"wrote {path} ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    main()
