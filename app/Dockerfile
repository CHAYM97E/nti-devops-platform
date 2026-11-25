# syntax=docker/dockerfile:1
###############################################################################
# Lab 09 — Multi-stage Dockerfile for the Django app
#
# Stage 1 (builder): has compilers; installs Python packages into a venv.
# Stage 2 (runtime): copies ONLY the venv + app code. No compilers, smaller
#                    image, fewer packages for Trivy to flag.
###############################################################################

FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


FROM python:3.13-slim AS runtime

ARG APP_VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    APP_VERSION=${APP_VERSION}

# curl is used only by the HEALTHCHECK below.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 1000 appgroup \
 && useradd --uid 1000 --gid 1000 --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=appuser:appgroup . .

# Collect static files AT BUILD TIME so the running container can use a
# read-only root filesystem (Kubernetes securityContext in Lab 11).
# The SECRET_KEY here is a throwaway used only for this build step.
RUN SECRET_KEY=build-only-not-secret python manage.py collectstatic --noinput \
 && mkdir -p /app/media \
 && chown -R appuser:appgroup /app/media /app/staticfiles \
 && chmod 755 /app/entrypoint.sh

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
