"""ibm_deck — build IBM-branded .pptx slides on the official IBM template.

This is a thin wrapper over python-pptx. It does NOT restyle anything: every
slide is created from a named layout in `ibm-brand-template.pptx` (the official
IBM presentation template v2.0 Plex, stripped to master + layouts + theme), and
only placeholder *text* is filled. IBM Plex, the Carbon palette and all geometry
are inherited from the template, which is what keeps decks on-brand.

    from ibm_deck import Deck
    d = Deck(footer="Platform engineering")
    d.cover("Why we rebuilt the deploy path", label="Point of view",
            meta=["Tony Phan", "August 2026"])
    d.section("The problem")
    d.columns("What changed", [["**Self-service** — teams ship without a queue."],
                               ["**Guardrails** — policy runs in CI, not review."]])
    d.save("deck.pptx")

Never set fonts, colors or positions from calling code. If a slide needs a shape
the template does not provide, add a layout-driven slide and place the extra
shape relative to `Deck.GRID`. Requires: python-pptx.
"""

import copy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree  # noqa: F401
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

TEMPLATE = Path(__file__).with_name("ibm-brand-template.pptx")

# Friendly key -> exact layout name in the IBM template. Trailing spaces in some
# names are IBM's, not a typo; matching is whitespace-insensitive below.
LAYOUTS = {
    "cover_image": "Cover, imagery",
    "cover_cyan": "Cover, cyan",
    "cover": "Cover, plain",
    "cover_label": "Cover, plain, label",
    "cover_image_half": "Cover, imagery, half",
    "cover_image_half_label": "Cover, imagery, half, label",
    "contents": "Contents",
    "section": "Section divider",
    "statement": "Large text",
    "callout": "Callout, headline",
    "quote": "Callout, stand-alone",
    "data_2_v": "Data, 2 callouts, vertical",
    "data_3_v": "Data, 3 callouts, vertical",
    "data_2": "Data, 2 callouts, horizontal",
    "data_3": "Data, 3 callouts, horizontal",
    "cols_4": "Text, 4 columns",
    "cols_4_div": "Text, 4 columns, short dividers",
    "cols_4_head": "Text, 4 columns, dividers, headlines",
    "cols_1": "Text, 1 wide column, divider",
    "cols_2_wide": "Text, 2 wide columns",
    "cols_2_large": "Text, 2 columns, large title",
    "cols_2": "Text, 2 columns, small title",
    "cols_2_div_large": "Text, 2 columns, dividers, large title",
    "cols_2_div": "Text, 2 columns, dividers, small title",
    "boxes_4": "Boxes, 4 stacked, small title",
    "boxes_4_h": "Boxes, 4 horizontal, small title",
    "boxes_6": "Boxes, 6 stacked",
    "image_half": "Video or imagery, half, inset",
    "image_bleed": "Video or imagery, 3/4, bleed",
    "image_inset": "Video or imagery, 3/4, inset",
    "image_full": "Video or imagery, bleed",
    "contacts": "Contacts, profiles, contributors",
    "table": "Table",
    "chart": "Chart",
    "blank": "Blank slide",
    "blank_bare": "Blank slide, no footer",
    "end": "End slide",
}

# Carbon tokens, only for shapes the template has no placeholder for (code panels).
GRAY_10 = RGBColor.from_string("F4F4F4")
GRAY_20 = RGBColor.from_string("E0E0E0")
GRAY_60 = RGBColor.from_string("6F6F6F")
GRAY_90 = RGBColor.from_string("262626")
GRAY_100 = RGBColor.from_string("161616")
BLUE_60 = RGBColor.from_string("0F62FE")
FONT_MONO = "IBM Plex Mono"


# IBM's reference table (template slide 51) does not get its look from the table
# style: tableStyles.xml only defines PowerPoint's generic blue "Medium Style 2 -
# Accent 1". Every cell instead carries explicit formatting — no fill, no vertical
# rules, a horizontal rule above and below, and 0.2 in top/bottom margins. Without
# this a generated table renders blue-banded and boxed, nothing like the template.
_CELL_MARGIN = 182880          # 0.2 in, in EMU
_RULE_W = 12700                # 1 pt



def _border(parent, name, solid):
    el = parent.makeelement(qn("a:" + name), {"w": str(_RULE_W), "cap": "flat",
                                              "cmpd": "sng", "algn": "ctr"})
    if solid:
        fill = el.makeelement(qn("a:solidFill"), {})
        clr = el.makeelement(qn("a:schemeClr"), {"val": "tx1"})
        fill.append(clr)
        el.append(fill)
    else:
        el.append(el.makeelement(qn("a:noFill"), {}))
    el.append(el.makeelement(qn("a:prstDash"), {"val": "solid"}))
    el.append(el.makeelement(qn("a:round"), {}))
    parent.append(el)
    return el


def style_cell(cell, is_header=False):
    """Stamp IBM's cell formatting onto one table cell."""
    tc = cell._tc
    old = tc.find(qn("a:tcPr"))
    if old is not None:
        tc.remove(old)
    pr = tc.makeelement(qn("a:tcPr"), {"marT": str(_CELL_MARGIN),
                                       "marB": str(_CELL_MARGIN)})
    _border(pr, "lnL", False)                 # no vertical rules
    _border(pr, "lnR", False)
    _border(pr, "lnT", not is_header)         # header has a rule below only
    _border(pr, "lnB", True)
    pr.append(pr.makeelement(qn("a:noFill"), {}))   # transparent, no banding
    tc.append(pr)
    return cell


class Deck:
    """An IBM-template presentation. Each method appends one slide and returns it."""

    #: template canvas, in inches — IBM ships a 26.67 x 15.0 in (16:9) stage
    GRID = {"margin": Inches(0.63), "col": Inches(6.67), "gutter": Inches(0.63)}

    def __init__(self, template=None, footer=None):
        self.prs = Presentation(str(template or TEMPLATE))
        self.footer = footer
        self._layouts = {self._key(l.name): l for l in self.prs.slide_layouts}

    @staticmethod
    def _key(name):
        return " ".join(name.split()).lower()

    def layout(self, key):
        """Resolve a friendly key (or an exact IBM layout name) to a layout."""
        name = LAYOUTS.get(key, key)
        try:
            return self._layouts[self._key(name)]
        except KeyError:
            raise KeyError(
                f"no layout {name!r} in the template; known keys: "
                + ", ".join(sorted(LAYOUTS))
            ) from None

    # -- low level -------------------------------------------------------------
    def add(self, key, notes=None):
        """Add a slide from a layout, with footer and slide number restored.

        python-pptx clones only title/body placeholders, so the footer and the
        slide-number field are deep-copied from the layout to keep the running
        chrome IBM's template defines.
        """
        layout = self.layout(key)
        slide = self.prs.slides.add_slide(layout)
        tree = slide.shapes._spTree
        for lph in layout.placeholders:
            kind = str(lph.placeholder_format.type).split()[0]
            if kind in ("FOOTER", "SLIDE_NUMBER"):
                tree.append(copy.deepcopy(lph._element))
        if self.footer:
            self.set_text(self.ph(slide, "FOOTER"), self.footer)
        if notes:
            slide.notes_slide.notes_text_frame.text = notes
        return slide

    @staticmethod
    def ph(slide, ref):
        """Placeholder by idx (int) or by type name ('FOOTER', 'PICTURE', ...)."""
        for p in slide.placeholders:
            f = p.placeholder_format
            if (isinstance(ref, int) and f.idx == ref) or (
                isinstance(ref, str) and str(f.type).split()[0] == ref
            ):
                return p
        return None

    @staticmethod
    def bodies(slide):
        """Body placeholders in IBM's reading order: top to bottom, left to right."""
        out = [
            p
            for p in slide.placeholders
            if str(p.placeholder_format.type).split()[0] == "BODY"
        ]
        return sorted(out, key=lambda p: (round(p.top / 100000), round(p.left / 100000)))

    @classmethod
    def split_bodies(cls, slide):
        """Separate short heading slots from full-height column slots.

        IBM's "dividers" layouts pair a ~2in heading placeholder above each ~10in
        column. Height is the reliable discriminator — order and vertical position
        are not, since the plain 2-column layouts put full-height columns at the
        same y as the divider layouts put headings.
        """
        bodies = cls.bodies(slide)
        heads = [b for b in bodies if b.height < Inches(5)]
        cols = [b for b in bodies if b.height >= Inches(5)]
        return heads, cols

    @classmethod
    def set_text(cls, placeholder, content):
        """Fill a placeholder. `content` is a string or a list of paragraphs.

        Inline `**bold**` is honoured. Formatting is otherwise left to inherit
        from the layout, so text lands in IBM Plex at the template's sizes.
        """
        if placeholder is None or content is None:
            return None
        paras = [content] if isinstance(content, str) else list(content)
        tf = placeholder.text_frame
        tf.clear()
        for i, text in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            for chunk, bold in _split_bold(str(text)):
                if not chunk:
                    continue
                r = p.add_run()
                r.text = chunk
                if bold:
                    r.font.bold = True
        return placeholder

    @staticmethod
    def drop_empty(slide):
        """Remove placeholders left unfilled, so no prompt text ships in the deck."""
        for p in list(slide.placeholders):
            kind = str(p.placeholder_format.type).split()[0]
            if kind in ("SLIDE_NUMBER", "FOOTER"):
                continue
            if p.has_text_frame and not p.text_frame.text.strip():
                p._element.getparent().remove(p._element)

    # -- slide types -----------------------------------------------------------
    def cover(self, title, label=None, meta=None, image=None, style=None, notes=None):
        """Opening slide. `label` is a kicker, `meta` short lines (presenter, date).

        The plain covers carry fewer text slots than the imagery ones, so any
        lines that do not fit are merged into the last slot rather than dropped.
        Pass `style` (e.g. "cover_cyan") to force a particular IBM cover.
        """
        lines = ([label] if label else []) + list(meta or [])
        if style:
            key = style
        elif image:
            key = "cover_image_half_label" if label else "cover_image_half"
        else:
            key = "cover_label" if lines else "cover"
        slide = self.add(key, notes)
        self.set_text(slide.shapes.title, title)
        slots = self.bodies(slide)
        if lines and slots:
            for i, slot in enumerate(slots):
                if i >= len(lines):
                    break
                last = i == len(slots) - 1
                self.set_text(slot, "  ·  ".join(lines[i:]) if last else lines[i])
        if image:
            self.place_image(slide, image)
        self.drop_empty(slide)
        return slide

    def contents(self, title, items, notes=None):
        """Agenda. Items are split across the template's two columns."""
        slide = self.add("contents", notes)
        self.set_text(slide.shapes.title, title)
        bodies = self.bodies(slide)
        half = -(-len(items) // 2)
        for body, chunk in zip(bodies, [items[:half], items[half:]]):
            self.set_text(body, chunk)
        self.drop_empty(slide)
        return slide

    def section(self, title, notes=None):
        slide = self.add("section", notes)
        self.set_text(slide.shapes.title, title)
        return slide

    def statement(self, text, notes=None):
        """One large sentence, alone. Use to break rhythm between sections."""
        slide = self.add("statement", notes)
        self.set_text(slide.shapes.title, text)
        return slide

    def quote(self, text, attribution=None, notes=None):
        slide = self.add("quote", notes)
        body = self.bodies(slide)[0]
        self.set_text(body, [text] + ([attribution] if attribution else []))
        return slide

    def callout(self, title, body, notes=None):
        """Headline on the left, supporting prose on the right."""
        slide = self.add("callout", notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.bodies(slide)[0], body)
        self.drop_empty(slide)
        return slide

    def columns(self, title, columns, headings=None, large_title=False, notes=None):
        """1-4 columns of prose, on the IBM layout that fits the shape.

        With `headings`, a "dividers" layout is used so each column gets its own
        heading slot. IBM's 4-column-with-headings layout spends its first column
        on the title, so it holds three headed columns; a fourth is folded in with
        its heading as a bold lead-in rather than dropped.
        """
        columns = [c for c in columns if c][:4]
        n = max(1, len(columns))
        headings = list(headings or [])
        if n == 1:
            key = "cols_1"
        elif n == 2:
            key = ("cols_2_div_large" if large_title else "cols_2_div") if headings \
                else ("cols_2_large" if large_title else "cols_2")
        elif n == 3 and headings:
            key = "cols_4_head"
        else:
            key = "cols_4"
        slide = self.add(key, notes)
        self.set_text(slide.shapes.title, title)
        heads, cols = self.split_bodies(slide)
        if n == 1:
            cols = [max(cols, key=lambda c: c.width)] if cols else []
        if headings and len(heads) < n:
            # not enough heading slots: fold each heading into its column
            columns = [[f"**{h}**"] + list(c) for h, c in zip(headings, columns)]
            headings = []
        for head, heading in zip(heads, headings):
            self.set_text(head, heading)
        for col, content in zip(cols, columns):
            self.set_text(col, content)
        if len(columns) > len(cols):
            raise ValueError(
                f"layout {key!r} has {len(cols)} column slot(s) for {len(columns)} columns"
            )
        self.drop_empty(slide)
        return slide

    #: Which placeholder idx holds the number and which the prose, per data layout.
    #: IBM indexes these inconsistently — the 2-callout layouts spend their title
    #: on the first number, the 3-callout ones keep it as a real headline — so this
    #: is a map, not a heuristic.
    METRIC_SLOTS = {
        "data_2": {"pairs": [(None, 11), (12, 13)], "title": "value"},
        "data_2_v": {"pairs": [(13, 12), (14, 11)], "title": None},
        "data_3": {"pairs": [(15, 12), (16, 13), (17, 14)], "title": "headline", "note": 11},
        "data_3_v": {"pairs": [(15, 12), (16, 13), (17, 14)], "title": "headline", "note": 11},
    }

    def metrics(self, cards, title=None, note=None, key=None, notes=None):
        """Big numbers with supporting prose. `cards` is [(value, prose), ...].

        Picks a 3-callout layout when there is a headline to carry, since the
        2-callout layouts give their title slot to the first number instead.
        """
        cards = list(cards)
        if key is None:
            key = "data_3" if (title or len(cards) > 2) else "data_2"
        spec = self.METRIC_SLOTS[key]
        if len(cards) > len(spec["pairs"]):
            raise ValueError(
                f"layout {key!r} holds {len(spec['pairs'])} callouts, got {len(cards)}"
            )
        if title and spec["title"] != "headline":
            raise ValueError(f"layout {key!r} has no headline slot; drop the title")
        slide = self.add(key, notes)
        if title:
            self.set_text(slide.shapes.title, title)
        for (value_idx, prose_idx), (value, prose) in zip(spec["pairs"], cards):
            target = slide.shapes.title if value_idx is None else self.ph(slide, value_idx)
            self.set_text(target, value)
            self.set_text(self.ph(slide, prose_idx), prose)
        if note and spec.get("note"):
            self.set_text(self.ph(slide, spec["note"]), note)
        self.drop_empty(slide)
        return slide

    def image(self, title, image_path, body=None, style="image_half", notes=None):
        slide = self.add(style, notes)
        if slide.shapes.title is not None:
            self.set_text(slide.shapes.title, title)
        if body:
            bodies = self.bodies(slide)
            if bodies:
                self.set_text(bodies[0], body)
        self.place_image(slide, image_path)
        self.drop_empty(slide)
        return slide

    def place_image(self, slide, image_path):
        """Fill the picture placeholder, cropping to cover rather than stretching."""
        ph = self.ph(slide, "PICTURE")
        if ph is None:
            return None
        box = (ph.left, ph.top, ph.width, ph.height)
        ph._element.getparent().remove(ph._element)
        pic = slide.shapes.add_picture(str(image_path), box[0], box[1])
        scale = max(box[2] / pic.width, box[3] / pic.height)
        pic.width, pic.height = Emu(int(pic.width * scale)), Emu(int(pic.height * scale))
        pic.left = Emu(int(box[0] - (pic.width - box[2]) / 2))
        pic.top = Emu(int(box[1] - (pic.height - box[3]) / 2))
        return pic

    # A table row only needs to be tall enough for its type. Left alone, python-pptx
    # divides the placeholder's full height evenly across the rows, so a short table
    # renders as a few enormous cells with the text marooned in them: six rows in the
    # 12.7 in placeholder gives 2.1 in per row for 0.25 in of text.
    ROW_HEIGHT = Inches(0.8)     # what IBM's own demo tables use
    CELL_PT = Pt(24)             # ditto; 18 pt reads small on a 26.7 in slide

    def table(self, title, rows, notes=None, row_height=None):
        """rows: list of lists; the first row is treated as the header.

        Rows are sized to their content rather than stretched to fill the
        placeholder. Pass row_height to override; tables too tall for the
        placeholder fall back to sharing it evenly.
        """
        slide = self.add("table", notes)
        self.set_text(slide.shapes.title, title)
        ph = self.ph(slide, "TABLE")
        box = (ph.left, ph.top, ph.width, ph.height)
        ph._element.getparent().remove(ph._element)
        n_rows, n_cols = len(rows), max(len(r) for r in rows)
        shape = slide.shapes.add_table(n_rows, n_cols, *box)
        for r, row in enumerate(rows):
            for c in range(n_cols):
                cell = shape.table.cell(r, c)
                cell.text = str(row[c]) if c < len(row) else ""
                style_cell(cell, is_header=(r == 0))
                for p in cell.text_frame.paragraphs:
                    for run in p.runs:
                        run.font.size = self.CELL_PT
        height = row_height or self.ROW_HEIGHT
        if height * n_rows <= ph.height:      # otherwise let it share the box evenly
            for row_obj in shape.table.rows:
                row_obj.height = height
            shape.height = height * n_rows
        self.drop_empty(slide)
        return slide

    def code(self, title, code_text, caption=None, notes=None):
        """Monospace block on a Carbon gray panel. The template has no code layout,
        so this is the one slide type that positions its own shapes."""
        slide = self.add("blank", notes)
        self.set_text(slide.shapes.title, title)
        x, y = Inches(0.63), Inches(3.33)
        w, h = Inches(25.4), Inches(10.0)
        panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        panel.fill.solid()
        panel.fill.fore_color.rgb = GRAY_100
        panel.line.fill.background()
        panel.shadow.inherit = False
        box = slide.shapes.add_textbox(
            Emu(int(x + Inches(0.5))), Emu(int(y + Inches(0.4))),
            Emu(int(w - Inches(1.0))), Emu(int(h - Inches(0.8))))
        tf = box.text_frame
        tf.word_wrap = True
        for i, line in enumerate(code_text.rstrip().split("\n")[:26]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = 1.35
            r = p.add_run()
            r.text = line or " "
            r.font.name = FONT_MONO
            r.font.size = Pt(16)
            r.font.color.rgb = GRAY_20
        if caption:
            cap = slide.shapes.add_textbox(x, Inches(13.5), w, Inches(0.4))
            r = cap.text_frame.paragraphs[0].add_run()
            r.text = caption
            r.font.name = FONT_MONO
            r.font.size = Pt(14)
            r.font.color.rgb = GRAY_60
        self.drop_empty(slide)
        return slide

    def end(self, notes=None):
        """IBM's closing slide. It carries the logo lockup and takes no content."""
        return self.add("end", notes)

    def save(self, path):
        self.prs.save(str(path))
        return path


def _split_bold(text):
    """'**Lead** — rest' -> [('Lead', True), (' — rest', False)]."""
    parts, buf, bold, i = [], "", False, 0
    while i < len(text):
        if text[i:i + 2] == "**":
            parts.append((buf, bold))
            buf, bold, i = "", not bold, i + 2
            continue
        buf += text[i]
        i += 1
    parts.append((buf, bold))
    return parts
