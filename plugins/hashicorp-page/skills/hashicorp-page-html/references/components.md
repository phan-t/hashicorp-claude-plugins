# Component reference — the block grammar

Every block below is styled by `assets/template.html`. Compose a section from these; do not
invent a new block when one of these fits.

## Document chrome

### Top bar

Always present. Wordmark on the left with the inlined logomark, status tags on the right.

```html
<div class="topbar">
  <div class="wrap">
    <div class="wordmark">
      <svg class="hc-logo" ...>...</svg>
      HashiCorp <span style="color:#9aa0ab;font-weight:400">/ SE ANZ &amp; SA APAC</span>
    </div>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <span class="tag conf">Confidential</span>
      <div class="tag">H2 2026 · operating model · draft</div>
    </div>
  </div>
</div>
```

The logomark is inlined as SVG, white fill, from `assets/hashicorp-logomark-white.svg`. Never
hotlink it, never redraw it, never recolour it.

### Confidentiality bar

Only for restricted documents, directly under the top bar, paired with `.tag.conf`. It names
what is sensitive, who must not receive it, and what must not be communicated as decided.

```html
<div class="confbar">
  <div class="wrap">
    <b>RESTRICTED. LEADERSHIP ONLY.</b> This document discusses reporting-line and incentive-plan
    changes affecting named individuals. Not for distribution to the teams or to sellers.
    Model 2 has not been decided and must not be communicated as a plan.
  </div>
</div>
```

Write it specifically or leave it out. A generic "internal use only" bar trains readers to
ignore the real ones.

### Hero

```html
<header class="hero">
  <div class="wrap">
    <p class="eyebrow">Solutions Architecture · operating model · remaining H2 2026</p>
    <h1>Two models for SA.<br>One decision, and the <span class="grad">right time</span> to make it.</h1>
    <p class="lede">Framing: what this decides, what evidence it rests on, what is being asked.</p>
    <div class="statstrip" role="list" aria-label="Headline numbers">
      <div class="stat" role="listitem"><div class="n">82%</div><div class="l">of SA hours already served in-region</div></div>
      <!-- 3 to 6 of these -->
    </div>
  </div>
</header>
```

The H1 states the finding as a sentence, not a topic. `<br>` controls the break; one phrase
takes `.grad`. Add `.sec` to `.hero` to switch to the security gradient, `.small` for a
secondary hero inside a toggled view.

`.statstrip` holds three to six numbers, each with a mono label saying what it measures. These
are the numbers the reader will quote back, so they must all appear again, sourced, in a
section below.

### Footer

```html
<footer>
  <div class="wrap">
    <div>
      <div><b style="color:#fff">Confidential, leadership only.</b> What this document is.</div>
      <div class="m" style="margin-top:8px">Prepared by Tony Phan · 17 Aug 2026 · draft for discussion, not a decision record</div>
    </div>
    <div class="m">
      SA data: team-impact-reporter, 2 Jan – 29 Jun 26<br>
      Book data: FY26 Final Territory List, eff. 1 Jun 26<br>
      Companion docs: h2-2026/plan.md
    </div>
  </div>
</footer>
```

Left: what it is and its status. Right, in mono: every data source with its window, and any
companion documents.

## Section shell

```html
<section id="asks" class="alt">
  <div class="wrap">
    <div class="seclabel"><span class="idx">07</span><h2>Leadership asks</h2><span class="sectag">3 open · backfills approved</span></div>
    <div class="keyline"></div>
    <p class="secintro">The paragraph that carries the finding, with the numbers in it.</p>
    ...
  </div>
</section>
```

`.sectag` is optional — a status, a scope, a count. `.sectag.solid` for the filled black
variant when it states the active scope of a filtered view. `.keyline.sec` switches gradient.

## Content blocks

### `.cards` — a row of parallel claims

`repeat(auto-fit,minmax(280px,1fr))`. Each card's `h3` is a claim, not a label; `p` is the
evidence; `.kpi` is the mono figure line under it. `acc-terraform` / `acc-vault` /
`acc-consul` / `acc-nomad` / `acc-boundary` / `acc-packer` set the top border; adjacent cards
must differ. Two to four per row.

```html
<div class="cards">
  <div class="card acc-boundary">
    <h3>The ANZ SE bench is half its intended size</h3>
    <p>Five SEs and the Regional Director have gone or are going between Oct 2025 and Sep 2026.</p>
    <div class="kpi">$32.2M book · 5 SEs + manager · 11% still uncovered</div>
  </div>
</div>
```

### `.models` — two mutually exclusive options, side by side

For a decision document with exactly two candidates. `.mtag` names the option, `.status` its
current standing, `.desc` defines it in one paragraph. Optional `.pc.pro` / `.pc.con` lists.

```html
<div class="models">
  <div class="model m1">
    <div class="mtag">Model 1 · status quo</div>
    <h3>SA as an APAC practice</h3>
    <span class="status">Current state · in effect since 1 Aug 2026</span>
    <p class="desc">One paragraph defining it.</p>
    <div class="pc pro">
      <h4><span class="dot"></span>What it protects</h4>
      <ul><li><b>Lead-in.</b> One tight sentence.</li></ul>
    </div>
  </div>
  <div class="model m2"> ... </div>
</div>
```

Define the options here, then score them in a comparison table. Do not do both in one block.

### `.tablebox` — every table

Always wrap a `<table>` in `.tablebox` so it scrolls on narrow screens instead of breaking the
page. `th.num` / `td.num` right-align and tabularise; `td.mono` for identifiers and dates.
`tr.grp` is a black full-width group header row inside `tbody`, `tr.sub` a tinted subtotal.

A comparison matrix puts the criterion in column one, one column per option carrying a `.pill`
verdict plus a short clause, and the evidence in a final `td.mono`:

```html
<tr>
  <td><b>Preserves the depth adoption needs</b></td>
  <td><span class="pill good">Yes</span> Separate ladder, account-aligned</td>
  <td><span class="pill crit">At risk</span> Quarterly pressure spends depth on closing</td>
  <td class="mono">median depth already −49% YoY</td>
</tr>
```

Wrap a long backing table in `details.tv` so it is available without dominating the page:

```html
<details class="tv">
  <summary>Table view · SA like-for-like window</summary>
  <div class="tablebox"><table>...</table></div>
</details>
```

### `.pill` — inline verdicts and categories

`.good` / `.warn` / `.crit` for status. `.t0`–`.t5` are category tints (`t0` neutral, then
purple, blue, pink, green, amber) — the source documents used them for regions. `.fill1` /
`.fill2` are solid, for the two options in a decision document. A bare `.pill` is a neutral
outline chip, used in an ask's `.meta` row for cost and deadline.

### `.chip` — product marks

`.chip.terraform` / `.vault` / `.consul` / `.boundary` / `.nomad` / `.packer`. Only where the
chip genuinely means that product.

### `.note` — callouts

```html
<div class="note"><b>Volume held. Depth halved.</b> The reading the data supports.</div>
<div class="note crit"><b>The sensitivity.</b> The risk, the caveat, or the competing explanation.</div>
```

Vault-yellow left border, or Boundary red with `.crit`. Use one to state the honest reading of
a figure, including the reading that weakens your own argument. Three per section is too many.

### `.src` — provenance

Mono, small, immediately under the thing it sources. Extract date, what it includes, what it
supersedes.

### `.heroNum` — headline numbers inside a section

`.n` (optionally `.c1` / `.c2` / `.crit`), `.l` mono label, `.d` a sentence of interpretation.

### `.asks` — numbered, ranked requests

```html
<div class="asks">
  <div class="ask a4">
    <div class="an">ASK 01 · decide, then sequence</div>
    <h3>Decide the SA model in H2, implement at the FY27 boundary</h3>
    <p>What is being asked, with the date in bold.</p>
    <p><b>Why the split:</b> the reasoning.</p>
    <div class="meta"><span class="pill fill2">Decision ask</span><span class="pill">Cost: nil</span><span class="pill crit">Decide by: 30 Sep 26</span></div>
  </div>
</div>
```

`.an` carries the number and a verb. `a2`–`a6` vary the left border. Every ask ends with a
`.meta` row stating who it binds, what it costs, and by when. An ask without a date is a wish.

### `.seq` — sequencing

Equal-width steps in a row, each with a mono `.when`, an imperative `h4`, and one sentence.

### Figures

`.figure` wraps a `.figtitle`, a mono `.figsub` stating units and basis, an optional
`.legend`, and the chart itself.

- **`.hbars`** — a three-column grid repeated per row: `.hlab` label, `.htrack` containing a
  `.hbar` whose `width` percentage is the value, `.hval` the number in text. Segment with
  `.hseg.s1` / `.hseg.s2` for a stacked bar. Put the full figure in a `title` attribute.
- **`.smallmult` / `.vbars`** — small multiples of vertical bars; `.vcol` holds `.vv` (value)
  above `.vb` (the bar, height set inline), with `.vaxis` labels underneath.
- **`.covbar`** — one stacked proportion bar. Segments take `width` or `flex-basis`
  percentages, a `.n` name and a `.v` value, and an explicit background and text colour. Give
  the bar `role="img"` and an `aria-label` with the totals. A `repeating-linear-gradient`
  hatch marks an uncovered or provisional segment.
- **`.covzones`** — the breakdown behind a proportion bar: `.zone.bad` and `.zone.good`
  columns of `.zcard` entries. `.covstrip` is the black summary strip below it.
- **`.fig`** — a bordered container for an SVG or PNG figure with a mono `figcaption`. Use it
  when a chart is built outside the page; inline the SVG rather than linking it.

All bar geometry is inline percentages, so the numbers are visible in the source and the page
needs no JavaScript to draw a chart.
