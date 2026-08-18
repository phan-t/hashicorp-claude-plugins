---
name: hashicorp-deck-html
description: Build elegant, single-file HTML5 scroll presentations in a HashiCorp-inspired brand style — a black/white foundation with product-gradient accents, mono structural labels, scroll-reveal animations, side nav, and a clean editorial slide structure. Use this skill whenever the user wants a slide deck, presentation, talk, or technical walkthrough as a self-contained HTML file (not PowerPoint), especially for engineering/developer audiences, project retros, "why I built X" talks, architecture explainers, product updates, or anything where they reference this style, the HashiCorp look, or a previous deck built this way. Prefer this over generic HTML when the user wants a polished, branded, scrollable web presentation.
---

# HashiCorp-style HTML5 presentation

This skill builds a **single, self-contained HTML file**: a vertical scroll deck of full-viewport slides with a refined HashiCorp-inspired aesthetic, scroll-reveal animation, side nav dots, a progress bar, and keyboard paging.

CSS and JS live inline in one `.html` file, so the deck is a single artefact that is trivial to share. Webfonts are the one exception: they load from a CDN, so first render needs network.

## When and how to build

1. **Read the design system first.** Before writing any markup, read `references/design-system.md`. It has the exact CSS tokens, typography rules, slide structure, and layout primitives. Treat those tokens as authoritative and do not invent new colors.
2. **Start from the boilerplate.** Copy `assets/template.html` into the project and build inside it. It already contains the `:root` tokens, base styles, nav/progress/reveal scaffolding, and keyboard paging. Add slides into the `.deck` container.
3. **Save the deck into the project**, at the path the user asked for, or alongside the source content if they have not said. Tell them the path when you are done. It is a file they open in a browser.

## Core aesthetic principles

The look is **"beauty works better"**: restrained, confident, mostly black and white, with color used sparingly and meaningfully.

- **Foundation is monochrome.** White (`--white`) and near-black (`--ink`/`--black`) carry the deck. Most slides are light; use dark slides (`.slide.dark`) and paper slides (`.slide.paper`) to create rhythm between sections.
- **Color is an accent, never a background wash.** The product gradients (purple→blue `--grad-ilm`, pink→purple `--grad-slm`) and single hues (Terraform purple, Vault yellow, Consul pink, Nomad green) appear only on one or two words of a heading, an eyebrow tick, a metric number, or a thin left border. If a slide has more than ~2 accent moments, it's overdesigned.
- **Sentence case everywhere.** Headlines, eyebrows, buttons. Never title case, never ALL CAPS except the mono micro-labels (eyebrows, section tags, captions) which use uppercase + wide letter-spacing.
- **Two typefaces only.** A warm sans (Inter) for display/body, a mono (JetBrains Mono) for structural labels, code, and metrics.
- **Minimal formatting.** Prose over bullets where possible; when bullets are used they're substantial (a bold lead-in + one tight sentence), aligned in a single column, never a ragged multi-column split.
- **Headings have no trailing full-stops.** Internal sentence breaks within a heading are fine; a trailing period is not.

## Slide grammar

Every slide is a `<section class="slide">` (optionally `.dark` or `.paper`) and follows this skeleton:

```html
<section class="slide" data-name="Short name">
  <div class="eyebrow reveal">Mono label for the section</div>
  <h2 class="reveal">Headline with one <span class="grad-text">accented</span> phrase</h2>
  <p class="lede reveal">One or two sentences of framing.</p>
  <!-- content: .row.split for two columns, .cards, .clean list, .fix blocks, or code -->
  <div class="secttag">02 — Section</div>
  <div class="pagenum">03</div>
</section>
```

- `eyebrow` — a short mono uppercase label with a colored tick, names the section's purpose.
- `secttag` (bottom-left) and `pagenum` (bottom-right) — mono wayfinding. Keep section numbers sequential across the deck and page numbers contiguous (01, 02, 03…). **When you add, remove, or reorder slides, renumber both.**
- Add `class="reveal"` to elements that should fade/rise in on scroll. Stagger happens automatically.
- `data-name` feeds the nav-dot tooltip.

A typical deck arc: **title → problem → why it matters → what was built/proposed → deep dive(s) → reflection/lessons → closing punchline.** Open and close strong; vary `.dark`/`.paper`/default backgrounds so consecutive slides don't blur together.

## Content blocks

Compose slide bodies from these primitives (all defined in the template and `references/design-system.md`):

- **`.row.split`** — a two-column layout (text + supporting visual/list), collapses to one column on narrow screens.
- **`.cards`** — a responsive grid of metric/feature cards, each with a big `.num`, a mono `.cap` caption, and small `.desc` prose. Ideal for stats, comparisons, or a "by the numbers" slide.
- **`ul.clean`** — a bullet list with colored dots; each item a bold lead-in plus one tight sentence, all in a single aligned column.
- **`.fix`** — a block with a colored left border and a small mono `.tag` chip; good for before/after, problem/cause pairs, or itemized takeaways.
- **`pre`** — a dark code block with syntax-accent spans (`.c` comment, `.k` keyword, `.s` string, `.n` number).
- **`.lockup`** — a small brand/byline lockup with a gradient square; good for a sign-off or repo/handle line.

## Output and accessibility

- One `.html` file written into the project, at the path the user asked for.
- Fonts load from a CDN, so the deck needs network access on first render. Everything else is inline. If the user needs it fully offline, say so and inline or drop the webfonts rather than letting it fail silently.
- Keep state in JS variables rather than `localStorage`/`sessionStorage`, so the deck also works when opened in a sandboxed viewer.
- Respect `prefers-reduced-motion`: reveal and transition animations must degrade to static final states. The template already does this, so preserve it.
- Validate the script block with `node --check` before handing it over, if Node is available.
- Open the finished file and look at it before calling it done. The design system covers color and type, not whether a heading collided with a nav dot.

## Quick checklist before presenting

- [ ] Monochrome foundation; accents are sparse and gradient/hue-based.
- [ ] Sentence case; no trailing full-stops on headings.
- [ ] Eyebrow + secttag + pagenum on every slide; numbers sequential.
- [ ] Background rhythm varied across sections.
- [ ] Reduced-motion handled; no browser storage used.
- [ ] Deck written to the agreed path, and opened and eyeballed.
