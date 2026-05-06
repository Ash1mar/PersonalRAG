from libs.common.models import Evidence, KnowledgeObject


def select_evidence(ko: KnowledgeObject, limit: int = 1) -> list[Evidence]:
    return ko.evidence[:limit]

