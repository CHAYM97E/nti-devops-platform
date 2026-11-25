import logging
import socket

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .forms import NoteForm
from .models import Note

logger = logging.getLogger(__name__)

VISITS_KEY = "notes:visits"


@require_GET
def health(request):
    """
    Liveness check: "is the Python process alive and serving?"

    Deliberately touches NO dependency. If Kubernetes restarted pods every
    time RDS blipped, a database hiccup would turn into a full outage.
    """
    return JsonResponse({"status": "ok", "version": settings.APP_VERSION})


@require_GET
def ready(request):
    """Readiness check: can this pod actually serve traffic (DB + Redis)?"""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report any failure
        logger.warning("Readiness: database check failed: %s", exc)
        checks["database"] = "error"
    try:
        cache.set("health:ping", "pong", 5)
        checks["cache"] = "ok" if cache.get("health:ping") == "pong" else "error"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness: cache check failed: %s", exc)
        checks["cache"] = "error"

    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=200 if healthy else 503,
    )


def note_list(request):
    """Home page: list notes (PostgreSQL) and count visits (Redis)."""
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("note_list")
    else:
        form = NoteForm()

    try:
        visits = cache.incr(VISITS_KEY)
    except ValueError:  # key does not exist yet
        cache.set(VISITS_KEY, 1, timeout=None)
        visits = 1
    except Exception:  # noqa: BLE001 - Redis down must not break the page
        logger.warning("Redis unavailable; visit counter disabled")
        visits = None

    context = {
        "notes": Note.objects.all()[:50],
        "form": form,
        "visits": visits,
        "hostname": socket.gethostname(),  # shows WHICH pod answered (load balancing demo)
        "version": settings.APP_VERSION,
    }
    return render(request, "notes/note_list.html", context)
