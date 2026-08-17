# hashicorp-claude-plugins

A Claude Code plugin marketplace for HashiCorp-branded deliverables.

The point of this repo is consistency. The same brand system had been copied into several
project repos and then drifted, so decks built in one place stopped matching decks built in
another. Skills live here once, and projects install them.

## Plugins

| Plugin | What it does |
|---|---|
| `hashicorp-deck` | Builds single-file HTML5 scroll presentations in the HashiCorp brand style. Monochrome foundation, sparing product-gradient accents, mono structural labels, scroll-reveal, side nav and keyboard paging. |

## Install

Add the marketplace, then install the plugin:

```
/plugin marketplace add phan-t/hashicorp-claude-plugins
/plugin install hashicorp-deck@hashicorp-field
```

To work on the plugins locally, point the marketplace at your clone instead:

```
/plugin marketplace add ~/Documents/GitHub/hashicorp-claude-plugins
```

## Layout

```
.claude-plugin/marketplace.json     Marketplace manifest, lists the plugins
plugins/<name>/
  .claude-plugin/plugin.json        Plugin manifest, carries the version
  skills/<name>/SKILL.md            The skill itself
  skills/<name>/references/         Design system and interaction detail, read on demand
  skills/<name>/assets/             Boilerplate and brand assets
```

## Conventions

- **Bump the version in `plugin.json`** on any change to a skill, so installs can be pinned.
- **The design system is authoritative.** Colors and type live in `references/design-system.md`.
  Skills read from it rather than restating values, which is what stopped it drifting before.
- **Keep skills portable.** No absolute paths and no assumptions about the surrounding repo,
  since these run wherever they are installed.
