"""
Django settings for production.

Use DJANGO_SETTINGS_MODULE=core.production_settings to use it.
"""

from settings import *

import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('no SECRET_KEY found')

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

