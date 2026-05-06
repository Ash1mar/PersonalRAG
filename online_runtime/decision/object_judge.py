from libs.common.models import KnowledgeObject
from online_runtime.decision.validity_checker import check_validity


def judge_object(ko: KnowledgeObject, slot_id: str) -> tuple[str, str, str]:
    validity, reason = check_validity(ko, slot_id)
    if validity == "valid":
        return "include", validity, reason
    if slot_id == "S4_issues" and ko.k_type == "experience":
        return "review", validity, "问题 slot 中经验类对象需要人工确认是否保留。"
    return "exclude", validity, reason

