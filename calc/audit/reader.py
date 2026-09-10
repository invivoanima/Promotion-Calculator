import json
from datetime import timedelta

from django.utils import timezone

from .writer import log_directory


def read_events(start, end, limit=5000):
    events, damaged = [], 0
    directory = log_directory()
    if not directory.exists():
        return events, damaged
    day = timezone.localtime(start).date()
    final_day = timezone.localtime(end).date()
    while day <= final_day and len(events) < limit:
        path = directory / f"user-actions-{day.isoformat()}.jsonl"
        if path.is_file():
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        item = json.loads(line)
                        stamp = timezone.datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                        if start <= stamp <= end:
                            events.append(item)
                    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                        damaged += 1
        day += timedelta(days=1)
    events.sort(key=lambda item: (item.get("timestamp", ""), item.get("event_id", "")), reverse=True)
    return events[:limit], damaged
