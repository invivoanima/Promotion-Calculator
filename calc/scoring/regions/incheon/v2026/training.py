"""Local training rules for vice-principal promotion (not training nomination)."""
from datetime import date
from decimal import Decimal
from calc.scoring.utils import clamp, decimal_value
from .catalog import ITEM_BY_CODE
from .policy import ASSESSMENT_DATE, JOB_TRAINING_START
from .precision import ZERO, rounded

DIRECT_VARIANT_SCORES = {'training_research': {'score_3': '3',
                       'score_1_5': '1.5',
                       'score_1': '1',
                       'research_1_5': '1.5',
                       'research_1_25': '1.25',
                       'research_1_05': '1.05',
                       'research_1': '1',
                       'research_0_875': '0.875',
                       'research_0_75': '0.75',
                       'research_0_7': '0.7',
                       'research_0_625': '0.625',
                       'research_0_525': '0.525',
                       'research_0_5': '0.5',
                       'research_0_45': '0.45',
                       'research_0_375': '0.375',
                       'research_0_35': '0.35',
                       'research_0_3': '0.3',
                       'research_0_25': '0.25',
                       'research_0_225': '0.225',
                       'research_0_15': '0.15',
                       'score_0_75': '0.75',
                       'score_0_7': '0.7',
                       'score_0_5': '0.5',
                       'score_0_45': '0.45',
                       'score_0_375': '0.375',
                       'score_0_3': '0.3',
                       'score_0_25': '0.25',
                       'score_0_225': '0.225',
                       'score_0_15': '0.15'}}

QUALIFICATION_COEFFICIENT = Decimal("0.05")

def converted_training_score(raw_score):
    raw = decimal_value(raw_score)
    if raw < 60:
        return ZERO
    if raw > 95:
        return Decimal("100")
    if raw > 90:
        return Decimal("95")
    if raw > 85:
        return Decimal("90")
    return Decimal("85")

def training_job_record_score(record):
    return rounded(Decimal("6") * converted_training_score((record.input_data or {}).get("value")) / 100)

def eligible_training_job_records(records):
    return [record for record in records if record.event_date
            and JOB_TRAINING_START <= record.event_date <= ASSESSMENT_DATE
            and decimal_value((record.input_data or {}).get("extra_value")) >= 60
            and decimal_value((record.input_data or {}).get("value")) >= 60]

def selected_training_job_records(records):
    # One scored course plus two other completion courses, without double-use.
    return sorted(eligible_training_job_records(records), key=lambda record: (
        decimal_value((record.input_data or {}).get("value")), record.event_date or date.min,
        getattr(record, "id", None) or 0), reverse=True)[:3]

def selected_research_records(records):
    competitions = {}
    degrees = []
    for record in records:
        variant = (record.input_data or {}).get("variant", "")
        if variant in {"score_3", "score_1_5", "score_1"}:
            degrees.append(record)
        elif record.event_date:
            year = record.event_date.year - (record.event_date.month < 3)
            if year not in competitions or record.calculated_score > competitions[year].calculated_score:
                competitions[year] = record
    selected = list(competitions.values())
    if degrees:
        selected.append(max(degrees, key=lambda record: record.calculated_score))
    return selected

def calculate_record_score(record):
    data = record.input_data or {}
    if record.item_code == "training_qualification":
        raw = clamp(data.get("value"), upper="100")
        if raw < 60:
            return ZERO
        return rounded(Decimal("9") - (100 - max(raw, Decimal("80"))) * QUALIFICATION_COEFFICIENT)
    if record.item_code == "training_job":
        return training_job_record_score(record)
    return rounded(Decimal(DIRECT_VARIANT_SCORES[record.item_code].get(data.get("variant"), "0")))

def calculate_item_score(item_code, records):
    if item_code == "training_qualification":
        return max((record.calculated_score for record in records), default=ZERO)
    if item_code == "training_job":
        selected = selected_training_job_records(records)
        if not selected:
            return ZERO
        return rounded(training_job_record_score(selected[0]) + Decimal("6") * (len(selected) - 1))
    return rounded(min(sum((record.calculated_score for record in selected_research_records(records)), ZERO), ITEM_BY_CODE[item_code]["max_score"]))

def validate_input(item, cleaned):
    errors = []
    if item["code"] == "training_job":
        day = cleaned.get("event_date")
        if day and not JOB_TRAINING_START <= day <= ASSESSMENT_DATE:
            errors.append(("event_date", "이 지역의 직무연수 인정기간 안의 수료일을 입력해주세요."))
        if cleaned.get("extra_value") is not None and cleaned["extra_value"] < 60:
            errors.append(("extra_value", "60시간 이상 직무연수만 인정됩니다."))
    if item["code"] == "training_research" and not cleaned.get("event_date"):
        errors.append(("event_date", "학년도별 중복 여부 확인을 위해 취득·입상일을 입력해주세요."))
    return errors
