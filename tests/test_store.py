import numpy as np
import pytest

from localrag import store
from localrag.chunking import Chunk


def make_chunk(text: str, source: str = "a.md", ordinal: int = 0) -> Chunk:
    return Chunk(source=source, heading="H", ordinal=ordinal, text=text)


@pytest.fixture
def connection(tmp_path):
    conn = store.connect(tmp_path / "index.db")
    yield conn
    conn.close()


def test_insert_and_load_round_trip(connection):
    chunks = [make_chunk("first", ordinal=0), make_chunk("second", ordinal=1)]
    vectors = [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]
    assert store.insert_chunks(connection, chunks, vectors) == 2

    loaded, matrix = store.load_index(connection)
    assert [c.text for c in loaded] == ["first", "second"]
    assert matrix.shape == (2, 3)


def test_vectors_come_back_normalised(connection):
    store.insert_chunks(connection, [make_chunk("x")], [[3.0, 4.0]])
    _, matrix = store.load_index(connection)
    assert np.isclose(np.linalg.norm(matrix[0]), 1.0)


def test_reinsert_of_same_text_is_skipped(connection):
    chunk = make_chunk("same text")
    store.insert_chunks(connection, [chunk], [[1.0, 0.0]])
    inserted = store.insert_chunks(connection, [chunk], [[1.0, 0.0]])
    assert inserted == 0
    loaded, _ = store.load_index(connection)
    assert len(loaded) == 1


def test_same_text_in_different_files_is_kept_separately(connection):
    store.insert_chunks(connection, [make_chunk("shared", source="a.md")], [[1.0, 0.0]])
    store.insert_chunks(connection, [make_chunk("shared", source="b.md")], [[1.0, 0.0]])
    loaded, _ = store.load_index(connection)
    assert {c.source for c in loaded} == {"a.md", "b.md"}


def test_mismatched_vector_count_is_rejected(connection):
    with pytest.raises(ValueError, match="chunks but"):
        store.insert_chunks(connection, [make_chunk("a"), make_chunk("b")], [[1.0]])


def test_mixed_dimensions_fail_loudly(connection):
    store.insert_chunks(connection, [make_chunk("a")], [[1.0, 0.0]])
    store.insert_chunks(connection, [make_chunk("b")], [[1.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="different dimensions"):
        store.load_index(connection)


def test_empty_index_loads_cleanly(connection):
    chunks, matrix = store.load_index(connection)
    assert chunks == []
    assert matrix.shape[0] == 0


def test_delete_source_removes_only_that_file(connection):
    store.insert_chunks(connection, [make_chunk("a", source="a.md")], [[1.0, 0.0]])
    store.insert_chunks(connection, [make_chunk("b", source="b.md")], [[0.0, 1.0]])
    assert store.delete_source(connection, "a.md") == 1
    assert store.stats(connection) == {"b.md": 1}
