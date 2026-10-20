"""Repair stored scores that bypassed the mixed professional-activity formula."""

from calendar import monthrange
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import migrations


# Keep this snapshot independent of future changes to the live calculation rules.
FIXED_SCORES = {
    "class_award": "0.25", "it_certificate": "0.25",
    "competition_gold": "0.25", "competition_silver": "0.1875",
    "competition_bronze": "0.125", "certificate_1": "0.3",
    "certificate_2": "0.2", "certificate_3": "0.1",
}
PERIOD_RATES = {
    "regular": ("0.0105", "0.00035"),
    "student_teacher": ("0.0315", "0.00105"),
    "youth": ("0.0053", "0.000177"),
    "hospital": ("0.0084", "0.00028"),
    "special_school": ("0.0084", "0.00028"),
    "special_class": ("0.0042", "0.00014"),
    "integrated_class": ("0.0021", "0.00007"),
    "leadership_extra": ("0.003", "0.0001"),
}


def record_score(record):
    data = record.input_data or {}
    variant = data.get("variant", "")
    try:
        raw_value = data.get("value")
        value = Decimal("1") if raw_value in (None, "") else Decimal(str(raw_value))
    except (InvalidOperation, TypeError, ValueError):
        value = Decimal("1")
    if variant in FIXED_SCORES:
        count = max(value, Decimal("1")) if variant.startswith("competition_") else Decimal("1")
        return Decimal(FIXED_SCORES[variant]) * count
    if variant in {"school_power", "good_lesson_extra"}:
        return Decimal("0.036" if variant == "school_power" else "0.02") * value
    if variant not in PERIOD_RATES or not record.start_date or not record.end_date:
        return Decimal("0")
    if record.end_date < record.start_date:
        return Decimal("0")
    start = record.start_date
    end = record.end_date + timedelta(days=1)
    months = (end.year - start.year) * 12 + end.month - start.month

    def anchor_for(month_count):
        year, month = divmod(start.month - 1 + month_count, 12)
        year += start.year
        month += 1
        return start.replace(year=year, month=month, day=min(start.day, monthrange(year, month)[1]))

    anchor = anchor_for(months)
    if anchor > end:
        months -= 1
        anchor = anchor_for(months)
    month_rate, day_rate = PERIOD_RATES[variant]
    return Decimal(month_rate) * months + Decimal(day_rate) * max((end - anchor).days, 0)


def recalculate_scores(apps, schema_editor):
    ScoreRecord = apps.get_model("calc", "ScoreRecord")
    records = ScoreRecord.objects.using(schema_editor.connection.alias).filter(
        item_code="jeonnam_professional_activity"
    )
    for record in records.iterator():
        score = record_score(record).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        if record.calculated_score != score:
            records.filter(pk=record.pk).update(calculated_score=score)


class Migration(migrations.Migration):
    dependencies = [("calc", "0010_auditpermission_operationlog_legalconsent")]

    operations = [migrations.RunPython(recalculate_scores, migrations.RunPython.noop)]
