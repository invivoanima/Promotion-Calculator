from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError


ROLE_PERMISSIONS = {
    "운영자": [
        "view_accesslog", "view_suggestion", "change_suggestion", "view_notice",
        "add_notice", "change_notice", "view_operation_logs", "view_user_action_logs",
    ],
    "콘텐츠 편집자": ["view_notice", "add_notice", "change_notice"],
}


class Command(BaseCommand):
    help = "관리자 기본 역할과 최소 권한을 생성하거나 동기화합니다. 최고관리자는 Django superuser로 관리합니다."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="실제로 역할을 생성·변경합니다.")

    def handle(self, *args, **options):
        missing = []
        resolved = {}
        for role, codenames in ROLE_PERMISSIONS.items():
            permissions = list(Permission.objects.filter(content_type__app_label="calc", codename__in=codenames))
            found = {permission.codename for permission in permissions}
            missing.extend(f"{role}:{name}" for name in codenames if name not in found)
            resolved[role] = permissions
        if missing:
            raise CommandError("권한을 찾을 수 없습니다: " + ", ".join(missing))
        if not options["apply"]:
            for role, permissions in resolved.items():
                self.stdout.write(f"[미리보기] {role}: {', '.join(sorted(p.codename for p in permissions))}")
            self.stdout.write("변경하려면 --apply를 사용하세요.")
            return
        for role, permissions in resolved.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"{role} 역할을 동기화했습니다."))
