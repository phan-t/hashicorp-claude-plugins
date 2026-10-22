"""flight_icons — HashiCorp's Flight icons as native PowerPoint vector shapes.

The plugin vendors Flight's 24 px single-colour icons once, in
`plugins/hashicorp-deck/assets/icons/flight/`, so the HTML skill and this one
draw from the same files. python-pptx cannot place an SVG, and a PNG would need
a rasteriser (Chrome or Cairo) on every machine that builds a deck. Flight
icons are nothing but filled `<path>` elements, so this module translates their
path data into DrawingML custom geometry instead: the icon lands as an ordinary
shape, sharp at any zoom and recolourable in PowerPoint, with nothing to install
beyond python-pptx.

    from flight_icons import names, custgeom
    "key" in names()            # True
    custgeom("key")             # <a:custGeom> element, 24 x 24 path space

Each SVG `<path>` becomes one `<a:path>`. Arcs and quadratics are converted to
cubic Béziers; DrawingML's own `arcTo` uses a different parameterisation and is
not worth the second code path.
"""

import difflib
import math
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

from lxml import etree
from pptx.oxml.ns import qn

#: plugins/hashicorp-deck/assets/icons/flight, shared with hashicorp-deck-html.
ICON_DIR = Path(__file__).resolve().parents[3] / "assets" / "icons" / "flight"

#: Path-space units per SVG unit. 1000 keeps three decimals of a 24-unit icon,
#: which is finer than Flight's own export precision.
_SCALE = 1000
_SVG_NS = "{http://www.w3.org/2000/svg}"
_NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


@lru_cache(maxsize=1)
def names():
    """Every icon name available, without the `-24` suffix."""
    return frozenset(p.stem[:-3] for p in ICON_DIR.glob("*-24.svg"))


def path_for(name):
    """The SVG file for `name`, or a KeyError that suggests the nearest names."""
    if name not in names():
        near = difflib.get_close_matches(name, names(), n=4, cutoff=0.5)
        hint = f"; did you mean {', '.join(near)}?" if near else ""
        raise KeyError(f"no Flight icon {name!r}{hint} "
                       f"(search {ICON_DIR / 'catalog.tsv'} by keyword)")
    return ICON_DIR / f"{name}-24.svg"


def svg_paths(name):
    """The `d` attribute of every path in the icon, in document order."""
    root = ET.parse(path_for(name)).getroot()
    return [el.get("d") for el in root.iter(f"{_SVG_NS}path") if el.get("d")]


# -- SVG path data -> absolute cubic segments ---------------------------------
def _tokens(d):
    """Yield command letters and numbers. Arc flags are read by `_parse`."""
    i = 0
    while i < len(d):
        c = d[i]
        if c.isalpha():
            yield c
            i += 1
        elif c in " ,\t\r\n":
            i += 1
        else:
            m = _NUM.match(d, i)
            if not m:
                raise ValueError(f"bad path data at {i}: {d[i:i + 12]!r}")
            yield m.group()
            i = m.end()


def _parse(d):
    """Return subpaths as lists of ('M', x, y) / ('L', x, y) / ('C', 6 numbers) / ('Z',)."""
    toks, i = list(_tokens(d)), 0
    segs, cmd = [], None
    x = y = sx = sy = 0.0
    last_c = last_q = None          # reflected control points for S and T
    closed = False

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def flag():
        # Arc flags are single digits that SVG lets run into the next number:
        # in "a.75.75 0 011.5 0" the tokeniser reads "011.5", which is
        # large=0, sweep=1, x=1.5.
        nonlocal i
        t = toks[i]
        if t in ("0", "1"):
            i += 1
            return int(t)
        toks[i] = t[1:]
        return int(t[0])

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                segs.append(("Z",))
                x, y = sx, sy
                last_c = last_q = None
                closed = True
                continue
        elif cmd is None:
            raise ValueError(f"path data must start with a command: {d[:20]!r}")
        up, rel = cmd.upper(), cmd.islower()
        if closed and up != "M":
            # SVG lets drawing carry on from the start point after a close;
            # DrawingML needs an explicit moveTo there, and PowerPoint drops
            # the whole shape without one (Flight's auth0 does this).
            segs.append(("M", x, y))
        closed = False
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if up == "M":
            x, y = ox + num(), oy + num()
            sx, sy = x, y
            segs.append(("M", x, y))
            cmd = "l" if rel else "L"       # extra pairs after M are lines
            last_c = last_q = None
        elif up == "L":
            x, y = ox + num(), oy + num()
            segs.append(("L", x, y))
            last_c = last_q = None
        elif up == "H":
            x = ox + num()
            segs.append(("L", x, y))
            last_c = last_q = None
        elif up == "V":
            y = oy + num()
            segs.append(("L", x, y))
            last_c = last_q = None
        elif up == "C":
            c = [ox + num(), oy + num(), ox + num(), oy + num(), ox + num(), oy + num()]
            segs.append(("C", *c))
            x, y, last_c, last_q = c[4], c[5], (c[2], c[3]), None
        elif up == "S":
            x1, y1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c else (x, y)
            c = [x1, y1, ox + num(), oy + num(), ox + num(), oy + num()]
            segs.append(("C", *c))
            x, y, last_c, last_q = c[4], c[5], (c[2], c[3]), None
        elif up in "QT":
            if up == "Q":
                qx, qy = ox + num(), oy + num()
            else:
                qx, qy = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q else (x, y)
            ex, ey = ox + num(), oy + num()
            segs.append(("C", x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y),
                         ex + 2 / 3 * (qx - ex), ey + 2 / 3 * (qy - ey), ex, ey))
            x, y, last_c, last_q = ex, ey, None, (qx, qy)
        elif up == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = flag(), flag()
            ex, ey = ox + num(), oy + num()
            segs.extend(("C", *c) for c in _arc(x, y, rx, ry, rot, large, sweep, ex, ey))
            x, y, last_c, last_q = ex, ey, None, None
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    return segs


def _arc(x1, y1, rx, ry, phi, large, sweep, x2, y2):
    """SVG endpoint arc -> cubic Béziers, per SVG 1.1 appendix F.6.5."""
    if (x1, y1) == (x2, y2):
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [(x1, y1, x2, y2, x2, y2)]
    phi = math.radians(phi % 360)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:                                  # radii too small: scale up
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi

    n = max(1, math.ceil(abs(dt) / (math.pi / 2) - 1e-9))
    step = dt / n
    k = 4 / 3 * math.tan(step / 4)
    out, t = [], t1

    def pt(a):
        ex, ey = rx * math.cos(a), ry * math.sin(a)
        return cp * ex - sp * ey + cx, sp * ex + cp * ey + cy

    def dpt(a):
        ex, ey = -rx * math.sin(a), ry * math.cos(a)
        return cp * ex - sp * ey, sp * ex + cp * ey

    for _ in range(n):
        p0, p3 = pt(t), pt(t + step)
        d0, d3 = dpt(t), dpt(t + step)
        out.append((p0[0] + k * d0[0], p0[1] + k * d0[1],
                    p3[0] - k * d3[0], p3[1] - k * d3[1], p3[0], p3[1]))
        t += step
    out[-1] = out[-1][:4] + (x2, y2)            # land exactly on the endpoint
    return out


# -- DrawingML ---------------------------------------------------------------
def _pt(parent, x, y):
    el = etree.SubElement(parent, qn("a:pt"))
    el.set("x", str(round(x * _SCALE)))
    el.set("y", str(round(y * _SCALE)))


def custgeom(name):
    """An `<a:custGeom>` drawing `name` in a 24 x 24 path space.

    The path space is stretched to the shape's frame, so the caller sizes the
    icon by sizing the shape, and colours it with the shape's fill.
    """
    geom = etree.Element(qn("a:custGeom"))
    for tag in ("a:avLst", "a:gdLst", "a:ahLst", "a:cxnLst"):
        etree.SubElement(geom, qn(tag))
    rect = etree.SubElement(geom, qn("a:rect"))
    for k, v in (("l", "l"), ("t", "t"), ("r", "r"), ("b", "b")):
        rect.set(k, v)
    lst = etree.SubElement(geom, qn("a:pathLst"))
    for d in svg_paths(name):
        path = etree.SubElement(lst, qn("a:path"))
        path.set("w", str(24 * _SCALE))
        path.set("h", str(24 * _SCALE))
        for seg in _parse(d):
            op = seg[0]
            if op == "Z":
                etree.SubElement(path, qn("a:close"))
                continue
            tag = {"M": "a:moveTo", "L": "a:lnTo", "C": "a:cubicBezTo"}[op]
            el = etree.SubElement(path, qn(tag))
            pts = seg[1:]
            for j in range(0, len(pts), 2):
                _pt(el, pts[j], pts[j + 1])
    return geom
