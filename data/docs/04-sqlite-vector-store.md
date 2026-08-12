# Storing Chunks and Vectors in SQLite

SQLite is a serverless, self-contained SQL database: the whole database is one file on disk,
and the engine is a library linked into your process. Python ships with it built in, so
there is nothing to install and nothing to run.

> Our own summary. Background: https://www.sqlite.org/whentouse.html

## Why SQLite for a local RAG assistant

The requirements for this project are modest and specific: persist a few hundred text chunks
with their vectors, survive a restart, and be queryable. SQLite meets all of them with zero
operational cost.

- **No server process.** Nothing to start before the app, nothing to leave running.
- **One file.** Backing up the index is `cp index.db backup.db`. Deleting it and re-running
  ingestion is a full reset.
- **In the standard library.** `import sqlite3` — no dependency, no version conflict.
- **Real SQL.** When you want to inspect what got ingested, you write a `SELECT` instead of
  writing a debugging script.

The alternative — keeping everything in a Python list in memory — means re-embedding the
entire corpus on every start. That is minutes of waiting for data that has not changed.

## The schema

```sql
CREATE TABLE chunks (
    id           INTEGER PRIMARY KEY,
    source       TEXT NOT NULL,   -- file name, used for citation
    heading      TEXT,            -- section heading, also used for citation
    ordinal      INTEGER NOT NULL,-- position within the source file
    text         TEXT NOT NULL,   -- the chunk itself
    embedding    BLOB NOT NULL,   -- float32 vector, raw bytes
    dim          INTEGER NOT NULL,-- vector length, sanity check
    content_hash TEXT NOT NULL    -- hash of the chunk text, for idempotent re-ingest
);
```

`source` and `heading` are not decoration: they are what makes citation possible. If you do
not store where a chunk came from, the assistant cannot tell the user where the answer came
from, and an uncheckable answer is a weak answer.

## Storing vectors as BLOBs

SQLite has no vector type. Two reasonable encodings:

- **JSON text** — human-readable, easy to debug, but roughly 10x larger and requires parsing
  on every read.
- **Raw float32 bytes** — compact and fast to load.

This project uses raw bytes:

```python
blob = np.asarray(vector, dtype=np.float32).tobytes()          # write
vector = np.frombuffer(blob, dtype=np.float32)                 # read
```

A 1024-dimension float32 vector is 4096 bytes. A thousand chunks is about 4 MB of vectors —
small enough to load the entire index into memory at startup, which is exactly what the
retrieval step does.

Two things to be careful about: always pin the dtype (`float32` on write *and* read, or you
get garbage), and store the dimension so a mismatch fails loudly instead of silently
returning nonsense.

## Idempotent ingestion

Re-running ingestion should not duplicate rows or waste time re-embedding text that has not
changed. The `content_hash` column makes that cheap: hash the chunk text, and if a row with
that hash already exists, skip it.

This matters more than it sounds. During development you re-run ingestion constantly, and at
roughly a second per batch of embeddings, an ingestion that skips unchanged content is the
difference between a tight edit loop and a slow one.

## Inspecting the index

Because it is real SQL, debugging is easy:

```sql
SELECT COUNT(*) FROM chunks;                          -- did ingestion run?
SELECT source, COUNT(*) FROM chunks GROUP BY source;  -- which file dominates?
SELECT DISTINCT dim FROM chunks;                      -- one embedding model, or two?
SELECT source, heading, substr(text, 1, 80) FROM chunks LIMIT 5;
```

That last query answers "what does a chunk actually look like?", which is the first question
worth asking when retrieval results are disappointing.

## Limits

SQLite cannot do vector similarity itself — there is no `ORDER BY cosine(...)` unless you
register a custom function or load an extension such as `sqlite-vec`. This project keeps it
simple: SQLite stores, numpy searches. At this scale the entire index fits in memory and a
brute-force scan is instant, so pushing the search into the database would add complexity
without buying speed.
