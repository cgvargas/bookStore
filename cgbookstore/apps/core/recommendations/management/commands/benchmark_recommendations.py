import time
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from cgbookstore.apps.core.models import Book, UserBookShelf
from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

User = get_user_model()


class Command(BaseCommand):
    """
    Classe resposável por comandar o gerenciamento do Django que executa um benchmark do sistema de recomendações.

    O objetivo é medir o desempenho do sistema de recomendações em termos de tempo de execução e número de queries
    no banco de dados, simulando um ambiente com vários usuários e livros.
    """
    help = 'Executa benchmark do sistema de recomendações'

    def add_arguments(self, parser):
        """
        Adiciona argumentos para o comando de gerenciamento.

        Args:
            parser: Objeto ArgumentParser para adicionar argumentos.
        """
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Número de usuários para teste'
        )
        parser.add_argument(
            '--books',
            type=int,
            default=1000,
            help='Número de livros para teste'
        )

    def handle(self, *args, **options):
        """
        Executa o benchmark do sistema de recomendações.

        Args:
            *args: Argumentos posicionais.
            **options: Argumentos de palavra-chave.
        """
        num_users = options['users']
        num_books = options['books']

        self.stdout.write('Preparando dados de teste...')

        # Cria livros de teste
        books = []
        for i in range(num_books):
            book = Book.objects.create(
                titulo=f'Livro {i}',
                autor=f'Autor {i % 50}',
                genero=f'Genero {i % 10}',
                categoria=f'Categoria {i % 5}'
            )
            books.append(book)

        # Cria usuários e histórico
        users = []
        for i in range(num_users):
            user = User.objects.create_user(
                username=f'test_user_{i}',
                password='test123'
            )
            users.append(user)

            # Adiciona histórico aleatório
            num_books_read = random.randint(5, 20)
            for book in random.sample(books, num_books_read):
                UserBookShelf.objects.create(
                    user=user,
                    book=book,
                    shelf_type='lido'
                )

        # Executa testes
        engine = RecommendationEngine()
        results = {
            'tempo_medio': 0,
            'queries_media': 0,
            'recomendacoes_media': 0
        }

        self.stdout.write('Executando testes...')

        for user in users:
            # Limpa queries anteriores
            connection.queries_log.clear()

            # Mede tempo e queries
            start = time.time()
            recommendations = engine.get_recommendations(user)
            _ = list(recommendations)  # Força execução
            end = time.time()

            results['tempo_medio'] += (end - start)
            results['queries_media'] += len(connection.queries)
            results['recomendacoes_media'] += len(recommendations)

        # Calcula médias
        for key in results:
            results[key] = results[key] / num_users

        # Exibe resultados
        self.stdout.write(self.style.SUCCESS('\nResultados do Benchmark:'))
        self.stdout.write(f"Usuários testados: {num_users}")
        self.stdout.write(f"Total de livros: {num_books}")
        self.stdout.write(f"Tempo médio: {results['tempo_medio']:.3f}s")
        self.stdout.write(f"Queries por requisição: {results['queries_media']:.1f}")
        self.stdout.write(f"Recomendações por requisição: {results['recomendacoes_media']:.1f}")