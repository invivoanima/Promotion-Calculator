"""Load selected-region rules and records. No scoring policy lives here."""

from copy import copy

from .models import ScoreRecord
from .scoring.registry import RulesUnavailable, get_ruleset
from .scoring.utils import decimal_value, period_months_days


def _region_code(*, region_code=None, user=None, portfolio=None, records=()):
    if portfolio is not None:
        if region_code and portfolio.region != region_code:
            raise ValueError("계산 지역과 기록의 지역이 일치하지 않습니다.")
        region_code = portfolio.region
    if region_code:
        return region_code
    if user is not None:
        profile = getattr(user, "profile", None)
        if profile and profile.region:
            return profile.region
    for record in records:
        if record.portfolio_id:
            return record.portfolio.region
        if record.user_id:
            profile = getattr(record.user, "profile", None)
            if profile and profile.region:
                return profile.region
    raise RulesUnavailable(None)


def calculate_record_score(record, *, region_code=None):
    region = _region_code(region_code=region_code, records=[record])
    if record.portfolio_id and record.portfolio.region != region:
        raise ValueError("계산 지역과 기록의 지역이 일치하지 않습니다.")
    return get_ruleset(region).calculate_record_score(record)


def _prepare_records(records, rules):
    """Recompute from raw inputs for this region, leaving saved records intact."""
    prepared = []
    for original in records:
        if original.portfolio_id and original.portfolio.region != rules.REGION_CODE:
            raise ValueError("다른 지역의 기록을 계산할 수 없습니다.")
        record = copy(original)
        record.rule_region_code = rules.REGION_CODE
        record.calculated_score = rules.calculate_record_score(record)
        prepared.append(record)
    return prepared


def records_for_item(user, item, portfolio=None):
    queryset = ScoreRecord.objects.filter(user=user, item_code=item["code"])
    if item["scope"] == "regional":
        return queryset.filter(portfolio=portfolio)
    return queryset.filter(portfolio__isnull=True)


def calculate_item_score_from_records(item_code, records, *, region_code=None):
    records = list(records)
    rules = get_ruleset(_region_code(region_code=region_code, records=records))
    return rules.calculate_item_score_from_records(item_code, _prepare_records(records, rules))


def calculate_item_score(user, item_code, portfolio=None, *, region_code=None):
    region = _region_code(region_code=region_code, user=user, portfolio=portfolio)
    rules = get_ruleset(region)
    return calculate_item_score_from_records(
        item_code, records_for_item(user, rules.ITEM_BY_CODE[item_code], portfolio),
        region_code=region,
    )


def score_summary_from_records(record_map, *, region_code):
    rules = get_ruleset(region_code)
    prepared = {
        code: _prepare_records(record_map.get(code, []), rules)
        for code in rules.ITEM_BY_CODE
    }
    summary = {
        "region_code": rules.REGION_CODE,
        "rule_year": rules.RULE_YEAR,
        "items": {
            code: rules.calculate_item_score_from_records(code, records)
            for code, records in prepared.items()
        },
        "record_counts": {code: len(records) for code, records in prepared.items()},
    }
    return rules.finalize_summary(summary, prepared)


def score_summary(user, portfolio=None, *, region_code=None):
    region = _region_code(region_code=region_code, user=user, portfolio=portfolio)
    rules = get_ruleset(region)
    return score_summary_from_records({
        code: records_for_item(user, item, portfolio)
        for code, item in rules.ITEM_BY_CODE.items()
    }, region_code=region)


def mark_selected_records(records, item_code, *, region_code):
    rules = get_ruleset(region_code)
    return rules.mark_selected_records(_prepare_records(records, rules), item_code)


# Legacy helper entry points also dispatch through a region; none defaults to Jeonnam.
def _record_helper(name, record, region_code):
    rules = get_ruleset(_region_code(region_code=region_code, records=[record]))
    return getattr(rules, name)(record)


def _records_helper(name, records, region_code):
    records = list(records)
    rules = get_ruleset(_region_code(region_code=region_code, records=records))
    return getattr(rules, name)(_prepare_records(records, rules))


def training_job_record_score(record, *, region_code=None):
    return _record_helper("training_job_record_score", record, region_code)


def converted_training_score(raw_score, *, region_code):
    return get_ruleset(region_code).converted_training_score(raw_score)


def eligible_training_job_records(records, *, region_code=None):
    return _records_helper("eligible_training_job_records", records, region_code)


def selected_training_job_records(records, *, region_code=None):
    return _records_helper("selected_training_job_records", records, region_code)


def selected_work_performance_records(records, *, region_code=None):
    return _records_helper("selected_work_performance_records", records, region_code)


def common_training_credit_contributions(records, *, region_code=None):
    return _records_helper("common_training_credit_contributions", records, region_code)
