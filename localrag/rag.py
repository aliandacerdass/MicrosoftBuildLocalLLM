"""The RAG loop: retrieve, augment, generate.

Two defences against a confident wrong answer live here. The first is the system
prompt, which tells the model to answer only from the supplied passages. The
second is a similarity threshold: if even the best passage is a poor match we
refuse before the model is called at all, which no amount of prompting can be
talked out of.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from . import config, store
from .backends import Backend, Message
from .retrieve import Hit, Retriever

SYSTEM_PROMPT = """You are a documentation assistant. Answer the user's question \
using ONLY the numbered context passages provided.

Rules:
- If the passages do not contain the answer, reply exactly: "{refusal}"
- Never use knowledge from outside the passages, and never guess.
- Cite the passages you used with their numbers, like [1] or [2].
- Be concise: a short paragraph, or a few bullet points at most."""


@dataclass(frozen=True)
class Source:
    """A passage that was given to the model, kept so the user can check it."""

    number: int
    label: str
    text: str
    score: float


@dataclass
class Answer:
    """Everything the interfaces need to display one answer."""

    question: str
    text: str
    sources: list[Source] = field(default_factory=list)
    refused: bool = False
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0

    @property
    def total_ms(self) -> float:
        return self.retrieval_ms + self.generation_ms


def format_context(hits: Iterable[Hit]) -> str:
    """Number the passages so the model has labels it can actually cite."""
    blocks = []
    for number, hit in enumerate(hits, start=1):
        blocks.append(f"[{number}] {hit.chunk.label}\n{hit.chunk.text}")
    return "\n\n".join(blocks)


def build_messages(question: str, hits: list[Hit]) -> list[Message]:
    """Assemble the prompt sent to the local model."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(refusal=config.REFUSAL_MESSAGE)},
        {
            "role": "user",
            "content": (
                f"Context passages:\n\n{format_context(hits)}\n\n"
                f"Question: {question.strip()}"
            ),
        },
    ]


class Assistant:
    """Ties the index, the retriever and the model together."""

    def __init__(
        self,
        backend: Backend,
        retriever: Retriever,
        top_k: int = config.TOP_K,
        min_score: float = config.MIN_SCORE,
    ) -> None:
        self.backend = backend
        self.retriever = retriever
        self.top_k = top_k
        self.min_score = min_score

    @classmethod
    def from_index(cls, backend: Backend, db_path: Path = config.DB_PATH, **kwargs) -> "Assistant":
        """Load the SQLite index from disk and build an assistant around it."""
        if not db_path.exists():
            raise FileNotFoundError(
                f"No index at {db_path}. Build it first with: python -m localrag.ingest"
            )
        connection = store.connect(db_path)
        try:
            chunks, matrix = store.load_index(connection)
        finally:
            connection.close()

        if not chunks:
            raise ValueError(
                f"The index at {db_path} is empty. Run: python -m localrag.ingest"
            )
        return cls(backend, Retriever(chunks, matrix), **kwargs)

    def retrieve(self, question: str) -> list[Hit]:
        """Find the passages most similar to the question."""
        query_vector = self.backend.embed([question])[0]
        return self.retriever.search(query_vector, self.top_k)

    def ask(self, question: str, on_token: Callable[[str], None] | None = None) -> Answer:
        """Answer one question. ``on_token`` receives the answer as it streams."""
        question = question.strip()
        if not question:
            return Answer(question="", text="Please ask a question.", refused=True)

        started = time.perf_counter()
        hits = self.retrieve(question)
        retrieval_ms = (time.perf_counter() - started) * 1000

        sources = [
            Source(number=i, label=h.chunk.label, text=h.chunk.text, score=h.score)
            for i, h in enumerate(hits, start=1)
        ]

        if not hits or hits[0].score < self.min_score:
            # Nothing close enough to be worth generating from. Refusing here is
            # both instant and impossible for the model to override.
            return Answer(
                question=question,
                text=config.REFUSAL_MESSAGE,
                sources=sources,
                refused=True,
                retrieval_ms=retrieval_ms,
            )

        started = time.perf_counter()
        parts: list[str] = []
        for token in self.backend.stream_chat(build_messages(question, hits)):
            parts.append(token)
            if on_token:
                on_token(token)
        generation_ms = (time.perf_counter() - started) * 1000

        text = "".join(parts).strip()
        return Answer(
            question=question,
            text=text or config.REFUSAL_MESSAGE,
            sources=sources,
            refused=config.REFUSAL_MESSAGE.lower() in text.lower(),
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
        )
