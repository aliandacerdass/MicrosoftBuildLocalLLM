import numpy as np
import pytest

from localrag import config
from localrag.backends import StubBackend
from localrag.rag import Assistant, build_messages, format_context
from localrag.retrieve import Hit, Retriever
from localrag.store import StoredChunk


def make_retriever(texts: list[str], backend: StubBackend | None = None) -> Retriever:
    """Index the given texts using the stub's own embeddings, as ingestion would."""
    vectors = (backend or StubBackend()).embed(texts)
    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    chunks = [
        StoredChunk(id=i, source=f"doc{i}.md", heading=f"H{i}", text=text)
        for i, text in enumerate(texts)
    ]
    return Retriever(chunks, matrix / norms)


def hit(text: str, score: float = 0.9) -> Hit:
    return Hit(chunk=StoredChunk(id=1, source="a.md", heading="Intro", text=text), score=score)


def test_context_is_numbered_and_labelled():
    context = format_context([hit("first passage"), hit("second passage")])
    assert "[1] a.md > Intro" in context
    assert "[2] a.md > Intro" in context


def test_prompt_carries_rules_question_and_context():
    messages = build_messages("What is RAG?", [hit("RAG means retrieval augmented generation")])
    assert messages[0]["role"] == "system"
    assert config.REFUSAL_MESSAGE in messages[0]["content"]
    assert "ONLY" in messages[0]["content"]
    assert "What is RAG?" in messages[1]["content"]
    assert "RAG means retrieval augmented generation" in messages[1]["content"]


def test_answer_is_generated_and_sources_returned():
    # The stub embeds by shared vocabulary, so the query matches the first chunk.
    retriever = make_retriever(
        ["execution provider backend cpu", "sqlite blob storage vectors"]
    )
    backend = StubBackend(reply="An execution provider runs the math [1]")
    assistant = Assistant(backend, retriever, top_k=2, min_score=0.0)

    answer = assistant.ask("what is an execution provider")

    assert answer.text == "An execution provider runs the math [1]"
    assert not answer.refused
    assert [s.number for s in answer.sources] == [1, 2]
    assert answer.generation_ms > 0


def test_tokens_are_streamed_to_the_callback():
    retriever = make_retriever(["some text here"])
    assistant = Assistant(StubBackend(reply="one two three"), retriever, min_score=0.0)

    streamed: list[str] = []
    answer = assistant.ask("some text", on_token=streamed.append)

    assert "".join(streamed) == "one two three"
    assert answer.text == "one two three"


def test_low_similarity_refuses_without_calling_the_model():
    retriever = make_retriever(["completely unrelated content"])
    backend = StubBackend(reply="this should never be produced")
    assistant = Assistant(backend, retriever, min_score=0.99)

    answer = assistant.ask("a question about something else entirely")

    assert answer.refused
    assert answer.text == config.REFUSAL_MESSAGE
    assert backend.seen_messages == []          # the model was never called
    assert answer.generation_ms == 0
    assert answer.sources                        # but we still show what was closest


def test_empty_question_is_rejected_before_retrieval():
    retriever = make_retriever(["anything"])
    backend = StubBackend()
    answer = Assistant(backend, retriever, min_score=0.0).ask("   ")

    assert answer.refused
    assert backend.seen_messages == []


def test_empty_generation_counts_as_a_refusal():
    retriever = make_retriever(["some text here"])
    assistant = Assistant(StubBackend(reply=""), retriever, min_score=0.0)

    answer = assistant.ask("some text")

    assert answer.text == config.REFUSAL_MESSAGE
    assert answer.refused


def test_model_refusal_is_detected():
    retriever = make_retriever(["some text here"])
    assistant = Assistant(StubBackend(reply=config.REFUSAL_MESSAGE), retriever, min_score=0.0)
    assert assistant.ask("some text").refused


def test_from_index_reports_a_missing_index(tmp_path):
    with pytest.raises(FileNotFoundError, match="python -m localrag.ingest"):
        Assistant.from_index(StubBackend(), db_path=tmp_path / "missing.db")


def test_from_index_reports_an_empty_index(tmp_path):
    from localrag import store

    db = tmp_path / "empty.db"
    store.connect(db).close()
    with pytest.raises(ValueError, match="empty"):
        Assistant.from_index(StubBackend(), db_path=db)
