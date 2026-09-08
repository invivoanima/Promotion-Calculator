import json
import os
from datetime import date, timedelta
from decimal import Decimal
from functools import wraps
from uuid import uuid4

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import get_valid_filename
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
    NoticeForm,
    ProfileForm,
    RegisterForm,
    ScoreRecordInputForm,
    SuggestionForm,
)
from .models import (
    AccessLog,
    ItemStatus,
    KoreanHistoryQualification,
    Notice,
    Profile,
    RegionPortfolio,
    ScoreChange,
    ScoreRecord,
    Suggestion,
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
        {
            "implemented_regions": [r for r in REGIONS if r["implemented"]],
            "latest_notices": Notice.objects.filter(is_published=True).order_by(
                "-is_pinned", "-published_at", "-date"
            )[:3],
        },
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
            "latest_notices": Notice.objects.filter(is_published=True).order_by(
                "-is_pinned", "-published_at", "-date"
            )[:3],
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


# ---------------------------------------------------------------------------
# Public notices and member suggestions
# ---------------------------------------------------------------------------


def notice_list(request):
    notices = Notice.objects.filter(is_published=True)
    category = request.GET.get("category", "")
    if category in Notice.Category.values:
        notices = notices.filter(category=category)
    return render(
        request,
        "calc/new/notices.html",
        {
            "notices": notices.order_by("-is_pinned", "-published_at", "-date"),
            "selected_category": category,
            "notice_categories": Notice.Category.choices,
        },
    )


def notice_detail(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id, is_published=True)
    return render(request, "calc/new/notice_detail.html", {"notice": notice})


@login_required
def suggestion_list(request):
    form = SuggestionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        suggestion = form.save(commit=False)
        profile = _profile_for(request.user)
        suggestion.user = request.user
        suggestion.source_path = request.path[:255]
        suggestion.region = (profile.region or "")[:30]
        suggestion.save()
        messages.success(request, "건의가 접수되었습니다.")
        return redirect("calc:suggestions")

    suggestions = Suggestion.objects.filter(user=request.user).order_by("-date")[:20]
    return render(
        request,
        "calc/new/suggestions.html",
        {"form": form, "suggestions": suggestions},
    )


@login_required
def suggestion_detail(request, suggestion_id):
    suggestion = get_object_or_404(Suggestion, id=suggestion_id, user=request.user)
    return render(
        request,
        "calc/new/suggestion_detail.html",
        {"suggestion": suggestion},
    )


@login_required
def suggestion_file(request, suggestion_id):
    suggestion = get_object_or_404(Suggestion, id=suggestion_id)
    if not request.user.is_staff and suggestion.user_id != request.user.id:
        raise Http404
    if not suggestion.file:
        raise Http404
    try:
        file_handle = suggestion.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404
    extension = os.path.splitext(suggestion.file.name)[1].lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    response = FileResponse(
        file_handle,
        content_type=content_types.get(extension, "application/octet-stream"),
    )
    filename = get_valid_filename(os.path.basename(suggestion.file.name)) or "attachment"
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Staff-only dashboard and administration screens
# ---------------------------------------------------------------------------


def staff_required(view_func):
    """Require authentication and reject authenticated non-staff users."""

    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


def _daily_trend(queryset, field_name, days=30):
    start = timezone.localdate() - timedelta(days=days - 1)
    date_key = f"{field_name}__date"
    rows = (
        queryset.filter(**{f"{field_name}__date__gte": start})
        .values(date_key)
        .annotate(count=Count("id"))
    )
    counts = {row[date_key]: row["count"] for row in rows}
    trend = []
    for offset in range(days):
        current = start + timedelta(days=offset)
        trend.append(
            {
                "date": current,
                "label": current.strftime("%m.%d"),
                "count": counts.get(current, 0),
            }
        )
    maximum = max((item["count"] for item in trend), default=0)
    for item in trend:
        item["percent"] = round(item["count"] / maximum * 100, 1) if maximum else 0
    return trend, maximum


def _dated_queryset_filter(request, queryset, field_name):
    start_value = request.GET.get("start_date", "")
    end_value = request.GET.get("end_date", "")
    try:
        start_date = date.fromisoformat(start_value) if start_value else None
    except ValueError:
        start_date = None
    try:
        end_date = date.fromisoformat(end_value) if end_value else None
    except ValueError:
        end_date = None
    if start_date:
        queryset = queryset.filter(**{f"{field_name}__date__gte": start_date})
    if end_date:
        queryset = queryset.filter(**{f"{field_name}__date__lte": end_date})
    return queryset


@staff_required
def staff_dashboard(request):
    now = timezone.now()
    general_users = User.objects.filter(is_staff=False)
    recent_cutoff = now - timedelta(days=7)
    recent_access_cutoff = now - timedelta(days=30)
    general_profiles = Profile.objects.filter(user__is_staff=False)
    score_records = ScoreRecord.objects.filter(user__is_staff=False)

    signup_trend, signup_max = _daily_trend(general_users, "date_joined", days=30)
    access_queryset = AccessLog.objects.filter(created_at__gte=recent_access_cutoff)
    access_trend, access_max = _daily_trend(access_queryset, "created_at", days=30)

    region_counts = {}
    for profile in general_profiles.values("primary_region", "area"):
        region_code = profile["primary_region"] or profile["area"]
        if region_code:
            region_counts[region_code] = region_counts.get(region_code, 0) + 1
    region_distribution = [
        {
            "code": code,
            "name": REGION_BY_CODE.get(code, {}).get("name", code),
            "count": count,
        }
        for code, count in sorted(
            region_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    region_max = max((item["count"] for item in region_distribution), default=0)
    for item in region_distribution:
        item["percent"] = round(item["count"] / region_max * 100, 1) if region_max else 0

    category_stats = []
    for category in ScoreRecord.Category:
        category_records = score_records.filter(category=category.value)
        record_count = category_records.count()
        evidence_count = category_records.filter(evidence_available=True).count()
        category_stats.append(
            {
                "code": category.value,
                "name": category.label,
                "record_count": record_count,
                "member_count": category_records.values("user_id").distinct().count(),
                "evidence_count": evidence_count,
                "evidence_percent": round(evidence_count / record_count * 100, 1)
                if record_count
                else 0,
                "needs_review_count": category_records.filter(
                    status=ScoreRecord.Status.NEEDS_REVIEW
                ).count(),
            }
        )

    qualifications = KoreanHistoryQualification.objects.filter(user__is_staff=False)
    qualification_counts = {
        "input": 0,
        "not_input": max(general_users.count() - qualifications.filter(~Q(method="")).count(), 0),
        "satisfied": 0,
        "not_satisfied": 0,
        "needs_review": 0,
    }
    for qualification in qualifications:
        if qualification.method:
            qualification_counts["input"] += 1
        status = qualification.qualification_status
        qualification_counts[status] += 1

    popular_pages = list(
        access_queryset.exclude(route_name="")
        .values("route_name")
        .annotate(count=Count("id"))
        .order_by("-count", "route_name")[:10]
    )
    auth_visits = access_queryset.filter(is_authenticated=True).count()
    guest_visits = access_queryset.filter(is_authenticated=False).count()
    total_visits = auth_visits + guest_visits
    visitor_ratio = {
        "authenticated": auth_visits,
        "guest": guest_visits,
        "authenticated_percent": round(auth_visits / total_visits * 100, 1)
        if total_visits
        else 0,
        "guest_percent": round(guest_visits / total_visits * 100, 1) if total_visits else 0,
    }

    conversion = {
        "total_members": general_users.count(),
        "primary_region": general_profiles.exclude(primary_region="").count(),
        "first_record": general_users.filter(score_records__isnull=False).distinct().count(),
        "five_records": general_users.annotate(
            record_count=Count("score_records")
        ).filter(record_count__gte=5).count(),
    }
    context = {
        "summary": {
            "member_count": conversion["total_members"],
            "scored_member_count": conversion["first_record"],
            "new_member_count": general_users.filter(date_joined__gte=recent_cutoff).count(),
            "active_score_member_count": score_records.filter(
                updated_at__gte=recent_cutoff
            ).values("user_id").distinct().count(),
            "record_count": score_records.count(),
            "pending_suggestion_count": Suggestion.objects.filter(
                status__in=[Suggestion.Status.RECEIVED, Suggestion.Status.REVIEWING]
            ).count(),
            "published_notice_count": Notice.objects.filter(is_published=True).count(),
        },
        "signup_trend": signup_trend,
        "signup_max": signup_max,
        "access_trend": access_trend,
        "access_max": access_max,
        "conversion": conversion,
        "region_distribution": region_distribution,
        "category_stats": category_stats,
        "qualification_counts": qualification_counts,
        "recent_suggestions": Suggestion.objects.select_related("user").order_by("-date")[:5],
        "recent_users": general_users.order_by("-date_joined")[:5],
        "recent_notices": Notice.objects.order_by("-date")[:5],
        "popular_pages": popular_pages,
        "visitor_ratio": visitor_ratio,
        "recent_error_count": access_queryset.filter(status_code__gte=400).count(),
    }
    return render(request, "calc/new/staff/dashboard.html", context)


@staff_required
def staff_suggestions(request):
    suggestions = Suggestion.objects.select_related("user").all()
    category = request.GET.get("category", "")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if category in Suggestion.Category.values:
        suggestions = suggestions.filter(category=category)
    if status in Suggestion.Status.values:
        suggestions = suggestions.filter(status=status)
    if query:
        suggestions = suggestions.filter(
            Q(title__icontains=query) | Q(user__username__icontains=query)
        )
    suggestions = _dated_queryset_filter(request, suggestions, "date").order_by("-date")[:100]
    return render(
        request,
        "calc/new/staff/suggestions.html",
        {
            "suggestions": suggestions,
            "selected_category": category,
            "selected_status": status,
            "query": query,
            "start_date": request.GET.get("start_date", ""),
            "end_date": request.GET.get("end_date", ""),
            "suggestion_categories": Suggestion.Category.choices,
            "suggestion_statuses": Suggestion.Status.choices,
        },
    )


@staff_required
def staff_suggestion_detail(request, suggestion_id):
    suggestion = get_object_or_404(
        Suggestion.objects.select_related("user"), id=suggestion_id
    )
    if request.method == "POST":
        status = request.POST.get("status", "")
        if status not in Suggestion.Status.values:
            messages.error(request, "유효하지 않은 처리 상태입니다.")
        else:
            suggestion.status = status
            suggestion.admin_memo = request.POST.get("admin_memo", "")[:20000]
            suggestion.resolved_at = timezone.now() if status == Suggestion.Status.COMPLETED else None
            suggestion.save(update_fields=["status", "admin_memo", "resolved_at", "updated_at"])
            messages.success(request, "건의 처리 상태를 저장했습니다.")
            return redirect("calc:staff_suggestion_detail", suggestion_id=suggestion.id)
    return render(
        request,
        "calc/new/staff/suggestion_detail.html",
        {"suggestion": suggestion, "suggestion_statuses": Suggestion.Status.choices},
    )


@staff_required
def staff_notices(request):
    notices = Notice.objects.all()
    category = request.GET.get("category", "")
    published = request.GET.get("published", "")
    if category in Notice.Category.values:
        notices = notices.filter(category=category)
    if published in {"published", "unpublished"}:
        notices = notices.filter(is_published=published == "published")
    return render(
        request,
        "calc/new/staff/notices.html",
        {
            "notices": notices.order_by("-is_pinned", "-date"),
            "selected_category": category,
            "selected_published": published,
            "notice_categories": Notice.Category.choices,
        },
    )


@staff_required
def staff_notice_create(request):
    form = NoticeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "공지를 작성했습니다.")
        return redirect("calc:staff_notices")
    return render(
        request,
        "calc/new/staff/notice_form.html",
        {"form": form, "is_edit": False},
    )


@staff_required
def staff_notice_edit(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    form = NoticeForm(request.POST or None, instance=notice)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "공지를 수정했습니다.")
        return redirect("calc:staff_notices")
    return render(
        request,
        "calc/new/staff/notice_form.html",
        {"form": form, "is_edit": True, "notice": notice},
    )


@staff_required
@require_POST
def staff_notice_toggle(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    action = request.POST.get("action", "")
    if action == "publish":
        notice.is_published = True
        notice.save()
        messages.success(request, "공지를 공개했습니다.")
    elif action == "unpublish":
        notice.is_published = False
        notice.save()
        messages.success(request, "공개를 중지했습니다.")
    elif action == "pin":
        notice.is_pinned = True
        notice.save(update_fields=["is_pinned", "updated_at"])
        messages.success(request, "공지를 상단에 고정했습니다.")
    elif action == "unpin":
        notice.is_pinned = False
        notice.save(update_fields=["is_pinned", "updated_at"])
        messages.success(request, "공지 고정을 해제했습니다.")
    else:
        messages.error(request, "유효하지 않은 공지 작업입니다.")
    return redirect("calc:staff_notices")


@staff_required
def staff_access_logs(request):
    logs = _dated_queryset_filter(request, AccessLog.objects.all(), "created_at")
    auth_filter = request.GET.get("auth", "")
    status_code = request.GET.get("status_code", "")
    if auth_filter == "authenticated":
        logs = logs.filter(is_authenticated=True)
    elif auth_filter == "guest":
        logs = logs.filter(is_authenticated=False)
    try:
        status_value = int(status_code) if status_code else None
    except ValueError:
        status_value = None
    if status_value is not None:
        logs = logs.filter(status_code=status_value)

    page_counts = list(
        logs.exclude(route_name="")
        .values("route_name")
        .annotate(count=Count("id"))
        .order_by("-count", "route_name")[:20]
    )
    date_key = "created_at__date"
    daily_counts = list(
        logs.values(date_key).annotate(count=Count("id")).order_by("-" + date_key)[:90]
    )
    recent_logs = logs.order_by("-created_at")[:100]
    return render(
        request,
        "calc/new/staff/access_logs.html",
        {
            "access_logs": recent_logs,
            "page_counts": page_counts,
            "daily_counts": daily_counts,
            "auth_filter": auth_filter,
            "status_code": status_code,
            "start_date": request.GET.get("start_date", ""),
            "end_date": request.GET.get("end_date", ""),
        },
    )
