"""Synthetic regional rules verify routing, not the rules of any real region."""

import json
import sys
from copy import deepcopy
from decimal import Decimal
from types import ModuleType
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .forms import ScoreRecordInputForm
from .models import Profile, RegionPortfolio, ScoreRecord
from .scoring import registry
from .scoring.regions.jeonnam import v2026 as jeonnam
from .services import calculate_record_score, score_summary, score_summary_from_records


class RegistryTests(SimpleTestCase):
    def test_unknown_region_or_year_never_uses_jeonnam(self):
        for region, year in [("invalid", None), ("invalid", 2026), ("jeonnam", 2027)]:
            with self.subTest(region=region, year=year):
                self.assertFalse(registry.rules_available(region, year))
                with self.assertRaises(registry.RulesUnavailable):
                    registry.get_ruleset(region, year)

    def test_calculation_requires_a_region_even_for_a_common_item(self):
        record = ScoreRecord(item_code="common_training_credit", input_data={"value": "2"})
        with self.assertRaises(registry.RulesUnavailable):
            calculate_record_score(record)
        with self.assertRaises(TypeError):
            score_summary_from_records({})

    def test_all_jeonnam_categories_are_owned_by_regional_modules(self):
        self.assertEqual(set(jeonnam.CATEGORY_MODULES), {
            "career", "work", "training", "common_bonus", "regional_bonus",
        })
        for module in jeonnam.CATEGORY_MODULES.values():
            self.assertTrue(module.__name__.startswith("calc.scoring.regions.jeonnam.v2026."))
        for item in jeonnam.ITEMS:
            self.assertEqual((item["rule_region"], item["rule_year"]), ("jeonnam", 2026))


class RegionalRoutingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="regional-routing")
        self.profile = Profile.objects.create(user=self.user, primary_region="jeonnam", area="jeonnam")
        self.portfolio = RegionPortfolio.objects.create(user=self.user, region="jeonnam")
        # A deliberately different rate, category cap, input label and validation.
        self.fake = ModuleType("calc.scoring.synthetic_seoul")
        self.fake.REGION_CODE = "seoul"
        self.fake.RULE_YEAR = 2026
        self.fake.RULE_DATE = "2026. 2. 28."
        self.fake.ROSTER_DATE = "2026. 3. 31."
        item = deepcopy(jeonnam.ITEM_BY_CODE["common_training_credit"])
        item.update(rule_region="seoul", rule_year=2026, formula="테스트 전용 계산식")
        item["fields"]["value"]["label"] = "테스트 지역 전용 인정 학점"
        self.fake.ITEM_BY_CODE = {item["code"]: item}
        self.fake.ITEMS = [item]
        category = {
            "code": "common_bonus", "name": "테스트 지역 공통가산점",
            "description": "테스트 전용 기준", "max_score": Decimal("0.15"), "items": [item],
        }
        self.fake.CATEGORIES = [category]
        self.fake.CATEGORY_BY_CODE = {"common_bonus": category}
        self.fake.calculate_record_score = lambda r: Decimal(r.input_data["value"]) * Decimal("0.1")
        self.fake.calculate_item_score_from_records = lambda code, records: sum(
            (r.calculated_score for r in records), Decimal("0")
        )

        def finalize(summary, records):
            score = min(summary["items"][item["code"]], category["max_score"])
            return {**summary, "categories": {"common_bonus": score}, "total": score}

        def mark(records, code):
            for record in records:
                record.display_calculated_score = record.calculated_score
            return records

        self.fake.finalize_summary = finalize
        self.fake.mark_selected_records = mark
        self.fake.item_context = lambda code, score_for_item: {}
        self.fake.validate_input = lambda item, cleaned: (
            [("year", "테스트 지역에서는 2024년만 허용합니다.")]
            if cleaned.get("year") != 2024 else []
        )
        self.patches = [
            patch.dict(sys.modules, {self.fake.__name__: self.fake}),
            patch.dict(registry.ACTIVE_RULE_YEARS, {"seoul": 2026}),
            patch.dict(registry.RULE_MODULES, {("seoul", 2026): self.fake.__name__}),
        ]
        registry.get_ruleset.cache_clear()
        for patched in self.patches:
            patched.start()
        self.addCleanup(self.cleanup_registry)

    def cleanup_registry(self):
        for patched in reversed(self.patches):
            patched.stop()
        registry.get_ruleset.cache_clear()

    def test_common_bonus_dispatches_by_region_and_ignores_cached_score(self):
        record = ScoreRecord(item_code="common_training_credit", input_data={"value": "2", "year": "2024"})
        record.calculated_score = Decimal("999")
        self.assertEqual(calculate_record_score(record, region_code="jeonnam"), Decimal("0.04"))
        self.assertEqual(calculate_record_score(record, region_code="seoul"), Decimal("0.2"))
        summary = score_summary_from_records({record.item_code: [record]}, region_code="seoul")
        self.assertEqual(summary["total"], Decimal("0.15"))
        self.assertEqual(summary["region_code"], "seoul")
        self.assertEqual(record.calculated_score, Decimal("999"))

    def test_primary_region_chooses_catalog_validation_and_calculation(self):
        self.client.force_login(self.user)
        self.client.post(reverse("calc:region_select"), {"region": "seoul", "action": "set_primary"})
        url = reverse("calc:score_item", args=["common_training_credit"])
        self.assertContains(self.client.get(url), "테스트 지역 전용 인정 학점")
        response = self.client.post(url, {"label": "연수", "year": "2025", "value": "2"})
        self.assertContains(response, "테스트 지역에서는 2024년만 허용합니다.")
        self.assertFalse(ScoreRecord.objects.exists())
        self.assertRedirects(self.client.post(url, {"label": "연수", "year": "2024", "value": "2"}), url)
        record = ScoreRecord.objects.get(user=self.user)
        self.assertEqual(record.portfolio.region, "seoul")
        self.assertEqual(record.calculated_score, Decimal("0.2"))
        summary = score_summary(self.user, record.portfolio)
        self.assertEqual(summary["total"], Decimal("0.15"))

    def test_reference_region_uses_its_provider_without_changing_primary(self):
        self.client.force_login(self.user)
        self.client.post(reverse("calc:region_select"), {"region": "seoul", "action": "view"})
        response = self.client.get(reverse("calc:score_index_category", args=["common_bonus"]))
        self.assertContains(response, "테스트 지역 공통가산점")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.region, "jeonnam")
        self.assertEqual(response.context["summary"]["region_code"], "seoul")

    def test_guest_uses_regional_rules_and_separate_storage_key(self):
        self.client.post(reverse("calc:region_select"), {"region": "seoul", "action": "view"})
        url = reverse("calc:guest_score_item", args=["common_training_credit"])
        response = self.client.get(url)
        self.assertContains(response, 'data-guest-local-key="promotionCalculator.guestRecords.v1.seoul.2026"')
        self.assertContains(response, 'data-guest-legacy-key=""')
        response = self.client.post(url, {
            "action": "record_form", "guest_payload": "{}", "label": "연수", "year": "2024", "value": "2",
        })
        storage = response.json()["storage"]
        self.assertEqual(Decimal(storage["common_training_credit"][0]["calculated_score"]), Decimal("0.2"))
        response = self.client.post(reverse("calc:guest_score_index"), {
            "action": "hydrate", "guest_payload": json.dumps(storage),
        })
        self.assertEqual(response.context["summary"]["total"], Decimal("0.15"))
        self.assertFalse(ScoreRecord.objects.exists())

    def test_legacy_guest_state_is_only_imported_for_jeonnam(self):
        response = self.client.get(reverse("calc:guest_score_index"))
        self.assertContains(response, 'data-guest-local-key="promotionCalculator.guestRecords.v1.jeonnam.2026"')
        self.assertContains(response, 'data-guest-legacy-key="promotionCalculator.guestRecords.v1"')

    def test_other_region_portfolios_are_rejected(self):
        record = ScoreRecord(
            user=self.user, portfolio=self.portfolio, item_code="common_training_credit",
            input_data={"value": "2", "year": "2024"},
        )
        with self.assertRaises(ValueError):
            calculate_record_score(record, region_code="seoul")
        with self.assertRaises(ValueError):
            score_summary_from_records({record.item_code: [record]}, region_code="seoul")

    @patch.dict(registry.RULE_MODULES, {("jeonnam", 2026): "calc.scoring.regions.jeonnam.v2026"}, clear=True)
    def test_unavailable_region_blocks_common_and_career_inputs(self):
        registry.get_ruleset.cache_clear()
        self.client.force_login(self.user)
        self.client.post(reverse("calc:region_select"), {"region": "busan", "action": "set_primary"})
        for code in ["career_history", "common_training_credit", "jeonnam_good_lesson"]:
            with self.subTest(code=code):
                url = reverse("calc:score_item", args=[code])
                self.assertNotContains(self.client.get(url), "data-record-form")
                response = self.client.post(url, {"label": "연수", "year": "2024", "value": "2"})
                self.assertEqual(response.status_code, 403)
        self.assertFalse(ScoreRecord.objects.exists())

    @patch.dict(registry.RULE_MODULES, {("jeonnam", 2026): "calc.scoring.regions.jeonnam.v2026"}, clear=True)
    def test_unavailable_guest_region_never_hydrates_with_jeonnam(self):
        registry.get_ruleset.cache_clear()
        self.client.post(reverse("calc:region_select"), {"region": "busan", "action": "view"})
        response = self.client.post(reverse("calc:guest_score_index"), {
            "action": "hydrate", "guest_payload": json.dumps({"common_training_credit": [{
                "key": "existing", "input_data": {"year": "2024", "value": "2"},
            }]}),
        })
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "부산광역시 점수 계산 기준 준비 중", status_code=403)
        self.assertNotContains(response, "data-guest-calculator", status_code=403)

    def test_form_validation_is_taken_from_the_catalogs_region(self):
        item = self.fake.ITEM_BY_CODE["common_training_credit"]
        form = ScoreRecordInputForm(item, data={"label": "연수", "year": "2025", "value": "2"})
        self.assertFalse(form.is_valid())
        self.assertIn("2024년만", str(form.errors))
