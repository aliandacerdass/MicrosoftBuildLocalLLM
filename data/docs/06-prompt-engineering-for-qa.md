# Prompt Engineering for Grounded Q&A

Retrieving the right passage is only half the job. The prompt decides whether the model
actually uses it, admits when it cannot answer, and tells the user where the answer came
from.

> Our own notes. Background reading:
> https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/prompt-engineering

## System and user messages

Chat models take a list of messages, each with a role:

- **system** — standing instructions: who the assistant is and what rules it follows. Set
  once, applies to the whole conversation.
- **user** — the actual question, plus the retrieved context.
- **assistant** — the model's own previous replies, if you are keeping history.

The split matters because rules put in the system message survive the conversation, while
rules buried inside a long user message tend to get lost behind the content.

## A grounding system prompt

Four instructions carry almost all the weight:

1. **Answer only from the provided context.** This is the whole point — it forbids the model
   from filling gaps with training-data memories.
2. **If the context does not contain the answer, say so.** Without this, a helpful-by-default
   model will guess. An explicit permission to fail is what makes "I don't know" an
   acceptable output.
3. **Cite the sources you used.** Numbered references like `[1]`, `[2]` are enough, as long
   as the context block is numbered to match.
4. **Be concise.** Local models on CPU generate a limited number of tokens per second, so a
   rambling answer is a slow answer. Brevity is a latency feature, not just a style
   preference.

## Formatting the context block

The model has to be able to tell where each passage starts, ends, and came from. A numbered
block with explicit source labels does that:

```
[1] 01-foundry-local.md > Execution providers
An execution provider is the backend that actually runs the model's math...

[2] 03-embeddings-and-vector-search.md > Cosine similarity
To compare two vectors we use cosine similarity...
```

Then the question follows. Numbering the passages is what makes `[1]`-style citation
possible at all: the model can only cite labels you gave it.

## Refusing before the model runs

An instruction to say "I don't know" is a request, not a guarantee — a small model may
ignore it. A more reliable defence sits earlier in the pipeline: if the best retrieved chunk
scores below a similarity threshold, refuse without calling the model at all.

This is deterministic, it cannot be talked around, and it is instant — no generation time
spent on a question the knowledge base cannot answer.

The threshold must be tuned against real data. Set it by looking at the actual similarity
scores of questions you know are answerable versus ones you know are not, and pick a value
that separates them. Guessing produces an assistant that either refuses everything or never
refuses.

## What goes wrong

- **The model answers from memory.** It ignored the context. Strengthen the system prompt,
  or use a stronger model. Test for it explicitly with a question whose correct answer only
  exists in your documents.
- **It refuses when the answer is right there.** Usually a retrieval problem, not a prompt
  problem — check what was retrieved before touching the prompt.
- **Citations are invented.** The model cites `[4]` when you only supplied three passages.
  Number the context explicitly and keep the count small.
- **Answers are too long.** Ask for brevity in the system prompt and cap the generated token
  count.

## Testing prompts

Prompt changes are code changes and deserve the same discipline: keep a fixed set of
questions, run them before and after, and compare. Without a fixed set you are tuning on
whichever question you happened to type, and it is very easy to fix one case while quietly
breaking three others.
