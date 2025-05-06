import os
import json
import re
from pathlib import Path

# Diretório dos arquivos exportados
project_dir = Path(__file__).resolve().parent
export_dir = project_dir / 'data_exports'
fixed_dir = project_dir / 'data_exports_fixed'

# Criar diretório para os arquivos corrigidos
os.makedirs(fixed_dir, exist_ok=True)

print(f"Processando arquivos em: {export_dir}")
print(f"Salvando arquivos corrigidos em: {fixed_dir}")

# Ordem de importação para respeitar dependências de chave estrangeira
import_order = [
    'django_content_type',
    'auth_permission',
    'auth_group',
    'core_user',  # Tabela de usuários
    'user',
    'core_profile',
    'core_book',
    'core_userbookshelf',
    'core_banner',
    'core_defaultshelftype',
    'core_homesection',
    'core_videoitem',
    'core_videosection',
    'core_videosectionitem',
]

# Mapeamento de correções para campos booleanos
boolean_fields = {
    'core_banner': ['ativo'],
    'core_book': ['adaptado_filme', 'e_destaque', 'e_lancamento', 'em_promocao'],
    'core_defaultshelftype': ['ativo'],
    'core_homesection': ['ativo'],
    'core_videoitem': ['ativo'],
    'core_videosection': ['ativo'],
    'core_videosectionitem': ['ativo'],
}


# Função para converter valores de inteiros para booleanos
def fix_boolean_value(value):
    if isinstance(value, int):
        return value == 1
    elif isinstance(value, str) and value.isdigit():
        return value == '1'
    elif isinstance(value, str) and value.lower() == 'true':
        return True
    elif isinstance(value, str) and value.lower() == 'false':
        return False
    return value


# Função para converter nomes de tabelas
def get_table_name(filename):
    # Remover a extensão .json
    base_name = os.path.splitext(filename)[0]

    # Tratamento especial para a tabela de usuários
    if base_name == 'user' or base_name == 'user_user_permissions':
        return 'core_user' if base_name == 'user' else 'core_user_user_permissions'

    return base_name


# Processar cada arquivo no diretório
files = [f for f in os.listdir(export_dir) if f.endswith('.json')]
for filename in files:
    file_path = os.path.join(export_dir, filename)
    fixed_file_path = os.path.join(fixed_dir, filename)

    # Obter nome da tabela
    table_name = get_table_name(filename)

    print(f"Processando {filename} (tabela: {table_name})...")

    try:
        # Carregar dados do arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"  ✗ Erro ao decodificar JSON em {filename}")
                continue

        if not data:
            print(f"  ⚠ Arquivo vazio: {filename}")
            continue

        # Corrigir valores booleanos
        if table_name in boolean_fields:
            print(f"  Corrigindo campos booleanos: {boolean_fields[table_name]}")
            for item in data:
                for field in boolean_fields[table_name]:
                    if field in item:
                        item[field] = fix_boolean_value(item[field])

        # Salvar arquivo corrigido
        with open(fixed_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Arquivo corrigido salvo: {fixed_file_path}")

    except Exception as e:
        print(f"  ✗ Erro ao processar {filename}: {str(e)}")

# Criar script para importação ordenada
import_script_path = os.path.join(project_dir, 'ordered_import.py')
with open(import_script_path, 'w', encoding='utf-8') as f:
    f.write("""
import os
import sys
import json
import psycopg2
import psycopg2.extras
from pathlib import Path

# Configuração do caminho
BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = os.path.join(BASE_DIR, 'data_exports_fixed')

# Configurações PostgreSQL (ajuste conforme necessário)
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB = 'cgbookstore_db'
PG_USER = 'cgbookstore_user'
PG_PASS = 'senha_segura_aqui'  # Ajuste para sua senha

print("Importando dados para o PostgreSQL...")
print(f"Diretório de origem: {EXPORT_DIR}")

# Ordem de importação para respeitar dependências
import_order = [
    'django_content_type',
    'auth_permission',
    'auth_group',
    'core_user',
    'core_profile',
    'core_book',
    'core_userbookshelf',
    'core_banner',
    'core_defaultshelftype',
    'core_homesection',
    'core_videoitem',
    'core_videosection',
    'core_videosectionitem',
]

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

    # Desativar triggers temporariamente
    cursor.execute("SET session_replication_role = 'replica';")

    # Importar na ordem correta
    for table_name in import_order:
        file_path = os.path.join(EXPORT_DIR, f"{table_name}.json")

        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado para tabela {table_name}, pulando...")
            continue

        print(f"Processando tabela: {table_name}")

        try:
            # Carregar dados do arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                print(f"  Sem dados para importar em {table_name}")
                continue

            print(f"  Importando {len(data)} registros para '{table_name}'")

            # Limpar tabela existente
            try:
                cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
            except Exception as e:
                print(f"  ⚠ Não foi possível limpar a tabela: {str(e)}")
                conn.rollback()

            # Inserir dados
            for row in data:
                # Criar placeholders para os valores
                placeholders = ', '.join(['%s'] * len(row))
                # Criar a query de inserção
                columns_str = ', '.join([f'"{col}"' for col in row.keys()])
                query = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})'

                try:
                    # Executar a query
                    cursor.execute(query, list(row.values()))
                except Exception as e:
                    print(f"  ⚠ Erro ao inserir registro: {str(e)}")
                    conn.rollback()

            conn.commit()
            print(f"  ✓ Dados importados com sucesso para {table_name}")

        except Exception as e:
            conn.rollback()
            print(f"  ✗ Erro ao importar {table_name}: {str(e)}")

    # Reativar triggers
    cursor.execute("SET session_replication_role = 'default';")

    print("\\nImportação concluída!")

except Exception as e:
    print(f"Erro ao conectar ao PostgreSQL: {str(e)}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
""")

print(f"\nScript de importação ordenada criado: {import_script_path}")
print("Execute o script com o comando:")
print("python ordered_import.py")