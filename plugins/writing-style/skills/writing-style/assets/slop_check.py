#!/usr/bin/env python3
"""Flag AI-slop patterns and the author's own banned patterns in prose.

Usage:
    slop_check.py FILE [FILE ...]
    slop_check.py - < draft.txt
    slop_check.py --profile path/to/profile.md FILE
    slop_check.py --strict FILE     # review hits also fail
    slop_check.py report.docx       # Word files are read directly

Fenced code, inline code and double-quoted phrases are skipped, so identifiers, commands and
words quoted as examples are never flagged.

A .docx is read from its body, footnotes and endnotes, with each paragraph and table cell
becoming one line. Hits are located as ¶N (the Nth paragraph with text) or "footnote N".
Deleted tracked changes are skipped, runs in a code style or a monospace font are treated as
inline code, and code paragraphs and table-of-contents lines are not checked. Headers, footers,
comments and text boxes are not read.

Two checks read the document's structure rather than single sentences. The first flags the
paragraph after a table or figure when it opens like a summary or repeats two or more of the
table's measurements. The second flags a phrase of four or more words used in four or more
paragraphs, ignoring headings and table cells. Both are review hits.

The summary line counts "rather than", which reads well once and becomes a tell when it recurs.

Levels:
    slop     always fix
    profile  a pattern the author banned in their profile; always fix
    review   a judgement call; fix unless the context earns it

Exits 1 when any slop or profile hit is found (or any hit at all with --strict), so the check
can sit in a script or hook, and 2 when a file cannot be read. Standard library only.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

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
    (r"\bfoster(s|ed|ing)?\b|\bshowcas(e|es|ed|ing)\b|\bboasts?\b", "slop", "vocabulary", "build, show, confirm, have"),
    # The verb only, told apart by what follows it: "underscores the need" against "contain underscores".
    (r"(?<!\ban )(?<!\bthe )(?<!\ba )\bunderscor(e|es|ed|ing)\b"
     r"(?= (the|that|how|why|what|its|this|our|their|a|an|by|just|again|both|rather|once)\b)",
     "slop", "vocabulary", "show, confirm"),
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
    (r"\b(doesn't|don't|does not|do not|didn't|did not) support the (reasoning|idea|view|assumption|claim|notion|hypothesis) that\b",
     "review", "strawman", "state what the results showed, unless someone really held the view"),
    (r"\bcontrary to (popular|common)\b|\bcommon misconception\b", "slop", "strawman", "state the finding"),
    (r"\bwhether you'?re (a |an )?", "slop", "opener", "address the actual reader"),
    (r"(^|[.!?]\s+)(and it'?s (only )?getting (harder|worse)|here'?s the thing|the (reality|truth) is|"
     r"make no mistake|let'?s be (clear|honest)|the bottom line is)\b", "slop", "stock opener", "start with the point"),
    (r"(^|[.!?]\s+)(?-i:[A-Z])[\w' -]{0,40}, not (a |an |the )?[\w' -]{1,40}\.", "review", "slogan fragment", "make it a sentence with 'rather than'"),
    (r"(?-i:\b[A-Z][a-z]+\. [A-Z][a-z]+\. [A-Z][a-z]+\.)", "slop", "slogan triple", "one sentence that says which, and why"),
    (r"\s—\s|\w—\w", "review", "em dash", "a comma, 'which', 'so' or a full stop"),
    # Chat residue
    (r"\b(certainly|absolutely|great question)!|\bi hope (this|that) helps\b|\blet me know if\b|\bhappy to help\b|\bas an ai\b", "slop", "chat residue", "delete"),
    (r"(^|\n)\s*here'?s (a|an|the|what|how)\b", "review", "chat residue", "lead with the content itself"),
    # Hedging and intensifiers
    (r"\b(could|may|might) (potentially|possibly|perhaps)\b", "slop", "stacked hedge", "one hedge, or a plain claim"),
    (r"\b(very|really|truly|incredibly|extremely)\b", "review", "intensifier", "the number that makes it true"),
    (r"\b(effectively|essentially|arguably|virtually)\b", "review", "hedge adverb", "the number or fact it stands in for"),
    (r"\b(simply|obviously|easily)\b", "review", "condescension", "cut it"),
]

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CODE_STYLES = {"code", "htmlcode", "verbatimchar", "sourcecode", "inlinecode"}
# Paragraph styles that hold code, or text generated from elsewhere in the document.
UNCHECKED_PARA_STYLE = re.compile(r"code|codeblock|sourcecode|htmlpreformatted|plaintext|macrotext"
                                  r"|toc ?\d|tableoffigures")
MONO_FONTS = {"consolas", "courier", "courier new", "menlo", "monaco", "sf mono", "space mono",
              "jetbrains mono", "ibm plex mono", "source code pro", "lucida console"}
# Subtrees whose text is not the document's current prose.
SKIP = {W + t for t in ("del", "moveFrom", "txbxContent", "pPr", "rPr", "instrText", "delInstrText")}
# The paragraph after a table or figure restates it when it opens like a summary, or when it
# repeats two or more of the table's measurements.
SUMMARY_OPENER = re.compile(r"\s*(?:[-*]\s+)?(this|these|the (table|figure|chart|graph|data|numbers|results?)"
                            r"|comparing|compared|against the|as (shown|seen|the (table|figure|chart)))\b", re.I)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
CAPTION = re.compile(r"\s*[*_]*(table|figure|fig\.) \d", re.I)
LIST_MARKER = re.compile(r"\s*([-*+]|\d+[.)])\s+")
WORD = re.compile(r"[a-z0-9][a-z0-9'-]*", re.I)
# A phrase this long, used in this many paragraphs, reads as pasted.
PHRASE_WORDS, PHRASE_PARAGRAPHS = 4, 4
STOPWORDS = set("""a about after all also an and any are as at be because been before but by can could
did do does each for from had has have he her his how i if in into is it its may more most no not of
on one only or other our out over she should so some such than that the their them then there these
they this those to under up was we were what when where which while who will with would you your""".split())
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "via", "with"}


def load_profile_patterns(path):
    """Return (regex, level, suggestion) triples from the profile's ```patterns block.

    A line is `regex => suggestion`, reported at the profile level. A line that starts with
    `review: ` is reported at the review level instead, for a rule a regex can only
    approximate.
    """
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
        level = "profile"
        if line.startswith("review: "):
            level, line = "review", line[len("review: "):]
        regex, _, hint = line.partition(" => ")
        try:
            pairs.append((re.compile(regex.strip(), re.I), level, hint.strip() or "banned in profile"))
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


def _run_is_code(run):
    rpr = run.find(W + "rPr")
    if rpr is None:
        return False
    style = rpr.find(W + "rStyle")
    if style is not None and style.get(W + "val", "").lower() in CODE_STYLES:
        return True
    fonts = rpr.find(W + "rFonts")
    return fonts is not None and any(
        (fonts.get(W + a) or "").lower() in MONO_FONTS for a in ("ascii", "hAnsi"))


def _para_text(p):
    """A paragraph's current text, with code runs blanked to spaces so columns stay exact."""
    segments = []  # [text, is_code], merged as runs are added

    def add(text, code):
        if not text:
            return
        if segments and segments[-1][1] == code:
            segments[-1][0] += text
        else:
            segments.append([text, code])

    def walk(el):
        for child in el:
            if child.tag in SKIP:
                continue
            if child.tag == W + "r":
                code = _run_is_code(child)
                for part in child:
                    if part.tag == W + "t":
                        add(part.text or "", code)
                    elif part.tag in (W + "tab", W + "br", W + "cr"):
                        add(" ", code)
                    elif part.tag == W + "noBreakHyphen":
                        add("-", code)
            else:
                walk(child)  # hyperlinks, fields, inserted text, content controls

    walk(p)
    return "".join(" " * len(t) if code else t for t, code in segments)


def _paragraphs(el, table=None, tables=None):
    """Every paragraph under el in reading order, with the number of the top-level table it is in."""
    tables = tables if tables is not None else [0]
    for child in el:
        if child.tag == W + "p":
            yield child, table
        elif child.tag not in SKIP:
            inner = table
            if child.tag == W + "tbl" and table is None:
                tables[0] += 1
                inner = tables[0]
            yield from _paragraphs(child, inner, tables)


def _para_style(p):
    style = p.find(f"{W}pPr/{W}pStyle")
    return (style.get(W + "val", "") if style is not None else "").lower()


def _heading_prefix(style):
    m = re.fullmatch(r"heading ?([1-6])", style)
    return "#" * int(m.group(1)) + " " if m else ""


def _has_text(p):
    return any((t.text or "").strip() for t in p.iter(W + "t"))


def read_docx(path):
    """Return (text, locations, kinds) for a .docx.

    locations[i] is (label, column offset) for line i+1, and kinds[i] is what that line is, as
    classify() describes. Each paragraph is one line, so each line is its own paragraph.
    """
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            parts = {n: z.read(n) for n in ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")
                     if n in names}
    except zipfile.BadZipFile:
        raise ValueError(f"{path}: not a Word file (it is not a zip archive)")
    if "word/document.xml" not in parts:
        raise ValueError(f"{path}: not a Word file (no word/document.xml)")

    lines, locations, kinds = [], [], []
    body = ET.fromstring(parts["word/document.xml"]).find(W + "body")
    count = 0
    for p, table in _paragraphs(body):
        # Count from the raw text, so a paragraph of code still takes a number.
        if not _has_text(p):
            if next(p.iter(W + "drawing"), None) is not None or next(p.iter(W + "pict"), None) is not None:
                lines.append("")
                locations.append(("figure", 0))
                kinds.append(("figure", None))
            continue
        count += 1
        style = _para_style(p)
        if UNCHECKED_PARA_STYLE.fullmatch(style):
            continue
        prefix = _heading_prefix(style)
        lines.append(prefix + _para_text(p))
        locations.append((f"\u00b6{count}", len(prefix)))
        kind = "cell" if table else "heading" if prefix else "caption" if style == "caption" else "prose"
        kinds.append((kind, table))

    for kind in ("footnote", "endnote"):
        part = parts.get(f"word/{kind}s.xml")
        if part is None:
            continue
        # Word numbers notes by the order they are referenced, which need not match their ids.
        shown = {}
        for ref in body.iter(f"{W}{kind}Reference"):
            shown.setdefault(ref.get(W + "id"), len(shown) + 1)
        for note in ET.fromstring(part).findall(W + kind):
            if note.get(W + "type") in ("separator", "continuationSeparator", "continuationNotice"):
                continue
            label = f"{kind} {shown.get(note.get(W + 'id'), note.get(W + 'id'))}"
            for p, _ in _paragraphs(note):
                if _has_text(p) and not UNCHECKED_PARA_STYLE.fullmatch(_para_style(p)):
                    lines.append(_para_text(p))
                    locations.append((label, 0))
                    kinds.append(("note", None))
    return "\n".join(lines), locations, kinds


def classify(lines):
    """Describe each Markdown or plain-text line as (kind, table number).

    Kinds are prose, heading, cell (a table row), figure (an image), caption and blank. Each run
    of table rows is one table. Word files get the same description from read_docx().
    """
    kinds, table, in_table = [], 0, False
    for line in lines:
        stripped = line.strip()
        is_row = stripped.startswith("|")
        if is_row and not in_table:
            table += 1
        in_table = is_row
        if is_row:
            kinds.append(("cell", table))
        elif not stripped:
            kinds.append(("blank", None))
        elif HEADING.match(line):
            kinds.append(("heading", None))
        elif stripped.startswith("!["):
            kinds.append(("figure", None))
        elif CAPTION.match(line):
            kinds.append(("caption", None))
        else:
            kinds.append(("prose", None))
    return kinds


def _paragraph_spans(lines, kinds, docx):
    """Group prose lines into paragraphs, as lists of line indices."""
    spans, current = [], []
    for i, (kind, _) in enumerate(kinds):
        prose = kind in ("prose", "note")
        if not prose or docx or LIST_MARKER.match(lines[i]):
            if current:
                spans.append(current)
            current = []
        if prose:
            current.append(i)
    if current:
        spans.append(current)
    return spans


def _measurements(text):
    """The numbers in text that look like results: percentages, decimals and 3+ digit values."""
    found = set()
    for m in NUMBER.finditer(text):
        raw = m.group(0).rstrip(",")
        digits = raw.replace(",", "").rstrip("%")
        if "%" in raw or "." in digits or len(digits) >= 3:
            found.add(digits)
    return found


def table_echoes(lines, kinds, spans):
    """Review hits for a paragraph that follows a table or figure and restates it."""
    hits = []
    starts = {span[0]: span for span in spans}
    i = 0
    while i < len(kinds):
        kind, table = kinds[i]
        if kind not in ("cell", "figure"):
            i += 1
            continue
        end = i
        while end + 1 < len(kinds) and kinds[end + 1][0] == kind and kinds[end + 1][1] == table:
            end += 1
        shown = _measurements(" ".join(lines[i:end + 1])) if kind == "cell" else set()
        nxt = end + 1
        while nxt < len(kinds) and kinds[nxt][0] in ("blank", "caption"):
            nxt += 1
        if nxt in starts:
            span = starts[nxt]
            text = " ".join(lines[j].strip() for j in span)
            repeated = shown & _measurements(text)
            if SUMMARY_OPENER.match(lines[nxt]) or len(repeated) >= 2:
                col = len(lines[nxt]) - len(lines[nxt].lstrip()) + 1
                snippet = text if len(text) <= 60 else text[:60].rsplit(" ", 1)[0] + "..."
                hits.append((nxt + 1, col, "review", "table echo", snippet,
                             f"say what the {'table' if kind == 'cell' else 'figure'} does not: the cause, "
                             "the exception or the decision"))
        i = end + 1
    return hits


def repeated_phrases(lines, spans):
    """Review hits for each use of a phrase of PHRASE_WORDS+ words found in PHRASE_PARAGRAPHS+ paragraphs."""
    # Words per paragraph, as (word, line, column, starts_run). A run breaks at sentence
    # punctuation and at masked code, so a phrase never spans either.
    paragraphs = []
    for span in spans:
        words, gap = [], ""
        for j in span:
            line = lines[j]
            marker = LIST_MARKER.match(line)
            pos = marker.end() if marker else 0
            gap += " "
            for m in WORD.finditer(line, pos):
                gap += line[pos:m.start()]
                breaks = bool(re.search(r"[.!?;:()\[\]|\"]", gap)) or "  " in gap.strip("\n")
                words.append((m.group(0).lower(), j, m.start() + 1, breaks or not words))
                pos, gap = m.end(), ""
            gap = line[pos:]
        paragraphs.append(words)

    def grams(words):
        for k in range(len(words) - PHRASE_WORDS + 1):
            window = words[k:k + PHRASE_WORDS]
            if not any(w[3] for w in window[1:]):
                yield k, tuple(w[0] for w in window)

    def has_content(key):
        return sum(w in STOPWORDS for w in key) < PHRASE_WORDS - 1

    seen = {}
    for n, words in enumerate(paragraphs):
        for _, key in grams(words):
            seen.setdefault(key, set()).add(n)
    hot = {key: len(ps) for key, ps in seen.items() if len(ps) >= PHRASE_PARAGRAPHS}

    hits = []
    for words in paragraphs:
        # Overlapping repeated windows merge into one phrase, which is reported if any of its
        # windows carries content words, so "at the end of" alone never counts.
        runs, run = [], None
        for k, key in grams(words):
            if key not in hot:
                continue
            if run and k <= run[1]:
                run = [run[0], k + PHRASE_WORDS - 1, max(run[2], hot[key]), run[3] or has_content(key)]
            else:
                if run:
                    runs.append(run)
                run = [k, k + PHRASE_WORDS - 1, hot[key], has_content(key)]
        if run:
            runs.append(run)
        for a, b, uses, content in runs:
            if not content:
                continue
            phrase = " ".join(w[0] for w in words[a:b + 1])
            hits.append((words[a][1] + 1, words[a][2], "review", "repetition", phrase,
                         f"used in {uses} paragraphs; keep it where it matters most"))
    return hits


def is_title_case(heading):
    words = [w for w in re.findall(r"[A-Za-z][\w'-]*", heading)]
    content = [w for w in words[1:] if w.lower() not in SMALL and len(w) > 3]
    return len(content) >= 2 and all(w[0].isupper() for w in content) and not all(w.isupper() for w in content)


def check(text, profile_patterns, kinds=None):
    """Return hits as (line, column, level, category, match, suggestion).

    kinds describes each line, as read_docx() returns it; without it the text is read as
    Markdown or plain text.
    """
    # Curly apostrophes and non-breaking spaces, as Word types them, would slip past patterns
    # such as "it's" and "dive into". Each swap is one character for one, so columns hold.
    masked = mask_code(text)
    for typed, plain in (("\u2019", "'"), ("\u2018", "'"), ("\u00a0", " "), ("\u202f", " ")):
        masked = masked.replace(typed, plain)
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
    rules = [(re.compile(r, re.I | re.M), lvl, cat, hint) for r, lvl, cat, hint in BUILTIN]
    rules += [(rx, level, "profile", hint) for rx, level, hint in profile_patterns]
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

    docx = kinds is not None
    kinds = kinds if docx else classify(lines)
    spans = _paragraph_spans(lines, kinds, docx)
    hits += table_echoes(lines, kinds, spans)
    hits += repeated_phrases(lines, spans)
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
    rather_than = words = 0
    unreadable = False
    for path in args.files:
        locations = kinds = None
        if path == "-":
            name, text = "<stdin>", sys.stdin.read()
        elif path.lower().endswith((".docx", ".docm", ".dotx")):
            name = path
            try:
                text, locations, kinds = read_docx(path)
            except (ValueError, ET.ParseError, OSError) as e:
                print(f"error: {e}", file=sys.stderr)
                unreadable = True
                continue
        else:
            name = path
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                print(f"error: {path}: not UTF-8 text (a .doc must be saved as .docx first)", file=sys.stderr)
                unreadable = True
                continue
            except OSError as e:
                print(f"error: {e}", file=sys.stderr)
                unreadable = True
                continue
        prose = mask_code(text)
        rather_than += len(re.findall(r"\brather than\b", prose, re.I))
        words += len(re.findall(r"[A-Za-z0-9][\w'\u2019-]*", prose))
        for ln, col, level, category, match, hint in check(text, profile_patterns, kinds):
            counts[level] += 1
            if locations:
                label, offset = locations[ln - 1]
                where = f"{label}:{max(col - offset, 1)}"
            else:
                where = f"{ln}:{col}"
            print(f'{name}:{where}: {level:<7} [{category}] "{match}" -> {hint}')

    total = sum(counts.values())
    # "rather than" is fine once and a tell when it recurs, so it is counted for the author to judge.
    print(f"\n{counts['slop']} slop, {counts['profile']} profile, {counts['review']} review"
          + f'; "rather than" x{rather_than} in {words:,} words'
          + ("" if profile_patterns or args.no_profile else " (no profile patterns loaded)"),
          file=sys.stderr)
    failing = total if args.strict else counts["slop"] + counts["profile"]
    sys.exit(2 if unreadable else 1 if failing else 0)


if __name__ == "__main__":
    main()
