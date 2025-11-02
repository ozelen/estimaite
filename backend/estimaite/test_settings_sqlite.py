"""
Django test settings for estimaite project using SQLite.

This file extends the base settings for faster local testing with SQLite.
"""

from .settings import *

# Use SQLite for faster tests (no Docker required)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests (optional)
LOGGING_CONFIG = None

# Cache configuration for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Security settings for tests
DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

ALLOWED_HOSTS = ["*"]

# Authentication
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "users:profile"
