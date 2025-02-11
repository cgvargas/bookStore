# Django settings for config project.
import os
from pathlib import Path
import environ

# Configuração do environ
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-r%4)z4dffs_qqw8y$8g!om4h_0h$md^_y70+1q=w$xh=foy!uj')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    # Apps locais
    'cgbookstore.apps.core.apps.CoreConfig',
    'cgbookstore.apps.core.recommendations.analytics.admin_dashboard',
    'cgbookstore.apps.core.recommendations.analytics.apps.AnalyticsConfig',

    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',

    # Apps terceiros
    'stdimage',
    'django_extensions',
]

MIDDLEWARE = [
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
        'DIRS': ['templates'],
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

# Configurações de E-mail
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@cgbookstore.com')
SERVER_EMAIL = env('SERVER_EMAIL', default='server@cgbookstore.com')

# Configurações de Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'google_books': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'google-books-cache',
        'TIMEOUT': 60 * 60 * 24,  # 24 horas
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Máximo de entradas no cache
            'CULL_FREQUENCY': 3,  # Frequência de limpeza quando MAX_ENTRIES é atingido
        }
    }
}

# Configurações da API Google Books
GOOGLE_BOOKS_CACHE_TIMEOUT = 60 * 60 * 24  # 24 horas em segundos
GOOGLE_BOOKS_CACHE_KEY_PREFIX = 'google_books:'

# API Key do Google Books
GOOGLE_BOOKS_API_KEY = os.getenv('GOOGLE_BOOKS_API_KEY', 'AIzaSyBF5W5NktgXZRfTnZXe3pVxqB_TCkXGzx0')

# Configurações de Autenticação
LOGIN_REDIRECT_URL = 'index'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'index'

# Configurações de Sessão
SESSION_COOKIE_AGE = 604800  # 1 semana em segundos
SESSION_COOKIE_SECURE = True  # Cookies apenas via HTTPS
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Sessão persiste após fechar navegador

