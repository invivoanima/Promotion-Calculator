"""Local career calculation; recognized periods/grades are entered explicitly."""
from decimal import Decimal, ROUND_HALF_UP
from calc.scoring.utils import period_months_days, period_score
from .precision import ZERO

CAREER_RATES = {
    "base_ga": ("0.3555", "0.0118"), "base_na": ("0.3333", "0.0111"),
    "base_da": ("0.3111", "0.0103"), "excess_ga": ("0.1000", "0.0033"),
    "excess_na": ("0.0833", "0.0027"), "excess_da": ("0.0666", "0.0022"),
}
FULL_PERIOD_SCORES = {
    "base_ga": Decimal("64"), "base_na": Decimal("60"), "base_da": Decimal("56"),
    "excess_ga": Decimal("6"), "excess_na": Decimal("5"), "excess_da": Decimal("4"),
}

def rounded_career(value):
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

def calculate_record_score(record):
    rates = CAREER_RATES.get((record.input_data or {}).get("variant"))
    return rounded_career(period_score(record, rates)) if rates else ZERO

def calculate_item_score(item_code, records):
    amounts = {}
    months_by_grade = {}
    days_by_grade = {}
    for record in records:
        grade = (record.input_data or {}).get("variant")
        if grade not in CAREER_RATES:
            continue
        months, days = period_months_days(record.start_date, record.end_date)
        months_by_grade[grade] = months_by_grade.get(grade, 0) + months
        days_by_grade[grade] = days_by_grade.get(grade, 0) + days
        # Round after summing recognized periods, rather than each row.
        amounts[grade] = amounts.get(grade, ZERO) + period_score(record, CAREER_RATES[grade])
    for grade in amounts:
        limit_months = 180 if grade.startswith("base_") else 60
        if months_by_grade[grade] + days_by_grade[grade] // 30 >= limit_months:
            amounts[grade] = FULL_PERIOD_SCORES[grade]
    basic = min(sum((value for grade, value in amounts.items() if grade.startswith("base_")), ZERO), Decimal("64"))
    excess = min(sum((value for grade, value in amounts.items() if grade.startswith("excess_")), ZERO), Decimal("6"))
    return rounded_career(basic + excess)
