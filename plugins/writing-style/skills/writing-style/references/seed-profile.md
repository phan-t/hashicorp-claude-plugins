# Writing style profile

The author's own rules, learned from their edits and corrections. This file outranks the
skill's references. Each rule cites its evidence. A rule seen once is **tentative** and a rule
seen twice or more is **firm**. Edit this file by hand whenever you like, because the skill
re-reads it each time.

Last updated: 2026-10-27

## Voice

Plain, specific, and explanatory. Writes as an engineer explaining a decision to a peer: what
was done, why, what it costs, and how it was checked. Prefers a full sentence that carries its
reason over a punchy fragment. Australian English.

## Rules

### R1. Full sentences, not dash-and-fragment · firm
Join a clause with a comma, "which", "so" or "because" rather than an em dash followed by a
fragment. One em dash pair around a genuine aside is acceptable.
- Evidence (README, c20f27f): "…with the demo slides and unused media removed — IBM's 21 MB down
  to 144 KB…" became "…removed, which takes IBM's from 21 MB to 144 KB…"
- Evidence (c20f27f commit message): "Plain sentences in place of the dash-and-fragment style".

### R2. State the claim; no "X, not Y." fragments · firm
Contrast fragments read as slogans. First try dropping the contrast and stating the claim. Use
"rather than" only when both sides are real options the reader would weigh, because "rather
than" in every other paragraph becomes its own tell (9 in one 12,000-word report).
- Evidence (design document, 2026-10-08): "The route from phase one to phase two is an
  addition, not a re-architecture." became "Moving from phase one to phase two only adds
  clusters."
- Evidence (test report, 2026-10-21): "the results show relative capacity rather than
  what the hardware will sustain" became "the results show relative capacity. They don't show
  what the hardware will sustain"

### R3. Lists in prose use commas and "and", never slashes · tentative
- Evidence (README, c20f27f): "ID / Impact / Effort / Priority / Category" became "ID, Impact,
  Effort, Priority and Category".

### R4. Oxford comma in every list · firm
Put a comma before the "and" or "or" that ends a list of three or more, in every document,
customer-facing or not. HashiCorp's Voice, Style & Language guide requires it, and one rule
everywhere is easier to keep than two.
- Evidence (author, 2026-10-24): after comparing the profile with the HashiCorp guide, chose
  "consistent across everything" and asked for the serial comma.

### R5. Plain statement over clever framing · tentative
- Evidence (README, c20f27f): "Name a font and you have only made a request." became "Naming a
  font is only a request."

### R6. Say how to verify, and why the obvious check is not enough · tentative
- Evidence (README, c20f27f): "Verify by rendering and reading back which fonts the PDF actually
  used." became "To check which font a file really uses, render it and read back the font table
  of the resulting PDF, because a substitute can look close enough to pass by eye."

### R7. Australian spelling · tentative
colour, modelled, artefact, utilisation, organisation, behaviour, licence (noun). Leave
identifiers, CSS properties, and product names alone.
- Evidence: "colours" in the README plugin table, "artefact" in hashicorp-page-html, git
  author timezone +1000.

### R8. Commit messages · tentative
Imperative subject line under about 60 characters with no full stop. The body explains why the
change was made, what it rules out, and how it was verified. Close with what did not change when
that is useful ("No change to any skill.").
- Evidence: git log of hashicorp-claude-plugins.

### R9. Say what the cost is; no balanced pairs written for rhythm · firm
Name the cost and who pays it. Two clauses or sentences built to mirror each other ("X carries
its cost here, Y carries it there", "X fixes A. Y fixes B.") read as a slogan. Say what each
part does, in whatever shape the facts take.
- Evidence (author, 2026-10-08): called "and carries its cost every day" AI slop; the pair became
  "Option A suits degraded running as a planned operating mode. Option B suits a programme
  where degraded running is rare."
- Evidence (author, 2026-10-22, Boundary deck): "Vault fixes the credential. Boundary
  fixes the path to the system" became "Vault makes credentials short-lived, and Boundary limits
  which systems they reach".

### R10. No maxims · firm
Don't state a general law to sound authoritative. State the specific consequence for this system.
- Evidence (author, 2026-10-08): "A rarely used procedure fails when it's needed." became "The
  procedure is rarely used."
- Evidence (author, 2026-10-08): "It happens at the worst time." became "It happens during the
  incident."

### R11. No cleft, "is how" or "is where" framing · firm
Put the subject first and say what it does.
- Evidence (author, 2026-10-08): "Terraform Stacks are how this design is built." became "This
  design is built with Terraform Stacks."
- Evidence (author, 2026-10-22, Boundary deck): "Dedicated agent auth is where Boundary
  is investing next." became "Boundary is building dedicated agent auth next."

### R12. No idiom, personification or slogan, in headings and labels too · firm
Systems are not "native", deployments are not "rehearsed by use", and nothing happens "on the
day". Say the literal thing. Card titles, column headers, phase names, and eyebrows follow the
same rules as sentences: a label names the literal thing.
- Evidence (author, 2026-10-22, Boundary deck): "Four places this pattern lets you
  down" became "Four risks in this pattern"; "Nothing hidden" became "Attribution"; "The pain" /
  "The benefit" became "Today" / "With Boundary and Vault".
- Evidence (author, 2026-10-08): "Isolation is native." became "Isolation needs no new cluster.";
  "It is a component in its own right and needs its own availability design." became "It needs
  its own availability design."

### R13. A section title cited in prose takes a singular verb · tentative
"**Design decisions and accepted risks** sets out…", even when the title reads as plural.
- Evidence (author, 2026-10-07): reverted Word's "set out" back to "sets out" in two places.

### R14. Keep each piece of detail at its level · firm
A list's items sit at one level of detail: don't put a runbook step among categories, lift it
to the category it belongs to. On a slide, say what each product does, and put mechanism
(protocol steps, challenge types, which component runs where) in the speaker notes.
- Evidence (author, 2026-10-20): in a list of failure domains, "stepping the active node down
  before maintenance" was "a bit specific" and became "coordinating maintenance with Vault's
  operators".
- Evidence (author, 2026-10-26, CLM slide): cut "Vault Agent on the web host answers the
  ACME HTTP-01 challenge." from a card, and reduced the lede to each product's role.

### R15. No sentence that announces the structure that follows · tentative
If labelled paragraphs or a figure carry the point, don't summarise them in a lead-in line.
- Evidence (author, 2026-10-20): removed "Each vendor supports its own product." from above
  three labelled paragraphs that each said who supports what.

### R19. Capitalise a named discipline in a title · tentative
A practice known by its acronym takes capitals in a deck title, even on a sentence-case template.
Other words in the title stay in sentence case.
- Evidence (author, 2026-10-26, CLM slide): "Certificate lifecycle management with
  <partner product>…" became "Certificate Lifecycle Management with <partner product>…" (CLM).

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
review: \b[\w'-]+, (?!(and|or|so|but|then|whether|which|because|if|when|where|while|on|in|with|for|to|specifically|including|namely|such|like|especially|particularly|notably|mainly|mostly|e\.g|i\.e)\b)[\w'-]+( (?!(and|or)\b)[\w'-]+){0,3} (and|or) [\w'-]+ => a comma before the last "and" or "or" (R4)
\bcarr(y|ies|ying) (its|their) cost\b => say what the cost is (R9)
\bcost falls (at|on)\b => say what the cost is (R9)
\bat the worst (time|moment)\b => say when it happens (R10)
\bfails? when (it'?s|it is) (most )?needed\b => state the consequence for this system (R10)
\bwhat (the )?[\w-]+( [\w-]+)? changes is\b => subject first (R11)
\b(is|are) how (this|the) [\w-]+ is (built|done|delivered|deployed)\b => subject first (R11)
\bon the day\b => when it is needed (R12)
\bby use\b(?! (of|cases?)\b) => say how it is tested (R12)
\bin its own right\b => cut (R12)
\bwhich is when it matters\b => cut (R12)
\b(is|are) where [\w-]+( [\w-]+){0,3} (is|are) (investing|heading|going|focused|focusing)\b => subject first (R11)
\bis one of (our|my) questions\b => ask it directly (R11)
\b(lets?|letting) (you|them|us) down\b => name the risk (R12)
\bhold the keys\b => say who holds which credential (R12)
```

## Titles

Headings that name a published work or product by its real title, one per line, exactly as
written. The checker leaves their capitals alone.

```titles
# For example, a line reading: The Staff Engineer's Path
```

## Retired

Rules the author overturned or merged, kept so they are not relearned.

### R16, R17, R18 · merged 2026-10-27
R16 (no balanced pair written for rhythm) merged into R9, R17 (labels are prose too) into R12,
and R18 (on a slide, product roles; mechanism in the notes) into R14, when the author asked to
consolidate overlapping rules. Their numbers are not reused.

### R4. No Oxford comma · retired 2026-10-24
Held from 2026-10-08. Retired when the author adopted the serial comma everywhere so that
personal and HashiCorp-branded writing follow one rule.
