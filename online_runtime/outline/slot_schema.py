from libs.common.models import Slot


def default_outline() -> list[Slot]:
    return [
        Slot(slot_id="S1_overview", title="总体情况", focus_types=["fact"]),
        Slot(slot_id="S2_measures", title="主要举措", focus_types=["experience"]),
        Slot(slot_id="S3_outcomes", title="取得成效", focus_types=["fact"]),
        Slot(slot_id="S4_issues", title="存在问题", focus_types=["fact", "experience"]),
        Slot(slot_id="S5_nextsteps", title="下一步计划", focus_types=["experience"]),
    ]

