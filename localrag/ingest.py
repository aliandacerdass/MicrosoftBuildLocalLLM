"""Build the index: markdown files -> chunks -> embeddings -> SQLite.

Run with ``python -m localrag.ingest``. Safe to re-run: chunks whose text has not
changed are skipped instead of being re-embedded.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import config, store
from .backends import Backend
from .chunking import Chunk, chunk_markdown

EMBED_BATCH = 16


def collect_chunks(docs_dir: Path) -> list[Chunk]:
    """Chunk every markdown file in the knowledge base directory."""
    files = sorted(docs_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No markdown files found in {docs_dir}")

    chunks: list[Chunk] = []
    for path in files:
        chunks.extend(chunk_markdown(path.name, path.read_text(encoding="utf-8")))
    return chunks


def ingest(
    backend: Backend,
    docs_dir: Path = config.DOCS_DIR,
    db_path: Path = config.DB_PATH,
    rebuild: bool = False,
    verbose: bool = True,
) -> dict[str, int]:
    """Ingest the knowledge base. Returns counts for reporting and tests."""
    if rebuild and db_path.exists():
        db_path.unlink()

    chunks = collect_chunks(docs_dir)
    connection = store.connect(db_path)

    try:
        known = store.existing_hashes(connection)
        pending = [c for c in chunks if store.content_hash(c.source, c.text) not in known]

        if verbose:
            print(f"{len(chunks)} chunks in {docs_dir}, {len(pending)} new")

        inserted = 0
        started = time.time()
        for start in range(0, len(pending), EMBED_BATCH):
            batch = pending[start : start + EMBED_BATCH]
            vectors = backend.embed([c.text for c in batch])
            inserted += store.insert_chunks(connection, batch, vectors)
            if verbose:
                done = min(start + EMBED_BATCH, len(pending))
                print(f"\r  embedded {done}/{len(pending)}", end="", flush=True)

        if verbose and pending:
            print(f"\n  done in {time.time() - started:.1f}s")

        totals = store.stats(connection)
        if verbose:
            for source, count in totals.items():
                print(f"  {source:<44} {count:>3} chunks")
            print(f"Index: {db_path} ({sum(totals.values())} chunks total)")

        return {"chunks": len(chunks), "new": len(pending), "inserted": inserted}
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local RAG index.")
    parser.add_argument("--docs", type=Path, default=config.DOCS_DIR)
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="delete the existing index first (needed after changing the embedding model)",
    )
    args = parser.parse_args(argv)

    from .backends import FoundryBackend

    backend = FoundryBackend()
    try:
        ingest(backend, docs_dir=args.docs, db_path=args.db, rebuild=args.rebuild)
    finally:
        backend.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
