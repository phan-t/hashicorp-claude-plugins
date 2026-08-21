"""html_to_pptx — extract an HTML presentation's content and rebuild it as a
HashiCorp-branded .pptx.

This is a *content* conversion, not a screenshot. Each HTML slide is read for
its eyebrow, headline, lede and body blocks; that content is then re-typeset on
the official kit layouts by `hashicorp_deck`. The source deck's own colours,
gradients and fonts are deliberately discarded — the output belongs to the
HashiCorp kit.

    python html_to_pptx.py deck.html -o deck.pptx --kicker "Acme - Briefing"

It prints a per-slide report of the layout chosen and anything it could not map,
so nothing is dropped silently. Treat the result as a first pass: the script does
mechanical extraction, and a human (or Claude) still makes the editorial calls
the report flags. Requires: python-pptx, beautifulsoup4.
"""

import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from hashicorp_deck import Deck  # noqa: E402

# Selectors tried in order to find the slides of an unknown HTML deck. The first
# entry matches decks built by the sibling `hashicorp-deck-html` skill.
SLIDE_SELECTORS = ["section.slide", "section.slide-container", ".reveal .slides section",
                   "section", ".slide"]
# Chrome the kit regenerates for itself; it must not become content.
CHROME = {"secttag", "pagenum", "progress", "dots", "nav", "footer", "eyebrow",
          "kbd", "lockup"}


def text(node, keep_bold=True):
    """Flatten a node to a single line, preserving **bold** for strong/b."""
    if node is None:
        return ""
    out = []
    for el in node.descendants:
        if getattr(el, "name", None) is None:
            parent = el.parent.name if el.parent else ""
            s = str(el)
            if keep_bold and parent in ("strong", "b"):
                s = f"**{s.strip()}**" if s.strip() else s
            out.append(s)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def items(node, selector="li"):
    return [t for t in (text(li) for li in node.select(selector)) if t]


def _card_prose(card):
    """Caption becomes a bold lead-in, so the two lines read as one sentence."""
    cap, desc = text(card.select_one(".cap")), text(card.select_one(".desc"))
    if cap and desc:
        return f"**{cap}** — {desc}"
    return cap or desc


class Slide:
    """The neutral model between HTML and pptx."""

    def __init__(self, el, index):
        self.el = el
        self.index = index
        self.name = el.get("data-name") or ""
        self.eyebrow = text(el.select_one(".eyebrow"))
        h1, h2 = el.select_one("h1"), el.select_one("h2")
        self.headline = text(h1 or h2)
        self.is_big = h1 is not None
        self.lede = text(el.select_one(".lede") or el.select_one("p"))
        self.cards = [
            (text(c.select_one(".num")) or text(c.select_one("h3")), _card_prose(c))
            for c in el.select(".card")
        ]
        self.bullets = items(el, "ul li")
        self.columns = [items(col, "li") or [text(col.select_one("p"))]
                        for col in el.select(".row.split > *")]
        self.headings = [text(h) for h in el.select(".row.split > * h3")]
        self.quote = text(el.select_one("blockquote"))
        self.code = "\n".join(pre.get_text() for pre in el.select("pre")).strip()
        self.images = [img.get("src") for img in el.select("img[src]")]
        self.notes = text(el.select_one(".notes") or el.select_one("aside"))
        self.dropped = []

    def kind(self):
        if self.index == 0:
            return "cover"
        if self.code:
            return "code"
        if self.quote:
            return "quote"
        if len(self.cards) >= 2:
            return "metrics"
        if len(self.columns) >= 2:
            return "columns"
        if self.images:
            return "image"
        if self.bullets:
            return "body"
        if self.is_big and not self.lede and not self.bullets:
            return "section"
        return "titled"


def convert(html_path, out_path, kicker=None, selector=None, title=None,
            speaker=None, date=None, base_dir=None, mode="light", report=print):
    soup = BeautifulSoup(Path(html_path).read_text(encoding="utf-8"), "html.parser")
    els = []
    for sel in ([selector] if selector else SLIDE_SELECTORS):
        els = soup.select(sel)
        if len(els) > 1:
            break
    if not els:
        raise SystemExit(f"no slides found in {html_path}; pass --selector")

    base = Path(base_dir or Path(html_path).parent)
    doc_title = title or text(soup.select_one("title")) or Path(html_path).stem
    deck = Deck(mode=mode)
    report(f"{len(els)} slide(s) in {html_path} -> {mode} kit")

    for i, el in enumerate(els):
        s = Slide(el, i)
        kind = s.kind()
        head = s.headline or s.name or doc_title
        notes = s.notes or None

        if kind == "cover":
            deck.cover(head, subtitle=s.lede or None, kicker=kicker or s.eyebrow or None,
                       date=date, speaker=speaker, notes=notes)
        elif kind == "section":
            deck.section(head, notes=notes)
        elif kind == "quote":
            deck.quote(s.quote, attribution=s.lede or None, notes=notes)
        elif kind == "metrics":
            if len(s.cards) > 3:
                s.dropped.append(f"{len(s.cards) - 3} extra card(s) — the kit holds 3 metrics")
            try:
                deck.metrics(s.cards[:3], title=head, subtitle=s.lede or None, notes=notes)
            except NotImplementedError as e:
                s.dropped.append(f"{e}; carried as columns instead")
                deck.columns(head, [f"**{v}** — {p}" for v, p in s.cards[:4]],
                             subtitle=s.lede or None, notes=notes)
        elif kind == "columns":
            cols = [c for c in s.columns if c]
            if len(cols) > 4:
                s.dropped.append(f"{len(cols) - 4} extra column(s) — the kit holds 4")
            heads = s.headings if len(s.headings) == len(cols[:4]) else None
            deck.columns(head, cols[:4], subtitle=s.lede or None,
                         headings=heads, notes=notes)
        elif kind == "body":
            if not s.lede:
                s.dropped.append("no lede — the body layout's left half will be empty; "
                                 "add one or move this to columns()")
            deck.body(head, prose=s.lede or None, bullets=s.bullets, notes=notes)
        elif kind == "code":
            deck.code(head, s.code, caption=s.eyebrow or None, notes=notes)
        elif kind == "image":
            img = base / s.images[0]
            if img.exists():
                deck.image(head, img, subtitle=s.lede or None, notes=notes)
            else:
                s.dropped.append(f"image not found: {s.images[0]}")
                deck.titled(head, s.lede or None, notes=notes)
        else:
            deck.titled(head, s.lede or None, notes=notes)

        if len(s.images) > 1 and kind == "image":
            s.dropped.append(f"{len(s.images) - 1} extra image(s) on this slide")
        if s.code and kind != "code":
            s.dropped.append("code block not carried over")
        if len(s.code.splitlines()) > 20 and kind == "code":
            s.dropped.append(f"code truncated to 20 lines (had {len(s.code.splitlines())})")
        report(f"  {i + 1:>3}. {kind:<8} <- {head[:52]!r}"
               + ("".join(f"\n         ! {d}" for d in s.dropped) if s.dropped else ""))

    deck.end()
    for w in deck.warnings:
        report(f"       ! {w}")
    deck.save(out_path)
    report(f"wrote {out_path} ({len(els) + 1} slides, incl. the kit's closing slide)")
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("html")
    ap.add_argument("-o", "--out", default=None, help="output .pptx (default: alongside the html)")
    ap.add_argument("--kicker", default=None, help="small line above the cover title")
    ap.add_argument("--speaker", default=None, help="presenter name for the cover")
    ap.add_argument("--date", default=None, help="date line for the cover")
    ap.add_argument("--selector", default=None, help="CSS selector for slide elements")
    ap.add_argument("--title", default=None, help="override the cover title")
    ap.add_argument("--dark", action="store_true", help="use the dark kit instead of the light one")
    a = ap.parse_args(argv)
    out = a.out or str(Path(a.html).with_suffix(".pptx"))
    convert(a.html, out, kicker=a.kicker, selector=a.selector, title=a.title,
            speaker=a.speaker, date=a.date, mode="dark" if a.dark else "light")


if __name__ == "__main__":
    main()
