#!/usr/bin/env python
"""
Script de Teste de Renderização de Templates - Livros do Google Books
Arquivo: tests/template_render_test.py
Objetivo: Testar como os templates estão renderizando as imagens dos livros do Google Books
"""

import os
import sys
import django
import re
from pathlib import Path

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.template.loader import render_to_string
from django.template import Context, Template
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models import Book
from django.urls import reverse
from django.db.models import Q

User = get_user_model()


class TemplateRenderTester:
    def __init__(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.results = {
            'template_tests': [],
            'html_analysis': {},
            'image_urls_found': [],
            'proxy_urls_generated': [],
            'issues_found': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def get_google_books_samples(self):
        """Obter amostras de livros do Google Books"""
        self.print_header("1. COLETANDO LIVROS DO GOOGLE BOOKS PARA TESTE")

        google_books = Book.objects.filter(
            capa_url__icontains='books.google.com'
        ).exclude(capa_url='')[:3]

        samples = []
        for book in google_books:
            samples.append(book)
            print(f"📖 {book.titulo}")
            print(f"   ID: {book.id}")
            print(f"   capa_url: {book.capa_url[:80]}...")
            print(f"   get_capa_url(): {book.get_capa_url()[:80]}...")
            print(f"   is_temporary: {book.is_temporary}")

        return samples

    def test_book_cover_template(self, books):
        """Testar template book_cover.html especificamente"""
        self.print_header("2. TESTE DO TEMPLATE BOOK_COVER.HTML")

        template_path = "core/components/book_cover.html"

        for book in books:
            print(f"\n📖 Testando renderização: {book.titulo}")

            try:
                # Contexto similar ao usado na aplicação
                context = {
                    'book': book,
                    'size': 'medium',
                    'thumbnail': book.get_capa_url(),
                    'title': book.titulo
                }

                # Renderizar template
                html = render_to_string(template_path, context)

                print(f"   ✅ Template renderizado com sucesso")
                print(f"   📏 Tamanho HTML: {len(html)} caracteres")

                # Analisar o HTML gerado
                self.analyze_rendered_html(html, book, "book_cover.html")

            except Exception as e:
                print(f"   ❌ Erro na renderização: {str(e)}")
                self.results['issues_found'].append(f"Erro renderizando {book.titulo}: {str(e)}")

    def test_book_card_template(self, books):
        """Testar template book_card.html"""
        self.print_header("3. TESTE DO TEMPLATE BOOK_CARD.HTML")

        template_path = "core/includes/book_card.html"

        for book in books:
            print(f"\n📖 Testando book_card: {book.titulo}")

            try:
                context = {
                    'livro': book,  # Note: book_card usa 'livro' em vez de 'book'
                }

                html = render_to_string(template_path, context)

                print(f"   ✅ Template renderizado")
                print(f"   📏 Tamanho: {len(html)} caracteres")

                self.analyze_rendered_html(html, book, "book_card.html")

            except Exception as e:
                print(f"   ❌ Erro: {str(e)}")
                self.results['issues_found'].append(f"Erro book_card {book.titulo}: {str(e)}")

    def analyze_rendered_html(self, html, book, template_name):
        """Analisar HTML renderizado em busca de problemas"""
        print(f"   🔍 Analisando HTML gerado...")

        # Procurar por tags img
        img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
        print(f"   🖼️ Tags <img> encontradas: {len(img_tags)}")

        analysis = {
            'template': template_name,
            'book_title': book.titulo,
            'img_tags_count': len(img_tags),
            'img_tags': img_tags,
            'proxy_urls': [],
            'direct_urls': [],
            'placeholder_urls': [],
            'empty_srcs': []
        }

        # Analisar cada tag img
        for i, tag in enumerate(img_tags):
            print(f"      {i + 1}. {tag}")

            # Extrair src
            src_match = re.search(r'src=["\']([^"\']*)["\']', tag)
            if src_match:
                src = src_match.group(1)

                if '/image-proxy/' in src:
                    analysis['proxy_urls'].append(src)
                    print(f"         📡 Proxy URL: {src[:60]}...")
                elif 'books.google.com' in src:
                    analysis['direct_urls'].append(src)
                    print(f"         🔗 URL Direta: {src[:60]}...")
                elif 'no-cover.svg' in src or 'placeholder' in src:
                    analysis['placeholder_urls'].append(src)
                    print(f"         🚫 Placeholder: {src}")
                elif not src or src.strip() == '':
                    analysis['empty_srcs'].append(tag)
                    print(f"         ⚠️ SRC vazio!")
                else:
                    print(f"         📄 Outro: {src[:60]}...")
            else:
                print(f"         ❌ SRC não encontrado na tag!")
                analysis['empty_srcs'].append(tag)

        # Procurar por construção específica do proxy
        proxy_constructions = re.findall(r'{%\s*url\s+["\']image_proxy["\'][^%]*%}', html)
        if proxy_constructions:
            print(f"   🔧 Construções de URL do proxy encontradas: {len(proxy_constructions)}")
            for construct in proxy_constructions:
                print(f"      {construct}")

        # Verificar variáveis Django não resolvidas
        unresolved_vars = re.findall(r'{{\s*[^}]+\s*}}', html)
        if unresolved_vars:
            print(f"   ⚠️ Variáveis não resolvidas: {unresolved_vars}")

        self.results['template_tests'].append(analysis)

    def test_home_page_rendering(self):
        """Testar renderização da página home completa"""
        self.print_header("4. TESTE DA PÁGINA HOME COMPLETA")

        try:
            # Simular request autenticado
            user = User.objects.first()
            if user:
                self.client.force_login(user)
                print(f"✅ Usuário logado: {user.username}")

            # Fazer request para home
            response = self.client.get('/')

            print(f"📊 Status: {response.status_code}")

            if response.status_code == 200:
                html = response.content.decode('utf-8')
                print(f"📏 Tamanho HTML: {len(html)} caracteres")

                # Analisar seção de recomendações
                self.analyze_recommendations_section(html)

                # Procurar por livros do Google Books especificamente
                google_books_sections = re.findall(r'Google Books[^<]*<[^>]*>[^<]*<[^>]*>([^<]*)', html, re.IGNORECASE)
                print(f"🔍 Seções 'Google Books' encontradas: {len(google_books_sections)}")

            else:
                print(f"❌ Página não carregou: {response.status_code}")

        except Exception as e:
            print(f"❌ Erro no teste da home: {str(e)}")

    def analyze_recommendations_section(self, html):
        """Analisar especificamente a seção de recomendações"""
        print(f"\n   🎯 Analisando seção de recomendações:")

        # Procurar pela seção de recomendações
        recommendations_pattern = r'<.*?[Rr]ecomenda.*?</.*?>'
        recommendations_sections = re.findall(recommendations_pattern, html, re.DOTALL)

        if recommendations_sections:
            print(f"   📋 Seções de recomendação encontradas: {len(recommendations_sections)}")

            # Analisar primeira seção
            first_section = recommendations_sections[0]
            img_tags_in_recommendations = re.findall(r'<img[^>]*>', first_section, re.IGNORECASE)
            print(f"   🖼️ Imagens na seção de recomendações: {len(img_tags_in_recommendations)}")

            for i, tag in enumerate(img_tags_in_recommendations[:3]):  # Primeiras 3
                print(f"      {i + 1}. {tag[:100]}...")

        # Procurar especificamente por dados de livros temporários
        temp_book_pattern = r'data-[^=]*temp[^=]*=["\']true["\']'
        temp_books = re.findall(temp_book_pattern, html, re.IGNORECASE)
        if temp_books:
            print(f"   ⏳ Livros temporários encontrados: {len(temp_books)}")

    def test_specific_book_rendering(self, books):
        """Testar renderização de livro específico"""
        self.print_header("5. TESTE DE RENDERIZAÇÃO INDIVIDUAL")

        for book in books:
            print(f"\n📖 Teste individual: {book.titulo}")

            # Testar diferentes contextos
            contexts_to_test = [
                {
                    'name': 'Context 1 - book',
                    'context': {'book': book}
                },
                {
                    'name': 'Context 2 - livro',
                    'context': {'livro': book}
                },
                {
                    'name': 'Context 3 - completo',
                    'context': {
                        'book': book,
                        'livro': book,
                        'thumbnail': book.get_capa_url(),
                        'title': book.titulo,
                        'size': 'medium'
                    }
                }
            ]

            # Template simples para teste
            test_template = """
            <div class="test-book">
                <h3>{{ book.titulo|default:livro.titulo }}</h3>
                <img src="{% url 'image_proxy' %}?url={{ book.capa_url|urlencode }}" alt="Test">
                <img src="{{ book.get_capa_url }}" alt="Direct">
                <p>Temporary: {{ book.is_temporary }}</p>
            </div>
            """

            for context_info in contexts_to_test:
                try:
                    template = Template(test_template)
                    context = Context(context_info['context'])

                    html = template.render(context)

                    print(f"   ✅ {context_info['name']}: Renderizado")

                    # Verificar se URLs foram geradas
                    if '/image-proxy/' in html:
                        print(f"      🔧 URL do proxy gerada")
                    if book.capa_url in html:
                        print(f"      🔗 URL direta presente")

                except Exception as e:
                    print(f"   ❌ {context_info['name']}: {str(e)}")

    def generate_final_diagnosis(self):
        """Gerar diagnóstico final baseado nos testes"""
        self.print_header("6. DIAGNÓSTICO FINAL")

        print(f"📊 Resumo dos Testes:")
        print(f"   Templates testados: {len(self.results['template_tests'])}")
        print(f"   Problemas encontrados: {len(self.results['issues_found'])}")

        # Analisar padrões
        total_img_tags = sum(t['img_tags_count'] for t in self.results['template_tests'])
        total_proxy_urls = sum(len(t['proxy_urls']) for t in self.results['template_tests'])
        total_empty_srcs = sum(len(t['empty_srcs']) for t in self.results['template_tests'])

        print(f"   Total tags <img>: {total_img_tags}")
        print(f"   URLs de proxy geradas: {total_proxy_urls}")
        print(f"   SRCs vazios: {total_empty_srcs}")

        # Identificar problema principal
        if total_proxy_urls == 0 and total_img_tags > 0:
            print(f"\n🚨 PROBLEMA IDENTIFICADO:")
            print(f"   ❌ Templates estão gerando tags <img> mas SEM URLs de proxy")
            print(f"   💡 Solução: Corrigir construção da URL do proxy nos templates")

        elif total_empty_srcs > 0:
            print(f"\n🚨 PROBLEMA IDENTIFICADO:")
            print(f"   ❌ Algumas tags <img> têm SRC vazio")
            print(f"   💡 Solução: Verificar variáveis nos templates")

        elif total_proxy_urls > 0:
            print(f"\n✅ TEMPLATES PARECEM OK:")
            print(f"   ✅ URLs de proxy sendo geradas corretamente")
            print(f"   💡 Problema pode estar no JavaScript ou CSS")

        # Mostrar problemas específicos
        if self.results['issues_found']:
            print(f"\n❌ Problemas específicos encontrados:")
            for issue in self.results['issues_found']:
                print(f"   • {issue}")

        # Recomendações
        print(f"\n💡 Próximos passos recomendados:")
        print(f"   1. Verificar se JavaScript está interferindo no carregamento")
        print(f"   2. Inspecionar elemento no navegador para ver HTML final")
        print(f"   3. Verificar console do navegador para erros de rede")
        print(f"   4. Testar URLs de proxy diretamente no navegador")

    def run_complete_test(self):
        """Executar teste completo de renderização"""
        print("🎨 TESTE COMPLETO DE RENDERIZAÇÃO DE TEMPLATES")
        print("Investigando como livros do Google Books são renderizados")

        # Obter amostras
        books = self.get_google_books_samples()

        if not books:
            print("❌ Nenhum livro do Google Books encontrado")
            return False

        # Executar testes
        self.test_book_cover_template(books)
        self.test_book_card_template(books)
        self.test_home_page_rendering()
        self.test_specific_book_rendering(books)
        self.generate_final_diagnosis()

        return True


if __name__ == "__main__":
    tester = TemplateRenderTester()
    tester.run_complete_test()

    print("\n" + "=" * 60)
    print("Teste de renderização concluído.")
    print("Use os resultados para identificar onde as imagens se perdem.")
    print("=" * 60)