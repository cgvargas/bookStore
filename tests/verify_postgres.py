import os
import sys
import django
import psycopg2
from pathlib import Path

# Configurar ambiente Django
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.conf import settings
from django.db import connection

print("\n=== Verificação da Configuração do PostgreSQL ===\n")

# Verificar configuração do Django
print("1. Verificando configuração no Django:")
db_config = settings.DATABASES['default']
if 'postgresql' in db_config['ENGINE']:
    print("  ✓ Engine correto: PostgreSQL")
else:
    print(f"  ✗ Engine incorreto: {db_config['ENGINE']}")

print(f"  DB Name: {db_config['NAME']}")
print(f"  DB User: {db_config['USER']}")
print(f"  DB Host: {db_config['HOST']}")
print(f"  DB Port: {db_config['PORT']}")

# Testar conexão direta
print("\n2. Tentando conexão direta com PostgreSQL:")
try:
    # Conectar usando as configurações do Django
    conn = psycopg2.connect(
        dbname=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        host=db_config['HOST'],
        port=db_config['PORT']
    )
    conn.close()
    print("  ✓ Conexão direta com PostgreSQL bem-sucedida!")
except Exception as e:
    print(f"  ✗ Erro na conexão direta: {str(e)}")

# Testar usando o Django
print("\n3. Testando conexão via Django ORM:")
try:
    # Executar uma query simples
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  ✓ Versão do PostgreSQL: {version}")

        # Listar tabelas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        print(f"\n4. Tabelas encontradas ({len(tables)}):")
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\";")
            count = cursor.fetchone()[0]
            print(f"  {i}. {table_name}: {count} registros")

except Exception as e:
    print(f"  ✗ Erro ao testar via Django: {str(e)}")

print("\n=== Verificação Concluída ===")