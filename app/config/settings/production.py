"""Production (EKS). Fails fast if a required secret is missing."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import SECRET_KEY, env_bool

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set in production.")

DEBUG = False

# The ALB terminates the client connection and forwards the original scheme
# in X-Forwarded-Proto. Trust it so Django knows when a request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Enable these once the ALB has an HTTPS listener (ACM certificate).
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = env_bool("SECURE_COOKIES", False)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
