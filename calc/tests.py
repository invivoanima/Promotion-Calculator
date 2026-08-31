import json
from datetime import date
from decimal import Decimal

from django.core import mail
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse

from django.conf import settings

from .catalog import CATEGORIES, ITEMS, ITEM_BY_CODE
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
    calculate_record_score,
    common_training_credit_contributions,
    period_months_days,
    score_summary,
    selected_training_job_records,
    selected_work_performance_records,
)


class CalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher@example.com", password="Strong-pass-2026")
        self.profile = Profile.objects.create(
            user=self.user,
            display_name="초등교사",
            primary_region="jeonnam",
            area="jeonnam",
        )
        self.portfolio = RegionPortfolio.objects.create(user=self.user, region="jeonnam")

    def create_record(self, item_code, *, portfolio=None, **kwargs):
        item = ITEM_BY_CODE[item_code]
        record = ScoreRecord(
            user=self.user,
            portfolio=portfolio,
            scope=item["scope"],
            category=item["category"],
            item_code=item_code,
            **kwargs,
        )
        record.calculated_score = calculate_record_score(record)
        record.full_clean()
        record.save()
        return record

    def test_period_calculation_is_inclusive(self):
        self.assertEqual(period_months_days(date(2026, 1, 1), date(2026, 1, 31)), (1, 0))

    def test_career_separates_base_and_excess_caps(self):
        self.create_record(
            "career_history",
            start_date=date(2000, 1, 1),
            end_date=date(2020, 12, 31),
            input_data={"variant": "base_ga"},
        )
        self.create_record(
            "career_history",
            start_date=date(1990, 1, 1),
            end_date=date(2000, 12, 31),
            input_data={"variant": "excess_ga"},
        )
        self.assertEqual(calculate_item_score(self.user, "career_history", self.portfolio), Decimal("70.000000"))

    def test_work_performance_selects_best_three_of_five_recent_years(self):
        for year, score in [
            (2025, 80),
            (2024, 99),
            (2023, 70),
            (2022, 98),
            (2021, 97),
            (2020, 100),
        ]:
            self.create_record(
                "work_performance",
                input_data={"year": str(year), "value": str(score)},
            )
        records = list(ScoreRecord.objects.filter(item_code="work_performance"))
        self.assertEqual(
            [int(record.input_data["year"]) for record in selected_work_performance_records(records)],
            [2024, 2022, 2021],
        )
        self.assertEqual(
            calculate_item_score(self.user, "work_performance", self.portfolio),
            Decimal("98.010000"),
        )

    def test_qualification_training_uses_single_best_record(self):
        self.create_record("training_qualification", input_data={"value": "90"})
        self.create_record("training_qualification", input_data={"value": "80"})
        self.assertEqual(
            calculate_item_score(self.user, "training_qualification", self.portfolio),
            Decimal("8.750000"),
        )

    def test_job_training_uses_highest_score_and_two_recognized_courses(self):
        highest = self.create_record(
            "training_job",
            event_date=date(2025, 8, 1),
            input_data={"value": "92", "extra_value": "60"},
        )
        second = self.create_record(
            "training_job",
            event_date=date(2024, 8, 1),
            input_data={"value": "88", "extra_value": "60"},
        )
        self.create_record(
            "training_job",
            event_date=date(2025, 9, 1),
            input_data={"value": "99", "extra_value": "30"},
        )
        self.create_record(
            "training_job",
            event_date=date(2015, 12, 31),
            input_data={"value": "100", "extra_value": "60"},
        )
        records = list(ScoreRecord.objects.filter(item_code="training_job"))
        self.assertEqual(highest.calculated_score, Decimal("5.700000"))
        self.assertEqual(second.calculated_score, Decimal("5.400000"))
        self.assertEqual(selected_training_job_records(records), [highest, second])
        self.assertEqual(
            calculate_item_score(self.user, "training_job", self.portfolio),
            Decimal("17.700000"),
        )

    def test_research_scores_cover_all_pdf_table_values(self):
        national = self.create_record(
            "training_research",
            input_data={"variant": "research_0_875"},
        )
        provincial = self.create_record(
            "training_research",
            input_data={"variant": "research_0_525"},
        )
        self.assertEqual(national.calculated_score, Decimal("0.875000"))
        self.assertEqual(provincial.calculated_score, Decimal("0.525000"))

    def test_common_training_credit_selects_records_within_annual_cap(self):
        for label in ["연수 A", "연수 B", "연수 C"]:
            self.create_record(
                "common_training_credit",
                portfolio=self.portfolio,
                label=label,
                input_data={"year": "2025", "value": "2"},
            )
        records = list(
            ScoreRecord.objects.filter(item_code="common_training_credit")
        )
        contributions = common_training_credit_contributions(records)
        self.assertEqual(
            [score for _, score in contributions if score > 0],
            [Decimal("0.040000"), Decimal("0.040000")],
        )
        self.assertEqual(
            calculate_item_score(
                self.user,
                "common_training_credit",
                self.portfolio,
            ),
            Decimal("0.080000"),
        )

    def test_regional_record_requires_matching_portfolio(self):
        record = self.create_record(
            "jeonnam_residence",
            portfolio=self.portfolio,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            input_data={"variant": "family"},
        )
        self.assertEqual(record.calculated_score, Decimal("0.002500"))

    def test_korean_history_status(self):
        qualification = KoreanHistoryQualification.objects.create(
            user=self.user,
            method=KoreanHistoryQualification.Method.TEST,
            test_grade=3,
        )
        self.assertEqual(qualification.qualification_status, "satisfied")
        qualification.method = KoreanHistoryQualification.Method.TRAINING
        qualification.training_hours = 60
        qualification.completed_after_appointment = True
        qualification.employment_type = KoreanHistoryQualification.EmploymentType.TEMPORARY
        self.assertEqual(qualification.qualification_status, "not_satisfied")


class FlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="flow@example.com", email="flow@example.com", password="Strong-pass-2026")
        self.profile = Profile.objects.create(
            user=self.user,
            display_name="흐름 테스트",
            primary_region="jeonnam",
            area="jeonnam",
        )
        self.portfolio = RegionPortfolio.objects.create(user=self.user, region="jeonnam")
        self.client.force_login(self.user)

    def test_registration_then_region_selection(self):
        self.client.logout()
        response = self.client.post(
            reverse("calc:register"),
            {
                "email": "new@example.com",
                "display_name": "새 사용자",
                "password1": "Strong-pass-2026",
                "password2": "Strong-pass-2026",
            },
        )
        self.assertRedirects(response, reverse("calc:region_select"))
        user = User.objects.get(username="new@example.com")
        self.assertEqual(user.profile.primary_region, "")

        response = self.client.post(
            reverse("calc:region_select"),
            {"region": "jeonnam", "action": "set_primary"},
        )
        self.assertRedirects(response, reverse("calc:dashboard"))
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.primary_region, "jeonnam")
        self.assertTrue(RegionPortfolio.objects.filter(user=user, region="jeonnam").exists())

    def test_unimplemented_region_can_be_primary_with_regional_bonus_disabled(self):
        response = self.client.post(
            reverse("calc:region_select"),
            {"region": "seoul", "action": "set_primary"},
        )
        self.assertRedirects(response, reverse("calc:dashboard"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.primary_region, "seoul")
        self.assertTrue(RegionPortfolio.objects.filter(user=self.user, region="seoul").exists())

        response = self.client.get(reverse("calc:dashboard"))
        self.assertContains(response, "서울특별시 선택가산점")
        self.assertContains(response, "입력·편집 비활성화")
        self.assertNotContains(
            response,
            f'href="{reverse("calc:score_index_category", args=["regional_bonus"])}"',
        )

        response = self.client.get(
            reverse("calc:score_item", args=["jeonnam_good_lesson"])
        )
        self.assertContains(response, "서울특별시 선택가산점 기준은 아직 준비 중입니다.")
        self.assertNotContains(response, "data-record-form")
        response = self.client.post(
            reverse("calc:score_item", args=["jeonnam_good_lesson"]),
            {"action": "record_form", "year": "2025", "value": "1"},
        )
        self.assertRedirects(
            response,
            reverse("calc:score_item", args=["jeonnam_good_lesson"]),
        )
        self.assertFalse(
            ScoreRecord.objects.filter(
                user=self.user,
                item_code="jeonnam_good_lesson",
            ).exists()
        )

        response = self.client.get(reverse("calc:score_item", args=["career_history"]))
        self.assertContains(response, "data-record-form")
        self.assertEqual(self.client.get(reverse("calc:resources")).status_code, 200)

    def test_public_main_actions_point_to_registration_and_calculator(self):
        self.client.logout()
        response = self.client.get(reverse("calc:welcome"))
        self.assertContains(response, "내 기록 시작하기")
        self.assertContains(response, "점수 계산해보기")
        self.assertNotContains(response, "지역별 기준 둘러보기")
        self.assertContains(response, f'href="{reverse("calc:guest_score_index")}"')

        response = self.client.get(reverse("calc:guest_score_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "이 브라우저에만 저장되는 계산입니다.")
        self.assertContains(response, "현재 점수 / 총점")
        self.assertContains(response, 'class="score-index-total"')

    def test_dashboard_and_score_pages_render(self):
        self.assertEqual(self.client.get(reverse("calc:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("calc:score_index")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("calc:score_item", args=["career_history"])).status_code,
            200,
        )

    def test_research_form_shows_pdf_score_tables_below_variant(self):
        response = self.client.get(
            reverse("calc:score_item", args=["training_research"])
        )
        self.assertContains(response, "연구대회 입상실적 평정표")
        self.assertContains(response, "전국 규모 연구대회")
        self.assertContains(response, "시·도 규모 연구대회")
        self.assertContains(response, "0.875")
        self.assertContains(response, "0.525")
        self.assertContains(response, "학위취득실적")

    def test_island_remote_form_shows_pdf_score_table_below_variant(self):
        response = self.client.get(
            reverse("calc:score_item", args=["jeonnam_island_remote"])
        )
        self.assertContains(response, "도서·벽지학교 급지별 평정표")
        self.assertContains(response, "도서학교")
        self.assertContains(response, "벽지학교")
        self.assertContains(response, "0.167")
        self.assertContains(response, "0.0014")
        self.assertContains(
            response,
            'class="island-remote-score-guide full-span"',
        )
        self.assertContains(response, 'item-sidebar item-sidebar-regional_bonus')

    def test_rural_form_shows_pdf_rate_table_below_variant(self):
        response = self.client.get(
            reverse("calc:score_item", args=["jeonnam_rural"])
        )
        self.assertContains(response, "농어촌교육진흥학교 급지별 평정표")
        self.assertContains(response, "1995.1.1. ~ 2013.2.28.")
        self.assertContains(response, "2013.3.1. ~ 2026.2.28.")
        self.assertContains(response, "0.0119")
        self.assertContains(response, "0.00027")
        self.assertContains(response, "추가경력점 0.15점")
        self.assertContains(response, 'class="rural-score-guide full-span"')

    def test_leadership_form_shows_pdf_rate_table_below_variant(self):
        response = self.client.get(
            reverse("calc:score_item", args=["jeonnam_leadership"])
        )
        self.assertContains(response, "보직교사 등 근무경력 평정표")
        self.assertContains(response, "유치원교사")
        self.assertContains(response, "초등교사 등")
        self.assertContains(response, "0.0143")
        self.assertContains(response, "0.00048")
        self.assertContains(response, "0.003")
        self.assertContains(response, "총 상한점 1.25점")
        self.assertContains(response, 'class="leadership-score-guide full-span"')

    def test_professional_activity_page_shows_pdf_table_above_form(self):
        response = self.client.get(
            reverse("calc:score_item", args=["jeonnam_professional_activity"])
        )
        self.assertContains(response, "기타 교육활동 및 전문성 신장 평정표")
        self.assertContains(response, "평정항목")
        self.assertContains(response, "실적 인정기간")
        self.assertContains(response, "평정점")
        self.assertContains(response, "상한점")
        self.assertContains(response, "월 0.0315점")
        self.assertContains(response, "은상 0.1875점")
        self.assertContains(response, "연 0.036점")
        self.assertContains(response, "전체 상한 1.0점")
        content = response.content.decode()
        self.assertLess(
            content.index('class="professional-activity-score-card"'),
            content.index('class="form-card" id="record-form"'),
        )

    def test_job_training_form_marks_highest_record_and_rejects_short_course(self):
        item_url = reverse("calc:score_item", args=["training_job"])
        for label, completed, score in [
            ("높은 연수", "2025-08-01", "92"),
            ("다음 연수", "2024-08-01", "88"),
        ]:
            response = self.client.post(
                item_url,
                {
                    "label": label,
                    "institution": "테스트연수원",
                    "event_date": completed,
                    "value": score,
                    "extra_value": "60",
                    "memo": "",
                },
            )
            self.assertRedirects(response, item_url)

        response = self.client.get(item_url)
        self.assertContains(response, "최고 성적 반영", count=1)
        self.assertContains(response, "이수실적 반영 · 6점", count=2)
        self.assertContains(response, "5.7000")
        self.assertContains(response, "최근 10년 2개월 이내")

        response = self.client.post(
            item_url,
            {
                "label": "시간 부족 연수",
                "institution": "테스트연수원",
                "event_date": "2025-09-01",
                "value": "99",
                "extra_value": "30",
                "memo": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "60시간 이상 직무연수만 인정됩니다.")
        self.assertFalse(
            ScoreRecord.objects.filter(label="시간 부족 연수").exists()
        )

    def test_common_training_credit_form_marks_records_within_cap(self):
        item_url = reverse("calc:score_item", args=["common_training_credit"])
        response = self.client.get(item_url)
        self.assertContains(response, "15시간당 1학점으로 계산합니다.")

        for label in ["연수 A", "연수 B", "연수 C"]:
            response = self.client.post(
                item_url,
                {
                    "label": label,
                    "institution": "테스트연수원",
                    "year": "2025",
                    "value": "2",
                    "memo": "",
                },
            )
            self.assertRedirects(response, item_url)

        response = self.client.get(item_url)
        self.assertContains(response, "점수 반영 · 0.0400점", count=2)
        self.assertContains(response, 'class="record-card score-selected"', count=2)
        self.assertContains(response, "연도별 0.08점과 전체 0.8점 상한")

    def test_every_category_and_score_item_renders(self):
        for category in CATEGORIES:
            with self.subTest(category=category["code"]):
                response = self.client.get(
                    reverse("calc:score_index_category", args=[category["code"]])
                )
                self.assertEqual(response.status_code, 200)
        for item in ITEMS:
            with self.subTest(item=item["code"]):
                response = self.client.get(
                    reverse("calc:score_item", args=[item["code"]])
                )
                self.assertEqual(response.status_code, 200)

    def test_all_primary_navigation_pages_render(self):
        route_names = [
            "calc:dashboard",
            "calc:score_index",
            "calc:korean_history",
            "calc:records",
            "calc:score_changes",
            "calc:resources",
            "calc:region_select",
            "calc:account_settings",
            "calc:password_reset",
        ]
        for route_name in route_names:
            with self.subTest(route=route_name):
                self.assertEqual(self.client.get(reverse(route_name)).status_code, 200)

    def test_official_manual_file_is_packaged(self):
        manual_path = settings.BASE_DIR / "calc" / "static" / "calc" / "manuals" / "jeonnam-2026.pdf"
        self.assertTrue(manual_path.is_file())
        self.assertGreater(manual_path.stat().st_size, 0)

    def test_password_reset_sends_email_for_existing_account(self):
        self.client.logout()
        response = self.client.post(
            reverse("calc:password_reset"),
            {"email": self.user.email},
        )
        self.assertRedirects(response, reverse("calc:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset/", mail.outbox[0].body)

    def test_account_deletion_requires_confirmation_phrase(self):
        response = self.client.post(
            reverse("calc:delete_account"),
            {"confirmation": "삭제"},
        )
        self.assertRedirects(response, reverse("calc:account_settings"))
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

        response = self.client.post(
            reverse("calc:delete_account"),
            {"confirmation": "계정 삭제"},
        )
        self.assertRedirects(response, reverse("calc:welcome"))
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_score_post_uses_server_calculation(self):
        response = self.client.post(
            reverse("calc:score_item", args=["jeonnam_good_lesson"]),
            {
                "label": "공개수업",
                "institution": "테스트초",
                "event_date": "2026-05-01",
                "variant": "regional",
                "value": "1",
                "memo": "",
                "evidence_available": "on",
                "hidden_total": "999999",
            },
        )
        self.assertRedirects(response, reverse("calc:score_item", args=["jeonnam_good_lesson"]))
        record = ScoreRecord.objects.get(user=self.user, item_code="jeonnam_good_lesson")
        self.assertEqual(record.calculated_score, Decimal("0.080000"))
        self.assertEqual(score_summary(self.user, self.portfolio)["total"], Decimal("0.080000"))

    def test_national_and_regional_records_are_scoped(self):
        career = ITEM_BY_CODE["career_history"]
        ScoreRecord.objects.create(
            user=self.user,
            scope=career["scope"],
            category=career["category"],
            item_code=career["code"],
            input_data={"variant": "base_ga"},
        )
        other_user = User.objects.create_user(username="other@example.com", password="Strong-pass-2026")
        Profile.objects.create(user=other_user, primary_region="jeonnam", area="jeonnam")
        other_portfolio = RegionPortfolio.objects.create(user=other_user, region="jeonnam")
        self.assertEqual(score_summary(other_user, other_portfolio)["total"], Decimal("0.000000"))

    def test_not_applicable_status_is_visible_and_can_be_cleared(self):
        item_url = reverse("calc:score_item", args=["jeonnam_good_lesson"])
        response = self.client.post(
            item_url,
            {"action": "toggle_not_applicable", "status": "not_applicable"},
        )
        self.assertRedirects(response, item_url)
        self.assertTrue(
            ItemStatus.objects.filter(
                user=self.user,
                portfolio=self.portfolio,
                item_code="jeonnam_good_lesson",
                status="not_applicable",
            ).exists()
        )
        category_response = self.client.get(
            reverse("calc:score_index_category", args=["regional_bonus"])
        )
        self.assertContains(category_response, "해당 없음")

        response = self.client.post(item_url, {"action": "clear_item_status"})
        self.assertRedirects(response, item_url)
        self.assertFalse(
            ItemStatus.objects.filter(
                user=self.user,
                portfolio=self.portfolio,
                item_code="jeonnam_good_lesson",
            ).exists()
        )


class GuestCalculatorTests(TestCase):
    def guest_lesson_data(self, variant="regional"):
        return {
            "label": "비로그인 공개수업",
            "institution": "테스트초",
            "event_date": "2026-05-01",
            "variant": variant,
            "memo": "임시 계산",
        }

    def test_every_guest_category_and_item_renders_without_login(self):
        self.assertEqual(
            self.client.get(reverse("calc:guest_score_index")).status_code,
            200,
        )
        for category in CATEGORIES:
            with self.subTest(category=category["code"]):
                response = self.client.get(
                    reverse("calc:guest_score_category", args=[category["code"]])
                )
                self.assertEqual(response.status_code, 200)
        for item in ITEMS:
            with self.subTest(item=item["code"]):
                response = self.client.get(
                    reverse("calc:guest_score_item", args=[item["code"]])
                )
                self.assertEqual(response.status_code, 200)

    def test_guest_can_select_unimplemented_region_with_regional_bonus_disabled(self):
        response = self.client.post(
            reverse("calc:region_select"),
            {"region": "seoul", "action": "view"},
        )
        self.assertRedirects(response, reverse("calc:guest_score_index"))
        response = self.client.get(reverse("calc:guest_score_index"))
        self.assertContains(response, "서울특별시 선택가산점")
        self.assertContains(response, "입력·편집 비활성화")

        response = self.client.get(
            reverse("calc:guest_score_item", args=["jeonnam_good_lesson"])
        )
        self.assertContains(response, "서울특별시 선택가산점 기준은 아직 준비 중입니다.")
        self.assertNotContains(response, "data-record-form")

        response = self.client.get(
            reverse("calc:guest_score_item", args=["career_history"])
        )
        self.assertContains(response, "data-record-form")

    def test_guest_calculation_returns_local_storage_payload_without_server_records(self):
        item_url = reverse(
            "calc:guest_score_item",
            args=["jeonnam_good_lesson"],
        )
        response = self.client.post(
            item_url,
            {
                **self.guest_lesson_data(),
                "action": "record_form",
                "guest_payload": json.dumps({}),
            },
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["redirect_url"], item_url)
        self.assertEqual(ScoreRecord.objects.count(), 0)
        self.assertEqual(ScoreChange.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)

        storage = result["storage"]
        self.assertEqual(len(storage["jeonnam_good_lesson"]), 1)
        response = self.client.post(
            item_url,
            {"action": "hydrate", "guest_payload": json.dumps(storage)},
        )
        self.assertContains(response, "0.0800")
        self.assertContains(response, "서버의 계정 기록과 점수 변화표에는 저장되지 않습니다.")
        response = self.client.post(
            reverse("calc:guest_score_index"),
            {"action": "hydrate", "guest_payload": json.dumps(storage)},
        )
        self.assertContains(response, "0.080")
        self.assertEqual(Session.objects.count(), 0)

    def test_guest_entry_can_be_edited_deleted_and_reset(self):
        item_url = reverse(
            "calc:guest_score_item",
            args=["jeonnam_good_lesson"],
        )
        response = self.client.post(
            item_url,
            {
                **self.guest_lesson_data(),
                "action": "record_form",
                "guest_payload": json.dumps({}),
            },
        )
        storage = response.json()["storage"]
        record_key = storage["jeonnam_good_lesson"][0]["key"]

        edit_url = reverse(
            "calc:guest_edit_score_record",
            args=["jeonnam_good_lesson", record_key],
        )
        response = self.client.post(
            edit_url,
            {
                **self.guest_lesson_data("school"),
                "action": "record_form",
                "guest_payload": json.dumps(storage),
            },
        )
        storage = response.json()["storage"]
        response = self.client.post(
            item_url,
            {"action": "hydrate", "guest_payload": json.dumps(storage)},
        )
        self.assertContains(response, "0.0600")

        delete_url = reverse(
            "calc:guest_delete_score_record",
            args=["jeonnam_good_lesson", record_key],
        )
        response = self.client.post(
            delete_url,
            {"guest_payload": json.dumps(storage)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["storage"]["jeonnam_good_lesson"], [])

        response = self.client.post(reverse("calc:guest_score_reset"))
        self.assertRedirects(response, reverse("calc:guest_score_index"))
        response = self.client.get(reverse("calc:guest_score_index"))
        self.assertContains(response, "data-guest-reset")
        self.assertContains(response, "promotionCalculator.guestRecords.v1")
        self.assertEqual(ScoreRecord.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
