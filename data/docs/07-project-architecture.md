# This Project's Architecture

How the assistant you are talking to is actually built. Everything below runs on one
machine; nothing leaves it at question time.

> Our own design notes for this repository.

## The pipeline

A question travels through five stages:

1. **Embed the question** with `qwen3-embedding-0.6b`, producing a 1024-dimension vector.
2. **Search** the SQLite index by cosine similarity and take the top 3 passages.
3. **Check the threshold.** If the best passage scores below 0.60, refuse immediately —
   the language model is never called.
4. **Build the prompt**: a system message with the grounding rules, then the numbered
   passages followed by the question.
5. **Generate** the answer with a chat model running on-device through Foundry Local, and
   return it together with the passages it was based on.

Ingestion runs the same machinery in reverse and ahead of time: markdown files are split
into passages, embedded in batches, and written to SQLite with their vectors.

## The modules

| Module | Responsibility |
|---|---|
| `chunking.py` | Splits markdown on headings into ~800-character passages with ~100 characters of overlap |
| `store.py` | SQLite schema, float32 BLOB vectors, idempotent inserts, stale-chunk removal, normalised loading |
| `ingest.py` | Documents to chunks to batched embeddings to SQLite |
| `retrieve.py` | Cosine top-k over the in-memory matrix |
| `rag.py` | Prompt assembly, citations, threshold refusal, timing |
| `backends.py` | The Foundry Local backend, plus a deterministic stub used by the tests |
| `cli.py`, `ui.py` | Two interfaces over a single `Assistant.ask()` |

Each module does one thing, which is what makes the system debuggable: when an answer is
wrong you can tell whether retrieval or generation failed, instead of guessing.

## Design decisions and why

**SQLite plus numpy instead of a vector database.** The index is 46 passages. Loading all
the vectors into memory and scoring them with one matrix product takes about 27
milliseconds. A dedicated vector store would add a dependency and buy nothing at this
scale.

**Raw float32 bytes instead of JSON vectors.** Roughly ten times smaller and no parsing on
read. The dimension is stored next to each vector so a mismatched embedding model fails
loudly instead of quietly returning nonsense.

**Lazy model loading.** Ingestion never loads the chat model and question answering never
loads a model it does not use. On a machine where loading takes seconds and downloading
takes minutes, this is worth the few lines it costs.

**A backend seam with a stub implementation.** The unit tests exercise chunking, storage,
retrieval and prompt assembly against a deterministic fake, so they run in under a second
with no downloads. The stub is explicitly not a substitute for a real end-to-end check —
it cannot tell you whether the assistant answers well.

**Refusing before generation.** A prompt instruction is a request the model can ignore. A
similarity threshold is arithmetic it cannot argue with, and it costs no generation time.

## How the threshold was chosen

Not by guessing. Running the 22-question evaluation set with the threshold disabled gave a
clean separation:

- Questions that *are* answerable from the knowledge base scored **0.624 and above**
  (median 0.696).
- Questions deliberately outside it scored **0.580 and below**.

So the threshold sits between them, at **0.60**. The gap is not large, and the closest
out-of-scope question — asking how to deploy this assistant to Azure Kubernetes Service —
scored 0.580 precisely because it is topically adjacent. Retrieval alone cannot separate
"about the same subject" from "answerable"; the system prompt is the second line of
defence there.

## What runs where

Everything: the embedding model, the vector search, the SQLite file and the chat model all
live on the local device. The only step that needs a network is the initial model download,
which is setup rather than runtime. Turning off Wi-Fi and asking another question is the
simplest proof, and it is the one worth showing.

## Measured performance

On an Apple M4 (CPU inference, no GPU execution provider registered):

| Step | Time |
|---|---|
| Retrieval (embed the query plus search 46 passages) | ~27 ms |
| Answer generation | a few seconds, depending on model size |
| Loading a cached model | 1.6-3.3 s |
| Downloading a model (one-time) | 5-9 minutes each |

The retrieval cost is negligible; generation dominates. That is why the assistant retrieves
three passages rather than twenty — on a local CPU, every extra token of prompt is time the
user waits.
