"""End-to-end checks against real Foundry Local models.

Skipped by default because they download and load model weights. Run with:

    .venv/bin/python -m pytest -m slow -v

A green unit-test run says the pipeline is wired correctly; only these say the
product actually answers questions.
"""

import pytest

from localrag import config
from localrag.backends import FoundryBackend
from localrag.rag import Assistant

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def assistant():
    backend = FoundryBackend()
    try:
        yield Assistant.from_index(backend)
    finally:
        backend.close()


def test_embeddings_have_the_expected_dimension(assistant):
    vectors = assistant.backend.embed(["one", "two"])
    assert len(vectors) == 2
    assert len(vectors[0]) == assistant.retriever.matrix.shape[1] == 1024


def test_retrieves_the_right_document(assistant):
    hits = assistant.retrieve("What is an execution provider?")
    assert hits[0].chunk.source == "01-foundry-local.md"
    assert hits[0].score > config.MIN_SCORE


def test_answers_a_question_from_the_knowledge_base(assistant):
    answer = assistant.ask("What are the three steps of RAG?")
    assert not answer.refused
    lowered = answer.text.lower()
    assert "retriev" in lowered and "augment" in lowered and "generat" in lowered
    assert answer.sources


def test_refuses_a_question_outside_the_knowledge_base(assistant):
    answer = assistant.ask("Who won the 2018 FIFA World Cup?")
    assert answer.refused
    assert answer.generation_ms == 0  # refused by the threshold, model never called
