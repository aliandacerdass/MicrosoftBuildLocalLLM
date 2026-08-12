from localrag.chunking import chunk_markdown

DOC = """# Foundry Local

Intro paragraph that sits before any heading and is long enough to matter for the
merge rule, so it should survive as its own section rather than being folded away.
It carries several sentences of prose to comfortably clear the minimum size.

## Execution providers

An execution provider is the backend that runs the model's math. It can be a CPU,
a GPU stack, or an NPU, and the SDK can discover which ones the machine supports
and download the ones that are missing before any model is loaded.

## Tiny

Too short.

## The catalog

The catalog lists every model Foundry Local knows how to fetch. Each entry has an
alias, a concrete model id, a context length, and a capability string that says
whether the model does embeddings, reasoning, or tool calling.
"""


def test_splits_on_headings():
    chunks = chunk_markdown("doc.md", DOC)
    headings = [c.heading for c in chunks]
    assert "Execution providers" in headings
    assert "The catalog" in headings


def test_title_and_heading_are_prepended_to_text():
    # A passage that never repeats the topic name still has to match a question
    # phrased with it, so the header goes into the embedded text.
    chunks = chunk_markdown("doc.md", DOC)
    catalog = next(c for c in chunks if c.heading == "The catalog")
    assert catalog.text.startswith("Foundry Local - The catalog")


def test_short_section_is_merged_not_kept_alone():
    chunks = chunk_markdown("doc.md", DOC)
    assert "Too short." not in [c.text.split("\n\n", 1)[-1] for c in chunks]
    assert any("Too short." in c.text for c in chunks)


def test_long_section_is_split_with_overlap():
    paragraph = "word " * 60  # ~300 chars
    body = "\n\n".join(paragraph.strip() for _ in range(6))
    chunks = chunk_markdown("long.md", f"# T\n\n## S\n\n{body}", target_chars=400, overlap_chars=50)
    assert len(chunks) > 1
    # The tail of one chunk reappears at the head of the next.
    first_body = chunks[0].text.split("\n\n", 1)[1]
    assert first_body[-20:] in chunks[1].text


def test_ordinals_are_unique_and_sequential():
    chunks = chunk_markdown("doc.md", DOC)
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))


def test_document_without_headings_still_produces_a_chunk():
    chunks = chunk_markdown("flat.md", "Just one paragraph of text, no headings at all.")
    assert len(chunks) == 1
    assert chunks[0].heading == ""


def test_label_is_citable():
    chunks = chunk_markdown("doc.md", DOC)
    catalog = next(c for c in chunks if c.heading == "The catalog")
    assert catalog.label == "doc.md > The catalog"
