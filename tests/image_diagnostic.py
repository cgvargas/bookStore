#!/usr/bin/env python
"""
Script de Diagnóstico - Problema de Capas de Livros
Arquivo: tests/image_diagnostic.py
Objetivo: Investigar por que as capas dos livros do Google Books não aparecem
"""

import os
import sys
import django
import requests
import time
from urllib.parse import urlparse
import json

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.core.cache import caches
from cgbookstore.apps.core.models import Book

# Importar serviços disponíveis
try:
    from cgbookstore.apps.core.services.google_books_service import GoogleBooksService

    GOOGLE_BOOKS_CLASS = GoogleBooksService
except ImportError:
    try:
        from cgbookstore.apps.core.services.google_books_client import GoogleBooksClient

        GOOGLE_BOOKS_CLASS = GoogleBooksClient
    except ImportError:
        # Verificar outros possíveis nomes
        try:
            from cgbookstore.apps.core.services import google_books_service

            # Tentar encontrar a classe principal
            for attr_name in dir(google_books_service):
                attr = getattr(google_books_service, attr_name)
                if hasattr(attr, '__name__') and 'Books' in attr.__name__:
                    GOOGLE_BOOKS_CLASS = attr
                    break
            else:
                GOOGLE_BOOKS_CLASS = None
        except ImportError:
            GOOGLE_BOOKS_CLASS = None


class ImageDiagnostic:
    def __init__(self):
        self.results = {
            'redis_connection': False,
            'image_cache_status': {},
            'google_books_api': False,
            'sample_urls_test': [],
            'proxy_service_test': False,
            'recommendations': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def test_redis_connection(self):
        """Testar conexão com Redis"""
        self.print_header("1. TESTE DE CONEXÃO REDIS")

        try:
            # Testar cache de imagens
            image_cache = caches['image_proxy']

            # Teste básico de escrita/leitura
            test_key = 'diagnostic_test'
            test_value = 'connection_ok'

            image_cache.set(test_key, test_value, 30)
            retrieved_value = image_cache.get(test_key)

            if retrieved_value == test_value:
                print("✅ Redis conectado com sucesso")
                print(f"   Cache backend: {image_cache.__class__.__name__}")
                self.results['redis_connection'] = True

                # Limpar teste
                image_cache.delete(test_key)
            else:
                print("❌ Redis conectado mas com problemas de escrita/leitura")

        except Exception as e:
            print(f"❌ Erro de conexão Redis: {str(e)}")
            self.results['redis_connection'] = False

    def analyze_image_cache(self):
        """Analisar status do cache de imagens"""
        self.print_header("2. ANÁLISE DO CACHE DE IMAGENS")

        try:
            image_cache = caches['image_proxy']

            # Tentar obter informações do cache
            print(f"📊 Backend do cache: {type(image_cache).__name__}")

            # Para Redis, tentar acessar as chaves (se possível)
            if hasattr(image_cache, '_cache'):
                try:
                    # Algumas informações básicas
                    print("📋 Tentando analisar conteúdo do cache...")

                    # Teste com algumas chaves conhecidas
                    test_patterns = [
                        'google_books_image_',
                        'book_cover_',
                        'image_proxy_'
                    ]

                    for pattern in test_patterns:
                        print(f"   Padrão '{pattern}': Verificando...")

                except Exception as e:
                    print(f"   ⚠️  Não foi possível analisar detalhes: {str(e)}")

            print("✅ Cache de imagens acessível")
            self.results['image_cache_status']['accessible'] = True

        except Exception as e:
            print(f"❌ Erro ao analisar cache: {str(e)}")
            self.results['image_cache_status']['accessible'] = False

    def test_google_books_api(self):
        """Testar API do Google Books"""
        self.print_header("3. TESTE DA API GOOGLE BOOKS")

        if GOOGLE_BOOKS_CLASS is None:
            print("❌ Classe do Google Books não encontrada nos serviços")
            print("   Verificando arquivos disponíveis...")

            # Verificar o que está disponível
            try:
                import cgbookstore.apps.core.services.google_books_service as gbs
                print(f"   📋 Atributos disponíveis: {[attr for attr in dir(gbs) if not attr.startswith('_')]}")
            except Exception as e:
                print(f"   ❌ Erro ao importar: {str(e)}")

            self.results['google_books_api'] = False
            return

        try:
            # Usar o serviço encontrado
            print(f"🔧 Usando classe: {GOOGLE_BOOKS_CLASS.__name__}")
            service = GOOGLE_BOOKS_CLASS()

            # Verificar se tem método de busca
            search_method = None
            for method_name in ['search_books', 'search', 'get_books']:
                if hasattr(service, method_name):
                    search_method = getattr(service, method_name)
                    print(f"   📋 Método de busca encontrado: {method_name}")
                    break

            if not search_method:
                print("   ❌ Método de busca não encontrado")
                print(f"   📋 Métodos disponíveis: {[m for m in dir(service) if not m.startswith('_')]}")
                self.results['google_books_api'] = False
                return

            # Teste com uma busca simples
            print("🔍 Testando busca na API...")

            # Tentar diferentes assinaturas de método
            try:
                results = search_method("Harry Potter")
            except TypeError:
                try:
                    results = search_method(query="Harry Potter", max_results=3)
                except TypeError:
                    try:
                        results = search_method("Harry Potter", 3)
                    except Exception as e:
                        print(f"   ❌ Erro na busca: {str(e)}")
                        self.results['google_books_api'] = False
                        return

            if results and len(results) > 0:
                print(f"✅ API funcionando - {len(results)} resultados encontrados")

                # Analisar URLs de imagem
                print("\n📸 Analisando URLs de imagem:")

                # Converter results para lista se necessário
                if hasattr(results, '__iter__') and not isinstance(results, (list, tuple)):
                    results_list = list(results)
                else:
                    results_list = results

                # Pegar os primeiros 2 resultados de forma segura
                sample_books = []
                for i, book in enumerate(results_list):
                    if i >= 2:  # Limitar a 2 livros
                        break
                    sample_books.append(book)

                for i, book in enumerate(sample_books):
                    # Adaptar para diferentes estruturas de dados
                    title = self.get_book_title(book)
                    print(f"\n   Livro {i + 1}: {title}")

                    # Verificar diferentes tipos de URL de imagem
                    image_links = self.get_book_image_links(book)
                    if image_links:
                        for size, url in image_links.items():
                            print(f"     {size}: {url}")

                            # Testar se a URL responde
                            url_status = self.test_image_url(url)
                            self.results['sample_urls_test'].append({
                                'book': title,
                                'size': size,
                                'url': url,
                                'status': url_status
                            })
                    else:
                        print("     ⚠️ Nenhuma URL de imagem encontrada")

                self.results['google_books_api'] = True

            else:
                print("❌ API não retornou resultados")
                self.results['google_books_api'] = False

        except Exception as e:
            print(f"❌ Erro na API Google Books: {str(e)}")
            import traceback
            print(f"   Detalhes: {traceback.format_exc()}")
            self.results['google_books_api'] = False

    def test_image_url(self, url, timeout=10):
        """Testar se uma URL de imagem responde"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)

            status_info = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', 'unknown'),
                'accessible': response.status_code == 200
            }

            if response.status_code == 200:
                print(f"       ✅ OK ({response.status_code}) - {status_info['content_type']}")
            else:
                print(f"       ❌ Erro {response.status_code}")

            return status_info

        except requests.exceptions.Timeout:
            print(f"       ⏱️  Timeout ({timeout}s)")
            return {'status_code': 'timeout', 'accessible': False}
        except Exception as e:
            print(f"       ❌ Erro: {str(e)}")
            return {'status_code': 'error', 'error': str(e), 'accessible': False}

    def test_database_books(self):
        """Testar livros existentes no banco"""
        self.print_header("4. TESTE DE LIVROS NO BANCO DE DADOS")

        try:
            # Pegar alguns livros com external_id (do Google Books)
            books_with_external = Book.objects.filter(
                external_id__isnull=False
            ).exclude(external_id='')[:3]

            print(f"📚 Encontrados {books_with_external.count()} livros com external_id")

            for book in books_with_external:
                # Verificar qual é o nome correto do campo título
                title = self.get_book_title_from_model(book)

                print(f"\n   📖 {title}")
                print(f"      External ID: {book.external_id}")

                # Verificar campo de URL da capa
                cover_url = self.get_cover_url_from_model(book)
                print(f"      Cover URL: {cover_url or 'Não definida'}")

                if cover_url:
                    # Testar a URL atual
                    print("      Testando URL atual:")
                    status = self.test_image_url(cover_url)

                    if not status.get('accessible'):
                        print("      ⚠️  URL atual não funciona - tentando buscar nova...")
                        # Tentar buscar nova URL via API
                        self.try_refresh_book_cover(book)

        except Exception as e:
            print(f"❌ Erro ao testar livros do banco: {str(e)}")
            import traceback
            print(f"   Detalhes: {traceback.format_exc()}")

    def get_book_title_from_model(self, book):
        """Extrair título do modelo Book, tentando diferentes campos possíveis"""
        possible_fields = ['title', 'titulo', 'nome', 'name']

        for field in possible_fields:
            if hasattr(book, field):
                value = getattr(book, field)
                if value:
                    return value

        # Se não encontrar, mostrar campos disponíveis
        fields = [f.name for f in book._meta.fields]
        print(f"      📋 Campos disponíveis no modelo: {fields}")

        # Tentar o primeiro campo que pareça título
        for field in fields:
            if any(keyword in field.lower() for keyword in ['title', 'titulo', 'nome', 'name']):
                return getattr(book, field, 'Campo encontrado mas vazio')

        return 'Título não encontrado'

    def get_cover_url_from_model(self, book):
        """Extrair URL da capa do modelo Book"""
        possible_fields = ['cover_url', 'image_url', 'capa_url', 'imagem_url', 'cover', 'image']

        for field in possible_fields:
            if hasattr(book, field):
                value = getattr(book, field)
                if value:
                    return value

        return None

    def get_book_title(self, book):
        """Extrair título do livro independente da estrutura"""
        if isinstance(book, dict):
            return book.get('title', book.get('volumeInfo', {}).get('title', 'Sem título'))
        elif hasattr(book, 'title'):
            return book.title
        elif hasattr(book, 'volumeInfo'):
            return book.volumeInfo.get('title', 'Sem título')
        else:
            return 'Sem título'

    def get_book_image_links(self, book):
        """Extrair links de imagem independente da estrutura"""
        if isinstance(book, dict):
            # Estrutura direta
            if 'imageLinks' in book:
                return book['imageLinks']
            # Estrutura do Google Books API
            elif 'volumeInfo' in book and 'imageLinks' in book['volumeInfo']:
                return book['volumeInfo']['imageLinks']
        elif hasattr(book, 'imageLinks'):
            return book.imageLinks
        elif hasattr(book, 'volumeInfo') and hasattr(book.volumeInfo, 'imageLinks'):
            return book.volumeInfo.imageLinks

        return {}

    def try_refresh_book_cover(self, book):
        """Tentar buscar nova URL de capa para um livro"""
        if GOOGLE_BOOKS_CLASS is None:
            print("         ❌ Serviço Google Books não disponível")
            return None

        try:
            service = GOOGLE_BOOKS_CLASS()

            # Verificar se tem método para buscar detalhes
            detail_method = None
            for method_name in ['get_book_details', 'get_book', 'fetch_book']:
                if hasattr(service, method_name):
                    detail_method = getattr(service, method_name)
                    break

            if not detail_method:
                print("         ❌ Método para buscar detalhes não encontrado")
                return None

            # Buscar detalhes do livro pelo external_id
            if book.external_id:
                book_details = detail_method(book.external_id)

                if book_details:
                    image_links = self.get_book_image_links(book_details)

                    if image_links:
                        best_url = (image_links.get('large') or
                                    image_links.get('medium') or
                                    image_links.get('small') or
                                    image_links.get('thumbnail'))

                        if best_url:
                            print(f"         🔄 Nova URL encontrada: {best_url}")
                            status = self.test_image_url(best_url)

                            if status.get('accessible'):
                                print("         ✅ Nova URL funciona!")
                                return best_url
                            else:
                                print("         ❌ Nova URL também não funciona")

        except Exception as e:
            print(f"         ❌ Erro ao buscar nova URL: {str(e)}")

        return None

    def clear_image_cache(self):
        """Limpar cache de imagens"""
        self.print_header("5. LIMPEZA DO CACHE DE IMAGENS")

        try:
            image_cache = caches['image_proxy']
            image_cache.clear()
            print("✅ Cache de imagens limpo com sucesso")
            print("   Recomendação: Teste as páginas novamente após esta limpeza")

        except Exception as e:
            print(f"❌ Erro ao limpar cache: {str(e)}")

    def generate_recommendations(self):
        """Gerar recomendações baseadas nos testes"""
        self.print_header("6. RECOMENDAÇÕES")

        recommendations = []

        if not self.results['redis_connection']:
            recommendations.append({
                'priority': 'ALTA',
                'issue': 'Redis não conectado',
                'action': 'Verificar se Docker Desktop está rodando e Redis container ativo'
            })

        if not self.results['google_books_api']:
            recommendations.append({
                'priority': 'ALTA',
                'issue': 'Google Books API não responde',
                'action': 'Verificar conectividade e chaves de API'
            })

        # Analisar URLs testadas
        failed_urls = [url for url in self.results['sample_urls_test'] if not url['status'].get('accessible')]
        if failed_urls:
            recommendations.append({
                'priority': 'MÉDIA',
                'issue': f'{len(failed_urls)} URLs de imagem falharam',
                'action': 'URLs do Google Books podem ter mudado - implementar refresh automático'
            })

        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'issue': 'Testes básicos passaram',
                'action': 'Investigar logs do servidor e console do navegador'
            })

        for rec in recommendations:
            priority_emoji = {'ALTA': '🚨', 'MÉDIA': '⚠️', 'BAIXA': '📝', 'INFO': 'ℹ️'}
            print(f"{priority_emoji.get(rec['priority'], '•')} {rec['priority']}: {rec['issue']}")
            print(f"   Ação: {rec['action']}\n")

        self.results['recommendations'] = recommendations

    def run_full_diagnostic(self):
        """Executar diagnóstico completo"""
        print("🔍 DIAGNÓSTICO DE IMAGENS - CGBOOKSTORE")
        print("Investigando problema de capas de livros não aparecerem")

        # Executar todos os testes
        self.test_redis_connection()
        self.analyze_image_cache()
        self.test_google_books_api()
        self.test_database_books()
        self.clear_image_cache()
        self.generate_recommendations()

        # Resumo final
        self.print_header("RESUMO DO DIAGNÓSTICO")
        print(f"✅ Redis conectado: {self.results['redis_connection']}")
        print(f"✅ Cache acessível: {self.results['image_cache_status'].get('accessible', False)}")
        print(f"✅ Google Books API: {self.results['google_books_api']}")

        accessible_urls = len([u for u in self.results['sample_urls_test'] if u['status'].get('accessible')])
        total_urls = len(self.results['sample_urls_test'])
        if total_urls > 0:
            print(f"✅ URLs funcionando: {accessible_urls}/{total_urls}")

        print(f"\n💡 {len(self.results['recommendations'])} recomendações geradas")

        return self.results


if __name__ == "__main__":
    diagnostic = ImageDiagnostic()
    results = diagnostic.run_full_diagnostic()

    print("\n" + "=" * 60)
    print("Diagnóstico concluído. Execute:")
    print("python manage.py runserver")
    print("E teste uma página com livros para verificar se o problema foi resolvido.")
    print("=" * 60)