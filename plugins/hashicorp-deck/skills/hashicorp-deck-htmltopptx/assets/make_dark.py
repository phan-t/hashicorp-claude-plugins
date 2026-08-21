"""Regenerate the dark template from the light CY26 kit v4.

    python make_dark.py        # rewrites hashicorp-darkv4-template.pptx

Run this whenever `hashicorp-brand-template.pptx` is refreshed: the dark template
is *derived*, and will otherwise drift from the light one it is supposed to
mirror. It is checked in rather than generated at import time only because the
per-pixel lockup pass is too slow to run on every `Deck()`.

Derive a dark template from the light CY26 kit v4, structure untouched.

The point is parity: same layout names, same placeholder indices, same list
styles, same glow gradients, same Inter. Only the neutrals flip. That makes
dark mode a template swap rather than a second grammar.
"""
import io, re, shutil, tempfile, zipfile, pathlib
from PIL import Image

A = pathlib.Path(__file__).parent
LIGHT = A / "hashicorp-brand-template.pptx"
V2 = A / "hashicorp-dark-template.pptx"          # only for its white lockup art
OUT = A / "hashicorp-darkv4-template.pptx"
W = pathlib.Path(tempfile.mkdtemp(prefix="hcdark-"))

# Explicit neutrals, light -> dark. Applied simultaneously so the two greys that
# swap places do not chase each other. Brand hues are deliberately absent: the
# glow stops and product colours read correctly on black already.
NEUTRALS = {
    "000000": "FFFFFF",   # ink
    "D9D9D9": "343536",   # hairline rules
    "646466": "9B9B9B",   # secondary text — must lighten, not darken
    "F7F7F8": "1A1A1A",   # tinted container fills
    "505052": "BFBFC0",
    "BFBFC0": "505052",
    "9B9B9B": "646466",
    "FFFBED": "1F1D16", "F1E5FF": "1A1626", "E9ECFF": "16181F", "FBDDDF": "241A1B",
    "FFF6D8": "231F14",
}

if W.exists(): shutil.rmtree(W)
with zipfile.ZipFile(LIGHT) as z: z.extractall(W)

def swap_neutrals(xml):
    return re.sub(r'(srgbClr val=")([0-9A-Fa-f]{6})(")',
                  lambda m: m.group(1) + NEUTRALS.get(m.group(2).upper(), m.group(2)) + m.group(3),
                  xml)


def reroot_derived_greys(xml):
    """Re-base `bg1 + lumMod` greys onto tx1.

    The kit derives its muted greys by darkening the *background* — a 65% lumMod
    on bg1, which is white in light mode. Flip the ground to black and every one
    of them becomes black on black: the eyebrow label, the closing line, the
    presenter details, the product-cover credits, twenty slots in all. Rooting
    them at tx1 instead keeps the intent (a grey one step off the text colour)
    and inverts correctly. A plain bg1 with no lumMod is a real background fill
    and is left alone.
    """
    return re.sub(r'<a:schemeClr val="bg1">(\s*<a:lumMod [^>]*/>\s*)</a:schemeClr>',
                  r'<a:schemeClr val="tx1">\1</a:schemeClr>', xml)

# 1. the whole ground flips from one place: the master's colour map -----------
mp = W / "ppt/slideMasters/slideMaster1.xml"
m = mp.read_text(encoding="utf-8")
before = re.search(r'<p:clrMap[^/]*/>', m).group(0)
# Both pairs flip. tx2 is easy to miss — it is only used twice, on the cover
# subtitle and the eyebrow title, but it resolves to a dark navy that is
# unreadable on black.
for a, b in (('bg1="lt1"', 'bg1="dk1"'), ('tx1="dk1"', 'tx1="lt1"'),
             ('bg2="lt2"', 'bg2="dk2"'), ('tx2="dk2"', 'tx2="lt2"')):
    m = m.replace(a, "\x00" + b + "\x00")
m = m.replace("\x00", "")
print("clrMap:", before, "->", re.search(r'<p:clrMap[^/]*/>', m).group(0))
mp.write_text(reroot_derived_greys(swap_neutrals(m)), encoding="utf-8")

# 2. explicit neutrals in every layout ----------------------------------------
for f in (W / "ppt/slideLayouts").glob("slideLayout*.xml"):
    f.write_text(reroot_derived_greys(swap_neutrals(f.read_text(encoding="utf-8"))),
                 encoding="utf-8")

# 3. art -----------------------------------------------------------------------
def whiten_neutral(data, thresh=40):
    """Invert only the near-grey pixels, so a coloured mark keeps its hue while
    the black wordmark beside it turns white."""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if max(r, g, b) - min(r, g, b) < thresh:
                px[x, y] = (255 - r, 255 - g, 255 - b, a)
    buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
    return buf.getvalue()

media = W / "ppt/media"
# the product-cover lockups pair a coloured mark with black type
for n in ["image12.png", "image13.png", "image14.png", "image15.png",
          "image16.png", "image17.png", "image18.png", "image19.png"]:
    p = media / n
    if p.exists():
        p.write_bytes(whiten_neutral(p.read_bytes()))
print(f"whitened {8} product lockups (coloured marks preserved)")

# the corporate lockup on General Divider / Thank You is a black EMF; the dark
# kit ships the same lockup in white, so that art is borrowed rather than faked
with zipfile.ZipFile(V2) as z:
    white_lockup = z.read("ppt/media/image1.png")
(media / "logo_white.png").write_bytes(white_lockup)
swapped = 0
for f in (W / "ppt/slideLayouts/_rels").glob("*.rels"):
    t = f.read_text(encoding="utf-8")
    if "image3.emf" in t:
        f.write_text(t.replace("../media/image3.emf", "../media/logo_white.png"),
                     encoding="utf-8")
        swapped += 1
(media / "image3.emf").unlink(missing_ok=True)
print(f"swapped the black EMF lockup for the kit's white one on {swapped} layout(s)")

# the EMF is gone, so its content-type default goes with it
ct = W / "[Content_Types].xml"
ct.write_text(re.sub(r'<Default Extension="emf"[^>]*/>', "",
                     ct.read_text(encoding="utf-8")), encoding="utf-8")

# python-pptx keeps a thumbnail relationship the stripped package no longer has
rp = W / "_rels/.rels"
rp.write_text(re.sub(r'<Relationship[^>]*Target="docProps/thumbnail\.jpeg"[^>]*/>', "",
                     rp.read_text(encoding="utf-8")), encoding="utf-8")

if OUT.exists(): OUT.unlink()
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(W.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(W).as_posix())
shutil.rmtree(W, ignore_errors=True)
print(f"wrote {OUT} — {OUT.stat().st_size/1e6:.2f} MB")
