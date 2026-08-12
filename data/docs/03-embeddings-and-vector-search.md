# Embeddings and Vector Search

An embedding is a list of numbers that represents the *meaning* of a piece of text. Texts
with similar meanings get vectors that point in similar directions, which turns "find
related text" into simple arithmetic.

> Our own summary. Official reference:
> https://learn.microsoft.com/en-us/azure/foundry-local/how-to/how-to-generate-embeddings

## From words to numbers

Keyword search matches characters. Ask it for "how do I shut this down" and it will not find
a document that says "terminating the process", because they share no words. An embedding
model has been trained so that both sentences map to nearby points in a high-dimensional
space — so a search over vectors finds it.

Each dimension is not individually meaningful; you cannot point at position 47 and say "this
is the politeness axis". What matters is the geometry: the relative direction between
vectors encodes relative meaning.

## Generating embeddings with Foundry Local

The embedding client works exactly like the chat client — same lifecycle, different client
object:

```python
model = manager.catalog.get_model("qwen3-embedding-0.6b")
model.download()
model.load()
client = model.get_embedding_client()

single = client.generate_embedding("What is RAG?")
vector = single.data[0].embedding

batch = client.generate_embeddings(["first text", "second text", "third text"])
for item in batch.data:
    print(len(item.embedding))
```

In this project, `qwen3-embedding-0.6b` produces vectors of **1024 dimensions**, and
embedding three short texts took about 0.9 seconds on an M4 CPU.

Always prefer `generate_embeddings` (the batch call) over looping `generate_embedding`. Each
call has fixed overhead, and batching amortises it across the whole set — this is the
difference between an ingestion that takes seconds and one that takes minutes.

## Cosine similarity

To compare two vectors we use cosine similarity: the cosine of the angle between them.

```
similarity(a, b) = (a · b) / (|a| * |b|)
```

It ranges from -1 (opposite) through 0 (unrelated) to 1 (identical direction). We use the
angle rather than the distance because we care about direction, not magnitude — a long
passage and a short one about the same topic should still match.

The useful trick: if you **normalise** every vector to unit length first, the denominator
becomes 1 and cosine similarity is just the dot product. Normalise once at ingestion time,
and every later search is a plain multiplication.

## Searching efficiently at small scale

With normalised vectors stacked into one matrix, scoring the entire corpus against a query
is a single matrix-vector product:

```python
matrix = np.vstack(all_chunk_vectors)      # shape (n_chunks, 1024)
scores = matrix @ query_vector             # shape (n_chunks,)
top_k = np.argsort(-scores)[:k]
```

For a few hundred or a few thousand chunks this is effectively instantaneous — numpy is
doing one BLAS call. There is no reason to add a dedicated vector database at this scale;
the extra dependency would cost more than it saves.

## When you would outgrow this

Brute force is O(n) per query. It stays comfortable into the tens of thousands of chunks.
Past that, the standard answer is an approximate nearest-neighbour index (HNSW, IVF), which
trades a small amount of recall for a large speedup, available through libraries like FAISS
or extensions such as `sqlite-vec`. Reach for one when you have measured a problem, not
before.

## Practical rules

- **Use the same embedding model for documents and queries.** Vectors from two different
  models are not comparable at all — the search will return noise.
- **If you change the embedding model, re-ingest everything.** The old vectors are dead.
- **Store the dimension count.** It is a cheap sanity check that catches a mismatched model
  immediately instead of three debugging hours later.
- **Embeddings do not understand negation well.** "Server supports TLS" and "server does not
  support TLS" land close together. Retrieval finds the topic; the language model has to
  read the detail.
