import json
import pickle
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.conf import settings
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Diagnostica cache Redis das recomendações de livros e compara com banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache',
            type=str,
            default='default',
            help='Nome do cache a ser verificado (default: default)'
        )
        parser.add_argument(
            '--clear-books',
            action='store_true',
            help='Limpa apenas cache relacionado a livros/recomendações'
        )
        parser.add_argument(
            '--test-images',
            action='store_true',
            help='Testa se as URLs das imagens estão acessíveis'
        )
        parser.add_argument(
            '--book-id',
            type=str,
            help='Analisa cache de um livro específico pelo ID'
        )
        parser.add_argument(
            '--external-id',
            type=str,
            help='Analisa cache de um livro específico pelo external_id'
        )

    def handle(self, *args, **options):
        cache_name = options['cache']

        try:
            cache = caches[cache_name]
            client = cache.client.get_client(write=True)

            self.stdout.write(
                self.style.SUCCESS(f'\n=== DIAGNÓSTICO CACHE LIVROS - CACHE: {cache_name} ===\n')
            )

            # Buscar todas as chaves relacionadas a livros
            self._analyze_book_cache_keys(client, options)

            # Analisar livro específico se solicitado
            if options['book_id']:
                self._analyze_specific_book_cache(cache, options['book_id'], 'id', options)

            if options['external_id']:
                self._analyze_specific_book_cache(cache, options['external_id'], 'external_id', options)

            # Limpar cache de livros se solicitado
            if options['clear_books']:
                self._clear_books_cache(client)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao acessar cache "{cache_name}": {e}')
            )

    def _analyze_book_cache_keys(self, client, options):
        """Analisa todas as chaves de cache relacionadas a livros"""
        self.stdout.write('🔍 BUSCANDO CHAVES DE CACHE RELACIONADAS A LIVROS...\n')

        # Padrões comuns de cache de livros
        book_patterns = [
            '*book*',
            '*livro*',
            '*recomend*',
            '*google*',
            '*api*',
            '*cover*',
            '*capa*'
        ]

        all_book_keys = set()

        for pattern in book_patterns:
            try:
                keys = client.keys(pattern)
                if keys:
                    decoded_keys = [key.decode('utf-8') if isinstance(key, bytes) else str(key) for key in keys]
                    all_book_keys.update(decoded_keys)
                    self.stdout.write(f'📋 Padrão "{pattern}": {len(decoded_keys)} chaves encontradas')
                    for key in decoded_keys[:5]:  # Mostrar apenas as primeiras 5
                        self.stdout.write(f'   • {key}')
                    if len(decoded_keys) > 5:
                        self.stdout.write(f'   ... e mais {len(decoded_keys) - 5} chaves')
                    self.stdout.write('')
            except Exception as e:
                self.stdout.write(f'❌ Erro ao buscar padrão "{pattern}": {e}')

        self.stdout.write(f'📊 TOTAL: {len(all_book_keys)} chaves únicas relacionadas a livros\n')

        # Analisar conteúdo das chaves encontradas
        if all_book_keys:
            self._analyze_cache_contents(client, list(all_book_keys), options)

    def _analyze_cache_contents(self, client, keys, options):
        """Analisa o conteúdo das chaves de cache"""
        self.stdout.write('🔬 ANALISANDO CONTEÚDO DO CACHE...\n')

        for key in keys[:10]:  # Limitar a 10 chaves para não sobrecarregar
            try:
                self.stdout.write(f'🔑 CHAVE: {key}')

                # Obter informações da chave
                key_type = client.type(key).decode('utf-8') if hasattr(client.type(key), 'decode') else str(
                    client.type(key))
                ttl = client.ttl(key)

                self.stdout.write(f'   Tipo: {key_type}')
                self.stdout.write(f'   TTL: {ttl}s ({self._format_ttl(ttl)})')

                # Tentar obter conteúdo
                if key_type == 'string':
                    try:
                        # Tentar via Django cache primeiro
                        cache_key = key.replace('default:1:', '') if 'default:1:' in key else key
                        django_value = caches['default'].get(cache_key)

                        if django_value is not None:
                            self._analyze_cache_value(django_value, key, options)
                        else:
                            # Tentar via Redis direto
                            raw_value = client.get(key)
                            if raw_value:
                                self._analyze_raw_cache_value(raw_value, key)
                            else:
                                self.stdout.write('   Conteúdo: Vazio ou não acessível')

                    except Exception as e:
                        self.stdout.write(f'   ❌ Erro ao ler conteúdo: {e}')

                self.stdout.write('')

            except Exception as e:
                self.stdout.write(f'❌ Erro ao analisar chave "{key}": {e}\n')

    def _analyze_cache_value(self, value, key, options):
        """Analisa o valor obtido do cache Django"""
        self.stdout.write(f'   Tipo de valor: {type(value).__name__}')

        if isinstance(value, dict):
            self.stdout.write(f'   Dicionário com {len(value)} chaves: {list(value.keys())[:5]}')

            # Procurar por dados de livros/imagens
            self._search_for_book_data(value, key, options)

        elif isinstance(value, list):
            self.stdout.write(f'   Lista com {len(value)} itens')

            # Analisar primeiros itens se forem dicts
            for i, item in enumerate(value[:3]):
                if isinstance(item, dict):
                    self.stdout.write(f'   Item {i}: {type(item).__name__} com chaves: {list(item.keys())[:3]}')
                    self._search_for_book_data(item, f'{key}[{i}]', options)

        elif isinstance(value, str):
            if len(value) > 200:
                self.stdout.write(f'   String longa ({len(value)} chars): {value[:100]}...')
            else:
                self.stdout.write(f'   String: {value}')

            # Verificar se é JSON
            try:
                json_data = json.loads(value)
                self._search_for_book_data(json_data, key, options)
            except:
                pass

        else:
            self.stdout.write(f'   Valor: {str(value)[:100]}...' if len(str(value)) > 100 else f'   Valor: {value}')

    def _analyze_raw_cache_value(self, raw_value, key):
        """Analisa valor bruto do Redis"""
        try:
            # Tentar decodificar como string
            if isinstance(raw_value, bytes):
                str_value = raw_value.decode('utf-8')
                self.stdout.write(f'   Valor bruto (string): {str_value[:100]}...' if len(
                    str_value) > 100 else f'   Valor bruto: {str_value}')
            else:
                self.stdout.write(f'   Valor bruto: {str(raw_value)[:100]}...' if len(
                    str(raw_value)) > 100 else f'   Valor bruto: {raw_value}')
        except:
            try:
                # Tentar deserializar pickle
                pickle_value = pickle.loads(raw_value)
                self.stdout.write(f'   Valor pickle: {type(pickle_value).__name__}')
            except:
                self.stdout.write(f'   Valor binário ({len(raw_value)} bytes)')

    def _search_for_book_data(self, data, key, options):
        """Procura por dados de livros/imagens no valor do cache"""
        if not isinstance(data, (dict, list)):
            return

        # Palavras-chave para identificar dados de livros
        book_keywords = ['id', 'titulo', 'title', 'capa_url', 'imageLinks', 'thumbnail', 'volumeInfo', 'external_id']

        if isinstance(data, dict):
            # Verificar se tem chaves relacionadas a livros
            found_keywords = [k for k in data.keys() if any(keyword.lower() in k.lower() for keyword in book_keywords)]

            if found_keywords:
                self.stdout.write(f'   📚 DADOS DE LIVRO ENCONTRADOS em {key}:')

                for keyword in found_keywords:
                    value = data[keyword]
                    self.stdout.write(f'     {keyword}: {value}')

                    # Verificar URLs de imagem
                    if any(img_key in keyword.lower() for img_key in ['capa', 'image', 'thumbnail', 'cover']):
                        if isinstance(value, str) and ('http' in value or 'books.google' in value):
                            self._analyze_image_url(value, f'{key}.{keyword}', options)

                # Verificar se é dados da API Google Books
                if 'volumeInfo' in data or 'imageLinks' in data:
                    self.stdout.write('     🔗 DADOS DA API GOOGLE BOOKS detectados')
                    self._analyze_google_books_data(data, key, options)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    self._search_for_book_data(item, f'{key}[{i}]', options)

    def _analyze_image_url(self, url, location, options):
        """Analisa URL de imagem encontrada no cache"""
        self.stdout.write(f'     🖼️  URL de imagem em {location}:')
        self.stdout.write(f'        {url}')

        # Verificar problemas comuns
        issues = []
        if url.startswith('http://'):
            issues.append('HTTP instead of HTTPS')
        if 'books.google.com' in url and 'zoom=' not in url:
            issues.append('Missing zoom parameter')
        if not url.strip():
            issues.append('Empty URL')

        if issues:
            self.stdout.write(f'        ⚠️  Problemas: {", ".join(issues)}')

        # Testar acessibilidade se solicitado
        if options.get('test_images'):
            self._test_image_accessibility(url)

    def _test_image_accessibility(self, url):
        """Testa se a URL da imagem está acessível"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                self.stdout.write(f'        ✅ Imagem acessível (Status: {response.status_code})')
            else:
                self.stdout.write(f'        ❌ Imagem inacessível (Status: {response.status_code})')
        except requests.exceptions.RequestException as e:
            self.stdout.write(f'        ❌ Erro ao acessar imagem: {e}')

    def _analyze_google_books_data(self, data, key, options):
        """Analisa dados específicos da API Google Books"""
        if 'volumeInfo' in data:
            vol_info = data['volumeInfo']

            if 'imageLinks' in vol_info:
                self.stdout.write('     📸 imageLinks encontrados:')
                for img_type, img_url in vol_info['imageLinks'].items():
                    self.stdout.write(f'       {img_type}: {img_url}')
                    self._analyze_image_url(img_url, f'{key}.volumeInfo.imageLinks.{img_type}', options)

    def _analyze_specific_book_cache(self, cache, book_identifier, id_type, options):
        """Analisa cache de um livro específico"""
        self.stdout.write(f'\n🎯 ANALISANDO LIVRO ESPECÍFICO ({id_type.upper()}: {book_identifier})\n')

        try:
            # Buscar livro no banco
            if id_type == 'id':
                book = Book.objects.get(id=book_identifier)
            else:
                book = Book.objects.get(external_id=book_identifier)

            self.stdout.write(f'📖 LIVRO NO BANCO:')
            self.stdout.write(f'   ID: {book.id}')
            self.stdout.write(f'   Título: {book.titulo}')
            self.stdout.write(f'   External ID: {book.external_id}')
            self.stdout.write(f'   Capa URL: {book.capa_url}')

            # Buscar possíveis chaves de cache para este livro
            possible_keys = [
                f'book_{book.id}',
                f'livro_{book.id}',
                f'recomendacoes_{book.id}',
                f'google_books_{book.external_id}',
                f'api_data_{book.external_id}',
            ]

            self.stdout.write(f'\n🔍 BUSCANDO NO CACHE...')
            found_in_cache = False

            for cache_key in possible_keys:
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    found_in_cache = True
                    self.stdout.write(f'✅ Encontrado em cache: {cache_key}')
                    self._analyze_cache_value(cached_value, cache_key, options)

                    # Comparar com dados do banco
                    self._compare_cache_with_db(cached_value, book)

            if not found_in_cache:
                self.stdout.write('❌ Livro não encontrado em cache específico')

        except Book.DoesNotExist:
            self.stdout.write(f'❌ Livro não encontrado no banco: {id_type}={book_identifier}')
        except Exception as e:
            self.stdout.write(f'❌ Erro ao analisar livro: {e}')

    def _compare_cache_with_db(self, cached_data, book):
        """Compara dados do cache com dados do banco"""
        self.stdout.write(f'\n🔄 COMPARAÇÃO CACHE vs BANCO:')

        if isinstance(cached_data, dict):
            # Comparar campos específicos
            if 'capa_url' in cached_data:
                cache_url = cached_data['capa_url']
                db_url = book.capa_url

                if cache_url != db_url:
                    self.stdout.write(f'   ⚠️  DIVERGÊNCIA - Capa URL:')
                    self.stdout.write(f'      Cache: {cache_url}')
                    self.stdout.write(f'      Banco: {db_url}')
                else:
                    self.stdout.write(f'   ✅ Capa URL consistente')

    def _clear_books_cache(self, client):
        """Limpa cache relacionado a livros"""
        self.stdout.write('\n🧹 LIMPANDO CACHE DE LIVROS...\n')

        patterns_to_clear = ['*book*', '*livro*', '*recomend*', '*google*books*', '*api*']
        total_cleared = 0

        for pattern in patterns_to_clear:
            try:
                keys = client.keys(pattern)
                # Filtrar para não deletar chaves críticas do Celery/Django
                safe_keys = [k for k in keys if not any(critical in k.decode('utf-8', errors='ignore').lower()
                                                        for critical in ['kombu', 'celery', 'session', 'csrf'])]

                if safe_keys:
                    deleted = client.delete(*safe_keys)
                    total_cleared += deleted
                    self.stdout.write(f'🗑️  Padrão "{pattern}": {deleted} chaves removidas')

            except Exception as e:
                self.stdout.write(f'❌ Erro ao limpar padrão "{pattern}": {e}')

        self.stdout.write(f'\n✅ Total de chaves removidas: {total_cleared}')

    def _format_ttl(self, ttl):
        """Formata TTL em formato legível"""
        if ttl == -1:
            return "sem expiração"
        elif ttl == -2:
            return "chave inexistente"
        elif ttl < 60:
            return f"{ttl}s"
        elif ttl < 3600:
            return f"{ttl // 60}m {ttl % 60}s"
        elif ttl < 86400:
            hours = ttl // 3600
            minutes = (ttl % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = ttl // 86400
            hours = (ttl % 86400) // 3600
            return f"{days}d {hours}h"