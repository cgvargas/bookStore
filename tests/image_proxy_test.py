#!/usr/bin/env python
"""
Script de Teste do Image Proxy - URLs do Google Books
Arquivo: tests/image_proxy_test.py
Objetivo: Testar especificamente o funcionamento do image proxy com URLs reais
"""

import os
import sys
import django
import requests
from urllib.parse import urlencode, quote

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from cgbookstore.apps.core.models import Book
from django.db.models import Q


class ImageProxyTester:
    def __init__(self):
        self.client = Client()
        self.results = {
            'direct_urls_test': [],
            'proxy_tests': [],
            'proxy_errors': [],
            'working_urls': [],
            'broken_urls': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def get_google_books_urls(self):
        """Obter URLs reais do Google Books do banco"""
        self.print_header("1. COLETANDO URLS REAIS DO GOOGLE BOOKS")

        # Pegar livros com URLs do Google Books
        google_books = Book.objects.filter(
            capa_url__icontains='books.google.com'
        ).exclude(capa_url='')[:5]

        urls = []
        for book in google_books:
            urls.append({
                'book_title': book.titulo,
                'book_id': book.id,
                'external_id': book.external_id,
                'capa_url': book.capa_url,
                'is_temporary': book.is_temporary
            })
            print(f"📖 {book.titulo}")
            print(f"   URL: {book.capa_url}")
            print(f"   External ID: {book.external_id}")
            print(f"   Temporário: {book.is_temporary}")

        print(f"\n✅ Coletadas {len(urls)} URLs do Google Books para teste")
        return urls

    def test_direct_url_access(self, urls):
        """Testar acesso direto às URLs do Google Books"""
        self.print_header("2. TESTE DE ACESSO DIRETO ÀS URLS")

        for url_info in urls:
            url = url_info['capa_url']
            print(f"\n📖 Testando: {url_info['book_title']}")
            print(f"🔗 URL: {url}")

            try:
                # Testar acesso direto
                response = requests.get(url, timeout=10, allow_redirects=True)

                status_info = {
                    'url': url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', 'unknown'),
                    'content_length': len(response.content),
                    'accessible': response.status_code == 200
                }

                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {status_info['content_type']}")
                print(f"   Tamanho: {status_info['content_length']} bytes")

                if response.status_code == 200:
                    if 'image' in status_info['content_type']:
                        print("   ✅ URL funcionando - imagem válida")
                        self.results['working_urls'].append(url_info)
                    else:
                        print("   ⚠️ URL responde mas não é imagem")
                else:
                    print(f"   ❌ URL não funciona: {response.status_code}")
                    self.results['broken_urls'].append(url_info)

                self.results['direct_urls_test'].append(status_info)

            except Exception as e:
                print(f"   ❌ Erro no acesso: {str(e)}")
                self.results['broken_urls'].append(url_info)

    def test_image_proxy_endpoint(self, urls):
        """Testar o endpoint do image proxy do Django"""
        self.print_header("3. TESTE DO ENDPOINT IMAGE PROXY")

        # Verificar se a URL do proxy existe
        try:
            proxy_url_name = 'image_proxy'  # ou o nome correto da URL
            proxy_base_url = reverse(proxy_url_name)
            print(f"✅ URL do proxy encontrada: {proxy_base_url}")
        except:
            # Tentar nomes alternativos
            possible_names = ['image_proxy', 'google_books_image_proxy', 'proxy_image']
            proxy_base_url = None

            for name in possible_names:
                try:
                    proxy_base_url = reverse(name)
                    print(f"✅ URL do proxy encontrada: {proxy_base_url} (nome: {name})")
                    break
                except:
                    continue

            if not proxy_base_url:
                print("❌ URL do proxy não encontrada")
                return

        # Testar cada URL através do proxy
        for url_info in urls:
            original_url = url_info['capa_url']
            print(f"\n📖 Testando proxy para: {url_info['book_title']}")

            # Diferentes formas de construir a URL do proxy
            proxy_variations = [
                f"{proxy_base_url}?url={quote(original_url)}",
                f"{proxy_base_url}?{urlencode({'url': original_url})}",
                f"{proxy_base_url}?url={original_url}",
            ]

            for i, proxy_url in enumerate(proxy_variations):
                print(f"\n   🧪 Variação {i + 1}: {proxy_url[:100]}...")

                try:
                    response = self.client.get(proxy_url)

                    test_result = {
                        'book_title': url_info['book_title'],
                        'original_url': original_url,
                        'proxy_url': proxy_url,
                        'status_code': response.status_code,
                        'content_type': response.get('Content-Type', 'unknown'),
                        'working': response.status_code == 200
                    }

                    print(f"      Status: {response.status_code}")
                    if hasattr(response, 'content'):
                        print(f"      Tamanho resposta: {len(response.content)} bytes")

                    if response.status_code == 200:
                        content_type = response.get('Content-Type', '')
                        if 'image' in content_type:
                            print("      ✅ Proxy funcionando - imagem retornada!")
                            break
                        else:
                            print(f"      ⚠️ Proxy responde mas Content-Type: {content_type}")
                    else:
                        print(f"      ❌ Proxy falhou: {response.status_code}")

                        # Se for 404 ou 500, mostrar conteúdo da resposta para debug
                        if response.status_code in [404, 500] and hasattr(response, 'content'):
                            content_preview = response.content.decode('utf-8', errors='ignore')[:200]
                            print(f"      📋 Preview da resposta: {content_preview}...")

                    self.results['proxy_tests'].append(test_result)

                except Exception as e:
                    error_msg = f"Erro no proxy para {url_info['book_title']}: {str(e)}"
                    print(f"      ❌ {error_msg}")
                    self.results['proxy_errors'].append(error_msg)

    def test_proxy_with_working_url(self):
        """Testar proxy com uma URL que sabemos que funciona"""
        self.print_header("4. TESTE COM URL CONHECIDAMENTE FUNCIONAL")

        # URL de teste conhecida
        test_url = "https://books.google.com/books/content?id=8JLnDwAAQBAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api&edge=curl"

        print(f"🧪 Testando com URL específica:")
        print(f"   {test_url}")

        # Testar acesso direto primeiro
        try:
            direct_response = requests.get(test_url, timeout=10)
            print(f"\n📊 Acesso direto:")
            print(f"   Status: {direct_response.status_code}")
            print(f"   Content-Type: {direct_response.headers.get('content-type')}")
            print(f"   Tamanho: {len(direct_response.content)} bytes")

            if direct_response.status_code == 200:
                print("   ✅ URL funciona diretamente")

                # Agora testar via proxy
                try:
                    proxy_url = reverse('image_proxy') + '?' + urlencode({'url': test_url})
                    print(f"\n🔄 Testando via proxy:")
                    print(f"   Proxy URL: {proxy_url[:100]}...")

                    proxy_response = self.client.get(proxy_url)
                    print(f"   Status proxy: {proxy_response.status_code}")

                    if proxy_response.status_code == 200:
                        print("   ✅ Proxy também funciona!")
                    else:
                        print(f"   ❌ Proxy falhou: {proxy_response.status_code}")

                        # Tentar capturar erro detalhado
                        if hasattr(proxy_response, 'content'):
                            error_content = proxy_response.content.decode('utf-8', errors='ignore')[:500]
                            print(f"   📋 Erro detalhado: {error_content}")

                except Exception as e:
                    print(f"   ❌ Erro no teste do proxy: {str(e)}")

            else:
                print(f"   ❌ URL não funciona diretamente: {direct_response.status_code}")

        except Exception as e:
            print(f"   ❌ Erro no acesso direto: {str(e)}")

    def check_proxy_view_file(self):
        """Verificar o arquivo da view do proxy"""
        self.print_header("5. ANÁLISE DO ARQUIVO IMAGE_PROXY.PY")

        import os
        proxy_file = "cgbookstore/apps/core/views/image_proxy.py"

        if os.path.exists(proxy_file):
            print(f"✅ Arquivo encontrado: {proxy_file}")

            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"📄 Tamanho: {len(content)} caracteres")

                # Procurar por possíveis problemas
                issues = []

                if 'def google_books_image_proxy' in content:
                    print("✅ Função google_books_image_proxy encontrada")
                else:
                    issues.append("Função principal não encontrada")

                if 'requests.get' in content:
                    print("✅ Chamada requests.get encontrada")
                else:
                    issues.append("Chamada HTTP não encontrada")

                if 'HttpResponse' in content:
                    print("✅ HttpResponse importado")
                else:
                    issues.append("HttpResponse não importado")

                # Verificar por tratamento de erro
                if 'except' in content:
                    print("✅ Tratamento de erro presente")
                else:
                    issues.append("Sem tratamento de erro")

                if issues:
                    print(f"\n⚠️ Possíveis problemas encontrados:")
                    for issue in issues:
                        print(f"   • {issue}")
                else:
                    print("\n✅ Estrutura básica do arquivo parece OK")

            except Exception as e:
                print(f"❌ Erro ao ler arquivo: {str(e)}")
        else:
            print(f"❌ Arquivo não encontrado: {proxy_file}")

    def generate_summary_report(self):
        """Gerar relatório final"""
        self.print_header("6. RELATÓRIO FINAL DO TESTE")

        print(f"📊 Estatísticas:")
        print(f"   URLs testadas diretamente: {len(self.results['direct_urls_test'])}")
        print(f"   Testes de proxy realizados: {len(self.results['proxy_tests'])}")
        print(f"   URLs funcionais: {len(self.results['working_urls'])}")
        print(f"   URLs quebradas: {len(self.results['broken_urls'])}")
        print(f"   Erros de proxy: {len(self.results['proxy_errors'])}")

        # Análise dos resultados
        if self.results['working_urls'] and not any(test['working'] for test in self.results['proxy_tests']):
            print(f"\n🚨 PROBLEMA IDENTIFICADO:")
            print(f"   ✅ URLs do Google Books funcionam diretamente")
            print(f"   ❌ Image Proxy não está funcionando")
            print(f"   💡 Solução: Corrigir implementação do image proxy")

        elif not self.results['working_urls']:
            print(f"\n⚠️ PROBLEMA NAS URLS:")
            print(f"   ❌ URLs do Google Books não funcionam diretamente")
            print(f"   💡 Solução: URLs precisam ser atualizadas")

        elif any(test['working'] for test in self.results['proxy_tests']):
            print(f"\n✅ TUDO FUNCIONANDO:")
            print(f"   ✅ URLs funcionam diretamente")
            print(f"   ✅ Image Proxy funciona")
            print(f"   💡 Problema pode ser no template/frontend")

        # Mostrar erros específicos
        if self.results['proxy_errors']:
            print(f"\n❌ Erros de Proxy:")
            for error in self.results['proxy_errors'][:3]:
                print(f"   • {error}")

    def run_complete_test(self):
        """Executar teste completo do image proxy"""
        print("🔍 TESTE ESPECÍFICO DO IMAGE PROXY")
        print("Verificando funcionamento com URLs reais do Google Books")

        # Coletar URLs
        urls = self.get_google_books_urls()

        if not urls:
            print("❌ Nenhuma URL do Google Books encontrada no banco")
            return False

        # Executar testes
        self.test_direct_url_access(urls)
        self.test_image_proxy_endpoint(urls)
        self.test_proxy_with_working_url()
        self.check_proxy_view_file()
        self.generate_summary_report()

        return True


if __name__ == "__main__":
    tester = ImageProxyTester()
    tester.run_complete_test()

    print("\n" + "=" * 60)
    print("Teste do image proxy concluído.")
    print("Use os resultados para identificar o problema específico.")
    print("=" * 60)