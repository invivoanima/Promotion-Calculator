import ipaddress
import json
import logging
import os
from pathlib import Path
from uuid import UUID, uuid4

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("calc.audit")

ALLOWED_OUTCOMES = {"success", "failure", "denied", "noop"}
ALLOWED_METADATA = {
    "item_code", "changed_fields", "previous_status", "new_status", "count",
}


def log_directory():
    configured = getattr(settings, "USER_ACTION_LOG_DIR", "")
    return Path(configured) if configured else Path(settings.BASE_DIR) / ".runtime" / "user-actions"


def _clean_ip(value):
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def _request_context(request):
    match = getattr(request, "resolver_match", None)
    return {
        "request_id": str(getattr(request, "request_id", uuid4())),
        "client_ip": _clean_ip(getattr(request, "client_ip", None)),
        "ip_source": getattr(request, "ip_source", "unknown"),
        "cf_ray": getattr(request, "cf_ray", None),
        "route": ((match.view_name or match.url_name) if match else "")[:150],
    }


def audit_event(request, action, *, outcome="success", object_type=None,
                object_id=None, user_id=None, reason_code="", metadata=None):
    """Append one privacy-minimized schema-v1 event without changing business results."""
    if not getattr(settings, "USER_ACTION_LOG_ENABLED", True):
        return False
    if outcome not in ALLOWED_OUTCOMES:
        raise ValueError("invalid audit outcome")
    if user_id is None:
        user = getattr(request, "user", None)
        user_id = user.pk if getattr(user, "is_authenticated", False) else None
    safe_metadata = {}
    for key, value in (metadata or {}).items():
        if key in ALLOWED_METADATA and isinstance(value, (str, int, bool, list, type(None))):
            safe_metadata[key] = value
    context = _request_context(request)
    event = {
        "schema_version": 1,
        "event_id": str(uuid4()),
        "timestamp": timezone.now().isoformat().replace("+00:00", "Z"),
        "request_id": context["request_id"],
        "user_id": user_id,
        "action": str(action)[:80],
        "object_type": str(object_type)[:64] if object_type else None,
        "object_id": str(object_id)[:128] if object_id is not None else None,
        "outcome": outcome,
        "reason_code": str(reason_code)[:64],
        "client_ip": context["client_ip"],
        "ip_source": context["ip_source"] if context["client_ip"] else "unknown",
        "cf_ray": str(context["cf_ray"])[:80] if context["cf_ray"] else None,
        "route": context["route"],
        "metadata": safe_metadata,
    }
    try:
        UUID(event["request_id"])
        encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 8192:
            raise ValueError("audit event exceeds 8 KiB")
        directory = log_directory()
        directory.mkdir(parents=True, exist_ok=True)
        local_day = timezone.localtime().date().isoformat()
        path = directory / f"user-actions-{local_day}.jsonl"
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded + "\n")
            stream.flush()
        return True
    except Exception:
        logger.exception("user action audit write failed")
        return False
