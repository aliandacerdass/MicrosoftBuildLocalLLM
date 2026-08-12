# Retrieval-Augmented Generation (RAG)

RAG is a design pattern for making a language model answer from *your* data instead of from
whatever it memorised during training. Three steps: **retrieve** the relevant passages,
**augment** the prompt with them, **generate** the answer from that context.

> Our own summary. Background reading:
> https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968

## The problem RAG solves

A language model is a compressed snapshot of its training data. Ask it about your company's
internal refund policy, your lecture notes, or a manual written last week, and it has three
possible behaviours: it says it does not know, it gives a plausible-sounding wrong answer,
or it gives a right answer by luck. The middle case — a fluent, confident, wrong answer — is
called a hallucination and it is the dangerous one, because nothing in the output signals
that it is wrong.

RAG attacks this by changing what the model is asked to do. Instead of "recall the answer",
the task becomes "read this passage and answer from it". Reading comprehension is a much
easier task than recall, which is why even small models get noticeably better with RAG.

## The three steps

**Retrieve.** Convert the user's question into a vector, compare it against vectors of all
stored document chunks, and take the most similar few. This is semantic search: it matches
meaning, so "how do I turn it off?" can find a passage titled "Shutting down the service"
even with no shared words.

**Augment.** Build a prompt containing the retrieved passages plus the original question,
along with instructions about how to use them — most importantly, an instruction to answer
only from the given context and to admit ignorance otherwise.

**Generate.** The model writes an answer grounded in the passages. Because you know which
passages went in, you can show the user exactly which sources the answer came from.

## Why grounding beats memory

Three concrete benefits:

- **Fewer hallucinations.** The facts are in the prompt, so the model does not have to
  invent them.
- **Attribution.** You can cite the source of every answer, which lets a human verify it.
  An answer you cannot check is worth much less than one you can.
- **Fresh knowledge without retraining.** Add a file, re-run ingestion, and the assistant
  knows about it. No fine-tuning, no GPU cluster, no waiting.

## RAG versus alternatives

**Versus pasting everything into the prompt.** If your whole knowledge base fits in the
context window, just paste it — that is simpler and it works. RAG starts to earn its keep
when the corpus is bigger than the context window, or when you want to keep prompts short so
inference stays fast. On a local CPU, prompt length directly costs seconds, so retrieving
three relevant chunks instead of pasting fifty documents is a real speed win.

**Versus fine-tuning.** Fine-tuning teaches a model a style, a format, or a skill. It is a
poor way to teach facts: the facts get blurred into the weights, they cannot be cited, and
updating them means retraining. For a factual Q&A assistant, retrieval is the right tool.

## Where RAG fails

RAG is not magic, and knowing its failure modes is part of using it well:

- **Retrieval misses.** If the right chunk is never retrieved, the model cannot answer
  correctly no matter how good it is. Most disappointing RAG results are retrieval bugs, not
  model bugs — which is why this project's CLI has a `--show-context` flag.
- **Bad chunking.** A passage split in the middle of an explanation gives the model half an
  answer.
- **Questions that span many documents.** "Summarise everything about X" needs breadth;
  top-k retrieval gives depth on a few passages.
- **The model ignores the context.** Small models sometimes answer from memory despite the
  instruction. This is worth testing for explicitly.

## What a minimal RAG system needs

Four components, and this project has exactly these four:

1. An **embedding model** to turn text into vectors.
2. A **store** that holds chunks and their vectors (here, SQLite).
3. A **similarity search** to rank chunks against the query (here, cosine similarity in
   numpy).
4. A **chat model** to write the final answer from the retrieved context.
