import os
import sys
from pathlib import Path

# Configuração do caminho
BASE_DIR = Path(__file__).resolve().parent
ENV_DEV_PATH = os.path.join(BASE_DIR, '.env.dev')
ENV_PROD_PATH = os.path.join(BASE_DIR, '.env.prod')

# Conteúdo para o arquivo .env.dev
ENV_DEV_CONTENT = """# Django
SECRET_KEY=django-insecure-r%4)z4dffs_qqw8y$8g!om4h_0h$md^_y70+1q=w$xh=foy!uj
DEBUG=True
ALLOWED_HOSTS=*
DJANGO_ENV=development

# Configurações de E-mail - SendGrid
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.GrZm2LEaSUmLbEwdnQ6eBg._UAWXniDaQWYinXCMS6ILdRlD9oiZgXeI8dUm9NmgXU
DEFAULT_FROM_EMAIL=cg.bookstore.online@outlook.com
SERVER_EMAIL=cg.bookstore.online@outlook.com

# Logging
LOGGING_LEVEL=DEBUG

# Configurações do PostgreSQL
DB_NAME=cgbookstore_db
DB_USER=cgbookstore_user
DB_PASSWORD=senha_segura_aqui
DB_HOST=localhost
DB_PORT=5432

# Use SQLite em desenvolvimento (opcional)
USE_SQLITE=False

# API Google Books
GOOGLE_BOOKS_API_KEY=AIzaSyBF5W5NktgXZRfTnZXe3pVxqB_TCkXGzx0
"""

# Conteúdo para o arquivo .env.prod
ENV_PROD_CONTENT = """# Configurações gerais
DEBUG=False
SECRET_KEY=gere_uma_chave_secreta_robusta_para_producao
DJANGO_ENV=production

# Configurações do PostgreSQL
DB_NAME=cgbookstore_db_prod
DB_USER=cgbookstore_user_prod
DB_PASSWORD=senha_muito_segura_para_producao
DB_HOST=localhost
DB_PORT=5432

# Sempre usar PostgreSQL em produção
USE_SQLITE=False

# Configurações da API Google Books
GOOGLE_BOOKS_API_KEY=AIzaSyBF5W5NktgXZRfTnZXe3pVxqB_TCkXGzx0

# Configurações do SendGrid
SENDGRID_API_KEY=SG.GrZm2LEaSUmLbEwdnQ6eBg._UAWXniDaQWYinXCMS6ILdRlD9oiZgXeI8dUm9NmgXU
DEFAULT_FROM_EMAIL=cg.bookstore.online@outlook.com
"""

# Verificar e criar/atualizar .env.dev
if os.path.exists(ENV_DEV_PATH):
    backup_dev_path = f"{ENV_DEV_PATH}.bak"
    print(f"Arquivo .env.dev já existe. Criando backup em: {backup_dev_path}")
    with open(ENV_DEV_PATH, 'r') as original:
        with open(backup_dev_path, 'w') as backup:
            backup.write(original.read())

    # Perguntar se deseja sobrescrever
    response = input("Deseja sobrescrever o arquivo .env.dev? (S/n): ").lower()
    if response != 'n':
        with open(ENV_DEV_PATH, 'w') as f:
            f.write(ENV_DEV_CONTENT)
        print("✓ Arquivo .env.dev atualizado.")
    else:
        print("Arquivo .env.dev mantido sem alterações.")
else:
    with open(ENV_DEV_PATH, 'w') as f:
        f.write(ENV_DEV_CONTENT)
    print("✓ Arquivo .env.dev criado.")

# Verificar e criar/atualizar .env.prod
if os.path.exists(ENV_PROD_PATH):
    backup_prod_path = f"{ENV_PROD_PATH}.bak"
    print(f"Arquivo .env.prod já existe. Criando backup em: {backup_prod_path}")
    with open(ENV_PROD_PATH, 'r') as original:
        with open(backup_prod_path, 'w') as backup:
            backup.write(original.read())

    # Perguntar se deseja sobrescrever
    response = input("Deseja sobrescrever o arquivo .env.prod? (S/n): ").lower()
    if response != 'n':
        with open(ENV_PROD_PATH, 'w') as f:
            f.write(ENV_PROD_CONTENT)
        print("✓ Arquivo .env.prod atualizado.")
    else:
        print("Arquivo .env.prod mantido sem alterações.")
else:
    with open(ENV_PROD_PATH, 'w') as f:
        f.write(ENV_PROD_CONTENT)
    print("✓ Arquivo .env.prod criado.")

print("\nLEMBRETE: Certifique-se de atualizar as senhas nos arquivos .env")
print("Principalmente o valor de DB_PASSWORD com a senha que você definiu para o PostgreSQL")