import importlib
import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.urls import reverse

from .scoring.regions.jeonnam.v2026.catalog import ITEM_BY_CODE
from .models import Profile, RegionPortfolio, ScoreRecord
from .services import calculate_record_score, score_summary


ITEM_CODE = "jeonnam_professional_activity"


class ProfessionalActivityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="professional-activity")
        Profile.objects.create(user=self.user, primary_region="jeonnam", area="jeonnam")
        self.portfolio = RegionPortfolio.objects.create(user=self.user, region="jeonnam")

    def record(self, variant, value="", **kwargs):
        return ScoreRecord(
            user=self.user,
            portfolio=self.portfolio,
            scope="regional",
            category="regional_bonus",
            item_code=ITEM_CODE,
            input_data={"variant": variant, "value": value},
            **kwargs,
        )

    def test_every_available_variant_uses_its_calculation(self):
        # One calendar month plus one day for period records; two units otherwise.
        expected = {
            "regular": "0.010850",
            "student_teacher": "0.032550",
            "youth": "0.005477",
            "hospital": "0.008680",
            "special_school": "0.008680",
            "special_class": "0.004340",
            "integrated_class": "0.002170",
            "leadership_extra": "0.003100",
            "class_award": "0.250000",
            "it_certificate": "0.250000",
            "competition_gold": "0.500000",
            "competition_silver": "0.375000",
            "competition_bronze": "0.250000",
            "certificate_1": "0.300000",
            "certificate_2": "0.200000",
            "certificate_3": "0.100000",
            "school_power": "0.072000",
            "good_lesson_extra": "0.040000",
        }
        choices = ITEM_BY_CODE[ITEM_CODE]["fields"]["variant"]["choices"]
        self.assertEqual(set(expected), {code for code, _ in choices})
        for variant, score in expected.items():
            with self.subTest(variant=variant):
                record = self.record(
                    variant, "2", start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)
                )
                self.assertEqual(calculate_record_score(record), Decimal(score))
                migration = importlib.import_module(
                    "calc.migrations.0011_recalculate_professional_activity_scores"
                )
                self.assertEqual(migration.record_score(record), Decimal(score))

    def test_existing_item_and_total_caps_are_preserved(self):
        for variant in ("regular", "student_teacher", "school_power"):
            record = self.record(
                variant, "100", start_date=date(2020, 1, 1), end_date=date(2025, 12, 31)
            )
            record.calculated_score = calculate_record_score(record)
            record.save()
            summary = score_summary(self.user, self.portfolio)
            expected = Decimal("0.5") if variant == "regular" else Decimal("1")
            self.assertEqual(summary["items"][ITEM_CODE], expected)
            self.assertEqual(summary["categories"]["regional_bonus"], expected)
            self.assertEqual(summary["total"], expected)

    def test_saved_record_create_and_edit_update_display_and_totals(self):
        self.client.force_login(self.user)
        url = reverse("calc:score_item", args=[ITEM_CODE])
        response = self.client.post(url, {
            "variant": "student_teacher", "start_date": "2025-01-01",
            "end_date": "2025-01-31",
        })
        self.assertRedirects(response, url)
        record = ScoreRecord.objects.get(user=self.user, item_code=ITEM_CODE)
        self.assertEqual(record.calculated_score, Decimal("0.031500"))
        response = self.client.get(url)
        self.assertEqual(response.context["item_score"], Decimal("0.031500"))
        self.assertContains(response, "0.0315")

        response = self.client.post(
            reverse("calc:edit_score_record", args=[ITEM_CODE, record.pk]),
            {"variant": "school_power", "value": "3"},
        )
        self.assertRedirects(response, url)
        record.refresh_from_db()
        self.assertEqual(record.calculated_score, Decimal("0.108000"))
        self.assertEqual(score_summary(self.user, self.portfolio)["total"], Decimal("0.108000"))

    def test_guest_saved_payload_is_recalculated_on_hydration(self):
        url = reverse("calc:guest_score_item", args=[ITEM_CODE])
        response = self.client.post(url, {
            "action": "record_form", "guest_payload": "{}",
            "variant": "good_lesson_extra", "value": "3",
        })
        self.assertEqual(response.status_code, 200)
        storage = response.json()["storage"]
        self.assertEqual(Decimal(storage[ITEM_CODE][0]["calculated_score"]), Decimal("0.06"))
        storage[ITEM_CODE][0]["calculated_score"] = "0"
        storage[ITEM_CODE].append({
            "key": "old-period-record", "start_date": "2025-01-01",
            "end_date": "2025-01-31", "input_data": {"variant": "student_teacher"},
            "calculated_score": "0",
        })
        response = self.client.post(url, {
            "action": "hydrate", "guest_payload": json.dumps(storage),
        })
        self.assertEqual(response.context["item_score"], Decimal("0.091500"))
        response = self.client.post(reverse("calc:guest_score_index"), {
            "action": "hydrate", "guest_payload": json.dumps(storage),
        })
        self.assertEqual(response.context["summary"]["total"], Decimal("0.091500"))
        self.assertFalse(ScoreRecord.objects.exists())

    def test_data_migration_repairs_existing_scores_without_changing_inputs(self):
        migration = importlib.import_module(
            "calc.migrations.0011_recalculate_professional_activity_scores"
        )
        historical_apps = MigrationExecutor(connection).loader.project_state([
            ("calc", "0010_auditpermission_operationlog_legalconsent")
        ]).apps
        cases = [
            ("student_teacher", "", "0", "0.031500"),
            ("school_power", "3", "0", "0.108000"),
            ("good_lesson_extra", "2", "0", "0.040000"),
            ("competition_silver", "2", "0.1875", "0.375000"),
            ("class_award", "2", "0.25", "0.250000"),
        ]
        records = []
        for variant, value, old_score, expected in cases:
            record = self.record(
                variant, value, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
                memo="보존할 메모", evidence_available=True,
                calculated_score=Decimal(old_score),
            )
            record.save()
            records.append((record, expected))
        unrelated = self.record("regional", "1", calculated_score=Decimal("0.08"))
        unrelated.item_code = "jeonnam_good_lesson"
        unrelated.save()

        for _ in range(2):
            migration.recalculate_scores(historical_apps, SimpleNamespace(connection=connection))
            for record, expected in records:
                original_data, original_updated_at = record.input_data.copy(), record.updated_at
                record.refresh_from_db()
                self.assertEqual(record.calculated_score, Decimal(expected))
                self.assertEqual(record.input_data, original_data)
                self.assertEqual(record.updated_at, original_updated_at)
                self.assertEqual(record.memo, "보존할 메모")
                self.assertTrue(record.evidence_available)
            unrelated.refresh_from_db()
            self.assertEqual(unrelated.calculated_score, Decimal("0.08"))
