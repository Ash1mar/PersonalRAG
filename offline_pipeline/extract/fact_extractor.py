from __future__ import annotations

import re

from libs.common.ids import make_ko_id
from libs.common.models import Document, Evidence, KnowledgeObject

FACT_HINTS = ("开展", "完成", "组织", "覆盖", "实现", "建立", "参加", "培训", "检查", "整改", "存在", "不规范", "差异", "问题")


def extract_facts(document: Document) -> list[KnowledgeObject]:
    facts: list[KnowledgeObject] = []
    seen: set[str] = set()
    for index, block in enumerate(document.blocks, start=1):
        sentences = _split_sentences(block.text)
        for sentence in sentences:
            if not _looks_like_fact(sentence):
                continue
            canonical = _normalize_sentence(sentence, document.meta.year)
            if canonical in seen:
                continue
            seen.add(canonical)
            facts.append(
                KnowledgeObject(
                    kid=make_ko_id("fact", index, len(facts) + 1),
                    k_type="fact",
                    canonical=canonical,
                    time=document.meta.year,
                    topic=_infer_topics(sentence),
                    source_headings=block.heading_path,
                    confidence=0.75,
                    evidence=[Evidence.from_block(block, sentence)],
                )
            )
    return facts


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。！？；;\n]+", text) if part.strip()]


def _looks_like_fact(sentence: str) -> bool:
    has_digit = any(char.isdigit() for char in sentence)
    has_hint = any(token in sentence for token in FACT_HINTS)
    return has_digit or has_hint


def _normalize_sentence(sentence: str, year: int | None) -> str:
    sentence = re.sub(r"\s+", "", sentence)
    if year and str(year) not in sentence and "本年" in sentence:
        sentence = sentence.replace("本年", f"{year}年")
    if not sentence.endswith("。"):
        sentence = f"{sentence}。"
    return sentence


def _infer_topics(sentence: str) -> list[str]:
    topics: list[str] = []
    mapping = {
        "党建": ("党建", "党组织", "党员"),
        "培训": ("培训", "学习", "教育"),
        "整改": ("整改", "问题", "改进"),
    }
    for topic, keywords in mapping.items():
        if any(keyword in sentence for keyword in keywords):
            topics.append(topic)
    return topics
