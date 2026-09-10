from uuid import uuid4

from django.conf import settings


class RequestAuditContextMiddleware:
    """Create a server-owned correlation id and conservative network context."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid4()
        request.client_ip = None
        request.ip_source = "unknown"
        request.cf_ray = None
        if getattr(settings, "TRUST_DIRECT_CLIENT_IP", False):
            request.client_ip = request.META.get("REMOTE_ADDR")
            request.ip_source = "direct"
        response = self.get_response(request)
        response["X-Request-ID"] = str(request.request_id)
        return response


class AccessLogMiddleware:
    """Record privacy-minimized page views after a response is rendered."""

    excluded_prefixes = ("/static/", "/media/", "/admin/", "/staff/")
    excluded_paths = (
        "/static",
        "/media",
        "/admin",
        "/staff",
        "/health",
        "/health/",
        "/healthz",
        "/healthz/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._record(request, response)
        return response

    @classmethod
    def _is_excluded_path(cls, path):
        return path.startswith(cls.excluded_prefixes) or path in cls.excluded_paths

    @staticmethod
    def _device_type(user_agent):
        value = (user_agent or "").lower()
        if "ipad" in value or "tablet" in value or ("android" in value and "mobile" not in value):
            return "tablet"
        if any(token in value for token in ("mobile", "iphone", "ipod", "android")):
            return "mobile"
        if value:
            return "desktop"
        return "other"

    @staticmethod
    def _region_for(user):
        if not user or not user.is_authenticated:
            return ""
        try:
            profile = user.profile
            return (profile.region or "")[:30]
        except Exception:
            return ""

    def _record(self, request, response):
        if request.method != "GET" or self._is_excluded_path(request.path):
            return
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "text/html":
            return

        try:
            from .models import AccessLog

            user = request.user if getattr(request.user, "is_authenticated", False) else None
            resolver_match = getattr(request, "resolver_match", None)
            route_name = ""
            if resolver_match:
                route_name = resolver_match.view_name or resolver_match.url_name or ""
            AccessLog.objects.create(
                user=user,
                is_authenticated=user is not None,
                route_name=str(route_name)[:150],
                region=self._region_for(user),
                device_type=self._device_type(request.META.get("HTTP_USER_AGENT", "")),
                status_code=int(response.status_code),
            )
        except Exception:
            # Observability must never make the user's page fail.
            return
