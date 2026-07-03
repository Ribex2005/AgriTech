"""
Django settings for agrosense_backend project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --------------------------------------------------
# BASE DIR
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = 'django-insecure-m$g_aig+qt*4n5g7#^v0m%r#2zljqfyow0xrb+s*&prjxz3ihr'
DEBUG = False
ALLOWED_HOSTS = ["agritech-uzc8.onrender.com",]


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your app
    'api',

    # Django REST Framework
    'rest_framework',

    # CORS
    'corsheaders',
]


# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------
REST_FRAMEWORK = {
    # ✅ FIX: Removed SessionAuthentication — it enforces CSRF on POST requests.
    # Since we use JWT, we don't need session-based auth at all.
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}


# --------------------------------------------------
# MIDDLEWARE
# ✅ FIX: Explicit ordering — CorsMiddleware first, then JWTAuthMiddleware,
#         then everything else. Removed the broken MIDDLEWARE.insert(0, ...)
#         pattern which was pushing JWT before CorsMiddleware and causing
#         preflight OPTIONS requests to fail.
# --------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',                          # ← MUST be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'api.middleware.auth_middleware.JWTAuthMiddleware',               # ← after CORS
    'django.middleware.common.CommonMiddleware',
    # ✅ FIX: CsrfViewMiddleware REMOVED — frontend sends no CSRF token,
    #         and we use JWT for auth. Keeping it was silently 403-ing every
    #         POST request (detect, chat, market) from the browser.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# --------------------------------------------------
# URLS & WSGI
# --------------------------------------------------
ROOT_URLCONF = 'agrosense_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agrosense_backend.wsgi.application'


# --------------------------------------------------
# DATABASE (SQLite for Django internals)
# MongoDB handled separately via pymongo
# --------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# STATIC & MEDIA FILES
# --------------------------------------------------
STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')


# --------------------------------------------------
# DEFAULT AUTO FIELD
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --------------------------------------------------
# CORS SETTINGS
# ✅ These are correct and unchanged.
# --------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# --------------------------------------------------
# EMAIL CONFIGURATION (GMAIL SMTP)
# --------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# --------------------------------------------------
# SAFETY CHECK (VERY IMPORTANT)
# --------------------------------------------------
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    raise Exception("EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not loaded from .env")
