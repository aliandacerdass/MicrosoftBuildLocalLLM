"""Streamlit interface. Run from the repository root with ``streamlit run app.py``."""

from __future__ import annotations

import streamlit as st

from . import config
from .backends import FoundryBackend
from .rag import Assistant


@st.cache_resource(show_spinner="Loading local models (first run downloads them)...")
def get_assistant() -> Assistant:
    """One assistant per session: models stay loaded between questions."""
    return Assistant.from_index(FoundryBackend())


def main() -> None:
    st.set_page_config(page_title="Local RAG Assistant", page_icon="📚", layout="centered")
    st.title("📚 Local RAG Assistant")
    st.caption(
        "Retrieval and answer generation run on this device with Microsoft Foundry Local."
    )

    try:
        assistant = get_assistant()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    with st.sidebar:
        st.subheader("Configuration")
        st.write(f"**Chat model:** `{config.CHAT_MODEL}`")
        st.write(f"**Embedding model:** `{config.EMBED_MODEL}`")
        st.write(f"**Indexed chunks:** {len(assistant.retriever)}")
        assistant.top_k = st.slider("Passages retrieved (top-k)", 1, 8, config.TOP_K)
        assistant.min_score = st.slider(
            "Refusal threshold", 0.0, 1.0, config.MIN_SCORE, 0.01,
            help="If the best passage scores below this, the assistant refuses without calling the model.",
        )

    question = st.chat_input("Ask a question about the knowledge base")
    if not question:
        st.info("Try: *What is an execution provider?* or *Why store vectors as float32 bytes?*")
        return

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        streamed: list[str] = []

        def on_token(token: str) -> None:
            streamed.append(token)
            placeholder.markdown("".join(streamed) + "▌")

        answer = assistant.ask(question, on_token=on_token)
        placeholder.markdown(answer.text)

        st.caption(
            f"{answer.retrieval_ms:.0f} ms retrieval · {answer.generation_ms:.0f} ms generation"
        )

        if answer.sources:
            with st.expander(f"Sources ({len(answer.sources)})"):
                for source in answer.sources:
                    st.markdown(f"**[{source.number}] {source.label}** — similarity {source.score:.3f}")
                    st.text(source.text)


if __name__ == "__main__":
    main()
