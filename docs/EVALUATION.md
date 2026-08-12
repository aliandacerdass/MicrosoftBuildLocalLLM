# Evaluation

How well the assistant works, measured rather than asserted. Every number here comes from
running `tests/eval/run_eval.py` on this machine; nothing is estimated.

## Method

The question set is `tests/eval/questions.yaml`: **25 questions**, split into two groups.

- **20 answerable** questions, each tagged with the document that contains the answer and
  the keywords a correct answer must mention. Three of them are phrased the way a real user
  asked them rather than the way the documents are worded — they were added after a user's
  question was wrongly refused (see below).
- **5 out-of-scope** questions the knowledge base genuinely cannot answer (world facts,
  personal data, cloud deployment). The assistant is expected to refuse these.

Three things are measured:

| Metric | What it tells you |
|---|---|
| **Retrieval hit rate** | Did the correct document appear in the top 3 passages? Isolates retrieval from generation. |
| **Answer accuracy** | Did the generated answer contain every expected keyword, without refusing? |
| **Refusal accuracy** | Were the out-of-scope questions refused rather than answered? |

Keyword matching is a blunt instrument — it can mark a correct answer wrong because it used
a synonym. Every failure below was read by hand before being counted.

The one current miss is exactly that: asked how the refusal threshold was chosen, the model
gives a complete and accurate answer — it names 0.624, 0.552, the overfitted 0.60 and the
final 0.45 — but never uses the word the check looks for. The keyword for that question had
already been adjusted once, so it was left alone rather than adjusted again: past a certain
point, editing the check until it passes stops being measurement. The headline number is
therefore reported as 19/20, with the caveat that reading the answer shows 20/20.

Reproduce with:

```bash
python -m localrag.ingest
python tests/eval/run_eval.py                    # full run
python tests/eval/run_eval.py --retrieval-only   # retrieval only, no chat model needed
```

## Results

Configuration: `qwen2.5-1.5b` chat model, `qwen3-embedding-0.6b` embeddings (1024
dimensions), `top_k = 3`, `min_score = 0.45`, 56 indexed passages. Apple M4, CPU inference.

| Metric | Result |
|---|---|
| Retrieval hit rate | **20/20 (100%)** |
| Answer accuracy | **19/20 by keyword, 20/20 by hand** (see below) |
| Out-of-scope questions refused | **5/5 (100%)** |
| Answerable questions wrongly refused | **0/20 (0%)** |
| Median retrieval time | 27 ms isolated, 70 ms with the chat model also resident |
| Median generation time | 3.3-5.8 s (varies noticeably between runs) |

## Choosing the refusal threshold

The first attempt set the threshold from the measured gap between the two groups. With the
original 17 questions, answerable ones scored 0.624 and above while out-of-scope ones stayed
at 0.552 and below, so `MIN_SCORE = 0.60` sat neatly between them.

**That was overfitted, and a real user broke it immediately.** Asked *"How was the refusal
threshold chosen?"* the assistant refused — even though it had retrieved exactly the right
passage, `07-project-architecture.md > How the threshold was chosen`, as the top hit. The
question simply scored 0.514, because it was phrased naturally instead of in the documents'
own words:

| Question (naturally phrased) | Top score | Correct passage retrieved? |
|---|---|---|
| How was the refusal threshold chosen? | 0.514 | yes, rank 1 |
| What runs on the device and what needs the network? | 0.512 | yes, rank 1 |
| What is the refusal threshold and why 0.60? | 0.517 | yes, rank 1 |
| Which parts run on the device and which need a network? | 0.539 | yes, rank 1 |

These land in the same band as the out-of-scope questions, so no threshold can separate
"badly phrased but answerable" from "off topic" on similarity alone.

The threshold was therefore lowered to **0.45** and the result measured rather than assumed:

| `min_score` | Out-of-scope refused | Answerable wrongly refused |
|---|---|---|
| 0.60 | 5/5 (all by the threshold) | real user questions, silently |
| 0.50 | 5/5 (3 by threshold, 2 by the model) | 0/20 |
| **0.45** | **5/5** (3 by threshold, 2 by the model) | **0/20** |

At 0.45 the protection is unchanged — the two out-of-scope questions that now reach the
model (`0.552` and `0.508`) are refused by the model itself, which is exactly the job the
system prompt was written for. So the loose threshold is strictly better: same refusals,
fewer false ones. It also turns "the system prompt is the second line of defence" from a
claim into something that has actually been exercised.

The individual out-of-scope scores show how narrow the band is:

| Question | Top score |
|---|---|
| Who won the 2018 FIFA World Cup? | 0.254 |
| What is the capital city of Australia? | 0.292 |
| What is my bank account balance? | 0.422 |
| What is the price per token of GPT-4 on the OpenAI API? | 0.508 |
| How do I deploy this assistant to Azure Kubernetes Service? | **0.552** |

The last one scores high because it *is* about this project — just about something the
documents never cover. Similarity measures topic, not answerability, so the threshold alone
can never separate "related" from "answerable". With `min_score = 0.45` this question and
the GPT-4 pricing one reach the model, and the model refuses both.

## What changed during tuning

Three iterations, each driven by a measurement rather than a hunch.

**1. The threshold started as a guess, was over-tightened, then corrected.** The initial
`MIN_SCORE = 0.35` was picked before any data existed. Measured separation moved it to 0.60,
which turned out to be overfitted to questions written in the documents' own vocabulary; a
real user's phrasing was refused despite perfect retrieval. It now sits at 0.45, with the
model handling the ambiguous band. The lesson is not "measure once" but "measure on inputs
you did not write".

**2. Two keyword checks were wrong, not two answers.** An early run scored 14/17. Reading
the answers showed two were correct but phrased differently: the expected keyword
`boundary` did not match the answer's `boundaries`, and `skip` did not match "only changes
are ingested". Those checks were fixed (a stem, and the concept word `unchanged`). This
changes the measuring instrument, not the system — worth stating plainly.

**3. One genuine error, fixed by better context.** In the same run the model answered the
float32-versus-JSON question with an invented figure ("around 4000 bytes for JSON"). After
`07-project-architecture.md` was added to the knowledge base, the "roughly ten times
smaller" fact was retrievable and the answer became correct. A reminder that in RAG, the
first thing to check after a bad answer is what was retrieved.

**4. Answers were being cut off.** `MAX_TOKENS` was 400, which truncated a verbose answer
mid-sentence — it reads as a crash rather than an answer. Raised to 600; most answers are far
shorter, so only the long ones cost more time.

**5. A cross-model review found three real bugs.** The diff was reviewed by a different
model family (Gemini, via the Antigravity CLI) and every finding was checked against the
code. Three held: a document with no subheadings had its title duplicated inside the chunk;
the chunk-size accounting ignored the two-character paragraph separators and could overshoot
the target on lists; and an empty generation produced the refusal *text* while reporting
`refused = False`, which the CLI then printed as a blank line. One finding was a false
positive (the chunk text embeds its heading, so identical bodies under different headings
already hash differently). All three fixes carry tests, and the evaluation was re-run after
them with identical results.

## Honest limits of these numbers

- **25 questions is a small set.** It is enough to catch systematic failures, not enough to
  claim a precise accuracy percentage.
- **Most questions were written by the person who wrote the documents.** They are phrased
  the way the source material is phrased, which flatters retrieval. Three questions from a
  real user were added after this bit us, and they scored 0.11 to 0.18 lower than the
  in-house phrasings of the same facts. Three is not enough; a bigger set of outside
  phrasings would probably find more.
- **Keyword matching is not comprehension.** An answer can contain every keyword and still
  be poorly reasoned.
- **100% is a ceiling artefact.** It means this set no longer discriminates between good and
  better; a harder set (paraphrased questions, multi-document questions) would.

## Model choice

`qwen2.5-1.5b` is the default: it answers the whole evaluation set correctly at a median of
3.3 to 5.8 seconds per answer on CPU, depending on the run.

Two smaller/larger alternatives were considered:

- **`qwen2.5-0.5b`** — rejected. Fast (~1.2 s) but too weak: asked what RAG means with no
  context, it invented "Retributionary Amplification Game". Retrieval can ground a small
  model, but this one is below the useful floor.
- **`phi-3.5-mini`** (3.8B) — the model the program brief suggests. Benchmarked on the same
  set:

  | | `qwen2.5-1.5b` | `phi-3.5-mini` |
  |---|---|---|
  | Retrieval hit rate | 100% | 100% |
  | Answer accuracy | 17/17 | 16/17 |
  | Refusal accuracy | 5/5 | 5/5 |
  | Median generation | **3.3 s** | 16.0 s |
  | Slowest answer | 14.5 s | 43.6 s |

  Its single miss is a keyword artefact, not a wrong answer — its reply about prepending
  headings is correct and more thorough than the smaller model's. So the two are comparable
  in quality on this set, and `phi-3.5-mini` is roughly **five times slower** on CPU. For an
  interactive assistant that trade is not worth it, so the smaller model is the default. Try
  it yourself with `LOCALRAG_CHAT_MODEL=phi-3.5-mini python tests/eval/run_eval.py`.

  A caveat: this set is not hard enough to separate the two models. On longer or
  multi-document questions the larger model would probably pull ahead.
