from __future__ import annotations

import hashlib
import math
import re

from libs.common.config import get_settings
from libs.llm.ollama_client import OllamaClient


class BaseEmbedder:
    backend_name = "base"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OllamaEmbedder(BaseEmbedder):
    backend_name = "ollama"

    def __init__(self, model: str | None = None) -> None:
        self.client = OllamaClient()
        self.model = model or get_settings().embedding_model
        self.backend_name = f"ollama:{self.model}"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts, model=self.model)


class HashEmbedder(BaseEmbedder):
    backend_name = "hash:256"

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions
        self.backend_name = f"hash:{dimensions}"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embed(text, self.dimensions) for text in texts]


def get_embedder(preferred_backend: str | None = None, provider_name: str | None = None, model_name: str | None = None) -> BaseEmbedder:
    settings = get_settings()
    if preferred_backend:
        backend = preferred_backend
    else:
        resolved_provider = provider_name or settings.embedding_provider
        resolved_model = model_name or settings.embedding_model
        backend = f"{resolved_provider}:{resolved_model}" if resolved_model else resolved_provider
    if backend.startswith("hash:"):
        dimensions = int(backend.split(":", maxsplit=1)[1])
        return HashEmbedder(dimensions=dimensions)
    if backend.startswith("ollama:"):
        model = backend.split(":", maxsplit=1)[1]
        return OllamaEmbedder(model=model)
    if backend == "ollama":
        return OllamaEmbedder(model=model_name or settings.embedding_model)
    raise ValueError(f"Unsupported embedding backend: {backend}")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _hash_embed(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    tokens = re.findall(r"\w+|[\u4e00-\u9fff]", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % dimensions
        sign = 1.0 if int(digest[8:16], 16) % 2 == 0 else -1.0
        vector[index] += sign
    return vector
