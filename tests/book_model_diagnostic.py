#!/usr/bin/env python
"""
Script de Diagnóstico do Modelo Book - Problema de Capas
Arquivo: tests/book_model_diagnostic.py
Objetivo: Investigar campos de imagem no modelo Book e como estão sendo populados
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from cgbookstore.apps.core.models import Book
from django.db.models import Q, Count
from django.conf import settings


class BookModelDiagnostic:
    def __init__(self):
        self.results = {
            'total_books': 0,
            'books_with_capa_url': 0,
            'books_with_capa_file': 0,
            'books_external': 0,
            'books_temporary': 0,
            'sample_analysis': [],
            'method_tests': [],
            'recommendations': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)

    def analyze_book_statistics(self):
        """Analisar estatísticas gerais dos livros"""
        self.print_header("1. ESTATÍSTICAS GERAIS DOS LIVROS")

        # Contadores básicos
        total_books = Book.objects.count()
        books_with_capa_url = Book.objects.exclude(Q(capa_url='') | Q(capa_url__isnull=True)).count()
        books_with_capa_file = Book.objects.exclude(Q(capa='') | Q(capa__isnull=True)).count()
        books_external = Book.objects.exclude(Q(external_id='') | Q(external_id__isnull=True)).count()
        books_temporary = Book.objects.filter(is_temporary=True).count()

        print(f"📚 Total de livros no banco: {total_books}")
        print(f"🔗 Livros com capa_url preenchida: {books_with_capa_url}")
        print(f"🖼️ Livros com arquivo de capa local: {books_with_capa_file}")
        print(f"🌐 Livros com external_id (Google Books): {books_external}")
        print(f"⏳ Livros temporários: {books_temporary}")

        # Percentuais
        if total_books > 0:
            print(f"\n📊 Percentuais:")
            print(f"   URLs de capa: {(books_with_capa_url / total_books) * 100:.1f}%")
            print(f"   Capas locais: {(books_with_capa_file / total_books) * 100:.1f}%")
            print(f"   Livros externos: {(books_external / total_books) * 100:.1f}%")

        # Salvar resultados
        self.results.update({
            'total_books': total_books,
            'books_with_capa_url': books_with_capa_url,
            'books_with_capa_file': books_with_capa_file,
            'books_external': books_external,
            'books_temporary': books_temporary
        })

    def analyze_sample_books(self):
        """Analisar uma amostra de livros em detalhe"""
        self.print_header("2. ANÁLISE DETALHADA DE LIVROS DE AMOSTRA")

        # Pegar diferentes tipos de livros
        sample_queries = [
            ("Livros com external_id", Book.objects.exclude(Q(external_id='') | Q(external_id__isnull=True))[:3]),
            ("Livros com capa_url", Book.objects.exclude(Q(capa_url='') | Q(capa_url__isnull=True))[:3]),
            ("Livros temporários", Book.objects.filter(is_temporary=True)[:3]),
            ("Livros locais", Book.objects.filter(Q(external_id='') | Q(external_id__isnull=True))[:3])
        ]

        for category, books in sample_queries:
            print(f"\n📋 {category}:")

            if books.exists():
                for book in books:
                    self.analyze_single_book(book)
            else:
                print("   ❌ Nenhum livro encontrado nesta categoria")

    def analyze_single_book(self, book):
        """Analisar um livro específico em detalhe"""
        print(f"\n   📖 {book.titulo} (ID: {book.id})")
        print(f"      Autor: {book.autor}")
        print(f"      External ID: {book.external_id or 'Não definido'}")
        print(f"      É temporário: {book.is_temporary}")
        print(f"      Origem: {book.origem}")

        # Análise dos campos de imagem
        print(f"\n   🖼️ Campos de Imagem:")
        print(f"      capa_url: {book.capa_url or 'Vazio'}")
        print(f"      capa (arquivo): {book.capa or 'Vazio'}")
        print(f"      capa_preview: {book.capa_preview or 'Vazio'}")

        # Testar métodos do modelo
        print(f"\n   🔧 Métodos do Modelo:")
        try:
            capa_url_method = book.get_capa_url()
            print(f"      get_capa_url(): {capa_url_method}")

            preview_url_method = book.get_preview_url()
            print(f"      get_preview_url(): {preview_url_method}")

            is_external_method = book.is_external()
            print(f"      is_external(): {is_external_method}")

            origem_display = book.get_origem_display()
            print(f"      get_origem_display(): {origem_display}")

            # Verificar se arquivos existem
            if book.capa:
                capa_path = Path(settings.MEDIA_ROOT) / book.capa.name
                print(f"      Arquivo capa existe: {capa_path.exists()}")

            if book.capa_preview:
                preview_path = Path(settings.MEDIA_ROOT) / book.capa_preview.name
                print(f"      Arquivo preview existe: {preview_path.exists()}")

            # Salvar para análise
            self.results['sample_analysis'].append({
                'id': book.id,
                'titulo': book.titulo,
                'capa_url': book.capa_url,
                'capa_file': str(book.capa) if book.capa else None,
                'external_id': book.external_id,
                'is_temporary': book.is_temporary,
                'get_capa_url': capa_url_method,
                'get_preview_url': preview_url_method,
                'is_external': is_external_method
            })

        except Exception as e:
            print(f"      ❌ Erro ao testar métodos: {str(e)}")

    def test_image_proxy_integration(self):
        """Testar integração com image proxy"""
        self.print_header("3. TESTE DE INTEGRAÇÃO COM IMAGE PROXY")

        # Pegar um livro com external_id para teste
        book_with_external = Book.objects.exclude(Q(external_id='') | Q(external_id__isnull=True)).first()

        if book_with_external:
            print(f"📖 Testando com: {book_with_external.titulo}")
            print(f"   External ID: {book_with_external.external_id}")

            # Simular URLs que seriam usadas no template
            from django.template import Template, Context
            from django.urls import reverse

            try:
                # Testar diferentes contextos de template
                test_contexts = [
                    {
                        'name': 'book.get_capa_url',
                        'value': book_with_external.get_capa_url()
                    },
                    {
                        'name': 'book.capa_url',
                        'value': book_with_external.capa_url
                    },
                    {
                        'name': 'book.get_preview_url',
                        'value': book_with_external.get_preview_url()
                    }
                ]

                print(f"\n   🔗 URLs disponíveis:")
                for context in test_contexts:
                    url_value = context['value']
                    print(f"      {context['name']}: {url_value}")

                    # Verificar se seria válida para o proxy
                    if url_value and url_value.startswith('http'):
                        print(f"         ✅ URL válida para proxy")
                    elif url_value and 'no-cover.svg' in url_value:
                        print(f"         📋 Placeholder padrão")
                    else:
                        print(f"         ⚠️ URL não utilizável")

                # Testar construção da URL do proxy
                if book_with_external.capa_url:
                    try:
                        from urllib.parse import urlencode
                        proxy_url = reverse('image_proxy') + '?' + urlencode({'url': book_with_external.capa_url})
                        print(f"\n   🔄 URL do proxy seria: {proxy_url}")
                    except Exception as e:
                        print(f"   ❌ Erro ao construir URL do proxy: {str(e)}")

            except Exception as e:
                print(f"   ❌ Erro no teste de integração: {str(e)}")

        else:
            print("❌ Nenhum livro com external_id encontrado para teste")

    def check_external_data_structure(self):
        """Verificar estrutura dos external_data"""
        self.print_header("4. ANÁLISE DOS DADOS EXTERNOS")

        books_with_external_data = Book.objects.exclude(external_data__isnull=True)[:3]

        print(f"📊 Livros com external_data: {books_with_external_data.count()}")

        for book in books_with_external_data:
            print(f"\n📖 {book.titulo}:")

            if book.external_data:
                print(f"   🔍 Estrutura do external_data:")

                # Verificar se há dados de imagem nos external_data
                if isinstance(book.external_data, dict):
                    # Procurar por imageLinks
                    if 'imageLinks' in book.external_data:
                        image_links = book.external_data['imageLinks']
                        print(f"      imageLinks encontrado: {image_links}")

                    # Procurar por volumeInfo
                    if 'volumeInfo' in book.external_data:
                        volume_info = book.external_data['volumeInfo']
                        if 'imageLinks' in volume_info:
                            print(f"      volumeInfo.imageLinks: {volume_info['imageLinks']}")

                    # Mostrar todas as chaves principais
                    print(f"      Chaves principais: {list(book.external_data.keys())}")
                else:
                    print(f"      ⚠️ external_data não é um dicionário: {type(book.external_data)}")
            else:
                print(f"   📋 external_data está vazio")

    def identify_issues_and_solutions(self):
        """Identificar problemas e soluções"""
        self.print_header("5. PROBLEMAS IDENTIFICADOS E SOLUÇÕES")

        issues = []

        # Análise baseada nos resultados
        if self.results['total_books'] == 0:
            issues.append({
                'priority': 'ALTA',
                'issue': 'Nenhum livro no banco de dados',
                'solution': 'Importar dados de livros ou verificar conexão com o banco'
            })
        elif self.results['books_with_capa_url'] == 0:
            issues.append({
                'priority': 'ALTA',
                'issue': 'Nenhum livro tem capa_url preenchida',
                'solution': 'Verificar processo de importação do Google Books - campo capa_url não está sendo salvo'
            })
        elif self.results['books_with_capa_url'] < (self.results['total_books'] * 0.5):
            issues.append({
                'priority': 'MÉDIA',
                'issue': f'Apenas {(self.results["books_with_capa_url"] / self.results["total_books"]) * 100:.1f}% dos livros têm capa_url',
                'solution': 'Atualizar livros existentes com URLs de capa do Google Books'
            })

        # Verificar se há livros externos sem capa_url
        external_without_cover = self.results['books_external'] - self.results['books_with_capa_url']
        if external_without_cover > 0:
            issues.append({
                'priority': 'ALTA',
                'issue': f'{external_without_cover} livros externos sem capa_url',
                'solution': 'Executar script para buscar URLs de capa dos livros já importados'
            })

        # Verificar problemas no template/renderização
        sample_with_methods = [s for s in self.results['sample_analysis'] if s.get('get_capa_url')]
        if sample_with_methods:
            methods_returning_placeholder = [s for s in sample_with_methods if
                                             'no-cover.svg' in s.get('get_capa_url', '')]
            if len(methods_returning_placeholder) == len(sample_with_methods):
                issues.append({
                    'priority': 'ALTA',
                    'issue': 'Métodos get_capa_url() retornando apenas placeholder',
                    'solution': 'Verificar lógica do método get_capa_url() no modelo Book'
                })

        if not issues:
            issues.append({
                'priority': 'INFO',
                'issue': 'Modelo Book parece estar configurado corretamente',
                'solution': 'Verificar templates e como as URLs estão sendo passadas para o frontend'
            })

        # Exibir problemas e soluções
        for issue in issues:
            priority_emoji = {'ALTA': '🚨', 'MÉDIA': '⚠️', 'BAIXA': '📝', 'INFO': 'ℹ️'}
            print(f"{priority_emoji.get(issue['priority'], '•')} {issue['priority']}: {issue['issue']}")
            print(f"   💡 Solução: {issue['solution']}\n")

        self.results['recommendations'] = issues

    def generate_fix_script_recommendations(self):
        """Gerar recomendações de scripts para corrigir problemas"""
        self.print_header("6. SCRIPTS RECOMENDADOS PARA CORREÇÃO")

        print("📝 Scripts que podem ser necessários:")

        if self.results['books_external'] > self.results['books_with_capa_url']:
            print("\n🔧 Script 1: Atualizar URLs de capa de livros externos")
            print("   Arquivo: update_book_covers.py")
            print("   Função: Buscar URLs de capa no Google Books para livros com external_id")

        if self.results['books_with_capa_url'] == 0:
            print("\n🔧 Script 2: Corrigir importação do Google Books")
            print("   Arquivo: fix_google_books_import.py")
            print("   Função: Corrigir processo de salvamento do campo capa_url")

        print("\n🔧 Script 3: Diagnóstico de template")
        print("   Arquivo: template_render_test.py")
        print("   Função: Testar renderização de templates com dados reais")

    def run_full_diagnostic(self):
        """Executar diagnóstico completo do modelo Book"""
        print("📚 DIAGNÓSTICO DO MODELO BOOK - CAMPOS DE IMAGEM")
        print("Investigando por que as capas não estão sendo exibidas")

        # Executar todos os testes
        self.analyze_book_statistics()
        self.analyze_sample_books()
        self.test_image_proxy_integration()
        self.check_external_data_structure()
        self.identify_issues_and_solutions()
        self.generate_fix_script_recommendations()

        # Resumo final
        self.print_header("RESUMO DO DIAGNÓSTICO DO MODELO")
        print(f"📚 Total de livros: {self.results['total_books']}")
        print(f"🔗 Com capa_url: {self.results['books_with_capa_url']}")
        print(f"🌐 Externos: {self.results['books_external']}")
        print(f"⏳ Temporários: {self.results['books_temporary']}")
        print(f"🖼️ Com arquivo local: {self.results['books_with_capa_file']}")

        print(f"\n💡 {len(self.results['recommendations'])} problemas identificados")

        return self.results


if __name__ == "__main__":
    diagnostic = BookModelDiagnostic()
    results = diagnostic.run_full_diagnostic()

    print("\n" + "=" * 60)
    print("Diagnóstico do modelo concluído.")
    print("Baseado nos resultados, implemente os scripts de correção recomendados.")
    print("=" * 60)