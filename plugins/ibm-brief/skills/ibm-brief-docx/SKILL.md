---
name: ibm-brief-docx
description: Build an IBM solution brief or data sheet as an editable Word document, laid out on IBM's own solution brief template (IBM Plex, the 8-bar, a side column of highlights and stats beside a main column of text, and the IBM legal page). Writes the brief from the user's draft, notes, or a description of the solution, then lays it out. Use this skill whenever the user wants an IBM solution brief, data sheet, one-pager, or two- to six-page product or partner brief, including a joint brief with HashiCorp, Red Hat, or another partner under IBM branding, or wants an existing brief rebuilt in the IBM template. For an IBM slide deck use ibm-deck-htmltopptx; for a HashiCorp-branded report use hashicorp-doc-docx.
---

# IBM solution brief

This skill builds an **IBM solution brief as an editable `.docx`**, laid out the way IBM's
InDesign solution brief template (v1.5) lays one out: the title and highlights on the cover,
a side column of highlights, stats, and callouts beside a main column of text, and the IBM
copyright and legal page at the end. It is Word rather than InDesign so that anyone can edit
the brief and pass it round for review; a PDF exported from Word is the finished article.

Everything visual comes from `assets/ibm-brief-template.docx`. You drive it through
`assets/ibm_brief.py`, which **never sets a font, size, or colour of its own**.
`assets/build_template.py` generates the template from measurements of IBM's, and is the
only place a style is defined.

## Setup

```
python3 -m venv .venv && .venv/bin/pip install python-docx
```

**IBM Plex is embedded in the template**, so a reader on Windows sees Plex without installing
it. Word for Mac ignores embedded fonts, so on a Mac, install IBM Plex Sans and IBM Plex
Serif (free, from github.com/IBM/plex) or the brief renders in a substitute.

## How to build one

The user usually hands over a draft, notes, or a description, and the skill writes the copy.

1. **Read `references/structure.md`.** It sets out what goes on the cover and in what order
   the inside pages argue, taken from IBM's template and two published briefs.
2. **Load the `writing-style` skill and write the brief's text** from the user's material,
   section by section, in the order structure.md gives. Run its checker over the text before
   it goes into the build script. A brief is persuasive writing, which is where slop gathers.
3. **Ask for anything a brief cannot go without** that the material lacks: a source for each
   statistic, permission to name a client, and the partner's trademark attribution wording.
   Do not invent a number or a quote.
4. **Write a build script in the user's project**, driving `ibm_brief.Brief`. See below.
5. **Read `Brief.warnings`.** A `!` line needs a decision: a title or subtitle over three
   lines, a missing image or logo, a ragged table row. The legal-text line prints on every
   build, as a reminder.
6. **Render it and look at every page.** On a Mac with Word installed:

   ```
   osascript <<'OSA'
   tell application "Microsoft Word"
     with timeout of 540 seconds
       set display alerts to none
       open file name (POSIX file "/abs/path/brief.docx" as text)
       set d to active document
       save as d file name (POSIX file "/abs/path/brief.pdf" as text) file format format PDF
       close d saving no
     end timeout
   end tell
   OSA
   ```

   If it fails with "active document doesn't understand the save as message" (-1708), a
   previous run left a document open behind a dialog. Close that document in Word and run
   it again.

   The 540-second timeout matters: a cold Word start and export routinely take longer than
   AppleScript's 60-second default, which fails as `AppleEvent timed out (-1712)`.

```python
from ibm_brief import Brief

b = Brief("Certificate lifecycle management",
          subtitle="Automate certificates end to end with HashiCorp Vault and Red Hat "
                   "Ansible Automation Platform",
          date="November 2026")
b.cover(highlights=["Stop certificate outages before they reach production",
                    "Issue short-lived certificates in seconds",
                    "Show auditors every certificate and who requested it"],
        logos=["logos/hashicorp.png", "logos/redhat.png"])
b.body("Digital certificates authenticate machines and encrypt data in transit ...",
       "The CA/Browser Forum has approved cutting certificate validity to 47 days.[^1]")
b.heading("Why certificates fail")
b.body("Certificate outages are rarely a cryptography problem ...")
b.stats([("up", "40%", "of enterprises had a certificate outage last year")])
b.body("Vault issues certificates on demand through an API ...")
b.quote("We went from a quarterly renewal fire drill to not thinking about certificates.",
        name="Platform lead", role="Australian financial services company", boxed=True)
b.table(["Capability", "Manual", "Automated"],
        [["Issuance", "Ticket, days", "API call, seconds"]],
        caption="Table 1. Manual and automated certificate management.")
b.heading("For more information")
b.body("Contact your IBM representative, or visit [ibm.com/vault](https://www.ibm.com/).")
b.button("Book a demonstration", "https://www.ibm.com/")
b.back_page(sources=["[Ballot SC-081v3](https://cabforum.org/), CA/Browser Forum, 11 April 2025."],
            attributions=["HashiCorp and Vault are trademarks or registered trademarks of "
                          "HashiCorp or its subsidiaries in the United States and other countries."])
b.save("certificate-lifecycle-brief.docx")
print("\n".join(b.warnings))
```

### Running from a project of your own

`ibm_brief` lives in this skill's `assets/`, which is not on `sys.path` elsewhere. Glob the
version, so a plugin update does not break the script:

```python
import glob, os, sys

hits = sorted(glob.glob(os.path.expanduser(
    "~/.claude/plugins/cache/*/ibm-brief/*/skills/ibm-brief-docx/assets")))
if not hits:
    sys.exit("ibm-brief plugin not found. Install it with:\n"
             "  /plugin install ibm-brief@hashicorp-field")
sys.path.insert(0, hits[-1])

from ibm_brief import Brief  # noqa: E402
```

Keep the build script in the project. It holds one brief's content; this skill owns the
format. Re-running the script is the reproducible path, so edit the script and never the `.docx` by hand.

## The API

| Call | Makes |
|---|---|
| `Brief(title, subtitle, date, footer_title=None)` | Opens the template. `date` is "Month Year" and appears in the running footer and on the back page. `footer_title` shortens the running title. |
| `cover(highlights, highlights_title, business_unit, logotype, logos, logo_height)` | Page 1. The title's size is chosen to fit three lines. Body calls that follow flow beside the highlights. |
| `heading(text)` `subheading(text)` | 14/20 heading and 9/12 semibold subheading, in the main column. |
| `body(*paragraphs)` `bullets(items)` `numbers(items)` | Text in the main column. A list item may be `(level, text)`. Each `numbers()` restarts at 1. |
| `side_heading(text, intro=None)` | A standalone heading in the side column, starting a section. |
| `stats(items)` | Big numbers in the side column: `(value, text)` or `(arrow, value, text)`, with arrow `"up"` or `"down"`. |
| `callout(title, text)` | A short callout in the side column under the blue marker. |
| `quote(text, name, role, company, boxed=False)` | A Plex Serif quote, in the side column or boxed in the main column. |
| `image(path, caption=None, full=False)` | A picture across the main column, or the page. |
| `table(headers, rows, widths=None, caption=None)` | A ruled data table across the page. `widths` in points. |
| `button(label, url, secondary=False)` | A call-to-action button with its arrow. |
| `pagebreak()` | Starts the next block on a new page. Writes nothing itself. |
| `back_page(sources, trademarks, attributions, extra, year, produced_in, legal)` | Sources, the copyright block, and the legal text. Always last. |
| `save(path)` | Writes the file. |

Side elements (`side_heading`, `stats`, `callout`, a side `quote`) each start a new band of
the page; main-column calls after one flow beside it until the next. Inline markup works in
any text: `**bold**` (set in SemiBold), `*italic*`, `[text](url)`, and `[^1]` for a
superscript source reference.

## Rules that keep it on-brand

- **Never set a font, colour, size, or border.** If a brief needs something the template has
  no style for, add the style in `build_template.py` so every brief gets it.
- **Sentence case** for the title, headings, and highlights. No full stop on a heading.
- **One quote or callout per page at most.**
- **Do not draw the 8-bar.** The template's page-1 and back-page footers carry it. A partner's
  logo goes in `cover(logos=...)`.
- **Every statistic has a source**, cited with `[^n]` and listed in `back_page(sources=...)`.
- **List only the trademarks the brief uses**, IBM's in `trademarks` and each partner's in its
  own `attributions` paragraph.

## Before handing it over

- [ ] `Brief.warnings` read, and every `!` line resolved or consciously accepted.
- [ ] Rendered to PDF and every page looked at: the cover holds its title, subtitle,
      highlights, and the start of the body; no heading ends a page; no stat's text is
      split across pages; no table or figure overflows.
- [ ] The brief is two to six pages, and the legal page is the last one.
- [ ] Every number has a source, and every source is cited in the text.
- [ ] The legal text has been checked against IBM's current Corporate Disclaimers document,
      and the trademark and attribution paragraphs name only marks the brief uses.
- [ ] The text has been through `writing-style`'s checker and a reading pass.
- [ ] Saved where the user asked, with the PDF beside it, and the user told where both are.

`references/design-system.md` has every measurement, what Word's quirks forced, and what the
InDesign template offers that this builder leaves to a designer.
