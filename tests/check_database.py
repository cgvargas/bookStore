import os
import sys
import django
from pathlib import Path

# Configurar ambiente Django
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


def check_database():
    """Verifica a quantidade de registros em cada tabela principal"""
    from django.db import connection

    tables = [
        'user',
        'core_book',
        'core_profile',
        'core_banner',
        'core_defaultshelftype',
        'core_homesection',
        'core_videoitem',
        'core_videosection',
        'core_videosectionitem',
        'core_userbookshelf'
    ]

    print("Verificando registros no banco de dados PostgreSQL:")
    print("-" * 50)

    for table in tables:
        with connection.cursor() as cursor:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                count = cursor.fetchone()[0]
                print(f"{table}: {count} registros")
            except Exception as e:
                print(f"{table}: Erro ao verificar - {str(e)}")

    print("-" * 50)
    print("Verificação concluída!")


if __name__ == "__main__":
    check_database()