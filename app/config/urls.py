from django.contrib import admin
from django.urls import include, path

from notes import views

urlpatterns = [
    path("health/", views.health, name="health"),        # liveness/readiness/ALB checks
    path("health/ready/", views.ready, name="ready"),    # deep check: DB + Redis
    path("", include("django_prometheus.urls")),          # exposes /metrics
    path("admin/", admin.site.urls),
    path("", include("notes.urls")),
]
