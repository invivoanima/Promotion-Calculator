"""Catalog access always requires the selected region."""

from .scoring.registry import get_ruleset


def get_item(item_code, *, region_code, year=None):
    return get_ruleset(region_code, year).ITEM_BY_CODE.get(item_code)


def get_category(category_code, *, region_code, year=None):
    return get_ruleset(region_code, year).CATEGORY_BY_CODE.get(category_code)
