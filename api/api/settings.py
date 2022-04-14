"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import sys
from pathlib import Path
import requests
from collections import OrderedDict
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import ignore_logger

from core.constants import PaginationTypes, AuthenticationTypes

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# We're adding the environments directory outside of the project directory to the path
# That way we can load the environments and re-use them in different contexts
# Like maintenance tasks and harvesting tasks
sys.path.append(os.path.join(BASE_DIR, "..", "environments"))
from project import create_configuration_and_session, MODE, CONTEXT
from utils.packaging import get_package_info
# Then we read some variables from the (build) environment
PACKAGE_INFO = get_package_info()
GIT_COMMIT = PACKAGE_INFO.get("commit", "unknown-git-commit")
VERSION = PACKAGE_INFO.get("versions").get("middleware", "0.0.0")
environment, session = create_configuration_and_session()
credentials = session.get_credentials()
IS_AWS = environment.aws.is_aws


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environment.secrets.django.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = environment.django.debug

ALLOWED_HOSTS = ["*"]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Detect our own IP address
try:
    response = requests.get("https://api.ipify.org/?format=json")
    IP = response.json()["ip"]
except Exception:
    IP = None


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'datagrowth',

    'api',
    'core',
    'sources',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'api.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "api.jinja2.environment",
            "extensions": []
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'api.wsgi.application'

SILENCED_SYSTEM_CHECKS = [
    'rest_framework.W001'
]


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environment.postgres.database,
        'USER':  environment.postgres.user,
        'PASSWORD': environment.secrets.postgres.password,
        'HOST': environment.postgres.host,
        'PORT':  environment.postgres.port
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Logging
# https://docs.djangoproject.com/en/2.2/topics/logging/
# https://docs.sentry.io/

if not DEBUG:

    def strip_sensitive_data(event, hint):
        user_agent = event.get('request', {}).get('headers', {}).get('User-Agent', None)

        if user_agent:
            del event['request']['headers']['User-Agent']

        return event

    sentry_sdk.init(
        before_send=strip_sensitive_data,
        dsn=environment.django.sentry.dsn,
        environment=environment.env,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        send_default_pii=False  # GDPR requirement
    )
    # We kill all DisallowedHost logging on the servers,
    # because it happens so frequently that we can't do much about it
    ignore_logger('django.security.DisallowedHost')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_ALLOW_ALL_ORIGINS = True


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Rest framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'PAGE_SIZE': 100
}


# Project specific settings

ENTITIES = ["persons", "projects"]

SOURCES = {
    "mock": {
        "base": {
            "url": "http://localhost:8080",
            "headers": {},
            "parameters": {}
        },
        "endpoints": {
            "persons": {
                "url": "/mocks/entity/persons/",
                "extractor": "MockPersonExtractProcessor"
            },
            "projects": {
                "url": "/mocks/entity/persons/",
                "extractor": "MockProjectExtractProcessor"
            }
        },
        "auth": {},
        "pagination": {
            "type": PaginationTypes.PAGE,
            "parameters": OrderedDict({
                "page": 1,
                "page_size": 100
            })
        }
    },
    "hva": {
        "base": {
            "url": environment.sources.hva.base_url,
            "headers": {},
            "parameters": {}
        },
        "endpoints": {
            "persons": {
                "url": "/ws/api/persons",
                "extractor": "HvaPersonExtractProcessor"
            },
            "projects": None
        },
        "auth": {
            "type": AuthenticationTypes.API_KEY_HEADER,
            "token": environment.secrets.hva.api_key
        },
        "pagination": {
            "type": PaginationTypes.OFFSET,
            "parameters": OrderedDict({
                "offset": 0,
                "size": 100
            })
        }
    },
    "hku": {
        "base": {
            "url": "https://octo.hku.nl",
            "headers": {},
            "parameters": {
                "format": "json",
                "project": "pubplatv4"
            }
        },
        "endpoints": {
            "persons": {
                "url": "/octo/repository/api2/getPersons",
                "extractor": "HkuPersonExtractProcessor"
            },
            "projects": {
                "url": "/octo/repository/api2/getProjects",
                "extractor": "HkuProjectExtractProcessor"
            }
        },
        "auth": {},
        "pagination": {}
    },
    "buas": {
        "base": {
            "url": environment.sources.buas.base_url,
            "headers": {
                "accept": "application/json"
            },
            "parameters": {}
        },
        "endpoints": {
            "persons": {
                "url": "/ws/api/523/persons",
                "extractor": "BuasPersonExtractProcessor"
            },
            "projects": None
        },
        "auth": {
            "type": AuthenticationTypes.API_KEY_HEADER,
            "token": environment.secrets.buas.api_key
        },
        "pagination": {
            "type": PaginationTypes.OFFSET,
            "parameters": OrderedDict({
                "offset": 0,
                "size": 100
            })
        }
    },
}
