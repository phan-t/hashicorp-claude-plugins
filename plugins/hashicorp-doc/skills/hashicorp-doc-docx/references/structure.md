# Document structure

The shape of a HashiCorp assessment, and why each part is there. The styling is in
`design-system.md`; this file is about what to write.

```
cover              art · title · subtitle · date · metadata block · wordmark
contents           live TOC field over Heading 1 and Heading 2
document version   revision history table
Introduction       Executive Summary · Challenges · Highlights (recommendation table)
<Area 1>           Current State · Recommendations
<Area 2>           Current State · Recommendations
…
Resources          numbered links to the guides the recommendations lean on
back cover         art · address block
```

Each `h1` starts a new page — `Doc.h1()` enforces it.

## Cover metadata

The block under the date is the document's provenance, and every line earns its place:

| Field | Why it is there |
|---|---|
| Company Name | The legal entity, not the trading name. |
| Company Address | Which office the engagement was run out of. |
| Primary Contact | The customer who owns this document on their side. |
| Phone Number, Email Address | Reachable without opening a CRM. |
| HashiCorp Account Team | Who to escalate to; link the names to email. |
| Document Author | Who wrote it and can defend a finding. |
| Internal Identifiers | The opportunity or project id, so it can be found later. |
| Last Modified | Distinguishes a stale copy from the current one. |

Leave a field out rather than filling it with `TBD`. `cover(logo=...)` places the
*customer's* mark, not HashiCorp's — the HashiCorp wordmark is already in the footer.

## Document version table

Version, Date, Author, Changes — one row per issued draft, oldest first. It matters more
than it looks: the customer will circulate this file, and the running header carries only
the version number, so this table is the only place that says what changed between `0.2`
and `1.0`. Keep `Doc(version=...)` in step with the last row.

Use `0.x` while the document is in review and `1.0` on release.

## Introduction

**Executive Summary** — four to six paragraphs, and it must stand alone. Someone who reads
only this page should come away with: who was engaged and why, when the workshops ran, the
state of the platform today, and the conclusion. Say plainly whether the findings are risks
or improvements; the reference says *"these are not significant risks but rather
enhancements to the platform's long-term capabilities"*, and that sentence is what stops an
assessment from reading as an audit. Close with the scope, and name the customer's core
contributors — the engagement is theirs too.

**Challenges** — a numbered list of what the customer told you, in their framing, in no
particular order. Say so: "the following challenges were brought to our attention during
the workshop sessions; these are outlined in no particular order." These are *their* words,
not your findings. Your findings come later, and the reader should be able to tell the two
apart.

**Highlights → Key Recommendations** — the recommendation table, every recommendation in
the document, in one place. Prefaced by a short read of what the table says: which are
quick wins, which are architectural, and what they add up to.

## The recommendation table

| Column | Holds |
|---|---|
| **ID** | Area prefix and letter: `ARC-A1`, `ARC-B`, `OPS-C`, `UX-A`. |
| **Recommendation** | One sentence, imperative, with its justification attached: *"Operate the ISD PR cluster for ISD consumers to enhance security and locality, and reduce latency."* |
| **Impact** | High / Medium / Low — what it buys. |
| **Effort** | High / Medium / Low — what it costs. |
| **Priority** | High / Medium / Low — your call, given the other two. |
| **Category** | Tactical or Strategic. |

The ID is the point of the table. It lets someone say "we are doing ARC-A1 this quarter and
deferring ARC-A3" six months after the engagement closed, and it lets the body of the
document argue for a recommendation without restating it. **Reference the ID in the section
that argues for it.**

Number within an area, and sub-number when one recommendation has variants that must be
chosen between: `ARC-A1`, `ARC-A2`, `ARC-A3` are three options for the same problem;
`ARC-B` is a different problem.

Impact, Effort and Priority are a judgement, so make it. A table where everything is High
Impact / High Priority has told the reader nothing.

## Assessment areas

One `h1` per area, each split into **Current State** and **Recommendations**. The reference
uses four, and they are a good default because they cover the ways a platform fails:

- **Architecture** — physical and logical topology, load balancing, HSMs, automation,
  backups, configuration. Ends on **Risks**.
- **Workflows** — how secrets and consumers move through the platform.
- **Operations** — disaster recovery, upgrades, backups, observability.
- **User Experience** — onboarding, self-service, documentation, auditing, governance, and
  what consumers actually say. If consumers were not interviewed, **say so** — the
  reference does, and it is the difference between a finding and an assumption.

**Current State** is descriptive and neutral: what is there, drawn from the workshops, with
diagrams. No judgement. **Recommendations** is where judgement goes, as a table of ID /
Recommendation / Justification, with the justification running to several paragraphs where
the change is significant.

Write Current State so the customer would sign off on it as accurate. If they would argue
with a sentence, it belongs in Recommendations instead.

## Resources

A numbered list of links to the HashiCorp Validated Designs, operating guides and tutorials
the recommendations lean on. Link every recommendation that has a published guide behind
it — it turns "adopt namespaces" into something the customer's team can start on Monday.

## Tone

- Third person, past tense for what happened, present for what is: "HashiCorp was engaged
  to provide…", "The primary cluster resides in…".
- The customer is named in full once, then by short name: *Westpac Banking Corporation,
  commonly referred to as "Westpac"*.
- Spell out an acronym on first use — Performance Replication (PR), Disaster Recovery (DR).
- Prefer the customer's own vocabulary for their zones, teams and systems. Using their
  names for things is what makes the document feel like it was written for them.
- No hedging where you have evidence, and no confidence where you do not. "It should be
  noted that consumers were not directly involved in this engagement" is worth more than a
  confident claim about consumer sentiment.
