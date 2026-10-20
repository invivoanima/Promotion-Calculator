"""Selectable regions; availability comes from the rule registry."""

REGIONS = [
    {"code": "seoul", "name": "서울특별시", "implemented": False},
    {"code": "busan", "name": "부산광역시", "implemented": False},
    {"code": "daegu", "name": "대구광역시", "implemented": False},
    {"code": "incheon", "name": "인천광역시", "implemented": False},
    {"code": "gwangju", "name": "광주광역시", "implemented": False},
    {"code": "daejeon", "name": "대전광역시", "implemented": False},
    {"code": "ulsan", "name": "울산광역시", "implemented": False},
    {"code": "sejong", "name": "세종특별자치시", "implemented": False},
    {"code": "gyeonggi", "name": "경기도", "implemented": False},
    {"code": "gangwon", "name": "강원특별자치도", "implemented": False},
    {"code": "chungbuk", "name": "충청북도", "implemented": False},
    {"code": "chungnam", "name": "충청남도", "implemented": False},
    {"code": "jeonbuk", "name": "전북특별자치도", "implemented": False},
    {"code": "jeonnam", "name": "전라남도", "implemented": True},
    {"code": "gyeongbuk", "name": "경상북도", "implemented": False},
    {"code": "gyeongnam", "name": "경상남도", "implemented": False},
    {"code": "jeju", "name": "제주특별자치도", "implemented": False},
]

from .scoring.registry import ACTIVE_RULE_YEARS, get_ruleset, rules_available

for region in REGIONS:
    region["implemented"] = rules_available(region["code"])
    region["rule_year"] = ACTIVE_RULE_YEARS.get(region["code"])
    rules = get_ruleset(region["code"]) if region["implemented"] else None
    region["regional_bonus_available"] = getattr(rules, "REGIONAL_BONUS_AVAILABLE", False)
    region["verification_status"] = getattr(rules, "VERIFICATION_STATUS", "unavailable")
    region["rule_notice"] = getattr(rules, "RULE_NOTICE", "")

REGION_BY_CODE = {region["code"]: region for region in REGIONS}
IMPLEMENTED_REGION_CODES = {region["code"] for region in REGIONS if region["implemented"]}
