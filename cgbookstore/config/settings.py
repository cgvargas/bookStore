# Django settings for config project.
import os
from pathlib import Path
import environ
import dj_database_url
import logging

from django.urls import reverse_lazy

logger = logging.getLogger(__name__)

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
    'storages',
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

# ==============================================================================
# SEÇÃO DE BANCO DE DADOS
# ==============================================================================

DATABASES = {
    'default': env.db_url('DATABASE_URL')
}

DATABASES['default']['OPTIONS'] = DATABASES['default'].get('OPTIONS', {})
DATABASES['default']['OPTIONS']['sslmode'] = 'require'

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
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# ==============================================================================
# CONFIGURAÇÃO DE MÍDIA E ARMAZENAMENTO
# ==============================================================================

# Por padrão, usa armazenamento local
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

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
            'TIMEOUT': 60 * 60 * 24 * 14,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 5000,
                'COMPRESS_MIN_LEN': 10,  # Comprimir dados maiores que 10 bytes
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',  # Compressão para imagens
            },
            'KEY_PREFIX': 'image_proxy',

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

# Configurações de Autenticação
LOGIN_REDIRECT_URL = reverse_lazy('core:index')
LOGIN_URL = 'core:login'
LOGOUT_REDIRECT_URL = 'core:index'

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

# ===== CONFIGURAÇÕES OLLAMA PARA CHATBOT LITERÁRIO COM GPT-OSS =====
# Substituir a seção existente no final do arquivo settings.py

# Configurações do Ollama AI Service com GPT-OSS
OLLAMA_CONFIG = {
    # Habilitação do serviço
    'enabled': env.bool('OLLAMA_ENABLED', default=True),

    # Configurações de conexão
    'base_url': env('OLLAMA_BASE_URL', default='http://localhost:11434'),
    'timeout': env.int('OLLAMA_TIMEOUT', default=90),
    'max_retries': env.int('OLLAMA_MAX_RETRIES', default=3),

    # ✅ MODELO ATUALIZADO PARA LLAMA 3.2
    'model': env('OLLAMA_MODEL', default='llama3.2:3b'),
    'temperature': env.float('OLLAMA_TEMPERATURE', default=0.7),
    'max_tokens': env.int('OLLAMA_MAX_TOKENS', default=2048),

    # Configurações de fallback
    'fallback_enabled': env.bool('OLLAMA_FALLBACK_ENABLED', default=True),
    'auto_download_model': env.bool('OLLAMA_AUTO_DOWNLOAD', default=True),

    # Configurações de cache
    'cache_responses': env.bool('OLLAMA_CACHE_RESPONSES', default=True),
    'cache_timeout': env.int('OLLAMA_CACHE_TIMEOUT', default=3600),
}

# Configurações específicas do GPT-OSS
GPT_OSS_CONFIG = {
    # Configurações de raciocínio
    'reasoning_effort': env('GPT_OSS_REASONING_EFFORT', default='medium'),
    'show_reasoning': env.bool('GPT_OSS_SHOW_REASONING', default=False),
    'use_chain_of_thought': env.bool('GPT_OSS_USE_COT', default=True),

    # Configurações avançadas do modelo
    'context_length': env.int('GPT_OSS_CONTEXT_LENGTH', default=8192),
    'repeat_penalty': env.float('GPT_OSS_REPEAT_PENALTY', default=1.1),
    'top_k': env.int('GPT_OSS_TOP_K', default=40),
    'top_p': env.float('GPT_OSS_TOP_P', default=0.9),

    # ✅ TIMEOUTS AJUSTADOS PARA LLAMA 3.2:3B
    'timeout_simple': env.int('GPT_OSS_TIMEOUT_SIMPLE', default=30),
    'timeout_reasoning': env.int('GPT_OSS_TIMEOUT_REASONING', default=60),
    'timeout_analysis': env.int('GPT_OSS_TIMEOUT_ANALYSIS', default=90),
    'timeout_complex': env.int('GPT_OSS_TIMEOUT_COMPLEX', default=120),

    # Configurações de performance
    'enable_moe_optimization': env.bool('GPT_OSS_MOE_OPTIMIZATION', default=True),
    'active_parameters_target': env.int('GPT_OSS_ACTIVE_PARAMS', default=3600000000),
}

# Template de prompt do sistema otimizado para GPT-OSS
OLLAMA_SYSTEM_PROMPT = """Você é um assistente literário especializado da CG.BookStore.Online, utilizando o modelo GPT-OSS para análises profundas.

CONTEXTO DA CONVERSA:
{context_info}

SUAS ESPECIALIDADES:
- Literatura brasileira e internacional com análise crítica avançada
- Recomendações de livros baseadas em raciocínio estruturado
- Análises de estilo, tema, personagens e contexto histórico
- Informações detalhadas sobre autores e movimentos literários
- Navegação e funcionalidades do site com suporte inteligente
- Sugestões personalizadas usando chain-of-thought

DIRETRIZES DE RESPOSTA COM GPT-OSS:
- Use seu raciocínio step-by-step para análises complexas
- Seja preciso e fundamentado nas informações sobre livros
- Demonstre o processo de pensamento quando apropriado
- Mantenha respostas úteis e bem estruturadas
- Foque em aspectos literários relevantes com profundidade
- Use exemplos concretos e citações quando possível
- Adapte a complexidade ao nível do usuário

NÍVEL DE RACIOCÍNIO: {reasoning_effort}
MOSTRAR CADEIA DE PENSAMENTO: {show_reasoning}

PERGUNTA DO USUÁRIO: {user_question}

Responda utilizando suas capacidades avançadas de raciocínio:"""

# ===== EXTERNAL AI SERVICES =====
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
GROQ_MAX_TOKENS = int(os.getenv('GROQ_MAX_TOKENS', '1024'))

# HuggingFace API (Backup)
HF_API_KEY = os.getenv('HF_API_KEY', '')
HF_MODEL = os.getenv('HF_MODEL', 'microsoft/DialoGPT-large')

# Configurações de logging específicas para GPT-OSS
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
    },
    'gpt_oss': {
        'handlers': ['console'],
        'level': env('GPT_OSS_LOG_LEVEL', default='INFO'),
        'propagate': False,
    }
}

# Integrar configurações de logging do Ollama ao LOGGING existente
if 'LOGGING' in locals() or 'LOGGING' in globals():
    LOGGING['loggers'].update(LOGGING_CONFIG_OLLAMA)
else:
    LOGGING['loggers'] = LOGGING_CONFIG_OLLAMA

# Configurações de integração com chatbot existente (atualizadas para GPT-OSS)
CHATBOT_AI_INTEGRATION = {
    # Quando usar IA como fallback
    'use_ai_fallback': env.bool('CHATBOT_USE_AI_FALLBACK', default=True),

    # Threshold de confiança para usar IA (ajustado para GPT-OSS)
    'ai_fallback_threshold': env.float('CHATBOT_AI_THRESHOLD', default=0.4),

    # Prioridade: 'local_first' ou 'ai_first' ou 'hybrid'
    'response_strategy': env('CHATBOT_RESPONSE_STRATEGY', default='hybrid'),

    # Usar IA para melhorar respostas de baixa qualidade
    'enhance_with_ai': env.bool('CHATBOT_ENHANCE_WITH_AI', default=True),

    # Timeout específico para integração (aumentado para GPT-OSS)
    'integration_timeout': env.int('CHATBOT_AI_INTEGRATION_TIMEOUT', default=120),

    # Configurações específicas para GPT-OSS
    'prefer_gpt_oss_for_analysis': env.bool('PREFER_GPT_OSS_ANALYSIS', default=True),
    'gpt_oss_reasoning_threshold': env.float('GPT_OSS_REASONING_THRESHOLD', default=0.6),
}

# Cache específico para respostas da IA GPT-OSS
CACHES['gpt_oss_responses'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': f'redis://127.0.0.1:6379/7',
    'TIMEOUT': OLLAMA_CONFIG.get('cache_timeout', 3600),
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'MAX_ENTRIES': 2000,
        'COMPRESS_MIN_LEN': 200,
        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    },
    'KEY_PREFIX': 'gpt_oss',
}

# Cache para chain-of-thought e reasoning
CACHES['gpt_oss_reasoning'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': f'redis://127.0.0.1:6379/8',
    'TIMEOUT': 60 * 60 * 6,
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'MAX_ENTRIES': 1000,
        'COMPRESS_MIN_LEN': 500,
        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    },
    'KEY_PREFIX': 'gpt_oss_reasoning',
}

# Configurações de monitoramento e estatísticas (atualizadas)
AI_MONITORING = {
    'enable_stats': env.bool('AI_ENABLE_STATS', default=True),
    'stats_retention_days': env.int('AI_STATS_RETENTION', default=30),
    'alert_on_high_failure_rate': env.bool('AI_ALERT_FAILURES', default=True),
    'failure_rate_threshold': env.float('AI_FAILURE_THRESHOLD', default=0.2),

    # Monitoramento específico GPT-OSS
    'monitor_reasoning_performance': env.bool('MONITOR_GPT_OSS_REASONING', default=True),
    'reasoning_timeout_threshold': env.int('GPT_OSS_REASONING_TIMEOUT', default=30),
    'track_model_switches': env.bool('TRACK_MODEL_SWITCHES', default=True),
}

# Configurações de desenvolvimento vs produção (atualizadas para GPT-OSS)
if DJANGO_ENV == 'development':
    # Configurações mais relaxadas para desenvolvimento
    OLLAMA_CONFIG.update({
        'timeout': env.int('OLLAMA_TIMEOUT', 300),
        'auto_download_model': True,
        'fallback_enabled': True,
        'cache_responses': True,
    })

    GPT_OSS_CONFIG.update({
        'show_reasoning': False,
        'reasoning_effort': 'medium',
        'enable_literary_reasoning': True,
    })

    CHATBOT_AI_INTEGRATION.update({
        'ai_fallback_threshold': 0.3,
        'enhance_with_ai': True,
        'response_strategy': 'hybrid',
    })

else:
    # Configurações otimizadas para produção
    OLLAMA_CONFIG.update({
        'timeout': 60,
        'auto_download_model': False,
        'cache_responses': True,
        'cache_timeout': 7200,
    })

    GPT_OSS_CONFIG.update({
        'show_reasoning': False,
        'reasoning_effort': 'medium',
        'enable_moe_optimization': True,
    })

    CHATBOT_AI_INTEGRATION.update({
        'ai_fallback_threshold': 0.4,
        'integration_timeout': 120,
        'response_strategy': 'local_first',
    })

# Configurações de segurança para IA (atualizadas para GPT-OSS)
AI_SECURITY = {
    'max_prompt_length': env.int('AI_MAX_PROMPT_LENGTH', default=4000),
    'max_response_length': env.int('AI_MAX_RESPONSE_LENGTH', default=3000),
    'max_reasoning_length': env.int('AI_MAX_REASONING_LENGTH', default=2000),
    'filter_sensitive_content': env.bool('AI_FILTER_CONTENT', default=True),
    'rate_limit_per_user': env.int('AI_RATE_LIMIT', default=15),
    'rate_limit_window': env.int('AI_RATE_WINDOW', default=60),

    # Segurança específica GPT-OSS
    'validate_reasoning_output': env.bool('VALIDATE_GPT_OSS_REASONING', default=True),
    'sanitize_chain_of_thought': env.bool('SANITIZE_COT', default=True),
}

# Aliases para compatibilidade com código existente
OLLAMA_MODEL = OLLAMA_CONFIG['model']
OLLAMA_BASE_URL = OLLAMA_CONFIG['base_url']
OLLAMA_TIMEOUT = OLLAMA_CONFIG['timeout']
OLLAMA_TEMPERATURE = OLLAMA_CONFIG['temperature']
OLLAMA_MAX_TOKENS = OLLAMA_CONFIG['max_tokens']

# Configurações consolidadas para facilitar acesso
AI_CONFIG = {
    'ollama': OLLAMA_CONFIG,
    'gpt_oss': GPT_OSS_CONFIG,
    'integration': CHATBOT_AI_INTEGRATION,
    'security': AI_SECURITY,
    'monitoring': AI_MONITORING,
}


# Validação de configurações críticas
def validate_gpt_oss_config():
    """Valida se as configurações do GPT-OSS estão corretas."""
    import logging
    logger = logging.getLogger(__name__)

    required_settings = [
        'OLLAMA_BASE_URL',
        'OLLAMA_MODEL',
        'GPT_OSS_REASONING_EFFORT'
    ]

    missing_settings = []
    for setting in required_settings:
        if not env(setting, default=None):
            missing_settings.append(setting)

    if missing_settings:
        logger.warning(f"Configurações GPT-OSS ausentes: {missing_settings}")

    return len(missing_settings) == 0


# Executar validação em desenvolvimento
if DJANGO_ENV == 'development':
    validate_gpt_oss_config()

# ==============================================================================
# CONFIGURAÇÃO DE ARMAZENAMENTO DE MÍDIA - VERSÃO FINAL CORRIGIDA
# ==============================================================================
# Apenas para ambientes de produção (ou sempre que não estiver usando SQLite local)
if not DEBUG:
    AWS_ACCESS_KEY_ID = env('SUPABASE_SERVICE_ROLE_KEY')
    AWS_SECRET_ACCESS_KEY = env('SUPABASE_SERVICE_ROLE_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL')
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_LOCATION = 'media'
    AWS_DEFAULT_ACL = 'public-read'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_LOCATION}/'
# ==============================================================================