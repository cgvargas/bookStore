# Arquivo: cgbookstore/apps/core/recommendations/analytics/tests/generate_test_data.py

from django.contrib.auth import get_user_model
from django.utils import timezone
from cgbookstore.apps.core.recommendations.analytics.models import RecommendationInteraction
from cgbookstore.apps.core.models.book import Book
from datetime import timedelta
import random
from decimal import Decimal


def generate_cpf():
    numbers = [random.randint(0, 9) for _ in range(9)]
    total = sum((10 - i) * n for i, n in enumerate(numbers))
    remainder = total % 11
    first_digit = 0 if remainder < 2 else 11 - remainder
    numbers.append(first_digit)
    total = sum((11 - i) * n for i, n in enumerate(numbers))
    remainder = total % 11
    second_digit = 0 if remainder < 2 else 11 - remainder
    numbers.append(second_digit)
    return ''.join(map(str, numbers))


def create_test_data():
    # Criar mais usuários de teste
    User = get_user_model()
    users = []
    for i in range(20):  # Aumentado para 20 usuários
        cpf = generate_cpf()
        user, created = User.objects.get_or_create(
            username=f'test_user_{i}',
            defaults={
                'email': f'test{i}@example.com',
                'cpf': cpf,
                'first_name': f'Test{i}',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('test123')
            user.save()
        users.append(user)

    # Mais categorias para melhor distribuição
    categorias = ['Ficção', 'Não Ficção', 'Tecnologia', 'Romance', 'Aventura', 'Autoajuda', 'História', 'Ciência']

    # Criar mais livros de teste
    books = []
    for i in range(30):  # Aumentado para 30 livros
        book, _ = Book.objects.get_or_create(
            titulo=f'Livro Teste {i}',
            defaults={
                'autor': f'Autor Teste {i}',
                'categoria': random.choice(categorias),
                'preco': Decimal(str(random.uniform(20, 100))),
                'descricao': f'Descrição do livro teste {i}'
            }
        )
        books.append(book)

    # Criar interações mais variadas
    now = timezone.now()
    interaction_types = ['view', 'click', 'add_shelf', 'purchase', 'ignore']
    source_types = ['general', 'history', 'category', 'similarity']

    # Distribuição das interações para simular padrões realistas
    interaction_weights = {
        'view': 0.5,  # 50% das interações
        'click': 0.25,  # 25% das interações
        'add_shelf': 0.15,  # 15% das interações
        'purchase': 0.05,  # 5% das interações
        'ignore': 0.05  # 5% das interações
    }

    # Criando 1000 interações para ter dados mais significativos
    for _ in range(1000):
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)

        interaction_date = now - timedelta(
            days=days_ago,
            hours=hours_ago,
            minutes=random.randint(0, 59)
        )

        # Seleção ponderada do tipo de interação
        interaction_type = random.choices(
            list(interaction_weights.keys()),
            weights=list(interaction_weights.values())
        )[0]

        # Atribuir score mais alto para compras e adições à prateleira
        recommendation_score = random.uniform(0.7, 1.0) if interaction_type in ['purchase',
                                                                                'add_shelf'] else random.uniform(0.1,
                                                                                                                 0.9)

        # Metadata mais detalhada
        metadata = {
            'session_id': f'session_{random.randint(1, 100)}',
            'page_source': random.choice(['home', 'search', 'category', 'recommendation']),
            'device_type': random.choice(['desktop', 'mobile', 'tablet']),
            'time_spent': random.randint(10, 300)  # segundos
        }

        RecommendationInteraction.objects.create(
            user=random.choice(users),
            book=random.choice(books),
            interaction_type=interaction_type,
            source=random.choice(source_types),
            timestamp=interaction_date,
            recommendation_score=recommendation_score,
            metadata=metadata,
            position=random.randint(1, 10) if interaction_type in ['view', 'click'] else None
        )

    print("Dados de teste criados com sucesso!")