from __future__ import annotations

from libs.common.models import Block, Expression, KnowledgeObject
from online_runtime.retrieval.base import BaseRetriever


class CompositeRetriever(BaseRetriever):
    def __init__(self, retrievers: list[BaseRetriever]) -> None:
        self.retrievers = retrievers

    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        merged: list[Block] = []
        seen: set[str] = set()
        per_backend_k = max(top_k, 5)
        for retriever in self.retrievers:
            for block in retriever.retrieve_blocks(query=query, filters=filters, top_k=per_backend_k):
                if block.block_id in seen:
                    continue
                seen.add(block.block_id)
                merged.append(block)
                if len(merged) >= top_k:
                    return merged
        return merged

    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        merged: list[KnowledgeObject] = []
        seen: set[str] = set()
        per_backend_k = max(top_k, 5)
        for retriever in self.retrievers:
            for item in retriever.retrieve_kos(query=query, filters=filters, top_k=per_backend_k, allowed_types=allowed_types):
                if item.kid in seen:
                    continue
                seen.add(item.kid)
                merged.append(item)
                if len(merged) >= top_k:
                    return merged
        return merged

    def retrieve_expressions(self, query: str, filters: dict, top_k: int) -> list[Expression]:
        merged: list[Expression] = []
        seen: set[str] = set()
        per_backend_k = max(top_k, 5)
        for retriever in self.retrievers:
            for item in retriever.retrieve_expressions(query=query, filters=filters, top_k=per_backend_k):
                if item.expr_id in seen:
                    continue
                seen.add(item.expr_id)
                merged.append(item)
                if len(merged) >= top_k:
                    return merged
        return merged
