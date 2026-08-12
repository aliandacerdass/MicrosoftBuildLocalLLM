"""SQLite storage for chunks and their embedding vectors.

Vectors are kept as raw float32 bytes rather than JSON: about ten times smaller
and no parsing on read. The dimension is stored alongside them so a mismatched
embedding model fails loudly instead of returning nonsense.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .chunking import Chunk

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id           INTEGER PRIMARY KEY,
    source       TEXT    NOT NULL,
    heading      TEXT    NOT NULL DEFAULT '',
    ordinal      INTEGER NOT NULL,
    text         TEXT    NOT NULL,
    embedding    BLOB    NOT NULL,
    dim          INTEGER NOT NULL,
    content_hash TEXT    NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source);
"""

DTYPE = np.float32


@dataclass(frozen=True)
class StoredChunk:
    """A chunk as it comes back out of the database."""

    id: int
    source: str
    heading: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.source} > {self.heading}" if self.heading else self.source


def content_hash(source: str, text: str) -> str:
    """Identity of a chunk: same file and same text means same chunk."""
    return hashlib.sha256(f"{source}\x00{text}".encode("utf-8")).hexdigest()


def connect(db_path: Path) -> sqlite3.Connection:
    """Open the index, creating the file and schema if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)
    return connection


def existing_hashes(connection: sqlite3.Connection) -> set[str]:
    """Hashes already stored, so ingestion can skip unchanged text."""
    return {row[0] for row in connection.execute("SELECT content_hash FROM chunks")}


def insert_chunks(
    connection: sqlite3.Connection,
    chunks: list[Chunk],
    vectors: list[list[float]],
) -> int:
    """Insert chunks with their vectors. Returns the number of new rows."""
    if len(chunks) != len(vectors):
        raise ValueError(f"{len(chunks)} chunks but {len(vectors)} vectors")

    rows = []
    for chunk, vector in zip(chunks, vectors):
        array = np.asarray(vector, dtype=DTYPE)
        rows.append(
            (
                chunk.source,
                chunk.heading,
                chunk.ordinal,
                chunk.text,
                array.tobytes(),
                int(array.shape[0]),
                content_hash(chunk.source, chunk.text),
            )
        )

    cursor = connection.executemany(
        "INSERT OR IGNORE INTO chunks "
        "(source, heading, ordinal, text, embedding, dim, content_hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    connection.commit()
    return cursor.rowcount


def delete_source(connection: sqlite3.Connection, source: str) -> int:
    """Remove every chunk that came from one file, so it can be re-ingested."""
    cursor = connection.execute("DELETE FROM chunks WHERE source = ?", (source,))
    connection.commit()
    return cursor.rowcount


def load_index(connection: sqlite3.Connection) -> tuple[list[StoredChunk], np.ndarray]:
    """Load every chunk and return its vectors as one L2-normalised matrix.

    Normalising here means each later search is a plain dot product instead of a
    full cosine calculation.
    """
    rows = connection.execute(
        "SELECT id, source, heading, text, embedding, dim FROM chunks ORDER BY id"
    ).fetchall()

    if not rows:
        return [], np.zeros((0, 0), dtype=DTYPE)

    dims = {row[5] for row in rows}
    if len(dims) > 1:
        raise ValueError(
            f"Index contains vectors of different dimensions ({sorted(dims)}). "
            "It was built with more than one embedding model - delete the database "
            "and re-run ingestion."
        )

    chunks = [StoredChunk(id=r[0], source=r[1], heading=r[2], text=r[3]) for r in rows]
    matrix = np.vstack([np.frombuffer(r[4], dtype=DTYPE) for r in rows])

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return chunks, matrix / norms


def stats(connection: sqlite3.Connection) -> dict[str, int]:
    """Chunk count per source file, for a quick look at what was ingested."""
    return dict(
        connection.execute(
            "SELECT source, COUNT(*) FROM chunks GROUP BY source ORDER BY source"
        ).fetchall()
    )
