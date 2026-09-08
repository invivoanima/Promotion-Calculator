import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import AccessLog, Notice, Profile, ScoreRecord, Suggestion


@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), "promotion-calculator-tests"))
class StaffAndPublicFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher@example.com",
            password="Strong-pass-2026",
        )
        Profile.objects.create(
            user=self.user,
            primary_region="jeonnam",
            area="jeonnam",
        )
        self.staff = User.objects.create_user(
            username="staff@example.com",
            password="Strong-pass-2026",
            is_staff=True,
        )
        Profile.objects.create(user=self.staff, primary_region="jeonnam", area="jeonnam")

    def test_staff_permission_and_sidebar_link(self):
        self.assertEqual(self.client.get(reverse("calc:staff_dashboard")).status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(reverse("calc:staff_dashboard"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("calc:dashboard"))
        self.assertNotContains(response, "관리자 대시보드")
        self.assertContains(response, "관리자에게 건의하기")

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("calc:staff_dashboard")).status_code, 200)
        response = self.client.get(reverse("calc:dashboard"))
        self.assertContains(response, "관리자 대시보드")

    def test_suggestion_submission_validation_ownership_and_staff_resolution(self):
        self.client.force_login(self.user)
        invalid_file = SimpleUploadedFile("report.svg", b"<svg></svg>", content_type="image/svg+xml")
        response = self.client.post(
            reverse("calc:suggestions"),
            {
                "category": "error",
                "title": "파일 오류",
                "content": "확인해주세요.",
                "file": invalid_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Suggestion.objects.count(), 0)

        suggestion = Suggestion.objects.create(
            user=self.user,
            category="error",
            title="화면 오류",
            content="내용",
            source_path="/suggestions/",
            region="jeonnam",
        )
        other = User.objects.create_user(username="other@example.com", password="Strong-pass-2026")
        self.client.force_login(other)
        self.assertEqual(
            self.client.get(reverse("calc:suggestion_detail", args=[suggestion.id])).status_code,
            404,
        )

        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("calc:staff_suggestion_detail", args=[suggestion.id]),
            {"status": "completed", "admin_memo": "처리했습니다."},
        )
        self.assertRedirects(response, reverse("calc:staff_suggestion_detail", args=[suggestion.id]))
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, Suggestion.Status.COMPLETED)
        self.assertIsNotNone(suggestion.resolved_at)
        self.client.post(
            reverse("calc:staff_suggestion_detail", args=[suggestion.id]),
            {"status": "reviewing", "admin_memo": "추가 확인 중"},
        )
        suggestion.refresh_from_db()
        self.assertIsNone(suggestion.resolved_at)

    def test_valid_attachment_signature_and_100mb_limit(self):
        self.client.force_login(self.user)
        png = SimpleUploadedFile(
            "evidence.PNG",
            b"\x89PNG\r\n\x1a\n" + b"0" * 20,
            content_type="application/octet-stream",
        )
        response = self.client.post(
            reverse("calc:suggestions"),
            {"category": "data", "title": "자료", "content": "수정", "file": png},
        )
        self.assertRedirects(response, reverse("calc:suggestions"))
        suggestion = Suggestion.objects.get()
        self.assertEqual(suggestion.source_path, "/suggestions/")
        self.assertEqual(suggestion.region, "jeonnam")

        oversized = SimpleUploadedFile(
            "large.pdf",
            b"%PDF-" + b"0" * (100 * 1024 * 1024),
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("calc:suggestions"),
            {"category": "other", "title": "큰 파일", "content": "내용", "file": oversized},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Suggestion.objects.count(), 1)

    def test_public_notice_visibility_pinning_and_staff_editing(self):
        Notice.objects.create(title="일반 공개", content="공개 내용", is_published=True)
        unpublished = Notice.objects.create(title="비공개", content="숨김", is_published=False)
        Notice.objects.create(title="고정 공지", content="먼저", is_published=True, is_pinned=True)
        response = self.client.get(reverse("calc:notices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "고정 공지")
        self.assertContains(response, "일반 공개")
        self.assertNotContains(response, "비공개")
        self.assertLess(response.content.find("고정 공지".encode()), response.content.find("일반 공개".encode()))
        self.assertEqual(
            self.client.get(reverse("calc:notice_detail", args=[unpublished.id])).status_code,
            404,
        )

        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse("calc:staff_notice_create")).status_code,
            403,
        )
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("calc:staff_notice_create"),
            {
                "category": "update",
                "title": "새 업데이트",
                "content": "줄바꿈\n내용",
                "is_published": "on",
                "is_pinned": "on",
            },
        )
        self.assertRedirects(response, reverse("calc:staff_notices"))
        notice = Notice.objects.get(title="새 업데이트")
        self.assertIsNotNone(notice.published_at)

    def test_staff_dashboard_counts_and_empty_sections_render(self):
        ScoreRecord.objects.create(
            user=self.user,
            scope=ScoreRecord.Scope.NATIONAL,
            category=ScoreRecord.Category.CAREER,
            item_code="career_history",
            input_data={"private_note": "개인 원문"},
        )
        Notice.objects.create(title="대시보드 공지", content="내용")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("calc:staff_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["member_count"], 1)
        self.assertEqual(response.context["summary"]["scored_member_count"], 1)
        self.assertEqual(response.context["summary"]["record_count"], 1)
        self.assertNotContains(response, "private_note")

    def test_access_log_middleware_records_only_html_pages(self):
        AccessLog.objects.all().delete()
        response = self.client.get(reverse("calc:notices"), HTTP_USER_AGENT="Mozilla/5.0 (iPhone)")
        self.assertEqual(response.status_code, 200)
        log = AccessLog.objects.get(route_name="calc:notices")
        self.assertFalse(log.is_authenticated)
        self.assertEqual(log.device_type, AccessLog.DeviceType.MOBILE)
        self.assertEqual(log.region, "")

        before = AccessLog.objects.count()
        self.client.get("/static/calc/app.css")
        self.client.get("/admin/login/")
        self.client.get(reverse("calc:staff_dashboard"))
        self.assertEqual(AccessLog.objects.count(), before)

        self.client.force_login(self.user)
        self.client.get(reverse("calc:notices"))
        log = AccessLog.objects.filter(route_name="calc:notices", is_authenticated=True).latest("created_at")
        self.assertEqual(log.region, "jeonnam")
        self.assertNotIn("user_agent", {field.name for field in AccessLog._meta.fields})
        self.assertNotIn("ip", {field.name for field in AccessLog._meta.fields})
