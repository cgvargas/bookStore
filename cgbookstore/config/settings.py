# Django settings for config project.
import os
from pathlib import Path
import environ
import logging


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuração do environ
env = environ.Env()

# Define explicitamente o ambiente
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
print(f"\nAmbiente de: {DJANGO_ENV}")

# Define qual arquivo .env usar baseado no ambiente
ENV_FILE = '.env.dev' if DJANGO_ENV == 'development' else '.env.prod'
environ.Env.read_env(os.path.join(BASE_DIR.parent, ENV_FILE))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-r%4)z4dffs_qqw8y$8g!om4h_0h$md^_y70+1q=w$xh=foy!uj')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = ['*']

# Configurações SMTP para SendGrid
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='apikey')  # Isso é fixo para o SendGrid
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='cg.bookstore.online@outlook.com')
SERVER_EMAIL = env('SERVER_EMAIL', default='cg.bookstore.online@outlook.com')

# Para debug de email
if DEBUG:
    EMAIL_SUBJECT_PREFIX = '[DEV] '

# Application definition
INSTALLED_APPS = [
    # Apps locais
    'cgbookstore.apps.core.apps.CoreConfig',
    'cgbookstore.apps.core.recommendations.analytics.admin_dashboard',
    'cgbookstore.apps.core.recommendations.analytics.apps.AnalyticsConfig',
    'cgbookstore.apps.chatbot_literario.apps.ChatbotLiterarioConfig',

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
        'DIRS': [
            # Templates padrão
            os.path.join(BASE_DIR, 'templates'),
            # Templates específicos do chatbot
            os.path.join(BASE_DIR, 'apps', 'chatbot_literario', 'templates'),
        ],
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
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='cgbookstore_db'),
        'USER': env('DB_USER', default='cgbookstore_user'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'LATIN1',
            'connect_timeout': 10,
            'application_name': 'cgv_bookstore',
        },
        'ATOMIC_REQUESTS': True,
        'TIME_ZONE': 'America/Sao_Paulo',
    }
}

# Fallback para SQLite se explicitamente solicitado no ambiente de desenvolvimento
if DJANGO_ENV == 'development' and env.bool('USE_SQLITE', default=False):
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

# Configurações de Cache
if DJANGO_ENV == 'production':
    # Configuração Redis para produção
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/0',
            'TIMEOUT': 600,  # 10 minutos
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            }
        },
        'books_search': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'TIMEOUT': 60 * 60 * 2,  # 2 horas
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 500,
            }
        },
        'recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'TIMEOUT': 60 * 60 * 6,  # 6 horas (unificado)
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            }
        },
        'books_recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',  # Mesmo DB do recommendations
            'TIMEOUT': 60 * 60 * 6,  # 6 horas (unificado)
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            }
        },
        'google_books': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',
            'TIMEOUT': 60 * 60 * 24 * 7,  # 7 dias
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 2000,
            }
        },
        'image_proxy': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/4',
            'TIMEOUT': 60 * 60 * 24 * 14,  # 14 dias
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 5000,
                'COMPRESS_MIN_LEN': 10,  # Comprimir dados maiores que 10 bytes
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',  # Compressão para imagens
            }
        }
    }

    # Configurar Redis como backend de sessão para produção
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

else:
    # Manter a configuração atual de DatabaseCache para desenvolvimento
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 600,  # 10 minutos
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 2,
            }
        },
        'books_search': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 60 * 60 * 2,  # 2 horas
            'OPTIONS': {
                'MAX_ENTRIES': 500,
                'CULL_FREQUENCY': 3,
            }
        },
        'books_recommendations': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 60 * 60 * 24,  # 24 horas
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        },
        'google_books': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 60 * 60 * 24,  # 24 horas
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        },
        'recommendations': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 60 * 60,  # 1 hora
            'OPTIONS': {
                'MAX_ENTRIES': 500,
                'CULL_FREQUENCY': 3,
            }
        },
        'image_proxy': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'TIMEOUT': 60 * 60 * 24 * 7,  # 7 dias
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

    # Manter configuração atual para desenvolvimento
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
    SESSION_CACHE_ALIAS = 'default'

# Configurações da API Google Books
GOOGLE_BOOKS_CACHE_TIMEOUT = 60 * 60 * 24  # 24 horas em segundos
GOOGLE_BOOKS_CACHE_KEY_PREFIX = 'google_books:'

# Novas configurações para o serviço centralizado
GOOGLE_BOOKS_SEARCH_CACHE_TIMEOUT = 60 * 60 * 2  # 2 horas
GOOGLE_BOOKS_RECOMMENDATIONS_CACHE_TIMEOUT = 60 * 60 * 24  # 24 horas

# API Key do Google Books
GOOGLE_BOOKS_API_KEY = env('GOOGLE_BOOKS_API_KEY', default='')

# Configuração de variáveis de ambiente sobre o tempo:
WEATHER_API_KEY = env('WEATHER_API_KEY', default='')

# Configurações de Autenticação
LOGIN_REDIRECT_URL = 'index'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'index'

# Configurações de Sessão
SESSION_COOKIE_AGE = 604800  # 1 semana em segundos
SESSION_COOKIE_SECURE = True  # Cookies apenas via HTTPS
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Sessão persiste após fechar navegador
CSRF_COOKIE_SECURE = False    # Set to True for HTTPS

# Logging simplificado
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Configurações adicionais de cache
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutos
CACHE_MIDDLEWARE_KEY_PREFIX = 'cgv_bookstore'

# Configuração de cache de templates em ambiente de produção
if not DEBUG:
    for template in TEMPLATES:
        if template['BACKEND'] == 'django.template.backends.django.DjangoTemplates':
            template['OPTIONS']['loaders'] = [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ]

# Usar ETag para habilitar cache no navegador
USE_ETAGS = True