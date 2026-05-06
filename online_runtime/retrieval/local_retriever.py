from __future__ import annotations

from libs.common.models import Block, KnowledgeObject
from online_runtime.retrieval.base import BaseRetriever


class LocalRetriever(BaseRetriever):
    def __init__(self, blocks: list[Block], kos: list[KnowledgeObject]) -> None:
        self.blocks = blocks
        self.kos = kos

    def retrieve_blocks(self, query: str, filters: dict, top_k: int) -> list[Block]:
        candidates = _filter_blocks(self.blocks, filters)
        ranked = sorted(
            candidates,
            key=lambda block: _score_block(block, query, filters),
            reverse=True,
        )
        return ranked[:top_k]

    def retrieve_kos(
        self,
        query: str,
        filters: dict,
        top_k: int,
        allowed_types: list[str] | None = None,
    ) -> list[KnowledgeObject]:
        candidates = self.kos
        if allowed_types:
            candidates = [item for item in candidates if item.k_type in allowed_types]
        candidates = _filter_kos(candidates, filters)
        ranked = sorted(
            candidates,
            key=lambda item: _score_ko(item, query, filters),
            reverse=True,
        )
        return ranked[:top_k]


def _score_block(block: Block, query: str, filters: dict) -> int:
    score = _score_text(block.text, query, block.heading_path)
    heading = " ".join(block.heading_path)
    stage_terms = filters.get("stage") or []
    if any(term in heading for term in stage_terms):
        score += 8
    return score


def _score_ko(item: KnowledgeObject, query: str, filters: dict) -> int:
    score = _score_text(item.canonical, query, item.topic + item.source_headings)
    stage_terms = filters.get("stage") or []
    heading = " ".join(item.source_headings)
    if any(term in heading for term in stage_terms):
        score += 8
    if item.k_type == "experience" and any(term in {"措施", "做法", "举措", "计划", "下一步"} for term in stage_terms):
        score += 4
    if item.k_type == "fact" and any(term in {"概况", "总体情况", "成效", "成果", "亮点", "问题", "不足"} for term in stage_terms):
        score += 4
    return score


def _score_text(text: str, query: str, extra_terms: list[str] | None) -> int:
    score = 0
    query_terms = _query_terms(query)
    haystack = text.lower()
    for term in query_terms:
        if term.lower() in haystack:
            score += 3
    for term in extra_terms or []:
        if term and term in query:
            score += 2
    if score == 0:
        score = len(text) // 40
    return score


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
