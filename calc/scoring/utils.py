"""Region-independent arithmetic; no rates, eligibility or score limits."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

ZERO = Decimal("0")

def decimal_value(value, default="0"):
    try:
        if value in (None, ""):
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def clamp(value, lower=ZERO, upper=None):
    value = max(decimal_value(value), decimal_value(lower))
    if upper is not None:
        value = min(value, decimal_value(upper))
    return value


def add_months(day, months):
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def period_months_days(start_date, end_date):
    """Return inclusive calendar months and remaining days."""
    if not start_date or not end_date or end_date < start_date:
        return 0, 0
    exclusive_end = end_date + timedelta(days=1)
    months = (exclusive_end.year - start_date.year) * 12 + exclusive_end.month - start_date.month
    anchor = add_months(start_date, months)
    if anchor > exclusive_end:
        months -= 1
        anchor = add_months(start_date, months)
    return months, max((exclusive_end - anchor).days, 0)


def period_score(record, rates):
    months, days = period_months_days(record.start_date, record.end_date)
    month_rate, day_rate = rates
    return Decimal(month_rate) * months + Decimal(day_rate) * days
