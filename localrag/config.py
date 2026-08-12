"""Central configuration. Every value can be overridden with an environment variable."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Models -----------------------------------------------------------------
# Foundry Local caches downloaded models per app name, so every entry point in
# this project must use the same one or models get downloaded again.
APP_NAME = os.getenv("LOCALRAG_APP_NAME", "microsoft-build-local-llm")

# Aliases come from the Foundry Local catalog. Run `python -m localrag.models`
# to see what is available on your machine before changing these.
CHAT_MODEL = os.getenv("LOCALRAG_CHAT_MODEL", "qwen2.5-1.5b")
EMBED_MODEL = os.getenv("LOCALRAG_EMBED_MODEL", "qwen3-embedding-0.6b")

# --- Paths ------------------------------------------------------------------
DOCS_DIR = Path(os.getenv("LOCALRAG_DOCS", ROOT / "data" / "docs"))
DB_PATH = Path(os.getenv("LOCALRAG_DB", ROOT / "data" / "index" / "chunks.db"))

# --- Chunking ---------------------------------------------------------------
# Target size of a chunk in characters: large enough to answer a question on its
# own, small enough to be about a single topic.
CHUNK_TARGET_CHARS = int(os.getenv("LOCALRAG_CHUNK_CHARS", "800"))
# Carried from the end of one chunk into the next, so a fact sitting on a split
# boundary stays retrievable from both sides.
CHUNK_OVERLAP_CHARS = int(os.getenv("LOCALRAG_CHUNK_OVERLAP", "100"))
# Sections shorter than this are merged into the next one instead of becoming
# their own chunk.
CHUNK_MIN_CHARS = int(os.getenv("LOCALRAG_CHUNK_MIN", "200"))

# --- Retrieval --------------------------------------------------------------
TOP_K = int(os.getenv("LOCALRAG_TOP_K", "3"))
# If the best chunk scores below this, we refuse without calling the model at
# all. Deliberately loose: a naturally phrased question can retrieve exactly the
# right passage and still score around 0.51, so a tight threshold refuses real
# questions. Measured at 0.45 the out-of-scope questions are still refused 5/5 -
# the ones that get past the threshold are refused by the model itself, which is
# what the system prompt is for. See docs/EVALUATION.md.
MIN_SCORE = float(os.getenv("LOCALRAG_MIN_SCORE", "0.45"))

# --- Generation -------------------------------------------------------------
# 400 was low enough to cut a verbose answer off mid-sentence, which reads as a
# bug. Most answers are far shorter, so raising it costs time only on the long ones.
MAX_TOKENS = int(os.getenv("LOCALRAG_MAX_TOKENS", "600"))
TEMPERATURE = float(os.getenv("LOCALRAG_TEMPERATURE", "0.2"))

REFUSAL_MESSAGE = (
    "I don't have that information in my knowledge base."
)
