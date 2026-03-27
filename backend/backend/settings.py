"""
Django settings for Forex Alpha backend
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ── Windows encoding fix ───────────────────────────────────────────────────────
# psycopg2 on Windows appends `pgpassfile=%APPDATA%\postgresql\pgpass.conf` to
# the DSN string.  If the Windows user-profile path (%APPDATA% / %USERPROFILE%)
# contains a non-ASCII character (e.g. "é" → 0xe9 in cp1252) the DSN cannot be
# decoded as UTF-8 and psycopg2 raises UnicodeDecodeError before connecting.
#
# Fixes applied:
#  1. PGPASSFILE=NUL  → psycopg2 stops appending the pgpass path to the DSN.
#  2. PGCLIENTENCODING=UTF8  → negotiate UTF-8 at the protocol level.
#  3. Strip LANG/LC_ vars → prevent libpq picking up a Latin-1 locale.
#  4. PYTHONIOENCODING=utf-8  → ensure Python IO also uses UTF-8.
import sys
if sys.platform == 'win32':
    os.environ['PGPASSFILE'] = 'NUL'          # suppress non-ASCII pgpass path
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    for _k in [k for k in list(os.environ) if k.startswith(('LANG', 'LC_'))]:
        del os.environ[_k]
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'forex-alpha-secret-key-change-in-production-2026')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
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

WSGI_APPLICATION = 'backend.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
# Local dev → SQLite (avoids psycopg2 Windows cp1252/UTF-8 DSN encoding bug).
# Docker / production → PostgreSQL (set USE_POSTGRES=1 in environment).
# Economic indicator data is always read via direct psycopg2 calls in views.py.
_USE_POSTGRES = os.getenv('USE_POSTGRES', '0') == '1'

if _USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'forex_metadata'),
            'USER': os.getenv('POSTGRES_USER', 'forex_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'forex_pass_2026'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'OPTIONS': {'client_encoding': 'UTF8'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS — allow React dev server
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_ALL_ORIGINS = DEBUG

# DRF
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 500,
}

# InfluxDB
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', '')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'forex_alpha')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'forex_data')

# LangChain / OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
LANGCHAIN_VERBOSE = os.getenv('LANGCHAIN_VERBOSE', 'False') == 'True'

# RL Model paths
RL_MODEL_DIR = os.path.join(BASE_DIR, 'models_rl')
