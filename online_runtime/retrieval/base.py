from __future__ import annotations

from abc import ABC, abstractmethod

from libs.common.models import Block, KnowledgeObject


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        raise NotImplementedError

    @abstractmethod
    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        raise NotImplementedError

