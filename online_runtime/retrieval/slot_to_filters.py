def slot_to_filters(slot_id: str, year: int | None, dept: str | None) -> dict:
    stage_map = {
        "S1_overview": ["概况", "总体情况"],
        "S2_measures": ["措施", "做法", "举措"],
        "S3_outcomes": ["成效", "成果", "亮点"],
        "S4_issues": ["问题", "不足", "风险"],
        "S5_nextsteps": ["计划", "下一步"],
    }
    return {
        "year": [year] if year else [],
        "dept": dept,
        "stage": stage_map.get(slot_id, []),
    }

