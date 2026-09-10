import calendar
import json
from datetime import datetime, timezone as datetime_timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from calc.audit.writer import log_directory


def subtract_months(value, months):
    absolute = value.year * 12 + value.month - 1 - months
    year, month_index = divmod(absolute, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class Command(BaseCommand):
    help = "달력 기준 보존기간이 지난 이용자 행동 JSONL을 미리보거나 파기합니다."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="미리보기에 표시된 파기를 실행합니다.")

    def handle(self, *args, **options):
        months = settings.USER_ACTION_LOG_RETENTION_MONTHS
        if months < 1:
            raise CommandError("USER_ACTION_LOG_RETENTION_MONTHS는 1 이상이어야 합니다.")
        directory = log_directory().resolve()
        if not directory.exists():
            self.stdout.write("로그 디렉터리가 없어 처리할 항목이 없습니다.")
            return
        cutoff = subtract_months(timezone.localtime(), months).astimezone(datetime_timezone.utc)
        removed_files = removed_rows = kept_rows = 0
        for path in sorted(directory.glob("user-actions-????-??-??.jsonl")):
            resolved = path.resolve()
            if resolved.parent != directory:
                raise CommandError("로그 디렉터리 밖의 경로는 처리하지 않습니다.")
            try:
                file_day = datetime.strptime(path.stem.removeprefix("user-actions-"), "%Y-%m-%d").date()
            except ValueError:
                continue
            cutoff_day = timezone.localtime(cutoff).date()
            if file_day < cutoff_day:
                removed_files += 1
                if options["apply"]:
                    path.unlink()
                continue
            if file_day != cutoff_day:
                continue
            kept = []
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        stamp = datetime.fromisoformat(json.loads(line)["timestamp"].replace("Z", "+00:00"))
                    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                        kept.append(line)
                        kept_rows += 1
                        continue
                    if stamp < cutoff:
                        removed_rows += 1
                    else:
                        kept.append(line)
                        kept_rows += 1
            if options["apply"] and removed_rows:
                temporary = path.with_suffix(".jsonl.tmp")
                temporary.write_text("".join(kept), encoding="utf-8")
                temporary.replace(path)
        mode = "실행" if options["apply"] else "미리보기"
        self.stdout.write(f"[{mode}] 기준 {cutoff.isoformat()} / 전체 파일 {removed_files}개 / 경계 행 {removed_rows}개 파기, {kept_rows}개 유지")
