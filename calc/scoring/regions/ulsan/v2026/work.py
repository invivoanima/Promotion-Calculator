"""Local five-year selection and chronological 34/33/33 weighting."""
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
from calc.scoring.utils import clamp
from .catalog import CURRENT_RULE_YEAR
from .precision import ZERO, rounded

WEIGHTS = (Decimal("0.34"), Decimal("0.33"), Decimal("0.33"))

def weighted_score(records):
    return sum((record.calculated_score * WEIGHTS[index] for index, record in enumerate(records)), ZERO)

def selected_work_performance_records(records):
    by_year = {}
    for record in records:
        try:
            year = int((record.input_data or {}).get("year") or 0)
        except (TypeError, ValueError):
            continue
        if not CURRENT_RULE_YEAR - 5 <= year < CURRENT_RULE_YEAR:
            continue
        if year not in by_year or record.calculated_score > by_year[year].calculated_score:
            by_year[year] = record
    recent = [by_year[year] for year in sorted(by_year, reverse=True)]
    if not recent:
        return []
    # The 34% weight can make a slightly lower recent score advantageous.
    return list(max(combinations(recent, min(3, len(recent))), key=weighted_score))

def calculate_record_score(record):
    return rounded(clamp((record.input_data or {}).get("value"), upper="100"))

def calculate_item_score(item_code, records):
    return weighted_score(selected_work_performance_records(records)).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP)
