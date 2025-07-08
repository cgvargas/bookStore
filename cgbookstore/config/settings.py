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
    #'django_extensions',
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
            os.path.join(BASE_DIR, 'templates'), # Mantenha para templates globais do projeto
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
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/0',
            'TIMEOUT': 600,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'default',
        },
        'books_search': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'TIMEOUT': 60 * 60 * 2,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 500,
            },
            'KEY_PREFIX': 'books_search',
        },
        'recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'TIMEOUT': 60 * 60 * 6,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'recommendations',
        },
        'books_recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'TIMEOUT': 60 * 60 * 6,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'books_recommendations',
        },
        'google_books': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',
            'TIMEOUT': 60 * 60 * 24 * 7,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 2000,
            },
            'KEY_PREFIX': 'google_books',
        },
        'image_proxy': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/4',
            'TIMEOUT': 60 * 60 * 24 * 14,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 5000,
                'COMPRESS_MIN_LEN': 10,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            },
            'KEY_PREFIX': 'image_proxy',
        },
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

else:
    # Configuração Redis local via Docker para desenvolvimento
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/0',
            'TIMEOUT': 600,  # 10 minutos
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'default',

        },
        'books_search': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'TIMEOUT': 60 * 60 * 2,  # 2 horas
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 500,
            },
            'KEY_PREFIX': 'books_search',
        },

        'recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'TIMEOUT': 60 * 60 * 6,  # 6 horas
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'recommendations',

        },
        'books_recommendations': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',  # Mesmo DB do recommendations
            'TIMEOUT': 60 * 60 * 6,  # 6 horas
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000,
            },
            'KEY_PREFIX': 'books_recommendations',

        },
        'google_books': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',
            'TIMEOUT': 60 * 60 * 24 * 7,  # 7 dias
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 2000,
            },
            'KEY_PREFIX': 'google_books',

        },
        'image_proxy': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://127.0.0.1:6379/4',
            'TIMEOUT': 60 * 60 * 24 * 14,  # 14 dias (alterado de 7 para 14 dias)
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 5000,
                'COMPRESS_MIN_LEN': 10,  # Comprimir dados maiores que 10 bytes
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',  # Compressão para imagens
            },
            'KEY_PREFIX': 'image_proxy',

        },
        'weather': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://127.0.0.1:6379/5',  # Uso do banco de dados Redis 5
            'TIMEOUT': 60 * 30,  # 30 minutos (os dados meteorológicos mudam constantemente)
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 500,  # Não precisa ser grande, só armazena algumas cidades
            },
            'KEY_PREFIX': 'weather',

        }
    }

    # Configurar Redis como backend de sessão para desenvolvimento
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

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
            template['APP_DIRS'] = False  # ← ADICIONE ESTA LINHA
            template['OPTIONS']['loaders'] = [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ]

# Usar ETag para habilitar cache no navegador
USE_ETAGS = True

# ===== CONFIGURAÇÕES OLLAMA PARA CHATBOT LITERÁRIO =====
# Adicionar ao final do arquivo settings.py

# Configurações do Ollama AI Service
OLLAMA_CONFIG = {
    # Habilitação do serviço
    'enabled': env.bool('OLLAMA_ENABLED', default=True),

    # Configurações de conexão
    'base_url': env('OLLAMA_BASE_URL', default='http://localhost:11434'),
    'timeout': env.int('OLLAMA_TIMEOUT', default=30),
    'max_retries': env.int('OLLAMA_MAX_RETRIES', default=3),

    # Configurações do modelo
    'model': env('OLLAMA_MODEL', default='llama3.2:3b'),
    'temperature': env.float('OLLAMA_TEMPERATURE', default=0.7),
    'max_tokens': env.int('OLLAMA_MAX_TOKENS', default=500),

    # Configurações de fallback
    'fallback_enabled': env.bool('OLLAMA_FALLBACK_ENABLED', default=True),
    'auto_download_model': env.bool('OLLAMA_AUTO_DOWNLOAD', default=True),

    # Configurações de cache
    'cache_responses': env.bool('OLLAMA_CACHE_RESPONSES', default=False),
    'cache_timeout': env.int('OLLAMA_CACHE_TIMEOUT', default=1800),  # 30 minutos
}

# Template de prompt do sistema para literatura
OLLAMA_SYSTEM_PROMPT = """Você é um assistente literário especializado da CG.BookStore.Online.

CONTEXTO DA CONVERSA:
{context_info}

SUAS ESPECIALIDADES:
- Literatura brasileira e internacional
- Recomendações de livros personalizadas
- Informações sobre autores e obras
- Navegação e funcionalidades do site
- Sugestões de leitura baseadas em preferências

DIRETRIZES DE RESPOSTA:
- Use linguagem natural, amigável e acessível
- Seja preciso e útil nas informações sobre livros
- Se não souber algo específico, seja honesto e ofereça alternativas
- Mantenha respostas concisas (máximo 3 parágrafos)
- Foque em aspectos literários relevantes
- Incentive a descoberta de novos livros e autores

PERGUNTA DO USUÁRIO: {user_question}

Responda de forma útil e contextual:"""

# Configurações de logging específicas para IA
LOGGING_CONFIG_OLLAMA = {
    'ollama_service': {
        'handlers': ['console'],
        'level': env('OLLAMA_LOG_LEVEL', default='INFO'),
        'propagate': False,
    },
    'chatbot_ai': {
        'handlers': ['console'],
        'level': env('CHATBOT_AI_LOG_LEVEL', default='DEBUG'),
        'propagate': False,
    }
}

# Integrar configurações de logging do Ollama ao LOGGING existente
if 'LOGGING' in locals() or 'LOGGING' in globals():
    LOGGING['loggers'].update(LOGGING_CONFIG_OLLAMA)
else:
    LOGGING['loggers'] = LOGGING_CONFIG_OLLAMA

# Configurações de integração com chatbot existente
CHATBOT_AI_INTEGRATION = {
    # Quando usar IA como fallback
    'use_ai_fallback': env.bool('CHATBOT_USE_AI_FALLBACK', default=True),

    # Threshold de confiança para usar IA
    'ai_fallback_threshold': env.float('CHATBOT_AI_THRESHOLD', default=0.5),

    # Prioridade: 'local_first' ou 'ai_first' ou 'hybrid'
    'response_strategy': env('CHATBOT_RESPONSE_STRATEGY', default='local_first'),

    # Usar IA para melhorar respostas de baixa qualidade
    'enhance_with_ai': env.bool('CHATBOT_ENHANCE_WITH_AI', default=True),

    # Timeout específico para integração
    'integration_timeout': env.int('CHATBOT_AI_INTEGRATION_TIMEOUT', default=25),
}

# Cache específico para respostas da IA (se usar cache)
if env.bool('OLLAMA_CACHE_RESPONSES', default=False):
    CACHES['ollama_responses'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://127.0.0.1:6379/6',
        'TIMEOUT': OLLAMA_CONFIG['cache_timeout'],
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': 1000,
            'COMPRESS_MIN_LEN': 100,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'ollama_ai',
    }

# Configurações de monitoramento e estatísticas
AI_MONITORING = {
    'enable_stats': env.bool('AI_ENABLE_STATS', default=True),
    'stats_retention_days': env.int('AI_STATS_RETENTION', default=30),
    'alert_on_high_failure_rate': env.bool('AI_ALERT_FAILURES', default=True),
    'failure_rate_threshold': env.float('AI_FAILURE_THRESHOLD', default=0.3),  # 30%
}

# Configurações de desenvolvimento vs produção
if DJANGO_ENV == 'development':
    # Configurações mais relaxadas para desenvolvimento
    OLLAMA_CONFIG.update({
        'timeout': 90,  # Timeout maior para desenvolvimento
        'auto_download_model': True,  # Auto-download habilitado
        'fallback_enabled': True,  # Sempre usar fallback
    })

    CHATBOT_AI_INTEGRATION.update({
        'ai_fallback_threshold': 0.3,  # Threshold menor para testar IA mais
        'enhance_with_ai': True,  # Sempre tentar melhorar com IA
    })

else:
    # Configurações otimizadas para produção
    OLLAMA_CONFIG.update({
        'timeout': 20,  # Timeout menor para produção
        'auto_download_model': False,  # Não baixar automaticamente em produção
        'cache_responses': True,  # Cache habilitado em produção
    })

    CHATBOT_AI_INTEGRATION.update({
        'ai_fallback_threshold': 0.5,  # Threshold padrão
        'integration_timeout': 15,  # Timeout menor para produção
    })

# Configurações de segurança para IA
AI_SECURITY = {
    'max_prompt_length': env.int('AI_MAX_PROMPT_LENGTH', default=2000),
    'max_response_length': env.int('AI_MAX_RESPONSE_LENGTH', default=1500),
    'filter_sensitive_content': env.bool('AI_FILTER_CONTENT', default=True),
    'rate_limit_per_user': env.int('AI_RATE_LIMIT', default=20),  # requests per minute
    'rate_limit_window': env.int('AI_RATE_WINDOW', default=60),  # seconds
}

# Configurações avançadas (opcional)
OLLAMA_ADVANCED = {
    # Configurações do modelo
    'model_options': {
        'num_ctx': env.int('OLLAMA_CONTEXT_LENGTH', default=2048),
        'repeat_penalty': env.float('OLLAMA_REPEAT_PENALTY', default=1.1),
        'top_k': env.int('OLLAMA_TOP_K', default=40),
        'top_p': env.float('OLLAMA_TOP_P', default=0.9),
    },

    # Configurações de sistema
    'system_settings': {
        'num_thread': env.int('OLLAMA_THREADS', default=4),
        'numa': env.bool('OLLAMA_NUMA', default=False),
    },

    # Configurações de monitoramento
    'monitoring': {
        'log_requests': env.bool('OLLAMA_LOG_REQUESTS', default=DEBUG),
        'log_responses': env.bool('OLLAMA_LOG_RESPONSES', default=DEBUG),
        'track_tokens': env.bool('OLLAMA_TRACK_TOKENS', default=True),
    }
}