# Django Settings for SafeHaven EHR System
import os
import sys
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-theracare-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,healthcheck.railway.app,.railway.app,shrm-backend-production.up.railway.app,shrm-frontend.up.railway.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Ensure Railway domains are present when deploying in Railway environment
if config('RAILWAY_ENVIRONMENT', default=None):
    for host in ['healthcheck.railway.app', '.railway.app']:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',
    'drf_spectacular',
    'django_filters',
    'channels',
]

LOCAL_APPS = [
    'core',
    'users',
    'patients',
    'appointments',
    'audit',
    'billing',
    'messages.apps.MessagesConfig',  # Use explicit config to avoid conflict with django.contrib.messages
    'telehealth',
    'soap_notes',
    'notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuditMiddleware',
    'core.middleware.HIPAAComplianceMiddleware',
]

ROOT_URLCONF = 'theracare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'theracare.wsgi.application'
ASGI_APPLICATION = 'theracare.asgi.application'

# Database Configuration
# Use DATABASE_URL if provided (for Railway/PostgreSQL), otherwise use individual DB variables
DB_CONNECTION = config('DB_CONNECTION', default='postgresql')
DATABASE_URL = (
    config('DATABASE_URL', default='')
    or config('POSTGRES_URL', default='')
    or config('POSTGRESQL_URL', default='')
    or ''
)

if DATABASE_URL:
    # Use DATABASE_URL for Railway PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Use individual database variables for MySQL or other databases
    db_name = config('DB_DATABASE', default=config('PGDATABASE', default='railway'))
    db_user = config('DB_USERNAME', default=config('PGUSER', default='postgres'))
    db_password = config('DB_PASSWORD', default=config('PGPASSWORD', default=''))
    db_host = config('DB_HOST', default=config('PGHOST', default='127.0.0.1'))
    db_port = config('DB_PORT', default=config('PGPORT', default='3306' if DB_CONNECTION == 'mysql' else '5432'))

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql' if DB_CONNECTION == 'mysql' else 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # HIPAA compliance requirement
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'core.validators.CustomPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATICFILES_DIRS = [BASE_DIR / 'static']  # Commented out - directory not needed

# Whitenoise configuration for serving static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', 
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,https://shrm-frontend.up.railway.app,https://shrm-backend-production.up.railway.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# Additional CORS settings for production
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# HIPAA Compliance Settings
HIPAA_SETTINGS = {
    'ENCRYPTION_KEY': config('ENCRYPTION_KEY', default='hipaa-encryption-key-change-in-production'),
    'AUDIT_ALL_REQUESTS': True,
    'REQUIRE_STRONG_PASSWORDS': True,
    'SESSION_TIMEOUT': 30,  # minutes
    'MAX_LOGIN_ATTEMPTS': 3,
    'LOCKOUT_DURATION': 15,  # minutes
    'REQUIRE_2FA': config('REQUIRE_2FA', default=False, cast=bool),
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session Security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF Security
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', 
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,https://shrm-frontend.up.railway.app,https://shrm-backend-production.up.railway.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:")

if DEBUG:
    # Development - allow local connections
    CSP_CONNECT_SRC = ("'self'", "localhost:3000", "localhost:5173", "localhost:5174", "localhost:8000", "127.0.0.1:3000", "127.0.0.1:5173", "127.0.0.1:5174", "127.0.0.1:8000", "ws:", "wss:", "ws://localhost:8000", "ws://127.0.0.1:8000")
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")  # Needed for Vite dev
    CSP_MEDIA_SRC = ("'self'", "blob:", "mediastream:")  # Allow camera/microphone streams
else:
    # Production - allow Railway backend
    CSP_CONNECT_SRC = ("'self'", "https://shrm-backend-production.up.railway.app", "https://shrm-frontend.up.railway.app", "wss://shrm-backend-production.up.railway.app", "ws:", "wss:")
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
    CSP_MEDIA_SRC = ("'self'", "blob:", "mediastream:")  # Allow camera/microphone streams

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@theracare.com')

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Channels Configuration (for WebSockets)
# Accept common Railway/Redis variable names and fall back to in-memory for local single-process runs.
REDIS_URL = (
    config('REDIS_URL', default='')
    or config('REDIS_PRIVATE_URL', default='')
    or config('REDIS_PUBLIC_URL', default='')
    or None
)

IS_PRODUCTION_RUNTIME = (not DEBUG) or bool(config('RAILWAY_ENVIRONMENT', default=None))
ALLOW_INMEMORY_CHANNEL_LAYER = config('ALLOW_INMEMORY_CHANNEL_LAYER', default=False, cast=bool)
MANAGEMENT_COMMANDS_ALLOWLIST = {'check', 'makemigrations', 'migrate', 'collectstatic', 'shell', 'test'}
IS_MANAGEMENT_COMMAND = len(sys.argv) > 1 and sys.argv[1] in MANAGEMENT_COMMANDS_ALLOWLIST

if IS_PRODUCTION_RUNTIME and not IS_MANAGEMENT_COMMAND and not REDIS_URL and not ALLOW_INMEMORY_CHANNEL_LAYER:
    raise ImproperlyConfigured(
        'Redis is required for Channels in production. Set REDIS_URL (or REDIS_PRIVATE_URL/REDIS_PUBLIC_URL). '
        'Use ALLOW_INMEMORY_CHANNEL_LAYER=true only for temporary emergency diagnostics.'
    )

if REDIS_URL:
    # Use Redis when REDIS_URL is provided
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    # Use in-memory channel layer (works for single-server deployments)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'theracare.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 20,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'theracare': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'SafeHaven EHR API',
    'DESCRIPTION': 'HIPAA-Compliant Therapeutic EHR System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Cache Configuration
# Use dummy cache for development (no Redis required)
# For production, use Redis by setting USE_REDIS=True in environment
USE_REDIS = config('USE_REDIS', default=False, cast=bool)

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://localhost:6379/2'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'theracare',
            'TIMEOUT': 300,
        }
    }
else:
    # Dummy cache for development - no Redis needed
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Ensure logs directory exists
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Frontend URL for email templates
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')