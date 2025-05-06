import os
import psycopg2

# Configurações PostgreSQL
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB = 'cgbookstore_db'
PG_USER = 'cgbookstore_user'
PG_PASS = 'senha_segura_aqui'  # Ajuste para sua senha

print("Verificando tabelas no PostgreSQL...")

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

    # Listar todas as tabelas no esquema 'public'
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"Encontradas {len(tables)} tabelas:")

    for i, (table_name,) in enumerate(tables, 1):
        print(f"{i}. {table_name}")

        # Verificar a estrutura da tabela
        try:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()
            print(f"   Colunas ({len(columns)}):")

            for col_name, data_type, is_nullable in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"   - {col_name} ({data_type}, {nullable})")

            print()
        except Exception as e:
            print(f"   Erro ao obter colunas: {str(e)}")

    # Buscar especificamente tabelas para usuários e livros
    print("\nBuscando tabelas específicas:")

    for pattern in ['user', 'book']:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' AND table_name LIKE %s
            ORDER BY table_name;
        """, (f'%{pattern}%',))

        tables = cursor.fetchall()
        print(f"Tabelas relacionadas a '{pattern}': {[t[0] for t in tables]}")

except Exception as e:
    print(f"Erro ao conectar ao PostgreSQL: {str(e)}")
finally:
    if 'conn' in locals() and conn:
        conn.close()