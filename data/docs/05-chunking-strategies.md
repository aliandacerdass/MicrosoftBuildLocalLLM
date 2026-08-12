# Chunking Documents for Retrieval

Chunking is splitting documents into the passages that get embedded and retrieved. It is the
least glamorous part of a RAG system and the one that most often decides whether it works.

> Our own notes, based on building and tuning this project.

## Why not embed whole documents

An embedding is a single vector, so embedding a 3000-word document compresses every topic in
it into one point. That point sits in the average of all those meanings and is strongly
similar to nothing in particular. Retrieval becomes vague, and the passage you hand the
model is mostly irrelevant text that costs inference time.

The opposite extreme — one sentence per chunk — fails differently: a sentence pulled out of
its section often does not contain enough context to answer anything.

## The size trade-off

A chunk should be **large enough to answer a question on its own** and **small enough to be
about one thing**.

| Chunk size | Effect |
|---|---|
| Too small (a sentence) | Precise retrieval, but the passage lacks the surrounding explanation |
| Well-sized (1–3 paragraphs) | Usually one topic, usually self-contained |
| Too large (a whole document) | Blurred vector, weak matching, slow generation |

This project targets roughly 800 characters per chunk, which is about two to three
paragraphs of technical prose.

## Heading-aware splitting

Splitting every N characters is easy and bad: it cuts sentences in half and merges the end
of one topic with the start of the next.

Markdown gives you the structure for free. An author who wrote `## Execution providers`
already told you where one topic ends and another begins. So this project splits on `##` and
`###` headings first, then splits any oversized section further, and merges very short
sections with their neighbour so a two-line section does not become its own chunk.

The side benefit is citation quality: because the split follows headings, every chunk knows
which section it came from, and the assistant can say "from *01-foundry-local.md >
Execution providers*" rather than just naming a file.

## Overlap

When a long section must be split, the split point can land in the middle of an explanation
and orphan the conclusion. A small overlap — this project uses about 100 characters, carried
from the end of one chunk to the start of the next — means a fact near a boundary appears in
both chunks and is retrievable from either side.

Overlap costs storage and adds slight redundancy in results. Keep it small: roughly 10% of
the chunk size is a reasonable default.

## Keeping the heading in the text

A subtle but high-value trick: prepend the document title and section heading to the chunk
text *before* embedding it. A chunk that begins "Foundry Local — Execution providers" embeds
closer to a question about Foundry Local than the same paragraph without that line, even if
the paragraph itself never repeats the product name.

This costs a few tokens per chunk and measurably improves retrieval on questions phrased
with the topic name.

## How to tell your chunking is wrong

Retrieval quality is easy to inspect and that is where debugging should start. In this
project, `python -m localrag.cli --show-context` prints the chunks that were retrieved and
their similarity scores. Signals to look for:

- The right document is retrieved but the wrong section → chunks are too large.
- The retrieved chunk is on-topic but does not contain the answer → chunks are too small, or
  the answer straddles a boundary and you need overlap.
- Scores are uniformly low for every question → check that documents and queries use the
  same embedding model.
- One document dominates every result → it is probably far longer than the others; consider
  splitting the file itself.

## The rule

Chunk on structure, not on character counts. The author's headings encode the topic
boundaries; character limits are only the fallback for when a section is too long.
