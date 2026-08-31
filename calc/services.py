"""Server-side score calculations.

The calculator intentionally remains an estimate, but saved scores are always
derived again on the server instead of trusting a hidden browser total.
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .catalog import CATEGORIES, CURRENT_RULE_YEAR, ITEM_BY_CODE
from .models import ScoreRecord


ZERO = Decimal("0")
SIX_PLACES = Decimal("0.000001")


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


def rounded(value):
    return decimal_value(value).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


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


PERIOD_RATES = {
    "common_research_school": {"default": ("0.018", "0.0006")},
    "common_foreign_institution": {"default": ("0.015", "0.0005")},
    "jeonnam_island_remote": {
        "island_ga": ("0.167", "0.0056"),
        "island_na": ("0.125", "0.0042"),
        "island_da": ("0.084", "0.0028"),
        "island_ra": ("0.063", "0.0021"),
        "remote_ga": ("0.084", "0.0028"),
        "remote_na": ("0.063", "0.0021"),
        "remote_da": ("0.050", "0.0017"),
        "remote_ra": ("0.042", "0.0014"),
    },
    "jeonnam_rural": {
        "rural_1": ("0.012", "0.0004"),
        "rural_2": ("0.008", "0.00027"),
        "rural_3": ("0.006", "0.0002"),
        "rural_add": ("0.002", "0.000067"),
    },
    "jeonnam_leadership": {
        "leadership_base": ("0.012", "0.0004"),
        "leadership_supplement": ("0.003", "0.0001"),
    },
    "jeonnam_designated_research": {
        "superintendent": ("0.0167", "0.00056"),
        "district": ("0.0139", "0.00047"),
    },
    "jeonnam_residence": {
        "solo": ("0.0016", "0.000053"),
        "family": ("0.0025", "0.000083"),
    },
}

CAREER_RATES = {
    "base_ga": ("0.3555", "0.0118"),
    "base_na": ("0.3333", "0.0111"),
    "base_da": ("0.3111", "0.0103"),
    "excess_ga": ("0.1000", "0.0033"),
    "excess_na": ("0.0833", "0.0027"),
    "excess_da": ("0.0666", "0.0022"),
}

DIRECT_VARIANT_SCORES = {
    "training_research": {
        "score_3": "3",
        "score_1_5": "1.5",
        "score_1": "1",
        "research_1_5": "1.5",
        "research_1_25": "1.25",
        "research_1_05": "1.05",
        "research_1": "1",
        "research_0_875": "0.875",
        "research_0_75": "0.75",
        "research_0_7": "0.7",
        "research_0_625": "0.625",
        "research_0_525": "0.525",
        "research_0_5": "0.5",
        "research_0_45": "0.45",
        "research_0_375": "0.375",
        "research_0_35": "0.35",
        "research_0_3": "0.3",
        "research_0_25": "0.25",
        "research_0_225": "0.225",
        "research_0_15": "0.15",
        "score_0_75": "0.75",
        "score_0_7": "0.7",
        "score_0_5": "0.5",
        "score_0_45": "0.45",
        "score_0_375": "0.375",
        "score_0_3": "0.3",
        "score_0_25": "0.25",
        "score_0_225": "0.225",
        "score_0_15": "0.15",
    },
    "jeonnam_professional_activity": {
        "class_award": "0.25",
        "it_certificate": "0.25",
        "competition_gold": "0.25",
        "competition_silver": "0.1875",
        "competition_bronze": "0.125",
        "certificate_1": "0.3",
        "certificate_2": "0.2",
        "certificate_3": "0.1",
    },
    "jeonnam_good_lesson": {
        "school": "0.06",
        "regional": "0.08",
    },
}


def _period_score(record, rates):
    months, days = period_months_days(record.start_date, record.end_date)
    month_rate, day_rate = rates
    return Decimal(month_rate) * months + Decimal(day_rate) * days


def _professional_activity_score(record):
    variant = record.input_data.get("variant", "")
    value = decimal_value(record.input_data.get("value"), "1")
    if variant in DIRECT_VARIANT_SCORES["jeonnam_professional_activity"]:
        return Decimal(DIRECT_VARIANT_SCORES["jeonnam_professional_activity"][variant]) * max(value, Decimal("1"))
    if variant == "good_lesson_extra":
        return Decimal("0.02") * value
    if variant == "school_power":
        return Decimal("0.036") * value
    period_rates = {
        "regular": ("0.0105", "0.00035"),
        "student_teacher": ("0.0315", "0.00105"),
        "youth": ("0.0053", "0.000177"),
        "hospital": ("0.0084", "0.00028"),
        "special_school": ("0.0084", "0.00028"),
        "special_class": ("0.0042", "0.00014"),
        "integrated_class": ("0.0021", "0.00007"),
        "leadership_extra": ("0.003", "0.0001"),
    }
    if variant in period_rates:
        return _period_score(record, period_rates[variant])
    return ZERO


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
    code = record.item_code
    data = record.input_data or {}
    variant = data.get("variant", "default")
    value = decimal_value(data.get("value"))

    if code == "career_history":
        rates = CAREER_RATES.get(variant)
        return rounded(_period_score(record, rates)) if rates else ZERO
    if code == "work_performance":
        return rounded(clamp(value, upper="100"))
    if code == "training_qualification":
        raw = clamp(value, upper="100")
        return rounded(clamp(Decimal("9") - (Decimal("100") - raw) * Decimal("0.025"), upper="9"))
    if code == "training_job":
        return training_job_record_score(record)
    if code in DIRECT_VARIANT_SCORES:
        point = Decimal(DIRECT_VARIANT_SCORES[code].get(variant, "0"))
        if code == "jeonnam_good_lesson":
            point *= max(value, Decimal("1"))
        return rounded(point)
    if code in PERIOD_RATES:
        rates = PERIOD_RATES[code].get(variant) or PERIOD_RATES[code].get("default")
        return rounded(_period_score(record, rates)) if rates else ZERO
    if code == "common_training_credit":
        return rounded(value * Decimal("0.02"))
    if code == "common_school_violence":
        return Decimal("0.1")
    if code == "jeonnam_professional_activity":
        return rounded(_professional_activity_score(record))
    return ZERO


def records_for_item(user, item, portfolio=None):
    queryset = ScoreRecord.objects.filter(user=user, item_code=item["code"])
    if item["scope"] == "regional":
        return queryset.filter(portfolio=portfolio)
    return queryset.filter(portfolio__isnull=True)


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


def common_training_credit_contributions(records):
    """Allocate the annual 0.08 and overall 0.8 caps to visible records."""
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
        annual_remaining = max(Decimal("0.08") - yearly_used.get(year, ZERO), ZERO)
        overall_remaining = max(Decimal("0.8") - overall_used, ZERO)
        contribution = min(
            max(record.calculated_score, ZERO),
            annual_remaining,
            overall_remaining,
        )
        contributions[id(record)] = contribution
        yearly_used[year] = yearly_used.get(year, ZERO) + contribution
        overall_used += contribution
    return [(record, contributions.get(id(record), ZERO)) for record in records]


def calculate_item_score_from_records(item_code, records):
    """Aggregate one item's score from saved or unsaved record objects."""
    item = ITEM_BY_CODE[item_code]
    records = list(records)
    if not records or item.get("input_disabled"):
        return ZERO

    if item_code == "career_history":
        base = sum((record.calculated_score for record in records if record.input_data.get("variant", "").startswith("base_")), ZERO)
        excess = sum((record.calculated_score for record in records if record.input_data.get("variant", "").startswith("excess_")), ZERO)
        return rounded(min(base, Decimal("64")) + min(excess, Decimal("6")))

    if item_code == "work_performance":
        selected = selected_work_performance_records(records)
        weights = [Decimal("0.34"), Decimal("0.33"), Decimal("0.33")]
        return rounded(sum((record.calculated_score * weights[index] for index, record in enumerate(selected)), ZERO))

    if item_code == "training_qualification":
        return rounded(max((record.calculated_score for record in records), default=ZERO))

    if item_code == "training_job":
        selected = selected_training_job_records(records)
        completion_points = Decimal("6") * len(selected)
        score_points = training_job_record_score(selected[0]) if selected else ZERO
        return rounded(min(completion_points + score_points, Decimal("18")))

    if item_code == "common_training_credit":
        return rounded(
            sum(
                (
                    contribution
                    for _, contribution in common_training_credit_contributions(records)
                ),
                ZERO,
            )
        )

    if item_code == "common_school_violence":
        recognized_years = {
            str(
                record.input_data.get("year")
                or record.event_date
                or getattr(record, "guest_key", None)
                or record.id
            )
            for record in records
        }
        return rounded(min(Decimal("0.1") * len(recognized_years), item["max_score"]))

    if item_code == "jeonnam_rural":
        base = sum((record.calculated_score for record in records if record.input_data.get("variant") != "rural_add"), ZERO)
        additional = sum((record.calculated_score for record in records if record.input_data.get("variant") == "rural_add"), ZERO)
        return rounded(min(base, Decimal("0.85")) + min(additional, Decimal("0.15")))

    if item_code == "jeonnam_leadership":
        base = sum((record.calculated_score for record in records if record.input_data.get("variant") == "leadership_base"), ZERO)
        supplement = sum((record.calculated_score for record in records if record.input_data.get("variant") == "leadership_supplement"), ZERO)
        return rounded(min(base, Decimal("1")) + min(supplement, Decimal("0.25")))

    if item_code == "jeonnam_professional_activity":
        per_variant = {}
        for record in records:
            variant = record.input_data.get("variant", "")
            per_variant[variant] = per_variant.get(variant, ZERO) + record.calculated_score
        total = sum((min(score, Decimal("0.5")) for score in per_variant.values()), ZERO)
        return rounded(min(total, item["max_score"]))

    total = sum((record.calculated_score for record in records), ZERO)
    return rounded(min(total, item["max_score"]))


def calculate_item_score(user, item_code, portfolio=None):
    item = ITEM_BY_CODE[item_code]
    records = records_for_item(user, item, portfolio)
    return calculate_item_score_from_records(item_code, records)


def score_summary_from_records(record_map):
    """Build a complete score summary from an item-code-to-records mapping."""
    category_scores = {}
    item_scores = {}
    record_counts = {}

    for category in CATEGORIES:
        category_total = ZERO
        for item in category["items"]:
            records = list(record_map.get(item["code"], []))
            score = calculate_item_score_from_records(item["code"], records)
            item_scores[item["code"]] = score
            record_counts[item["code"]] = len(records)
            category_total += score
        category_scores[category["code"]] = rounded(
            min(category_total, category["max_score"])
        )

    return {
        "categories": category_scores,
        "items": item_scores,
        "record_counts": record_counts,
        "total": rounded(sum(category_scores.values(), ZERO)),
    }


def score_summary(user, portfolio=None):
    record_map = {
        item["code"]: records_for_item(user, item, portfolio)
        for category in CATEGORIES
        for item in category["items"]
    }
    return score_summary_from_records(record_map)
