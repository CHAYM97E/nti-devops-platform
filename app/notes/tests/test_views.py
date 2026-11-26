from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


class HealthTests(TestCase):
    def test_health_is_ok_without_dependencies(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_reports_database_and_cache(self):
        response = self.client.get(reverse("ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"database": "ok", "cache": "ok"})

    def test_ready_returns_503_when_cache_fails(self):
        with mock.patch("notes.views.cache.set", side_effect=ConnectionError("redis down")):
            response = self.client.get(reverse("ready"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["cache"], "error")


class NoteListTests(TestCase):
    def setUp(self):
        cache.clear()  # the cache is shared across tests; start each from zero

    def test_home_page_renders(self):
        response = self.client.get(reverse("note_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NTI DevOps Notes")

    def test_create_note_redirects_and_persists(self):
        response = self.client.post(reverse("note_list"), {"title": "First", "body": "Hello"})
        self.assertRedirects(response, reverse("note_list"))
        self.assertEqual(Note.objects.get().title, "First")

    def test_invalid_note_is_rejected(self):
        response = self.client.post(reverse("note_list"), {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Note.objects.count(), 0)

    def test_visit_counter_increments(self):
        self.client.get(reverse("note_list"))
        response = self.client.get(reverse("note_list"))
        self.assertEqual(response.context["visits"], 2)

    def test_page_still_works_when_redis_is_down(self):
        with mock.patch("notes.views.cache.incr", side_effect=ConnectionError("redis down")):
            response = self.client.get(reverse("note_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["visits"])


class PodIpHostTests(TestCase):
    """Probes and Prometheus use the pod IP as Host; they must not get 400."""

    POD_IP = "10.0.10.37:8000"

    def test_health_accepts_pod_ip_host(self):
        self.assertEqual(self.client.get("/health/", HTTP_HOST=self.POD_IP).status_code, 200)

    def test_metrics_accepts_pod_ip_host(self):
        self.assertEqual(self.client.get("/metrics", HTTP_HOST=self.POD_IP).status_code, 200)

    def test_normal_pages_still_enforce_allowed_hosts(self):
        self.assertEqual(self.client.get("/", HTTP_HOST=self.POD_IP).status_code, 400)


class MetricsTests(TestCase):
    def test_metrics_endpoint_exposes_prometheus_format(self):
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"django_http_requests", response.content)


class ProductionBackendsImportTests(TestCase):
    """
    Tests run with an in-memory cache, so they would never notice a missing
    Redis library. Import the PRODUCTION backends explicitly so a missing
    dependency in requirements.txt fails CI instead of the running container.
    """

    def test_production_cache_backend_is_importable(self):
        from django.utils.module_loading import import_string

        from config.settings import base

        import_string(base.CACHES["default"]["BACKEND"])

    def test_production_database_backend_is_importable(self):
        import importlib

        from config.settings import base

        importlib.import_module(base.DATABASES["default"]["ENGINE"] + ".base")
