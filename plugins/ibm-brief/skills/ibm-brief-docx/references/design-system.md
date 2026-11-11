# Design system reference

Every measurement here was read off the PDF proof of IBM's "Solution brief / data sheet"
InDesign template, v1.5 (US Letter, 57 pages of layouts and instructions), with PyMuPDF.
`build_template.py` holds these values and is the only place they are set.

## Page grid

| Measure | Value | Where it shows |
|---|---|---|
| Page | US Letter, 612 × 792pt | |
| Left and right margins | 32pt | All text starts at x = 32 |
| Main column | x = 246.5 to 580, 333.5pt | Title, subtitle, body, headings |
| Side column | x = 32 to 246.5 | Highlights, stats, callouts, standalone headings, side quotes |
| Side text, narrow | 122pt | Highlights, stats, and callouts wrap at x ≈ 154 |
| Side text, wide | 194pt | A standalone heading's intro and a side quote run to x ≈ 226 |
| Content limit | y = 700 | The template's "content should not cross this line" guide |
| Folio and running title | 7pt, baseline y = 760 | Folio at x = 32, title at x = 246.5 |
| 8-bar logo | 58.5 × 21.7pt at (32, 738.3) | Page 1 and the back page |

Tables run the full 548pt from x = 32. A two-column table splits at the main column.

## Type

All IBM Plex, black, on a 12pt baseline grid.

| Style | Face | Size / leading | Notes |
|---|---|---|---|
| Title | Plex Sans Light | 32/40, 28/36 or 24/30 | Three lines at most |
| Subtitle | Plex Sans | 14/20 | 34pt from the title's last baseline |
| Body (`Normal`) | Plex Sans | 9/12 | 12pt between paragraphs |
| Heading 1 | Plex Sans | 14/20 | 52pt above from body, 24pt to body |
| Heading 2 (subheading) | Plex Sans SemiBold | 9/12 | |
| Side Heading | Plex Sans | 14/20 | 48pt between sections |
| Stat | Plex Sans Light | 30/30 | Arrow in IBM Blue; text 24pt below |
| Quote, Quote Box | Plex Serif | 12/16 | Attribution 16pt below the last line |
| Caption | Plex Sans | 7/9 | |
| Legal, Source | Plex Sans | 7/9 | |
| Logotype | Plex Sans Regular + Bold | 16pt | "IBM Consulting", kerned −40 |

Word names Plex's weights by their legacy family names: `IBM Plex Sans Light` and
`IBM Plex Sans SmBld`, not "SemiBold". The shipped TTFs (Plex Sans 1.1.0 and Plex Serif 1.1.0,
font version 3.005) and IBM's installable OTFs carry the same names.

## Colour

| Use | Value |
|---|---|
| Text, rules | `#000000` |
| Links, buttons, stat arrows, the marker square | IBM Blue 60, `#0F62FE` |
| Quote box | `#E5F6FF` |

The template uses no other colour in text. The HashiCorp and Red Hat brief set a stat in red
and a link in purple; the template governs, so neither is offered.

## Elements

- **Marker:** a 6pt IBM Blue square above "Highlights" and above a callout, at y = 272 on
  the cover.
- **Cover:** the title block is a fixed 236pt row, so the highlights and the first body line
  share the y = 296 baseline whatever the title's length. A three-line title starts at the
  top of the page; a shorter one sits on the block's bottom edge.
- **Table:** 0.25pt black rules under the header and every row, no verticals, no fills,
  header in SemiBold, 5pt above and 8pt below each cell's text.
- **Quote box:** fills the main column, text inset 15.5pt, 27pt from the box's top to the
  first baseline.
- **Buttons:** 24pt tall; primary filled IBM Blue with white text, secondary a 0.5pt blue
  outline with black text; a → on the right. "Learn more about IBM" makes a 135.8pt button.
- **Back page:** sources at the top of the main column, the copyright block in the side
  column and the legal text in the main column, both on the bottom margin.

## Measured against the template

A sample brief built with this skill, exported to PDF by Word for Mac and measured the same
way, lands within 1.5pt of the template on each of these:

| Position | Template | This skill |
|---|---|---|
| "Highlights" and first body baseline | 296 | 295.6 |
| Subtitle's last baseline, two-line title | 235 | 234.1 |
| Marker square | 272 to 278 | 273.2 to 279.2 |
| Folio baseline | 760 | 760.5 |
| 8-bar logo | 738.3 to 760 | 738.5 to 760.2 |
| Heading at the top of a page | 48 | 49 |
| Heading to body | 24 | 23.5 |
| Quote box top to first baseline | 27.3 | 27.3 |

## What Word taught

These cost a render each to find. The tests pin them.

- **No style may keep with next or keep lines together.** Almost every paragraph sits in a
  layout-table cell, and there Word reads either flag as "keep this row whole and with the
  next". A cover whose highlights title kept with next pushed the entire body to page 2. The
  template strips both flags from every style, stock ones included. A heading can therefore
  end a page, which is why the SKILL.md checklist asks for a look.
- **Two tables must never touch.** Word merges them. A `Spacer` paragraph, one grid line,
  always separates them.
- **Word ignores a page break inside a table**, so `pagebreak()` puts it on a 1pt
  `Page Break` paragraph between tables.
- **Word does not apply widow control to a cell that splits across pages.** A stat's text can
  leave one line on the next page. Check by eye.
- **Word for Mac ignores embedded fonts** and resolves Plex by name, so the brief renders as
  designed on a Mac only with Plex installed. Windows uses the embedded copies.
- **Word for Mac writes the tab after a list number in Arial** in its PDF export, even with
  the numbering's font set to Plex. It is an invisible whitespace glyph, so `pdffonts` lists
  Arial while no visible text uses it.

## Not reproduced

The template offers more than the builder does. These are left to a designer working in the
InDesign template:

- pictograms beside the highlights, from IBM's pictogram library;
- big numbers in the main column, two to a row;
- images that span two of three columns with a caption beside them, and the image-ratio
  crops on the template's last pages;
- QR codes for printed briefs;
- the business-unit logotypes for units other than the hero units, which need their own
  artwork.

## Refreshing

```
gh release download "@ibm/plex-sans@1.1.0" -R IBM/plex -p ibm-plex-sans.zip
gh release download "@ibm/plex-serif@1.1.0" -R IBM/plex -p ibm-plex-serif.zip
# copy fonts/complete/ttf/IBMPlexSans-{Regular,Bold,Italic,BoldItalic,Light,SemiBold}.ttf
# and IBMPlexSerif-Regular.ttf into assets/fonts/, then:
python3 assets/build_template.py
```

When IBM issues a new template version, re-measure its PDF proof against the tables above,
change `build_template.py`, and render a sample through Word before trusting it.
