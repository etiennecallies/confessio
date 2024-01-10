"""
Django settings for production.

Use DJANGO_SETTINGS_MODULE=core.production_settings to use it.
"""

from core.settings import *

import os

# SECURITY WARNING: keep the secret key used in production secret!
if not os.environ.get('DJANGO_SECRET_KEY'):
    raise ValueError('no DJANGO_SECRET_KEY found')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')


# Allow server host only
if not os.environ.get('SERVER_HOST'):
    raise ValueError('no SERVER_HOST found')
ALLOWED_HOSTS = [f'.{os.environ.get("SERVER_HOST")}']
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Render Production Code
DEBUG = False


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE   = os.getenv('PROD_DB_ENGINE'   , None)
DB_USERNAME = os.getenv('PROD_DB_USERNAME' , None)
DB_PASS     = os.getenv('PROD_DB_PASS'     , None)
DB_HOST     = os.getenv('PROD_DB_HOST'     , None)
DB_PORT     = os.getenv('PROD_DB_PORT'     , None)
DB_NAME     = os.getenv('PROD_DB_NAME'     , None)

DATABASES = {
  'default': {
    'ENGINE'  : DB_ENGINE,
    'NAME'    : DB_NAME,
    'USER'    : DB_USERNAME,
    'PASSWORD': DB_PASS,
    'HOST'    : DB_HOST,
    'PORT'    : DB_PORT,
    },
}

# Email
LOGIN_REDIRECT_URL = '/'
DEFAULT_FROM_EMAIL = f"no-reply@{os.environ.get('SERVER_HOST')}"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
if not os.environ.get('STATIC_ROOT'):
    raise ValueError('no STATIC_ROOT found')
STATIC_ROOT = os.environ.get('STATIC_ROOT')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

# DB BACKUP
INSTALLED_APPS += ['dbbackup']
DBBACKUP_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DBBACKUP_STORAGE_OPTIONS = {
    'access_key': os.environ.get('AWS_ACCESS_KEY'),
    'secret_key': os.environ.get('AWS_SECRET_KEY'),
    'bucket_name': os.environ.get('DBBACKUP_BUCKET') or 'confessio-dbbackup-daily',
    'default_acl': 'private',
}
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = [('Mr Admin', os.environ.get('ADMIN_EMAIL'))]
