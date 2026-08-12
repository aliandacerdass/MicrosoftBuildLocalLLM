import numpy as np
import pytest

from localrag.retrieve import Retriever
from localrag.store import StoredChunk


def build(vectors: list[list[float]]) -> Retriever:
    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    chunks = [
        StoredChunk(id=i, source=f"{i}.md", heading="H", text=f"chunk {i}")
        for i in range(len(vectors))
    ]
    return Retriever(chunks, matrix / norms)


def test_returns_best_match_first():
    retriever = build([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]])
    hits = retriever.search([1.0, 0.0], top_k=3)
    assert hits[0].chunk.id == 0
    assert hits[0].score > hits[1].score >= hits[2].score


def test_scores_are_cosine_similarities():
    retriever = build([[1.0, 0.0]])
    assert np.isclose(retriever.search([2.0, 0.0], top_k=1)[0].score, 1.0)
    assert np.isclose(retriever.search([0.0, 5.0], top_k=1)[0].score, 0.0, atol=1e-6)


def test_top_k_is_capped_at_index_size():
    retriever = build([[1.0, 0.0], [0.0, 1.0]])
    assert len(retriever.search([1.0, 0.0], top_k=10)) == 2


def test_empty_index_returns_nothing():
    retriever = Retriever([], np.zeros((0, 0), dtype=np.float32))
    assert retriever.search([1.0, 0.0], top_k=3) == []


def test_wrong_query_dimension_is_rejected():
    retriever = build([[1.0, 0.0]])
    with pytest.raises(ValueError, match="same embedding model"):
        retriever.search([1.0, 0.0, 0.0], top_k=1)


def test_chunk_and_vector_count_must_agree():
    with pytest.raises(ValueError, match="chunks but"):
        Retriever([], np.ones((2, 3), dtype=np.float32))
