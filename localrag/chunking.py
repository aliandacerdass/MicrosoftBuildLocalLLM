"""Split markdown documents into retrievable passages.

Structure first, size second: we cut on the author's own headings, because a
heading is where they already decided one topic ends and the next begins. Only
oversized sections get split further on character count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import config

# A markdown heading of level 2 or deeper. Level 1 is the document title, which
# we keep as context for every chunk rather than as a split point.
_HEADING = re.compile(r"^(#{2,6})\s+(.*)$", re.MULTILINE)
_TITLE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    """One retrievable passage, with enough provenance to cite it."""

    source: str
    heading: str
    ordinal: int
    text: str

    @property
    def label(self) -> str:
        """Human-readable citation label, e.g. ``01-foundry-local.md > Chunking``."""
        return f"{self.source} > {self.heading}" if self.heading else self.source


def _sections(markdown: str) -> list[tuple[str, str]]:
    """Split a document into ``(heading, body)`` pairs, in document order."""
    matches = list(_HEADING.finditer(markdown))
    if not matches:
        return [("", markdown.strip())]

    sections: list[tuple[str, str]] = []
    # The H1 title is dropped here because it is prepended to every chunk later;
    # keeping it would duplicate it in the first chunk.
    preamble = _TITLE.sub("", markdown[: matches[0].start()], count=1).strip()
    if preamble:
        sections.append(("", preamble))

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[match.end() : end].strip()
        sections.append((match.group(2).strip(), body))
    return sections


def _merge_short(sections: list[tuple[str, str]], min_chars: int) -> list[tuple[str, str]]:
    """Fold sections that are too short to stand alone into the following one.

    A two-line section makes a poor chunk: it rarely contains a whole answer, and
    it dilutes the index with near-empty vectors. The merged result is labelled
    with the heading of whichever section contributed the most text, so citations
    name the substantive section rather than the stub that triggered the merge.
    """

    def flush(pending: list[tuple[str, str]]) -> tuple[str, str]:
        heading = max(pending, key=lambda item: len(item[1]))[0]
        return heading, "\n\n".join(body for _, body in pending)

    merged: list[tuple[str, str]] = []
    pending: list[tuple[str, str]] = []

    for section in sections:
        pending.append(section)
        if sum(len(body) for _, body in pending) >= min_chars:
            merged.append(flush(pending))
            pending = []

    if pending:
        heading, body = flush(pending)
        if merged:
            # Nothing left to merge forward into, so append to the previous chunk.
            last_heading, last_body = merged[-1]
            merged[-1] = (last_heading, f"{last_body}\n\n{body}")
        else:
            merged.append((heading, body))
    return merged


def _split_long(body: str, target: int, overlap: int) -> list[str]:
    """Split an oversized section on paragraph boundaries, with a small overlap."""
    if len(body) <= target:
        return [body]

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current: list[str] = []
    length = 0

    for paragraph in paragraphs:
        if current and length + len(paragraph) > target:
            pieces.append("\n\n".join(current))
            tail = pieces[-1][-overlap:] if overlap else ""
            current = [tail, paragraph] if tail else [paragraph]
            length = len(tail) + len(paragraph)
        else:
            current.append(paragraph)
            length += len(paragraph)

    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_markdown(
    source: str,
    markdown: str,
    target_chars: int = config.CHUNK_TARGET_CHARS,
    overlap_chars: int = config.CHUNK_OVERLAP_CHARS,
    min_chars: int = config.CHUNK_MIN_CHARS,
) -> list[Chunk]:
    """Turn one markdown document into chunks ready for embedding."""
    title_match = _TITLE.search(markdown)
    title = title_match.group(1).strip() if title_match else source

    sections = _merge_short(_sections(markdown), min_chars)

    chunks: list[Chunk] = []
    for heading, body in sections:
        if not body.strip():
            continue
        for piece in _split_long(body, target_chars, overlap_chars):
            # The title and heading are prepended to the embedded text on
            # purpose: a passage that never repeats the topic name still needs to
            # match a question phrased with it.
            header = f"{title} - {heading}" if heading else title
            chunks.append(
                Chunk(
                    source=source,
                    heading=heading,
                    ordinal=len(chunks),
                    text=f"{header}\n\n{piece.strip()}",
                )
            )
    return chunks
