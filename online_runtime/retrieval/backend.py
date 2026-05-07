from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from libs.common.models import Document, ExtractionArtifacts, SearchHit
from online_runtime.retrieval.base import BaseRetriever


class BaseRetrievalBackend(ABC):
    backend_id = "base"

    @abstractmethod
    def create_retriever(
        self,
        *,
        document: Document,
        extracted: ExtractionArtifacts,
        persist_index: bool = True,
        embedding_backend: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ) -> tuple[BaseRetriever, dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        *,
        query: str,
        top_k: int,
        item_types: list[str] | None = None,
        doc_id: str | None = None,
    ) -> list[SearchHit]:
        raise NotImplementedError
