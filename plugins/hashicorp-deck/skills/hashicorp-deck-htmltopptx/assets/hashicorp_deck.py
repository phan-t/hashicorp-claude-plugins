"""hashicorp_deck — build HashiCorp-branded .pptx slides on the official kit.

A thin wrapper over python-pptx. It does NOT restyle anything: every slide is
created from a named layout in `hashicorp-brand-template.pptx` (the HashiCorp
Light-mode CY26 Presentation Kit v4, stripped to master + layouts + theme +
embedded Inter), and only placeholder *text* is filled. Inter, the signature
glow gradient and all geometry are inherited from the layouts, which is what
keeps decks on-brand.

    from hashicorp_deck import Deck
    d = Deck()                      # or Deck(mode="dark")
    d.cover("Rebuilding deploys", subtitle="Platform engineering",
            kicker="Acme - Briefing", date="August 2026", speaker="Tony Phan")
    d.section("The problem")
    d.body("Every deploy went through one queue",
           prose="One team owned the pipeline, so every change queued behind it.",
           bullets=["Lead time was four days", "Rollbacks needed a ticket"])
    d.metrics([("92%", "Faster lead time"), ("3x", "Deploys per week")],
              title="By the numbers")
    d.end()
    d.save("deck.pptx")

Unlike a theme-driven template, this kit carries its brand in the *layouts*: the
theme is stock Office (Aptos / blue accents) and every layout overrides it with
Inter and HashiCorp colour. So never set a font, colour or size from calling
code — fill placeholders and let the layout resolve them. The exceptions, where
the kit ships no placeholder at all, are `code()`, `table()`, `chart()` and the
attribution line on `quote()`; each is marked in the source.

Two kits ship here. `mode="light"` is the CY26 light kit v4 and is the default;
`mode="dark"` is the CY26 dark kit v2. They are different *generations*, not a
recolour of each other — they share no layout names, and the dark kit predates
the glow gradient — so `MODES` carries everything that differs and a couple of
methods are refused in dark mode with an explanation. See references/dark.md.

Requires: python-pptx.
"""

from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

LIGHT_TEMPLATE = Path(__file__).with_name("hashicorp-brand-template.pptx")
DARK_TEMPLATE = Path(__file__).with_name("hashicorp-darkv4-template.pptx")
DARK_V2_TEMPLATE = Path(__file__).with_name("hashicorp-dark-template.pptx")

# Friendly key -> exact layout name in the light kit. Matching is
# whitespace-insensitive; the odd spacing in some names is HashiCorp's.
LIGHT_LAYOUTS = {
    # openers and closers
    "cover": "General Divider",
    "section": "Section Divider",
    "agenda": "Agenda",
    "end": "Thank You",
    "cover_terraform": "Cover - Terraform",
    "cover_packer": "Cover - Packer",
    "cover_waypoint": "Cover - Waypoint",
    "cover_nomad": "Cover - Nomad",
    "cover_vault": "Cover - Vault",
    "cover_vault_alt": "Cover - Vault Alt",
    "cover_boundary": "Cover - Boundary",
    "cover_consul": "Cover - Consul",
    # content
    "titled": "Title Subtitle",
    "eyebrow": "Eyebrow Title",
    "quote": "Quote-3lines",
    "pillars": "3 Pillars",
    "body": "Content- body + bullet list",
    "grid_2": "Content- body + bullet list, 2-column",
    "grid_3": "Content- body + bullet list, 3-column",
    "grid_4": "Content- body + bullet list, 4-column",
    "cols_3": "Content - 3-column bullet",
    "cols_4": "Content - 4-column bullet",
    "icons_2": "Icon Text Container - 2-column",
    "icons_3": "Icon Text Container - 3-column",
    "icons_4": "Icon Text Container - 4-column",
    # imagery and people
    "image_right": "Image Overlay - small, right",
    "image_left": "Image Overlay - small, left",
    "image_large": "Image Overlay - large",
    "images_2": "2 Image - Body Copy",
    "images_3": "1_2 Image - Body Copy",
    "speaker": "Speaker-1",
    "speakers_2": "Speaker-2",
    "metrics_2": "2 Metric",
    "metrics_3": "3 Metric",
    # bare canvases
    "gradient": "Blank-Gradient",
    "blank": "Blank",
}

# The *official* dark kit (v2) names almost nothing: 74 of its layouts are Google Slides export
# artifacts called CUSTOM_1_2_2_1_1_1_1_1_1_1_1_1 and the like, and none of its
# names match the light kit's. This map was built by inspecting placeholder
# geometry and the kit's own demo slides, so the friendly keys mean the same
# thing in both modes even though the layouts behind them share no vocabulary.
DARK_V2_LAYOUTS = {
    "cover": "CUSTOM_1_2_2",                              # title + 4 presenter lines
    "agenda": "CUSTOM_1_1_1_1_1_1_1_1_2",
    "section": "CUSTOM_1_1_1_3_1_1_1_1_1_1_1",            # no placeholder; drawn
    "statement": "CUSTOM_1_2_2_1_1_1_1_1_1_1_1_1",
    "eyebrow": "CUSTOM_1_2_2_1_1_1_1_1_1_1_1_1",          # small slot above the title
    "titled": "CUSTOM_1_1_1_1_2",                         # its two columns are dropped
    "body": "CUSTOM_1_1_1_1_2",
    "cols_2": "CUSTOM_1_1_1_1_2",
    "cols_3": "CUSTOM_1_1_1_1_1_2",
    "cols_4": "CUSTOM_1_1_1_1_1_1_3",
    "image_right": "1_Image-Overlay-small",
    "image_left": "1_Image-Overlay-small",
    "quote": "CUSTOM_1_1_2",
    "speaker": "Presenter 1 - Single Presenter",
    "speakers_2": "Presenter 2 - 2 Presenters",
    "end": "CUSTOM_1_2_1",
    "gradient": "CUSTOM_1_1_1_1_1_1_1_1_1_1_1",
    "blank": "CUSTOM_1_1_1_1_1_1_1_1_1_1_1",
}

#: The four stops of HashiCorp's signature glow, in the order the kit uses them.
#: The layouts already apply this to metric numbers, the quote and the metric
#: rules; these values exist so drawn shapes (charts) can stay in the family.
GLOW = ["6C81FF", "C08DFF", "FF8791", "F9B571"]

#: Product hues, read off the kit's own "Product colors" reference slide.
PRODUCT = {
    "terraform": "7B42BC", "packer": "63D0FF", "waypoint": "62D4DC",
    "nomad": "60DEA9", "vault": "FFCF25", "boundary": "EC585D",
    "consul": "DC477D",
}

#: Categorical series colours for charts: the glow stops, then two product hues.
#: Needed because the light kit's *theme* is stock Office — accent1 is Office
#: blue, not a HashiCorp colour — so a native chart left to the theme comes out
#: off-brand. They read correctly on both grounds.
CHART_COLORS = GLOW + ["62D4DC", "60DEA9"]

#: Everything that differs between the modes, in one place. Methods read this
#: rather than branching on the mode name.
_LIGHT_STRUCTURE = {
    "layouts": LIGHT_LAYOUTS,
    "cover_slots": {"kicker": 10, "title": 11, "subtitle": 12,
                    "date": 13, "speaker": 14, "speaker_title": 15},
    "body_slots": {"prose": 13, "bullets": 14},
    "quote_slot": 13,
    "eyebrow_slot": "SUBTITLE",
    "end_slot": 11,
    "end_text": "Thank you",
    "section_drawn": False,
    "unsupported": {},
}

MODES = {
    "light": dict(_LIGHT_STRUCTURE,
        template=LIGHT_TEMPLATE,
        ink="000000", muted="646466", rule="D9D9D9", head_rule="000000",
        panel="171717", panel_text="EDEDED",
    ),
    # Derived from the light kit, so every layout name, placeholder index, list
    # style, bullet and gradient is the same object light mode uses. Only the
    # neutrals differ, which is why this shares _LIGHT_STRUCTURE wholesale
    # instead of carrying a map of its own.
    "dark": dict(_LIGHT_STRUCTURE,
        template=DARK_TEMPLATE,
        ink="FFFFFF", muted="9B9B9B", rule="343536", head_rule="FFFFFF",
        # A #171717 panel is invisible on a black ground, so this one lifts
        # away from the background rather than sinking into it.
        panel="242424", panel_text="EDEDED",
    ),
    # HashiCorp's own dark kit. A different generation (v2 against light's v4):
    # no shared layout names, no glow gradient, no metric layout. Kept because it
    # is the only *official* dark artefact; see references/dark.md.
    "dark-v2": {
        "template": DARK_V2_TEMPLATE,
        "layouts": DARK_V2_LAYOUTS,
        "cover_slots": None,
        "body_slots": None,
        "quote_slot": 13,
        "eyebrow_slot": 2,
        "end_slot": 1,
        "end_text": "hello@hashicorp.com",
        "section_drawn": True,
        "ink": "FFFFFF", "muted": "727374", "rule": "343536",
        "head_rule": "D9D9D9",
        "panel": "242424", "panel_text": "EDEDED",
        "unsupported": {
            "metrics": "the CY26 dark kit v2 ships no metric-callout layout; use "
                       "mode='dark', which has one, or columns()",
            "product_cover": "the CY26 dark kit v2 ships no product covers; use "
                             "mode='dark', which has them",
        },
    },
}

# Text and rule colours are per-mode and live in MODES above: black ink on the
# light kit, white on the dark one. Nothing here may hardcode a neutral.

FONT_HEAD = "Inter SemiBold"
FONT_BODY = "Inter"
FONT_LIGHT = "Inter Light"
FONT_MEDIUM = "Inter Medium"
FONT_MONO = "JetBrains Mono"

_CELL_MARGIN = 54864     # 0.06 in, in EMU
_RULE_W = 12700          # 1 pt


def _border(parent, name, color=None, w=_RULE_W):
    """Append one a:lnL/R/T/B to a tcPr. `color` None means an explicit no-fill."""
    el = parent.makeelement(qn("a:" + name), {"w": str(w), "cap": "flat",
                                              "cmpd": "sng", "algn": "ctr"})
    if color is None:
        el.append(el.makeelement(qn("a:noFill"), {}))
    else:
        fill = el.makeelement(qn("a:solidFill"), {})
        fill.append(fill.makeelement(qn("a:srgbClr"), {"val": str(color)}))
        el.append(fill)
    el.append(el.makeelement(qn("a:prstDash"), {"val": "solid"}))
    parent.append(el)
    return el


#: Order of a:pPr's children, per the DrawingML schema. buNone has to be inserted
#: at its slot, not appended, or PowerPoint rejects the paragraph.
_PPR_AFTER_BULLET = ("a:tabLst", "a:defRPr", "a:extLst")


def clear_bullet(paragraph):
    """Force a paragraph to carry no bullet.

    Needed on the icon containers' header slots. Their layout leaves the bullet
    *inherited*, so it resolves to the master's bullet character and the header
    renders as "• Self-service". HashiCorp's own slides fix this the same way,
    per-paragraph, rather than in the layout.
    """
    pPr = paragraph._p.get_or_add_pPr()
    for tag in ("a:buChar", "a:buAutoNum", "a:buNone"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    el = pPr.makeelement(qn("a:buNone"), {})
    for tag in _PPR_AFTER_BULLET:
        nxt = pPr.find(qn(tag))
        if nxt is not None:
            nxt.addprevious(el)
            return paragraph
    pPr.append(el)
    return paragraph


def style_cell(cell, is_header=False, cfg=None):
    """Stamp the deck's table look onto one cell.

    The kit ships an empty `tableStyles.xml`, so an untouched python-pptx table
    inherits PowerPoint's generic blue "Medium Style 2 - Accent 1" — banded rows
    on an Office-blue header, nothing like the rest of the deck. Every cell
    therefore carries its own formatting: no fill, no vertical rules, a hairline
    under each row and a solid rule under the header. The run colour is not
    cosmetic either — the inherited style sets first-row text to lt1 (white),
    which vanishes once the blue fill is suppressed.
    """
    cfg = cfg or MODES["light"]
    for para in cell.text_frame.paragraphs:
        for run in para.runs:
            run.font.color.rgb = RGBColor.from_string(cfg["ink"])
            run.font.name = FONT_HEAD if is_header else FONT_LIGHT
    tc = cell._tc
    old = tc.find(qn("a:tcPr"))
    if old is not None:
        tc.remove(old)
    pr = tc.makeelement(qn("a:tcPr"), {"marL": str(_CELL_MARGIN), "marR": str(_CELL_MARGIN),
                                       "marT": str(_CELL_MARGIN), "marB": str(_CELL_MARGIN)})
    _border(pr, "lnL", None)                                    # no vertical rules
    _border(pr, "lnR", None)
    _border(pr, "lnT", None)
    _border(pr, "lnB", cfg["head_rule"] if is_header else cfg["rule"],
            _RULE_W if is_header else _RULE_W * 3 // 4)
    pr.append(pr.makeelement(qn("a:noFill"), {}))               # transparent, no banding
    tc.append(pr)
    return cell


class Deck:
    """A HashiCorp-kit presentation. Each method appends one slide and returns it."""

    #: Kit canvas, in inches — 10.0 x 5.63 (16:9). Content sits in a 9.1 in
    #: measure at x=0.45; the title/subtitle band runs from y=0.40 to y=1.20.
    GRID = {"margin": Inches(0.45), "measure": Inches(9.10), "content_top": Inches(1.60)}

    #: Where drawn content (tables, charts, code) goes on the "Title Subtitle"
    #: layout: below the subtitle, clear of the page number at y=5.28.
    CONTENT_BOX = (Inches(0.45), Inches(1.60), Inches(9.10), Inches(3.45))

    #: Mean advance width of Inter as a fraction of its point size, measured off
    #: rendered output. Used only to predict wrapping, never to set anything.
    CHAR_RATIO = 0.52

    def __init__(self, template=None, mode="light"):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {sorted(MODES)}, got {mode!r}")
        self.mode = mode
        self.cfg = MODES[mode]
        self.prs = Presentation(str(template or self.cfg["template"]))
        self._layouts = {self._key(l.name): l for l in self.prs.slide_layouts}
        #: Slots whose text is predicted to overflow. Nothing is changed on your
        #: behalf — read this after building and shorten the copy, or accept it.
        self.warnings = []

    @staticmethod
    def _key(name):
        return " ".join(name.split()).lower()

    def layout(self, key):
        """Resolve a friendly key (or an exact kit layout name) to a layout."""
        name = self.cfg["layouts"].get(key, key)
        try:
            return self._layouts[self._key(name)]
        except KeyError:
            raise KeyError(
                f"no layout {name!r} in the {self.mode} template; known keys: "
                + ", ".join(sorted(self.cfg["layouts"]))
            ) from None

    def _require(self, method):
        """Refuse a method the current kit has no layout for, and say what to do."""
        why = self.cfg["unsupported"].get(method)
        if why:
            raise NotImplementedError(f"Deck.{method}() is not available in "
                                      f"{self.mode} mode: {why}")

    # -- low level -------------------------------------------------------------
    def add(self, key, notes=None):
        """Add a slide from a layout.

        No chrome fix-up is needed here: the kit's custom layouts carry the page
        number field and the copyright line as *layout* shapes, not placeholders,
        so both inherit onto every slide automatically.
        """
        slide = self.prs.slides.add_slide(self.layout(key))
        if notes:
            slide.notes_slide.notes_text_frame.text = notes
        return slide

    @staticmethod
    def ph(slide, ref):
        """Placeholder by idx (int) or by type name ('PICTURE', 'SUBTITLE', ...).

        Most of the kit's custom layouts have no `title`-type placeholder — even
        the slot the kit calls a title is often a plain body — so addressing by
        idx is the norm here, not the exception.
        """
        for p in slide.placeholders:
            f = p.placeholder_format
            if (isinstance(ref, int) and f.idx == ref) or (
                isinstance(ref, str) and str(f.type).split()[0] == ref
            ):
                return p
        return None

    @staticmethod
    def bodies(slide):
        """Text placeholders in reading order: top to bottom, then left to right."""
        out = [p for p in slide.placeholders
               if str(p.placeholder_format.type).split()[0]
               in ("BODY", "OBJECT", "SUBTITLE", "TITLE", "CENTER_TITLE")]
        return sorted(out, key=lambda p: (round(p.top / 100000), round(p.left / 100000)))

    @classmethod
    def content_bodies(cls, slide):
        """`bodies()` minus the title and subtitle slots.

        Placeholders are unhashable, so they cannot be filtered out by identity;
        the discriminator is the placeholder *type*, which is reliable on every
        layout whose title is a real title.
        """
        return [p for p in cls.bodies(slide)
                if str(p.placeholder_format.type).split()[0]
                not in ("TITLE", "CENTER_TITLE", "SUBTITLE")]

    @classmethod
    def set_text(cls, placeholder, content):
        """Fill a placeholder. `content` is a string or a list of paragraphs.

        Inline `**bold**` is honoured. Nothing else is set, so the text lands in
        Inter at the layout's own size, colour and — on metric and quote slots —
        the glow gradient.
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
    def unbullet(placeholder):
        """Strip the bullet from a slot that holds a *field*, not a list.

        Both kits bullet more slots than they should: cover lines, presenter
        details, agenda items and the closing line all arrive with a bullet
        character that HashiCorp's own slides clear per-paragraph. Content
        columns are left alone — there a bullet is the point.
        """
        if placeholder is None or not placeholder.has_text_frame:
            return placeholder
        for para in placeholder.text_frame.paragraphs:
            clear_bullet(para)
        return placeholder

    @staticmethod
    def drop_empty(slide):
        """Remove placeholders left unfilled.

        The kit prompts many slots with real words — "Metric", "Details here / 2
        lines max", "[Speaker name]" — so an untouched placeholder ships copy
        that looks deliberate. Every method below calls this.
        """
        for p in list(slide.placeholders):
            if str(p.placeholder_format.type).split()[0] in ("SLIDE_NUMBER", "FOOTER", "DATE"):
                continue
            if p.has_text_frame and not p.text_frame.text.strip():
                p._element.getparent().remove(p._element)

    @staticmethod
    def slot_pt(layout, idx):
        """The point size one placeholder resolves to, or None.

        python-pptx cannot read this: the size lives in the layout placeholder's
        `<a:lstStyle>`, not on any run, which is exactly why filling a
        placeholder inherits it. Some slots omit `sz` there and fall through to
        the master's own body style, so that is followed too — without the
        fallback those slots look sizeless and escape the overflow check.
        """
        def lvl1_sz(el):
            if el is None:
                return None
            lvl1 = el.find(qn("a:lvl1pPr"))
            rpr = lvl1.find(qn("a:defRPr")) if lvl1 is not None else None
            sz = rpr.get("sz") if rpr is not None else None
            return int(sz) / 100 if sz else None

        for lph in layout.placeholders:
            if lph.placeholder_format.idx != idx:
                continue
            body = lph._element.find(qn("p:txBody"))
            size = lvl1_sz(body.find(qn("a:lstStyle"))) if body is not None else None
            if size:
                return size
            kind = str(lph.placeholder_format.type).split()[0]
            styles = layout.slide_master._element.find(qn("p:txStyles"))
            if styles is None:
                return None
            tag = "p:titleStyle" if kind in ("TITLE", "CENTER_TITLE") else "p:bodyStyle"
            return lvl1_sz(styles.find(qn(tag)))
        return None

    def check_fit(self, slide, idx, text, label, lines=1):
        """Record a warning when text will wrap past what a tight slot allows.

        The kit marks its cover and title slots `<a:noAutofit/>`, so overlong
        text does not shrink — it wraps and lands on top of the slot beneath.
        This predicts that rather than silently shipping the collision.
        """
        ph = self.ph(slide, idx)
        if ph is None or not text:
            return None
        size = self.slot_pt(slide.slide_layout, idx)
        if not size:
            return None
        per_line = int((ph.width / 12700) / (size * self.CHAR_RATIO))
        plain = str(text).replace("**", "")
        if per_line > 0 and len(plain) > per_line * lines:
            self.warnings.append(
                f"{label}: {len(plain)} chars in a slot that holds about "
                f"{per_line * lines} at {size:g} pt — it will wrap onto the slot "
                f"below (this layout disables shrink-to-fit)")
        return ph

    # -- openers and closers ---------------------------------------------------
    #: "General Divider" slot map. The kit uses this one layout for both the
    #: title page and the interior dividers; the slots are all plain bodies.
    COVER_SLOTS = {"kicker": 10, "title": 11, "subtitle": 12,
                   "date": 13, "speaker": 14, "speaker_title": 15}

    def cover(self, title, subtitle=None, kicker=None, date=None,
              speaker=None, speaker_title=None, notes=None):
        """Title page. `kicker` is the small line above (the kit prompts it
        "<Customer Name - Briefing>"); the rest fill the presenter block."""
        slide = self.add("cover", notes)
        slots = self.cfg["cover_slots"]
        if slots:
            for name, value in (("kicker", kicker), ("title", title), ("subtitle", subtitle),
                                ("date", date), ("speaker", speaker),
                                ("speaker_title", speaker_title)):
                self.set_text(self.ph(slide, slots[name]), value)
            self.check_fit(slide, slots["title"], title, "cover title")
            self.check_fit(slide, slots["subtitle"], subtitle, "cover subtitle")
        else:
            # The dark kit's cover is a real title over four unlabelled lines, so
            # the presenter block is filled in reading order instead of by name.
            self.set_text(slide.shapes.title, title)
            lines = [v for v in (kicker, subtitle, speaker, speaker_title, date) if v]
            for slot, value in zip(self.content_bodies(slide), lines):
                self.unbullet(self.set_text(slot, value))
                self.check_fit(slide, slot.placeholder_format.idx, value,
                               f"cover line {value[:24]!r}")
            if len(lines) > len(self.content_bodies(slide)):
                self.warnings.append(
                    f"cover: {len(lines)} lines for "
                    f"{len(self.content_bodies(slide))} slots in the dark kit; "
                    "the surplus was dropped")
        self.drop_empty(slide)
        return slide

    def product_cover(self, title, product="terraform", lines=None, notes=None):
        """A product-branded cover. `lines` fills the kit's two footer slots
        (it prompts them "Your Name / Company")."""
        self._require("product_cover")
        key = f"cover_{product.lower().replace(' ', '_')}"
        if key not in self.cfg["layouts"]:
            raise KeyError(f"no product cover for {product!r}; "
                           + "known: " + ", ".join(sorted(PRODUCT)))
        slide = self.add(key, notes)
        self.set_text(slide.shapes.title, title)
        for slot, value in zip(self.content_bodies(slide), list(lines or [])):
            self.set_text(slot, value)
        self.drop_empty(slide)
        return slide

    #: Where the dark kit's own demo slides put the divider title and its rule.
    #: That layout ships no placeholder, so this is copied from HashiCorp's usage
    #: rather than invented — one of the few places a layout cannot be filled.
    DARK_SECTION = {"box": (Inches(0.44), Inches(4.01), Inches(7.29), Inches(0.81)),
                    "pt": Pt(42)}

    def section(self, title, notes=None):
        """Full-bleed divider. Title only — the layout carries no other slot."""
        slide = self.add("section", notes)
        if not self.cfg["section_drawn"]:
            self.set_text(slide.shapes.title, title)
            return slide
        x, y, w, h = self.DARK_SECTION["box"]
        box = slide.shapes.add_textbox(x, y, w, h)
        box.text_frame.word_wrap = True
        r = box.text_frame.paragraphs[0].add_run()
        r.text = title
        r.font.name = FONT_HEAD
        r.font.size = self.DARK_SECTION["pt"]
        # This divider is the one *white* slide in the dark kit — a deliberate
        # contrast break — so the mode's white ink would render it invisible.
        # HashiCorp's own divider text is dk1; this matches that markup exactly.
        r.font.color.theme_color = MSO_THEME_COLOR.DARK_1
        return slide

    def agenda(self, title, items, numbers=None, notes=None):
        """Contents page. Up to six items, each with an optional page number.

        Item slots are idx 1-6 and number slots idx 11-16, but the kit does not
        pair them in index order — idx 16 sits beside idx 1. Both runs are read
        in vertical order instead, which pairs them correctly.
        """
        items = list(items)
        if len(items) > 6:
            raise ValueError(f"the Agenda layout holds 6 items, got {len(items)}")
        slide = self.add("agenda", notes)
        head = slide.shapes.title
        self.set_text(head, title)
        # Geometry, not placeholder type, is the discriminator: the light kit
        # makes the page numbers BODY placeholders and the dark kit makes them
        # TITLE ones, but in both they are the narrow column on the right.
        rows = [p for p in self.bodies(slide)
                if p is not None and (head is None or p.placeholder_format.idx
                                      != head.placeholder_format.idx)]
        text_slots = sorted([p for p in rows if p.width > Inches(2)], key=lambda p: p.top)
        num_slots = sorted([p for p in rows if p.width <= Inches(2)], key=lambda p: p.top)
        for slot, value in zip(text_slots, items):
            self.unbullet(self.set_text(slot, value))
        for slot, value in zip(num_slots, list(numbers or [])):
            self.unbullet(self.set_text(slot, str(value)))
        self.drop_empty(slide)
        return slide

    def end(self, text=None, notes=None):
        """Closing slide. The words are a *prompt* in the kit, not real content,
        so an unfilled slot renders blank — pass text (or accept the default)."""
        slide = self.add("end", notes)
        self.unbullet(self.set_text(self.ph(slide, self.cfg["end_slot"]),
                                    self.cfg["end_text"] if text is None else text))
        self.drop_empty(slide)
        return slide

    # -- content ---------------------------------------------------------------
    def titled(self, title, subtitle=None, notes=None):
        """A bare titled canvas. Use when a slide needs shapes of its own."""
        slide = self.add("titled", notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, "SUBTITLE"), subtitle)
        self.drop_empty(slide)
        return slide

    def eyebrow(self, title, eyebrow, notes=None):
        """Title with a small label *above* it — the kit's case-study opener.

        The label lives in the subtitle placeholder even though it sits on top;
        that inversion is the layout's, and it is why the label is set here
        rather than through `titled()`.
        """
        slide = self.add("eyebrow", notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, self.cfg["eyebrow_slot"]), eyebrow)
        self.drop_empty(slide)
        return slide

    def quote(self, text, attribution=None, notes=None):
        """Large centred pull-quote in the glow gradient.

        The layout holds exactly one slot and its outline levels are all 36 pt,
        so there is nowhere for an attribution to go. It is drawn instead — one
        of the four places this module positions its own shapes.
        """
        slide = self.add("quote", notes)
        box = self.ph(slide, self.cfg["quote_slot"])
        self.set_text(box, text)
        if attribution:
            cap = slide.shapes.add_textbox(box.left, box.top + box.height,
                                           box.width, Inches(0.3))
            cap.text_frame.word_wrap = True
            p = cap.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER   # the layout centres the quote in its
            r = p.add_run()                 # lstStyle, so there is nothing to copy
            r.text = attribution
            r.font.name = FONT_LIGHT
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor.from_string(self.cfg["muted"])
        self.drop_empty(slide)
        return slide

    def body(self, title, prose=None, bullets=None, subtitle=None, notes=None):
        """The kit's workhorse: prose on the left, a bullet list on the right.

        The two slots are not interchangeable — only the right one carries a
        bullet character — so prose and bullets are addressed by name, and a
        bullets-only slide leaves the left half empty on purpose.
        """
        slide = self.add("body", notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, "SUBTITLE"), subtitle)
        slots = self.cfg["body_slots"]
        if slots:
            self.set_text(self.ph(slide, slots["prose"]), prose)
            self.set_text(self.ph(slide, slots["bullets"]), bullets)
        else:
            # The dark kit's two columns are equal and neither is bulleted, so
            # the asymmetry light mode relies on does not exist here.
            cols = self.content_bodies(slide)
            for slot, value in zip(cols, [prose, bullets]):
                self.set_text(slot, value)
        self.drop_empty(slide)
        return slide

    def columns(self, title, columns, subtitle=None, headings=None,
                key=None, notes=None):
        """2-4 columns of bullets, on the kit layout that fits the shape.

        With `headings`, the "Icon Text Container" layouts are used: each column
        is a bold header over a short paragraph, under one of the kit's icons.
        Without, the plain N-column bullet layouts are used. Two plain columns
        land on the body+bullets layout, whose first column has no bullet
        character — pass `headings` if that asymmetry is not what you want.
        """
        columns = [c for c in columns if c]
        n = len(columns)
        headings = list(headings or [])
        if key is None:
            if n < 1 or n > 4:
                raise ValueError(f"the kit holds 1-4 columns, got {n}")
            if headings and f"icons_{max(2, n)}" in self.cfg["layouts"]:
                key = f"icons_{max(2, n)}"
            elif n <= 2:
                key = "cols_2" if "cols_2" in self.cfg["layouts"] else "body"
            else:
                key = f"cols_{n}"
        slide = self.add(key, notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, "SUBTITLE"), subtitle)

        if key.startswith("icons_"):
            slots = self.content_bodies(slide)
            # Icon layouts stack a header row above a body row; both are read in
            # vertical order, so split on the row boundary rather than by index.
            top = min(p.top for p in slots)
            split = top + Inches(0.2)
            heads = sorted([p for p in slots if p.top < split], key=lambda p: p.left)
            texts = sorted([p for p in slots if p.top >= split], key=lambda p: p.left)
            if n > len(heads):
                raise ValueError(f"layout {key!r} has {len(heads)} columns for {n}")
            for slot, value in zip(heads, headings):
                self.set_text(slot, value)
                for para in slot.text_frame.paragraphs:
                    clear_bullet(para)
            for slot, value in zip(texts, columns):
                # These slots carry no bullet character, so a list of points
                # reads as separate lines rather than a run-on sentence.
                self.set_text(slot, value)
        else:
            slots = self._column_slots(slide, key)
            if n > len(slots):
                raise ValueError(f"layout {key!r} has {len(slots)} column slot(s) for {n}")
            if headings:
                # No icon-container layout in this kit: fold each heading into
                # its column as a bold lead-in rather than dropping it.
                columns = [[f"**{h}**"] + (list(c) if not isinstance(c, str) else [c])
                           for h, c in zip(headings, columns)]
            for slot, value in zip(slots, columns):
                self.set_text(slot, value)
        self.drop_empty(slide)
        return slide

    def _column_slots(self, slide, key):
        if key == "body" and self.cfg["body_slots"]:   # prose slot, then bullet slot
            b = self.cfg["body_slots"]
            return [self.ph(slide, b["prose"]), self.ph(slide, b["bullets"])]
        return sorted(self.content_bodies(slide), key=lambda p: p.left)

    #: Which slot holds the number and which the caption, per metric layout. The
    #: kit indexes these unevenly (2 Metric jumps 13 -> 22 -> 23 -> 26), so this
    #: is a map rather than a heuristic.
    METRIC_SLOTS = {
        "metrics_2": [(13, 22), (23, 26)],
        "metrics_3": [(13, 22), (16, 23), (19, 24)],
    }

    def metrics(self, cards, title=None, subtitle=None, key=None, notes=None):
        """Big numbers with a caption each. `cards` is [(value, caption), ...].

        The numbers pick up the glow gradient and the rule beneath them from the
        layout, so pass the value as plain text and set nothing.
        """
        self._require("metrics")
        cards = list(cards)
        if key is None:
            key = "metrics_2" if len(cards) <= 2 else "metrics_3"
        pairs = self.METRIC_SLOTS[key]
        if len(cards) > len(pairs):
            raise ValueError(f"layout {key!r} holds {len(pairs)} metrics, got {len(cards)}")
        slide = self.add(key, notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, "SUBTITLE"), subtitle)
        for (value_idx, caption_idx), (value, caption) in zip(pairs, cards):
            self.set_text(self.ph(slide, value_idx), value)
            self.set_text(self.ph(slide, caption_idx), caption)
        self.drop_empty(slide)
        return slide

    # -- imagery and people ----------------------------------------------------
    def image(self, title, image_path, subtitle=None, body=None,
              style="image_right", notes=None):
        """Picture with copy beside it. `body` is a list, one entry per text slot."""
        slide = self.add(style, notes)
        self.set_text(slide.shapes.title, title)
        self.set_text(self.ph(slide, "SUBTITLE"), subtitle)
        if body:
            slots = self.content_bodies(slide)
            paras = [body] if isinstance(body, str) else list(body)
            for slot, value in zip(slots, paras):
                self.set_text(slot, value)
        self.place_image(slide, image_path)
        self.drop_empty(slide)
        return slide

    def speaker(self, name, lines=None, image=None, notes=None):
        """Presenter slide. `name` may be a list to break it across two lines."""
        slide = self.add("speaker", notes)
        self.set_text(slide.shapes.title, name)
        self.unbullet(self.set_text(self.ph(slide, "SUBTITLE"), lines))
        if image:
            self.place_image(slide, image)
        self.drop_empty(slide)
        return slide

    def place_image(self, slide, image_path, ref="PICTURE"):
        """Fill a picture placeholder, cropping to cover rather than stretching."""
        ph = self.ph(slide, ref)
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

    # -- drawn content ---------------------------------------------------------
    # A table row only needs to be tall enough for its type. Left alone,
    # python-pptx divides the box height evenly across the rows, so a short table
    # renders as a few enormous cells with the text marooned in them.
    ROW_HEIGHT = Inches(0.34)
    CELL_PT = Pt(11)          # matches the kit's body copy

    def table(self, title, rows, subtitle=None, notes=None, row_height=None):
        """rows: list of lists; the first row is treated as the header.

        The kit ships no table layout, so this draws one on the titled canvas.
        Rows are sized to their content; a table too tall for the content box
        falls back to sharing it evenly.
        """
        slide = self.titled(title, subtitle, notes=notes)
        x, y, w, h = self.CONTENT_BOX
        n_rows, n_cols = len(rows), max(len(r) for r in rows)
        shape = slide.shapes.add_table(n_rows, n_cols, x, y, w, h)
        for r, row in enumerate(rows):
            for c in range(n_cols):
                cell = shape.table.cell(r, c)
                cell.text = str(row[c]) if c < len(row) else ""
                style_cell(cell, is_header=(r == 0), cfg=self.cfg)
                for p in cell.text_frame.paragraphs:
                    for run in p.runs:
                        run.font.size = self.CELL_PT
        height = row_height or self.ROW_HEIGHT
        if height * n_rows <= h:
            for row_obj in shape.table.rows:
                row_obj.height = height
            shape.height = height * n_rows
        return slide

    def chart(self, title, categories, series, subtitle=None,
              chart_type=None, notes=None):
        """A native chart on the titled canvas. `series` is [(name, values), ...].

        Native rather than an image, so the numbers stay editable. Series colours
        are set explicitly, which is the one honest exception to "never set a
        colour": the kit's theme is stock Office, so a chart left to inherit
        would come out in Office blue and orange.

        One value axis only — python-pptx cannot build a secondary axis, so two
        measures of different scale have to be indexed to a common base first.
        """
        slide = self.titled(title, subtitle, notes=notes)
        data = CategoryChartData()
        data.categories = list(categories)
        for name, values in series:
            data.add_series(name, tuple(values))
        frame = slide.shapes.add_chart(
            chart_type or XL_CHART_TYPE.COLUMN_CLUSTERED, *self.CONTENT_BOX, data)
        ch = frame.chart
        ch.has_title = False
        ch.has_legend = len(series) > 1
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        ch.font.name = FONT_LIGHT
        ch.font.size = Pt(10)
        ch.font.color.rgb = RGBColor.from_string(self.cfg["muted"])
        for i, plot_series in enumerate(ch.plots[0].series):
            color = RGBColor.from_string(CHART_COLORS[i % len(CHART_COLORS)])
            fmt = plot_series.format
            if chart_type in (XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS):
                fmt.line.color.rgb = color
                fmt.line.width = Pt(2)
            else:
                fmt.fill.solid()
                fmt.fill.fore_color.rgb = color
                fmt.line.fill.background()
        return slide

    def code(self, title, code_text, caption=None, subtitle=None, notes=None):
        """Monospace block on a dark panel. The kit has no code layout, so this
        is drawn on the titled canvas."""
        slide = self.titled(title, subtitle, notes=notes)
        x, y, w, h = self.CONTENT_BOX
        if caption:
            h = Emu(int(h - Inches(0.3)))
        # Fit the panel to the code. Left at the full content height a six-line
        # snippet sits in a half-empty slab.
        lines = code_text.rstrip().split("\n")[:20]
        needed = Inches(0.32) + int(Inches(0.1625)) * len(lines)
        h = Emu(int(min(h, max(Inches(0.9), needed))))
        panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        panel.adjustments[0] = 0.04
        panel.fill.solid()
        panel.fill.fore_color.rgb = RGBColor.from_string(self.cfg["panel"])
        panel.line.fill.background()
        panel.shadow.inherit = False
        box = slide.shapes.add_textbox(Emu(int(x + Inches(0.22))), Emu(int(y + Inches(0.16))),
                                       Emu(int(w - Inches(0.44))), Emu(int(h - Inches(0.32))))
        tf = box.text_frame
        tf.word_wrap = True
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = 1.3
            r = p.add_run()
            r.text = line or " "
            r.font.name = FONT_MONO
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor.from_string(self.cfg["panel_text"])
        if caption:
            cap = slide.shapes.add_textbox(x, Emu(int(y + h + Inches(0.06))), w, Inches(0.24))
            r = cap.text_frame.paragraphs[0].add_run()
            r.text = caption
            r.font.name = FONT_MONO
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor.from_string(self.cfg["muted"])
        return slide

    def save(self, path):
        self.prs.save(str(path))
        return path


def _split_bold(text):
    """'**Lead** - rest' -> [('Lead', True), (' - rest', False)]."""
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
