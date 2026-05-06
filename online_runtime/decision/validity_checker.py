from libs.common.models import KnowledgeObject


def check_validity(ko: KnowledgeObject, slot_id: str) -> tuple[str, str]:
    if ko.k_type == "experience" and slot_id == "S1_overview":
        return "uncertain", "经验类对象不优先用于总体情况概述。"
    return "valid", "对象与当前 slot 类型基本匹配。"

