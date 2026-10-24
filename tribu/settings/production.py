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

# SMTP activé dès que EMAIL_HOST est défini (OVH, cf. README) ; sinon
# les mails (formulaire de contact…) sont seulement écrits dans les logs.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend",
)
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = 10

# Expéditeur par défaut quand le champ « Adresse de l'expéditeur » de la page
# de contact est vide. Doit être la boîte OVH authentifiée (EMAIL_HOST_USER) :
# le SMTP OVH refuse d'envoyer au nom d'une autre adresse.
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
