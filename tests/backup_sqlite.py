import os
import shutil
import datetime
from pathlib import Path

# Obter o diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent

# Possíveis locais do arquivo SQLite
sqlite_locations = [
    os.path.join(BASE_DIR, 'db.sqlite3'),
    os.path.join(BASE_DIR, 'cgbookstore', 'db.sqlite3'),
]

SQLITE_DB_PATH = None

# Verificar cada localização possível
for location in sqlite_locations:
    if os.path.exists(location):
        SQLITE_DB_PATH = location
        print(f"Arquivo de banco de dados encontrado em: {SQLITE_DB_PATH}")
        break

if not SQLITE_DB_PATH:
    print("Arquivo db.sqlite3 não encontrado nas localizações padrão.")
    print("Procurando em todo o projeto...")

    # Buscar recursivamente em todo o projeto
    for root, dirs, files in os.walk(BASE_DIR):
        if 'db.sqlite3' in files:
            SQLITE_DB_PATH = os.path.join(root, 'db.sqlite3')
            print(f"Arquivo de banco de dados encontrado em: {SQLITE_DB_PATH}")
            break

    if not SQLITE_DB_PATH:
        print("Arquivo db.sqlite3 não encontrado em nenhum diretório.")
        exit(1)

# Criar diretório de backup se não existir
BACKUP_DIR = os.path.join(BASE_DIR, 'backups', 'sqlite')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Gerar nome de arquivo com timestamp
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = f'db_backup_{timestamp}.sqlite3'
backup_path = os.path.join(BACKUP_DIR, backup_filename)

# Realizar o backup
try:
    shutil.copy2(SQLITE_DB_PATH, backup_path)
    print(f"Backup realizado com sucesso: {backup_path}")
except Exception as e:
    print(f"Erro ao realizar backup: {str(e)}")