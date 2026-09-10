import json
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import LegalConsent, Profile, Suggestion


class GovernanceTests(TestCase):
    def setUp(self):
        self.test_root = Path(settings.BASE_DIR) / ".runtime" / "governance-tests"
        shutil.rmtree(self.test_root, ignore_errors=True)
        (self.test_root / "media").mkdir(parents=True, exist_ok=True)
        (self.test_root / "audit").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_registration_requires_and_records_current_legal_versions(self):
        self.assertContains(self.client.get(reverse("calc:terms")), "개발용 초안")
        self.assertContains(self.client.get(reverse("calc:privacy")), "개발용 초안")
        data = {
            "username": "legal_user", "display_name": "법률테스트",
            "password1": "Strong-pass-2026", "password2": "Strong-pass-2026",
        }
        response = self.client.post(reverse("calc:register"), data)
        self.assertEqual(response.status_code, 200)
        data.update(agree_terms="on", agree_privacy="on")
        response = self.client.post(reverse("calc:register"), data)
        self.assertRedirects(response, reverse("calc:region_select"))
        consent = LegalConsent.objects.get(user__username="legal_user")
        self.assertEqual(consent.terms_version, "2026-09-10")
        self.assertEqual(consent.privacy_version, "2026-09-10")

    def test_legal_links_use_sidebar_for_members_and_footer_for_guests(self):
        guest_response = self.client.get(reverse("calc:welcome"))
        self.assertContains(guest_response, 'class="site-footer"')
        self.assertNotContains(guest_response, 'class="sidebar-legal-links"')

        user = User.objects.create_user("links@example.com", password="Strong-pass-2026")
        Profile.objects.create(user=user, primary_region="jeonnam", area="jeonnam")
        self.client.force_login(user)
        member_response = self.client.get(reverse("calc:dashboard"))
        self.assertContains(member_response, 'class="sidebar-legal-links"')
        self.assertNotContains(member_response, 'class="site-footer"')

    def test_suggestion_attachment_is_deleted_with_record(self):
        user = User.objects.create_user("file@example.com")
        with override_settings(MEDIA_ROOT=self.test_root / "media"):
                item = Suggestion.objects.create(
                    user=user, title="첨부", content="내용",
                    file=SimpleUploadedFile("proof.pdf", b"%PDF-test"),
                )
                path = Path(item.file.path)
                self.assertTrue(path.exists())
                item.delete()
                self.assertFalse(path.exists())

    def test_user_action_log_permission_masking_and_no_store(self):
        directory = self.test_root / "audit"
        with override_settings(USER_ACTION_LOG_ENABLED=True, USER_ACTION_LOG_DIR=directory):
                user = User.objects.create_user("member@example.com", password="Strong-pass-2026")
                Profile.objects.create(user=user)
                self.client.post(reverse("calc:login"), {
                    "username": "member@example.com", "password": "Strong-pass-2026",
                }, REMOTE_ADDR="192.0.2.2")
                files = list(directory.glob("user-actions-*.jsonl"))
                self.assertEqual(len(files), 1)
                event = json.loads(files[0].read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual(event["action"], "auth.login")
                self.assertIsNone(event["client_ip"])
                self.assertNotIn("member@example.com", files[0].read_text(encoding="utf-8"))

                viewer = User.objects.create_user("auditor", password="Strong-pass-2026", is_staff=True)
                viewer.user_permissions.add(Permission.objects.get(codename="view_user_action_logs"))
                self.client.force_login(viewer)
                response = self.client.get(reverse("calc:manage_user_actions"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertNotContains(response, "member@example.com")

    def test_staff_flag_without_feature_permission_is_denied(self):
        staff = User.objects.create_user("staff-only", password="Strong-pass-2026", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("calc:staff_notices")).status_code, 403)
