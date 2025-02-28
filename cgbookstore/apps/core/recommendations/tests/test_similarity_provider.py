import pytest
import logging
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models.book import Book, UserBookShelf
from cgbookstore.apps.core.recommendations.providers.similarity import SimilarityBasedProvider

@pytest.fixture(autouse=True)
def clear_database(db):
    """
    Limpa o banco de dados antes de cada teste
    """
    User = get_user_model()
    User.objects.all().delete()
    Book.objects.all().delete()
    UserBookShelf.objects.all().delete()


logger = logging.getLogger(__name__)
User = get_user_model()


@pytest.mark.django_db
class TestSimilarityBasedProvider:
    def setup_method(self):
        """
        Configura o ambiente de testes com diversos cenários
        """
        # Cria um usuário de teste com campos adicionais
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='12345',
            cpf='12345678901',
            first_name='Test',
            last_name='User'
        )

        # Cria livros com diferentes níveis de completude
        self.book_data = [
            {
                'titulo': f'Livro de Ficção Científica {i}',
                'genero': 'Ficção Científica',
                'autor': f'Autor A{i}',
                'categoria': 'Aventura',
                'temas': f'futuro,tecnologia,robôs,tema{i}',
                'descricao': f'Descrição do livro de ficção científica {i}',
                'isbn': f'ISBN-FC-{i}'
            } for i in range(1, 6)
        ]
        self.book_data.extend([
            {
                'titulo': f'Livro de Romance {i}',
                'genero': 'Romance',
                'autor': f'Autor B{i}',
                'categoria': 'Drama',
                'temas': f'amor,relacionamento,tema{i}',
                'descricao': f'Descrição do livro de romance {i}',
                'isbn': f'ISBN-ROM-{i}'
            } for i in range(1, 6)
        ])

        # Livros com campos incompletos
        self.book_data.append({
            'titulo': 'Livro Incompleto',
            'genero': '',
            'autor': '',
            'categoria': '',
            'temas': '',
            'descricao': '',
            'isbn': ''
        })

        # Cria os livros
        self.books = [Book.objects.create(**data) for data in self.book_data]

        # Adiciona alguns livros à estante do usuário
        for book in self.books[:3]:
            UserBookShelf.objects.create(
                user=self.user,
                book=book,
                shelf_type='favorito'
            )

        # Instancia o provider
        self.provider = SimilarityBasedProvider()

    def test_calculate_similarity_score(self):
        """
        Testa o cálculo de similaridade entre livros com diferentes níveis de semelhança
        """
        # Livros do mesmo gênero e categoria
        book1, book2 = self.books[:2]
        score_similar = self.provider.calculate_similarity_score(book1, book2)
        assert score_similar > 0.5, "Livros similares devem ter pontuação alta"

        # Livros completamente diferentes
        book_sci_fi = next(book for book in self.books if book.genero == 'Ficção Científica')
        book_romance = next(book for book in self.books if book.genero == 'Romance')
        score_different = self.provider.calculate_similarity_score(book_sci_fi, book_romance)
        assert score_different < 0.3, "Livros de gêneros diferentes devem ter baixa pontuação"

        # Teste com livro incompleto
        incomplete_book = self.books[-1]
        score_incomplete = self.provider.calculate_similarity_score(book1, incomplete_book)
        assert score_incomplete >= 0, "Deve lidar com livros com campos vazios"

    def test_get_recommendations(self):
        """
        Testa recomendações em diferentes cenários
        """
        # Recomendações para usuário com vários livros
        recommendations = self.provider.get_recommendations(self.user, limit=10)
        assert recommendations.count() > 0, "Deve retornar recomendações para usuário com livros"

        # Verifica se não recomenda livros já na estante
        recommended_ids = set(recommendations.values_list('id', flat=True))
        user_book_ids = set(UserBookShelf.objects.filter(user=self.user).values_list('book_id', flat=True))
        assert len(recommended_ids.intersection(user_book_ids)) == 0, "Não deve recomendar livros da estante"

    def test_get_recommendations_with_single_book(self):
        """
        Testa recomendações para usuário com apenas um livro
        """
        # Cria novo usuário com apenas um livro
        single_book_user = User.objects.create_user(
            username='singlebookuser',
            email='single@example.com',
            password='12345',
            cpf='98765432109'
        )

        # Adiciona apenas um livro à estante
        UserBookShelf.objects.create(
            user=single_book_user,
            book=self.books[0],
            shelf_type='favorito'
        )

        # Obtém recomendações
        recommendations = self.provider.get_recommendations(single_book_user, limit=10)
        assert recommendations.count() > 0, "Deve retornar recomendações mesmo com um único livro"

    def test_adjust_weights_for_user(self):
        """
        Testa o ajuste de pesos para diferentes perfis de usuário
        """
        # Testa ajuste de pesos
        adjusted_weights = self.provider._adjust_weights_for_user(self.user)

        # Verifica se os pesos foram ajustados
        assert adjusted_weights, "Deve retornar pesos ajustados"

        # Verifica se os pesos são diferentes dos originais
        original_weights = self.provider.WEIGHTS
        assert any(adjusted_weights[key] != original_weights[key] for key in original_weights), \
            "Pesos devem ser ajustados baseado no perfil do usuário"

    def test_find_similar_books(self):
        """
        Testa a busca de livros similares em diferentes cenários
        """
        # Obtém os livros base do usuário
        base_books = self.provider._get_base_books(self.user)

        # Ajusta os pesos para o usuário
        weights = self.provider._adjust_weights_for_user(self.user)

        # Busca livros similares
        similar_books = self.provider._find_similar_books(base_books, weights)

        # Verifica os resultados
        assert similar_books.count() > 0, "Deve encontrar livros similares"

        # Verifica se os livros base não estão na lista de similares
        base_book_ids = {book.book.id for book in base_books}
        similar_book_ids = set(similar_books.values_list('id', flat=True))

        assert len(base_book_ids.intersection(similar_book_ids)) == 0, \
            "Livros base não devem estar na lista de similares"

    def test_user_without_books(self):
        """
        Testa comportamento quando usuário não tem livros na estante
        """
        # Cria um novo usuário sem livros
        new_user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='12345',
            cpf='45612378909'
        )

        # Obtém recomendações
        recommendations = self.provider.get_recommendations(new_user, limit=10)

        # Verifica se retorna um queryset vazio
        assert recommendations.count() == 0, "Usuário sem livros deve retornar recomendações vazias"

    def test_similarity_with_incomplete_data(self):
        """
        Testa comportamento com livros com dados incompletos
        """
        # Livro com dados incompletos
        incomplete_book = self.books[-1]

        # Tenta calcular similaridade com um livro completo
        complete_book = self.books[0]

        # Calcula similaridade
        similarity_score = self.provider.calculate_similarity_score(complete_book, incomplete_book)

        # Verifica se o método lida com dados incompletos
        assert isinstance(similarity_score, float), "Deve retornar um score numérico"
        assert similarity_score >= 0, "Score não pode ser negativo"

    @pytest.mark.django_db
    def test_combine_recommendations_detailed(self):
        """
        Teste abrangente para o método de combinação de recomendações
        Cenários:
        - Diferentes tamanhos de listas de entrada
        - Verificação de exclusão de livros
        - Respeito ao limite de recomendações
        - Aleatoriedade da seleção
        """
        # Prepara conjuntos de livros para simulação
        history_books = self.books[:3]  # Primeiros 3 livros
        category_books = self.books[3:6]  # Próximos 3 livros
        similarity_books = self.books[6:9]  # Próximos 3 livros
        temporal_books = self.books[9:12]  # Próximos 3 livros (ou menos se não houver)

        # Cria alguns livros excluídos
        excluded_books = [book.id for book in self.books[:2]]

        # Simula livros favoritos
        favorite_books = UserBookShelf.objects.filter(
            user=self.user,
            shelf_type='favorito'
        )

        # Cenários de teste
        test_limits = [5, 10, 15]

        for limit in test_limits:
            # Chama o método de combinação
            combined_recommendations = self.provider._combine_recommendations(
                user=self.user,
                history_books=history_books,
                category_books=category_books,
                similarity_books=similarity_books,
                temporal_books=temporal_books,
                excluded_books=excluded_books,
                favorite_books=favorite_books,
                limit=limit
            )

            # Converte para lista para inspeção
            rec_list = list(combined_recommendations)

            # Verificações
            assert len(rec_list) <= limit, f"Deve respeitar o limite de {limit} recomendações"

            # Verifica se não há livros excluídos
            recommended_ids = {book.id for book in rec_list}
            assert len(set(excluded_books) & recommended_ids) == 0, "Não deve recomendar livros excluídos"

            # Verifica se não há livros favoritos
            favorite_book_ids = {fb.book.id for fb in favorite_books}
            assert len(favorite_book_ids & recommended_ids) == 0, "Não deve recomendar livros favoritos"

            # Verificação de diversidade
            # Garante que as recomendações vêm de diferentes sources
            source_counts = {
                'history': sum(1 for book in rec_list if book in history_books),
                'category': sum(1 for book in rec_list if book in category_books),
                'similarity': sum(1 for book in rec_list if book in similarity_books),
                'temporal': sum(1 for book in rec_list if book in temporal_books)
            }

            print(f"Distribuição de recomendações para limite {limit}:")
            print(source_counts)

            # Verifica se há uma distribuição mínima
            assert all(count > 0 for count in source_counts.values()), \
                "Deve ter recomendações de todos os sources"

    @pytest.mark.django_db
    def test_analyze_user_preferences_comprehensive(self, django_user_model):
        """
        Teste abrangente para análise de preferências do usuário
        """

        def create_unique_cpf():
            """Gera um CPF único para teste"""
            from random import randint
            return f"{randint(10000000000, 99999999999)}"

        def create_user_with_books(username, email, books_data):
            # Gera CPF único para cada usuário
            cpf = create_unique_cpf()

            user = django_user_model.objects.create_user(
                username=username,
                email=email,
                password='12345',
                cpf=cpf
            )

            # Cria e adiciona livros à estante
            for book_info in books_data:
                book = Book.objects.create(
                    titulo=book_info['titulo'],
                    autor=book_info['autor'],
                    genero=book_info['genero'],
                    categoria=book_info.get('categoria', 'Diversos')
                )
                UserBookShelf.objects.create(user=user, book=book, shelf_type='lido')

            return user

        # Teste de usuário com poucos livros
        few_books_user = create_user_with_books(
            username='few_books_user_test',
            email='few@example.com',
            books_data=[
                {'titulo': 'Livro 1', 'autor': 'Autor 1', 'genero': 'Ficção'},
                {'titulo': 'Livro 2', 'autor': 'Autor 2', 'genero': 'Romance'}
            ]
        )
        assert few_books_user is not None, "Falha ao criar usuário com poucos livros"

        preferences = self.provider._analyze_user_preferences(few_books_user)
        assert preferences == {}, "Deve retornar dicionário vazio para poucos livros"

        # Teste de usuário com múltiplos livros do mesmo autor
        loyal_user = create_user_with_books(
            username='author_loyal_user_test',
            email='loyal@example.com',
            books_data=[
                {'titulo': f'Livro do Autor A {i}', 'autor': 'Autor Leal', 'genero': 'Ficção',
                 'categoria': 'Literatura'}
                for i in range(5)
            ]
        )
        assert loyal_user is not None, "Falha ao criar usuário leal a autor"

        preferences = self.provider._analyze_user_preferences(loyal_user)
        assert preferences.get('author_loyal', False) == True, "Deve identificar lealdade a autor"

        # Teste de usuário com livros de diferentes gêneros
        diverse_user = create_user_with_books(
            username='diverse_genre_user_test',
            email='diverse@example.com',
            books_data=[
                {'titulo': f'Livro Gênero {gen}', 'autor': f'Autor {gen}', 'genero': gen}
                for gen in ['Ficção', 'Romance', 'Fantasia', 'Suspense', 'Ficção Científica']
            ]
        )
        assert diverse_user is not None, "Falha ao criar usuário com gêneros diversos"

        preferences = self.provider._analyze_user_preferences(diverse_user)
        assert preferences.get('genre_focused', False) == False, "Deve identificar usuário com gêneros diversos"

    @pytest.mark.django_db
    def test_similarity_score_edge_cases(self):
        """
        Testa cálculo de similaridade em casos extremos
        """

        def create_specific_book(genero='', autor='', categoria='', temas=''):
            return Book.objects.create(
                titulo='Livro Específico',
                genero=genero,
                autor=autor,
                categoria=categoria,
                temas=temas
            )

        # Caso 1: Livros completamente diferentes
        book1 = create_specific_book(
            genero='Ficção Científica',
            autor='Autor Sci-Fi',
            categoria='Tecnologia',
            temas='futuro,robôs,tecnologia'
        )
        book2 = create_specific_book(
            genero='Romance',
            autor='Autor Romance',
            categoria='Drama',
            temas='amor,relacionamento,drama'
        )

        score_different = self.provider.calculate_similarity_score(book1, book2)
        assert score_different < 0.3, "Livros completamente diferentes devem ter baixa similaridade"

        # Caso 2: Livros quase idênticos
        book3 = create_specific_book(
            genero='Ficção Científica',
            autor='Autor Sci-Fi',
            categoria='Tecnologia',
            temas='futuro,robôs,tecnologia'
        )
        book4 = create_specific_book(
            genero='Ficção Científica',
            autor='Autor Sci-Fi',
            categoria='Tecnologia',
            temas='futuro,robôs,inteligencia artificial'
        )

        score_similar = self.provider.calculate_similarity_score(book3, book4)
        assert score_similar > 0.8, "Livros muito similares devem ter alta pontuação"

        # Caso 3: Livros com dados parcialmente preenchidos
        book5 = create_specific_book(genero='Ficção Científica')
        book6 = create_specific_book(autor='Autor Sci-Fi')

        score_partial = self.provider.calculate_similarity_score(book5, book6)
        assert 0 <= score_partial < 0.3, "Livros com poucos atributos em comum devem ter baixa similaridade"
