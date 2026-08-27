# hashicorp-claude-plugins

A Claude Code plugin marketplace for HashiCorp-branded deliverables.

The point of this repo is consistency. The same brand system had been copied into several
project repos and then drifted, so decks built in one place stopped matching decks built in
another. Skills live here once, and projects install them.

## Plugins

| Plugin | Skill | What it does |
|---|---|---|
| `hashicorp-deck` | `hashicorp-deck-html` | Builds single-file HTML5 scroll presentations in the HashiCorp brand style. Monochrome foundation, sparing product-gradient accents, mono structural labels, scroll-reveal, side nav and keyboard paging. |
| `hashicorp-deck` | `hashicorp-deck-htmltopptx` | Converts an existing HTML presentation into an editable HashiCorp-branded `.pptx`, re-typeset on the official CY26 presentation kit — Inter, the signature glow gradient and HashiCorp's own slide layouts. Light or dark, sharing one layout grammar. Content conversion, not screenshots. |
| `ibm-deck` | `ibm-deck-htmltopptx` | Converts an existing HTML presentation into an editable IBM-branded `.pptx`, re-typeset on the official IBM template — IBM Plex, the Carbon palette and IBM's own slide layouts. Content conversion, not screenshots. |
| `hashicorp-diagram` | `hashicorp-diagram-excalidraw` | Supplies HashiCorp-branded icons and Helios product colours for architecture diagrams drawn by hand in Excalidraw or Excalidraw+. Ships a stencil scene of 54 Flight icons and the individual SVGs. Assets, not a generator. |

A plugin can carry more than one skill — each groups the deck builders for one brand, one skill
per output format, so they share a single install and the same design system.

## Install

Add the marketplace, then install the plugin:

```
/plugin marketplace add phan-t/hashicorp-claude-plugins
/plugin install hashicorp-deck@hashicorp-field
/plugin install ibm-deck@hashicorp-field
/plugin install hashicorp-diagram@hashicorp-field
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
- **Keep skills portable.** No absolute paths and no assumptions about the surrounding repo,
  since these run wherever they are installed.
- **Vendor brand templates, stripped.** Both `.pptx` skills ship their brand's official template
  with the demo slides and unused media removed — IBM's 21 MB down to 144 KB, HashiCorp's 26 MB
  down to 6 MB. Bundling them is what guarantees every converted deck uses the same master, and
  keeps the skills working with no external download. Each skill's `references/design-system.md`
  records the exact strip, so the template can be refreshed when the brand ships a new kit.
- **Derive, don't fork.** `hashicorp-deck`'s dark template is generated from its light one by
  `assets/make_dark.py`, so the two cannot drift in layout, slot indices or bullets. Re-run it
  after refreshing the light kit.
