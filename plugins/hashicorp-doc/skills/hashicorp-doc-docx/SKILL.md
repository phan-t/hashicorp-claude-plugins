---
name: hashicorp-doc-docx
description: Build a HashiCorp-branded Microsoft Word document — an assessment, engagement report, architecture review, health check or professional-services deliverable that goes to a customer as an editable .docx. Full-bleed cover art with the wordmark, a metadata block, a live table of contents, a revision-history table, numbered sections under a `version / title` running header, rule-and-band recommendation tables carrying ID / Impact / Effort / Priority / Category, and the HashiCorp back cover. Use this skill whenever the user wants a Word document, .docx, assessment, engagement report, findings report, architecture or platform review, discovery readout or customer-facing deliverable in the HashiCorp house style — especially when they mention a previous assessment built this way. For slides use hashicorp-deck-htmltopptx; for a self-contained HTML report use hashicorp-page-html.
---

# HashiCorp Word document

This skill builds a **customer-facing `.docx`**: the format HashiCorp professional services
ships assessments and engagement reports in, because the customer has to be able to edit,
comment on and circulate it inside their own review process. A PDF or an HTML page cannot
do that job.

Everything visual comes from `assets/hashicorp-doc-template.docx` — the styles, the page
geometry, the wordmark on the cover footer. You drive it through `assets/hashicorp_doc.py`,
which fills that template in and **never sets a font, size or colour of its own**. That is
the whole point: assessments written in different repos come out the same.

`assets/build_template.py` regenerates the template, and is the only place a style is
defined. Change a heading size there, not in a build script.

## Setup

```
pip install python-docx
```

On an externally managed system Python (Homebrew, macOS system Python) pip refuses this with
a PEP 668 error. Use a virtualenv rather than `--break-system-packages`:

```
python3 -m venv .venv && .venv/bin/pip install python-docx
```

**Inter is embedded in the template, and that is deliberate.** Word resolves fonts by name
much less reliably than it appears to — it silently renders `Helvetica Neue` as a serif and
`Inter` as Calibri — so naming a face is only a request. Embedding is what makes the
document actually arrive in Inter, on the customer's machine as well as yours. Inter is
OFL 1.1, so this is permitted; `assets/fonts/OFL.txt` travels with it.

Inline `` `code` `` uses Consolas, which Microsoft Office installs on macOS and Windows
alike, so it needs no embedding. `Doc(font=...)` changes the name but **not** the embedding,
so use it only for a face you know the reader has. `references/design-system.md` has the
measured evidence.

## How to build one

1. **Read `references/structure.md` first.** It carries the document's architecture — what
   goes on the cover, why the recommendation table has the columns it has, how findings are
   written. That is the part that makes the document useful; the styling is the easy half.
2. **Read `references/design-system.md`** before changing any measurement. The tokens there
   are authoritative.
3. **Write a build script in the project**, not here — see below. Drive `hashicorp_doc.Doc`.
4. **Read `Doc.warnings` after the last call.** Nothing is dropped silently. A `!` line
   means a decision for you, not the script:
   - **cover overflows** — the art takes the top 4.2in, so the cover holds roughly a
     one-line title and eight metadata rows. `cover()` spends its own two spacers first
     and only warns once neither is enough; shorten the title or drop a row.
   - **column too narrow** — Word breaks mid-word rather than shrinking, so `Medium`
     becomes `Mediu` over `m`. Widen the column or shorten the value.
   - **ragged table row**, **missing image**.
5. **Open the result before calling it done.** The warnings prove the content landed; they
   cannot tell you a table column is too narrow for its longest cell.

```python
from hashicorp_doc import Doc

d = Doc("Vault Assessment", subtitle="Architecture and Workflow", version="1.0")
d.cover(date="October 2025", meta={
    "Company Name": "Acme Corporation",
    "Company Address": "1 Example Street, Sydney NSW 2000",
    "Primary Contact": "A. Reviewer",
    "HashiCorp Account Team": "[Tony Phan](mailto:tphan@hashicorp.com)",
    "Internal Identifiers": "SAAPJ-0000",
    "Last Modified": "02/12/2025",
})
d.contents()
d.versions([("0.1", "17-Nov-2025", "Tony Phan", "Initial draft"),
            ("1.0", "02-Dec-2025", "Tony Phan", "Release")])

d.h1("Introduction")
d.h2("Executive Summary")
d.body("HashiCorp was engaged to provide **Acme Corporation** with best practices ...",
       "The scope of this engagement includes physical and logical architectures ...")
d.h2("Challenges")
d.numbers(["The current implementation consists of Vault Enterprise PR clusters ...",
           "Operating System patching is controlled separately from Vault ..."])
d.h2("Highlights")
d.h3("Key Recommendations")
d.recommendations([
    ("ARC-A1", "Retain CMD consumers on the primary cluster.", "High", "Low", "High", "Tactical"),
    ("ARC-B", "Migrate from HAProxy to an enterprise load balancer.", "High", "Medium", "High", "Strategic"),
])

d.h1("Architecture")
d.h2("Current State")
d.body("The health check endpoint `/v1/sys/health` returns 200 for the active node.")
d.image("diagrams/current-state.png", caption="Figure 1. Current-state physical architecture.")

d.resources([("Vault Enterprise Operating Guide: People and Process",
              "https://developer.hashicorp.com/validated-designs/...")])
d.backpage()
d.save("acme-vault-assessment.docx")
print(d.warnings)
```

### Running from a project of your own

`hashicorp_doc` lives in this skill's `assets/`, which is not on `sys.path` anywhere else.
Glob the version rather than hardcoding one, or the script breaks the next time this plugin
is updated:

```python
import glob, os, sys

hits = sorted(glob.glob(os.path.expanduser(
    "~/.claude/plugins/cache/*/hashicorp-doc/*/skills/hashicorp-doc-docx/assets")))
if not hits:
    sys.exit("hashicorp-doc plugin not found. Install it with:\n"
             "  /plugin install hashicorp-doc@hashicorp-field")
sys.path.insert(0, hits[-1])

from hashicorp_doc import Doc  # noqa: E402
```

**Keep that build script in the project, not here.** It carries one engagement's content,
which is almost never shareable, and nobody else can run it against theirs. This skill owns
the format; the project owns what goes in it. Re-running the script stays the reproducible
path — edit it rather than patching the `.docx`.

## The API

| Call | Makes |
|---|---|
| `Doc(title, subtitle, version, font=None)` | Opens the template. `font` swaps the document off Inter — but only Inter is embedded, so pass a face the reader definitely has. |
| `cover(date, meta, logo=None, art=True)` | Cover art, title, subtitle, date, metadata block. The wordmark comes from the template footer. |
| `contents(levels="1-2")` | A live Word TOC field over Heading 1 and Heading 2. |
| `versions(rows)` | The revision-history table: version, date, author, changes. |
| `h1` `h2` `h3` `h4` | Headings. **`h1` always starts a new page**, and the first one opens the body section where the running header begins. |
| `body(*paragraphs)` | Body paragraphs. |
| `bullets(items)` `numbers(items)` | Lists. An item may be `(level, text)` to nest. Each `numbers()` call restarts at 1. |
| `table(headers, rows, widths=None, caption=None)` | Rule-and-band table on the 6in measure. |
| `recommendations(rows)` | The ID / Recommendation / Impact / Effort / Priority / Category table at its tuned widths. |
| `image(path, width_in=6.0, caption=None)` | A figure. |
| `caption(text)` | A figure or table caption. |
| `pagebreak()` | Starts the *next* block on a new page. It writes nothing itself, so a trailing or doubled `pagebreak()` can never leave a blank page behind. |
| `resources(items)` | Closing `Resources` section; items are `(text, url)`. |
| `backpage(lines=...)` | The back cover: art, address block, no running header. |
| `save(path)` | Writes the file and returns the path. |

`**bold**`, `*italic*`, `` `code` `` and `[text](url)` work anywhere text is accepted,
including table cells and the cover metadata block.

## Rules that keep the output on-brand

- **Never set a font, colour, size or border.** Use the styles the template defines. If a
  document needs something the template has no style for, add the style in
  `build_template.py` so every future document gets it too.
- **Sentence case for headings, title case for the document title.** No trailing full stop
  on a heading.
- **One `h1` per page.** `h1()` enforces it. Sections are Introduction, then one per area
  assessed, then Resources.
- **Every recommendation carries an ID**, prefixed by area (`ARC-A1`, `OPS-B`, `UX-C`), so
  it can be cited in a meeting and tracked after the engagement closes.
- **Tables have no vertical rules and no boxes.** The style draws a heavy rule above the
  header row, one below the last row, and bands alternate rows. That is the whole grammar.
- **Do not draw the wordmark yourself.** It is the template's first-page footer, and
  `backpage()` carries the back cover. A second logo on the cover is the *customer's*, via
  `cover(logo=...)`.
- **The TOC is a field, not text.** Word rebuilds it on open. Never hand-write the contents.
- **Never write your own page breaks into content.** `pagebreak()` and `h1()` handle it, and
  they set `pageBreakBefore` on the next block rather than emitting a break paragraph — the
  difference is a blank page every time a break lands on an already-full page.

## Before handing it over

- [ ] `Doc.warnings` read; every `!` line resolved or consciously accepted.
- [ ] Opened in Word and paged through — headings fall where intended, no table column is
      too narrow, no figure overflows the measure.
- [ ] Contents page shows real page numbers, not the placeholder line.
- [ ] Cover fits on one page, and the metadata is complete: company, contact, account team,
      internal identifier, date.
- [ ] No blank pages. If one appears, something wrote its own break instead of using
      `pagebreak()`.
- [ ] Revision history matches the version in the running header.
- [ ] Every recommendation has an ID, and the IDs are referenced in the section that
      argues for them.
- [ ] Saved to the path the user asked for, and they were told where it is.
