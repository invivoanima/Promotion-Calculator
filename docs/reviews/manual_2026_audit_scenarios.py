"""Read-only manual comparison using synthetic, unsaved records.

Run with .venv/Scripts/python.exe docs/reviews/manual_2026_audit_scenarios.py.
Expected values refer to the printed pages of the bundled 2026 manual.
This script never reads or writes personal records.
"""

import itertools
import json
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promocalc.settings")

import django

django.setup()

from calc.scoring.regions.jeonnam.v2026.catalog import ITEM_BY_CODE
from calc.forms import ScoreRecordInputForm
from calc.models import ScoreRecord
from calc.services import (
    calculate_item_score_from_records,
    calculate_record_score,
    converted_training_score,
    score_summary_from_records,
)


# Select the audited region explicitly; the service no longer assumes Jeonnam.
from functools import partial
calculate_record_score = partial(calculate_record_score, region_code="jeonnam")
calculate_item_score_from_records = partial(calculate_item_score_from_records, region_code="jeonnam")
score_summary_from_records = partial(score_summary_from_records, region_code="jeonnam")
converted_training_score = partial(converted_training_score, region_code="jeonnam")

RESULTS = []
PRO = "jeonnam_professional_activity"


def record(code, variant="", value=None, start=None, end=None, event=None, year=None, **kwargs):
    data = {"variant": variant}
    if value is not None:
        data["value"] = str(value)
    if year is not None:
        data["year"] = str(year)
    item = ITEM_BY_CODE[code]
    entry = ScoreRecord(
        item_code=code, scope=item["scope"], category=item["category"],
        input_data=data,
        start_date=date.fromisoformat(start) if start else None,
        end_date=date.fromisoformat(end) if end else None,
        event_date=date.fromisoformat(event) if event else None,
        **kwargs,
    )
    entry.calculated_score = calculate_record_score(entry)
    return entry


def item_score(code, entries):
    return calculate_item_score_from_records(code, entries)


def check(case, pages, description, actual, expected):
    actual, expected = Decimal(str(actual)), Decimal(str(expected))
    RESULTS.append({
        "case": case, "manual_printed_pages": pages, "description": description,
        "actual": str(actual), "expected": str(expected), "matches": actual == expected,
    })


check("C01", "19", "기본 가경력 정확히 15년", item_score("career_history", [
    record("career_history", "base_ga", start="2011-03-01", end="2026-02-28"),
]), "64")
check("C02", "19", "초과 나경력 정확히 5년", item_score("career_history", [
    record("career_history", "excess_na", start="2006-03-01", end="2011-02-28"),
]), "5")
check("C03", "32", "같은 학년도 연구대회 1.5점과 0.75점", item_score("training_research", [
    record("training_research", "research_1_5", event="2025-06-01"),
    record("training_research", "research_0_75", event="2025-11-01"),
]), "1.5")
check("C04", "33-34", "2005년 1학기 이전 입학 특례에 해당하지 않는 서로 다른 석사 2개", item_score("training_research", [
    record("training_research", "score_1_5", event="2020-08-01"),
    record("training_research", "score_1", event="2023-08-01"),
]), "1.5")
shared = score_summary_from_records({
    "common_research_school": [record("common_research_school", start="2010-03-01", end="2015-02-28")],
    "jeonnam_designated_research": [record("jeonnam_designated_research", "superintendent", start="2015-03-01", end="2022-02-28")],
})
check("C05", "11,40", "기간이 겹치지 않는 교육부+교육감 연구학교 합산 상한", shared["total"], "1.25")
check("C06", "39", "2013년 3월 이전 농어촌 1년, 현재 3급지 선택", item_score("jeonnam_rural", [
    record("jeonnam_rural", "rural_3", start="2012-03-01", end="2013-02-28"),
]), "0.1428")
check("C07", "41", "2010년 청소년단체 담당 1년", item_score(PRO, [
    record(PRO, "youth", start="2010-01-01", end="2010-12-31"),
]), "0.126")
check("C08", "42", "학교교육력 증진 유공 6년", item_score(PRO, [record(PRO, "school_power", 6)]), "0.2")
check("C09", "42", "적격 보직교사 추가경력 90개월의 머목 상한", item_score(PRO, [
    record(PRO, "leadership_extra", start="2018-09-01", end="2026-02-28"),
]), "0.25")
check("C10", "43", "다른 분야 국가기술자격 0.3점+0.2점의 거목 합산 상한", item_score(PRO, [
    record(PRO, "certificate_1", event="2020-01-01"),
    record(PRO, "certificate_2", event="2021-01-01"),
]), "0.3")
check("C11", "12", "학급경영 우수교사 실적을 두 번 등록", item_score(PRO, [
    record(PRO, "class_award", event="2010-01-01"),
    record(PRO, "class_award", event="2011-01-01"),
]), "0.25")
check("C12", "41", "타목에서 서로 다른 연도 금상 2회+은상 1회", item_score(PRO, [
    record(PRO, "competition_gold", 1, event="2018-06-01"),
    record(PRO, "competition_gold", 1, event="2019-06-01"),
    record(PRO, "competition_silver", 1, event="2020-06-01"),
]), "0.5")
check("C13", "41", "같은 연도 전국대회 금상 2회", item_score(PRO, [
    record(PRO, "competition_gold", 1, event="2025-06-01"),
    record(PRO, "competition_gold", 1, event="2025-11-01"),
]), "0.25")
check("C14", "41-42", "서로 겹치지 않는 하목의 학교+학급+통합학급 경력", item_score(PRO, [
    record(PRO, "special_school", start="2000-01-01", end="2001-12-31"),
    record(PRO, "special_class", start="2002-01-01", end="2007-12-31"),
    record(PRO, "integrated_class", start="2008-01-01", end="2008-01-31"),
]), "0.5")
check("C15", "41", "별개 목인 다목 사이버 5년+라목 영재 5년, 비중복", item_score(PRO, [
    record(PRO, "regular", start="2009-01-01", end="2013-12-31", label="사이버가정학습"),
    record(PRO, "regular", start="2014-01-01", end="2018-12-31", label="영재교육원"),
]), "1")
check("C16", "41", "인정기간 종료 후 2025년 학급경영 우수교사", item_score(PRO, [
    record(PRO, "class_award", event="2025-06-01"),
]), "0")
check("C17", "45", "전남 거주 인정 시작 전인 2011년 전가족 거주", item_score("jeonnam_residence", [
    record("jeonnam_residence", "family", start="2011-01-01", end="2011-12-31"),
]), "0")
check("C18", "44", "일반 교사의 같은 학년도 좋은수업 3회, 간격 1개월 초과", item_score("jeonnam_good_lesson", [
    record("jeonnam_good_lesson", "regional", event=d)
    for d in ["2025-03-01", "2025-06-01", "2025-09-01"]
]), "0.16")
check("C19", "44", "1개월 이내 좋은수업 2회", item_score("jeonnam_good_lesson", [
    record("jeonnam_good_lesson", "regional", event=d)
    for d in ["2025-05-30", "2025-06-13"]
]), "0.08")
check("C20", "45", "좋은수업 1.5점 도달 전 추가실적만 2회", score_summary_from_records({
    PRO: [record(PRO, "good_lesson_extra", 2)]
})["total"], "0")
check("C21", "39", "농어촌 기본점 없이 추가경력만 1년", item_score("jeonnam_rural", [
    record("jeonnam_rural", "rural_add", start="2025-03-01", end="2026-02-28"),
]), "0")
check("C22", "39", "보직교사 기본점 없이 보완경력만 1년", item_score("jeonnam_leadership", [
    record("jeonnam_leadership", "leadership_supplement", start="2025-03-01", end="2026-02-28"),
]), "0")
check("C23", "38-39", "동일 기간 벽지 라급지와 농어촌 1급지 동시 등록", score_summary_from_records({
    "jeonnam_island_remote": [record("jeonnam_island_remote", "remote_ra", start="2024-03-01", end="2025-02-28")],
    "jeonnam_rural": [record("jeonnam_rural", "rural_1", start="2024-03-01", end="2025-02-28")],
})["total"], "0.504")
check("C24", "41", "2009년 이전 영재 전담 취득점의 종전점수 상한", item_score(PRO, [
    record(PRO, "regular", start="2006-01-01", end="2008-12-31", label="영재교육원"),
]), "0.25")

work = [record("work_performance", value=score, year=year) for year, score in [
    (2025, "99"), (2024, "100"), (2023, "100"), (2022, "98.99"), (2021, "0"),
]]
weights = [Decimal("0.34"), Decimal("0.33"), Decimal("0.33")]
best = max(sum((entry.calculated_score * weight for entry, weight in zip(
    sorted(combo, key=lambda r: int(r.input_data["year"]), reverse=True), weights
)), Decimal("0")) for combo in itertools.combinations(work, 3))
check("C25", "26", "유리한 3년: 단순 최고 3개와 최대 가중합의 차이", item_score("work_performance", work), best)

courses = [record("training_job", value=score, event=completed) for score, completed in [
    ("92", "2025-08-01"), ("88", "2024-08-01"), ("86", "2023-08-01"),
]]
for course in courses:
    course.input_data["extra_value"] = "60"
for count, expected in [(1, "5.7"), (2, "11.7"), (3, "17.7")]:
    check(f"C{25 + count:02d}", "8,28,36,68", f"서로 다른 적격 직무연수 {count}건: 성적 1건+별도 이수실적 최대 2건",
          item_score("training_job", courses[:count]), expected)
check("SCOPE-PROMOTION", "27,68,70", "교감 승진 대상자의 교감 자격연수 90점(현 앱은 1정·자격연수 대상 모드만 제공)",
      record("training_qualification", value="90").calculated_score, "8.5")
check("C29", "28", "자격연수 원점수 70점: 60점 이상 80점 미만의 80점 간주 미반영",
      record("training_qualification", value="70").calculated_score, "8.5")
check("C30", "28", "자격연수 원점수 50점: 60점 미만 비평정 미반영",
      record("training_qualification", value="50").calculated_score, "0")

# Positive controls: the audit distinguishes correct base rates from missing rules.
for variant, expected in [("95", "95"), ("95.01", "100"), ("90", "90"), ("85", "85")]:
    check("OK-JOB-" + variant, "28", "직무연수 환산 경계값 " + variant,
          converted_training_score(variant), expected)
check("OK-QUAL", "27", "교감 자격연수 대상 1정 성적 90점", calculate_record_score(
    record("training_qualification", value="90")
), "8.75")
check("OK-CREDIT", "35", "같은 연도 2학점 3건의 연도별 상한", item_score("common_training_credit", [
    record("common_training_credit", value="2", year="2025") for _ in range(3)
]), "0.08")

form = ScoreRecordInputForm(ITEM_BY_CODE[PRO], data={"variant": "school_power", "value": "-1"})
check("INPUT-NEGATIVE", "해당 없음", "서버 입력검증: 음수 횟수 허용 여부(1=허용)", int(form.is_valid()), "0")

destination = Path(__file__).with_suffix(".json")
destination.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
for result in RESULTS:
    print(f"{result['case']}: {'MATCH' if result['matches'] else 'DIFF'} "
          f"current={result['actual']} expected={result['expected']} {result['description']}")
print(f"{len(RESULTS)} scenarios, {sum(not r['matches'] for r in RESULTS)} differences; {destination}")
