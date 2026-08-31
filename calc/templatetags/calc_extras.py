from django import template

from calc.catalog import ITEM_BY_CODE, REGION_BY_CODE


register = template.Library()


@register.filter
def dict_get(mapping, key):
    if not mapping:
        return None
    return mapping.get(key)


@register.filter
def item_name(item_code):
    item = ITEM_BY_CODE.get(item_code)
    return item["name"] if item else item_code


@register.filter
def region_name(region_code):
    region = REGION_BY_CODE.get(region_code)
    return region["name"] if region else region_code


@register.filter
def input_summary(record):
    data = record.input_data or {}
    parts = []
    item = ITEM_BY_CODE.get(record.item_code, {})
    variant = data.get("variant")
    choices = item.get("fields", {}).get("variant", {}).get("choices", [])
    choice_map = dict(choices)
    if variant:
        parts.append(choice_map.get(variant, variant))
    if data.get("year"):
        parts.append(f"{data['year']}년")
    if data.get("value"):
        if record.item_code == "training_job":
            parts.append(f"원점수 {data['value']}점")
        else:
            parts.append(str(data["value"]))
    if record.item_code == "training_job" and data.get("extra_value"):
        parts.append(f"{data['extra_value']}시간")
    return " · ".join(parts)
