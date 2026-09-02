# Interactive layer — optional, and a trade

A page document is static by default: no scripts, no network, one file that renders identically
in any browser and prints cleanly. Four of the five source documents ship exactly that way.
Add JavaScript only when a reader genuinely needs to re-cut the same data, and say in the
document that it needs a browser with scripting.

Three patterns exist, in increasing cost.

## 1. View toggle — two audiences, one file

A team view and a personal view of the same half, switched from the top bar. No data, no
dependencies, ~12 lines.

```html
<div class="viewtoggle" role="group" aria-label="View switch">
  <button data-view="team" aria-pressed="true">Team</button>
  <button data-view="personal" aria-pressed="false">Personal</button>
</div>

<div id="view-team"> ... </div>
<div id="view-personal" hidden> ... </div>
```

```js
(function(){
  var vt=document.getElementById('view-team'),vp=document.getElementById('view-personal');
  var btns=document.querySelectorAll('.viewtoggle button');
  btns.forEach(function(b){b.addEventListener('click',function(){
    btns.forEach(function(x){x.setAttribute('aria-pressed','false')});
    b.setAttribute('aria-pressed','true');
    var personal=b.dataset.view==='personal';
    vt.hidden=personal; vp.hidden=!personal;
    window.scrollTo(0,0);
  })});
})();
```

Toggle with the `hidden` property, not `style.display` — `[hidden]{display:none!important}` is
in the template. `aria-pressed` is the state; the CSS reads it, so there is no second source of
truth.

## 2. Filter bar — one dimension, recomputed

A sticky `.filterbar` of `.fbtn` buttons that re-cuts every chart, table and hero stat on the
page. The pattern:

```html
<div class="filterbar">
  <div class="wrap">
    <span class="fl">Region</span>
    <button class="fbtn" data-region="ALL" aria-pressed="true">All APJ</button>
    <button class="fbtn" data-region="ANZ" aria-pressed="false">ANZ</button>
    <span class="fnote" id="fnote">showing 139 of 139 requests</span>
  </div>
</div>
```

```js
function apply(region){
  const rows = region==='ALL' ? DATA : DATA.filter(r => r.g===region);
  // recompute every stat, chart dataset and table body from `rows`
}
document.querySelectorAll('.fbtn').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.fbtn').forEach(x => x.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed','true');
  apply(b.dataset.region);
}));
```

Rules:

- **One flat `DATA` array of row objects, embedded in the page**, and every displayed figure
  derived from it. Never carry a hardcoded total beside a computed one — they will diverge.
- Every `.sectag[data-scope]` and `.fnote` updates with the filter, so a screenshot of a
  filtered view is unambiguous about what it is showing.
- A section whose figure cannot be filtered gets `.sectag.solid` naming its fixed scope.
- Filtering only ever narrows rows. It must never change a definition, a denominator rule or a
  date window; those belong in the prose.

## 3. Chart.js — when a chart must be interactive

Load one pinned version from cdnjs, before the inline script:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
```

Set the defaults from the brand tokens once, so charts match the page:

```js
Chart.defaults.font.family = "'Inter','Helvetica Neue',Helvetica,Arial,sans-serif";
Chart.defaults.font.size = 12.5;
Chart.defaults.color = '#656a76';
```

Series colours come from `--c1`…`--c4` in that fixed order. Each canvas sits in
`.chartbox > .cwrap` with an explicit pixel height on `.cwrap`, and carries `role="img"` and an
`aria-label` describing what it plots for the selected filter.

**This is the point where the file stops being self-contained.** It now needs the CDN and
scripting to render at all. Before choosing it, check whether `.hbars`, `.vbars` or `.covbar`
would do: they need neither, they keep the numbers readable in the source, and they print.

## Verifying before you hand it over

- `node --check` the inline script, or extract it to a temp file and check that.
- With a `DATA` array: stub `Chart` and `document`, run the script, and call `apply()` for
  every filter value. Each cut's totals must equal the source aggregate. A filter that silently
  drops rows is the failure mode that survives visual review.
- Open the file in a browser with JavaScript disabled. Decide deliberately what a reader sees
  in that state, and if it is a blank section, say so in the document.
