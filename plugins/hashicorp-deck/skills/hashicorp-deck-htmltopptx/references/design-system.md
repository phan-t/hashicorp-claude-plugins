# HashiCorp design system reference

These are the values the shipped template actually carries, read out of its layouts. They
are here so you can *check* output, not so you can restate them in code. Setting any of
them from a build script is a bug — fill placeholders and let the layout resolve them.

## The template

`assets/hashicorp-brand-template.pptx` is the official **HashiCorp Light-mode CY26
Presentation Kit v4**, stripped to what a builder needs:

- 1 slide master, 47 slide layouts, 1 theme, the embedded Inter faces, and the media those
  layouts reference
- no demo slides, no notes slides, no revision or authorship history
- 26 MB → 6 MB, which is why it can live in a plugin

**Two layouts were dropped**: *Do cloud right* and *Dark*. Neither has a single
placeholder — they are pure decoration, so nothing could be built on them — and between
them they carried an 15.7 MB EMF and 2.1 MB of PNG, two-thirds of the whole package.

To refresh from a newer kit, repeat the strip: drop `ppt/slides/*`, `ppt/notesSlides/*`,
`ppt/changesInfos/*`, `authors.xml` and `revisionInfo.xml`; remove `<p:sldIdLst>` and the
slide relationships from `presentation.xml`; drop those two layouts from the master's
`<p:sldLayoutIdLst>` and its rels; delete media no surviving layout references; downsample
the remaining PNGs to 1600 px on the long edge (they are 4K glow overlays scaled onto a
10-inch stage, so nothing is visibly lost); then prune `[Content_Types].xml` of every
`<Override>` whose part no longer exists.

### Verified against the source kit

The strip was checked against `HashiCorp_Lightmode_CY26_Kit_v4.pptx`, not just eyeballed:

- **All 47 surviving layouts are byte-identical** to the original (ignoring relationship ids,
  which renumber when media is dropped). The theme, `tableStyles.xml`, `presProps.xml`,
  `viewProps.xml`, the notes and handout masters, and all ten embedded Inter font files are
  byte-identical too.
- **The master differs only** by the two removed `<p:sldLayoutId>` entries and a CRLF→LF in
  the XML prolog. Layout ids and their order are otherwise untouched.
- **Rendered side by side** in PowerPoint — the same layout from each file — General Divider
  and Thank You came out at a mean difference of **0.12/255 with not one channel over
  8/255**, and Blank-Gradient's background at **max 2/255**. The downsampled glow art is
  indistinguishable at the size it is drawn.

Re-run that comparison after any refresh. The layouts and fonts should stay byte-identical;
only the media is expected to differ, and only below the perceptual floor.

## Stage

**10.0 × 5.63 in** (16:9) — PowerPoint's older on-screen-show size, not the 13.33 × 7.5 in
default. Type sizes therefore read at face value; a 26 pt title really is 26 pt. Content
sits in a 9.1 in measure at x = 0.45. The title/subtitle band runs y = 0.40 → 1.20, content
starts at y = 1.60, and the page number sits at y = 5.28.

## The theme is not the brand

This is the one structural thing to know about this kit. Its theme is **stock Microsoft
Office**: Aptos Display / Aptos, `accent1` = `#156082`, `accent2` = `#e97132`. None of that
is HashiCorp. Every layout overrides it in its own `<a:lstStyle>`, stamping Inter and
HashiCorp colour onto each placeholder.

The practical consequences:

- **Filling a placeholder is safe.** A run with no explicit formatting inherits the
  layout's list style and comes out on-brand.
- **Drawing a shape is not.** A textbox you add inherits the *theme* — Aptos, Office blue —
  because there is no layout style behind it. Anything drawn must name its own font and
  colour, which is why `code()`, `table()`, `chart()` and the `quote()` attribution do.
- **`tableStyles.xml` is empty**, so a python-pptx table falls back to PowerPoint's generic
  blue "Medium Style 2 - Accent 1". `hashicorp_deck.style_cell()` overrides every cell.
- **Native charts inherit Office blue and orange.** `Deck.chart()` therefore sets series
  colours explicitly, from `CHART_COLORS`.

## Type

| Role | Family | Where |
|---|---|---|
| Slide titles | Inter SemiBold | 26 pt on content layouts, 40 pt on covers and dividers, 48 pt on the title page |
| Subtitles / ledes | Inter Light | 16 pt |
| Body and bullets | Inter | 12 pt; 11 pt in the icon containers |
| Captions, metric detail | Inter Medium | 12 pt |
| Metric numbers | Inter | 48 pt, gradient-filled |
| Pull-quote | Inter | 36 pt, gradient-filled |
| Eyebrow label | Inter Light | 11 pt, grey |
| Code | JetBrains Mono | 9 pt — the brand mono, and the only face not in this file |

Inter is **embedded** in the template, so Windows PowerPoint renders correctly with nothing
installed. macOS PowerPoint ignores embedded fonts and substitutes unless Inter is
installed locally. JetBrains Mono is never embedded.

## Color

The signature **glow gradient** — four stops at 45° — is what makes a HashiCorp slide look
like one. The layouts apply it to metric numbers, the metric rules and the pull-quote, so
you get it by filling those slots and nothing else:

| Stop | Position |
|---|---|
| `#6c81ff` | 0% |
| `#c08dff` | 25% |
| `#ff8791` | 75% |
| `#f9b571` | 100% |

Neutrals the kit uses directly:

| Value | Role |
|---|---|
| `#000000` | Body and title text |
| `#646466` | Page numbers, captions, secondary text |
| `#d9d9d9` | Hairline rules |
| `#f7f7f8` | Tinted container fills |

Product hues, read off the kit's own "Product colors" slide. Use one at a time, as an
accent — never as a slide background:

| Product | Value | The kit's phrase for it |
|---|---|---|
| Terraform | `#7b42bc` | Infrastructure as code |
| Packer | `#63d0ff` | Build and manage images |
| Waypoint | `#62d4dc` | Internal developer platform |
| Nomad | `#60dea9` | Deployment as code |
| Vault | `#ffcf25` | Identity-based security |
| Boundary | `#ec585d` | Identity-based user access |
| Consul | `#dc477d` | Service-based networking |

These are the kit's values, not [Helios](https://helios.hashicorp.design/foundations/colors)
ones. Helios is the product UI system and publishes darker hues for Consul (`#e03875`),
Nomad (`#06d092`), Boundary (`#f24c53`), Packer (`#02a8ef`) and Waypoint (`#14c6cb`). The kit
governs slides because this skill re-typesets onto the kit's own master; Helios governs
diagrams, which is what `hashicorp-diagram` follows. Do not reconcile this table to Helios.

`hashicorp_deck.GLOW`, `.PRODUCT` and `.CHART_COLORS` carry these. Chart series run the
four glow stops, then Waypoint teal and Nomad green — six categoricals that stay in the
family and hold up on a light ground.

## Dark mode

`Deck(mode="dark")` uses a template derived from this one — same layouts, same slots, same
gradients, inverted neutrals — so everything in this file applies there with the palette
swapped. `references/dark.md` has the derivation and the dark values. Re-run
`assets/make_dark.py` after refreshing this template, or the two drift.

## Relationship to the sibling HTML skill

`hashicorp-deck-html` builds web decks on a slightly different palette: a monochrome
foundation with `--tf-purple` accents and two named gradients (`--grad-ilm`,
`--grad-slm`). Those are the web brand; this file is the deck kit's own. They agree on
Inter, JetBrains Mono and the product hues, and diverge on gradients — the kit uses one
four-stop glow everywhere. **When converting, take the kit's version.** The whole point of
the conversion is that the source deck's colours are discarded.

## A kit inconsistency worth knowing

The copyright line is baked into the layouts as static art, and it is not uniform: the
product covers (*Cover - Terraform* and its siblings) read **©2025 HASHICORP**, while
*General Divider* and *Thank You* read **©2026**. That is HashiCorp's own drift, visible in
the shipped kit. It is layout art, so a build script cannot change it — edit the layout in
PowerPoint if a deck must be consistent, or avoid mixing the two families in one deck.

## Rendering note

Verify in PowerPoint, or structurally with python-pptx. macOS Quick Look shows a package's
embedded thumbnail rather than rendering it, and generated decks carry none, so `qlmanage`
output tells you nothing about the file.

If you script a visual check, capture **PowerPoint's window**, not the display:
`screencapture -l <windowID>` reads that window's own buffer. A full-screen `screencapture`
is both unreliable — it catches half-drawn frames and blank slides that are actually fine —
and a privacy problem, since it records whatever else is on screen. Get the window id from
`Quartz.CGWindowListCopyWindowInfo` and match on owner name "Microsoft PowerPoint". Note
that PowerPoint for Mac's AppleScript `save ... as save as PNG` / `save as PDF` reports
success and writes nothing, so exporting is not an alternative.
