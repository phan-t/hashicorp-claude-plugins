#!/usr/bin/env python3
"""Flag AI-slop patterns and the author's own banned patterns in prose.

Usage:
    slop_check.py FILE [FILE ...]
    slop_check.py - < draft.txt
    slop_check.py --profile path/to/profile.md FILE
    slop_check.py --strict FILE     # review hits also fail

Fenced code, inline code and double-quoted phrases are skipped, so identifiers, commands and
words quoted as examples are never flagged.

Levels:
    slop     always fix
    profile  a pattern the author banned in their profile; always fix
    review   a judgement call; fix unless the context earns it

Exits 1 when any slop or profile hit is found (or any hit at all with --strict), so the check
can sit in a script or hook. Standard library only.
"""

import argparse
import os
import re
import sys

DEFAULT_PROFILE = os.path.join("~", ".claude", "writing-style", "profile.md")

# (regex, level, category, suggestion). Matching is case-insensitive unless the regex says
# otherwise with (?-i:...).
BUILTIN = [
    # Vocabulary
    (r"\bdelv(e|es|ed|ing)\b", "slop", "vocabulary", "look at, examine, or state the finding"),
    (r"\b(dive|diving|dives) (deep )?into\b|\bdeep[- ]dive\b", "slop", "vocabulary", "look at, or state the finding"),
    (r"\bleverag(e|es|ed|ing)\b", "slop", "vocabulary", "use"),
    (r"\butili[sz](e|es|ed|ing)\b", "slop", "vocabulary", "use"),
    (r"\bseamless(ly)?\b", "slop", "vocabulary", "say what no longer needs doing by hand"),
    (r"\btapestry\b|\btestament to\b|\bsymphony of\b|\bbeacon of\b", "slop", "vocabulary", "delete the metaphor"),
    (r"\bmyriad\b|\bplethora\b", "slop", "vocabulary", "the number, or 'many'"),
    (r"\bever[- ](evolving|changing)\b|\bfast[- ]paced\b|\brapidly (evolving|changing)\b", "slop", "vocabulary", "delete, or say what changed"),
    (r"\bcutting[- ]edge\b|\bstate[- ]of[- ]the[- ]art\b|\bgame[- ]chang(er|ing)\b", "slop", "vocabulary", "name what is new"),
    (r"\bembark(s|ed|ing)?\b|\bjourney\b", "slop", "vocabulary", "project, migration, rollout"),
    (r"\b(realm|landscape)\b", "review", "vocabulary", "name the actual field or market"),
    (r"\bempower(s|ed|ing)?\b|\bunlock(s|ed|ing)?\b|\belevat(e|es|ed|ing)\b", "slop", "vocabulary", "say what the reader can now do"),
    (r"\bfoster(s|ed|ing)?\b|\bshowcas(e|es|ed|ing)\b|\bunderscor(e|es|ed|ing)\b|\bboasts?\b", "slop", "vocabulary", "build, show, confirm, have"),
    (r"\b(robust|comprehensive|holistic)\b", "review", "vocabulary", "say what it covers or survives"),
    (r"\b(crucial|vital|pivotal)\b", "review", "vocabulary", "say what breaks without it"),
    (r"\bstreamlin(e|es|ed|ing)\b|\bsynerg(y|ies)\b|\bparadigm\b", "slop", "vocabulary", "say what changed, by how much"),
    (r"\bmeticulous(ly)?\b|\bintricate\b|\bnuanced\b", "review", "vocabulary", "say what the care consisted of"),
    (r"\b(serves|stands|acts) as\b", "review", "vocabulary", "is"),
    (r"\bnavigat(e|es|ing) the (complexit|challeng|intricac)", "slop", "vocabulary", "delete"),
    # Stock structures
    (r"(\bnot|n't) (just|only|merely|simply) [^.;:!?]{1,60}?,? (but|it's|it is)\b", "slop", "false contrast", "state the claim directly"),
    (r"\b(isn't|is not|wasn't|was not) about [^.!?]{1,60}[.;] (it's|it is|it was) about\b", "slop", "false contrast", "state the claim directly"),
    (r"\bit'?s (worth noting|important to (note|remember|understand))\b|\bnotably\b|\binterestingly\b", "slop", "signposting", "delete the signpost"),
    (r"(^|[.!?]\s+)(in short|in summary|in conclusion|ultimately|overall|at the end of the day)\b", "slop", "echo", "delete the restatement"),
    (r"\bwhether you'?re (a |an )?", "slop", "opener", "address the actual reader"),
    (r"(^|[.!?]\s+)(?-i:[A-Z])[\w' -]{0,40}, not (a |an |the )?[\w' -]{1,40}\.", "review", "slogan fragment", "make it a sentence with 'rather than'"),
    (r"(?-i:\b[A-Z][a-z]+\. [A-Z][a-z]+\. [A-Z][a-z]+\.)", "slop", "slogan triple", "one sentence that says which, and why"),
    (r"\s—\s|\w—\w", "review", "em dash", "a comma, 'which', 'so' or a full stop"),
    # Chat residue
    (r"\b(certainly|absolutely|great question)!|\bi hope (this|that) helps\b|\blet me know if\b|\bhappy to help\b|\bas an ai\b", "slop", "chat residue", "delete"),
    (r"(^|\n)\s*here'?s (a|an|the|what|how)\b", "review", "chat residue", "lead with the content itself"),
    # Hedging and intensifiers
    (r"\b(could|may|might) (potentially|possibly|perhaps)\b", "slop", "stacked hedge", "one hedge, or a plain claim"),
    (r"\b(very|really|truly|incredibly|extremely)\b", "review", "intensifier", "the number that makes it true"),
    (r"\b(simply|obviously|easily)\b", "review", "condescension", "cut it"),
]

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "via", "with"}


def load_profile_patterns(path):
    """Return (regex, suggestion) pairs from the profile's ```patterns block."""
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    block = re.search(r"^```patterns\s*\n(.*?)^```", text, re.S | re.M)
    if not block:
        return []
    pairs = []
    for raw in block.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        regex, _, hint = line.partition(" => ")
        try:
            pairs.append((re.compile(regex.strip(), re.I), hint.strip() or "banned in profile"))
        except re.error as e:
            print(f"warning: bad profile pattern {regex!r}: {e}", file=sys.stderr)
    return pairs


def mask_code(text):
    """Blank out fenced code, inline code and quoted phrases, keeping line and column positions intact."""
    out, in_fence, fence = [], False, ""
    for line in text.split("\n"):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in ("```", "~~~") and (not in_fence or marker == fence):
            in_fence, fence = (not in_fence), marker
            out.append(" " * len(line))
        elif in_fence:
            out.append(" " * len(line))
        else:
            line = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), line)
            # A quoted phrase is a mention rather than a use ("don't say leverage").
            out.append(re.sub(r'"[^"\n]{1,80}"|\u201c[^\u201d\n]{1,80}\u201d', lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


def is_title_case(heading):
    words = [w for w in re.findall(r"[A-Za-z][\w'-]*", heading)]
    content = [w for w in words[1:] if w.lower() not in SMALL and len(w) > 3]
    return len(content) >= 2 and all(w[0].isupper() for w in content) and not all(w.isupper() for w in content)


def check(text, profile_patterns):
    masked = mask_code(text)
    lines = masked.split("\n")
    starts, pos = [], 0
    for line in lines:
        starts.append(pos)
        pos += len(line) + 1

    def locate(offset):
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1, offset - starts[lo] + 1

    hits = []
    rules = [(re.compile(r, re.I), lvl, cat, hint) for r, lvl, cat, hint in BUILTIN]
    rules += [(rx, "profile", "profile", hint) for rx, hint in profile_patterns]
    for rx, level, category, hint in rules:
        for m in rx.finditer(masked):
            start = m.start() + (len(m.group(0)) - len(m.group(0).lstrip(" \n.!?")))
            ln, col = locate(start)
            hits.append((ln, col, level, category, m.group(0).strip(" \n.!?"), hint))

    for i, line in enumerate(lines, 1):
        if EMOJI.search(line):
            hits.append((i, EMOJI.search(line).start() + 1, "review", "emoji", EMOJI.search(line).group(0), "remove"))
        h = HEADING.match(line)
        if h and is_title_case(h.group(1)):
            hits.append((i, 1, "review", "title case", h.group(1), "sentence case"))
    hits.sort()
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="files to check, or - for stdin")
    ap.add_argument("--profile", default=os.environ.get("WRITING_STYLE_PROFILE", DEFAULT_PROFILE))
    ap.add_argument("--no-profile", action="store_true", help="built-in patterns only")
    ap.add_argument("--strict", action="store_true", help="review hits also fail")
    args = ap.parse_args()

    profile_patterns = [] if args.no_profile else load_profile_patterns(args.profile)
    counts = {"slop": 0, "profile": 0, "review": 0}
    for path in args.files:
        if path == "-":
            name, text = "<stdin>", sys.stdin.read()
        else:
            name = path
            with open(path, encoding="utf-8") as f:
                text = f.read()
        for ln, col, level, category, match, hint in check(text, profile_patterns):
            counts[level] += 1
            print(f'{name}:{ln}:{col}: {level:<7} [{category}] "{match}" -> {hint}')

    total = sum(counts.values())
    print(f"\n{counts['slop']} slop, {counts['profile']} profile, {counts['review']} review"
          + ("" if profile_patterns or args.no_profile else " (no profile patterns loaded)"),
          file=sys.stderr)
    failing = total if args.strict else counts["slop"] + counts["profile"]
    sys.exit(1 if failing else 0)


if __name__ == "__main__":
    main()
