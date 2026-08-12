"""Measure the assistant against the evaluation set.

Run from the repository root (needs a real Foundry Local model):

    .venv/bin/python tests/eval/run_eval.py
    .venv/bin/python tests/eval/run_eval.py --retrieval-only   # no generation
    .venv/bin/python tests/eval/run_eval.py --chat-model qwen2.5-1.5b

Reports retrieval hit rate, refusal accuracy and latency - the numbers that go
into docs/EVALUATION.md.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from localrag import config  # noqa: E402
from localrag.backends import FoundryBackend  # noqa: E402
from localrag.rag import Assistant  # noqa: E402

QUESTIONS = Path(__file__).with_name("questions.yaml")


def evaluate(assistant: Assistant, cases: dict, retrieval_only: bool) -> dict:
    results = {"answerable": [], "unanswerable": []}

    for case in cases["answerable"]:
        started = time.perf_counter()
        hits = assistant.retrieve(case["question"])
        retrieval_ms = (time.perf_counter() - started) * 1000

        retrieved = [h.chunk.source for h in hits]
        record = {
            "question": case["question"],
            "expected_source": case["source"],
            "retrieved": retrieved,
            "top_score": round(hits[0].score, 3) if hits else 0.0,
            "hit": case["source"] in retrieved,
            "retrieval_ms": round(retrieval_ms, 1),
        }

        if not retrieval_only:
            answer = assistant.ask(case["question"])
            lowered = answer.text.lower()
            record.update(
                {
                    "answer": answer.text,
                    "refused": answer.refused,
                    "keywords_found": [k for k in case["keywords"] if k.lower() in lowered],
                    "keywords_expected": case["keywords"],
                    "generation_ms": round(answer.generation_ms, 1),
                }
            )
            record["correct"] = (
                not answer.refused
                and len(record["keywords_found"]) == len(case["keywords"])
            )
        results["answerable"].append(record)
        print(".", end="", flush=True)

    for case in cases["unanswerable"]:
        hits = assistant.retrieve(case["question"])
        record = {
            "question": case["question"],
            "top_score": round(hits[0].score, 3) if hits else 0.0,
            "refused_by_threshold": not hits or hits[0].score < assistant.min_score,
        }
        if not retrieval_only:
            answer = assistant.ask(case["question"])
            record["answer"] = answer.text
            record["refused"] = answer.refused
        results["unanswerable"].append(record)
        print(".", end="", flush=True)

    print()
    return results


def summarise(results: dict, retrieval_only: bool) -> dict:
    answerable = results["answerable"]
    unanswerable = results["unanswerable"]

    summary = {
        "answerable_count": len(answerable),
        "retrieval_hit_rate": round(sum(r["hit"] for r in answerable) / len(answerable), 3),
        "answerable_score_min": min(r["top_score"] for r in answerable),
        "answerable_score_median": round(
            statistics.median(r["top_score"] for r in answerable), 3
        ),
        "unanswerable_count": len(unanswerable),
        "unanswerable_score_max": max(r["top_score"] for r in unanswerable),
        "threshold_refusal_rate": round(
            sum(r["refused_by_threshold"] for r in unanswerable) / len(unanswerable), 3
        ),
    }

    if not retrieval_only:
        summary["answer_accuracy"] = round(
            sum(r["correct"] for r in answerable) / len(answerable), 3
        )
        summary["false_refusal_rate"] = round(
            sum(r["refused"] for r in answerable) / len(answerable), 3
        )
        summary["refusal_accuracy"] = round(
            sum(r["refused"] for r in unanswerable) / len(unanswerable), 3
        )
        summary["median_generation_ms"] = round(
            statistics.median(r["generation_ms"] for r in answerable), 1
        )
    summary["median_retrieval_ms"] = round(
        statistics.median(r["retrieval_ms"] for r in answerable), 1
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--chat-model", default=config.CHAT_MODEL)
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--min-score", type=float, default=config.MIN_SCORE)
    parser.add_argument("--out", type=Path, help="write the full results as JSON")
    args = parser.parse_args(argv)

    cases = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    backend = FoundryBackend(chat_alias=args.chat_model)
    try:
        assistant = Assistant(
            backend,
            Assistant.from_index(backend).retriever,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        results = evaluate(assistant, cases, args.retrieval_only)
    finally:
        backend.close()

    summary = summarise(results, args.retrieval_only)
    print(f"\nchat model: {args.chat_model}  top_k={args.top_k}  min_score={args.min_score}")
    for key, value in summary.items():
        print(f"  {key:<26} {value}")

    if args.out:
        args.out.write_text(
            json.dumps({"config": vars(args) | {"out": str(args.out)}, "summary": summary,
                        "results": results}, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\nfull results written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
