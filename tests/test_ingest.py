import pytest

from localrag import store
from localrag.backends import StubBackend
from localrag.ingest import ingest

DOC_A = """# Alpha

## One

Alpha section one has enough prose to clear the minimum chunk size comfortably,
covering a single topic in a couple of sentences so that it stands on its own as
a passage somebody could actually get an answer out of without more context.

## Two

Alpha section two also carries enough text to be a chunk of its own, describing a
second topic that a reader could ask a question about, with enough sentences that
it is not folded into its neighbour by the merge rule.
"""

DOC_B = """# Beta

## Only

Beta has a single section, again long enough to survive the merge rule and become
one retrievable passage in the index rather than being merged away into whatever
section happens to follow it in the document.
"""


@pytest.fixture
def docs(tmp_path):
    directory = tmp_path / "docs"
    directory.mkdir()
    (directory / "a.md").write_text(DOC_A, encoding="utf-8")
    (directory / "b.md").write_text(DOC_B, encoding="utf-8")
    return directory


def test_ingest_populates_the_index(docs, tmp_path):
    db = tmp_path / "index.db"
    result = ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    assert result["inserted"] == result["chunks"] > 0
    connection = store.connect(db)
    try:
        assert set(store.stats(connection)) == {"a.md", "b.md"}
    finally:
        connection.close()


def test_second_run_embeds_nothing_new(docs, tmp_path):
    db = tmp_path / "index.db"
    ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    class CountingBackend(StubBackend):
        calls = 0

        def embed(self, texts):
            CountingBackend.calls += 1
            return super().embed(texts)

    second = ingest(CountingBackend(), docs_dir=docs, db_path=db, verbose=False)
    assert second["new"] == 0
    assert CountingBackend.calls == 0


def test_edited_document_adds_its_new_chunks(docs, tmp_path):
    db = tmp_path / "index.db"
    first = ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    (docs / "b.md").write_text(
        DOC_B + "\n## Extra\n\nA newly added section with enough words in it to "
        "become a chunk of its own rather than being merged away into the section "
        "before it, which is what the minimum size rule would otherwise do to a "
        "section this short if it did not carry enough characters of its own.\n",
        encoding="utf-8",
    )
    second = ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    assert second["new"] == 1
    assert second["chunks"] == first["chunks"] + 1


def test_edited_document_drops_its_old_chunks(docs, tmp_path):
    db = tmp_path / "index.db"
    ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    (docs / "b.md").write_text(
        DOC_B.replace("Beta has a single section", "Beta was completely rewritten"),
        encoding="utf-8",
    )
    second = ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    assert second["removed"] == 1
    connection = store.connect(db)
    try:
        rows = connection.execute("SELECT text FROM chunks WHERE source = 'b.md'").fetchall()
    finally:
        connection.close()
    assert len(rows) == 1
    assert "completely rewritten" in rows[0][0]


def test_deleted_document_is_removed_from_the_index(docs, tmp_path):
    db = tmp_path / "index.db"
    ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    (docs / "b.md").unlink()
    ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)

    connection = store.connect(db)
    try:
        assert "b.md" not in store.stats(connection)
    finally:
        connection.close()


def test_rebuild_starts_from_an_empty_index(docs, tmp_path):
    db = tmp_path / "index.db"
    ingest(StubBackend(), docs_dir=docs, db_path=db, verbose=False)
    rebuilt = ingest(StubBackend(), docs_dir=docs, db_path=db, rebuild=True, verbose=False)
    assert rebuilt["new"] == rebuilt["chunks"]


def test_missing_docs_directory_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest(StubBackend(), docs_dir=tmp_path / "nope", db_path=tmp_path / "i.db", verbose=False)
