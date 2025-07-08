# /cgbookstore/apps/chatbot_literario/management/commands/diagnose_chatbot.py

from django.core.management.base import BaseCommand
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Diagnostica problemas do chatbot e mostra estrutura dos modelos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-search',
            action='store_true',
            help='Testa busca de livros',
        )
        parser.add_argument(
            '--test-embeddings',
            action='store_true',
            help='Testa serviço de embeddings',
        )
        parser.add_argument(
            '--show-models',
            action='store_true',
            help='Mostra estrutura dos modelos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DIAGNÓSTICO DO CHATBOT ===\n'))

        if options['show_models']:
            self.show_model_structure()

        if options['test_search']:
            self.test_book_search()

        if options['test_embeddings']:
            self.test_embeddings_service()

        # Diagnóstico geral sempre executado
        self.general_diagnosis()

    def show_model_structure(self):
        """Mostra a estrutura dos modelos relevantes."""
        self.stdout.write(self.style.WARNING('=== ESTRUTURA DOS MODELOS ==='))

        models_to_check = [
            ('core', 'Book'),
            ('core', 'Author'),
            ('chatbot_literario', 'KnowledgeItem'),
        ]

        for app_name, model_name in models_to_check:
            try:
                model = apps.get_model(app_name, model_name)
                self.stdout.write(f'\n--- Modelo {app_name}.{model_name} ---')

                # Lista todos os campos
                for field in model._meta.get_fields():
                    field_info = f"  {field.name}: {field.__class__.__name__}"

                    # Adiciona informações extras para relacionamentos
                    if hasattr(field, 'related_model') and field.related_model:
                        field_info += f" -> {field.related_model.__name__}"

                    self.stdout.write(field_info)

                # Verifica métodos especiais
                if hasattr(model, 'get_nome_completo'):
                    self.stdout.write("  ✅ Método get_nome_completo() encontrado")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erro ao analisar {app_name}.{model_name}: {e}")
                )

    def test_book_search(self):
        """Testa diferentes tipos de busca de livros."""
        self.stdout.write(self.style.WARNING('\n=== TESTE DE BUSCA DE LIVROS ==='))

        try:
            Book = apps.get_model('core', 'Book')

            # Teste 1: Busca simples por título
            self.stdout.write('Testando busca por título...')
            try:
                books = Book.objects.filter(titulo__icontains='o')[:3]
                self.stdout.write(f"  ✅ Encontrados {books.count()} livros")
                for book in books:
                    self.stdout.write(f"    - {book.titulo}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erro: {e}"))

            # Teste 2: Busca por autor
            self.stdout.write('\nTestando busca por autor...')
            try:
                books = Book.objects.filter(autor__nome__icontains='a')[:3]
                self.stdout.write(f"  ✅ Encontrados {books.count()} livros por autor")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erro na busca por autor: {e}"))

            # Teste 3: Busca por categoria
            self.stdout.write('\nTestando busca por categoria...')
            try:
                books = Book.objects.filter(categorias__nome__icontains='ficção')[:3]
                self.stdout.write(f"  ✅ Encontrados {books.count()} livros por categoria")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erro na busca por categoria: {e}"))

                # Verifica se o campo categorias existe
                if hasattr(Book, 'categorias'):
                    self.stdout.write("    ℹ️ Campo 'categorias' existe no modelo")
                    # Verifica o tipo de relacionamento
                    categorias_field = Book._meta.get_field('categorias')
                    self.stdout.write(f"    ℹ️ Tipo do campo: {categorias_field.__class__.__name__}")
                    if hasattr(categorias_field, 'related_model'):
                        self.stdout.write(f"    ℹ️ Modelo relacionado: {categorias_field.related_model.__name__}")
                else:
                    self.stdout.write("    ⚠️ Campo 'categorias' NÃO existe no modelo")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao carregar modelo Book: {e}"))

    def test_embeddings_service(self):
        """Testa o serviço de embeddings."""
        self.stdout.write(self.style.WARNING('\n=== TESTE DE EMBEDDINGS ==='))

        try:
            from cgbookstore.apps.chatbot_literario.services.functional_chatbot import chatbot_service

            # Teste 1: Verifica se o serviço está disponível
            if chatbot_service.embeddings_service:
                self.stdout.write('  ✅ Serviço de embeddings carregado')

                # Teste 2: Tenta criar um embedding
                try:
                    test_text = "teste de embedding"
                    embedding = chatbot_service.embeddings_service.create_embedding(test_text)
                    if embedding is not None:
                        self.stdout.write(f"  ✅ Embedding criado com sucesso (dimensão: {len(embedding)})")
                    else:
                        self.stdout.write('  ❌ Embedding retornou None')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ Erro ao criar embedding: {e}"))
                    if "10053" in str(e):
                        self.stdout.write('  ℹ️ Error 10053 detectado - problema de conectividade')
            else:
                self.stdout.write('  ❌ Serviço de embeddings não disponível')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao testar embeddings: {e}"))

    def general_diagnosis(self):
        """Diagnóstico geral do sistema."""
        self.stdout.write(self.style.WARNING('\n=== DIAGNÓSTICO GERAL ==='))

        # Verifica base de conhecimento
        try:
            KnowledgeItem = apps.get_model('chatbot_literario', 'KnowledgeItem')

            total_items = KnowledgeItem.objects.count()
            active_items = KnowledgeItem.objects.filter(active=True).count()
            items_with_embeddings = KnowledgeItem.objects.filter(
                active=True,
                embedding__isnull=False
            ).exclude(embedding=[]).count()

            self.stdout.write(f'Base de Conhecimento:')
            self.stdout.write(f'  - Total de itens: {total_items}')
            self.stdout.write(f'  - Itens ativos: {active_items}')
            self.stdout.write(f'  - Itens com embeddings: {items_with_embeddings}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao verificar base de conhecimento: {e}"))

        # Verifica modelos principais
        models_to_verify = [
            ('core', 'Book'),
            ('core', 'Author'),
            ('core', 'Profile'),
        ]

        for app_name, model_name in models_to_verify:
            try:
                model = apps.get_model(app_name, model_name)
                count = model.objects.count()
                self.stdout.write(f'{app_name}.{model_name}: {count} registros')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao verificar {app_name}.{model_name}: {e}"))

        self.stdout.write(self.style.SUCCESS('\n=== FIM DO DIAGNÓSTICO ==='))