from .regions import REGIONS, REGION_BY_CODE
from .models import Profile
from .scoring.registry import get_ruleset, rules_available


def navigation_context(request):
    profile = None
    primary_region = ""
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        primary_region = profile.region
    viewed_region = request.session.get("view_region") or primary_region
    if not request.user.is_authenticated and request.path.startswith("/try/"):
        viewed_region = request.session.get("view_region") or "jeonnam"
        if viewed_region not in REGION_BY_CODE:
            viewed_region = "jeonnam"
    # Read the active provider so this also follows changed primary/reference regions.
    rules = get_ruleset(viewed_region) if rules_available(viewed_region) else None
    return {
        "app_regions": REGIONS,
        "app_profile": profile,
        "primary_region": REGION_BY_CODE.get(primary_region),
        "viewed_region": REGION_BY_CODE.get(viewed_region),
        "scoring_rule_notice": getattr(rules, "RULE_NOTICE", ""),
        "is_reference_region": bool(
            primary_region and viewed_region and primary_region != viewed_region
        ),
    }
