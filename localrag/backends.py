"""Model backends.

The application only ever talks to a backend through two methods, ``embed`` and
``stream_chat``. ``FoundryBackend`` is the real one; ``StubBackend`` is a
deterministic fake so the pipeline can be tested without downloading gigabytes of
model weights.
"""

from __future__ import annotations

import hashlib
from typing import Iterator, Protocol

from . import config

Message = dict[str, str]


class Backend(Protocol):
    """What the rest of the application needs from a model provider."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    def stream_chat(self, messages: list[Message]) -> Iterator[str]:
        """Yield the answer token by token."""


class FoundryBackend:
    """Runs models on-device through Microsoft Foundry Local.

    Models are loaded lazily: ingestion never pays for the chat model, and the
    Q&A path never pays for a model it does not use.
    """

    def __init__(
        self,
        chat_alias: str = config.CHAT_MODEL,
        embed_alias: str = config.EMBED_MODEL,
        app_name: str = config.APP_NAME,
    ) -> None:
        from foundry_local_sdk import Configuration, FoundryLocalManager

        FoundryLocalManager.initialize(Configuration(app_name=app_name))
        self._manager = FoundryLocalManager.instance
        self._manager.download_and_register_eps()

        self._chat_alias = chat_alias
        self._embed_alias = embed_alias
        self._chat_model = None
        self._embed_model = None
        self._chat_client = None
        self._embed_client = None

    # -- model management ---------------------------------------------------

    def _load(self, alias: str, on_progress=None):
        model = self._manager.catalog.get_model(alias)
        if model is None:
            available = ", ".join(sorted(m.alias for m in self._manager.catalog.list_models()))
            raise ValueError(f"Model alias {alias!r} is not in the catalog. Available: {available}")
        if not model.is_cached and on_progress:
            on_progress(alias)
        model.download()
        model.load()
        return model

    def _embedding_client(self):
        if self._embed_client is None:
            self._embed_model = self._load(
                self._embed_alias,
                lambda a: print(f"Downloading embedding model {a} (one-time, several minutes)..."),
            )
            self._embed_client = self._embed_model.get_embedding_client()
        return self._embed_client

    def _chat(self):
        if self._chat_client is None:
            self._chat_model = self._load(
                self._chat_alias,
                lambda a: print(f"Downloading chat model {a} (one-time, several minutes)..."),
            )
            client = self._chat_model.get_chat_client()
            client.settings.temperature = config.TEMPERATURE
            client.settings.max_tokens = config.MAX_TOKENS
            self._chat_client = client
        return self._chat_client

    # -- Backend protocol ---------------------------------------------------

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._embedding_client().generate_embeddings(list(texts))
        return [item.embedding for item in response.data]

    def stream_chat(self, messages: list[Message]) -> Iterator[str]:
        for chunk in self._chat().complete_streaming_chat(messages):
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def close(self) -> None:
        """Unload whatever was loaded. Safe to call more than once."""
        for model in (self._chat_model, self._embed_model):
            if model is not None and model.is_loaded:
                model.unload()
        self._chat_model = self._embed_model = None
        self._chat_client = self._embed_client = None


class StubBackend:
    """Deterministic fake backend for tests.

    Embeddings are derived from a hash of the words in the text, so texts that
    share vocabulary land close together. That is enough to exercise chunking,
    storage, retrieval and prompt assembly without any model download - but it is
    NOT semantic search, so it can never stand in for a real end-to-end check.
    """

    DIM = 64

    def __init__(self, reply: str = "Stub answer [1]") -> None:
        self.reply = reply
        self.seen_messages: list[list[Message]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.DIM
        for word in text.lower().split():
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            vector[digest[0] % self.DIM] += 1.0
        if not any(vector):
            vector[0] = 1.0
        return vector

    def stream_chat(self, messages: list[Message]) -> Iterator[str]:
        self.seen_messages.append(messages)
        for index, word in enumerate(self.reply.split(" ")):
            yield word if index == 0 else f" {word}"

    def close(self) -> None:
        return None
