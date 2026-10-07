---
name: writing-style
description: Write, edit and review prose in Tony's own voice, as a technical writer would, with no AI slop. Use this skill whenever you are about to write prose someone will read, such as a README, docs, a commit message, a PR description, a design or decision paper, a report section, an email, a Slack message or a customer deliverable, and whenever the user asks to tighten, rewrite, de-slop, proofread or "make this sound like me". Also use it to learn: when the user edits a draft you wrote, corrects a word or phrase, says "I'd never say that", or points you at their own writing to study, update the style profile so the correction sticks. Not for code, only for the prose around it.
---

# Writing style

This skill writes in one person's voice and gets closer to it over time. It has three parts:

- **The profile** at `~/.claude/writing-style/profile.md`. It holds the author's own rules, each
  with the evidence it came from. It lives outside the plugin so that plugin updates never
  overwrite what has been learned. **The profile outranks everything in this skill.**
- **The references** in this skill: `references/ai-slop.md` lists the patterns that make text read
  as machine-written, and `references/technical-writing.md` sets the baseline craft.
- **The checker**, `assets/slop_check.py`, which enforces both lists mechanically, along with
  any patterns the profile bans.

## Before writing anything

1. **Load the profile.** Read `~/.claude/writing-style/profile.md`. If it does not exist, create
   the directory and copy `references/seed-profile.md` into it, then tell the user it was created
   and where.
2. **Read `references/ai-slop.md`** the first time this skill loads in a session. Read
   `references/technical-writing.md` when the piece is longer than a few paragraphs or is
   documentation.

## Writing

Apply the profile first, then the technical-writing baseline, then the slop list. Where they
conflict, the profile wins, because it records what the author actually chose.

Write the piece the way the author would and do not write a draft to fix later. Most slop gets in
through filler, so the fastest route to clean prose is having something specific to say in
each sentence: a number, a name, a cause or a consequence.

## Checking

Run the checker over every piece of prose before handing it over:

```
python3 assets/slop_check.py <file> [<file> ...]
python3 assets/slop_check.py - < draft.txt
```

For text that is going into chat, a commit message or a tool rather than a file, write it to a
scratch file first and check that. The checker skips fenced code, inline code and double-quoted phrases, and it reads
the profile's banned patterns automatically (`--profile` overrides the path).

- **`slop` hits** are fixed, every time.
- **`review` hits** are judgement calls. Fix them unless the context earns the word, such as
  "robust" in a statistics paper.
- **Rewrite the sentence rather than swapping the word.** Replacing "leverage" with "use" in a
  sentence that says nothing still leaves a sentence that says nothing. If a fix makes the
  sentence worse, the sentence was the problem.

Do not mention the checker or the profile in the prose itself. Report to the user only if
something needs their decision.

## Learning

The profile grows from evidence the author supplies, never from text Claude wrote. Read
`references/learning.md` whenever one of these happens:

- The user edits text you wrote. Diff their version against yours.
- The user corrects a word, phrase or habit ("don't say X", "too formal", "I'd never write that").
- The user asks you to study their writing, whether it is a file, a folder, a doc or a git range.
- The user says a rule is wrong, or a rule in the profile contradicts what they just did.

Record what was learned in the profile in the same turn, then tell the user in one line what
changed, for example: `Learned: "rather than" over "X, not Y" fragments (2nd sighting, now firm).`

## Commands

When invoked directly, the argument picks the mode:

| Invocation | What it does |
|---|---|
| `/writing-style` or `/writing-style write …` | Write the requested piece in the author's voice. |
| `/writing-style check <path>` | Run the checker and rewrite the flagged passages, showing before and after. |
| `/writing-style learn <path, glob or git range>` | Study the author's own text and propose profile rules. Read `references/learning.md`. |
| `/writing-style profile` | Show the profile's rules, grouped as firm and tentative. |
| `/writing-style forget <rule id>` | Move a rule to Retired, with the user's reason. |
