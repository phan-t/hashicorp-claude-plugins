# Learning the author's style

The profile at `~/.claude/writing-style/profile.md` is how this skill improves. It only works if
every rule in it comes from something the author actually did, so this file is strict about
where evidence comes from.

## What counts as evidence

- **Edits to your drafts.** This is the strongest signal, because each change is a choice the
  author made against an alternative they saw.
- **Explicit corrections in chat**, such as "don't use leverage", "too formal" or
  "I write colour, not color".
- **Text the author wrote themselves**, such as documents, messages and their own edits in git.

What does not count:

- Text Claude wrote, even if the author approved it. Approval means it was acceptable, which is
  weaker than meaning it was chosen. In git, check whether a commit carries a `Claude-Session`
  or `Co-Authored-By: Claude` trailer before treating its message as the author's. The exception
  is a later diff in which the author edited Claude's text, because that edit is evidence.
- Text by other people, unless the author says to adopt it.
- One-off choices forced by the context, such as a customer's required terminology.

## Learning from an edit

1. Diff your version against theirs at the sentence level.
2. For each change, name the general rule rather than the instance.
   "Changed 'leverage' to 'use'" is an instance. "Prefers the plain verb to the business verb"
   is the rule, and it also tells you what to do with "utilise".
3. Ignore changes that are only about content (a fact corrected, a section added). They teach
   nothing about style.
4. If one edit could support two different rules, record the narrower one.

## Learning from a corpus

For `/writing-style learn <path, glob or git range>`:

1. Collect the author's text and leave out code, quotations and Claude-authored material.
   For a git range, `git log -p --author=<them>` shows their own edits, and edits to prose are
   worth more than new prose.
2. Look for choices that recur: spelling, punctuation (Oxford comma, dashes, semicolons),
   sentence length, how they open and close, how they hedge, headings, lists versus prose, and
   words they use often or never.
3. Propose rules to the user as a short list with one quoted example each, and add only the ones
   they accept.

## Writing a rule into the profile

Add it under `## Rules` with the next free id:

```
### R9. <the rule as an instruction> · tentative
<one or two lines on how to apply it, and the exceptions>
- Evidence (<source>, <date or commit>): "<before>" became "<after>"
```

- **Tentative** means one sighting. Apply it, but do not contort a sentence to obey it.
- **Firm** means two or more independent sightings, or the author stated it outright. When a
  tentative rule is seen again, add the evidence line and change the label.
- If the rule can be caught by a regular expression, also add a line to the `patterns` block,
  as `regex => suggestion (R9)`. Test the pattern against the evidence before saving it, and
  make sure it does not hit ordinary prose that obeys the rule.
- Update the `Last updated` date.

## When the author contradicts a rule

The newest evidence wins. Move the old rule to `## Retired` with the date and the reason, and
remove its pattern line. Do not delete it, because a retired rule stops the same mistake being
relearned from old text.

If the contradiction might be about context rather than preference, such as formal customer
writing compared with Slack, ask once and split the rule by context rather than retiring it.

## Keeping the profile usable

- Keep it under about 150 lines. When it grows past that, merge rules that say the same thing
  and keep the two strongest evidence lines for each.
- Do not record anything already in `ai-slop.md` or `technical-writing.md` unless the author's
  rule differs from it.
- Never put customer names, confidential figures or private content in evidence lines. Paraphrase
  the example or swap in a placeholder.
