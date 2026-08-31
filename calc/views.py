import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .catalog import (
    CATEGORIES,
    CATEGORY_BY_CODE,
    CURRENT_RULE_YEAR,
    IMPLEMENTED_REGION_CODES,
    ITEM_BY_CODE,
    REGIONS,
    REGION_BY_CODE,
)
from .forms import (
    KoreanHistoryForm,
    LoginForm,
    ProfileForm,
    RegisterForm,
    ScoreRecordInputForm,
)
from .models import (
    ItemStatus,
    KoreanHistoryQualification,
    Profile,
    RegionPortfolio,
    ScoreChange,
    ScoreRecord,
)
from .services import (
    calculate_item_score,
    calculate_item_score_from_records,
    calculate_record_score,
    common_training_credit_contributions,
    records_for_item,
    score_summary,
    score_summary_from_records,
    selected_training_job_records,
    selected_work_performance_records,
    training_job_record_score,
)


CURRENT_RULE_DATE = "2026. 2. 28."
CURRENT_ROSTER_DATE = "2026. 3. 31."
GUEST_SCORE_LOCAL_KEY = "promotionCalculator.guestRecords.v1"
MAX_GUEST_PAYLOAD_SIZE = 500_000


def _profile_for(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    if not profile.primary_region and profile.area in REGION_BY_CODE:
        profile.primary_region = profile.area
        profile.save(update_fields=["primary_region", "updated_at"])
    return profile


def _primary_region_or_redirect(request):
    profile = _profile_for(request.user)
    if profile.region not in REGION_BY_CODE:
        return profile, None, redirect("calc:region_select")
    return profile, profile.region, None


def _viewed_region(request, profile):
    region = request.session.get("view_region")
    if region not in REGION_BY_CODE:
        region = profile.region
    return region


def _region_bonus_disabled(region_code):
    return region_code not in IMPLEMENTED_REGION_CODES


def _total_max_for_region(region_code):
    return sum(
        (
            category["max_score"]
            for category in CATEGORIES
            if not (
                category["code"] == "regional_bonus"
                and _region_bonus_disabled(region_code)
            )
        ),
        Decimal("0"),
    )


def _category_for_region(category, region_code):
    category_view = dict(category)
    if category["code"] == "regional_bonus" and _region_bonus_disabled(region_code):
        category_view["name"] = f"{REGION_BY_CODE[region_code]['name']} 선택가산점"
        category_view["description"] = "이 지역의 선택가산점 기준은 아직 준비 중이며 입력·편집할 수 없습니다."
        category_view["input_disabled"] = True
    else:
        category_view["input_disabled"] = False
    return category_view


def _portfolio_for(user, region):
    return RegionPortfolio.objects.get_or_create(user=user, region=region)[0]


def _category_cards(summary, region_code):
    cards = []
    for category in CATEGORIES:
        score = summary["categories"][category["code"]]
        maximum = category["max_score"]
        category_view = _category_for_region(category, region_code)
        cards.append(
            {
                **category_view,
                "score": score,
                "percent": float(score / maximum * 100) if maximum else 0,
                "record_count": sum(
                    summary["record_counts"].get(item["code"], 0)
                    for item in category["items"]
                ),
            }
        )
    return cards


def _date_from_session(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _guest_record_from_entry(item, entry):
    record = ScoreRecord(
        scope=item["scope"],
        category=item["category"],
        item_code=item["code"],
        label=entry.get("label", ""),
        institution=entry.get("institution", ""),
        start_date=_date_from_session(entry.get("start_date")),
        end_date=_date_from_session(entry.get("end_date")),
        event_date=_date_from_session(entry.get("event_date")),
        input_data=entry.get("input_data", {}),
        memo=entry.get("memo", ""),
        evidence_available=bool(entry.get("evidence_available")),
        calculated_score=Decimal("0"),
    )
    record.guest_key = entry.get("key", "")
    record.calculated_score = calculate_record_score(record)
    return record


def _guest_record_to_entry(record, record_key=None):
    return {
        "key": record_key or uuid4().hex,
        "label": record.label,
        "institution": record.institution,
        "start_date": record.start_date.isoformat() if record.start_date else "",
        "end_date": record.end_date.isoformat() if record.end_date else "",
        "event_date": record.event_date.isoformat() if record.event_date else "",
        "input_data": record.input_data,
        "memo": record.memo,
        "evidence_available": record.evidence_available,
        "calculated_score": str(record.calculated_score),
    }


def _guest_storage_from_payload(raw_payload):
    if not raw_payload or len(raw_payload) > MAX_GUEST_PAYLOAD_SIZE:
        return {}
    try:
        submitted = json.loads(raw_payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(submitted, dict):
        return {}

    storage = {}
    allowed_input_keys = {"year", "variant", "value", "extra_value"}
    for item_code, submitted_entries in submitted.items():
        item = ITEM_BY_CODE.get(item_code)
        if not item or not isinstance(submitted_entries, list):
            continue
        entries = []
        for submitted_entry in submitted_entries[:200]:
            if not isinstance(submitted_entry, dict):
                continue
            raw_input_data = submitted_entry.get("input_data", {})
            if not isinstance(raw_input_data, dict):
                raw_input_data = {}
            entry = {
                "key": str(submitted_entry.get("key") or uuid4().hex)[:64],
                "label": str(submitted_entry.get("label", ""))[:160],
                "institution": str(submitted_entry.get("institution", ""))[:160],
                "start_date": str(submitted_entry.get("start_date", ""))[:10],
                "end_date": str(submitted_entry.get("end_date", ""))[:10],
                "event_date": str(submitted_entry.get("event_date", ""))[:10],
                "input_data": {
                    key: str(value)[:100]
                    for key, value in raw_input_data.items()
                    if key in allowed_input_keys
                },
                "memo": str(submitted_entry.get("memo", ""))[:5000],
                "evidence_available": submitted_entry.get("evidence_available")
                in {True, 1, "1", "true", "True"},
                "calculated_score": "0",
            }
            record = _guest_record_from_entry(item, entry)
            entry["calculated_score"] = str(record.calculated_score)
            entries.append(entry)
        storage[item_code] = entries
    return storage


def _guest_record_map(storage):
    record_map = {}
    for item_code, entries in storage.items():
        item = ITEM_BY_CODE.get(item_code)
        if item:
            record_map[item_code] = [
                _guest_record_from_entry(item, entry) for entry in entries
            ]
    return record_map


def _mark_selected_records(records, item_code):
    records = list(records)
    for record in records:
        record.is_score_selected = False
        record.is_completion_selected = False
        record.score_weight_percent = None
        record.applied_score = Decimal("0")
        record.display_calculated_score = record.calculated_score
    if item_code == "work_performance":
        weights = (34, 33, 33)
        for index, record in enumerate(selected_work_performance_records(records)):
            record.is_score_selected = True
            record.score_weight_percent = weights[index]
    elif item_code == "training_job":
        selected = selected_training_job_records(records)
        for record in records:
            record.display_calculated_score = training_job_record_score(record)
        for record in selected:
            record.is_completion_selected = True
        if selected:
            selected[0].is_score_selected = True
    elif item_code == "common_training_credit":
        for record, contribution in common_training_credit_contributions(records):
            record.applied_score = contribution
            record.is_score_selected = contribution > 0
    return records


def _guest_region(request):
    region = request.session.get("view_region")
    return region if region in REGION_BY_CODE else "jeonnam"


def _records_for_available_region(record_map, region_code):
    if not _region_bonus_disabled(region_code):
        return record_map
    return {
        item_code: records
        for item_code, records in record_map.items()
        if ITEM_BY_CODE[item_code]["category"] != "regional_bonus"
    }


def welcome(request):
    if request.user.is_authenticated:
        profile = _profile_for(request.user)
        if profile.region in REGION_BY_CODE:
            return redirect("calc:dashboard")
        return redirect("calc:region_select")
    return render(
        request,
        "calc/new/welcome.html",
        {"implemented_regions": [r for r in REGIONS if r["implemented"]]},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("calc:welcome")
    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth.login(request, form.get_user())
        profile = _profile_for(form.get_user())
        messages.success(request, "로그인했습니다.")
        if profile.region not in REGION_BY_CODE:
            return redirect("calc:region_select")
        request.session["view_region"] = profile.region
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("calc:dashboard")
    return render(request, "calc/new/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("calc:welcome")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth.login(request, user)
        messages.success(request, "가입이 완료되었습니다. 먼저 내 지역을 선택해주세요.")
        return redirect("calc:region_select")
    return render(request, "calc/new/register.html", {"form": form})


@require_POST
def logout_view(request):
    auth.logout(request)
    messages.success(request, "로그아웃했습니다.")
    return redirect("calc:welcome")


def region_select(request):
    profile = _profile_for(request.user) if request.user.is_authenticated else None
    if request.method == "POST":
        region = request.POST.get("region", "")
        action = request.POST.get("action", "view")
        if region not in REGION_BY_CODE:
            messages.error(request, "지역을 다시 선택해주세요.")
            return redirect("calc:region_select")

        request.session["view_region"] = region
        if not request.user.is_authenticated:
            if _region_bonus_disabled(region):
                messages.info(request, "전국 공통 항목은 계산할 수 있지만 이 지역의 선택가산점은 아직 준비 중입니다.")
            return redirect("calc:guest_score_index")

        if action == "set_primary" or not profile.region:
            previous_region = profile.region
            profile.primary_region = region
            profile.area = region
            profile.save(update_fields=["primary_region", "area", "updated_at"])
            _portfolio_for(request.user, region)
            if previous_region and previous_region != region:
                messages.success(request, "내 지역을 변경했습니다. 기존 기록은 참고 계산으로 보관됩니다.")
            else:
                messages.success(request, "내 지역을 설정했습니다.")
            if _region_bonus_disabled(region):
                messages.info(request, "이 지역의 선택가산점은 준비 중이어서 입력·편집할 수 없습니다.")
            return redirect("calc:dashboard")

        if profile.region == region:
            return redirect("calc:dashboard")

        _portfolio_for(request.user, region)
        if _region_bonus_disabled(region):
            messages.info(request, f"{REGION_BY_CODE[region]['name']} 참고 계산을 열었습니다. 선택가산점은 준비 중입니다.")
        else:
            messages.info(request, f"{REGION_BY_CODE[region]['name']} 참고 계산을 열었습니다.")
        return redirect("calc:score_index")

    return render(
        request,
        "calc/new/region_select.html",
        {
            "regions": REGIONS,
            "profile": profile,
            "selected_region": request.session.get("view_region"),
        },
    )


def guest_score_index(request, category_code=None):
    if request.user.is_authenticated:
        if category_code:
            return redirect("calc:score_index_category", category_code=category_code)
        return redirect("calc:score_index")

    storage = (
        _guest_storage_from_payload(request.POST.get("guest_payload", ""))
        if request.method == "POST"
        else {}
    )
    region_code = _guest_region(request)
    record_map = _records_for_available_region(
        _guest_record_map(storage),
        region_code,
    )
    summary = score_summary_from_records(record_map)
    selected_category = None
    if category_code:
        selected_category = CATEGORY_BY_CODE.get(category_code)
        if not selected_category:
            raise Http404("점수 영역을 찾을 수 없습니다.")
        selected_category = _category_for_region(selected_category, region_code)

    selected_item_rows = []
    if selected_category:
        for item in selected_category["items"]:
            selected_item_rows.append(
                {
                    "item": item,
                    "status": None,
                    "input_disabled": selected_category["input_disabled"] or item.get("input_disabled", False),
                    "record_count": summary["record_counts"].get(item["code"], 0),
                    "score": summary["items"].get(item["code"], Decimal("0")),
                }
            )

    return render(
        request,
        "calc/new/score_index.html",
        {
            "is_guest": True,
            "region": REGION_BY_CODE[region_code],
            "summary": summary,
            "total_max": _total_max_for_region(region_code),
            "category_cards": _category_cards(summary, region_code),
            "selected_category": selected_category,
            "selected_item_rows": selected_item_rows,
            "guest_storage": storage,
            "guest_hydrated": request.method == "POST",
            "guest_local_key": GUEST_SCORE_LOCAL_KEY,
        },
    )


def guest_score_item(request, item_code, record_key=None):
    if request.user.is_authenticated:
        if record_key:
            return redirect("calc:score_item", item_code=item_code)
        return redirect("calc:score_item", item_code=item_code)

    item = ITEM_BY_CODE.get(item_code)
    if not item:
        raise Http404("점수 항목을 찾을 수 없습니다.")
    region_code = _guest_region(request)
    regional_bonus_disabled = (
        item["category"] == "regional_bonus"
        and _region_bonus_disabled(region_code)
    )
    action = request.POST.get("action", "") if request.method == "POST" else ""
    storage = (
        _guest_storage_from_payload(request.POST.get("guest_payload", ""))
        if request.method == "POST"
        else {}
    )
    entries = list(storage.get(item_code, []))
    editing_entry = None
    if record_key:
        editing_entry = next(
            (entry for entry in entries if entry.get("key") == record_key),
            None,
        )
        if request.method == "POST" and editing_entry is None:
            raise Http404("임시 계산 항목을 찾을 수 없습니다.")

    editing_record = (
        _guest_record_from_entry(item, editing_entry) if editing_entry else None
    )
    form = None
    if not item.get("input_disabled") and not regional_bonus_disabled:
        form = ScoreRecordInputForm(
            item,
            request.POST if action == "record_form" else None,
            record=editing_record,
        )
        if action == "record_form" and form.is_valid():
            transient_record = ScoreRecord(
                scope=item["scope"],
                category=item["category"],
                item_code=item_code,
            )
            form.apply_to_record(transient_record)
            transient_record.calculated_score = calculate_record_score(transient_record)
            new_entry = _guest_record_to_entry(transient_record, record_key)
            if editing_entry:
                entries = [
                    new_entry if entry.get("key") == record_key else entry
                    for entry in entries
                ]
            else:
                entries.append(new_entry)
            storage[item_code] = entries
            return JsonResponse(
                {
                    "storage": storage,
                    "redirect_url": reverse(
                        "calc:guest_score_item",
                        kwargs={"item_code": item_code},
                    ),
                }
            )

    record_map = _records_for_available_region(
        _guest_record_map(storage),
        region_code,
    )
    records = _mark_selected_records(
        record_map.get(item_code, []),
        item_code,
    )
    item_score = calculate_item_score_from_records(item_code, records)
    category = _category_for_region(CATEGORY_BY_CODE[item["category"]], region_code)
    category_items = category["items"]
    index = category_items.index(item)
    previous_item = category_items[index - 1] if index > 0 else None
    next_item = category_items[index + 1] if index + 1 < len(category_items) else None

    qualification_score = None
    qualification_gap = None
    if item_code in {"training_qualification", "jeonnam_leadership"} and not regional_bonus_disabled:
        qualification_score = calculate_item_score_from_records(
            "training_qualification",
            record_map.get("training_qualification", []),
        )
        qualification_gap = max(Decimal("9") - qualification_score, Decimal("0"))

    return render(
        request,
        "calc/new/score_item.html",
        {
            "is_guest": True,
            "region": REGION_BY_CODE[region_code],
            "item": item,
            "category": category,
            "category_items": category_items,
            "records": records,
            "item_score": item_score,
            "form": form,
            "editing_record": editing_record,
            "status_object": None,
            "previous_item": previous_item,
            "next_item": next_item,
            "qualification_score": qualification_score,
            "qualification_gap": qualification_gap,
            "input_disabled": item.get("input_disabled", False) or regional_bonus_disabled,
            "input_disabled_reason": (
                f"{REGION_BY_CODE[region_code]['name']} 선택가산점 기준은 아직 준비 중입니다. 전국 공통 항목은 계속 계산할 수 있습니다."
                if regional_bonus_disabled
                else item.get("description", "")
            ),
            "regional_bonus_disabled": regional_bonus_disabled,
            "guest_storage": storage,
            "guest_hydrated": request.method == "POST",
            "guest_local_key": GUEST_SCORE_LOCAL_KEY,
        },
    )


@require_POST
def guest_delete_score_record(request, item_code, record_key):
    if request.user.is_authenticated:
        return redirect("calc:score_item", item_code=item_code)
    if item_code not in ITEM_BY_CODE:
        raise Http404("점수 항목을 찾을 수 없습니다.")
    item = ITEM_BY_CODE[item_code]
    if item["category"] == "regional_bonus" and _region_bonus_disabled(_guest_region(request)):
        return JsonResponse(
            {"error": "이 지역의 선택가산점은 아직 편집할 수 없습니다."},
            status=403,
        )
    storage = _guest_storage_from_payload(request.POST.get("guest_payload", ""))
    entries = storage.get(item_code, [])
    storage[item_code] = [
        entry for entry in entries if entry.get("key") != record_key
    ]
    return JsonResponse(
        {
            "storage": storage,
            "redirect_url": reverse(
                "calc:guest_score_item",
                kwargs={"item_code": item_code},
            ),
        }
    )


@require_POST
def guest_score_reset(request):
    if request.user.is_authenticated:
        return redirect("calc:score_index")
    return redirect("calc:guest_score_index")


@login_required
def dashboard(request):
    profile, region, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    request.session["view_region"] = region
    portfolio = _portfolio_for(request.user, region)
    summary = score_summary(request.user, portfolio)
    recent_records = ScoreRecord.objects.filter(user=request.user).filter(
        Q(portfolio__isnull=True) | Q(portfolio=portfolio)
    )[:5]
    qualification, _ = KoreanHistoryQualification.objects.get_or_create(user=request.user)
    total_max = _total_max_for_region(region)
    return render(
        request,
        "calc/new/dashboard.html",
        {
            "profile": profile,
            "portfolio": portfolio,
            "summary": summary,
            "category_cards": _category_cards(summary, region),
            "recent_records": recent_records,
            "qualification": qualification,
            "total_max": total_max,
            "rule_year": CURRENT_RULE_YEAR,
        },
    )


@login_required
def score_index(request, category_code=None):
    profile, _, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    region = _viewed_region(request, profile)
    portfolio = _portfolio_for(request.user, region)
    summary = score_summary(request.user, portfolio)
    selected_category = None
    if category_code:
        category = CATEGORY_BY_CODE.get(category_code)
        if not category:
            raise Http404("점수 영역을 찾을 수 없습니다.")
        selected_category = _category_for_region(category, region)
    selected_item_rows = []
    if selected_category:
        for item in selected_category["items"]:
            selected_item_rows.append(
                {
                    "item": item,
                    "status": _status_for_item(request.user, item, portfolio),
                    "input_disabled": selected_category["input_disabled"] or item.get("input_disabled", False),
                    "record_count": summary["record_counts"].get(item["code"], 0),
                    "score": summary["items"].get(item["code"], Decimal("0")),
                }
            )
    return render(
        request,
        "calc/new/score_index.html",
        {
            "profile": profile,
            "portfolio": portfolio,
            "region": REGION_BY_CODE[region],
            "summary": summary,
            "total_max": _total_max_for_region(region),
            "category_cards": _category_cards(summary, region),
            "selected_category": selected_category,
            "selected_item_rows": selected_item_rows,
        },
    )


def _status_for_item(user, item, portfolio):
    status_portfolio = portfolio if item["scope"] == "regional" else None
    return ItemStatus.objects.filter(
        user=user,
        portfolio=status_portfolio,
        item_code=item["code"],
    ).first()


@login_required
def score_item(request, item_code, record_id=None):
    item = ITEM_BY_CODE.get(item_code)
    if not item:
        raise Http404("점수 항목을 찾을 수 없습니다.")

    profile, _, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    region = _viewed_region(request, profile)
    portfolio = _portfolio_for(request.user, region)
    item_portfolio = portfolio if item["scope"] == "regional" else None
    regional_bonus_disabled = (
        item["category"] == "regional_bonus"
        and _region_bonus_disabled(region)
    )
    if request.method == "POST" and regional_bonus_disabled:
        messages.info(request, "이 지역의 선택가산점은 아직 입력·편집할 수 없습니다.")
        return redirect("calc:score_item", item_code=item_code)
    record = None
    if record_id:
        record = get_object_or_404(
            ScoreRecord,
            id=record_id,
            user=request.user,
            item_code=item_code,
            portfolio=item_portfolio,
        )

    if request.method == "POST" and request.POST.get("action") == "toggle_not_applicable":
        status = request.POST.get("status", ScoreRecord.Status.NOT_APPLICABLE)
        if status not in ScoreRecord.Status.values:
            status = ScoreRecord.Status.NOT_APPLICABLE
        status_object, _ = ItemStatus.objects.get_or_create(
            user=request.user,
            portfolio=item_portfolio,
            item_code=item_code,
        )
        status_object.status = status
        status_object.save()
        messages.success(request, "항목 상태를 저장했습니다.")
        return redirect("calc:score_item", item_code=item_code)

    if request.method == "POST" and request.POST.get("action") == "clear_item_status":
        ItemStatus.objects.filter(
            user=request.user,
            portfolio=item_portfolio,
            item_code=item_code,
        ).delete()
        messages.success(request, "항목 상태 표시를 해제했습니다.")
        return redirect("calc:score_item", item_code=item_code)

    form = None
    if not item.get("input_disabled") and not regional_bonus_disabled:
        form = ScoreRecordInputForm(item, request.POST or None, record=record)
        if request.method == "POST" and form.is_valid():
            before = score_summary(request.user, portfolio)
            if record is None:
                record = ScoreRecord(
                    user=request.user,
                    item_code=item_code,
                    category=item["category"],
                    scope=item["scope"],
                    portfolio=item_portfolio,
                )
            form.apply_to_record(record)
            record.calculated_score = calculate_record_score(record)
            record.full_clean()
            record.save()
            ItemStatus.objects.filter(
                user=request.user,
                portfolio=item_portfolio,
                item_code=item_code,
            ).delete()
            after = score_summary(request.user, portfolio)
            ScoreChange.objects.create(
                user=request.user,
                portfolio=item_portfolio,
                item_code=item_code,
                previous_item_score=before["items"][item_code],
                new_item_score=after["items"][item_code],
                previous_total=before["total"],
                new_total=after["total"],
            )
            messages.success(request, "기록을 저장했습니다.")
            return redirect("calc:score_item", item_code=item_code)

    records = _mark_selected_records(
        [] if regional_bonus_disabled else records_for_item(request.user, item, portfolio),
        item_code,
    )
    item_score = (
        Decimal("0")
        if regional_bonus_disabled
        else calculate_item_score(request.user, item_code, portfolio)
    )
    status_object = None if regional_bonus_disabled else _status_for_item(request.user, item, portfolio)
    category = _category_for_region(CATEGORY_BY_CODE[item["category"]], region)
    category_items = category["items"]
    index = category_items.index(item)
    previous_item = category_items[index - 1] if index > 0 else None
    next_item = category_items[index + 1] if index + 1 < len(category_items) else None

    qualification_score = None
    qualification_gap = None
    if item_code in {"training_qualification", "jeonnam_leadership"} and not regional_bonus_disabled:
        qualification_score = calculate_item_score(request.user, "training_qualification", portfolio)
        qualification_gap = max(Decimal("9") - qualification_score, Decimal("0"))

    return render(
        request,
        "calc/new/score_item.html",
        {
            "profile": profile,
            "portfolio": portfolio,
            "region": REGION_BY_CODE[region],
            "item": item,
            "category": category,
            "category_items": category_items,
            "records": records,
            "item_score": item_score,
            "form": form,
            "editing_record": record,
            "status_object": status_object,
            "previous_item": previous_item,
            "next_item": next_item,
            "qualification_score": qualification_score,
            "qualification_gap": qualification_gap,
            "input_disabled": item.get("input_disabled", False) or regional_bonus_disabled,
            "input_disabled_reason": (
                f"{REGION_BY_CODE[region]['name']} 선택가산점 기준은 아직 준비 중입니다. 전국 공통 항목은 계속 입력·저장할 수 있습니다."
                if regional_bonus_disabled
                else item.get("description", "")
            ),
            "regional_bonus_disabled": regional_bonus_disabled,
        },
    )


@login_required
@require_POST
def delete_score_record(request, record_id):
    record = get_object_or_404(ScoreRecord, id=record_id, user=request.user)
    item = ITEM_BY_CODE.get(record.item_code)
    if not item:
        raise Http404("점수 항목을 찾을 수 없습니다.")
    if (
        item["category"] == "regional_bonus"
        and record.portfolio
        and _region_bonus_disabled(record.portfolio.region)
    ):
        messages.info(request, "이 지역의 선택가산점은 아직 편집할 수 없습니다.")
        return redirect("calc:score_item", item_code=record.item_code)
    profile, _, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    region = record.portfolio.region if record.portfolio else _viewed_region(request, profile)
    portfolio = _portfolio_for(request.user, region)
    before = score_summary(request.user, portfolio)
    item_code = record.item_code
    item_portfolio = record.portfolio
    record.delete()
    after = score_summary(request.user, portfolio)
    ScoreChange.objects.create(
        user=request.user,
        portfolio=item_portfolio,
        item_code=item_code,
        previous_item_score=before["items"][item_code],
        new_item_score=after["items"][item_code],
        previous_total=before["total"],
        new_total=after["total"],
    )
    messages.success(request, "기록을 삭제하고 점수를 다시 계산했습니다.")
    return redirect("calc:score_item", item_code=item_code)


@login_required
def korean_history(request):
    profile, _, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    qualification, _ = KoreanHistoryQualification.objects.get_or_create(user=request.user)
    form = KoreanHistoryForm(request.POST or None, instance=qualification)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "한국사 자격요건을 저장했습니다.")
        return redirect("calc:korean_history")
    return render(
        request,
        "calc/new/korean_history.html",
        {"profile": profile, "qualification": qualification, "form": form},
    )


@login_required
def records_overview(request):
    profile, region, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    portfolio = _portfolio_for(request.user, region)
    summary = score_summary(request.user, portfolio)
    groups = []
    for category in CATEGORIES:
        item_groups = []
        for item in category["items"]:
            records = list(records_for_item(request.user, item, portfolio))
            item_groups.append(
                {
                    "item": item,
                    "records": records,
                    "score": summary["items"][item["code"]],
                }
            )
        groups.append(
            {
                "category": category,
                "items": item_groups,
                "score": summary["categories"][category["code"]],
            }
        )
    return render(
        request,
        "calc/new/records.html",
        {"profile": profile, "portfolio": portfolio, "summary": summary, "groups": groups},
    )


@login_required
def score_changes(request):
    profile, region, redirect_response = _primary_region_or_redirect(request)
    if redirect_response:
        return redirect_response
    portfolio = _portfolio_for(request.user, region)
    changes = ScoreChange.objects.filter(user=request.user).filter(
        Q(portfolio__isnull=True) | Q(portfolio=portfolio)
    )[:100]
    return render(
        request,
        "calc/new/score_changes.html",
        {"profile": profile, "portfolio": portfolio, "changes": changes},
    )


def resources(request):
    if request.user.is_authenticated:
        profile = _profile_for(request.user)
        region_code = _viewed_region(request, profile) if profile.region else request.session.get("view_region")
    else:
        profile = None
        region_code = request.GET.get("region") or request.session.get("view_region")
    if region_code not in REGION_BY_CODE:
        return redirect("calc:region_select")
    return render(
        request,
        "calc/new/resources.html",
        {
            "profile": profile,
            "region": REGION_BY_CODE[region_code],
            "rule_year": CURRENT_RULE_YEAR,
            "rule_date": CURRENT_RULE_DATE,
            "roster_date": CURRENT_ROSTER_DATE,
            "region_implemented": region_code in IMPLEMENTED_REGION_CODES,
        },
    )


@login_required
def account_settings(request):
    profile = _profile_for(request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "계정 설정을 저장했습니다.")
        return redirect("calc:account_settings")
    portfolios = RegionPortfolio.objects.filter(user=request.user)
    return render(
        request,
        "calc/new/account_settings.html",
        {"profile": profile, "form": form, "portfolios": portfolios},
    )


@login_required
@require_POST
def delete_account(request):
    if request.POST.get("confirmation") != "계정 삭제":
        messages.error(request, "확인 문구가 일치하지 않아 삭제하지 않았습니다.")
        return redirect("calc:account_settings")
    user = get_object_or_404(User, id=request.user.id)
    auth.logout(request)
    user.delete()
    messages.success(request, "계정과 개인 기록을 삭제했습니다.")
    return redirect("calc:welcome")


def legacy_common(request):
    return redirect("calc:score_index")


def legacy_area(request, *args, **kwargs):
    return redirect("calc:score_index_category", category_code="regional_bonus")
