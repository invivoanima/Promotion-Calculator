from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from calc.models import AccessLog


class Command(BaseCommand):
    help = "지정한 보존 기간보다 오래된 개인정보 최소화 접속 기록을 삭제합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="보존할 최근 일수 (기본값: 90)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            self.stderr.write(self.style.ERROR("--days는 1 이상이어야 합니다."))
            return
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = AccessLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"접속 기록 {deleted}건을 정리했습니다."))
