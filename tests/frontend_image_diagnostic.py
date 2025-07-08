#!/usr/bin/env python
"""
Script de Diagnóstico Frontend - Problema de Renderização de Capas
Arquivo: tests/frontend_image_diagnostic.py
Objetivo: Investigar proxy de imagem e renderização nos templates
"""

import os
import sys
import django
import requests
from pathlib import Path
import re

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.urls import reverse
from django.test import Client
from django.core.cache import caches
from cgbookstore.apps.core.models import Book
from django.conf import settings


class FrontendImageDiagnostic:
    def __init__(self):
        self.client = Client()
        self.results = {
            'image_proxy_view': False,
            'templates_analysis': {},
            'url_patterns': {},
            'sample_pages_test': [],
            'static_files': {},
            'recommendations': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def check_image_proxy_view(self):
        """Verificar se a view image_proxy existe e está funcionando"""
        self.print_header("1. ANÁLISE DA VIEW IMAGE_PROXY")

        # Verificar se o arquivo existe
        proxy_file = Path("cgbookstore/apps/core/views/image_proxy.py")

        if proxy_file.exists():
            print("✅ Arquivo image_proxy.py encontrado")

            # Analisar o conteúdo
            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"📄 Tamanho do arquivo: {len(content)} caracteres")

                # Procurar por funções/classes
                functions = re.findall(r'def\s+(\w+)', content)
                classes = re.findall(r'class\s+(\w+)', content)

                print(f"🔧 Funções encontradas: {functions}")
                print(f"📋 Classes encontradas: {classes}")

                # Verificar imports importantes
                important_imports = [
                    'HttpResponse', 'requests', 'cache', 'logging'
                ]

                for imp in important_imports:
                    if imp in content:
                        print(f"✅ Import '{imp}' encontrado")
                    else:
                        print(f"⚠️ Import '{imp}' não encontrado")

                self.results['image_proxy_view'] = True

            except Exception as e:
                print(f"❌ Erro ao ler arquivo: {str(e)}")

        else:
            print("❌ Arquivo image_proxy.py NÃO encontrado")
            print("📂 Verificando views disponíveis...")

            views_dir = Path("cgbookstore/apps/core/views/")
            if views_dir.exists():
                view_files = list(views_dir.glob("*.py"))
                print(f"📋 Arquivos de view encontrados: {[f.name for f in view_files]}")

            self.results['image_proxy_view'] = False

    def check_url_patterns(self):
        """Verificar padrões de URL relacionados a imagens"""
        self.print_header("2. ANÁLISE DOS PADRÕES DE URL")

        try:
            # Verificar URLs principais
            urls_to_check = [
                'cgbookstore.config.urls',
                'cgbookstore.apps.core.urls'
            ]

            for url_module in urls_to_check:
                try:
                    # Tentar importar e analisar
                    module_path = url_module.replace('.', '/') + '.py'
                    file_path = Path(module_path)

                    if file_path.exists():
                        print(f"\n📂 Analisando {url_module}:")

                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Procurar por padrões relacionados a imagem
                        image_patterns = re.findall(r"path\(['\"]([^'\"]*(?:image|proxy|cover)[^'\"]*)['\"]", content)

                        if image_patterns:
                            print(f"🖼️ Padrões de URL de imagem encontrados: {image_patterns}")
                            self.results['url_patterns'][url_module] = image_patterns
                        else:
                            print("⚠️ Nenhum padrão de URL de imagem encontrado")

                except Exception as e:
                    print(f"❌ Erro ao analisar {url_module}: {str(e)}")

        except Exception as e:
            print(f"❌ Erro geral na análise de URLs: {str(e)}")

    def analyze_templates(self):
        """Analisar templates que renderizam imagens"""
        self.print_header("3. ANÁLISE DOS TEMPLATES")

        template_dirs = [
            Path("cgbookstore/apps/core/templates/core/book/"),
            Path("cgbookstore/apps/core/templates/core/components/"),
            Path("cgbookstore/apps/core/templates/core/includes/")
        ]

        for template_dir in template_dirs:
            if template_dir.exists():
                print(f"\n📂 Analisando {template_dir}:")

                template_files = list(template_dir.glob("*.html"))

                for template_file in template_files:
                    self.analyze_template_file(template_file)

    def analyze_template_file(self, template_file):
        """Analisar um arquivo de template específico"""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"\n   📄 {template_file.name}:")

            # Procurar por tags de imagem
            img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
            print(f"     🖼️ Tags <img> encontradas: {len(img_tags)}")

            if img_tags:
                for i, tag in enumerate(img_tags[:3]):  # Mostrar apenas as 3 primeiras
                    print(f"       {i + 1}. {tag[:80]}...")

            # Procurar por variáveis relacionadas a imagem
            image_vars = re.findall(r'\{\{\s*([^}]*(?:cover|image|capa)[^}]*)\s*\}\}', content, re.IGNORECASE)
            if image_vars:
                print(f"     📋 Variáveis de imagem: {image_vars}")

            # Procurar por filtros ou tags customizadas
            custom_tags = re.findall(r'\{\%\s*([^%]*(?:image|cover|proxy)[^%]*)\s*\%\}', content, re.IGNORECASE)
            if custom_tags:
                print(f"     🏷️ Tags customizadas: {custom_tags}")

            self.results['templates_analysis'][template_file.name] = {
                'img_tags': len(img_tags),
                'image_vars': image_vars,
                'custom_tags': custom_tags
            }

        except Exception as e:
            print(f"     ❌ Erro ao analisar template: {str(e)}")

    def test_sample_pages(self):
        """Testar páginas que deveriam mostrar imagens"""
        self.print_header("4. TESTE DE PÁGINAS COM IMAGENS")

        pages_to_test = [
            {
                'name': 'Home',
                'url': '/',
                'should_have_images': True
            },
            {
                'name': 'Recomendações',
                'url': '/recommendations/',
                'should_have_images': True
            },
            {
                'name': 'Catálogo',
                'url': '/books/catalogue/',
                'should_have_images': True
            }
        ]

        for page_info in pages_to_test:
            self.test_page_images(page_info)

    def test_page_images(self, page_info):
        """Testar uma página específica"""
        try:
            print(f"\n🌐 Testando página: {page_info['name']} ({page_info['url']})")

            response = self.client.get(page_info['url'])

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                content = response.content.decode('utf-8')

                # Contar tags de imagem
                img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
                print(f"   🖼️ Tags <img> encontradas: {len(img_tags)}")

                # Procurar por URLs específicas do Google Books
                google_books_urls = re.findall(r'books\.google\.com[^"\s]*', content)
                print(f"   📚 URLs Google Books: {len(google_books_urls)}")

                # Procurar por placeholders ou imagens de erro
                placeholder_imgs = re.findall(r'(?:placeholder|no-cover|default)[^"\s]*\.(jpg|png|svg)', content,
                                              re.IGNORECASE)
                print(f"   🚫 Imagens placeholder: {len(placeholder_imgs)}")

                # Verificar se há erros de JavaScript
                js_errors = re.findall(r'console\.error|onerror', content, re.IGNORECASE)
                if js_errors:
                    print(f"   ⚠️ Possíveis erros JS detectados: {len(js_errors)}")

                self.results['sample_pages_test'].append({
                    'page': page_info['name'],
                    'status_code': response.status_code,
                    'img_tags': len(img_tags),
                    'google_books_urls': len(google_books_urls),
                    'placeholders': len(placeholder_imgs)
                })

            else:
                print(f"   ❌ Página não acessível: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Erro ao testar página: {str(e)}")

    def check_static_files(self):
        """Verificar arquivos estáticos relacionados a imagens"""
        self.print_header("5. VERIFICAÇÃO DE ARQUIVOS ESTÁTICOS")

        static_dirs = [
            Path("cgbookstore/static/images/"),
            Path("cgbookstore/static/css/"),
            Path("cgbookstore/static/js/")
        ]

        for static_dir in static_dirs:
            if static_dir.exists():
                print(f"\n📂 {static_dir}:")

                if 'images' in str(static_dir):
                    # Para pasta de imagens, listar arquivos
                    image_files = list(static_dir.glob("*"))
                    print(f"   🖼️ Arquivos de imagem: {[f.name for f in image_files]}")

                    # Verificar especificamente por placeholder ou no-cover
                    placeholder_files = [f for f in image_files if any(
                        keyword in f.name.lower() for keyword in ['placeholder', 'no-cover', 'default'])]
                    if placeholder_files:
                        print(f"   🚫 Placeholders encontrados: {[f.name for f in placeholder_files]}")

                elif 'css' in str(static_dir):
                    # Para CSS, procurar por estilos relacionados a imagem
                    css_files = list(static_dir.glob("*.css"))
                    image_related_css = []

                    for css_file in css_files:
                        if any(keyword in css_file.name.lower() for keyword in ['book', 'cover', 'image']):
                            image_related_css.append(css_file.name)

                    if image_related_css:
                        print(f"   🎨 CSS relacionado a imagens: {image_related_css}")

                elif 'js' in str(static_dir):
                    # Para JS, procurar por scripts relacionados a imagem
                    js_files = list(static_dir.glob("*.js"))
                    image_related_js = []

                    for js_file in js_files:
                        if any(keyword in js_file.name.lower() for keyword in ['book', 'image', 'cover']):
                            image_related_js.append(js_file.name)

                    if image_related_js:
                        print(f"   📜 JS relacionado a imagens: {image_related_js}")

    def test_direct_image_proxy(self):
        """Testar diretamente o proxy de imagem com uma URL conhecida"""
        self.print_header("6. TESTE DIRETO DO IMAGE PROXY")

        # Pegar uma URL de imagem que sabemos que funciona
        try:
            book = Book.objects.filter(external_id__isnull=False).exclude(external_id='').first()

            if book and hasattr(book, 'cover_url') and book.cover_url:
                print(
                    f"📖 Testando com livro: {getattr(book, 'titulo', getattr(book, 'title', 'Título não encontrado'))}")
                print(f"🔗 URL original: {book.cover_url}")

                # Tentar diferentes formatos de URL do proxy
                proxy_urls_to_test = [
                    f"/image-proxy/?url={book.cover_url}",
                    f"/proxy/image/?url={book.cover_url}",
                    f"/core/image-proxy/?url={book.cover_url}",
                ]

                for proxy_url in proxy_urls_to_test:
                    print(f"\n🧪 Testando proxy: {proxy_url}")

                    try:
                        response = self.client.get(proxy_url)
                        print(f"   Status: {response.status_code}")

                        if response.status_code == 200:
                            content_type = response.get('Content-Type', 'unknown')
                            print(f"   ✅ Proxy funcionando! Content-Type: {content_type}")

                            if 'image' in content_type:
                                print(f"   🖼️ Imagem retornada com sucesso!")
                                return True
                        else:
                            print(f"   ❌ Proxy falhou: {response.status_code}")

                    except Exception as e:
                        print(f"   ❌ Erro no teste: {str(e)}")

            else:
                print("❌ Nenhum livro com cover_url encontrado para teste")

        except Exception as e:
            print(f"❌ Erro ao testar proxy: {str(e)}")

        return False

    def generate_recommendations(self):
        """Gerar recomendações baseadas na análise"""
        self.print_header("7. RECOMENDAÇÕES ESPECÍFICAS")

        recommendations = []

        if not self.results['image_proxy_view']:
            recommendations.append({
                'priority': 'ALTA',
                'issue': 'View image_proxy não encontrada ou com problemas',
                'action': 'Implementar/corrigir view de proxy de imagem'
            })

        # Analisar resultados dos templates
        templates_with_issues = []
        for template, analysis in self.results['templates_analysis'].items():
            if analysis['img_tags'] == 0:
                templates_with_issues.append(template)

        if templates_with_issues:
            recommendations.append({
                'priority': 'MÉDIA',
                'issue': f'Templates sem tags <img>: {templates_with_issues}',
                'action': 'Verificar se imagens estão sendo renderizadas nos templates'
            })

        # Analisar testes de páginas
        pages_without_images = []
        for page_test in self.results['sample_pages_test']:
            if page_test['img_tags'] == 0 and page_test['status_code'] == 200:
                pages_without_images.append(page_test['page'])

        if pages_without_images:
            recommendations.append({
                'priority': 'ALTA',
                'issue': f'Páginas sem imagens renderizadas: {pages_without_images}',
                'action': 'Investigar por que as imagens não aparecem no HTML final'
            })

        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'issue': 'Estrutura básica parece OK',
                'action': 'Verificar console do navegador e logs do servidor em tempo real'
            })

        for rec in recommendations:
            priority_emoji = {'ALTA': '🚨', 'MÉDIA': '⚠️', 'BAIXA': '📝', 'INFO': 'ℹ️'}
            print(f"{priority_emoji.get(rec['priority'], '•')} {rec['priority']}: {rec['issue']}")
            print(f"   Ação: {rec['action']}\n")

        self.results['recommendations'] = recommendations

    def run_full_diagnostic(self):
        """Executar diagnóstico completo do frontend"""
        print("🎨 DIAGNÓSTICO FRONTEND E IMAGE PROXY - CGBOOKSTORE")
        print("Investigando renderização de imagens nos templates")

        # Executar todos os testes
        self.check_image_proxy_view()
        self.check_url_patterns()
        self.analyze_templates()
        self.test_sample_pages()
        self.check_static_files()
        proxy_works = self.test_direct_image_proxy()
        self.generate_recommendations()

        # Resumo final
        self.print_header("RESUMO DO DIAGNÓSTICO FRONTEND")
        print(f"✅ Image Proxy View: {self.results['image_proxy_view']}")
        print(f"✅ Padrões URL encontrados: {len(self.results['url_patterns'])}")
        print(f"✅ Templates analisados: {len(self.results['templates_analysis'])}")
        print(f"✅ Páginas testadas: {len(self.results['sample_pages_test'])}")
        print(f"✅ Proxy direto funciona: {proxy_works}")

        print(f"\n💡 {len(self.results['recommendations'])} recomendações geradas")

        return self.results


if __name__ == "__main__":
    diagnostic = FrontendImageDiagnostic()
    results = diagnostic.run_full_diagnostic()

    print("\n" + "=" * 60)
    print("Diagnóstico frontend concluído.")
    print("Execute 'python manage.py runserver' e abra o console do navegador")
    print("para verificar erros de JavaScript ou problemas de carregamento.")
    print("=" * 60)