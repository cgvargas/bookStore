import os
import sys
import json
import psycopg2
import psycopg2.extras
from pathlib import Path

# Configuração do caminho
BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = os.path.join(BASE_DIR, 'data_exports')

# Configurações PostgreSQL (ajuste conforme necessário)
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB = 'cgbookstore_db'
PG_USER = 'cgbookstore_user'
PG_PASS = 'senha_segura_aqui'  # Substitua pela sua senha

print("Importando dados para o PostgreSQL...")
print(f"Diretório de origem: {EXPORT_DIR}")

# Verificar arquivos JSON disponíveis
json_files = [f for f in os.listdir(EXPORT_DIR) if f.endswith('.json')]
if not json_files:
    print("Nenhum arquivo JSON encontrado no diretório de exportação.")
    sys.exit(1)

print(f"Arquivos encontrados: {len(json_files)}")

try:
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )
    cursor = conn.cursor()

    print("Conexão com PostgreSQL estabelecida.")

    # Para cada arquivo JSON
    for json_file in json_files:
        table_name = json_file.replace('.json', '')
        file_path = os.path.join(EXPORT_DIR, json_file)

        print(f"Processando tabela: {table_name}")

        try:
            # Carregar dados do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                print(f"  Sem dados para importar em {table_name}")
                continue

            # Verificar se há registros
            if len(data) == 0:
                print(f"  Arquivo vazio: {json_file}")
                continue

            # Obter colunas da primeira linha
            columns = list(data[0].keys())
            if not columns:
                print(f"  Sem colunas em {table_name}")
                continue

            print(f"  Importando {len(data)} registros para '{table_name}'")

            # Limpar tabela existente
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")

            # Inserir dados
            for row in data:
                # Criar placeholders para os valores
                placeholders = ', '.join(['%s'] * len(row))
                # Criar a query de inserção
                columns_str = ', '.join([f'"{col}"' for col in row.keys()])
                query = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})'

                # Executar a query
                cursor.execute(query, list(row.values()))

            conn.commit()
            print(f"  ✓ Dados importados com sucesso para {table_name}")

        except Exception as e:
            conn.rollback()
            print(f"  ✗ Erro ao importar {table_name}: {str(e)}")

    print("\nImportação concluída!")

except Exception as e:
    print(f"Erro ao conectar ao PostgreSQL: {str(e)}")
finally:
    if 'conn' in locals() and conn:
        conn.close()