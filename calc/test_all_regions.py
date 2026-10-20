"""Functional coverage and boundary cases for all independently owned providers.

These verify the declared statutory baseline, not a claim that each local manual
has been verified. That distinction must remain visible in the product.
"""
import ast
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .forms import ScoreRecordInputForm
from .models import Profile, RegionPortfolio, ScoreRecord
from .regions import REGIONS
from .scoring.registry import get_ruleset, REGION_CODES
from .services import calculate_item_score_from_records, calculate_record_score, score_summary, score_summary_from_records


OTHER_REGIONS = [code for code in REGION_CODES if code != "jeonnam"]
EXAMPLES = {
    "career_history": {"institution": "예시학교", "start_date": "2025-03-01", "end_date": "2026-02-28", "variant": "base_ga"},
    "work_performance": {"year": "2025", "value": "90"},
    "training_qualification": {"label": "교감 자격연수", "value": "90"},
    "training_job": {"label": "예시연수", "event_date": "2025-06-01", "value": "92", "extra_value": "60"},
    "training_research": {"label": "석사학위", "event_date": "2025-06-01", "variant": "score_1_5"},
    "common_research_school": {"institution": "연구학교", "start_date": "2025-03-01", "end_date": "2025-03-31"},
    "common_foreign_institution": {"institution": "재외기관", "start_date": "2025-03-01", "end_date": "2025-03-31"},
    "common_training_credit": {"label": "학점연수", "year": "2025", "value": "6"},
    "common_school_violence": {"institution": "예시학교", "year": "2025"},
}
EXPECTED = {
    "career_history": "4.266", "work_performance": "30.6", "training_qualification": "8.5",
    "training_job": "5.7", "training_research": "1.5", "common_research_school": "0.018",
    "common_foreign_institution": "0.015", "common_training_credit": "0.12", "common_school_violence": "0.1",
}


def record_for(region, code, **overrides):
    form = ScoreRecordInputForm(get_ruleset(region).ITEM_BY_CODE[code], data={**EXAMPLES[code], **overrides})
    assert form.is_valid(), form.errors
    record = form.apply_to_record(ScoreRecord(item_code=code))
    return record


class AllRegionCalculationTests(SimpleTestCase):
    def test_all_17_registered_and_non_optional_catalogs_are_independent(self):
        self.assertEqual(len(REGIONS), 17)
        for region in OTHER_REGIONS:
            with self.subTest(region=region):
                rules = get_ruleset(region)
                self.assertEqual(set(rules.ITEM_BY_CODE), set(EXAMPLES))
                self.assertFalse(rules.REGIONAL_BONUS_AVAILABLE)
                self.assertEqual(rules.CATEGORY_BY_CODE["regional_bonus"]["items"], [])
                self.assertEqual(rules.CATEGORY_BY_CODE["regional_bonus"]["max_score"], 0)
                for item in rules.ITEMS:
                    self.assertEqual(item["rule_region"], region)
                for module in rules.CATEGORY_MODULES.values():
                    self.assertTrue(module.__name__.startswith(f"calc.scoring.regions.{region}.v2026."))
                # No aliases, subclasses or imports of a different region's policy.
                for file in Path(rules.__file__).parent.glob("*.py"):
                    tree = ast.parse(file.read_text(encoding="utf-8"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom) and node.module:
                            self.assertNotIn("scoring.regions.", node.module)
                self.assertIn("교육청 원문 대조 전", rules.RULE_NOTICE)

    def test_every_input_calculates_and_total_excludes_optional_bonus(self):
        for region in OTHER_REGIONS:
            with self.subTest(region=region):
                records = {code: [record_for(region, code)] for code in EXAMPLES}
                summary = score_summary_from_records(records, region_code=region)
                for code, expected in EXPECTED.items():
                    self.assertEqual(summary["items"][code], Decimal(expected), (region, code))
                self.assertEqual(summary["total"], Decimal("50.819"))
                self.assertEqual(summary["categories"]["regional_bonus"], 0)
                self.assertEqual(summary["excluded_categories"], ["regional_bonus"])

    def test_changing_one_region_does_not_change_any_other_region(self):
        for category, code in [("career", "career_history"), ("work", "work_performance"),
                               ("training", "training_qualification"), ("common_bonus", "common_training_credit")]:
            seoul = get_ruleset("seoul")
            with patch.object(seoul.CATEGORY_MODULES[category], "calculate_record_score", return_value=Decimal("99")):
                self.assertEqual(calculate_record_score(record_for("seoul", code), region_code="seoul"), 99)
                for region in [r for r in REGION_CODES if r != "seoul"]:
                    record = record_for(region, code)
                    self.assertNotEqual(calculate_record_score(record, region_code=region), 99)
        self.assertIsNot(get_ruleset("seoul").ITEM_BY_CODE, get_ruleset("busan").ITEM_BY_CODE)

    def test_one_two_three_training_courses_are_not_double_counted(self):
        for region in OTHER_REGIONS:
            courses = [record_for(region, "training_job", label=f"연수 {index}", value=value)
                       for index, value in enumerate(["92", "88", "86", "84"])]
            for count, expected in [(1, "5.7"), (2, "11.7"), (3, "17.7"), (4, "17.7")]:
                with self.subTest(region=region, count=count):
                    self.assertEqual(calculate_item_score_from_records("training_job", courses[:count], region_code=region), Decimal(expected))

    def test_research_best_per_school_year_and_only_one_degree(self):
        for region in OTHER_REGIONS:
            records = [
                record_for(region, "training_research", event_date="2024-04-01", variant="research_1_5"),
                record_for(region, "training_research", event_date="2025-02-28", variant="research_0_75"),
                record_for(region, "training_research", event_date="2025-03-01", variant="research_0_75"),
            ]
            self.assertEqual(calculate_item_score_from_records("training_research", records, region_code=region), Decimal("2.25"))
            degrees = [record_for(region, "training_research", variant="score_1_5"),
                       record_for(region, "training_research", variant="score_1")]
            self.assertEqual(calculate_item_score_from_records("training_research", degrees, region_code=region), Decimal("1.5"))

    def test_weighted_result_can_prefer_fourth_highest_raw_score(self):
        for region in OTHER_REGIONS:
            records = [record_for(region, "work_performance", year=year, value=value)
                       for year, value in [(2025, "99.5"), (2024, "100"), (2023, "99.51"), (2022, "99.49")]]
            # Skipping the newest year lets the 100-point year receive 34%.
            score = calculate_item_score_from_records("work_performance", records, region_code=region)
            self.assertEqual(score, Decimal("99.67"))

    def test_complete_career_periods_receive_full_scores(self):
        for region in OTHER_REGIONS:
            basic = record_for(region, "career_history", start_date="2011-03-01", end_date="2026-02-28", variant="base_ga")
            excess = record_for(region, "career_history", start_date="2006-03-01", end_date="2011-02-28", variant="excess_na")
            self.assertEqual(calculate_item_score_from_records("career_history", [basic], region_code=region), Decimal("64"))
            self.assertEqual(calculate_item_score_from_records("career_history", [basic, excess], region_code=region), Decimal("69"))

    def test_work_total_is_rounded_to_three_decimal_places(self):
        for region in OTHER_REGIONS:
            records = [record_for(region, "work_performance", year=year, value=value)
                       for year, value in [(2025, "99.5"), (2024, "100"), (2023, "99.51")]]
            self.assertEqual(calculate_item_score_from_records("work_performance", records, region_code=region), Decimal("99.668"))

    def test_common_credit_annual_overall_caps_and_duplicate_violence_year(self):
        for region in OTHER_REGIONS:
            credits = [record_for(region, "common_training_credit", year=year, value="100") for year in range(2010, 2026)]
            self.assertEqual(calculate_item_score_from_records("common_training_credit", credits[:2], region_code=region), Decimal("0.24"))
            self.assertEqual(calculate_item_score_from_records("common_training_credit", credits, region_code=region), Decimal("1"))
            violence = [record_for(region, "common_school_violence") for _ in range(2)]
            self.assertEqual(calculate_item_score_from_records("common_school_violence", violence, region_code=region), Decimal("0.1"))

    def test_qualification_floor_and_low_score_exclusion(self):
        for region in OTHER_REGIONS:
            for raw, expected in [("59", "0"), ("60", "8"), ("79", "8"), ("80", "8"), ("100", "9")]:
                record = record_for(region, "training_qualification", value=raw)
                self.assertEqual(calculate_record_score(record, region_code=region), Decimal(expected))

    def test_region_input_constraints_are_enforced_on_server(self):
        for region in OTHER_REGIONS:
            for code, overrides in [
                ("work_performance", {"year": "2026"}), ("work_performance", {"value": "101"}),
                ("common_training_credit", {"value": "-1"}), ("common_training_credit", {"year": "2026"}),
                ("training_job", {"extra_value": "59"}), ("training_job", {"event_date": "2016-02-29"}),
                ("training_job", {"event_date": "2026-03-01"}), ("training_research", {"event_date": ""}),
            ]:
                with self.subTest(region=region, code=code, overrides=overrides):
                    form = ScoreRecordInputForm(get_ruleset(region).ITEM_BY_CODE[code], data={**EXAMPLES[code], **overrides})
                    self.assertFalse(form.is_valid())


class AllRegionInputTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="all-regions")
        Profile.objects.create(user=self.user, primary_region="jeonnam", area="jeonnam")

    def test_qualification_inputs_for_different_assessment_targets_are_separate(self):
        ScoreRecord.objects.create(user=self.user, item_code="training_qualification", category="training",
                                   scope="national", label="1급 정교사", input_data={"value": "90"})
        jeonnam_portfolio = RegionPortfolio.objects.create(user=self.user, region="jeonnam")
        seoul_portfolio = RegionPortfolio.objects.create(user=self.user, region="seoul")
        self.assertEqual(score_summary(self.user, jeonnam_portfolio)["items"]["training_qualification"], Decimal("8.75"))
        self.assertEqual(score_summary(self.user, seoul_portfolio)["items"]["training_qualification"], 0)
        ScoreRecord.objects.create(user=self.user, portfolio=seoul_portfolio, item_code="training_qualification",
                                   category="training", scope="regional", label="교감", input_data={"value": "90"})
        self.assertEqual(score_summary(self.user, seoul_portfolio)["items"]["training_qualification"], Decimal("8.5"))
        self.assertEqual(score_summary(self.user, jeonnam_portfolio)["items"]["training_qualification"], Decimal("8.75"))

    def test_member_can_open_save_edit_delete_each_non_optional_item_in_all_regions(self):
        self.client.force_login(self.user)
        for region in OTHER_REGIONS:
            self.client.post(reverse("calc:region_select"), {"region": region, "action": "set_primary"})
            self.assertContains(self.client.get(reverse("calc:dashboard")), "교육청 원문 대조 전 기본 계산")
            for code, data in EXAMPLES.items():
                with self.subTest(region=region, code=code):
                    url = reverse("calc:score_item", args=[code])
                    self.assertContains(self.client.get(url), "data-record-form")
                    self.assertRedirects(self.client.post(url, data), url, fetch_redirect_response=False)
                    record = ScoreRecord.objects.get(user=self.user, item_code=code)
                    if record.scope == "regional":
                        self.assertEqual(record.portfolio.region, region)
                    else:
                        self.assertIsNone(record.portfolio)
                    edit = reverse("calc:edit_score_record", args=[code, record.id])
                    self.assertRedirects(self.client.post(edit, {**data, "memo": "수정 확인"}), url, fetch_redirect_response=False)
                    record.refresh_from_db()
                    self.assertEqual(record.memo, "수정 확인")
                    self.assertEqual(self.client.post(reverse("calc:delete_score_record", args=[record.id])).status_code, 302)
            optional = reverse("calc:score_index_category", args=["regional_bonus"])
            self.assertContains(self.client.get(optional), "선택가산점 준비 중")
            self.assertEqual(self.client.post(reverse("calc:score_item", args=["jeonnam_good_lesson"]), {}).status_code, 404)
            resources = self.client.get(reverse("calc:resources"))
            self.assertContains(resources, "교육공무원 승진규정")
            self.assertNotContains(resources, 'href="/static/"')
        self.assertFalse(ScoreRecord.objects.exists())

    def test_guest_can_save_hydrate_edit_delete_all_nine_items_in_all_regions(self):
        for region in OTHER_REGIONS:
            self.client.post(reverse("calc:region_select"), {"region": region, "action": "view"})
            storage = {}
            for code, data in EXAMPLES.items():
                with self.subTest(region=region, code=code):
                    url = reverse("calc:guest_score_item", args=[code])
                    self.assertContains(self.client.get(url), f"promotionCalculator.guestRecords.v1.{region}.2026")
                    response = self.client.post(url, {**data, "action": "record_form", "guest_payload": json.dumps(storage)})
                    self.assertEqual(response.status_code, 200)
                    storage = response.json()["storage"]
                    self.assertEqual(len(storage[code]), 1)
            url = reverse("calc:guest_score_index")
            response = self.client.post(url, {"action": "hydrate", "guest_payload": json.dumps(storage)})
            self.assertEqual(response.context["summary"]["total"], Decimal("50.819"))
            code = "common_training_credit"
            key = storage[code][0]["key"]
            response = self.client.post(reverse("calc:guest_edit_score_record", args=[code, key]), {
                **EXAMPLES[code], "value": "2", "action": "record_form", "guest_payload": json.dumps(storage),
            })
            storage = response.json()["storage"]
            self.assertEqual(storage[code][0]["input_data"]["value"], "2")
            response = self.client.post(reverse("calc:guest_delete_score_record", args=[code, key]), {"guest_payload": json.dumps(storage)})
            self.assertFalse(response.json()["storage"].get(code))
            self.assertEqual(self.client.get(reverse("calc:guest_score_item", args=["jeonnam_good_lesson"])).status_code, 404)
        self.assertFalse(ScoreRecord.objects.exists())

    def test_guest_hydration_revalidates_raw_values_and_drops_other_region_items(self):
        self.client.post(reverse("calc:region_select"), {"region": "seoul", "action": "view"})
        response = self.client.post(reverse("calc:guest_score_index"), {
            "action": "hydrate", "guest_payload": json.dumps({
                "common_training_credit": [{"label": "연수", "input_data": {"year": "2025", "value": "-10"}, "calculated_score": "999"}],
                "jeonnam_good_lesson": [{"input_data": {"variant": "research_1"}, "calculated_score": "999"}],
            }),
        })
        self.assertEqual(response.context["summary"]["total"], 0)
        self.assertNotIn("jeonnam_good_lesson", response.context["summary"]["items"])
