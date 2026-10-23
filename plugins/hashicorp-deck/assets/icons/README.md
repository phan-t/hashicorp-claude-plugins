# Flight icons

Both deck skills draw their icons from here: `hashicorp-deck-html` inlines them into `.ico`
cards, and `hashicorp-deck-htmltopptx` draws them into the kit's icon squares as vector shapes.
Keeping one copy means an HTML deck and its .pptx show the same icon in the same column.

| | |
|---|---|
| Source | [Helios icon library](https://helios.hashicorp.design/icons/library) |
| Package | `@hashicorp/flight-icons` 5.3.0, MPL-2.0 (`flight/LICENSE.md`) |
| Contents | 552 of Flight's 24 px single-colour icons, unmodified |
| Index | `flight/catalog.tsv`: name, category, and Flight's own keywords |

The `-color` variants are left out, because a multi-colour mark clashes with the kit's
pastel gradient square. The animated `loading` and `running` icons are left out too; their
`-static` versions are included.

## Finding and using an icon

```bash
python3 flight.py search lock     # names whose name or keywords start with "lock"
python3 flight.py ico key         # an .ico block for an HTML card
```

In python-pptx, pass names to `Deck.columns(..., icons=["key", ...])`. An unknown name raises
with the nearest matches.

Match the icon to what the column says. A column about short-lived credentials wants `key` or
`clock`, even when its heading is "Vault".

## Refreshing

```bash
npm pack @hashicorp/flight-icons
tar xzf hashicorp-flight-icons-*.tgz
for f in package/svg/*-24.svg; do
  case $(basename "$f") in *-color-24.svg|loading-24.svg|running-24.svg) continue;; esac
  cp "$f" flight/
done
cp package/LICENSE.md flight/
```

Then rebuild `catalog.tsv` from `package/catalog.json` (the 24 px entries of `assets`, keyed
by `iconName`), bump the version above and in `plugin.json`, and run
`tests/test_flight_icons.py` at the plugin root. That test converts every icon and
fails on any path data the converter cannot read.
