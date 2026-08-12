"""Console interface. Run with ``python -m localrag.cli``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .rag import Answer, Assistant

BANNER = """Local RAG Assistant - Microsoft Foundry Local
Chat model : {chat}
Index      : {chunks} chunks from {db}
Ask a question, or type 'exit' to quit.
"""


def print_sources(answer: Answer, show_text: bool) -> None:
    if not answer.sources:
        return
    print("\nSources:")
    for source in answer.sources:
        print(f"  [{source.number}] {source.label}  (similarity {source.score:.3f})")
        if show_text:
            for line in source.text.splitlines():
                print(f"      | {line}")


def ask_once(assistant: Assistant, question: str, show_context: bool) -> Answer:
    print("\n", end="")
    streamed: list[str] = []

    def show(token: str) -> None:
        streamed.append(token)
        print(token, end="", flush=True)

    answer = assistant.ask(question, on_token=show)
    if not "".join(streamed).strip():
        # Refused before generation, or the model produced nothing at all.
        print(answer.text, end="")
    print()
    print_sources(answer, show_context)
    print(
        f"\n({answer.retrieval_ms:.0f} ms retrieval, "
        f"{answer.generation_ms:.0f} ms generation)\n"
    )
    return answer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask questions about the local knowledge base.")
    parser.add_argument("question", nargs="*", help="ask one question and exit")
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--min-score", type=float, default=config.MIN_SCORE)
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="print the retrieved passages - the first thing to check when an answer looks wrong",
    )
    args = parser.parse_args(argv)

    from .backends import FoundryBackend

    backend = FoundryBackend()
    try:
        assistant = Assistant.from_index(
            backend, db_path=args.db, top_k=args.top_k, min_score=args.min_score
        )

        if args.question:
            ask_once(assistant, " ".join(args.question), args.show_context)
            return 0

        print(
            BANNER.format(
                chat=config.CHAT_MODEL, chunks=len(assistant.retriever), db=args.db
            )
        )
        while True:
            try:
                question = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if question.lower() in {"exit", "quit", "q"}:
                return 0
            if question:
                ask_once(assistant, question, args.show_context)
    finally:
        backend.close()


if __name__ == "__main__":
    sys.exit(main())
