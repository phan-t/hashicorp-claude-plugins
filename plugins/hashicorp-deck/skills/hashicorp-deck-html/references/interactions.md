# Interactions reference — JS wiring

All scripts go in one `<script>` at the end of `<body>`. They execute after the DOM is present. Animations respect `prefers-reduced-motion`. Validate with `node --check` when possible.

This block is already in `assets/template.html`. It: adds `.in` to `.reveal` elements as they enter view (staggered), builds one nav dot per `.slide`, fills the top progress bar on scroll, highlights the active dot, and pages with arrow keys.

## Reveal-on-scroll

```js
const revObs=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');revObs.unobserve(e.target);}});},{threshold:.18});
document.querySelectorAll('.reveal').forEach((el,i)=>{el.style.transitionDelay=(i%6*0.06)+'s';revObs.observe(el);});
```
Elements fade and rise in as they scroll into view, with a small stagger by index. The matching CSS (`.reveal` / `.reveal.in`) is in design-system.md and degrades to static under reduced motion.

## Nav dots (generated from slides)

```js
const slides=[...document.querySelectorAll('.slide')];
const dots=document.getElementById('dots');
slides.forEach((s,i)=>{if(!s.id)s.id='s'+i;const a=document.createElement('a');a.href='#'+s.id;a.title=s.dataset.name||('Slide '+(i+1));dots.appendChild(a);});
const dotEls=[...dots.children];
```
One dot per slide, tooltip from `data-name`. Hidden under 880px via CSS.

## Progress bar

```js
const prog=document.getElementById('progress');
function onScroll(){const h=document.documentElement;prog.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
```

## Active dot + current slide tracking

```js
let cur=0;
const actObs=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){const idx=slides.indexOf(e.target);cur=idx;dotEls.forEach((d,i)=>d.classList.toggle('active',i===idx));}});},{threshold:.5});
slides.forEach(s=>actObs.observe(s));
```

## Keyboard paging

```js
function go(n){cur=Math.max(0,Math.min(slides.length-1,n));slides[cur].scrollIntoView({behavior:'smooth'});}
window.addEventListener('keydown',(e)=>{
  if(e.key==='ArrowDown'||e.key==='PageDown'||e.key===' '){e.preventDefault();go(cur+1);}
  if(e.key==='ArrowUp'||e.key==='PageUp'){e.preventDefault();go(cur-1);}
});
```

## Optional: animated counters

For a "by the numbers" slide, count a metric up to its target on reveal (easeOutCubic), respecting reduced motion:

```js
function countUp(el, target, dur, suffix){
  if(window.matchMedia('(prefers-reduced-motion:reduce)').matches){el.textContent=target+(suffix||'');return;}
  const start=performance.now();
  (function frame(now){const t=Math.min(1,(now-start)/dur),e=1-Math.pow(1-t,3);
    el.textContent=Math.round(target*e)+(suffix||''); if(t<1)requestAnimationFrame(frame);})(start);
}
```
Trigger it from an IntersectionObserver when the card enters view.

## Renumbering reminder

When slides are added/removed/reordered, update each slide's `.secttag` and `.pagenum`. Nav dots and reveal regenerate automatically from the DOM, but the printed numbers do not.
