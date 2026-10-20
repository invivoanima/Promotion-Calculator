from django import template

from calc.regions import REGION_BY_CODE
from calc.scoring.registry import RulesUnavailable, get_ruleset


register = template.Library()


@register.filter
def dict_get(mapping, key):
    if not mapping:
        return None
    return mapping.get(key)


@register.filter
def item_name(item_code, region_code=None):
    try:
        item = get_ruleset(region_code).ITEM_BY_CODE.get(item_code)
    except RulesUnavailable:
        item = None
    return item["name"] if item else item_code


@register.filter
def region_name(region_code):
    region = REGION_BY_CODE.get(region_code)
    return region["name"] if region else region_code


@register.filter
def input_summary(record):
    data = record.input_data or {}
    parts = []
    region_code = getattr(record, "rule_region_code", None)
    if not region_code and record.portfolio_id:
        region_code = record.portfolio.region
    if not region_code and record.user_id:
        profile = getattr(record.user, "profile", None)
        region_code = profile.region if profile else None
    try:
        item = get_ruleset(region_code).ITEM_BY_CODE.get(record.item_code, {})
    except RulesUnavailable:
        item = {}
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
