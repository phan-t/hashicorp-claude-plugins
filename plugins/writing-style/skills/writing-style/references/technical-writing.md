# Technical writing baseline

The craft the profile builds on. Where the profile says otherwise, the profile wins.

## Know the reader and what they will do next

Before writing, name the reader and the action the text should leave them able to take: approve
a change, run a command, choose an option or trust a finding. Cut whatever does not serve that
action.

## Lead with the point

Put the conclusion, decision or instruction first, then the reasoning. A reader who stops after
one sentence should still leave with the right idea. A commit subject, a section's first
sentence and an email's opening line all do this job.

## Be specific

- Use numbers with units and a source: "21 MB to 144 KB" rather than "much smaller".
- Name things: the file, the function, the setting, the team.
- Give the cause. "So", "because" and "which means" carry more than any adjective.
- State the limits. Say what was not tested, what is assumed and what would change the answer.

## Say how it was checked

A claim about behaviour is stronger with the check that established it: what was run, what it
showed and what it caught. If the obvious check would mislead, say why.

## Plain words, short paths

- Prefer the common word: use, help, start, show, need, about.
- Prefer the active voice when the actor matters. "Word substitutes Calibri" says who did it,
  where "Calibri is substituted" hides the culprit.
- Keep one idea per sentence where you can, but do not chop reasoning into fragments to get
  there. A long sentence with a clear spine reads faster than four short ones that have lost
  their connections.
- Use the same term for the same thing throughout. Do not vary terms for elegance.

## Structure for the reading, not the look

- Prose for arguments and explanations, since bullets drop the "because" between ideas.
- Bullets for parallel items a reader will scan or tick off.
- Numbered steps for procedures, with one action per step and the expected result after it.
- Tables for comparisons across the same attributes.
- Headings in sentence case, written as the thing the section tells you rather than a label.

## Instructions

- Imperative mood: "Run", "Set", "Open".
- Put the condition before the action: "If the build fails, re-run with `--verbose`."
- Show the exact command or value in code formatting and say what success looks like.

## Edit by cutting

Read the draft once for each of these:

1. Delete every sentence the reader would not miss.
2. Replace every vague word with the specific fact behind it.
3. Check each paragraph's first sentence carries its point.
4. Read it aloud. Anything you would not say to a colleague goes.
