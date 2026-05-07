from __future__ import annotations

from libs.common.models import Block, Expression, KnowledgeObject, LocalKnowledgeBaseIndex
from libs.embedding.embedder import cosine_similarity, get_embedder
from online_runtime.retrieval.base import BaseRetriever


class LocalRetriever(BaseRetriever):
    def __init__(self, index: LocalKnowledgeBaseIndex) -> None:
        self.index = index
        self.embedder = get_embedder(index.embedding_backend)

    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        query_vector = self.embedder.embed_texts([query])[0]
        candidates = _filter_blocks(self.index.blocks, self.index.block_vectors, filters)
        ranked = sorted(
            candidates,
            key=lambda item: _score_block(item[0], item[1], query, query_vector, filters),
            reverse=True,
        )
        return [block for block, _ in ranked[:top_k]]

    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        query_vector = self.embedder.embed_texts([query])[0]
        candidates = _filter_kos(self.index.knowledge_objects, self.index.ko_vectors, filters, allowed_types)
        ranked = sorted(
            candidates,
            key=lambda item: _score_ko(item[0], item[1], query, query_vector, filters),
            reverse=True,
        )
        return [ko for ko, _ in ranked[:top_k]]

    def retrieve_expressions(self, query: str, filters: dict, top_k: int) -> list[Expression]:
        query_vector = self.embedder.embed_texts([query])[0]
        candidates = _filter_expressions(self.index.expressions, self.index.expression_vectors, filters)
        ranked = sorted(
            candidates,
            key=lambda item: _score_expression(item[0], item[1], query, query_vector, filters),
            reverse=True,
        )
        return [expression for expression, _ in ranked[:top_k]]


def _score_block(block: Block, vector: list[float], query: str, query_vector: list[float], filters: dict) -> float:
    score = cosine_similarity(query_vector, vector)
    score += _heading_stage_boost(block.heading_path, filters)
    score += _keyword_overlap(query, block.text)
    return score


def _score_ko(item: KnowledgeObject, vector: list[float], query: str, query_vector: list[float], filters: dict) -> float:
    score = cosine_similarity(query_vector, vector)
    score += _heading_stage_boost(item.source_headings, filters)
    score += _keyword_overlap(query, item.canonical)
    return score


def _score_expression(item: Expression, vector: list[float], query: str, query_vector: list[float], filters: dict) -> float:
    score = cosine_similarity(query_vector, vector)
    score += _heading_stage_boost(item.source_headings, filters)
    score += _keyword_overlap(query, item.canonical)
    return score


def _heading_stage_boost(headings: list[str], filters: dict) -> float:
    stage_terms = filters.get("stage") or []
    heading_text = " ".join(headings)
    return 0.2 if any(term in heading_text for term in stage_terms) else 0.0


def _keyword_overlap(query: str, text: str) -> float:
    compact = query.replace("，", " ").replace("。", " ").strip()
    terms = [term for term in compact.split() if term]
    if not terms and compact:
        terms = [compact, compact[:2], compact[-2:]] if len(compact) > 4 else [compact]
    overlap = sum(1 for term in terms if term and term in text)
    return overlap * 0.05


def _filter_blocks(blocks: list[Block], vectors: list[list[float]], filters: dict) -> list[tuple[Block, list[float]]]:
    stage_terms = filters.get("stage") or []
    pairs = list(zip(blocks, vectors))
    if not stage_terms:
        return pairs
    matched = [pair for pair in pairs if any(term in " ".join(pair[0].heading_path) for term in stage_terms)]
    return matched or pairs


def _filter_kos(
    kos: list[KnowledgeObject],
    vectors: list[list[float]],
    filters: dict,
    allowed_types: list[str] | None,
) -> list[tuple[KnowledgeObject, list[float]]]:
    pairs = list(zip(kos, vectors))
    if allowed_types:
        pairs = [pair for pair in pairs if pair[0].k_type in allowed_types]
    stage_terms = filters.get("stage") or []
    if not stage_terms:
        return pairs
    matched = [pair for pair in pairs if any(term in " ".join(pair[0].source_headings) for term in stage_terms)]
    return matched or pairs


def _filter_expressions(
    expressions: list[Expression],
    vectors: list[list[float]],
    filters: dict,
) -> list[tuple[Expression, list[float]]]:
    pairs = list(zip(expressions, vectors))
    stage_terms = filters.get("stage") or []
    if not stage_terms:
        return pairs
    matched = [pair for pair in pairs if any(term in " ".join(pair[0].source_headings) for term in stage_terms)]
    return matched or pairs
