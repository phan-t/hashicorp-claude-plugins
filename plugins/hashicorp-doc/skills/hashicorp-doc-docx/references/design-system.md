# Design system reference

Authoritative measurements for a HashiCorp `.docx` document. Every value here is set in
`assets/build_template.py` and nowhere else — change it there and regenerate the template
rather than overriding it in a build script.

All measurements are in **twips** (1/20 pt, 1440 to the inch) because that is what OOXML
stores. `w:sz` is the exception: it is in half-points.

## Page

| | Value | Why |
|---|---|---|
| Size | 12240 × 15840 (US Letter, portrait) | The reference's, and what US customers print. |
| Margins | top 1872, bottom 1512, **left 1612, right 1987** | Asymmetric on purpose. |
| Measure | 8641 twips = **6.00in** | ~85 characters at 10pt — a readable line. |
| Header distance | 763 | |
| Footer distance | 432 | |

The right margin is 375 twips wider than the left, which sets the text block left of centre
and leaves a quiet gutter on the outside edge. Do not "fix" it to symmetric: the cover art
and the back-cover art are both weighted to the right, and the asymmetry is what balances
them.

## Type

The body font is **Helvetica Neue** at **10pt**, line 348 auto (1.45), 200 after.

| Style | Size | Before / after | Weight |
|---|---|---|---|
| Title | 40pt | 0 / 0 | bold |
| Subtitle | 24pt | 0 / 0, line 2.0 | Helvetica Neue Light |
| Heading 1 | 26pt | 0 / 520 | bold |
| Heading 2 | 16pt | 600 / 240 | bold |
| Heading 3 | 12pt | 280 / 160 | bold |
| Heading 4 | 12pt | 280 / 80 | bold |
| Heading 5 | 11pt | 240 / 80 | regular, `#666666` |
| Heading 6 | 10pt | 200 / 120 | regular, `#666666` |
| Normal | 10pt | 0 / 200, line 1.45 | regular |
| Cover Meta | 11pt Arial | 0 / 0, line 1.0 | labels bold |
| Contents Heading | 14pt | 0 / 240 | bold |
| Caption | 9pt | 80 / 240 | `#666666` |
| Colophon | 10pt | 0 / 280, line 1.15 | regular |
| Code (character) | inherits | — | Space Mono, bold |
| Hyperlink (character) | inherits | — | `#1155CC`, underlined |

Headings 1–4 all carry `keepNext` and `keepLines`, so a heading never strands at the foot
of a page.

### Fonts, and why they are embedded

**Word for Mac resolves fonts by name far less reliably than it looks.** This was
established by rendering probe documents through Word and reading back which fonts the
exported PDF actually used — not by assuming.

| Name in the `.docx` | What Word used |
|---|---|
| `Helvetica Neue` | a serif — even though macOS ships and enables it |
| `Inter` | **Calibri** — it looks like a sans, so this is easy to miss |
| `Helvetica`, `Arial`, `Calibri`, `Consolas` | themselves |
| `Space Mono`, `JetBrains Mono`, `SF Mono` | a serif |

The reference document named Helvetica Neue and got away with it *because Google Docs
embedded the font*. Naming a face is a request; embedding it is what makes it happen.

So the template **embeds Inter** — regular, bold, italic and bold-italic, in
`assets/fonts/`, wired into `fontTable.xml` by `build_template.py`. Inter is SIL OFL 1.1,
which explicitly permits embedding and redistribution; `fonts/OFL.txt` travels with it.
Word for Mac honours embedded fonts (unlike PowerPoint), and so does Word for Windows, so
the customer sees Inter whether or not they have it installed.

Two consequences worth knowing:

- **Inter is wider than Calibri**, so a document rebuilt after this change reflows and runs
  a page or two longer. That is the document finally being set in its own font.
- **`Doc(font=...)` overrides the name but not the embedding.** Only Inter is embedded, so
  an override is a request again — use it only for a face you know the reader has:
  `Arial` is universal, `HashiCorp Sans` works internally.

`Consolas` carries inline code. It is not embedded and does not need to be: Microsoft
Office installs it on both macOS and Windows, so anyone who can open a `.docx` has it.
`Arial`, used only for the cover metadata block as the reference did, is universal too.

## Colour

This document type is **monochrome**. There is no product palette in it, and adding one
would be wrong: the colour in the document comes entirely from the two pieces of brand art.

| Token | Value | Used for |
|---|---|---|
| Rule | `#000000`, `w:sz 12` (1.5pt) | Above a table's header row, below its last row |
| Band | `#F3F3F3` | Every other body row of a table |
| Muted | `#666666` | Captions, Heading 5 and 6 |
| Link | `#1155CC` | Hyperlinks |

Status is **not** encoded in colour here — the recommendation table's Impact, Effort and
Priority columns carry the words High / Medium / Low. In a printed, forwarded, commented-on
Word file that survives everything colour does not.

## Tables

One style, `HashiCorp Table`, and it is conditional rather than uniform:

```
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━  1.5pt rule
  header row  bold, repeats across pages
  body row 1  #F3F3F3
  body row 2  white
  body row 3  #F3F3F3
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━  1.5pt rule
```

No vertical rules, no outer box, no rules between body rows — the banding does that work.
Cell margins are 99 twips on every edge. Tables are fixed-layout on the 6in measure;
`Doc.table(widths=...)` takes proportional twips and scales them to fit, so a width list
lifted from another document still lands on the measure.

The header row carries `w:tblHeader`, so it repeats when a long table breaks across pages.

### Recommendation table widths

`Doc.recommendations()` uses `982 / 3434 / 1020 / 1020 / 1020 / 1165`. Each judgement column
is sized to hold its **bold** header and the word `Medium` without breaking, measured from
Inter's own advance widths; Recommendation takes what is left, about 40% of the measure,
because it holds a sentence.

## Brand art

Three PNGs in `assets/media/`, all from the reference document:

| File | Placed | Size |
|---|---|---|
| `cover-art.png` | Cover, anchored to the page at 0,0 | 7772400 × 3837623 EMU (8.5 × 4.20in) |
| `back-cover.png` | Back page, anchored to the page at 0,0 | 7772400 × 5022913 EMU (8.5 × 5.49in) |
| `hashicorp-wordmark.png` | Cover footer, inline | 1866000 EMU wide (2.04in) |

Both full-bleed images are anchored **relative to the page**, not the paragraph, with
`wrapSquare`. That is what makes the cover text start below the art no matter which
paragraph the anchor is attached to. The cover art is cropped 0.4% top and bottom
(`srcRect t="40" b="40"`) to remove the source PNG's hairline edge.

The wordmark PNG carries about 3.8% of padding on its left edge, so the footer paragraph
pulls back 71000 EMU to set the mark flush with the left margin.

## What fits on a cover

The art occupies the top 4.20in of the page and the text flows below it, so the cover has
about **5.75in of text height**, not the usual 8.65in. That is roughly a one-line title plus
a subtitle, a date and eight metadata rows.

`Doc.cover()` budgets this before it writes anything and spends two spacers in order — the
blank line between subtitle and date, then the 18pt gap above the metadata block — before it
warns.

Line heights come from `assets/font_metrics.py`, which `build_template.py` generates from
the embedded font files: real advance widths for every printable character in regular and
bold, and the font's own single-line ratio. That is what makes `Doc.table()`'s narrow-column
warning exact rather than a guess, and it measures the header row as bold, which is where
`Category` overflows first.

Font metrics alone are not the whole story, though. **Word adds leading around a paragraph
that ascent and descent do not express**, and at the Subtitle style's double line spacing it
is substantial — a measured cover ran 1400 twips taller than the sum of its line heights.
`COVER_LEADING_ALLOWANCE` holds that back so the budget errs toward warning. Any change to
the Subtitle style should be re-measured against a render.

## Page breaks

A break is requested, not written. `pagebreak()` sets a flag and the next paragraph created
carries `pageBreakBefore`; `h1()` uses the same path. A break carried by its own empty
paragraph — which is what `python-docx`'s `add_page_break()` makes — leaves a blank page
behind whenever the preceding page was already full, and the cover almost always is.

The one exception is a table, which has no `pageBreakBefore` of its own: a pending break
ahead of a table does get a paragraph to carry it.

## Lists

Bullets are `●` `○` `■`, repeating every three levels. Numbers are `1.` `a.` `i.`, the same
way. Every level indents 720 twips with a 360 hang, and list items sit tight
(`spacing after 0`, `contextualSpacing`) so a list reads as one block.

The last item of a list carries the 200-twip space after that the others suppress, so a
paragraph following a list does not run into it. `contextualSpacing` only collapses space
between neighbours of the same style, which the paragraph after a list is not.

Each `Doc.numbers()` call gets its own copy of the abstract numbering definition. That is
how Word itself restarts a list: sharing one definition makes the second list continue from
the first, and `startOverride` restarts on *every item* in Word for Mac.

## Sections and chrome

The document runs in three sections, and the chrome is the reason:

1. **Front matter** — cover, contents, revision history. `titlePg` is on, so page 1 takes
   the wordmark footer and no header. Pages 2–3 have neither.
2. **Body** — opened by the first `h1()`. Its default header carries
   **`1.0`&nbsp;&nbsp;/&nbsp;&nbsp;`Document title`**, the version bold, three spaces either
   side of the slash. Every body page has it.
3. **Back cover** — opened by `backpage()`. Header and footer are unlinked and left blank,
   so the running header does not print over the art.

There are no page numbers anywhere. The contents field supplies them; the pages themselves
do not carry them, which is the reference's choice and worth keeping — these documents get
re-cut and re-exported, and a wrong page number is worse than none.
