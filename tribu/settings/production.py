import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

# SECURITY ---------------------------------------------------------------

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# Behind the nginx reverse proxy, trust the forwarded protocol header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Toggle HTTPS hardening once a TLS certificate is in front of nginx.
if os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "false").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# DATABASE ---------------------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# STATIC / MEDIA ---------------------------------------------------------

# ManifestStaticFilesStorage prevents stale cached JS/CSS after a deploy.
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

# WAGTAIL ----------------------------------------------------------------

WAGTAILADMIN_BASE_URL = os.environ.get(
    "WAGTAILADMIN_BASE_URL", "https://latribudoya.fr"
)

# LOGGING ----------------------------------------------------------------

# Sans config explicite, Django n'attache aucun handler aux loggers
# applicatifs quand DEBUG=False : les warnings partent dans le vide.
# Tout est envoyé sur la console (stdout/stderr), que gunicorn propage
# à `docker logs` / `docker compose logs web`.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} : {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}

# EMAIL ------------------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
