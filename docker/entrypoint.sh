#!/usr/bin/env sh
# Container entrypoint: prepare the app, then exec the given command (gunicorn).
set -e

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

# Optional: seed the legacy content on first boot (set SEED_CONTENT=1).
if [ "${SEED_CONTENT:-0}" = "1" ]; then
    echo "==> Seeding content"
    python manage.py seed_content
fi

# Optional: create an admin user non-interactively if the env vars are provided.
# Requires DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "==> Ensuring superuser '${DJANGO_SUPERUSER_USERNAME}' exists"
    python manage.py createsuperuser --noinput || true
fi

echo "==> Starting: $*"
exec "$@"
