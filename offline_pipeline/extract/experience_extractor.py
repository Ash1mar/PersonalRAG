from __future__ import annotations

import re

from libs.common.ids import make_ko_id
from libs.common.models import Document, Evidence, KnowledgeObject

CONDITION_PATTERNS = (
    r"针对(?P<condition>[^，。；]+?)(问题|情况)",
    r"为解决(?P<condition>[^，。；]+?)",
)

ACTION_HINTS = ("推进", "建立", "完善", "采取", "实行", "形成")
ISSUE_HINTS = ("存在", "不足", "不规范", "差异", "薄弱", "不够")


def extract_experiences(document: Document) -> list[KnowledgeObject]:
    experiences: list[KnowledgeObject] = []
    for index, block in enumerate(document.blocks, start=1):
        sentences = _split_sentences(block.text)
        for sentence_index, sentence in enumerate(sentences, start=1):
            if not _looks_like_experience(sentence):
                continue
            condition = _extract_condition(sentence)
            canonical = _normalize_experience(sentence, condition)
            experiences.append(
                KnowledgeObject(
                    kid=make_ko_id("experience", index, sentence_index),
                    k_type="experience",
                    canonical=canonical,
                    topic=_infer_topics(sentence),
                    source_headings=block.heading_path,
                    confidence=0.7,
                    evidence=[Evidence.from_block(block, sentence)],
                    condition=condition,
                    action=sentence,
                    status="candidate",
                )
            )
    return experiences


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。！？；;\n]+", text) if part.strip()]


def _looks_like_experience(sentence: str) -> bool:
    has_action = any(hint in sentence for hint in ACTION_HINTS)
    if sentence.startswith("下一步") and has_action:
        return True
    if not has_action:
        return False
    if any(hint in sentence for hint in ISSUE_HINTS) and not (
        sentence.startswith("针对") or sentence.startswith("为解决")
    ):
        return False
    return True


def _extract_condition(sentence: str) -> str | None:
    for pattern in CONDITION_PATTERNS:
        match = re.search(pattern, sentence)
        if match:
            return match.group("condition").strip()
    return None


def _normalize_experience(sentence: str, condition: str | None) -> str:
    cleaned = re.sub(r"\s+", "", sentence)
    if condition and not cleaned.startswith("针对"):
        cleaned = f"针对{condition}，{cleaned}"
    if not cleaned.endswith("。"):
        cleaned = f"{cleaned}。"
    return cleaned


def _infer_topics(sentence: str) -> list[str]:
    topics: list[str] = []
    mapping = {
        "机制": ("机制", "闭环", "清单"),
        "培训": ("培训", "学习", "教育"),
        "整改": ("整改", "改进", "问题"),
    }
    for topic, keywords in mapping.items():
        if any(keyword in sentence for keyword in keywords):
            topics.append(topic)
    return topics
