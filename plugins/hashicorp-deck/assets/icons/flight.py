"""flight — find a Flight icon and print it ready to paste into an HTML deck.

    python flight.py search lock          # names, categories and keywords that match
    python flight.py ico key              # <div class="ico" data-icon="key"><svg>…</svg></div>
    python flight.py svg key              # the bare inline <svg>

Standard library only, so the HTML skill needs nothing installed. The icons are
Flight's 24 px single-colour set, vendored in `flight/` beside this file; they
fill with `currentColor`, so the surrounding CSS sets their colour.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

ICON_DIR = Path(__file__).resolve().with_name("flight")


def catalog():
    rows = (ICON_DIR / "catalog.tsv").read_text(encoding="utf-8").splitlines()[1:]
    return [tuple(r.split("\t")) for r in rows]


def search(term):
    """Rows whose name or keywords have a word starting with `term`, so that
    "lock" finds unlock and cloud-lock but not clock."""
    word = re.compile(rf"\b{re.escape(term.lower())}")
    return [r for r in catalog() if word.search(f"{r[0]} {r[2].lower()}")]


def svg(name):
    path = ICON_DIR / f"{name}-24.svg"
    if not path.exists():
        names = [r[0] for r in catalog()]
        near = difflib.get_close_matches(name, names, n=4, cutoff=0.5)
        hint = f"; did you mean {', '.join(near)}?" if near else ""
        raise SystemExit(f"no Flight icon {name!r}{hint}")
    text = path.read_text(encoding="utf-8").strip()
    # Size comes from CSS, and the icon is decoration beside a heading.
    text = re.sub(r' (width|height)="24"', "", text, count=2)
    return text.replace("<svg ", '<svg aria-hidden="true" ', 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("search").add_argument("term")
    sub.add_parser("ico").add_argument("name")
    sub.add_parser("svg").add_argument("name")
    a = ap.parse_args(argv)
    if a.cmd == "search":
        hits = search(a.term)
        for name, category, keywords in hits:
            print(f"{name:<28} {category:<14} {keywords}")
        if not hits:
            print(f"no icon matches {a.term!r}", file=sys.stderr)
            return 1
    elif a.cmd == "ico":
        print(f'<div class="ico" data-icon="{a.name}">{svg(a.name)}</div>')
    else:
        print(svg(a.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
