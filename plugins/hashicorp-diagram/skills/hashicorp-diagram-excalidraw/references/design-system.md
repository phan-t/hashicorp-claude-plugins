# Design system reference

Authoritative colours and icon vocabulary for HashiCorp architecture diagrams drawn in
Excalidraw. Copy these values verbatim; do not invent product colours.

## Upstream sources

| What | Source | Pinned |
|---|---|---|
| Product colours | [Helios](https://helios.hashicorp.design/foundations/colors) | `@hashicorp/design-system-tokens` 5.1.0, MPL-2.0 |
| Icons | [Helios icon library](https://helios.hashicorp.design/icons/library) | `@hashicorp/flight-icons` 5.1.0, MPL-2.0 |

Helios is the **product UI** system, not the marketing brand kit. Take its product colours
and its icons. Do **not** take its typography — Helios deliberately uses system fonts
(SF Pro, Segoe UI), while the deck skills use Inter. It also diverges from the CY26
presentation kit on several product hues, which is why the table below records both.

## Product colours

These are the Helios values, and they govern **diagrams**. They are not the only HashiCorp
product palette: the CY26 presentation kit publishes its own, and where the two disagree the
kit governs slides while Helios governs diagrams, page documents and application UI. See
`plugins/hashicorp-deck/skills/hashicorp-deck-html/references/design-system.md` and
`plugins/hashicorp-page/skills/hashicorp-page-html/references/design-system.md`.

| Product | Helios (diagrams) | CY26 kit (decks) |
|---|---|---|
| Terraform | `#7b42bc` | `#7b42bc` — agrees |
| Vault | `#ffcf25` | `#ffcf25` — agrees |
| Vault Radar | `#ffcf25` | — |
| Vault Secrets | `#ffcf25` | — |
| Consul | `#e03875` | `#dc477d` |
| Nomad | `#06d092` | `#60dea9` |
| Boundary | `#f24c53` | `#ec585d` |
| Packer | `#02a8ef` | `#63d0ff` |
| Waypoint | `#14c6cb` | `#62d4dc` |
| Vagrant | `#1868f2` | — |
| HCP | `#000000` | — |

The kit's hues are lighter, tuned to read on a projected slide. Do not carry them into a
diagram, and do not carry Helios values into a deck — a deck converted by
`hashicorp-deck-htmltopptx` is re-typeset onto the kit's master and would shift colour.

Neutrals for diagram strokes and labels, from the Helios semantic tokens:

| Role | Token | Hex |
|---|---|---|
| Strokes, labels | `foreground-strong` | `#0c0c0e` |
| Secondary text | `foreground-primary` | `#3b3d45` |
| Muted text | `foreground-faint` | `#656a76` |
| Container fill | `surface-faint` | `#fafafa` |

`build_stencil.py` records the product table in `HELIOS_PRODUCT_HEX` and **fails the build**
if a Flight icon ships a colour that disagrees with it. That is the drift guard: a brand
refresh upstream surfaces as a failed build rather than as a diagram that quietly went stale.

## Icon vocabulary

54 icons are vendored into `assets/icons/`, all at 24px, chosen as a diagram vocabulary
rather than a full mirror of Flight's 1,353:

- **Products** (11, colour variants) — the marks above.
- **Clouds and platforms** (8, colour variants) — aws, azure, gcp, kubernetes, docker,
  github, gitlab, helm.
- **Infrastructure** (17, mono) — server, server-cluster, network, network-alt,
  load-balancer, connection-gateway, node, database, queue, api, module, layers, box,
  globe, globe-private, entry-point, exit-point.
- **Security and identity** (11, mono) — lock, key, keychain, certificate, token, shield,
  identity-service, identity-user, user, users, org.
- **State and signals** (7, mono) — check-circle, alert-triangle, activity, monitor, clock,
  sync, repeat.

Product marks use Flight's `-color` variants, which already carry the exact Helios hexes —
so they are correct by construction with no recolouring. Mono icons ship `currentColor`,
which has no meaning once embedded in a canvas, so the build pins them to
`foreground-strong` (`#0c0c0e`).

## Why a scene and not a library

The obvious deliverable would be an `.excalidrawlib` that loads into Excalidraw's sidebar.
It cannot work. `ExportedLibraryData` is `{type, version, source, libraryItems}` — there is
**no `files` map**, and no image rehydration on library import, so image elements in a
library reference file IDs whose binary data has nowhere to live. They import as broken
placeholders. Scene exports (`ExportedDataState`) *do* carry `files`, which is why the
stencil is a `.excalidraw`.

Verified against `packages/excalidraw/data/types.ts` and `data/json.ts` at
excalidraw/excalidraw master, and `@excalidraw/excalidraw` 0.18.1.

## Excalidraw's limits against the brand

Three things the deck system does that Excalidraw cannot, worth knowing before promising a
diagram will match a slide:

- **No gradients.** `grep -i gradient` over the element types returns nothing; fills are
  solid only. The signature `--grad-ilm` / `--grad-slm` glow has no equivalent.
- **No Inter.** `FONT_FAMILY` is `Virgil 1, Helvetica 2, Cascadia 3, Excalifont 5, Nunito 6,
  Lilita One 7, Comic Shanns 8, Liberation Sans 9, Assistant 10`. Use Helvetica (2) as the
  neutral choice; there is no letter-spacing or weight control, so the mono uppercase
  eyebrow style cannot be reproduced.
- **Icon colour is frozen.** Icons embed as `image` elements with a baked dataURL, so they
  do not inherit canvas colour the way inline SVG inherits `currentColor`. A dark-canvas
  diagram needs a separately built stencil.

Set `roughness: 0` on shapes to drop the hand-drawn look.

## Refreshing the icons

```
npm pack @hashicorp/flight-icons          # 5.1.0, 7.5 MB, 1,353 SVGs
tar xzf hashicorp-flight-icons-*.tgz
cp package/svg/<name>.svg assets/icons/   # only the names listed above
python3 assets/build_stencil.py
```

The strip is 1,353 SVGs (5.4 MB) down to 54 (216 KB), keeping only the vendored vocabulary.
Bump `plugin.json` and the pinned version in the table above when the upstream version moves.
