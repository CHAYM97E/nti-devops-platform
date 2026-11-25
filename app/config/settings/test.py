"""
Test settings (Jenkins "Unit Tests" stage).

Uses the real PostgreSQL from DATABASE_URL when CI provides one; otherwise
falls back to SQLite so a developer can run `python manage.py test` with no
services running. The cache is in-memory so tests never depend on Redis.
"""
import os

from .base import *  # noqa: F401,F403

SECRET_KEY = "test-only-secret-key"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

if not os.environ.get("DATABASE_URL") and not os.environ.get("DB_HOST"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast tests only
