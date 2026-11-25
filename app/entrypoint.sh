#!/bin/bash
###############################################################################
# Container entrypoint
#
# 1. Wait until PostgreSQL (and Redis, if configured) accept TCP connections.
# 2. Optionally run migrations (RUN_MIGRATIONS=true). On Kubernetes we set it
#    to false and run migrations ONCE in a Job, so 2–6 replicas don't race.
# 3. exec Gunicorn so it becomes PID 1 and receives SIGTERM directly
#    (graceful shutdown during rolling updates).
#
# If arguments are passed (e.g. `python manage.py test`), run them instead
# of Gunicorn — this is how the Jenkins test stage uses the same image.
###############################################################################
set -euo pipefail

log() { echo "[entrypoint] $(date -u +%FT%TZ) $*"; }

wait_for() {
  local host="$1" port="$2" name="$3" retries="${4:-30}"
  log "Waiting for ${name} at ${host}:${port}..."
  until python -c "import socket,sys; socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=2).close()" "$host" "$port" 2>/dev/null; do
    retries=$((retries - 1))
    if [ "$retries" -le 0 ]; then
      log "ERROR: ${name} at ${host}:${port} is not reachable"
      exit 1
    fi
    sleep 2
  done
  log "${name} is reachable."
}

[ -n "${DB_HOST:-}" ] && wait_for "$DB_HOST" "${DB_PORT:-5432}" "PostgreSQL"
[ -n "${REDIS_HOST:-}" ] && wait_for "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" 15

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  log "Running database migrations..."
  python manage.py migrate --noinput
fi

if [ "$#" -gt 0 ]; then
  log "Running command: $*"
  exec "$@"
fi

WORKERS="${GUNICORN_WORKERS:-$(( 2 * $(nproc) + 1 ))}"
log "Starting Gunicorn (workers=${WORKERS}, threads=${GUNICORN_THREADS:-2}, version=${APP_VERSION:-dev})"
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:8000" \
  --workers "${WORKERS}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --worker-class gthread \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --graceful-timeout 25 \
  --worker-tmp-dir /dev/shm \
  --access-logfile - \
  --error-logfile - \
  --forwarded-allow-ips "*"
