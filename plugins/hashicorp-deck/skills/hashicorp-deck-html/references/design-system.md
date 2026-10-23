# Design system reference

Authoritative tokens, typography, and base styles for the HashiCorp-style deck. Copy these verbatim; do not invent new colors or fonts.

## Brand tokens (`:root`)

```css
:root{
  /* Foundation: black + white primary, neutral gray scale */
  --black:#000000;
  --white:#ffffff;
  --ink:#0a0a0a;
  --gray-900:#171717;
  --gray-800:#242424;
  --gray-700:#3b3b3b;
  --gray-500:#7a7a7a;
  --gray-300:#c2c2c2;
  --gray-100:#ededed;
  --gray-50:#f7f7f5;

  /* Iconic product hues — used ONLY as small accents */
  --tf-purple:#7b42bc;        /* Terraform */
  --tf-purple-bright:#a067e8; /* purple on dark backgrounds */
  --vault-yellow:#ffcf25;     /* Vault */
  --consul-pink:#dc477d;      /* Consul */
  --nomad-green:#60dea9;      /* Nomad */
  /* extra signal hues for data viz / status */
  --solar-yellow:#f5c518;
  --solar-red:#e3492f;

  /* Signature gradients */
  --grad-ilm:linear-gradient(120deg,#7b42bc 0%,#5c4ee5 50%,#2e71e5 100%); /* purple→blue */
  --grad-slm:linear-gradient(120deg,#dc477d 0%,#9a4ec2 60%,#5c4ee5 100%); /* pink→purple */

  --font-display:"Inter",system-ui,sans-serif;
  --font-mono:"JetBrains Mono",ui-monospace,monospace;
}
```

Load fonts via Google Fonts in `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

## Where these values come from

Two authorities publish HashiCorp product colours and they do not agree:

- The **CY26 presentation kit**, whose own "Product colors" slide governs anything that ends
  up on a slide. `hashicorp-deck-htmltopptx` re-typesets onto that kit's master, so the hues
  here match it — otherwise a deck would shift colour on conversion.
- **[Helios](https://helios.hashicorp.design/foundations/colors)**, the product UI system,
  which governs application, diagram, and page-document work. `hashicorp-diagram` and
  `hashicorp-page` follow Helios.

The kit and Helios agree on Terraform (`#7b42bc`) and Vault (`#ffcf25`) and diverge on Consul
(kit `#dc477d`, Helios `#e03875`) and Nomad (kit `#60dea9`, Helios `#06d092`). **For decks the
kit wins.** The divergence is deliberate; do not "fix" these to the Helios values.

Vault was `#ffec6e` here until it was reconciled — that value matched neither authority.

## Color usage rules

- **Backgrounds**: white (default), `--black` (`.dark`), or `--gray-50` (`.paper`). Never a saturated color.
- **Gradients**: only on text (`-webkit-background-clip:text`), a thin left border, or a small swatch. Never as a full slide background.
- **Hues**: one accent per element max — an eyebrow tick, a metric number, or a `.fix` left border. On dark slides prefer `--tf-purple-bright` and `--nomad-green` (they read better than the base purple).

## Typography scale

```css
h1{font-size:clamp(2.6rem,7vw,6rem);font-weight:700;letter-spacing:-.02em;line-height:1.04;}
h2{font-size:clamp(2rem,4.6vw,3.6rem);font-weight:600;letter-spacing:-.02em;line-height:1.04;}
h3{font-size:clamp(1.25rem,2.4vw,1.7rem);font-weight:600;letter-spacing:-.01em;}
.lede{font-size:clamp(1.1rem,1.9vw,1.5rem);font-weight:300;color:var(--gray-700);max-width:46ch;margin-top:1.6rem;}
```

- **Eyebrow** (section label): mono, `.72rem`, uppercase, letter-spacing `.22em`, gray, preceded by a 2.2rem colored tick (`::before` bar in `--tf-purple`).
- **secttag / pagenum / captions**: mono, `~.74rem`, uppercase where structural, `--gray-500`.
- Gradient text helper:
```css
.grad-text{background:var(--grad-ilm);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.grad-text-slm{background:var(--grad-slm);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
```

## Layout primitives

- `.slide` — `min-height:100vh`, generous responsive padding `clamp(2rem,6vw,7rem) clamp(1.5rem,7vw,9rem)`, flex column centered, 1px bottom border between slides.
- `.row.split` — two-column grid `1.05fr .95fr`, collapses to one column under 880px.
- `.cards` — `repeat(auto-fit,minmax(220px,1fr))`; `.card` has 1px border, 16px radius, used for metrics (`.num` big number, `.cap` mono caption, `.desc` small prose).
- `.card .ico` — a feature card's icon: a 44px rounded square in the kit's pastel icon
  gradient holding one 24px Flight icon (see "Icons" below). An icon card has `.ico`, an `h3`
  and a `.desc`, and no `.num`.
- `.clean` list — no bullets-as-discs default; custom colored dot `::before`, each `li` a bold lead-in + sentence. Keep all items in ONE column.
- `.fix` block — content with a 3px colored left border and a small mono `.tag` chip; good for before/after, problem/cause, or itemized points.
- `pre` — dark code block (`--gray-900` bg), mono, with syntax accent spans `.c`(comment/gray) `.k`(keyword/purple) `.s`(string/green) `.n`(number/yellow).
- `.kbd` — inline key/code chip.

## Icons

Icons come from HashiCorp's Flight set, vendored once for the plugin in
`../../assets/icons/flight/` (552 single-colour 24px SVGs, MPL-2.0). Do not draw icons, pull
them from another set, or use emoji. Find one by keyword and print the block to paste:

```bash
python3 ../../assets/icons/flight.py search lock
python3 ../../assets/icons/flight.py ico key
```

```html
<div class="card">
  <div class="ico" data-icon="key"><svg aria-hidden="true" viewBox="0 0 24 24">…</svg></div>
  <h3>Short-lived credentials</h3>
  <p class="desc">One sentence on what this means for the reader.</p>
</div>
```

```css
.card .ico{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;
  justify-content:center;color:var(--ink);
  background:linear-gradient(135deg,#a8b5ff 0%,#cfa9fc 22%,#fdafb5 75%,#ffeeb1 99%);}
.card .ico svg{width:24px;height:24px;display:block;}
.card .ico+h3{margin-top:1.3rem;font-size:clamp(1.05rem,1.6vw,1.25rem);}
```

- The gradient is the CY26 kit's icon square (`A8B5FF`, `CFA9FC`, `FDAFB5`, `FFEEB1` at 45°).
  It is one of the kit's own fills, so it is allowed here even though gradients are otherwise
  text-only. It stays the same on `.dark` slides, and so does the `--ink` icon on it.
- Keep `data-icon`. `hashicorp-deck-htmltopptx` reads it to put the same icon in the same
  column of the .pptx, because a pasted SVG cannot be traced back to its name.
- Match the icon to what the card says. A card about short-lived credentials wants `key` or
  `clock`, even when its heading names a product.
- Use 2 to 4 icon cards on a slide. That is what the kit's icon layouts hold, so a deck
  converts without dropping a card.

## Wayfinding & chrome

- `.progress` — fixed top gradient bar that fills with scroll.
- `.dots` — fixed right-edge nav dots, one per slide, active state in `--tf-purple`; hidden under 880px. Generated from `.slide` elements in JS.
- `.secttag` bottom-left, `.pagenum` bottom-right on each slide.
- Keyboard: ArrowDown/PageDown/Space → next slide; ArrowUp/PageUp → previous.

## Reveal animation

```css
.reveal{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease;}
.reveal.in{opacity:1;transform:none;}
@media(prefers-reduced-motion:reduce){
  .reveal{opacity:1;transform:none;transition:none;}
  html{scroll-behavior:auto;}
}
```
An IntersectionObserver adds `.in` when elements enter view, with a small stagger by index.

The complete, ready-to-use stylesheet and scaffolding are in `assets/template.html`. Start there rather than re-deriving these rules.
