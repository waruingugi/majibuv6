"""
Django settings for majibu project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Path of the env file used in development
ENV_PATH = os.path.join(BASE_DIR, "env/.env.local").replace("\\", "/")

# Load environment variables
load_dotenv(ENV_PATH, override=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.environ["DEBUG"]))

ALLOWED_HOSTS: list[str] = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "phonenumber_field",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    # Apps
    "users",
    "commons",
    "notifications",
    "accounts",
]

MIDDLEWARE = [
    "log_request_id.middleware.RequestIDMiddleware",  # Third party app
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "commons.middlewares.UserIsActiveMiddleware",
    "commons.middlewares.RequestResponseLoggerMiddleware",
]

ROOT_URLCONF = "majibu.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "majibu.local_wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "CONN_MAX_AGE": 300,  # 5 minutes
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Nairobi"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ["REDIS_URL"],
    }
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=5),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": (
        "rest_framework_simplejwt.tokens.AccessToken",
        "users.tokens.UserRefreshToken",
    ),
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_RATES": {
        "authentication_throttle": "10/hour",
        "mpesa_stkpush_throttle": "3/minute",
        "mpesa_withdrawal_throttle": "1/minute",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "commons.pagination.StandardPageNumberPagination",
}

CELERY_BROKER_URL = os.environ["REDIS_URL"]
CELERY_ACCEPT_CONTENT = {"application/json"}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Nairobi"

HOST_PINNACLE_USER_ID = ""
HOST_PINNACLE_PASSWORD = ""
HOST_PINNACLE_SENDER_ID = ""

# DRF Spectacular Settings for Swagger
SPECTACULAR_SETTINGS = {
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
    },
    # Only authenticated users can access the schema and documentation views.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "AUTHENTICATION_WHITELIST": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "SERVE_AUTHENTICATION": [
        # User can only view swagger docs if they've logged in via django admin
        "rest_framework.authentication.SessionAuthentication",
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}


MPESA_BUSINESS_SHORT_CODE = os.environ["MPESA_BUSINESS_SHORT_CODE"]
MPESA_B2C_CHARGE = int(os.environ["MPESA_B2C_CHARGE"])
MPESA_B2C_CONSUMER_KEY = os.environ["MPESA_B2C_CONSUMER_KEY"]
MPESA_B2C_SECRET = os.environ["MPESA_B2C_SECRET"]
MPESA_B2C_PASSWORD = os.environ["MPESA_B2C_PASSWORD"]
MPESA_B2C_URL = os.environ["MPESA_B2C_URL"]
MPESA_B2C_INITIATOR_NAME = os.environ["MPESA_B2C_INITIATOR_NAME"]
MPESA_B2C_SHORT_CODE = os.environ["MPESA_B2C_SHORT_CODE"]
MPESA_B2C_QUEUE_TIMEOUT_URL = os.environ["MPESA_B2C_QUEUE_TIMEOUT_URL"]
MPESA_B2C_RESULT_URL = os.environ["MPESA_B2C_RESULT_URL"]


MPESA_CALLBACK_URL = os.environ["MPESA_CALLBACK_URL"]
MPESA_CONSUMER_KEY = os.environ["MPESA_CONSUMER_KEY"]
MPESA_DATETIME_FORMAT = "%Y%m%d%H%M%S"

MPESA_PASS_KEY = os.environ["MPESA_PASS_KEY"]
MPESA_SECRET = os.environ["MPESA_SECRET"]
MPESA_STKPUSH_URL = os.environ["MPESA_STKPUSH_URL"]
MPESA_TOKEN_URL = os.environ["MPESA_TOKEN_URL"]
WITHDRAWAL_BUFFER_PERIOD = int(os.environ["WITHDRAWAL_BUFFER_PERIOD"])
