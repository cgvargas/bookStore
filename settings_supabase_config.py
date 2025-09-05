# Configuracao de Banco de Dados Supabase
# Configuracao funcional: Host com DB Prefix
# Gerado em: 2025-07-22 18:22:08

import os
from decouple import config

# Database Configuration
DATABASES = {
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
    }
}

# Alternativa usando DATABASE_URL (mais simples)
# import dj_database_url
# DATABASES = {
#     'default': dj_database_url.config(
#         default=config('DATABASE_URL', default=''),
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
# }