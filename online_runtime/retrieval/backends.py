from __future__ import annotations

from libs.common.models import Document, ExtractionArtifacts, SearchHit
from online_runtime.retrieval.backend import BaseRetrievalBackend
from online_runtime.retrieval.company_retriever import CompanyRetriever
from online_runtime.retrieval.local_kb import LocalKnowledgeBase
from online_runtime.retrieval.local_keyword_retriever import LocalKeywordRetriever
from online_runtime.retrieval.local_retriever import LocalRetriever


class LocalVectorBackend(BaseRetrievalBackend):
    backend_id = "local_vector"

    def __init__(self) -> None:
        self.knowledge_base = LocalKnowledgeBase()

    def create_retriever(
        self,
        *,
        document: Document,
        extracted: ExtractionArtifacts,
        persist_index: bool = True,
        embedding_backend: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ):
        index = self.knowledge_base.build_index(
            document=document,
            extracted=extracted,
            persist=persist_index,
            embedding_backend=embedding_backend,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        return LocalRetriever(index=index), {"backend": self.backend_id, "embedding_backend": index.embedding_backend}

    def search(
        self,
        *,
        query: str,
        top_k: int,
        item_types: list[str] | None = None,
        doc_id: str | None = None,
    ) -> list[SearchHit]:
        hits = self.knowledge_base.search(query=query, top_k=top_k, item_types=item_types, doc_id=doc_id)
        return [
            hit.model_copy(update={"metadata": {**hit.metadata, "backend": self.backend_id}})
            for hit in hits
        ]


class LocalKeywordBackend(BaseRetrievalBackend):
    backend_id = "local_keyword"

    def __init__(self) -> None:
        self.knowledge_base = LocalKnowledgeBase()

    def create_retriever(
        self,
        *,
        document: Document,
        extracted: ExtractionArtifacts,
        persist_index: bool = True,
        embedding_backend: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ):
        index = self.knowledge_base.build_index(
            document=document,
            extracted=extracted,
            persist=persist_index,
            embedding_backend=embedding_backend,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        return LocalKeywordRetriever(index=index), {"backend": self.backend_id, "embedding_backend": index.embedding_backend}

    def search(
        self,
        *,
        query: str,
        top_k: int,
        item_types: list[str] | None = None,
        doc_id: str | None = None,
    ) -> list[SearchHit]:
        indices = [self.knowledge_base.load_index(doc_id)] if doc_id else self.knowledge_base.load_all_indices()
        hits: list[SearchHit] = []
        for index in indices:
            retriever = LocalKeywordRetriever(index)
            hits.extend(_hits_from_keyword_retriever(retriever, query, top_k, item_types))
        return sorted(hits, key=lambda item: item.score, reverse=True)[:top_k]


class CompanyBackend(BaseRetrievalBackend):
    backend_id = "company"

    def create_retriever(
        self,
        *,
        document: Document,
        extracted: ExtractionArtifacts,
        persist_index: bool = True,
        embedding_backend: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ):
        return CompanyRetriever(), {"backend": self.backend_id}

    def search(
        self,
        *,
        query: str,
        top_k: int,
        item_types: list[str] | None = None,
        doc_id: str | None = None,
    ) -> list[SearchHit]:
        raise NotImplementedError("Company backend is a placeholder. Wire the internal retrieval API here.")


def _hits_from_keyword_retriever(retriever: LocalKeywordRetriever, query: str, top_k: int, item_types: list[str] | None) -> list[SearchHit]:
    hits: list[SearchHit] = []
    if not item_types or "block" in item_types:
        for rank, block in enumerate(retriever.retrieve_blocks(query=query, filters={}, top_k=top_k), start=1):
            hits.append(
                SearchHit(
                    item_id=block.block_id,
                    item_type="block",
                    score=_keyword_rank_score(rank),
                    doc_id=block.doc_id,
                    text=block.text,
                    source_headings=block.heading_path,
                    metadata={"backend": "local_keyword"},
                )
            )
    if not item_types or any(item_type in item_types for item_type in {"fact", "experience"}):
        for rank, item in enumerate(retriever.retrieve_kos(query=query, filters={}, top_k=top_k, allowed_types=item_types), start=1):
            hits.append(
                SearchHit(
                    item_id=item.kid,
                    item_type=item.k_type,
                    score=_keyword_rank_score(rank),
                    doc_id=item.evidence[0].doc_id if item.evidence else "",
                    text=item.canonical,
                    source_headings=item.source_headings,
                    metadata={"backend": "local_keyword"},
                )
            )
    if not item_types or "expression" in item_types:
        for rank, item in enumerate(retriever.retrieve_expressions(query=query, filters={}, top_k=top_k), start=1):
            hits.append(
                SearchHit(
                    item_id=item.expr_id,
                    item_type="expression",
                    score=_keyword_rank_score(rank),
                    doc_id=item.evidence[0].doc_id if item.evidence else "",
                    text=item.canonical,
                    source_headings=item.source_headings,
                    metadata={"backend": "local_keyword"},
                )
            )
    return hits


def _keyword_rank_score(rank: int) -> float:
    return max(0.1, 0.45 - (rank - 1) * 0.05)
