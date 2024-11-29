"""
Django settings for profiling mode.

Use DJANGO_SETTINGS_MODULE=core.profiling_settings to use it.
"""

from core.settings import *

MIDDLEWARE = ['silk.middleware.SilkyMiddleware'] + MIDDLEWARE

INSTALLED_APPS += ['silk']

ROOT_URLCONF = "core.profiling_urls"

STATIC_ROOT = os.path.join(BASE_DIR, 'profiling_static')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True

SILKY_PYTHON_PROFILER_RESULT_PATH = 'profiling_prof_files/'

# create directory if not exists
if not os.path.exists(SILKY_PYTHON_PROFILER_RESULT_PATH):
    os.makedirs(SILKY_PYTHON_PROFILER_RESULT_PATH)

