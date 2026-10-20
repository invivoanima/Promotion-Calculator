"""Complete Jeonnam 2026 rule provider, including common bonus policy.

This extraction preserves existing calculations. See the manual audit for
outstanding rule corrections; moving a rule is not confirmation of its accuracy.
"""

from decimal import Decimal
from .catalog import CATEGORIES, CATEGORY_BY_CODE, ITEM_BY_CODE, ITEMS, CURRENT_RULE_YEAR
from . import career, work, training, common_bonus, regional_bonus
from .precision import ZERO, rounded
from .work import selected_work_performance_records
from .training import converted_training_score, training_job_record_score, eligible_training_job_records, selected_training_job_records
from .common_bonus import common_training_credit_contributions

REGION_CODE = "jeonnam"
REGIONAL_BONUS_AVAILABLE = True
VERIFICATION_STATUS = "manual_audited"
RULE_NOTICE = ""
RULE_YEAR = CURRENT_RULE_YEAR
RULE_DATE = "2026. 2. 28."
ROSTER_DATE = "2026. 3. 31."
MANUAL_STATIC_PATH = "calc/manuals/jeonnam-2026.pdf"
SCORE_ITEM_TEMPLATE = "calc/regions/jeonnam/v2026/score_item.html"
RESOURCE_NOTES = [
    {"badge": "삭제", "title": "선택가산점 5번", "description": "2018.9.1. 삭제되어 6번 기타 교육활동 항목으로 이동한 흔적만 표시합니다."},
    {"badge": "초등 제외", "title": "선택가산점 9·10번", "description": "학급 담임 경력과 도서·벽지 대체 가산점은 초등 계산 대상이 아닙니다."},
    {"badge": "자격요건", "title": "한국사 능력 검정·연수", "description": "총점이 아닌 교감 자격연수 응시요건으로 별도 관리합니다."},
]
CATEGORY_MODULES = {
    "career": career, "work": work, "training": training,
    "common_bonus": common_bonus, "regional_bonus": regional_bonus,
}


def calculate_record_score(record):
    item = ITEM_BY_CODE[record.item_code]
    if item.get("input_disabled"):
        return ZERO
    return CATEGORY_MODULES[item["category"]].calculate_record_score(record)


def calculate_item_score_from_records(item_code, records):
    item = ITEM_BY_CODE[item_code]
    records = list(records)
    if not records or item.get("input_disabled"):
        return ZERO
    return CATEGORY_MODULES[item["category"]].calculate_item_score(item_code, records)


def validate_input(item, cleaned):
    if item["category"] == "training":
        return training.validate_input(item, cleaned)
    return []


def finalize_summary(summary, record_map):
    """Region-owned category limits and cross-category adjustments live here."""
    summary["categories"] = {
        category["code"]: rounded(min(
            sum((summary["items"][item["code"]] for item in category["items"]), ZERO),
            category["max_score"],
        )) for category in CATEGORIES
    }
    summary["total"] = rounded(sum(summary["categories"].values(), ZERO))
    return summary


def mark_selected_records(records, item_code):
    records = list(records)
    for record in records:
        record.is_score_selected = False
        record.is_completion_selected = False
        record.score_weight_percent = None
        record.applied_score = Decimal("0")
        record.display_calculated_score = record.calculated_score
    if item_code == "work_performance":
        weights = (34, 33, 33)
        for index, record in enumerate(selected_work_performance_records(records)):
            record.is_score_selected = True
            record.score_weight_percent = weights[index]
    elif item_code == "training_job":
        selected = selected_training_job_records(records)
        for record in records:
            record.display_calculated_score = training_job_record_score(record)
        for record in selected:
            record.is_completion_selected = True
        if selected:
            selected[0].is_score_selected = True
    elif item_code == "common_training_credit":
        for record, contribution in common_training_credit_contributions(records):
            record.applied_score = contribution
            record.is_score_selected = contribution > 0
    return records



def item_context(item_code, score_for_item):
    if item_code not in {"training_qualification", "jeonnam_leadership"}:
        return {}
    qualification_score = score_for_item("training_qualification")
    return {
        "qualification_score": qualification_score,
        "qualification_gap": max(Decimal("9") - qualification_score, ZERO),
    }
