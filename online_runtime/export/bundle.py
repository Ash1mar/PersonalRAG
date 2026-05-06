from __future__ import annotations

from apps.api.schemas import SlotInput
from libs.common.models import (
    Document,
    EvidenceBundle,
    KnowledgeObject,
    RetrievalInfo,
    Slot,
    SlotBundle,
    TaskContext,
)
from offline_pipeline.extract.expression_extractor import get_default_expressions
from offline_pipeline.extract.fact_extractor import extract_facts
from offline_pipeline.extract.experience_extractor import extract_experiences
from online_runtime.decision.evidence_selector import select_evidence
from online_runtime.decision.object_judge import judge_object
from online_runtime.outline.slot_schema import default_outline
from online_runtime.retrieval.local_retriever import LocalRetriever
from online_runtime.retrieval.slot_to_filters import slot_to_filters


def build_evidence_bundle(
    document: Document,
    task_id: str,
    task_type: str,
    dept: str | None,
    year: int | None,
    outline: list[SlotInput] | None,
) -> EvidenceBundle:
    facts = extract_facts(document)
    experiences = extract_experiences(document)
    expressions = get_default_expressions()
    all_kos: list[KnowledgeObject] = facts + experiences
    retriever = LocalRetriever(document.blocks, all_kos)
    slots = _resolve_outline(outline)
    slot_bundles: list[SlotBundle] = []

    for slot in slots:
        filters = slot_to_filters(slot.slot_id, year=year or document.meta.year, dept=dept or document.meta.dept)
        ranked_blocks = retriever.retrieve_blocks(query=slot.title, filters=filters, top_k=5)
        ranked_kos = retriever.retrieve_kos(
            query=slot.title,
            filters=filters,
            top_k=5,
            allowed_types=slot.focus_types,
        )

        decided: list[KnowledgeObject] = []
        for ko in ranked_kos:
            decision, validity, reason = judge_object(ko, slot.slot_id)
            decided.append(
                ko.model_copy(
                    update={
                        "decision": decision,
                        "validity": validity,
                        "decision_reason": reason,
                        "selected_evidence": select_evidence(ko),
                    }
                )
            )

        slot_bundles.append(
            SlotBundle(
                slot_id=slot.slot_id,
                title=slot.title,
                focus_types=slot.focus_types,
                retrieval_info=RetrievalInfo(filters=filters, candidate_block_count=len(ranked_blocks)),
                ranked_blocks=ranked_blocks,
                knowledge_objects=decided,
                expressions=expressions if slot.slot_id in {"S1_overview", "S2_measures", "S5_nextsteps"} else [],
            )
        )

    return EvidenceBundle(
        schema_version="evidence_bundle.v1",
        task_id=task_id,
        task_context=TaskContext(task_type=task_type, year=year or document.meta.year, dept=dept or document.meta.dept),
        outline=slots,
        slots=slot_bundles,
    )


def _resolve_outline(outline: list[SlotInput] | None) -> list[Slot]:
    if not outline:
        return default_outline()
    return [Slot(slot_id=item.slot_id, title=item.title, focus_types=item.focus_types) for item in outline]

