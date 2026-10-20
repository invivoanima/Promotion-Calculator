"""Jeonnam 2026 work rules."""

from decimal import Decimal
from calc.scoring.utils import clamp
from .precision import ZERO, rounded
from .catalog import CURRENT_RULE_YEAR


def selected_work_performance_records(records):
    """Return the best three scores from the five most recent recorded years."""
    best_by_year = {}
    for record in records:
        try:
            year = int((record.input_data or {}).get("year") or 0)
        except (TypeError, ValueError):
            continue
        if year <= 0:
            continue
        current = best_by_year.get(year)
        if current is None or record.calculated_score > current.calculated_score:
            best_by_year[year] = record

    latest_year = CURRENT_RULE_YEAR - 1
    recent_five_years = [
        year
        for year in range(latest_year, latest_year - 5, -1)
        if year in best_by_year
    ]
    recent_records = [best_by_year[year] for year in recent_five_years]
    selected = sorted(
        recent_records,
        key=lambda record: (
            record.calculated_score,
            int((record.input_data or {}).get("year") or 0),
        ),
        reverse=True,
    )[:3]
    return sorted(
        selected,
        key=lambda record: int((record.input_data or {}).get("year") or 0),
        reverse=True,
    )


def calculate_record_score(record):
    return rounded(clamp((record.input_data or {}).get("value"), upper="100"))


def calculate_item_score(item_code, records):
    selected = selected_work_performance_records(records)
    weights = [Decimal("0.34"), Decimal("0.33"), Decimal("0.33")]
    return rounded(sum((record.calculated_score * weights[index] for index, record in enumerate(selected)), ZERO))
