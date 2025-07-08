from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services.training_service import training_service
import csv
import json
import requests
from pathlib import Path


class Command(BaseCommand):
    help = 'Importação avançada de base de conhecimento de múltiplas fontes'

    def add_arguments(self, parser):
        parser.add_argument('--source', choices=['file', 'url', 'api'], required=True)
        parser.add_argument('--path', type=str, help='Caminho do arquivo ou URL')
        parser.add_argument('--format', choices=['csv', 'json', 'txt'], default='csv')
        parser.add_argument('--category', type=str, default='importado')
        parser.add_argument('--batch-size', type=int, default=100)
        parser.add_argument('--update-embeddings', action='store_true')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        source = options['source']
        path = options['path']
        format_type = options['format']
        category = options['category']
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write("=" * 60)
        self.stdout.write("📥 IMPORTAÇÃO AVANÇADA DE BASE DE CONHECIMENTO")
        self.stdout.write("=" * 60)

        if source == 'file':
            self.import_from_file(path, format_type, category, batch_size, dry_run)
        elif source == 'url':
            self.import_from_url(path, format_type, category, batch_size, dry_run)
        elif source == 'api':
            self.import_from_api(path, category, batch_size, dry_run)

        if options['update_embeddings'] and not dry_run:
            self.stdout.write("\n🔄 Atualizando embeddings...")
            training_service.update_embeddings()

    def import_from_file(self, file_path, format_type, category, batch_size, dry_run):
        """Importa de arquivo local."""
        self.stdout.write(f"\n📁 Importando de arquivo: {file_path}")

        if not Path(file_path).exists():
            self.stdout.write(f"❌ Arquivo não encontrado: {file_path}")
            return

        items = []

        if format_type == 'csv':
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                items = list(reader)

        elif format_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as file:
                items = json.load(file)

        elif format_type == 'txt':
            # Formato: pergunta|resposta (uma por linha)
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if '|' in line:
                        question, answer = line.strip().split('|', 1)
                        items.append({
                            'question': question.strip(),
                            'answer': answer.strip(),
                            'category': category,
                            'source': 'arquivo_txt'
                        })

        self.process_items(items, batch_size, dry_run)

    def import_from_url(self, url, format_type, category, batch_size, dry_run):
        """Importa de URL remota."""
        self.stdout.write(f"\n🌐 Importando de URL: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()

            items = []

            if format_type == 'csv':
                from io import StringIO
                reader = csv.DictReader(StringIO(response.text))
                items = list(reader)

            elif format_type == 'json':
                items = response.json()

            self.process_items(items, batch_size, dry_run)

        except Exception as e:
            self.stdout.write(f"❌ Erro ao baixar de URL: {e}")

    def import_from_api(self, api_endpoint, category, batch_size, dry_run):
        """Importa de API específica (exemplo: OpenLibrary)."""
        self.stdout.write(f"\n🔌 Importando de API: {api_endpoint}")

        # Exemplo para OpenLibrary API
        if 'openlibrary.org' in api_endpoint:
            items = self.fetch_from_openlibrary(api_endpoint, category)
            self.process_items(items, batch_size, dry_run)
        else:
            self.stdout.write("❌ API não suportada")

    def fetch_from_openlibrary(self, api_endpoint, category):
        """Busca dados da OpenLibrary API."""
        items = []

        try:
            # Exemplo: buscar autores famosos
            authors = ['J.K. Rowling', 'J.R.R. Tolkien', 'Machado de Assis']

            for author in authors:
                search_url = f"https://openlibrary.org/search/authors.json?q={author}"
                response = requests.get(search_url)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('docs'):
                        author_data = data['docs'][0]

                        items.append({
                            'question': f"Quem é {author}?",
                            'answer': f"{author} é um(a) escritor(a) conhecido(a).",
                            'category': category,
                            'source': 'openlibrary_api'
                        })

                        # Buscar obras do autor
                        if 'key' in author_data:
                            works_url = f"https://openlibrary.org/authors/{author_data['key']}/works.json"
                            works_response = requests.get(works_url)

                            if works_response.status_code == 200:
                                works_data = works_response.json()

                                if works_data.get('entries'):
                                    books = [work.get('title', '') for work in works_data['entries'][:5]]
                                    books_list = ', '.join(filter(None, books))

                                    if books_list:
                                        items.append({
                                            'question': f"Quais livros {author} escreveu?",
                                            'answer': f"{author} escreveu: {books_list}.",
                                            'category': category,
                                            'source': 'openlibrary_api'
                                        })

        except Exception as e:
            self.stdout.write(f"❌ Erro na API OpenLibrary: {e}")

        return items

    def process_items(self, items, batch_size, dry_run):
        """Processa lista de itens para importação."""
        if not items:
            self.stdout.write("❌ Nenhum item encontrado para importar")
            return

        self.stdout.write(f"\n📊 Total de itens encontrados: {len(items)}")

        if dry_run:
            self.stdout.write("🔍 DRY-RUN - Primeiros 5 itens:")
            for i, item in enumerate(items[:5], 1):
                self.stdout.write(f"   {i}. P: {item.get('question', '')[:50]}...")
                self.stdout.write(f"      R: {item.get('answer', '')[:50]}...")
            return

        # Processar em lotes
        imported = 0
        failed = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            self.stdout.write(f"\n📦 Processando lote {i // batch_size + 1}...")

            for item in batch:
                try:
                    # Validar campos obrigatórios
                    if not item.get('question') or not item.get('answer'):
                        failed += 1
                        continue

                    # Verificar se já existe
                    existing = KnowledgeItem.objects.filter(
                        question=item['question']
                    ).first()

                    if existing:
                        self.stdout.write(f"   ⚠️  Já existe: {item['question'][:30]}...")
                        continue

                    # Criar item
                    success = training_service.add_knowledge_item(
                        item['question'],
                        item['answer'],
                        category=item.get('category', 'importado'),
                        source=item.get('source', 'importacao')
                    )

                    if success:
                        imported += 1
                        if imported <= 3:  # Mostrar primeiros 3
                            self.stdout.write(f"   ✅ {item['question'][:40]}...")
                    else:
                        failed += 1

                except Exception as e:
                    self.stdout.write(f"   ❌ Erro: {e}")
                    failed += 1

        self.stdout.write(f"\n📈 Resultados:")
        self.stdout.write(f"   ✅ Importados: {imported}")
        self.stdout.write(f"   ❌ Falharam: {failed}")
        self.stdout.write(f"   📊 Total na base: {KnowledgeItem.objects.filter(active=True).count()}")

    def import_wikipedia_summaries(self, topics, language='pt'):
        """Importa resumos da Wikipedia para tópicos específicos."""
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(language)
        items = []

        for topic in topics:
            try:
                page = wiki.page(topic)
                if page.exists():
                    summary = page.summary[:500]  # Primeiros 500 caracteres

                    items.append({
                        'question': f"O que é {topic}?",
                        'answer': summary,
                        'category': 'Wikipedia',
                        'source': 'wikipedia_api'
                    })

                    items.append({
                        'question': f"Fale sobre {topic}",
                        'answer': summary,
                        'category': 'Wikipedia',
                        'source': 'wikipedia_api'
                    })

            except Exception as e:
                self.stdout.write(f"❌ Erro Wikipedia para {topic}: {e}")

        return items