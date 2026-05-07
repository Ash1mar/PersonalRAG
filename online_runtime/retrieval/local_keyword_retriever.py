from __future__ import annotations

from libs.common.models import Block, Expression, KnowledgeObject, LocalKnowledgeBaseIndex
from online_runtime.retrieval.base import BaseRetriever


class LocalKeywordRetriever(BaseRetriever):
    def __init__(self, index: LocalKnowledgeBaseIndex) -> None:
        self.index = index

    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        candidates = _filter_blocks(self.index.blocks, filters)
        ranked = sorted(candidates, key=lambda block: _score_block(block, query, filters), reverse=True)
        return ranked[:top_k]

    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        candidates = self.index.knowledge_objects
        if allowed_types:
            candidates = [item for item in candidates if item.k_type in allowed_types]
        candidates = _filter_kos(candidates, filters)
        ranked = sorted(candidates, key=lambda item: _score_ko(item, query, filters), reverse=True)
        return ranked[:top_k]

    def retrieve_expressions(self, query: str, filters: dict, top_k: int) -> list[Expression]:
        candidates = _filter_expressions(self.index.expressions, filters)
        ranked = sorted(candidates, key=lambda item: _score_expression(item, query, filters), reverse=True)
        return ranked[:top_k]


def _score_block(block: Block, query: str, filters: dict) -> float:
    return _score_text(block.text, query, block.heading_path, filters)


def _score_ko(item: KnowledgeObject, query: str, filters: dict) -> float:
    return _score_text(item.canonical, query, item.source_headings + item.topic, filters)


def _score_expression(item: Expression, query: str, filters: dict) -> float:
    extra = item.source_headings + ([item.topic] if item.topic else [])
    return _score_text(item.canonical, query, extra, filters)


def _score_text(text: str, query: str, extras: list[str], filters: dict) -> float:
    score = 0.0
    query_terms = _query_terms(query)
    for term in query_terms:
        if term in text:
            score += 1.0
    for extra in extras:
        if extra and extra in query:
            score += 0.2
    stage_terms = filters.get("stage") or []
    if any(term in " ".join(extras) for term in stage_terms):
        score += 0.4
    return score + (len(text) / 500.0)


def _query_terms(query: str) -> list[str]:
    compact = query.replace("，", " ").replace("。", " ").strip()
    terms = [term for term in compact.split() if term]
    if terms:
        return terms
    if len(compact) <= 4:
        return [compact]
    return [compact, compact[:2], compact[-2:]]


def _filter_blocks(blocks: list[Block], filters: dict) -> list[Block]:
    stage_terms = filters.get("stage") or []
    if not stage_terms:
        return blocks
    matched = [block for block in blocks if any(term in " ".join(block.heading_path) for term in stage_terms)]
    return matched or blocks


def _filter_kos(kos: list[KnowledgeObject], filters: dict) -> list[KnowledgeObject]:
    stage_terms = filters.get("stage") or []
    if not stage_terms:
        return kos
    matched = [item for item in kos if any(term in " ".join(item.source_headings) for term in stage_terms)]
    return matched or kos


def _filter_expressions(expressions: list[Expression], filters: dict) -> list[Expression]:
    stage_terms = filters.get("stage") or []
    if not stage_terms:
        return expressions
    matched = [item for item in expressions if any(term in " ".join(item.source_headings) for term in stage_terms)]
    return matched or expressions
