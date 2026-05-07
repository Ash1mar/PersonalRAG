from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from libs.common.config import get_settings
from libs.common.models import (
    Block,
    ExtractionArtifacts,
    Expression,
    KnowledgeObject,
    LocalKnowledgeBaseIndex,
    SearchHit,
)
from libs.embedding.embedder import BaseEmbedder, HashEmbedder, cosine_similarity, get_embedder


class LocalKnowledgeBase:
    def __init__(self, kb_dir: Path | None = None) -> None:
        settings = get_settings()
        self.kb_dir = kb_dir or settings.local_kb_dir
        self.kb_dir.mkdir(parents=True, exist_ok=True)

    def build_index(
        self,
        *,
        document,
        extracted: ExtractionArtifacts,
        persist: bool = True,
        embedding_backend: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ) -> LocalKnowledgeBaseIndex:
        block_texts = [_block_repr(block) for block in document.blocks]
        ko_texts = [_ko_repr(item) for item in (extracted.facts + extracted.experiences)]
        expression_texts = [_expression_repr(item) for item in extracted.expressions]

        block_vectors, resolved_embedding_backend = self._embed_texts(
            block_texts,
            preferred_backend=embedding_backend,
            provider_name=embedding_provider,
            model_name=embedding_model,
        )
        ko_vectors, _ = self._embed_texts(ko_texts, preferred_backend=resolved_embedding_backend)
        expression_vectors, _ = self._embed_texts(expression_texts, preferred_backend=resolved_embedding_backend)

        index = LocalKnowledgeBaseIndex(
            doc_id=document.meta.doc_id,
            source_path=document.meta.source_path,
            built_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            extraction_method=extracted.summary.method,
            chat_model=extracted.summary.chat_model,
            embedding_backend=resolved_embedding_backend,
            blocks=document.blocks,
            block_vectors=block_vectors,
            knowledge_objects=extracted.facts + extracted.experiences,
            ko_vectors=ko_vectors,
            expressions=extracted.expressions,
            expression_vectors=expression_vectors,
        )
        if persist:
            self.save_index(index)
        return index

    def save_index(self, index: LocalKnowledgeBaseIndex) -> Path:
        path = self._path_for_doc(index.doc_id)
        path.write_text(index.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_index(self, doc_id: str) -> LocalKnowledgeBaseIndex:
        path = self._path_for_doc(doc_id)
        if not path.exists():
            raise ValueError(f"Local knowledge base index not found for doc_id={doc_id}")
        return LocalKnowledgeBaseIndex.model_validate_json(path.read_text(encoding="utf-8"))

    def load_all_indices(self) -> list[LocalKnowledgeBaseIndex]:
        indices: list[LocalKnowledgeBaseIndex] = []
        for path in sorted(self.kb_dir.glob("*.json")):
            indices.append(LocalKnowledgeBaseIndex.model_validate_json(path.read_text(encoding="utf-8")))
        return indices

    def search(
        self,
        *,
        query: str,
        top_k: int,
        item_types: list[str] | None = None,
        doc_id: str | None = None,
    ) -> list[SearchHit]:
        indices = [self.load_index(doc_id)] if doc_id else self.load_all_indices()
        hits: list[SearchHit] = []
        for index in indices:
            hits.extend(self._search_index(index=index, query=query, top_k=top_k, item_types=item_types))
        return sorted(hits, key=lambda item: item.score, reverse=True)[:top_k]

    def _search_index(
        self,
        *,
        index: LocalKnowledgeBaseIndex,
        query: str,
        top_k: int,
        item_types: list[str] | None,
    ) -> list[SearchHit]:
        embedder = _embedder_for_backend(index.embedding_backend)
        query_vector = embedder.embed_texts([query])[0]
        hits: list[SearchHit] = []

        if not item_types or "block" in item_types:
            hits.extend(_rank_blocks(index.blocks, index.block_vectors, query_vector))
        if not item_types or any(item_type in item_types for item_type in {"fact", "experience"}):
            hits.extend(_rank_kos(index.knowledge_objects, index.ko_vectors, query_vector, item_types))
        if not item_types or "expression" in item_types:
            hits.extend(_rank_expressions(index.expressions, index.expression_vectors, query_vector))
        return sorted(hits, key=lambda item: item.score, reverse=True)[:top_k]

    def _embed_texts(
        self,
        texts: list[str],
        preferred_backend: str | None = None,
        provider_name: str | None = None,
        model_name: str | None = None,
    ) -> tuple[list[list[float]], str]:
        if not texts:
            return [], preferred_backend or HashEmbedder().backend_name
        embedder = get_embedder(preferred_backend, provider_name=provider_name, model_name=model_name)
        try:
            return embedder.embed_texts(texts), embedder.backend_name
        except Exception:
            fallback = HashEmbedder()
            return fallback.embed_texts(texts), fallback.backend_name

    def _path_for_doc(self, doc_id: str) -> Path:
        return self.kb_dir / f"{doc_id}.json"


def _embedder_for_backend(backend: str) -> BaseEmbedder:
    return get_embedder(backend)


def _block_repr(block: Block) -> str:
    headings = " > ".join(block.heading_path)
    return f"{headings}\n{block.text}"


def _ko_repr(item: KnowledgeObject) -> str:
    headings = " > ".join(item.source_headings)
    extras = [part for part in [item.condition, item.action] if part]
    return f"{headings}\n{item.canonical}\n{' '.join(extras)}"


def _expression_repr(item: Expression) -> str:
    headings = " > ".join(item.source_headings)
    topic = item.topic or ""
    return f"{headings}\n{topic}\n{item.canonical}"


def _rank_blocks(blocks: list[Block], vectors: list[list[float]], query_vector: list[float]) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for block, vector in zip(blocks, vectors):
        hits.append(
            SearchHit(
                item_id=block.block_id,
                item_type="block",
                score=cosine_similarity(query_vector, vector),
                doc_id=block.doc_id,
                text=block.text,
                source_headings=block.heading_path,
                metadata={"page_no": block.page_no, "order": block.order},
            )
        )
    return hits


def _rank_kos(
    kos: list[KnowledgeObject],
    vectors: list[list[float]],
    query_vector: list[float],
    item_types: list[str] | None,
) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for item, vector in zip(kos, vectors):
        if item_types and item.k_type not in item_types:
            continue
        hits.append(
            SearchHit(
                item_id=item.kid,
                item_type=item.k_type,
                score=cosine_similarity(query_vector, vector),
                doc_id=item.evidence[0].doc_id if item.evidence else "",
                text=item.canonical,
                source_headings=item.source_headings,
                metadata={"topic": item.topic, "confidence": item.confidence},
            )
        )
    return hits


def _rank_expressions(expressions: list[Expression], vectors: list[list[float]], query_vector: list[float]) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for item, vector in zip(expressions, vectors):
        hits.append(
            SearchHit(
                item_id=item.expr_id,
                item_type="expression",
                score=cosine_similarity(query_vector, vector),
                doc_id=item.evidence[0].doc_id if item.evidence else "",
                text=item.canonical,
                source_headings=item.source_headings,
                metadata={"topic": item.topic, "confidence": item.confidence},
            )
        )
    return hits
