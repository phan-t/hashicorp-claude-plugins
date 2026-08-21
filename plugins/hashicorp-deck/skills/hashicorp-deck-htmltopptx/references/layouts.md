# Layouts reference — the HashiCorp slide grammar

The kit ships 47 layouts. `hashicorp_deck.LAYOUTS` maps a friendly key to each exact
HashiCorp name; pass either to `Deck.add()`. This file covers the ones the builder uses and
the traps that make text land in the wrong place.

## Deck methods and the layouts behind them

| Method | Layout | Slots |
|---|---|---|
| `cover(title, subtitle, kicker, date, speaker, speaker_title)` | General Divider | 6 named slots |
| `product_cover(title, product, lines)` | Cover - Terraform / Vault / … | title + 2 lines |
| `agenda(title, items, numbers)` | Agenda | title + 6 items, each with a page number |
| `section(title)` | Section Divider | title only, over a full-bleed gradient |
| `titled(title, subtitle)` | Title Subtitle | title + subtitle, then a bare canvas |
| `eyebrow(title, eyebrow)` | Eyebrow Title | title with a small label *above* it |
| `quote(text, attribution)` | Quote-3lines | one slot, in the glow gradient |
| `body(title, prose, bullets, subtitle)` | Content- body + bullet list | prose left, bullets right |
| `columns(title, columns, subtitle, headings)` | Content - N-column bullet / Icon Text Container | 2–4 columns |
| `metrics(cards, title, subtitle)` | 2 Metric / 3 Metric | number + caption per card |
| `image(title, path, subtitle, body, style)` | Image Overlay - small right/left/large | picture + copy |
| `speaker(name, lines, image)` | Speaker-1 | name, detail lines, portrait |
| `table(title, rows, subtitle)` | Title Subtitle + drawn table | first row is the header |
| `chart(title, categories, series, subtitle)` | Title Subtitle + native chart | one value axis |
| `code(title, code, caption, subtitle)` | Title Subtitle + drawn panel | up to 20 lines |
| `end(text)` | Thank You | one slot, defaults to "Thank you" |

## Trap 1: most "titles" are not title placeholders

The kit's General Divider — the layout behind `cover()` — has **no title placeholder at
all**. Its six slots are plain bodies at idx 10–15, and `slide.shapes.title` is `None`.
The same is true of Quote-3lines (idx 13) and Thank You (idx 11).

`Deck.COVER_SLOTS` names those six so calling code never counts placeholders:

| Slot | idx | Kit's own prompt |
|---|---|---|
| kicker | 10 | `<Customer Name – Briefing>` |
| title | 11 | Title |
| subtitle | 12 | Sub-title |
| date | 13 | Date |
| speaker | 14 | `[Speaker name]` |
| speaker_title | 15 | `[Speaker title]` |

Reach for `Deck.ph(slide, idx)` on these layouts, not `shapes.title`.

## Trap 2: the metric layouts index unevenly

| Layout | Number slots | Caption slots |
|---|---|---|
| 2 Metric | 13, 23 | 22, 26 |
| 3 Metric | 13, 16, 19 | 22, 23, 24 |

`Deck.METRIC_SLOTS` encodes this as a map for exactly that reason — the 2-metric layout
jumps 13 → 22 → 23 → 26, so neither index order nor a stride works.

Both layouts give the number the four-stop glow gradient and a matching gradient rule
beneath it. That comes from the layout's list style, so pass the value as plain text and
set no colour; setting one replaces the gradient with a flat fill.

## Trap 3: only one of the two body columns has bullets

"Content- body + bullet list" is named literally. Its left slot (idx 13) is prose with
`buNone`; its right slot (idx 14) carries the bullet character. They are not
interchangeable, which is why `body()` takes `prose=` and `bullets=` by name rather than a
list of columns.

The same split runs through the whole family:

| Layout | Shape |
|---|---|
| Content- body + bullet list | 2 half-width columns: prose, then bullets |
| Content- body + bullet list, N-column | N columns × 2 rows: prose on top, bullets beneath |
| Content - N-column bullet | N full-height columns, all bulleted |
| Icon Text Container - N-column | N columns: bold header over a short paragraph, under an icon |

A lone bullet list has no home in this kit — every layout that bullets is at least two
columns wide. `body()` with only `bullets=` leaves the left half empty on purpose, and the
converter reports it rather than inventing a lede.

## Trap 4: the icon headers inherit a bullet

On all three Icon Text Container layouts, the header slots (idx 16, 18, 20, 22) do **not**
set `buNone` — they leave the bullet inherited, so it resolves to the master's bullet
character and the header renders as "• Self-service". Their body slots below do set
`buNone`, which is what makes the omission easy to miss.

HashiCorp's own slides fix this per-paragraph rather than in the layout, and
`hashicorp_deck.clear_bullet()` does the same. `columns()` applies it to every heading.
These are the only text slots this skill uses that leave the bullet inherited — the rest of
that list is picture placeholders and Microsoft's stock layouts.

## Trap 5: the tight slots disable shrink-to-fit

Every slot on the General Divider carries `<a:noAutofit/>`. A cover title that runs past one
line does not shrink — it wraps and lands on top of the subtitle, which lands on the date.
Rendered proof: a 26-character title at 48 pt in a 7.6 in slot wraps, and the second line
sits across the subtitle.

`Deck.check_fit()` predicts this and appends to `Deck.warnings`; `cover()` runs it on the
title and subtitle, and the converter prints the warnings as `!` lines. Nothing is changed
for you — shorten the copy, or accept the wrap knowingly. As a rule of thumb the cover title
holds about **22 characters** and the subtitle about **44**.

## Trap 6: unfilled placeholders ship real-looking copy

The kit prompts many slots with words that read as deliberate content — "Metric", "Details
here / 2 lines max", "[Speaker name]", "xx%". An untouched placeholder ships them.
`Deck.drop_empty()` removes any placeholder left blank; every `Deck` method already calls it.

## The Agenda pairs its slots out of order

Item text is idx 1–6 and the page numbers are idx 11–16, but idx **16** sits beside idx 1,
not idx 6. `agenda()` therefore reads both runs in vertical order and zips them, which
pairs them correctly whatever the indices say. Six items maximum; asking for more raises.

## Column capacity

| Columns | Without headings | With headings |
|---|---|---|
| 1–2 | Content- body + bullet list | Icon Text Container - 2-column |
| 3 | Content - 3-column bullet | Icon Text Container - 3-column |
| 4 | Content - 4-column bullet | Icon Text Container - 4-column |

The icon layouts' body slots carry no bullet character, so `columns()` writes a list of
points there as separate lines rather than running them together into one sentence.

## Layouts the builder does not wrap

Available via `Deck.add(key)` if a deck needs them: `pillars` (3 Pillars — its three
headings are static art, so it takes only a title and subtitle), `grid_2` / `grid_3` /
`grid_4`, `images_2`, `images_3`, `speakers_2`, `gradient` (Blank-Gradient, a bare
brand-gradient canvas), `blank`, and Microsoft's stock layouts by their own names.

Two layouts from the shipped kit are **not** in this template: *Do cloud right* and *Dark*.
Both are pure decoration with no placeholders to fill, and between them they carried 18 MB
of artwork. See `design-system.md`.

Inspect any layout's slots with:

```python
for ph in Deck().layout("icons_3").placeholders:
    f = ph.placeholder_format
    print(f.idx, f.type, ph.width, ph.height, ph.top)
```
