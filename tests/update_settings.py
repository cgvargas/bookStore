import os
import re
import shutil
from pathlib import Path

# Configuração do caminho
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = os.path.join(BASE_DIR, 'cgbookstore', 'config', 'settings.py')

# Verificar se o arquivo existe
if not os.path.exists(SETTINGS_PATH):
    print(f"Arquivo settings.py não encontrado em: {SETTINGS_PATH}")
    print("Por favor, verifique o caminho e tente novamente.")
    exit(1)

print(f"Atualizando configurações em: {SETTINGS_PATH}")

# Criar backup do arquivo original
backup_path = f"{SETTINGS_PATH}.bak"
shutil.copy2(SETTINGS_PATH, backup_path)
print(f"Backup criado em: {backup_path}")

# Ler o conteúdo do arquivo
with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Padrão para encontrar a configuração do banco de dados
db_pattern = r'DATABASES\s*=\s*\{.*?\'default\'.*?\}.*?\}'
db_pattern = re.compile(db_pattern, re.DOTALL)

# Nova configuração de banco de dados
new_db_config = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='cgbookstore_db'),
        'USER': env('DB_USER', default='cgbookstore_user'),
        'PASSWORD': env('DB_PASSWORD', default='senha_segura_aqui'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'connect_timeout': 30,
        },
        'CONN_MAX_AGE': 600,  # 10 minutos
        'ATOMIC_REQUESTS': True,  # Cada solicitação HTTP ocorre em uma transação
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
"""

# Substituir a configuração
if db_pattern.search(content):
    new_content = db_pattern.sub(new_db_config, content)

    # Salvar as alterações
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✓ Configuração do banco de dados atualizada com sucesso!")
else:
    print("✗ Não foi possível encontrar a configuração do banco de dados.")
    print("Verifique o arquivo manualmente e faça as alterações necessárias.")