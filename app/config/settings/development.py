"""Local development (Docker Compose on your laptop)."""
from .base import *  # noqa: F401,F403
from .base import SECRET_KEY, env_bool

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = SECRET_KEY or "dev-only-insecure-key-never-use-in-production"
