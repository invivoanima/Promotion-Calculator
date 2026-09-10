"""Django settings for the promotion calculator.

Production deployments should provide ``DJANGO_SECRET_KEY``,
``DJANGO_DEBUG=0`` and ``DJANGO_ALLOWED_HOSTS``.
"""

from pathlib import Path
import os
from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean environment variable using common truthy values."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "development-only-promotion-calculator-secret",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,127.0.0.1.nip.io,testserver",
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "calc.apps.CalcConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "calc.middleware.RequestAuditContextMiddleware",
    "calc.middleware.AccessLogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "promocalc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "calc.context_processors.navigation_context",
            ],
        },
    },
]

WSGI_APPLICATION = "promocalc.wsgi.application"
ASGI_APPLICATION = "promocalc.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(
            os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3"))
        ),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Suggestion attachments are validated again in the form/model.  The small
# request overhead allowance keeps a file exactly at the application limit
# from being rejected by Django's multipart parser.
MAX_UPLOAD_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE + (1024 * 1024)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "calc:login"
LOGIN_REDIRECT_URL = "calc:dashboard"
LOGOUT_REDIRECT_URL = "calc:welcome"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

if env_bool("DJANGO_USE_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

APP_ENV = os.environ.get("PROMOCALC_ENV", "development").strip().lower()
USER_ACTION_LOG_ENABLED = env_bool("USER_ACTION_LOG_ENABLED", False)
USER_ACTION_LOG_DIR = os.environ.get("USER_ACTION_LOG_DIR", "")
USER_ACTION_LOG_RETENTION_MONTHS = int(os.environ.get("USER_ACTION_LOG_RETENTION_MONTHS", "3"))
USER_ACTION_LOG_MAX_QUERY_DAYS = 7
USER_ACTION_LOG_PAGE_SIZE = 50
# Keep false until the deployment proves the direct peer is the real client.
TRUST_DIRECT_CLIENT_IP = env_bool("TRUST_DIRECT_CLIENT_IP", False)
LEGAL_TERMS_VERSION = "2026-09-10"
LEGAL_PRIVACY_VERSION = "2026-09-10"
LEGAL_OPERATOR_NAME = os.environ.get("LEGAL_OPERATOR_NAME", "").strip()
LEGAL_CONTACT = os.environ.get("LEGAL_CONTACT", "").strip()
