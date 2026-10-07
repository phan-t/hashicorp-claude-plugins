# Writing style profile

The author's own rules, learned from their edits and corrections. This file outranks the
skill's references. Each rule cites its evidence. A rule seen once is **tentative** and a rule
seen twice or more is **firm**. Edit this file by hand whenever you like, because the skill
re-reads it each time.

Last updated: 2026-10-07

## Voice

Plain, specific and explanatory. Writes as an engineer explaining a decision to a peer: what
was done, why, what it costs and how it was checked. Prefers a full sentence that carries its
reason over a punchy fragment. Australian English.

## Rules

### R1. Full sentences, not dash-and-fragment · firm
Join a clause with a comma, "which", "so" or "because" rather than an em dash followed by a
fragment. One em dash pair around a genuine aside is acceptable.
- Evidence (README, c20f27f): "…the official CY26 presentation kit — Inter, the signature glow
  gradient…" became "…the official CY26 presentation kit using Inter, the signature glow
  gradient…"
- Evidence (README, c20f27f): "…with the demo slides and unused media removed — IBM's 21 MB down
  to 144 KB…" became "…removed, which takes IBM's from 21 MB to 144 KB…"
- Evidence (c20f27f commit message): "Plain sentences in place of the dash-and-fragment style".

### R2. "Rather than" or a real sentence, not "X, not Y." · firm
Contrast fragments read as slogans. Make the contrast part of a sentence with a subject.
- Evidence (README, c20f27f): "Assets, not a generator." became "These are assets rather than a
  generator."
- Evidence (README, c20f27f): "Content conversion, not screenshots." became "It carries the
  content across rather than taking screenshots."
- Evidence (README, c20f27f): "A document, not a deck." became "It is a document rather than a
  deck."

### R3. Lists in prose use commas and "and", never slashes · tentative
- Evidence (README, c20f27f): "ID / Impact / Effort / Priority / Category" became "ID, Impact,
  Effort, Priority and Category".

### R4. No Oxford comma · tentative
- Evidence (README, c20f27f): "…Inter, the signature glow gradient and HashiCorp's own slide
  layouts."

### R5. Plain statement over clever framing · tentative
- Evidence (README, c20f27f): "Name a font and you have only made a request." became "Naming a
  font is only a request."

### R6. Say how to verify, and why the obvious check is not enough · tentative
- Evidence (README, c20f27f): "Verify by rendering and reading back which fonts the PDF actually
  used." became "To check which font a file really uses, render it and read back the font table
  of the resulting PDF, because a substitute can look close enough to pass by eye."

### R7. Australian spelling · tentative
colour, modelled, artefact, utilisation, organisation, behaviour, licence (noun). Leave
identifiers, CSS properties and product names alone.
- Evidence: "colours" in the README plugin table, "artefact" in hashicorp-page-html, git
  author timezone +1000.

### R8. Commit messages · tentative
Imperative subject line under about 60 characters with no full stop. The body explains why the
change was made, what it rules out and how it was verified. Close with what did not change when
that is useful ("No change to any skill.").
- Evidence: git log of hashicorp-claude-plugins.

## Banned patterns

Read by `slop_check.py`. One pattern per line, as `regex => suggestion`. Matching is
case-insensitive. Lines starting with `#` are comments.

```patterns
\bcolor(s|ed|ing)?\b => colour (R7)
\borganiz(e|es|ed|ing|ation|ations)\b => organis- (R7)
\butiliz(e|es|ed|ing|ation)\b => use, or utilis- if the noun is meant (R7)
\bbehavior(s|al)?\b => behaviour (R7)
\bmodeled\b => modelled (R7)
\w+ / \w+ / \w+ => a comma list with "and" (R3)
```

## Retired

Rules the author overturned, kept so they are not relearned.

(none yet)
