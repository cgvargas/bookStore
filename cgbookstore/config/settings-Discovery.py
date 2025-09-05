# Configuração de Banco de Dados Supabase - Atualizada em 2025-07-22
# Host funcional confirmado: db.amytpwmgpkizuwkwvpzm.supabase.co

import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega variáveis de ambiente do arquivo .env
try:
    from decouple import config

    ENV_LOADED = True
except ImportError:
    print("⚠️  python-decouple não instalado. Usando configurações padrão.")
    ENV_LOADED = False


    # Fallback simples para leitura de .env
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast and value is not None:
            try:
                return cast(value)
            except (ValueError, TypeError):
                return default
        return value

# Carrega arquivo .env se existir
env_file = BASE_DIR / '.env'
if env_file.exists() and ENV_LOADED:
    # python-decouple carrega automaticamente
    pass
elif env_file.exists():
    # Carregamento manual do .env
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
    except Exception as e:
        print(f"⚠️  Erro ao carregar .env: {e}")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# Database Configuration
# Configuração do Supabase com fallback para SQLite
def get_database_config():
    """
    Retorna configuração de banco de dados com fallback
    """
    # Tenta configuração Supabase primeiro
    supabase_host = config('SUPABASE_DB_HOST', default='')
    supabase_password = config('SUPABASE_DB_PASSWORD', default='')

    if supabase_host and supabase_password:
        # Configuração Supabase
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'HOST': config('SUPABASE_DB_HOST', default='db.amytpwmgpkizuwkwvpzm.supabase.co'),
                'NAME': config('SUPABASE_DB_NAME', default='postgres'),
                'USER': config('SUPABASE_DB_USER', default='postgres'),
                'PASSWORD': config('SUPABASE_DB_PASSWORD', default=''),
                'PORT': config('SUPABASE_DB_PORT', default='5432', cast=int),
                'OPTIONS': {
                    'connect_timeout': 30,
                    'options': '-c statement_timeout=30000',
                    'sslmode': 'require',
                },
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'TEST': {
                    'NAME': 'test_postgres',
                },
            }
        }
    else:
        # Fallback para SQLite
        print("⚠️  Credenciais Supabase não encontradas. Usando SQLite local.")
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
                'OPTIONS': {
                    'timeout': 20,
                },
            }
        }


# Aplica configuração de banco
DATABASES = get_database_config()

# Configuração alternativa usando DATABASE_URL (comentada por problemas no Windows)
# try:
#     import dj_database_url
#     database_url = config('DATABASE_URL', default='')
#     if database_url:
#         DATABASES = {
#             'default': dj_database_url.config(
#                 default=database_url,
#                 conn_max_age=600,
#                 conn_health_checks=True,
#             )
#         }
# except ImportError:
#     pass

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
    'corsheaders',
]

LOCAL_APPS = [
    'cgbookstore.apps.core',
    'cgbookstore.apps.books',
    'cgbookstore.apps.users',
    'cgbookstore.apps.api',
    'cgbookstore.apps.chatbot',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

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

ROOT_URLCONF = 'cgbookstore.config.urls'

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

WSGI_APPLICATION = 'cgbookstore.config.wsgi.application'

# Password validation
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
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

# Supabase Configuration
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_ANON_KEY = config('SUPABASE_ANON_KEY', default='')
SUPABASE_SERVICE_ROLE_KEY = config('SUPABASE_SERVICE_ROLE_KEY', default='')

# Chatbot Configuration
OLLAMA_BASE_URL = config('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3.2:3b')

# Google Books API
GOOGLE_BOOKS_API_KEY = config('GOOGLE_BOOKS_API_KEY', default='')

# Email Configuration (para produção)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True

# Security Settings (para produção)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cgbookstore': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Cria diretório de logs se não existir
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configurações específicas do ambiente
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'development':
    print(f"🔧 Ambiente: {ENVIRONMENT}")
    print(f"🗄️  Database: {DATABASES['default']['ENGINE'].split('.')[-1]}")
    if 'postgresql' in DATABASES['default']['ENGINE']:
        print(f"🌐 Host: {DATABASES['default']['HOST']}")
    print(f"🔍 Debug: {DEBUG}")

# Configurações do projeto específicas
BOOKS_PER_PAGE = 12
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'WEBP']

# Rate limiting (implementar com django-ratelimit se necessário)
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)