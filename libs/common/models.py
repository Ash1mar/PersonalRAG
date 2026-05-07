from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel, Field

from libs.common.ids import make_doc_id


class DocumentMeta(BaseModel):
    doc_id: str
    doc_type: str | None = None
    dept: str | None = None
    year: int | None = None
    source_path: str | None = None

    @classmethod
    def from_inputs(
        cls,
        doc_id: str | None,
        doc_type: str | None,
        dept: str | None,
        year: int | None,
        source_path: str | None,
    ) -> "DocumentMeta":
        resolved_doc_id = doc_id or _doc_id_from_path(source_path) or make_doc_id()
        return cls(
            doc_id=resolved_doc_id,
            doc_type=doc_type,
            dept=dept,
            year=year,
            source_path=source_path,
        )


class Block(BaseModel):
    block_id: str
    doc_id: str
    page_no: int = 1
    order: int
    heading_path: list[str] = Field(default_factory=list)
    text: str


class Evidence(BaseModel):
    doc_id: str
    block_id: str
    page_no: int
    quote: str

    @classmethod
    def from_block(cls, block: Block, quote: str) -> "Evidence":
        return cls(doc_id=block.doc_id, block_id=block.block_id, page_no=block.page_no, quote=quote)


class KnowledgeObject(BaseModel):
    kid: str
    k_type: Literal["fact", "experience"]
    canonical: str
    time: int | None = None
    topic: list[str] = Field(default_factory=list)
    source_headings: list[str] = Field(default_factory=list)
    confidence: float
    evidence: list[Evidence] = Field(default_factory=list)
    condition: str | None = None
    action: str | None = None
    status: str | None = None
    decision: str | None = None
    validity: str | None = None
    decision_reason: str | None = None
    selected_evidence: list[Evidence] = Field(default_factory=list)


class Expression(BaseModel):
    expr_id: str
    canonical: str
    topic: str | None = None
    status: str = "active"
    confidence: float = 0.0
    source_headings: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class Document(BaseModel):
    meta: DocumentMeta
    blocks: list[Block]
    raw_text: str


class ExtractionSummary(BaseModel):
    method: str
    chat_model: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ExtractionArtifacts(BaseModel):
    facts: list[KnowledgeObject] = Field(default_factory=list)
    experiences: list[KnowledgeObject] = Field(default_factory=list)
    expressions: list[Expression] = Field(default_factory=list)
    summary: ExtractionSummary


class Slot(BaseModel):
    slot_id: str
    title: str
    focus_types: list[str] = Field(default_factory=list)


class RetrievalInfo(BaseModel):
    filters: dict
    candidate_block_count: int
    candidate_ko_count: int = 0
    candidate_expression_count: int = 0
    backend: str | None = None


class SlotBundle(BaseModel):
    slot_id: str
    title: str
    focus_types: list[str]
    retrieval_info: RetrievalInfo
    ranked_blocks: list[Block]
    knowledge_objects: list[KnowledgeObject]
    expressions: list[Expression] = Field(default_factory=list)


class TaskContext(BaseModel):
    task_type: str
    year: int | None = None
    dept: str | None = None


class EvidenceBundle(BaseModel):
    schema_version: str
    task_id: str
    task_context: TaskContext
    outline: list[Slot]
    slots: list[SlotBundle]


class SearchHit(BaseModel):
    item_id: str
    item_type: Literal["block", "fact", "experience", "expression"]
    score: float
    doc_id: str
    text: str
    source_headings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalKnowledgeBaseIndex(BaseModel):
    doc_id: str
    source_path: str | None = None
    built_at: str
    extraction_method: str
    chat_model: str | None = None
    embedding_backend: str
    blocks: list[Block] = Field(default_factory=list)
    block_vectors: list[list[float]] = Field(default_factory=list)
    knowledge_objects: list[KnowledgeObject] = Field(default_factory=list)
    ko_vectors: list[list[float]] = Field(default_factory=list)
    expressions: list[Expression] = Field(default_factory=list)
    expression_vectors: list[list[float]] = Field(default_factory=list)


def _doc_id_from_path(source_path: str | None) -> str | None:
    if not source_path:
        return None
    return Path(source_path).stem.replace(" ", "_")
