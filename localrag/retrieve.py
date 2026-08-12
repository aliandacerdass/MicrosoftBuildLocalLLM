"""Semantic search over the stored chunks.

At this scale (hundreds of chunks, 1024 dimensions) the whole index fits in
memory and scoring is a single matrix-vector product, so there is nothing to gain
from an approximate-nearest-neighbour index.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .store import DTYPE, StoredChunk


@dataclass(frozen=True)
class Hit:
    """One retrieved chunk and how well it matched."""

    chunk: StoredChunk
    score: float


class Retriever:
    """Holds the in-memory index and answers top-k queries against it."""

    def __init__(self, chunks: list[StoredChunk], matrix: np.ndarray) -> None:
        if len(chunks) != matrix.shape[0]:
            raise ValueError(f"{len(chunks)} chunks but {matrix.shape[0]} vectors")
        self.chunks = chunks
        self.matrix = matrix

    def __len__(self) -> int:
        return len(self.chunks)

    def search(self, query_vector: list[float], top_k: int) -> list[Hit]:
        """Return the ``top_k`` most similar chunks, best first."""
        if not self.chunks:
            return []

        query = np.asarray(query_vector, dtype=DTYPE)
        if query.shape[0] != self.matrix.shape[1]:
            raise ValueError(
                f"Query vector has {query.shape[0]} dimensions but the index has "
                f"{self.matrix.shape[1]}. The query and the documents must come from "
                "the same embedding model."
            )

        norm = float(np.linalg.norm(query))
        if norm:
            query = query / norm

        # The stored matrix is already L2-normalised, so the dot product is the
        # cosine similarity.
        scores = self.matrix @ query
        top_k = min(top_k, len(scores))
        best = np.argpartition(-scores, top_k - 1)[:top_k]
        best = best[np.argsort(-scores[best])]
        return [Hit(chunk=self.chunks[i], score=float(scores[i])) for i in best]
