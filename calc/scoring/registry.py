"""Explicit region/year routing. An unavailable region never falls back."""

from functools import lru_cache
from importlib import import_module


REGION_CODES = (
    "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", "ulsan", "sejong",
    "gyeonggi", "gangwon", "chungbuk", "chungnam", "jeonbuk", "jeonnam",
    "gyeongbuk", "gyeongnam", "jeju",
)
ACTIVE_RULE_YEARS = {code: 2026 for code in REGION_CODES}
RULE_MODULES = {
    (code, 2026): f"calc.scoring.regions.{code}.v2026" for code in REGION_CODES
}


class RulesUnavailable(ValueError):
    def __init__(self, region_code, year=None):
        self.region_code = region_code
        self.year = year
        super().__init__(f"계산 기준이 준비되지 않은 지역·연도입니다: {region_code or '미선택'} / {year or '미지정'}")


def rules_available(region_code, year=None):
    year = year if year is not None else ACTIVE_RULE_YEARS.get(region_code)
    return (region_code, year) in RULE_MODULES


@lru_cache(maxsize=None)
def get_ruleset(region_code, year=None):
    year = year if year is not None else ACTIVE_RULE_YEARS.get(region_code)
    module_path = RULE_MODULES.get((region_code, year))
    if not module_path:
        raise RulesUnavailable(region_code, year)
    rules = import_module(module_path)
    if (rules.REGION_CODE, rules.RULE_YEAR) != (region_code, year):
        raise ValueError("등록된 계산 모듈의 지역·연도가 일치하지 않습니다.")
    return rules
