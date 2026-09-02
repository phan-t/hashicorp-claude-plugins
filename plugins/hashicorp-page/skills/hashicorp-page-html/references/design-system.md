# Design system reference

Authoritative tokens, typography, and layout rules for a HashiCorp-style HTML page document.
Copy these values verbatim; do not invent colours or fonts. The complete stylesheet is in
`assets/template.html` — start there rather than re-deriving these rules.

## Brand tokens (`:root`)

```css
:root{
  --black:#0c0c0e; --white:#ffffff;
  --gray-bg:#f7f8fa; --gray-line:#e4e7ec; --gray-text:#656a76; --gray-faint:#9aa0ab;

  /* Product hues, Helios. Accents only, never a background wash. */
  --terraform:#7B42BC; --terraform-bright:#A067DA;
  --vault:#FFCF25; --boundary:#F24C53; --consul:#E03875; --packer:#02A8EF; --nomad:#06D092;

  --grad-security:linear-gradient(90deg,#FFCF25 0%,#E03875 60%,#F24C53 100%);
  --grad-infra:linear-gradient(90deg,#02A8EF 0%,#7B42BC 100%);

  --font-sans:'Inter','Helvetica Neue',Helvetica,Arial,sans-serif;
  --font-mono:'IBM Plex Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  --max:1080px;

  /* Chart tokens. Categorical c1-c4 in fixed order; status three-way. */
  --c1:#7B42BC; --c2:#02A8EF; --c3:#E03875; --c4:#06D092;
  --st-good:#06D092; --st-warn:#FFCF25; --st-crit:#F24C53;
  --grid:#eceef2;
}
```

## Which palette governs a page

Three authorities publish HashiCorp product colours and they do not agree.

- **[Helios](https://helios.hashicorp.design/foundations/colors)** is the product UI system.
  **It governs pages**, for the same reason it governs diagrams: a page document is read on a
  screen in a browser, not projected from a slide master.
- The **CY26 presentation kit** governs slides. `hashicorp-deck-html` follows it, because a deck
  converted by `hashicorp-deck-htmltopptx` is re-typeset onto that kit's master and would shift
  colour otherwise. Its hues are lighter, tuned for projection. Do not carry them into a page.
- **Marketing brand guidelines** cover logo usage and the two gradients, which all three share.

| Product | Helios — pages and diagrams | CY26 kit — decks |
|---|---|---|
| Terraform | `#7B42BC` | `#7B42BC` — agrees |
| Vault | `#FFCF25` | `#FFCF25` — agrees |
| Consul | `#E03875` | `#dc477d` |
| Nomad | `#06D092` | `#60dea9` |
| Boundary | `#F24C53` | `#ec585d` |
| Packer | `#02A8EF` | `#63d0ff` |

`--terraform-bright:#A067DA` is a page-local tint for hover states and purple on the black
hero. It is not a product identity colour, and it differs from the deck skill's `#a067e8`
because that value is the kit's, not Helios'.

**Vault was `#FFD814` in all five source documents.** That matched neither authority and has
been reconciled here, the same drift that was corrected in `hashicorp-deck-html`. Documents
built before this skill existed carry the old value; leave them, do not retro-fit.

## Colour usage rules

- **Backgrounds** are white, `--gray-bg` (`.alt` sections), or `--black` (top bar, hero,
  footer, `.covstrip`). Never a saturated colour.
- **Gradients** appear in exactly three places: the 4px hero bottom border, the 56x4 `.keyline`
  under a section heading, and one accented phrase in the H1. Never as a fill.
- Pick **one gradient per document** and use it for the hero border and most keylines:
  `--grad-infra` for capacity, coverage, pipeline and operating-model work, `--grad-security`
  for delivery and impact reporting. Switch a single keyline to the other gradient to mark a
  section that changes subject.
- **Product hues encode that product and nothing else.** A `.chip.vault` means Vault. A card's
  `acc-*` top border is the exception: it is an ordering device across a row of cards, and any
  hue may be used as long as adjacent cards differ.
- **Status is three-way**, `--st-good` / `--st-warn` / `--st-crit`, and never any other hue.

## Chart colours

`--c1` through `--c4` are the categorical ramp, always used in that order so the same series
takes the same colour in every figure across a document. Never reorder them per chart, and
never introduce a fifth: if a chart needs five categories it needs a different chart. The four
were validated with the `dataviz` skill's `validate_palette.js` for light-background contrast
and colour-blind separation; changing one invalidates the set.

Charts are never colour-only. Every bar carries its value in `.hval` or `.vv`, every stacked
segment carries a label, and every figure has a `.legend` or a `title` attribute.

## Typography

```css
.hero h1{font-size:clamp(32px,5vw,50px);line-height:1.08;font-weight:700;letter-spacing:-0.02em;text-wrap:balance}
.hero p.lede{font-size:17px;max-width:56rem}
.seclabel h2{font-size:clamp(22px,3vw,30px);font-weight:700;letter-spacing:-0.015em}
section h3.sub{font-size:17px;font-weight:600}
body{font-size:16px;line-height:1.6}
```

- **Sans carries prose.** Mono carries structure only: eyebrows, section indices, table headers,
  pills, KPI lines, captions, source notes, timeline dates. Mono is never used for a sentence.
- **Sentence case throughout.** Uppercase belongs to mono micro-labels alone, always with
  letter-spacing between `.04em` and `.08em`.
- **Numbers are mono and tabular** — `font-variant-numeric:tabular-nums` on every `.stat .n`,
  `td.num`, `.hn .n` and bar value, so columns align.
- Prose is capped at `62rem` and the lede at `56rem`. The page itself is capped at 1080px.
  Long measure is what makes a document unreadable; do not widen it.

## Webfonts

Inter and IBM Plex Mono load from Google Fonts. Both stacks fall back to `Helvetica Neue` and
the system mono, which is what four of the five source documents shipped with, so **deleting
the three `<link>` tags in `<head>` gives a fully offline file with no layout shift.** Do that
whenever the document is confidential or will be read on an air-gapped machine, and say so.

## Page rhythm

- `section{padding:54px 0}` with a 1px bottom rule; alternate `.alt` so no two consecutive
  sections share a background.
- Sections are numbered `01`, `02`, … in `.seclabel .idx` and the numbers are contiguous.
  **When you add, remove or reorder a section, renumber them.**
- Give each section an `id` when the document is long enough to link into.
- A document runs: top bar → optional confidentiality bar → hero with `.statstrip` → numbered
  sections → footer carrying preparer, date, status and data provenance.
