# hashicorp-claude-plugins

A Claude Code plugin marketplace for HashiCorp-branded deliverables.

The point of this repo is consistency. The same brand system had been copied into several
project repos and then drifted, so decks built in one place stopped matching decks built in
another. The skills live here once, and projects install them.

## Plugins

| Plugin | Skill | What it does |
|---|---|---|
| `hashicorp-deck` | `hashicorp-deck-html` | Builds single-file HTML5 scroll presentations in the HashiCorp brand style, with a monochrome foundation, sparing product-gradient accents, mono structural labels, scroll-reveal, side nav and keyboard paging. |
| `hashicorp-deck` | `hashicorp-deck-htmltopptx` | Converts an existing HTML presentation into an editable HashiCorp-branded `.pptx`, re-typeset on the official CY26 presentation kit using Inter, the signature glow gradient and HashiCorp's own slide layouts. Light and dark share one layout grammar, so a deck can be rebuilt in either. It carries the content across rather than taking screenshots. |
| `ibm-deck` | `ibm-deck-htmltopptx` | Converts an existing HTML presentation into an editable IBM-branded `.pptx`, re-typeset on the official IBM template using IBM Plex, the Carbon palette and IBM's own slide layouts. It carries the content across rather than taking screenshots. |
| `hashicorp-diagram` | `hashicorp-diagram-excalidraw` | Supplies HashiCorp-branded icons and Helios product colours for architecture diagrams drawn by hand in Excalidraw or Excalidraw+. Ships a stencil scene of 54 Flight icons and the individual SVGs. These are assets rather than a generator. |
| `hashicorp-doc` | `hashicorp-doc-docx` | Builds customer-facing Microsoft Word documents in the HashiCorp house style, such as assessments, engagement reports, architecture reviews and other professional-services deliverables. Full-bleed cover art with the wordmark, a metadata block, a live table of contents, a revision-history table, one section per page under a `version / title` running header, rule-and-band recommendation tables carrying ID, Impact, Effort, Priority and Category, and the HashiCorp back cover. The output is an editable `.docx`, because the customer has to review and circulate it. |
| `hashicorp-page` | `hashicorp-page-html` | Builds single-file HTML page documents in the HashiCorp brand style, such as long-form reports, briefings, decision papers and leadership readouts. Black top bar and hero with a headline-number strip, numbered sections on alternating backgrounds, evidence tables with status pills, charts drawn in CSS, ranked asks and a provenance footer. It is a document rather than a deck. |

A plugin can carry more than one skill. Each plugin groups the builders for one brand and one
kind of deliverable, with a skill per output format, so they share a single install and the
same design system.

## Install

Add the marketplace, then install the plugin:

```
/plugin marketplace add phan-t/hashicorp-claude-plugins
/plugin install hashicorp-deck@hashicorp-field
/plugin install ibm-deck@hashicorp-field
/plugin install hashicorp-diagram@hashicorp-field
/plugin install hashicorp-page@hashicorp-field
/plugin install hashicorp-doc@hashicorp-field
```

To work on the plugins locally, point the marketplace at your clone instead:

```
/plugin marketplace add ~/Documents/GitHub/hashicorp-claude-plugins
```

## Layout

```
.claude-plugin/marketplace.json     Marketplace manifest, lists the plugins
plugins/<plugin>/
  .claude-plugin/plugin.json        Plugin manifest, carries the version
  skills/<skill>/SKILL.md           The skill itself, one directory per skill
  skills/<skill>/references/        Design system and interaction detail, read on demand
  skills/<skill>/assets/            Boilerplate, build helpers and brand assets
```

## Conventions

- **Bump the version in `plugin.json`** on any change to a skill, so installs can be pinned.
- **The design system is authoritative.** Colors and type live in `references/design-system.md`.
  Skills read from it rather than restating values, which is what stopped it drifting before.
- **Keep skills portable.** No absolute paths, and no assumptions about the surrounding repo,
  since these run wherever they are installed.
- **Vendor brand templates, stripped.** Both `.pptx` skills ship their brand's official template
  with the demo slides and unused media removed, which takes IBM's from 21 MB to 144 KB and
  HashiCorp's from 26 MB to 6 MB. Bundling them is what guarantees every converted deck uses the
  same master, and it keeps the skills working with no external download. Each skill's
  `references/design-system.md` records the exact strip, so the template can be refreshed when
  the brand ships a new kit.
- **One palette per medium.** Three HashiCorp palettes disagree on product hues. The CY26
  presentation kit governs decks, because `hashicorp-deck-htmltopptx` re-typesets onto its
  master. Helios governs diagrams and page documents, which are read on a screen. Each skill's
  `references/design-system.md` records both columns so the divergence stays deliberate.
- **Naming a font is only a request.** Word grants it far less often than it looks, rendering
  `Helvetica Neue` as a serif and `Inter` as Calibri, so `hashicorp-doc` embeds Inter (OFL 1.1)
  in its template rather than naming it and hoping. `hashicorp-deck` does the same through the
  kit's own embedded Inter. To check which font a file really uses, render it and read back the
  font table of the resulting PDF, because a substitute can look close enough to pass by eye.
- **Generate the template, don't copy one.** `hashicorp-doc`'s `.docx` template is written by
  `assets/build_template.py` on top of python-docx's empty package rather than derived from a
  real document, so it carries no customer content, revision ids, comments or author names.
  Every style in it is defined in that one file.
- **Derive, don't fork.** `hashicorp-deck`'s dark template is generated from its light one by
  `assets/make_dark.py`, so the two cannot drift in layout, slot indices or bullets. Re-run it
  after refreshing the light kit.
