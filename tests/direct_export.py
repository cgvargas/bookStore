import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

# Configuração do caminho
BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = os.path.join(BASE_DIR, 'cgbookstore', 'db.sqlite3')
EXPORT_DIR = os.path.join(BASE_DIR, 'data_exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

print(f"Exportando dados do SQLite: {SQLITE_PATH}")
print(f"Diretório de exportação: {EXPORT_DIR}")

# Conectar ao banco SQLite
conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Obter todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
table_names = [table['name'] for table in tables]

print(f"Tabelas encontradas: {len(table_names)}")

# Dados para exportação final
all_data = []


# Função para serializar tipos especiais
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Tipo não serializável: {type(obj)}")


# Exportar cada tabela
for table_name in table_names:
    if table_name.startswith('sqlite_') or table_name.startswith('django_'):
        continue

    print(f"Exportando tabela: {table_name}")
    cursor.execute(f"SELECT * FROM '{table_name}';")
    rows = cursor.fetchall()

    if not rows:
        print(f"  Sem dados na tabela {table_name}")
        continue

    # Converter para lista de dicionários
    table_data = []
    for row in rows:
        row_dict = {key: row[key] for key in row.keys()}
        table_data.append(row_dict)

    # Salvar dados da tabela em arquivo
    table_file = os.path.join(EXPORT_DIR, f"{table_name}.json")
    with open(table_file, 'w', encoding='utf-8', errors='replace') as f:
        json.dump(table_data, f, default=json_serial, ensure_ascii=False, indent=2)

    print(f"  ✓ Exportados {len(table_data)} registros para {table_file}")

conn.close()
print("Exportação direta concluída!")