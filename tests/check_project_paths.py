import os
import sys
from pathlib import Path

# Obter o diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent
print(f"Diretório base do projeto: {BASE_DIR}")

# Verificar se o módulo config existe
config_path = os.path.join(BASE_DIR, 'config')
cgbookstore_config_path = os.path.join(BASE_DIR, 'cgbookstore', 'config')

if os.path.exists(config_path):
    print(f"✓ Módulo 'config' encontrado em: {config_path}")
    print("  Caminho do módulo para settings: 'config.settings'")
elif os.path.exists(cgbookstore_config_path):
    print(f"✓ Módulo 'config' encontrado em: {cgbookstore_config_path}")
    print("  Caminho do módulo para settings: 'cgbookstore.config.settings'")
else:
    print("✗ Módulo 'config' não encontrado nas localizações padrão.")
    print("  Procurando arquivo settings.py em todo o projeto...")

    # Procurar o arquivo settings.py
    settings_found = False
    for root, dirs, files in os.walk(BASE_DIR):
        if 'settings.py' in files:
            settings_path = os.path.join(root, 'settings.py')
            relative_path = os.path.relpath(settings_path, BASE_DIR)
            module_path = relative_path.replace(os.path.sep, '.').replace('.py', '')
            print(f"✓ Arquivo settings.py encontrado em: {settings_path}")
            print(f"  Caminho do módulo sugerido: '{module_path}'")
            settings_found = True

    if not settings_found:
        print("✗ Arquivo settings.py não encontrado em nenhum diretório.")

# Verificar localização do manage.py
manage_path = os.path.join(BASE_DIR, 'manage.py')
if os.path.exists(manage_path):
    print(f"✓ Arquivo manage.py encontrado em: {manage_path}")
else:
    print("✗ Arquivo manage.py não encontrado na raiz do projeto.")
    # Procurar manage.py
    for root, dirs, files in os.walk(BASE_DIR):
        if 'manage.py' in files:
            print(f"✓ Arquivo manage.py encontrado em: {os.path.join(root, 'manage.py')}")
            break
    else:
        print("✗ Arquivo manage.py não encontrado em nenhum diretório.")

# Verificar localização do db.sqlite3
sqlite_path = os.path.join(BASE_DIR, 'db.sqlite3')
cgbookstore_sqlite_path = os.path.join(BASE_DIR, 'cgbookstore', 'db.sqlite3')

if os.path.exists(sqlite_path):
    print(f"✓ Arquivo db.sqlite3 encontrado em: {sqlite_path}")
elif os.path.exists(cgbookstore_sqlite_path):
    print(f"✓ Arquivo db.sqlite3 encontrado em: {cgbookstore_sqlite_path}")
else:
    print("✗ Arquivo db.sqlite3 não encontrado nas localizações padrão.")
    for root, dirs, files in os.walk(BASE_DIR):
        if 'db.sqlite3' in files:
            print(f"✓ Arquivo db.sqlite3 encontrado em: {os.path.join(root, 'db.sqlite3')}")
            break
    else:
        print("✗ Arquivo db.sqlite3 não encontrado em nenhum diretório.")

# Verificar estrutura do módulo cgbookstore
cgbookstore_path = os.path.join(BASE_DIR, 'cgbookstore')
if os.path.exists(cgbookstore_path) and os.path.isdir(cgbookstore_path):
    print(f"✓ Módulo 'cgbookstore' encontrado em: {cgbookstore_path}")
    apps_dir = os.path.join(cgbookstore_path, 'apps')
    if os.path.exists(apps_dir) and os.path.isdir(apps_dir):
        print(f"✓ Diretório 'apps' encontrado em: {apps_dir}")
else:
    print("✗ Módulo 'cgbookstore' não encontrado na raiz do projeto.")

print("\nDICAS:")
print("- Todos os scripts devem usar o mesmo caminho para o módulo de settings")
print("- Verifique se você está executando os scripts a partir do diretório correto")
print("- Para iniciar o Django, use: os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CAMINHO_CORRETO.settings')")