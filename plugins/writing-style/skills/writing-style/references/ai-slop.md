# AI slop

These are the patterns that make a reader decide, often within a sentence, that nobody really
wrote the text. Each one is cheap to produce and says less than it seems to. `slop_check.py`
catches the mechanical ones, and the rest need reading.

## Why it matters

Slop costs trust rather than style points. Once a reader spots it they stop reading carefully
and start skimming for the one sentence with content in it. In a customer deliverable it makes
the work look generated, whether or not it was.

## Vocabulary

Words that are rarely wrong in themselves but appear far more often in generated text than in
anything a person writes. Use the plain word, or better, the specific fact.

| Instead of | Write |
|---|---|
| delve into, dive into, deep dive | look at, examine, or just say what you found |
| leverage, utilise, harness | use |
| robust, comprehensive, holistic | say what it covers or survives |
| seamless, seamlessly | say what no longer needs doing by hand |
| streamline, optimise (vaguely) | say what got faster, by how much |
| empower, enable, unlock, elevate | say what the reader can now do |
| crucial, vital, pivotal, key (as an adjective) | say what breaks without it |
| landscape, realm, ecosystem, space (figurative) | name the actual market, field, or set of tools |
| journey, embark | project, migration, rollout |
| tapestry, testament to, symphony, beacon | delete the metaphor |
| foster, showcase, underscore, boast | build, show, confirm, have |
| myriad, plethora, a wide range of | the number, or "many" |
| ever-evolving, fast-paced, rapidly changing | delete, or say what changed and when |
| cutting-edge, state-of-the-art, game-changer | delete, or name what is new |
| meticulous, intricate, nuanced | say what the care consisted of |

## Stock structures

- **The false contrast.** "It's not just X, it's Y." "Not only X but also Y." "This isn't
  about X. It's about Y." These set up a claim nobody made in order to knock it down.
- **Arguing against a view nobody stated.** "These results don't support the reasoning that
  more voters slow writes" refutes a position the reader never saw. Say what the results showed:
  "The voter count made no measurable difference to write performance." If the customer did
  hold the view, name them and the view before answering it.
- **The slogan fragment.** "Fast. Reliable. Secure." "A document, not a deck." Fold it into a
  sentence that has a subject and a reason.
- **The reflexive triple.** Three adjectives or three parallel clauses because three sounds
  finished. Keep the ones that are true and specific, which is often one.
- **The em dash bolt-on.** "…the deployment model — simple, repeatable and auditable." The dash
  attaches a fragment that should either be its own sentence or be cut.
- **The balanced pair.** Two clauses built to mirror each other: "Vault fixes the
  credential. Boundary fixes the path." "The controller decides, workers act." The symmetry is
  doing the work the facts should do. Say what each part does in whatever shape is true.
- **The stock opener.** "And it's getting harder." "Here's the thing." "The reality is…" A
  sentence that builds drama before the point. Start with the point.
- **The slogan label.** A card title or phase name written as a tagline: "Nothing hidden",
  "Every zone, every actor", "The pain" and "The benefit". Name the literal thing.
- **The signposted point.** "It's worth noting that", "It's important to remember", "Notably",
  "Interestingly". If it were not worth noting it would not be in the text.
- **The topic-sentence echo.** A closing line that restates the paragraph: "In short…",
  "Ultimately…", "Overall…", "In conclusion…". The same goes for the paragraph after a table or
  figure that reads the numbers back ("Against the agreed criteria, success was 100% in the soak
  and both bursts"). Use that paragraph for what the table cannot show: why a run failed, which
  result matters most or what the reader should decide.
- **The repeated caveat.** One qualifying sentence pasted into every section that needs it. Say
  it once where it matters most and refer back to it, or cut it.
- **The bold-label bullet.** Every bullet starting with a bolded label and a colon, used to make
  a list look structured. Use it only when readers will scan the labels, as in a reference
  table.
- **The "whether you're" opener.** "Whether you're a seasoned engineer or just starting out…"
- **The rhetorical question heading.** "So what does this mean for you?"
- **Serves as, stands as, acts as.** Write "is".

## Chat residue

Text that belongs to a conversation with an assistant and leaks into the artefact: "Certainly!",
"Great question", "I hope this helps", "Let me know if you'd like", "Here's a…", "Happy to help",
"As an AI". It must never appear in a deliverable.

## Hedging and intensifiers

- Stacked hedges ("could potentially", "may possibly", "might perhaps") mean one hedge or a
  plain claim. If you are unsure, say what you are unsure of and why.
- Hedge adverbs ("effectively", "essentially", "arguably", "virtually") soften a claim the
  writer could have measured. "Effectively none of the 100,000 cached certificates was
  re-issued" hid a count the results had, so give the count.
- Intensifiers ("very", "really", "truly", "incredibly", "extremely", "highly") usually weaken
  the claim. Replace with the number that makes it true.
- "Simply", "just", "easily" and "obviously" in instructions tell a reader who is stuck that the
  step was meant to be easy. Cut them.

## Formatting tells

- Title Case Headings, where the author writes sentence case.
- Emoji as bullet markers or in headings.
- A heading over every two sentences, or bullets for content that is an argument.
- Bold scattered across a paragraph for emphasis. Bold the one thing a skimmer must not miss.
