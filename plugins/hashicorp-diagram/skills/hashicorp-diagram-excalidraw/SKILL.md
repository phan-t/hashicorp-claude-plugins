---
name: hashicorp-diagram-excalidraw
description: Supplies HashiCorp-branded icons and Helios product colours for architecture diagrams drawn in Excalidraw or Excalidraw+. Ships a stencil scene of 54 Flight icons — product marks, clouds, infrastructure, security and signal vocabulary — with colours pinned to the Helios design system, plus the individual SVGs for dragging in one at a time. Use this skill whenever the user is drawing, editing or asking about a HashiCorp architecture diagram, a Terraform/Vault/Consul/Nomad/Boundary/Packer/Waypoint topology, or wants the correct product colour or icon for a diagram. Also use it to answer "what colour is Vault" or "which icon for a load balancer" — the design system reference is authoritative over memory.
---

# HashiCorp diagram assets for Excalidraw

This skill is **assets, not a generator**. Excalidraw diagrams are drawn by hand; this makes
the hand-drawn ones on-brand. It does not emit diagrams — see "When not to use this" below.

## What ships

| Path | What |
|---|---|
| `assets/hashicorp-stencil.excalidraw` | A scene of all 54 icons, labelled and grouped into five sections. Open it, copy the icons you need into your own diagram. |
| `assets/icons/*.svg` | The same 54 icons as individual files. Drag one onto a canvas to place it. |
| `assets/build_stencil.py` | Regenerates the stencil from `icons/`. |
| `references/design-system.md` | Helios product colours, the icon vocabulary, and Excalidraw's brand limits. |

## Using it

1. **Read `references/design-system.md` before naming a colour.** It is authoritative, and it
   disagrees with the `hashicorp-deck` skills on three products (Vault, Consul, Nomad) — the
   deck skills carry older hexes. Never state a product colour from memory.
2. **To place icons**, either open `assets/hashicorp-stencil.excalidraw` and copy from it, or
   drag single files out of `assets/icons/`. Dragging an SVG onto a canvas creates an image
   element with the file embedded, so the diagram stays self-contained.
3. **Opening the stencil replaces the current canvas.** Excalidraw loads a scene file over
   whatever is open, and the canvas persists in browser local storage. Tell the user to open
   it in a fresh tab or save their work first — do not open it over a diagram in progress.
4. **Set `roughness: 0`** on shapes you create so the diagram reads as an architecture
   drawing rather than a sketch.

## Colour rules

Same restraint as the deck system: the diagram is monochrome, and colour identifies products.

- **Structure is neutral.** Boxes, groups, arrows and labels in `#0c0c0e` on white, or
  `#fafafa` fills for containers. Never a saturated background.
- **Product colour marks a product, nothing else.** A Vault box gets the Vault mark; it does
  not get a yellow fill. If a diagram has more than a handful of coloured moments, the colour
  has stopped meaning anything.
- **Do not tint mono icons per product.** They are infrastructure vocabulary, not brand.

## When not to use this

- **A diagram that must sit inside a deck slide** — Excalidraw has no gradients, no Inter, and
  bakes icon colour, so it cannot match the deck's visual language. Hand-author inline SVG
  instead, using the same Helios colours and the SVGs in `assets/icons/` (which still carry
  `currentColor` and so inherit slide colour).
- **Generating a diagram from a description** — this skill has no generator. Draw it in SVG,
  or draw it by hand in Excalidraw with these assets.

## Maintenance

`hashicorp-stencil.excalidraw` is generated — edit `SECTIONS` in `build_stencil.py` and re-run,
never hand-edit the JSON. The build is deterministic (seeds derive from icon names), so an
unchanged icon set rebuilds byte-identical and shows an empty diff.

The build also **fails** if a Flight icon's colour disagrees with the Helios table in
`build_stencil.py`. That is intentional: an upstream brand refresh should surface as a broken
build, not as diagrams that quietly went stale.
