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
  --vault-yellow:#ffec6e;     /* Vault */
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
- `.clean` list — no bullets-as-discs default; custom colored dot `::before`, each `li` a bold lead-in + sentence. Keep all items in ONE column.
- `.fix` block — content with a 3px colored left border and a small mono `.tag` chip; good for before/after, problem/cause, or itemized points.
- `pre` — dark code block (`--gray-900` bg), mono, with syntax accent spans `.c`(comment/gray) `.k`(keyword/purple) `.s`(string/green) `.n`(number/yellow).
- `.kbd` — inline key/code chip.

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
