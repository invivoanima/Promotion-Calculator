"""Jeonnam 2026 training rules."""

from decimal import Decimal
from calc.scoring.utils import decimal_value, clamp
from .precision import ZERO, rounded
from .catalog import ITEM_BY_CODE


from datetime import date

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


def converted_training_score(raw_score):
    raw_score = decimal_value(raw_score)
    if raw_score > 95:
        return Decimal("100")
    if raw_score > 90:
        return Decimal("95")
    if raw_score > 85:
        return Decimal("90")
    return Decimal("85")


def training_job_record_score(record):
    """Convert one job-training raw score to its six-point contribution."""
    raw_score = (record.input_data or {}).get("value")
    return rounded(Decimal("6") * converted_training_score(raw_score) / Decimal("100"))


def eligible_training_job_records(records):
    """Return recognized 60+ hour courses completed in the 2026 ten-year-two-month window."""
    recognized = []
    for record in records:
        data = record.input_data or {}
        hours = decimal_value(data.get("extra_value"))
        if (
            record.event_date
            and date(2016, 1, 1) <= record.event_date <= date(2026, 2, 28)
            and hours >= Decimal("60")
        ):
            recognized.append(record)
    return recognized


def selected_training_job_records(records):
    """Return up to two recognized courses, highest raw score first."""
    return sorted(
        eligible_training_job_records(records),
        key=lambda record: (
            decimal_value((record.input_data or {}).get("value")),
            record.event_date or date.min,
            getattr(record, "id", None) or 0,
        ),
        reverse=True,
    )[:2]


def calculate_record_score(record):
    data = record.input_data or {}
    if record.item_code == "training_qualification":
        raw = clamp(data.get("value"), upper="100")
        return rounded(clamp(Decimal("9") - (Decimal("100") - raw) * Decimal("0.025"), upper="9"))
    if record.item_code == "training_job":
        return training_job_record_score(record)
    return rounded(Decimal(DIRECT_VARIANT_SCORES[record.item_code].get(data.get("variant", "default"), "0")))


def calculate_item_score(item_code, records):
    if item_code == "training_qualification":
        return rounded(max((record.calculated_score for record in records), default=ZERO))
    if item_code == "training_job":
        selected = selected_training_job_records(records)
        completion_points = Decimal("6") * len(selected)
        score_points = training_job_record_score(selected[0]) if selected else ZERO
        return rounded(min(completion_points + score_points, Decimal("18")))
    return rounded(min(sum((record.calculated_score for record in records), ZERO), ITEM_BY_CODE[item_code]["max_score"]))


def validate_input(item, cleaned):
    errors = []
    if item["code"] == "training_job":
        completion_date = cleaned.get("event_date")
        hours = cleaned.get("extra_value")
        if completion_date and not (date(2016, 1, 1) <= completion_date <= date(2026, 2, 28)):
            errors.append(("event_date", "2026년 평정에서는 2016.1.1.부터 2026.2.28.까지 수료한 연수만 인정됩니다."))
        if hours is not None and hours < 60:
            errors.append(("extra_value", "60시간 이상 직무연수만 인정됩니다."))
    return errors
