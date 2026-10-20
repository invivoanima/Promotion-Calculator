"""Local common bonus policy, including annual and overall limits."""

from decimal import Decimal
from calc.scoring.utils import decimal_value, period_score as _period_score
from .precision import ZERO, rounded
from .catalog import ITEM_BY_CODE
from .policy import TRAINING_CREDIT_RATE, TRAINING_CREDIT_ANNUAL_CAP, TRAINING_CREDIT_TOTAL_CAP


PERIOD_RATES = {'common_research_school': {'default': ('0.018', '0.0006')},
 'common_foreign_institution': {'default': ('0.015', '0.0005')}}


def common_training_credit_contributions(records):
    """Allocate this region's annual and overall limits to visible records."""
    records = list(records)
    ordered = sorted(
        enumerate(records),
        key=lambda pair: (
            int((pair[1].input_data or {}).get("year") or 0),
            -pair[0],
        ),
        reverse=True,
    )
    yearly_used = {}
    overall_used = ZERO
    contributions = {}
    for _, record in ordered:
        year = str((record.input_data or {}).get("year") or "")
        annual_remaining = max(TRAINING_CREDIT_ANNUAL_CAP - yearly_used.get(year, ZERO), ZERO)
        overall_remaining = max(TRAINING_CREDIT_TOTAL_CAP - overall_used, ZERO)
        contribution = min(
            max(record.calculated_score, ZERO),
            annual_remaining,
            overall_remaining,
        )
        contributions[id(record)] = contribution
        yearly_used[year] = yearly_used.get(year, ZERO) + contribution
        overall_used += contribution
    return [(record, contributions.get(id(record), ZERO)) for record in records]


def calculate_record_score(record):
    data = record.input_data or {}
    if record.item_code in PERIOD_RATES:
        return rounded(_period_score(record, PERIOD_RATES[record.item_code]["default"]))
    if record.item_code == "common_training_credit":
        return rounded(decimal_value(data.get("value")) * TRAINING_CREDIT_RATE)
    return Decimal("0.1")


def calculate_item_score(item_code, records):
    if item_code == "common_training_credit":
        return rounded(sum((contribution for _, contribution in common_training_credit_contributions(records)), ZERO))
    if item_code == "common_school_violence":
        years = {str(r.input_data.get("year") or r.event_date or getattr(r, "guest_key", None) or r.id) for r in records}
        return rounded(min(Decimal("0.1") * len(years), ITEM_BY_CODE[item_code]["max_score"]))
    return rounded(min(sum((record.calculated_score for record in records), ZERO), ITEM_BY_CODE[item_code]["max_score"]))
