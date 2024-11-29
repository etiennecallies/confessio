"""
Django settings for profiling mode.

Use DJANGO_SETTINGS_MODULE=core.profiling_settings to use it.
"""

from core.settings import *

MIDDLEWARE = ['silk.middleware.SilkyMiddleware'] + MIDDLEWARE

INSTALLED_APPS += ['silk']

ROOT_URLCONF = "core.profiling_urls"

STATIC_ROOT = os.path.join(BASE_DIR, 'static_profiling')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
