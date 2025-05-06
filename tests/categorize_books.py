import os
import sys
import django
import random
from pathlib import Path

# Configurar ambiente Django
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


def categorize_books():
    """Categoriza livros para aparecerem nas prateleiras"""
    from django.db import connection

    # Determinar o nome correto da tabela de livros
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'core_book'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("Tabela core_book não encontrada!")
            return

    # Exibir total de livros
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM core_book;
        """)
        total_books = cursor.fetchone()[0]
        print(f"Total de livros no banco: {total_books}")

    # Distribuir livros nas prateleiras
    if total_books == 0:
        print("Nenhum livro encontrado no banco de dados!")
        return

    # Obter IDs de todos os livros
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM core_book;
        """)
        book_ids = [row[0] for row in cursor.fetchall()]

    if not book_ids:
        print("Não foi possível obter IDs dos livros.")
        return

    print(f"Encontrados {len(book_ids)} livros para categorizar.")

    # Distribuir aleatoriamente os livros (para garantir uma boa distribuição inicial)
    random.shuffle(book_ids)

    # Definir quantidades para cada categoria
    total = len(book_ids)
    ebooks_count = max(2, total // 6)
    tecnologia_count = max(2, total // 6)
    lancamentos_count = max(2, total // 6)
    destaques_count = max(2, total // 6)
    adaptados_count = max(2, total // 6)
    mangas_count = max(2, total // 6)

    # Dividir os IDs em categorias
    ebooks = book_ids[:ebooks_count]
    tecnologia = book_ids[ebooks_count:ebooks_count + tecnologia_count]
    lancamentos = book_ids[ebooks_count + tecnologia_count:ebooks_count + tecnologia_count + lancamentos_count]
    destaques = book_ids[
                ebooks_count + tecnologia_count + lancamentos_count:ebooks_count + tecnologia_count + lancamentos_count + destaques_count]
    adaptados = book_ids[
                ebooks_count + tecnologia_count + lancamentos_count + destaques_count:ebooks_count + tecnologia_count + lancamentos_count + destaques_count + adaptados_count]
    mangas = book_ids[
             ebooks_count + tecnologia_count + lancamentos_count + destaques_count + adaptados_count:ebooks_count + tecnologia_count + lancamentos_count + destaques_count + adaptados_count + mangas_count]

    # Categorizar: eBooks
    if ebooks:
        ids_str = ','.join(str(id) for id in ebooks)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET tipo_shelf_especial = 'ebooks' 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(ebooks)} livros como eBooks")

    # Categorizar: Tecnologia
    if tecnologia:
        ids_str = ','.join(str(id) for id in tecnologia)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET tipo_shelf_especial = 'tecnologia' 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(tecnologia)} livros como Tecnologia")

    # Categorizar: Lançamentos
    if lancamentos:
        ids_str = ','.join(str(id) for id in lancamentos)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET e_lancamento = TRUE 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(lancamentos)} livros como Lançamentos")

    # Categorizar: Destaques
    if destaques:
        ids_str = ','.join(str(id) for id in destaques)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET e_destaque = TRUE 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(destaques)} livros como Destaques")

    # Categorizar: Adaptados para Filmes/Séries
    if adaptados:
        ids_str = ','.join(str(id) for id in adaptados)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET adaptado_filme = TRUE 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(adaptados)} livros como Adaptados para Filmes/Séries")

    # Categorizar: Mangás
    if mangas:
        ids_str = ','.join(str(id) for id in mangas)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                UPDATE core_book 
                SET e_manga = TRUE 
                WHERE id IN ({ids_str});
            """)
        print(f"Categorizados {len(mangas)} livros como Mangás")

    print("Categorização concluída!")


if __name__ == "__main__":
    categorize_books()