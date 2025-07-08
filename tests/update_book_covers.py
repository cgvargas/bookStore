#!/usr/bin/env python
"""
Script de Atualização de Capas - Buscar URLs de capa para livros sem capa_url
Arquivo: tests/update_book_covers.py
Objetivo: Buscar e atualizar URLs de capa do Google Books para livros que não têm
"""

import os
import sys
import django
import requests
import time
from pathlib import Path

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from cgbookstore.apps.core.models import Book
from django.db.models import Q
from django.db import transaction

# Importar serviços disponíveis
try:
    from cgbookstore.apps.core.services.google_books_service import GoogleBooksService

    GOOGLE_BOOKS_CLASS = GoogleBooksService
except ImportError:
    try:
        from cgbookstore.apps.core.services.google_books_client import GoogleBooksClient

        GOOGLE_BOOKS_CLASS = GoogleBooksClient
    except ImportError:
        GOOGLE_BOOKS_CLASS = None


class BookCoverUpdater:
    def __init__(self):
        self.results = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'skipped': 0,
            'errors': [],
            'updated_books': []
        }
        self.service = None

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def initialize_service(self):
        """Inicializar serviço do Google Books"""
        self.print_header("INICIALIZANDO SERVIÇO GOOGLE BOOKS")

        if GOOGLE_BOOKS_CLASS is None:
            print("❌ Classe do Google Books não encontrada")
            return False

        try:
            self.service = GOOGLE_BOOKS_CLASS()
            print(f"✅ Serviço inicializado: {GOOGLE_BOOKS_CLASS.__name__}")

            # Verificar todos os métodos disponíveis
            available_methods = [method for method in dir(self.service) if not method.startswith('_')]
            print(f"📋 Métodos disponíveis: {available_methods}")

            # Verificar se tem método para buscar detalhes
            detail_methods = ['get_book_details', 'get_book', 'fetch_book', 'get_volume_info', 'fetch_volume']
            self.detail_method = None

            for method_name in detail_methods:
                if hasattr(self.service, method_name):
                    self.detail_method = getattr(self.service, method_name)
                    print(f"✅ Método de detalhes encontrado: {method_name}")
                    break

            if not self.detail_method:
                print("⚠️ Método específico não encontrado, tentando implementação direta")
                # Implementar método direto se a classe não tiver
                self.detail_method = self.direct_api_call
                return True

            return True

        except Exception as e:
            print(f"❌ Erro ao inicializar serviço: {str(e)}")
            return False

    def direct_api_call(self, book_id):
        """Implementação direta da chamada à API do Google Books"""
        try:
            import requests

            url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
            print(f"   🌐 Fazendo chamada direta: {url}")

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print("   ✅ Dados recebidos da API")
                return data
            else:
                print(f"   ❌ API retornou status {response.status_code}")
                return None

        except Exception as e:
            print(f"   ❌ Erro na chamada direta: {str(e)}")
            return None

    def find_books_needing_covers(self):
        """Encontrar livros que precisam de URLs de capa"""
        self.print_header("IDENTIFICANDO LIVROS QUE PRECISAM DE CAPAS")

        # Livros com external_id mas sem capa_url
        books_without_cover_url = Book.objects.filter(
            Q(external_id__isnull=False) &
            ~Q(external_id='') &
            (Q(capa_url='') | Q(capa_url__isnull=True))
        )

        print(f"📚 Livros com external_id sem capa_url: {books_without_cover_url.count()}")

        # Livros temporários sem capa_url (estes são críticos)
        temp_books_without_cover = books_without_cover_url.filter(is_temporary=True)
        print(f"⏳ Livros temporários sem capa: {temp_books_without_cover.count()}")

        # Livros com capa_url quebrada (opcional - para verificação futura)
        # books_with_broken_urls = Book.objects.exclude(
        #     Q(capa_url='') | Q(capa_url__isnull=True)
        # ).filter(external_id__isnull=False)

        return books_without_cover_url

    def test_image_url(self, url, timeout=10):
        """Testar se uma URL de imagem é válida"""
        if not url:
            return False

        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200 and 'image' in response.headers.get('content-type', '')
        except:
            return False

    def extract_image_urls_from_book_data(self, book_data):
        """Extrair URLs de imagem dos dados do livro"""
        image_urls = {}

        if not book_data:
            return image_urls

        # Tentar diferentes estruturas
        image_sources = []

        # Estrutura direta
        if isinstance(book_data, dict) and 'imageLinks' in book_data:
            image_sources.append(book_data['imageLinks'])

        # Estrutura Google Books API (volumeInfo)
        if isinstance(book_data, dict) and 'volumeInfo' in book_data:
            volume_info = book_data['volumeInfo']
            if 'imageLinks' in volume_info:
                image_sources.append(volume_info['imageLinks'])

        # Processar todos os image_sources encontrados
        for image_links in image_sources:
            if isinstance(image_links, dict):
                for size, url in image_links.items():
                    if url and isinstance(url, str):
                        image_urls[size] = url

        return image_urls

    def get_best_image_url(self, image_urls):
        """Selecionar a melhor URL de imagem disponível"""
        if not image_urls:
            return None

        # Ordem de preferência por qualidade
        preferred_sizes = ['extraLarge', 'large', 'medium', 'small', 'thumbnail']

        for size in preferred_sizes:
            if size in image_urls:
                url = image_urls[size]
                # Testar se a URL funciona
                if self.test_image_url(url):
                    return url

        # Se nenhuma das preferidas funcionar, testar todas
        for size, url in image_urls.items():
            if self.test_image_url(url):
                return url

        return None

    def update_single_book(self, book):
        """Atualizar URL de capa de um livro específico"""
        try:
            print(f"\n📖 Processando: {book.titulo} (ID: {book.id})")
            print(f"   External ID: {book.external_id}")

            # Buscar dados do livro na API
            try:
                book_data = self.detail_method(book.external_id)
            except TypeError as e:
                # Se der erro de assinatura, tentar sem parâmetros
                print(f"   ⚠️ Erro de assinatura, tentando abordagem alternativa: {str(e)}")
                book_data = self.direct_api_call(book.external_id)

            if not book_data:
                print("   ❌ Nenhum dado retornado da API")
                return False

            # Extrair URLs de imagem
            image_urls = self.extract_image_urls_from_book_data(book_data)

            if not image_urls:
                print("   ⚠️ Nenhuma URL de imagem encontrada nos dados")
                # Debug: mostrar estrutura dos dados
                if isinstance(book_data, dict):
                    print(f"   📋 Chaves disponíveis: {list(book_data.keys())}")
                    if 'volumeInfo' in book_data:
                        volume_keys = list(book_data['volumeInfo'].keys()) if isinstance(book_data['volumeInfo'],
                                                                                         dict) else []
                        print(f"   📋 Chaves volumeInfo: {volume_keys}")
                return False

            print(f"   🖼️ URLs encontradas: {list(image_urls.keys())}")
            for size, url in image_urls.items():
                print(f"      {size}: {url[:60]}...")

            # Selecionar a melhor URL
            best_url = self.get_best_image_url(image_urls)

            if not best_url:
                print("   ❌ Nenhuma URL de imagem válida")
                return False

            print(f"   ✅ Melhor URL selecionada: {best_url[:80]}...")

            # Verificar se deve salvar (modo de teste vs produção)
            if hasattr(self, 'test_mode') and self.test_mode:
                print("   🧪 MODO TESTE - Não salvando no banco")
            else:
                # Atualizar o livro
                book.capa_url = best_url
                book.save(update_fields=['capa_url'])
                print("   💾 Livro atualizado com sucesso!")

            self.results['updated_books'].append({
                'id': book.id,
                'titulo': book.titulo,
                'external_id': book.external_id,
                'new_capa_url': best_url
            })

            return True

        except Exception as e:
            error_msg = f"Erro ao processar livro {book.id}: {str(e)}"
            print(f"   ❌ {error_msg}")
            self.results['errors'].append(error_msg)
            import traceback
            print(f"   📋 Detalhes: {traceback.format_exc()}")
            return False

    def update_books_batch(self, books, batch_size=10, delay=1.0):
        """Atualizar livros em lotes com delay para evitar rate limiting"""
        self.print_header("ATUALIZANDO URLS DE CAPA DOS LIVROS")

        total_books = len(books)
        print(f"📚 Total de livros a processar: {total_books}")
        print(f"📦 Tamanho do lote: {batch_size}")
        print(f"⏱️ Delay entre requisições: {delay}s")

        for i, book in enumerate(books):
            self.results['total_processed'] += 1

            print(f"\n🔄 Progresso: {i + 1}/{total_books}")

            try:
                # Atualizar o livro
                success = self.update_single_book(book)

                if success:
                    self.results['successful_updates'] += 1
                else:
                    self.results['failed_updates'] += 1

                # Delay entre requisições
                if i < total_books - 1:  # Não fazer delay na última iteração
                    time.sleep(delay)

            except KeyboardInterrupt:
                print("\n\n⚠️ Processo interrompido pelo usuário")
                break
            except Exception as e:
                self.results['failed_updates'] += 1
                error_msg = f"Erro inesperado no livro {book.id}: {str(e)}"
                print(f"   ❌ {error_msg}")
                self.results['errors'].append(error_msg)

    def verify_updates(self):
        """Verificar se as atualizações foram bem-sucedidas"""
        self.print_header("VERIFICAÇÃO DAS ATUALIZAÇÕES")

        if not self.results['updated_books']:
            print("❌ Nenhum livro foi atualizado")
            return

        print(f"✅ {len(self.results['updated_books'])} livros atualizados")

        # Verificar alguns livros atualizados
        for book_info in self.results['updated_books'][:3]:  # Verificar os primeiros 3
            try:
                book = Book.objects.get(id=book_info['id'])
                current_url = book.get_capa_url()

                print(f"\n📖 {book.titulo}:")
                print(f"   URL salva: {book.capa_url[:80]}...")
                print(f"   get_capa_url(): {current_url[:80] if current_url else 'None'}...")

                # Testar se a URL ainda funciona
                if self.test_image_url(book.capa_url):
                    print("   ✅ URL funcionando!")
                else:
                    print("   ⚠️ URL não responde (pode ser temporário)")

            except Exception as e:
                print(f"   ❌ Erro na verificação: {str(e)}")

    def generate_summary_report(self):
        """Gerar relatório final do processo"""
        self.print_header("RELATÓRIO FINAL")

        print(f"📊 Estatísticas do Processo:")
        print(f"   Total processados: {self.results['total_processed']}")
        print(f"   ✅ Atualizações bem-sucedidas: {self.results['successful_updates']}")
        print(f"   ❌ Falhas: {self.results['failed_updates']}")
        print(f"   ⏭️ Ignorados: {self.results['skipped']}")

        if self.results['successful_updates'] > 0:
            success_rate = (self.results['successful_updates'] / self.results['total_processed']) * 100
            print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")

        if self.results['errors']:
            print(f"\n❌ Erros encontrados ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Mostrar apenas os primeiros 5
                print(f"   • {error}")
            if len(self.results['errors']) > 5:
                print(f"   ... e mais {len(self.results['errors']) - 5} erros")

        # Recomendações
        print(f"\n💡 Próximos Passos:")
        if self.results['successful_updates'] > 0:
            print("   ✅ Execute o diagnóstico frontend novamente para verificar melhorias")
            print("   ✅ Teste as páginas no navegador para confirmar que as imagens aparecem")

        if self.results['failed_updates'] > 0:
            print("   ⚠️ Alguns livros falharam - verifique os external_ids")
            print("   ⚠️ Considere executar novamente para os livros que falharam")

    def run_update_process(self, limit=None, test_mode=False):
        """Executar processo completo de atualização"""
        print("🔄 SCRIPT DE ATUALIZAÇÃO DE CAPAS DE LIVROS")
        print("Buscando URLs de capa do Google Books para livros sem capa_url")

        # Salvar modo de teste na instância
        self.test_mode = test_mode

        if test_mode:
            print("🧪 MODO DE TESTE - Nenhuma alteração será salva no banco")

        # Inicializar serviço
        if not self.initialize_service():
            print("❌ Não foi possível inicializar o serviço. Abortando.")
            return False

        # Encontrar livros que precisam de atualização
        books_to_update = self.find_books_needing_covers()

        if not books_to_update.exists():
            print("✅ Todos os livros já têm URLs de capa configuradas!")
            return True

        # Aplicar limite se especificado
        if limit:
            books_to_update = books_to_update[:limit]
            print(f"📏 Limitando a {limit} livros para este teste")

        # Converter para lista
        books_list = list(books_to_update)

        if not test_mode:
            # Confirmar antes de prosseguir
            response = input(f"\n⚠️ Isso irá atualizar {len(books_list)} livros. Continuar? (s/N): ")
            if response.lower() not in ['s', 'sim', 'yes', 'y']:
                print("❌ Processo cancelado pelo usuário")
                return False

        # Atualizar livros
        self.update_books_batch(books_list)

        # Verificar atualizações (apenas se não for modo teste)
        if not test_mode and self.results['successful_updates'] > 0:
            self.verify_updates()

        # Relatório final
        self.generate_summary_report()

        return self.results['successful_updates'] > 0


if __name__ == "__main__":
    updater = BookCoverUpdater()

    # Parâmetros do script
    TEST_MODE = False  # Mude para True para teste sem salvar
    LIMIT = None  # Limite de livros (None = todos)

    # Para teste inicial, recomendo começar com poucos livros
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        TEST_MODE = True
        LIMIT = 5
        print("🧪 Executando em modo de teste com 5 livros")

    # Executar atualização
    success = updater.run_update_process(limit=LIMIT, test_mode=TEST_MODE)

    if success:
        print("\n🎉 Processo concluído com sucesso!")
        print("Execute 'python tests/frontend_image_diagnostic.py' para verificar melhorias")
    else:
        print("\n❌ Processo falhou ou foi cancelado")

    print("\n" + "=" * 60)