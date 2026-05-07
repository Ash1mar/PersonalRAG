from __future__ import annotations

from pydantic import BaseModel, Field

from libs.common.ids import make_ko_id
from libs.common.models import Document, Evidence, Expression, ExtractionArtifacts, ExtractionSummary, KnowledgeObject
from libs.llm.factory import get_chat_model_provider
from offline_pipeline.extract.expression_extractor import get_default_expressions
from offline_pipeline.extract.fact_extractor import extract_facts as extract_facts_by_rules
from offline_pipeline.extract.experience_extractor import extract_experiences as extract_experiences_by_rules


class FactCandidate(BaseModel):
    canonical: str
    topic: list[str] = Field(default_factory=list)
    time: int | None = None
    confidence: float = 0.0


class ExperienceCandidate(BaseModel):
    canonical: str
    condition: str | None = None
    action: str | None = None
    topic: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    status: str = "candidate"


class ExpressionCandidate(BaseModel):
    canonical: str
    topic: str | None = None
    status: str = "active"
    confidence: float = 0.0


class BlockExtractionPayload(BaseModel):
    facts: list[FactCandidate] = Field(default_factory=list)
    experiences: list[ExperienceCandidate] = Field(default_factory=list)
    expressions: list[ExpressionCandidate] = Field(default_factory=list)


SYSTEM_PROMPT = """你是知识抽取器。你的任务是把单个 block 的文本转换为可复用的知识对象。

约束：
1. 只能依据给定 block 文本和标题路径输出，禁止补充 block 中没有明确出现的事实。
2. fact 是客观可写事实；experience 是做法/机制/措施；expression 是正式口径表达。
3. 只输出结构化 JSON，不要输出解释。
4. 如果某一类没有内容，返回空数组。
5. canonical 必须简洁、可直接复用；confidence 取 0 到 1。
6. 除非 block 里本身就是短语，否则不要把一句话切成多个碎片对象；优先保留完整句子或完整做法。
7. fact 优先保留带时间、数量、结果、问题状态的完整事实句；experience 优先保留条件和动作闭环；expression 优先保留正式提法。
"""


def extract_knowledge(
    document: Document,
    chat_model: str | None = None,
    chat_provider: str | None = None,
) -> ExtractionArtifacts:
    warnings: list[str] = []
    chat_client = get_chat_model_provider(provider_name=chat_provider, model_name=chat_model)
    facts: list[KnowledgeObject] = []
    experiences: list[KnowledgeObject] = []
    expressions: list[Expression] = []
    seen_fact: set[str] = set()
    seen_experience: set[str] = set()
    seen_expression: set[str] = set()

    for block_index, block in enumerate(document.blocks, start=1):
        prompt = _build_user_prompt(document=document, block=block)
        try:
            raw = chat_client.chat_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                schema=BlockExtractionPayload.model_json_schema(),
            )
            payload = BlockExtractionPayload.model_validate(raw)
        except Exception as exc:
            warnings.append(f"Block {block.block_id} fell back to rule extraction: {exc}")
            payload = BlockExtractionPayload()

        _append_facts(
            facts=facts,
            seen=seen_fact,
            payload=payload.facts,
            block=block,
            block_index=block_index,
            default_year=document.meta.year,
        )
        _append_experiences(
            experiences=experiences,
            seen=seen_experience,
            payload=payload.experiences,
            block=block,
            block_index=block_index,
        )
        _append_expressions(
            expressions=expressions,
            seen=seen_expression,
            payload=payload.expressions,
            block=block,
            block_index=block_index,
        )

    if not facts and not experiences and not expressions:
        warnings.append("LLM extraction returned no usable objects; using rule fallback for the full document.")
        facts = extract_facts_by_rules(document)
        experiences = extract_experiences_by_rules(document)
        expressions = get_default_expressions()
        return ExtractionArtifacts(
            facts=facts,
            experiences=experiences,
            expressions=expressions,
            summary=ExtractionSummary(
                method="rules_fallback",
                chat_model=chat_client.backend_name,
                warnings=warnings,
            ),
        )

    if not facts:
        warnings.append("No facts were produced by LLM extraction; merged rule fallback facts.")
        facts = extract_facts_by_rules(document)
    if not experiences:
        warnings.append("No experiences were produced by LLM extraction; merged rule fallback experiences.")
        experiences = extract_experiences_by_rules(document)
    if not expressions:
        warnings.append("No expressions were produced by LLM extraction; merged lightweight default expressions.")
        expressions = get_default_expressions()

    return ExtractionArtifacts(
        facts=facts,
        experiences=experiences,
        expressions=expressions,
        summary=ExtractionSummary(
            method="llm_plus_fallback",
            chat_model=chat_client.backend_name,
            warnings=warnings,
        ),
    )


def _build_user_prompt(document: Document, block) -> str:
    return f"""文档元信息：
- doc_id: {document.meta.doc_id}
- doc_type: {document.meta.doc_type or 'unknown'}
- dept: {document.meta.dept or 'unknown'}
- year: {document.meta.year or 'unknown'}

当前标题路径：
{block.heading_path}

当前 block 文本：
{block.text}

请抽取 facts / experiences / expressions。"""


def _append_facts(
    *,
    facts: list[KnowledgeObject],
    seen: set[str],
    payload: list[FactCandidate],
    block,
    block_index: int,
    default_year: int | None,
) -> None:
    for item_index, item in enumerate(payload, start=1):
        canonical = _ground_candidate_to_sentence(item.canonical, block.text)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        facts.append(
            KnowledgeObject(
                kid=make_ko_id("fact", block_index, item_index),
                k_type="fact",
                canonical=canonical,
                time=item.time or default_year,
                topic=item.topic,
                source_headings=block.heading_path,
                confidence=_normalize_confidence(item.confidence),
                evidence=[Evidence.from_block(block, canonical)],
            )
        )


def _append_experiences(
    *,
    experiences: list[KnowledgeObject],
    seen: set[str],
    payload: list[ExperienceCandidate],
    block,
    block_index: int,
) -> None:
    for item_index, item in enumerate(payload, start=1):
        canonical = _ground_candidate_to_sentence(item.canonical, block.text)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        action = _ground_candidate_to_sentence(item.action or item.canonical, block.text)
        experiences.append(
            KnowledgeObject(
                kid=make_ko_id("experience", block_index, item_index),
                k_type="experience",
                canonical=canonical,
                topic=item.topic,
                source_headings=block.heading_path,
                confidence=_normalize_confidence(item.confidence),
                evidence=[Evidence.from_block(block, canonical)],
                condition=_normalize_optional_text(item.condition),
                action=action,
                status=item.status or "candidate",
            )
        )


def _append_expressions(
    *,
    expressions: list[Expression],
    seen: set[str],
    payload: list[ExpressionCandidate],
    block,
    block_index: int,
) -> None:
    for item_index, item in enumerate(payload, start=1):
        canonical = _normalize_text(item.canonical)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        expressions.append(
            Expression(
                expr_id=f"EXPR_{block_index:03d}_{item_index:02d}",
                canonical=canonical,
                topic=item.topic,
                status=item.status or "active",
                confidence=_normalize_confidence(item.confidence),
                source_headings=block.heading_path,
                evidence=[Evidence.from_block(block, canonical)],
            )
        )


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = "".join(text.split())
    if cleaned and not cleaned.endswith("。"):
        cleaned = f"{cleaned}。"
    return cleaned


def _normalize_optional_text(text: str | None) -> str | None:
    cleaned = _normalize_text(text)
    return cleaned or None


def _normalize_confidence(value: float | None) -> float:
    if value is None:
        return 0.7
    return max(0.0, min(float(value), 1.0))


def _ground_candidate_to_sentence(candidate: str | None, block_text: str) -> str:
    canonical = _normalize_text(candidate)
    if not canonical:
        return ""
    sentences = [_normalize_text(part) for part in block_text.replace("\n", " ").split("。") if _normalize_text(part)]
    if not sentences:
        return canonical
    if not _looks_like_fragment(canonical):
        return canonical

    best_sentence = max(sentences, key=lambda sentence: _sentence_overlap_score(canonical, sentence))
    if _sentence_overlap_score(canonical, best_sentence) >= 0.35:
        return best_sentence
    return canonical


def _looks_like_fragment(text: str) -> bool:
    return len(text) < 16 or ("，" not in text and not any(char.isdigit() for char in text))


def _sentence_overlap_score(candidate: str, sentence: str) -> float:
    if candidate in sentence:
        return 1.0
    candidate_chars = {char for char in candidate if char.strip()}
    sentence_chars = {char for char in sentence if char.strip()}
    if not candidate_chars:
        return 0.0
    return len(candidate_chars & sentence_chars) / len(candidate_chars)
