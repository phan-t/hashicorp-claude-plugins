# IBM design system reference

These are the values the shipped template actually carries, read out of its theme. They are
here so you can *check* output, not so you can restate them in code. Setting any of them from
a build script is a bug — fill placeholders and let the template resolve them.

## The template

`assets/ibm-brand-template.pptx` is the official **IBM presentation template v2.0 (Plex)**,
converted from `.potx` and stripped to what a builder needs:

- 1 slide master, 48 slide layouts, 1 theme, and the media those layouts reference
- no demo slides, no demo charts/diagrams/embedded workbooks, no file thumbnail
- 21 MB → 144 KB, which is why it can live in a plugin

To refresh it from a newer IBM template, repeat that strip: drop `ppt/slides/*`, remove the
slide relationships and `<p:sldIdLst>`, garbage-collect unreachable parts, and rewrite the
main part's content type from `…presentationml.template.main+xml` to
`…presentationml.presentation.main+xml`. python-pptx refuses to open a `.potx` otherwise.

## Stage

**26.67 × 15.0 in** (16:9). Not the 13.33 × 7.5 in default — IBM works at double scale, so
type sizes in the template read roughly double what you would write by hand. Content margin
is 0.63 in; columns sit on a 6.67 in pitch with a 0.63 in gutter.

## Type

| Role | Family |
|---|---|
| Major (headings) | IBM Plex Sans Light |
| Minor (body) | IBM Plex Sans Light |
| Code | IBM Plex Mono |

Title sizes on the master run **68 / 84 / 132 pt**, with the master's own guidance:
*"5 lines maximum, sentence case."* Weight comes from the family name, not a bold flag —
`**bold**` in body text is for lead-ins, not headings.

The fonts are named in the theme, not embedded. Install IBM Plex locally or PowerPoint
substitutes.

## Color

Theme colors, as the template defines them:

| Slot | Value | |
|---|---|---|
| accent1 | `#0f62fe` | IBM Blue 60 — the primary accent, and hyperlink color |
| accent2 | `#a56eff` | Purple 50 |
| accent3 | `#003a6d` | Blue 90 |
| accent4 | `#009d9a` | Teal 60 |
| accent5 | `#9f1853` | Magenta 70 |
| accent6 | `#fa4d56` | Red 50 |
| dk1 / lt1 | `#ffffff` / `#000000` | **inverted**, see below |

The theme stores dk1 as white and lt1 as black, and the master's `clrMap` compensates with
`bg1="dk1" tx1="lt1"`. Net effect: **white background, black text.** Do not "fix" the theme
to look conventional — the map is what makes every layout resolve correctly, and tools that
ignore `clrMap` will render these decks inverted.

Carbon grays used by `Deck.code()`, the one place this skill draws its own shape:
`#161616` (Gray 100, panel), `#e0e0e0` (Gray 20, code text), `#6f6f6f` (Gray 60, caption).

## Rendering note

macOS Quick Look does not render these files — it shows the package's embedded thumbnail, and
the shipped template has none, so `qlmanage` output is a black frame regardless of content.
That is a limitation of the previewer, not a defect in the deck. Verify in PowerPoint or
Keynote, or structurally with python-pptx.
