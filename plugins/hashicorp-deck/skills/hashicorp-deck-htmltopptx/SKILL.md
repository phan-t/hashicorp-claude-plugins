---
name: hashicorp-deck-htmltopptx
description: Convert an existing HTML presentation into an editable, HashiCorp-branded PowerPoint file. Reads the content out of an HTML deck — headlines, ledes, bullets, metric cards, columns, quotes, code, images — and re-typesets it on the official HashiCorp presentation kit (Inter, the signature glow gradient, HashiCorp's own slide layouts), producing a .pptx whose text stays editable rather than a stack of screenshots. Use this skill whenever the user wants an HTML deck, scroll deck, reveal.js deck, or web presentation turned into PowerPoint, .pptx, or "a deck I can send to HashiCorp / present in PowerPoint", or wants an existing presentation rebranded to HashiCorp. Prefer this over hand-building slides in python-pptx when a source HTML deck already exists.
---

# HTML presentation → HashiCorp PowerPoint

This skill converts a **web deck into an editable HashiCorp-branded `.pptx`**. It is a
content conversion, not a screenshot: each HTML slide is read for its structure, and that
content is re-typeset on the official kit layouts. The source deck's colors, gradients and
fonts are deliberately discarded — the output belongs to the HashiCorp kit.

Everything visual comes from `assets/hashicorp-brand-template.pptx`, the HashiCorp
Light-mode CY26 Presentation Kit v4, stripped to its master, 47 layouts, theme and
embedded Inter. **`Deck(mode="dark")`** — or `--dark` on the converter — builds the same
deck on black: the dark template is derived from this one, so every layout, slot, bullet and
gradient is identical and nothing is unavailable. `references/dark.md` covers it, and
`assets/make_dark.py` regenerates it when the light template is refreshed. Nothing in this skill sets a font, color or size that a layout can supply.
That is the whole point: the kit is authoritative, so decks converted in different repos
come out the same.

**One thing works differently here than in a normal template.** The kit's *theme* is stock
Microsoft Office — Aptos type, Office-blue accents — and every layout overrides it with
Inter and HashiCorp color in its own list styles. So brand fidelity depends on filling
**placeholders**. Text you drop into a shape you drew yourself inherits Office, not
HashiCorp, and there is no theme to fall back on. Read `references/design-system.md`
before drawing anything.

## Setup

```
pip install python-pptx beautifulsoup4
```

On a system Python that is externally managed (Homebrew, and macOS system Python), pip refuses
this with a PEP 668 error. Use a virtualenv rather than `--break-system-packages`:

```
python3 -m venv .venv && .venv/bin/pip install python-pptx beautifulsoup4
```

Inter is embedded in the template, so PowerPoint on Windows renders the deck correctly
with nothing installed. PowerPoint on macOS ignores embedded fonts — install Inter locally
there, or the deck falls back to a substitute. JetBrains Mono, used only by `Deck.code()`,
is never embedded; install it if a deck carries code.

## How to convert

1. **Read the source deck first.** Open the HTML and see what is actually on each slide.
   The converter's structural guesses are good, not clairvoyant, and step 4 is where you
   earn the result.
2. **Run the converter.** From the skill's `assets/` directory:
   ```
   python html_to_pptx.py <deck.html> -o <deck.pptx> \
       --kicker "<Customer — Briefing>" --speaker "<name>" --date "<month year>"
   ```
   It prints one line per slide — the layout it chose and the content it took — plus a `!`
   line for anything it could not carry. Read that report; nothing is dropped silently.
3. **Check the report's `!` lines.** Extra metric cards, missing images, a bullet slide
   with no lede, code truncated past 20 lines, and any slot whose text is predicted to
   overflow. Each one is a decision for you, not the script.

   Overflow warnings matter more here than in most templates: the kit marks its cover
   slots `<a:noAutofit/>`, so a title too long for one line does not shrink — it wraps
   onto the subtitle. The cover title holds about 22 characters. When building directly,
   read `Deck.warnings` after the last slide.
4. **Fix the slides that need judgment**, by editing a short build script that imports
   `hashicorp_deck` (see below) rather than by patching the `.pptx`. Re-running the converter
   must stay the reproducible path.
5. **Open the result before calling it done.** The report proves content landed in the right
   *placeholder*; it cannot tell you a headline is three lines too long for the slot.

## Building slides directly

When a slide needs a layout the converter would not have picked, drive `hashicorp_deck` yourself:

```python
from hashicorp_deck import Deck

d = Deck()                       # Deck(mode="dark") for the dark kit
d.cover("Rebuilding deploys", subtitle="From one queue to self-service",
        kicker="Acme Corp — Briefing", date="August 2026",
        speaker="Tony Phan", speaker_title="Solutions Engineer, HashiCorp")
d.agenda("Table of contents", ["Where we started", "What broke", "The rebuild"],
         numbers=[3, 7, 12])
d.section("The problem")
d.quote("The queue was a person, and now it is a pipeline.",
        attribution="Anthony Ralston, Senior Software Engineer")
d.body("One team owned the pipeline",
       prose="Platform engineering reviewed every change by hand.",
       bullets=["**Four days** — median lead time.", "**Rollbacks** — needed a ticket."])
d.columns("Three things moved",
          ["Teams ship without a ticket.", "Policy runs in CI.", "One dashboard."],
          headings=["Self-service", "Guardrails", "Visibility"])
d.metrics([("92%", "Faster lead time"), ("3x", "Deploys per week")], title="By the numbers")
d.code("The guardrail", open("policy.sentinel").read(), caption="policy.sentinel")
d.end()
d.save("deck.pptx")
```

### Running from a project of your own

`hashicorp_deck` lives in this skill's `assets/`, which is not on `sys.path` anywhere else, so a
build script kept in a project repo has to locate it. Glob the version rather than hardcoding
one, or the script breaks the next time this plugin is updated:

```python
import glob, os, sys

hits = sorted(glob.glob(os.path.expanduser(
    "~/.claude/plugins/cache/*/hashicorp-deck/*/skills/hashicorp-deck-htmltopptx/assets")))
if not hits:
    sys.exit("hashicorp-deck plugin not found. Install it with:\n"
             "  /plugin install hashicorp-deck@hashicorp-field")
sys.path.insert(0, hits[-1])

from hashicorp_deck import Deck  # noqa: E402
```

**Keep that build script in the project, not here.** It carries one deck's content, which is
frequently not shareable, and nobody else can run it against theirs. This skill owns the layouts;
the project owns what goes in them. Re-running the script stays the reproducible path, so edit it
rather than patching the `.pptx`.

Every method appends one slide and returns it, so you can reach for python-pptx afterwards
if a slide needs something bespoke. `**bold**` works inside any text. Full method list and
the layout keys they map to are in `references/layouts.md`.

## Rules that keep the output on-brand

- **Never set a font, color, size or position.** Fill placeholders and let the layout's list
  styles resolve the rest. The sanctioned exceptions are `code()`, `table()`, `chart()` and
  the attribution line on `quote()` — the four places the kit ships no placeholder at all.
- **Sentence case, always.** The kit writes its own slide titles in sentence case. The one
  place it uses caps is the eyebrow label (`BLUEPRINT FOR CLOUD SUCCESS`), and `eyebrow()`
  is where that belongs.
- **Headlines carry no trailing full-stop.**
- **Use the subtitle slot.** Almost every content layout pairs a title with a one-line
  subtitle; the kit prompts it *"1-line max. Delete if unneeded"*. It is the natural home
  for an HTML deck's lede, and a title alone often reads thin.
- **Respect the slot counts.** The kit holds 3 metrics, 4 columns, and 6 agenda items. If
  the content does not fit, split the slide — do not shrink type.
- **Let the chrome regenerate.** The page number and the copyright line are layout shapes,
  so they appear on every slide by themselves. Strip the source deck's own `.pagenum` /
  `.secttag` text; the converter already ignores them.
- **Keep the closing slide.** `Deck.end()` appends the kit's closing slide — "Thank you"
  in light, the contact line in dark.
- **Do not mix modes in one deck.** `light` and `dark` share a stage so a deck could be
  rebuilt in either, but a single deck should commit to one.

## What the converter maps

| In the HTML | Becomes |
|---|---|
| First slide | Cover (kicker / title / subtitle / date / presenter) |
| `h1` alone | Section divider |
| `blockquote` | Pull-quote in the glow gradient |
| `ul li` + a lede | Body copy left, bullet list right |
| `.row.split` children | 2–4 columns; with `h3` headings, the icon containers |
| `.card` with `.num` | 2 or 3 metrics, number + caption |
| `pre` | Code panel on a titled slide |
| `img` | Image overlay, small right |
| anything else | Title + subtitle |

The mapping is identical in dark mode. Only `mode="dark-v2"`, HashiCorp's own older dark
kit, is missing layouts; there a `.card` slide falls back to columns and says so.

Detail on each layout's slots — and the four traps that make text land in the wrong place —
is in `references/layouts.md`. Read it before adding a slide type.

## Checklist before handing it over

- [ ] Converter report read; every `!` line resolved or consciously accepted.
- [ ] Sentence case throughout; no trailing full-stops on headlines.
- [ ] No slide exceeds its layout's slot count.
- [ ] Deck opened and eyeballed — headlines fit, nothing overflows, gradients render.
- [ ] Saved to the path the user asked for, and they were told where it is.
