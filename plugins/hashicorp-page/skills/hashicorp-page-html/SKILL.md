---
name: hashicorp-page-html
description: Build a single-file, HashiCorp-branded HTML page document — a long-form scrolling report, briefing paper, decision paper or leadership readout, not a slide deck. Black top bar and hero with a headline-number strip, numbered sections on alternating backgrounds, dense evidence tables with status pills, CSS-drawn charts, ranked asks and a provenance footer. Use this skill whenever the user wants a report, readout, briefing, business case, decision paper, options paper, impact analysis, pipeline or capacity review, half/quarter plan, or any evidence-heavy internal document as a self-contained .html file — especially for leadership audiences, or when they reference this style or a previous document built this way. For slides use hashicorp-deck-html instead.
---

# HashiCorp-style HTML page document

This skill builds a **single, self-contained HTML file**: a long-form document that scrolls as a
web page. CSS lives inline, charts are drawn in CSS, and the logomark is inlined as SVG, so the
file is one artefact that can be attached to an email and opened offline.

**This is not a deck.** There are no slides, no viewport-height sections, no scroll snapping and
no nav dots. Sections are as tall as their content, and the reader scrolls a document. If the
user wants slides, use `hashicorp-deck-html`.

## When and how to build

1. **Read `references/design-system.md` first.** It carries the exact tokens, the type scale, and
   which of the three HashiCorp palettes governs a page. Treat those values as authoritative.
2. **Read `references/components.md`** for the block grammar. Compose sections from those blocks
   rather than writing new markup patterns.
3. **Start from `assets/template.html`.** It has the complete stylesheet, the top bar with the
   inlined logomark, the hero, a section skeleton and the footer. Build inside it.
4. **Only if the document needs to be re-cut by the reader**, read `references/interactive.md`.
   The default is no JavaScript at all.
5. **Write the file into the project** at the path the user asked for, or alongside the source
   material if they have not said. Tell them the path.

## What this document type is for

An evidence-carrying internal document that someone will read alone, at their own pace, and
quote from later. The forms it takes:

- **Decision paper** — two options defined side by side, scored against criteria, with a
  recommendation and sequencing. (`h2-2026-operating-model-confidential.html`)
- **Impact analysis** — what a constraint costs, quantified across a region or a period.
  (`h2-2026-apac-hiring-impact-confidential.html`)
- **Pipeline or capacity review** — the numbers per quarter and per person, with method and
  caveats. (`h2-2026-pipeline-confidential.html`)
- **Plan or leadership readout** — recap, themes, goals, milestones, asks.
  (`h2-2026-leadership-review.html`)
- **Interactive utilisation report** — one filterable dataset, charted.
  (`sa-impact-report-*.html`)

## Structure

```
top bar            wordmark · audience/type/status tags · optional Confidential chip
confidentiality    restricted documents only, specific about what and who
hero               eyebrow · H1 stating the finding · lede · 3–6 headline numbers
sections 01…NN     numbered, alternating .alt background, one finding each
footer             what it is · preparer, date, status · every data source with its window
```

Each section is: `.seclabel` (index + heading + optional status tag) → `.keyline` →
`.secintro` paragraph carrying the finding → the evidence blocks → a `.note` with the honest
reading → `.src` provenance. Renumber the indices whenever sections move.

The document should end on what the reader has to do: a `.asks` block, a recommendation with
`.seq` sequencing, or a list of open items blocking a decision.

## Voice

The design carries authority, so the prose does not have to perform it.

- **Sentence case everywhere.** Uppercase is for mono micro-labels only.
- **A heading makes a claim, not a label.** "The ANZ SE bench is half its intended size", not
  "Bench status". No trailing full stops on headings.
- **Every number traces to a source.** Anything in the `.statstrip` reappears, sourced, in a
  section below. `.src` states the extract date and what the figure excludes.
- **State the reading that weakens your own argument.** The source documents do this in
  `.note` and `.note.crit` blocks — a competing explanation, a denominator that moved, a
  business case sized from one region. It is the thing that makes the rest credible.
- **Prose over bullets.** When a list is right, each item is a bold lead-in and one tight
  sentence, in `ul.body` or a `.pc` list.
- **Plain declarative sentences.** No em-dashes in prose, no "not just X but Y", no inflated
  verbs. Ranges take an en dash.
- **People are named neutrally.** Flag a risk, do not judge a person. Where a document carries
  individual performance or departure data, the confidentiality bar is not optional.

## Output and accessibility

- One `.html` file. Everything inline except the two webfonts; delete the three `<link>` tags
  in `<head>` for a fully offline file that falls back to Helvetica Neue with no layout shift.
  Do that for confidential documents, and say so.
- Give `.statstrip` `role="list"` and its items `role="listitem"`; give every CSS chart
  `role="img"` and an `aria-label` carrying the totals.
- Never colour-only: every bar and segment carries its value or label as text.
- Keep state in JS variables, not `localStorage`/`sessionStorage`, so the file works in a
  sandboxed viewer.
- Respect `prefers-reduced-motion` — the template's smooth scrolling already degrades.
- Validate any script block with `node --check` before handing it over, if Node is available.
- Open the finished file and look at it. The design system covers colour and type, not whether
  a table overflowed or a section number repeated.

## Checklist before delivering

- [ ] Section indices contiguous and matching the order they appear in.
- [ ] Every `.statstrip` number appears again, sourced, in a section.
- [ ] One gradient chosen for the document; accents sparse; Vault is `#FFCF25`.
- [ ] Chart series use `--c1`…`--c4` in the same order in every figure.
- [ ] Every table inside `.tablebox`; numeric columns `td.num`.
- [ ] Asks carry an owner, a cost and a date.
- [ ] Footer names every data source with its window and extract date.
- [ ] Confidentiality bar present and specific, or deliberately absent.
- [ ] Written to the agreed path, opened, and eyeballed.
