# What goes in a solution brief

A solution brief argues for one solution to one problem, for a reader who has not yet decided
to buy it. It runs to two to six pages, and four is typical: a cover page that carries the
whole argument in brief, two inside pages that make it, and the legal page. A data sheet uses
the same template with more tables and fewer paragraphs.

This structure comes from IBM's solution brief template (v1.5) and two published briefs:
IBM watsonx Orchestrate (February 2024) and a HashiCorp and Red Hat brief on certificate
lifecycle management (April 2026).

## The cover

The cover is the page most readers finish on, so it has to stand alone.

| Element | Call | What it holds |
|---|---|---|
| Title | `Brief(title)` | The solution's name, or the problem it ends. Three lines at most; the builder drops from 32pt to 28pt to 24pt to fit and warns past that. |
| Subtitle | `Brief(subtitle=)` | The outcome, in one sentence of 14 to 20 words. Three lines at most. |
| Highlights | `cover(highlights=)` | Three short benefit statements, written as phrases. They are what a skimming reader takes away. |
| Intro | `body()` after `cover()` | Two or three paragraphs: the problem, with a number that shows its size, and the change that makes it urgent now. |
| Business unit | `cover(business_unit=)` | A unit without its own logotype, such as "IBM Data and AI", set top left. |
| Hero logotype | `cover(logotype=)` | Consulting, iX, Research, Security, Cloud, or Watson, set as "IBM Consulting" in place of the 8-bar. |
| Partner logos | `cover(logos=)` | On a joint brief, the partners' marks, top left. |

## The inside pages

The published briefs follow one order, and a reader who has seen a few expects it.

1. **The problem, and why now.** What fails, what it costs, and the change in the market or
   in regulation that makes it urgent. Put the strongest number in `stats()` beside it.
2. **The solution.** What it is and how it works, at the level of the components and what
   each does. A diagram earns its place here, through `image()`.
3. **Capabilities or use cases.** A short list (`bullets()`) or a table when the reader will
   compare rows. Each item names something the reader can do.
4. **Proof.** Client examples with a measured result, a quote (`quote()`), or both. Name the
   client when you have permission; otherwise describe it ("an Australian bank").
5. **Conclusion.** One paragraph that restates the outcome in the reader's terms.
6. **Why IBM, or why these partners.** Optional, and short.
7. **For more information.** Who to contact and where to go, with a `button()` or a link.

Two placements exist for headings. Main-column headings (`heading()`) suit a brief that reads
straight through. Standalone headings in the side column (`side_heading()`) suit a data sheet
whose sections a reader jumps between. The template asks for one approach throughout.

## Elements and their limits

These come from the template's own instructions.

- **One quote or callout per page at most**, and ideally fewer. A page full of them reads
  as a brochure.
- **A boxed quote takes no quotation marks.** The box already says it is a quote.
- **Stats need a source.** Every number in `stats()` that is not the reader's own gets a
  `[^n]` reference in the text beside it and an entry in `sources`.
- **Short captions.** A caption says what the figure or table shows, as "Figure 1. ..." or
  "Table 1. ...", and what to notice in it.
- **Tables are for comparison.** Narrow columns with a lot of text read badly; the template
  says so in as many words.

## The back page

`back_page()` always comes last.

- **Sources**, numbered to match the `[^n]` references, before the legal text. The template's
  format is `Title, Publisher, DD Month YYYY.` (or `Month YYYY`, or `YYYY`, as far as the
  date is known), with only the title hyperlinked and a full stop at the end.
- **Trademarks.** `trademarks` lists the IBM marks the brief uses beyond IBM and the IBM
  logo, such as "IBM Cloud Pak". List only marks the brief actually uses.
- **Attributions.** One paragraph per third-party owner, again naming only marks the brief
  uses: "Red Hat and Ansible are trademarks or registered trademarks of Red Hat, Inc. or its
  subsidiaries in the United States and other countries." The IBM copyright and trademark
  page lists the special attributions that are required.
- **The disclaimers** are the template's v1.5 text. The template itself calls them a
  placeholder and points to IBM's "Corporate Disclaimers" document, so check them against the
  current version before a brief is published. `Brief.warnings` says so on every build.

## Writing it

A brief is persuasive, and that is where AI slop gathers: "seamless", "robust",
"transform", and "unlock" turn up in every vendor brief and say nothing. Write it with the
`writing-style` skill, and give each paragraph a number, a name, a cause, or a consequence.
The published briefs that read best state a measured result ("saved 12,000 hours in one
quarter") rather than a quality ("improves productivity").

Use the trademark symbol on the first mention of an IBM product in the body, as the
watsonx Orchestrate brief does ("IBM watsonx Orchestrate™"), and plain text after that.
