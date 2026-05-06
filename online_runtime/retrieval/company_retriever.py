from libs.common.models import Block, KnowledgeObject
from online_runtime.retrieval.base import BaseRetriever


class CompanyRetriever(BaseRetriever):
    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        raise NotImplementedError("CompanyRetriever is a placeholder. Wire the internal knowledge API here.")

    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        raise NotImplementedError("CompanyRetriever is a placeholder. Wire the internal knowledge API here.")

