"""
Production settings — used on the DO droplet.
"""
import sys

import sentry_sdk

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[".lawsaas.app"])

# Strict cookie / TLS posture
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default=".lawsaas.app")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Next.js needs to read it to attach to mutating requests
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://*.lawsaas.app"])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Validate critical secrets at startup — fail fast.
_required_secrets = ["SECRET_KEY", "MASTER_KEK", "POSTGRES_PASSWORD"]
for _key in _required_secrets:
    if not env(_key, default=""):
        sys.stderr.write(f"FATAL: missing required env var {_key}\n")
        sys.exit(1)

# Sentry
_sentry_dsn = env("SENTRY_DSN_API", default="")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
        release=env("SENTRY_RELEASE", default=None),
    )

# JSON logs to stdout — droplet's journald captures them.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security.DisallowedHost": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}

# Email via Resend SMTP relay (or use the resend Python SDK directly in tasks)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = env("RESEND_API_KEY", default="")
