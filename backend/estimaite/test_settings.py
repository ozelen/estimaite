"""
Django test settings for estimaite project.

This file extends the base settings for testing purposes.
"""
import os
from .settings import *

# Use PostgreSQL for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "test_estimaite"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": os.environ.get("POSTGRES_DB", "test_estimaite"),
        },
    }
}

# Disable migrations for faster tests (optional - comment out if you need migrations)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None

# MIGRATION_MODULES = DisableMigrations()

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

