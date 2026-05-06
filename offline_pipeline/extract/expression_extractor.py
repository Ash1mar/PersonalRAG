from libs.common.models import Expression


def get_default_expressions() -> list[Expression]:
    return [
        Expression(
            expr_id="EXPR_001",
            canonical="以高质量知识组织支撑高质量写作产出",
            topic="知识管理",
            status="active",
        ),
        Expression(
            expr_id="EXPR_002",
            canonical="建立清单化推进、闭环式督办机制",
            topic="机制建设",
            status="active",
        ),
    ]

