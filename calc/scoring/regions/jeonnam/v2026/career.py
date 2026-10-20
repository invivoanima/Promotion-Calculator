"""Jeonnam 2026 career rules."""

from decimal import Decimal
from calc.scoring.utils import period_score as _period_score
from .precision import ZERO, rounded


CAREER_RATES = {'base_ga': ('0.3555', '0.0118'),
 'base_na': ('0.3333', '0.0111'),
 'base_da': ('0.3111', '0.0103'),
 'excess_ga': ('0.1000', '0.0033'),
 'excess_na': ('0.0833', '0.0027'),
 'excess_da': ('0.0666', '0.0022')}


def calculate_record_score(record):
    rates = CAREER_RATES.get((record.input_data or {}).get("variant", "default"))
    return rounded(_period_score(record, rates)) if rates else ZERO


def calculate_item_score(item_code, records):
    base = sum((r.calculated_score for r in records if r.input_data.get("variant", "").startswith("base_")), ZERO)
    excess = sum((r.calculated_score for r in records if r.input_data.get("variant", "").startswith("excess_")), ZERO)
    return rounded(min(base, Decimal("64")) + min(excess, Decimal("6")))
