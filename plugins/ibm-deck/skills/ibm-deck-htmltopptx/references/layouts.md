# Layouts reference — the IBM slide grammar

The template ships 48 layouts. `ibm_deck.LAYOUTS` maps a friendly key to each exact IBM name;
pass either to `Deck.add()`. This file covers the ones the builder uses and the traps that
make text land in the wrong place.

## Deck methods and the layouts behind them

| Method | Layout | Slots |
|---|---|---|
| `cover(title, label, meta, image, style)` | Cover, plain / …, label / Cover, imagery, half | title + up to 2 text lines |
| `contents(title, items)` | Contents | title + 2 columns, items split evenly |
| `section(title)` | Section divider | title |
| `statement(text)` | Large text | title, set at display size |
| `quote(text, attribution)` | Callout, stand-alone | one body |
| `callout(title, body)` | Callout, headline | title left, prose right |
| `columns(title, columns, headings)` | Text, 1/2/4 columns (± dividers) | 1–4 columns |
| `metrics(cards, title, note)` | Data, 2/3 callouts, horizontal | number + prose per row |
| `image(title, path, body, style)` | Video or imagery, half / bleed / inset | picture + optional prose |
| `table(title, rows)` | Table | first row is the header |
| `code(title, code, caption)` | Blank slide + drawn panel | up to 26 lines |
| `end()` | End slide | none — it is IBM's closing lockup |

## Trap 1: heading slots and column slots look alike

The "dividers" layouts pair a short heading placeholder **above** each full-height column.
Both are `BODY` placeholders, so neither placeholder order nor vertical position separates
them — the plain 2-column layouts put *full-height* columns at the same `y` the divider
layouts put *headings*.

**Height is the discriminator.** Headings are ~2.0–2.4 in tall, columns ~10–12.7 in.
`Deck.split_bodies()` does this; use it rather than indexing `bodies()` positionally.

Get this wrong and body text silently lands in a 2 in heading slot and overflows the slide.

## Trap 2: the data layouts index inconsistently

| Layout | Title slot is | Number slots | Prose slots |
|---|---|---|---|
| Data, 2 callouts, horizontal | **the first number** | title, 12 | 11, 13 |
| Data, 3 callouts, horizontal | a real headline | 15, 16, 17 | 12, 13, 14 |
| Data, 3 callouts, vertical | a real headline | 15, 16, 17 | 12, 13, 14 |
| Data, 2 callouts, vertical | *(no title)* | 13, 14 | 12, 11 |

`Deck.METRIC_SLOTS` encodes this as a map for exactly that reason. `metrics()` picks a
3-callout layout whenever there is a headline to carry, since the 2-callout layouts spend
their title on a number instead.

## Trap 3: python-pptx drops the running chrome

`slides.add_slide()` clones only title and body placeholders. Footer and slide-number
placeholders — including the `<a:fld>` that makes numbering live — are **not** copied.
`Deck.add()` deep-copies them from the layout. Any slide built without going through it
loses its footer and page number.

## Trap 4: unfilled placeholders ship their prompt text

An untouched placeholder carries "Click to edit Master text styles" into the deck.
`Deck.drop_empty()` removes any placeholder left blank, footer and slide number excepted.
Call it after filling a slide; every `Deck` method already does.

## Column capacity

| Columns | Without headings | With headings |
|---|---|---|
| 1 | Text, 1 wide column, divider | same, heading in the lead slot |
| 2 | Text, 2 columns, small/large title | Text, 2 columns, dividers |
| 3 | Text, 4 columns | Text, 4 columns, dividers, headlines |
| 4 | Text, 4 columns | *no such layout* — headings fold into each column as a bold lead-in |

IBM's 4-column-with-headings layout spends its first column on the slide title, so it holds
three headed columns, not four. `columns()` handles the fourth by folding rather than
dropping, and asking for more columns than a layout has slots raises rather than truncates.

## Layouts the builder does not wrap

Available via `Deck.add(key)` if a deck needs them: `cover_cyan`, `cover_image`,
`boxes_4`, `boxes_4_h`, `boxes_6`, `cols_4_div`, `image_full`, `contacts`, `chart`,
`blank_bare`, and the legal-disclaimer layouts by their exact IBM names. Inspect any layout's
slots with:

```python
for ph in Deck().layout("boxes_6").placeholders:
    f = ph.placeholder_format
    print(f.idx, f.type, ph.width, ph.height)
```
