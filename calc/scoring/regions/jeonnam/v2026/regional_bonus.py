"""Jeonnam 2026 regional bonus rules."""

from decimal import Decimal
from calc.scoring.utils import decimal_value, period_score as _period_score
from .precision import ZERO, rounded
from .catalog import ITEM_BY_CODE


PERIOD_RATES = {'jeonnam_island_remote': {'island_ga': ('0.167', '0.0056'),
                           'island_na': ('0.125', '0.0042'),
                           'island_da': ('0.084', '0.0028'),
                           'island_ra': ('0.063', '0.0021'),
                           'remote_ga': ('0.084', '0.0028'),
                           'remote_na': ('0.063', '0.0021'),
                           'remote_da': ('0.050', '0.0017'),
                           'remote_ra': ('0.042', '0.0014')},
 'jeonnam_rural': {'rural_1': ('0.012', '0.0004'),
                   'rural_2': ('0.008', '0.00027'),
                   'rural_3': ('0.006', '0.0002'),
                   'rural_add': ('0.002', '0.000067')},
 'jeonnam_leadership': {'leadership_base': ('0.012', '0.0004'),
                        'leadership_supplement': ('0.003', '0.0001')},
 'jeonnam_designated_research': {'superintendent': ('0.0167', '0.00056'),
                                 'district': ('0.0139', '0.00047')},
 'jeonnam_residence': {'solo': ('0.0016', '0.000053'), 'family': ('0.0025', '0.000083')}}

DIRECT_VARIANT_SCORES = {'jeonnam_professional_activity': {'class_award': '0.25',
                                   'it_certificate': '0.25',
                                   'competition_gold': '0.25',
                                   'competition_silver': '0.1875',
                                   'competition_bronze': '0.125',
                                   'certificate_1': '0.3',
                                   'certificate_2': '0.2',
                                   'certificate_3': '0.1'},
 'jeonnam_good_lesson': {'school': '0.06', 'regional': '0.08'}}


def _professional_activity_score(record):
    variant = record.input_data.get("variant", "")
    value = decimal_value(record.input_data.get("value"), "1")
    if variant in DIRECT_VARIANT_SCORES["jeonnam_professional_activity"]:
        point = Decimal(DIRECT_VARIANT_SCORES["jeonnam_professional_activity"][variant])
        if variant.startswith("competition_"):
            point *= max(value, Decimal("1"))
        return point
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


def calculate_record_score(record):
    code = record.item_code
    data = record.input_data or {}
    variant = data.get("variant", "default")
    if code == "jeonnam_professional_activity":
        return rounded(_professional_activity_score(record))
    if code == "jeonnam_good_lesson":
        return rounded(Decimal(DIRECT_VARIANT_SCORES[code].get(variant, "0")) * max(decimal_value(data.get("value")), Decimal("1")))
    rates = PERIOD_RATES.get(code, {}).get(variant)
    return rounded(_period_score(record, rates)) if rates else ZERO


def calculate_item_score(item_code, records):
    if item_code == "jeonnam_rural":
        base = sum((r.calculated_score for r in records if r.input_data.get("variant") != "rural_add"), ZERO)
        additional = sum((r.calculated_score for r in records if r.input_data.get("variant") == "rural_add"), ZERO)
        return rounded(min(base, Decimal("0.85")) + min(additional, Decimal("0.15")))
    if item_code == "jeonnam_leadership":
        base = sum((r.calculated_score for r in records if r.input_data.get("variant") == "leadership_base"), ZERO)
        supplement = sum((r.calculated_score for r in records if r.input_data.get("variant") == "leadership_supplement"), ZERO)
        return rounded(min(base, Decimal("1")) + min(supplement, Decimal("0.25")))
    if item_code == "jeonnam_professional_activity":
        per_variant = {}
        for record in records:
            variant = record.input_data.get("variant", "")
            per_variant[variant] = per_variant.get(variant, ZERO) + record.calculated_score
        total = sum((min(score, Decimal("0.5")) for score in per_variant.values()), ZERO)
        return rounded(min(total, ITEM_BY_CODE[item_code]["max_score"]))
    return rounded(min(sum((record.calculated_score for record in records), ZERO), ITEM_BY_CODE[item_code]["max_score"]))
