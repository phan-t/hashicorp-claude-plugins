# Dark mode

```python
Deck(mode="dark")        # default dark: the light kit, recoloured. Full parity.
Deck(mode="dark-v2")     # HashiCorp's own dark kit. A different, older design.
```

## Why the default dark is derived, not the official kit

HashiCorp ships a dark kit, but it is a **different generation**: the light kit is at v4 and
the dark kit is still at v2 from the same June 2025 drop. They have nothing in common —

| | Light v4 | Official dark v2 |
|---|---|---|
| Layout names in common | — | **none** |
| Layouts | 49, all named | 74, of which 61 have no placeholders |
| Naming | `3 Metric`, `Agenda` | `CUSTOM_1_2_2_1_1_1_1_1_1_1_1_1` |
| Slide masters | 1 | 4 |
| Metric layouts | 2 Metric, 3 Metric | **none** |
| Glow-gradient text | metric numbers, pull-quote | **none anywhere** |
| Fonts | Inter ×5 | Inter ×6 + Poppins ×3 |
| Stage | 10.0 × 5.63 in | 10.0 × 5.625 in |

— so a deck built in `dark-v2` cannot look like its light twin, and `metrics()` and
`product_cover()` have nowhere to go.

`mode="dark"` solves that by **deriving the dark template from the light one**. Every layout
name, placeholder index, list style, bullet, gradient and font is literally the same object
light mode uses; only the neutrals flip. Verified: layout names identical, stage identical,
and every layout's placeholder set matches light index-for-index and pixel-for-pixel.

That means dark mode needs no layout map, no slot map and no unsupported list — it shares
`_LIGHT_STRUCTURE` wholesale, and `metrics()`, `product_cover()`, the glow gradient and the
icon containers all work exactly as they do in light.

**It is a derived asset, not HashiCorp's official dark design.** For internal and customer
decks that is usually what you want — it matches the light deck. If you need the
brand-sanctioned artefact, use `dark-v2` and accept the reduced feature set.

## How the derivation works

`assets/make_dark.py` regenerates `hashicorp-darkv4-template.pptx` from
`hashicorp-brand-template.pptx`. **Re-run it whenever the light template is refreshed**, or
the two will drift:

```
python assets/make_dark.py
```

Three transforms, and nothing else:

1. **The colour map flips, once, on the master.** `bg1="lt1" tx1="dk1"` becomes
   `bg1="dk1" tx1="lt1"`, and the same for `bg2`/`tx2`. All 47 layouts inherit their
   background from the master, so the entire ground turns over from one edit. Forgetting the
   `tx2` pair is the easy mistake — it is used only twice, on the cover subtitle and the
   eyebrow title, and it resolves to a dark navy that vanishes on black.
2. **Explicit neutrals are remapped** (`NEUTRALS` in the script): ink, hairlines, secondary
   text and tinted fills. The glow stops and product hues are deliberately left alone — they
   read correctly on black already, which is why the metric numbers and pull-quote keep their
   gradient.
3. **Art is handled by kind.** The kit's decorative glow overlays are translucent and work on
   black untouched. The product lockups pair a coloured mark with black type, so only their
   *near-grey* pixels are inverted — the Terraform purple survives, the wordmark turns white.
   The corporate lockup is a black EMF with no such trick available, so the white version is
   borrowed from the official dark kit.

## The dark palette

| Role | Light | Dark |
|---|---|---|
| Ground | `#ffffff` | `#000000` |
| Ink | `#000000` | `#ffffff` |
| Secondary text | `#646466` | `#9b9b9b` |
| Hairline rules | `#d9d9d9` | `#343536` |
| Tinted fills | `#f7f7f8` | `#1a1a1a` |
| Code panel | `#171717` | `#242424` |

The code panel is the one value that does not simply invert: on a black ground a `#171717`
panel is invisible, so the dark panel lifts *away* from the background instead of sinking
into it.

## If you use `dark-v2`

Its quirks, all handled but worth knowing:

- **`metrics()` and `product_cover()` raise**, naming `mode="dark"` as the alternative.
  `columns(headings=…)` degrades instead — headings fold in as bold lead-ins.
- **The section divider is white** and ships no placeholder; HashiCorp's own slides draw the
  title as a textbox, so `section()` does too, in `dk1`.
- **More slots arrive bulleted than should be** — cover lines, agenda items, presenter
  details, the closing line. `Deck.unbullet()` clears those field-like slots; content columns
  keep their bullets.
- **Only master 1 survives the strip**; it carries all 13 fillable layouts and python-pptx
  exposes only the first master anyway.

If HashiCorp ever ships a dark kit at v4 parity, point `DARK_TEMPLATE` at it and delete
`make_dark.py` — that is the outcome worth asking their brand team for.
