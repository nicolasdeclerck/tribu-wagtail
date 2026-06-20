# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# STAGE 1 — Build the Tailwind stylesheet with the standalone CLI (no Node).
# ---------------------------------------------------------------------------
FROM debian:bookworm-slim AS tailwind

ARG TARGETARCH
ARG TAILWIND_VERSION=v3.4.17

RUN apt-get update --yes --quiet \
 && apt-get install --yes --quiet --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download the CLI matching the build architecture.
RUN case "$TARGETARCH" in \
        amd64) ASSET="tailwindcss-linux-x64" ;; \
        arm64) ASSET="tailwindcss-linux-arm64" ;; \
        *) echo "Unsupported arch: $TARGETARCH" && exit 1 ;; \
    esac \
 && curl -sL -o /usr/local/bin/tailwindcss \
        "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/${ASSET}" \
 && chmod +x /usr/local/bin/tailwindcss

# Copy the bits Tailwind needs to scan template/JS content + the config.
COPY tailwind.config.js ./
COPY theme ./theme
COPY tribu ./tribu
COPY core ./core
COPY home ./home
COPY projets ./projets
COPY stages ./stages
COPY compagnie ./compagnie
COPY reseaux ./reseaux
COPY search ./search

RUN tailwindcss -c tailwind.config.js \
        -i theme/static_src/input.css \
        -o core/static/css/app.css --minify


# ---------------------------------------------------------------------------
# STAGE 2 — Build the Python virtual environment.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/* \
 && python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt


# ---------------------------------------------------------------------------
# STAGE 3 — Runtime image.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home wagtail

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=tribu.settings.production \
    PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
WORKDIR /app

# Python environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Application source.
COPY --chown=wagtail:wagtail . .

# Tailwind-compiled stylesheet from the tailwind stage (overrides any committed copy).
COPY --from=tailwind --chown=wagtail:wagtail /app/core/static/css/app.css ./core/static/css/app.css

# STATIC_ROOT and MEDIA_ROOT live on mounted volumes, created and owned by wagtail.
RUN mkdir -p /app/static /app/media && chown -R wagtail:wagtail /app/static /app/media

COPY --chown=wagtail:wagtail docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER wagtail

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "tribu.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
