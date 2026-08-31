from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import migrations


SIX_PLACES = Decimal("0.000001")


def converted_score(raw_value):
    try:
        raw_score = Decimal(str(raw_value or 0))
    except (InvalidOperation, TypeError, ValueError):
        raw_score = Decimal("0")
    if raw_score > 95:
        return Decimal("100")
    if raw_score > 90:
        return Decimal("95")
    if raw_score > 85:
        return Decimal("90")
    return Decimal("85")


def rebase_to_six_point_scale(apps, schema_editor):
    ScoreRecord = apps.get_model("calc", "ScoreRecord")
    for record in ScoreRecord.objects.filter(item_code="training_job").iterator():
        raw_value = (record.input_data or {}).get("value")
        record.calculated_score = (
            Decimal("6") * converted_score(raw_value) / Decimal("100")
        ).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
        record.save(update_fields=["calculated_score"])


def restore_hundred_point_scale(apps, schema_editor):
    ScoreRecord = apps.get_model("calc", "ScoreRecord")
    for record in ScoreRecord.objects.filter(item_code="training_job").iterator():
        raw_value = (record.input_data or {}).get("value")
        record.calculated_score = converted_score(raw_value).quantize(
            SIX_PLACES,
            rounding=ROUND_HALF_UP,
        )
        record.save(update_fields=["calculated_score"])


class Migration(migrations.Migration):
    dependencies = [("calc", "0007_expand_region_choices")]

    operations = [
        migrations.RunPython(
            rebase_to_six_point_scale,
            restore_hundred_point_scale,
        )
    ]
