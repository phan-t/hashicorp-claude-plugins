---
name: ibm-deck-htmltopptx
description: Convert an existing HTML presentation into an editable, IBM-branded PowerPoint file. Reads the content out of an HTML deck — headlines, ledes, bullets, metric cards, columns, code, images — and re-typesets it on the official IBM presentation template (IBM Plex, Carbon palette, IBM's own slide layouts), producing a .pptx whose text stays editable rather than a stack of screenshots. Use this skill whenever the user wants an HTML deck, scroll deck, reveal.js deck, or web presentation turned into PowerPoint, .pptx, or "a deck I can send to IBM / present in PowerPoint", or wants an existing presentation rebranded to IBM. Prefer this over hand-building slides in python-pptx when a source HTML deck already exists.
---

# HTML presentation → IBM PowerPoint

This skill converts a **web deck into an editable IBM-branded `.pptx`**. It is a content
conversion, not a screenshot: each HTML slide is read for its structure, and that content
is re-typeset on the official IBM layouts. The source deck's colors, gradients and fonts
are deliberately discarded — the output belongs to the IBM design system.

Everything visual comes from `assets/ibm-brand-template.pptx`, the official IBM
presentation template v2.0 (Plex), stripped to its master, 48 layouts and theme. Nothing
in this skill sets a font, color or size that the template can supply. That is the whole
point: the template is authoritative, so decks converted in different repos come out the same.

## Setup

```
pip install python-pptx beautifulsoup4
```

IBM Plex must be installed locally for the deck to *look* right when opened; without it
PowerPoint substitutes a fallback face. The file is still correct either way — the font is
named in the theme, not embedded.

## How to convert

1. **Read the source deck first.** Open the HTML and see what is actually on each slide.
   The converter's structural guesses are good, not clairvoyant, and step 4 is where you
   earn the result.
2. **Run the converter.** From the skill's `assets/` directory:
   ```
   python html_to_pptx.py <deck.html> -o <deck.pptx> --footer "<running footer>"
   ```
   It prints one line per slide — the layout it chose and the content it took — plus a `!`
   line for anything it could not carry. Read that report; nothing is dropped silently.
3. **Check the report's `!` lines.** Extra metric cards, missing images, code on a slide that
   became something else. Each one is a decision for you, not the script.
4. **Fix the slides that need judgment**, by editing a short build script that imports
   `ibm_deck` (see below) rather than by patching the `.pptx`. Re-running the converter
   must stay the reproducible path.
5. **Open the result before calling it done.** The report proves content landed in the right
   *placeholder*; it cannot tell you a headline is three lines too long for the slot.

## Building slides directly

When a slide needs a layout the converter would not have picked, drive `ibm_deck` yourself:

```python
from ibm_deck import Deck

d = Deck(footer="Platform engineering")
d.cover("Why we rebuilt the deploy path", label="Point of view",
        meta=["Tony Phan", "August 2026"])
d.section("The problem")
d.statement("Every deploy went through one queue")
d.columns("Three things moved",
          [["**Self-service** — teams ship without a ticket."],
           ["**Guardrails** — policy runs in CI, not review."]],
          headings=["Before", "After"])
d.metrics([("92%", "**Faster** — lead time fell from 4 days to 7 hours."),
           ("3x", "**Throughput** — deploys per week, same headcount.")],
          title="By the numbers")
d.code("The guardrail", open("policy.rego").read(), caption="policy.rego")
d.end()
d.save("deck.pptx")
```

Every method appends one slide and returns it, so you can reach for python-pptx afterwards
if a slide needs something bespoke. `**bold**` works inside any text. Full method list and
the layout keys they map to are in `references/layouts.md`.

## Rules that keep the output on-brand

- **Never set a font, color, size or position.** Fill placeholders and let the template's
  theme resolve the rest. The one sanctioned exception is `Deck.code()`, which draws a panel
  because IBM ships no code layout.
- **Sentence case, always.** IBM's own template says so on its title master: *"5 lines
  maximum, sentence case"*. Never title case, never ALL CAPS.
- **Headlines carry no trailing full-stop.**
- **Respect the slot counts.** IBM's data layouts hold three callouts, its column layouts
  hold four columns. If the content does not fit, split the slide — do not shrink type.
- **Let the chrome regenerate.** Section tags, page numbers and footers come from the
  template. Strip the source deck's own `.pagenum` / `.secttag` text; the converter already
  ignores them.
- **Keep the end slide.** `Deck.end()` appends IBM's closing lockup and takes no content.

## What the converter maps

| In the HTML | Becomes |
|---|---|
| First slide | Cover, plain (+ label / meta lines) |
| `h1` alone | Section divider |
| `h2` alone, short | Large text |
| `ul li` | Text, 1 wide column |
| `.row.split` children | Text, 2–4 columns |
| `.card` with `.num` | Data callouts, number + prose per row |
| `pre` | Code panel on a blank slide |
| `img` | Video or imagery, half |
| anything else | Callout, headline |

Detail on each layout's placeholders — and the two traps that make text land in the wrong
slot — is in `references/layouts.md`. Read it before adding a slide type.

## Checklist before handing it over

- [ ] Converter report read; every `!` line resolved or consciously accepted.
- [ ] Sentence case throughout; no trailing full-stops on headlines.
- [ ] No slide exceeds its layout's slot count.
- [ ] Deck opened and eyeballed — headlines fit, nothing overflows.
- [ ] Saved to the path the user asked for, and they were told where it is.
