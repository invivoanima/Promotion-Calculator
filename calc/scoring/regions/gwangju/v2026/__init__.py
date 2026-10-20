"""광주광역시 2026 independent scoring provider; local-manual verification pending."""
from decimal import Decimal
from .catalog import CATEGORIES, CATEGORY_BY_CODE, ITEMS, ITEM_BY_CODE, CURRENT_RULE_YEAR
from . import career, work, training, common_bonus, regional_bonus
from .precision import ZERO, rounded
from .policy import RULE_NOTICE, SOURCE_LINKS, ASSESSMENT_DATE
from .work import selected_work_performance_records
from .training import converted_training_score, training_job_record_score, eligible_training_job_records, selected_training_job_records
from .common_bonus import common_training_credit_contributions

REGION_CODE = "gwangju"
RULE_YEAR = CURRENT_RULE_YEAR
RULE_DATE = "2026. 2. 28. (기본 계산 기준일)"
ROSTER_DATE = "교육청 원문 확인 필요"
REGIONAL_BONUS_AVAILABLE = False
VALIDATE_GUEST_STORAGE = True
VERIFICATION_STATUS = "statutory_baseline"
SCORE_ITEM_TEMPLATE = "calc/new/score_item.html"
MANUAL_STATIC_PATH = ""
RESOURCE_NOTES = [
    {"badge": "입력 가능", "title": "선택가산점 외 9개 항목", "description": "경력, 근무성적, 자격·직무연수, 연구실적과 공통가산점 4개 항목을 계산합니다."},
    {"badge": "기준 확인 필요", "title": "교육청 원문 대조 전", "description": RULE_NOTICE},
    {"badge": "평정 대상", "title": "교감 승진후보자명부 기본 계산", "description": "자격연수는 교감 자격연수 성적에 0.05 계수를 적용합니다. 교감 자격연수 대상자 선발 기준은 교육청별 확인이 필요합니다."},
    {"badge": "제외", "title": "선택가산점", "description": "선택가산점은 입력과 총점에서 제외합니다."},
]
CATEGORY_MODULES = {"career": career, "work": work, "training": training,
                    "common_bonus": common_bonus, "regional_bonus": regional_bonus}

def calculate_record_score(record):
    item = ITEM_BY_CODE[record.item_code]
    return CATEGORY_MODULES[item["category"]].calculate_record_score(record)

def calculate_item_score_from_records(item_code, records):
    records = list(records)
    if not records:
        return ZERO
    return CATEGORY_MODULES[ITEM_BY_CODE[item_code]["category"]].calculate_item_score(item_code, records)

def validate_input(item, cleaned):
    errors = []
    # These are server-side constraints, also applied to guest hydration.
    for name, config in item.get("fields", {}).items():
        value = cleaned.get(name)
        if value is None or config.get("input_type") != "number":
            continue
        if "min" in config and value < Decimal(str(config["min"])):
            errors.append((name, f"{config['min']} 이상으로 입력해주세요."))
        if "max" in config and value > Decimal(str(config["max"])):
            errors.append((name, f"{config['max']} 이하로 입력해주세요."))
    for name in ("start_date", "end_date", "event_date"):
        if cleaned.get(name) and cleaned[name] > ASSESSMENT_DATE:
            errors.append((name, "평정 기준일 이후의 날짜는 입력할 수 없습니다."))
    if item["category"] == "training":
        errors.extend(training.validate_input(item, cleaned))
    return errors

def finalize_summary(summary, record_map):
    summary["categories"] = {category["code"]: rounded(min(
        sum((summary["items"][item["code"]] for item in category["items"]), ZERO),
        category["max_score"])) for category in CATEGORIES}
    summary["total"] = rounded(sum(summary["categories"].values(), ZERO))
    summary["verification_status"] = VERIFICATION_STATUS
    summary["excluded_categories"] = ["regional_bonus"]
    return summary

def mark_selected_records(records, item_code):
    records = list(records)
    for record in records:
        record.is_score_selected = False
        record.is_completion_selected = False
        record.score_weight_percent = None
        record.applied_score = ZERO
        record.display_calculated_score = record.calculated_score
    if item_code == "work_performance":
        for index, record in enumerate(selected_work_performance_records(records)):
            record.is_score_selected = True
            record.score_weight_percent = (34, 33, 33)[index]
    elif item_code == "training_job":
        selected = selected_training_job_records(records)
        for record in selected[1:]:
            record.is_completion_selected = True
        if selected:
            selected[0].is_score_selected = True
    elif item_code == "training_research":
        for record in training.selected_research_records(records):
            record.is_score_selected = True
    elif item_code == "training_qualification" and records:
        max(records, key=lambda record: record.calculated_score).is_score_selected = True
    elif item_code == "common_training_credit":
        for record, contribution in common_training_credit_contributions(records):
            record.applied_score = contribution
            record.is_score_selected = contribution > 0
    return records

def item_context(item_code, score_for_item):
    return {}
