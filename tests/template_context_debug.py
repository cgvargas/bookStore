#!/usr/bin/env python
"""
Script de Debug de Contextos e Views - Problema de Imagens
Arquivo: tests/template_context_debug.py
Objetivo: Analisar dados que chegam aos templates e investigar views
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from cgbookstore.apps.core.models import Book
from django.urls import reverse
from django.template import Context, Template
from django.template.loader import render_to_string
import json

User = get_user_model()


class ViewContextDebugger:
    def __init__(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.results = {
            'views_analysis': {},
            'context_data': {},
            'books_analysis': {},
            'recommendations_debug': {},
            'issues_found': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    def analyze_book_data_in_db(self):
        """Analisar dados de livros no banco"""
        self.print_header("1. ANÁLISE DOS DADOS DE LIVROS NO BANCO")

        # Livros do Google Books
        google_books = Book.objects.filter(
            capa_url__icontains='books.google.com'
        ).exclude(capa_url='')

        print(f"📚 Total de livros com URLs do Google Books: {google_books.count()}")

        # Análise detalhada dos primeiros 3
        for book in google_books[:3]:
            print(f"\n📖 {book.titulo} (ID: {book.id})")
            print(f"   capa_url: {book.capa_url}")
            print(f"   get_capa_url(): {book.get_capa_url()}")
            print(f"   is_temporary: {book.is_temporary}")
            print(f"   external_id: {book.external_id}")

            # Verificar se está sendo usado em recomendações
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

            self.results['books_analysis'][book.id] = {
                'titulo': book.titulo,
                'capa_url': book.capa_url,
                'get_capa_url': book.get_capa_url(),
                'is_temporary': book.is_temporary,
                'external_id': book.external_id
            }

    def debug_home_view_context(self):
        """Debug da view da home page"""
        self.print_header("2. DEBUG DA VIEW DA HOME PAGE")

        try:
            # Fazer login com usuário
            user = User.objects.first()
            if user:
                self.client.force_login(user)
                print(f"✅ Usuário logado: {user.username}")

            # Capturar response da home
            response = self.client.get('/')

            print(f"📊 Status da home: {response.status_code}")

            if response.status_code == 200:
                # Analisar o contexto
                context = response.context

                print(f"🔍 Chaves do contexto: {list(context.keys()) if context else 'Nenhum contexto'}")

                # Procurar por dados de recomendações
                recommendation_keys = [key for key in context.keys() if 'recommend' in key.lower()]
                book_keys = [key for key in context.keys() if 'book' in key.lower() or 'livro' in key.lower()]

                print(f"📋 Chaves de recomendação: {recommendation_keys}")
                print(f"📋 Chaves de livros: {book_keys}")

                # Analisar cada contexto relevante
                for key in recommendation_keys + book_keys:
                    if key in context:
                        self.analyze_context_variable(key, context[key])

            self.results['views_analysis']['home'] = {
                'status': response.status_code,
                'context_keys': list(response.context.keys()) if response.context else []
            }

        except Exception as e:
            print(f"❌ Erro no debug da home: {str(e)}")
            self.results['issues_found'].append(f"Erro na home: {str(e)}")

    def analyze_context_variable(self, key, value):
        """Analisar uma variável específica do contexto"""
        print(f"\n🔍 Analisando contexto '{key}':")

        if hasattr(value, '__iter__') and not isinstance(value, str):
            # É uma lista ou queryset
            try:
                items = list(value)
                print(f"   📊 Tipo: Lista/QuerySet com {len(items)} itens")

                # Analisar primeiros itens
                for i, item in enumerate(items[:2]):
                    print(f"\n   📖 Item {i + 1}:")
                    self.analyze_book_object(item, indent="      ")

            except Exception as e:
                print(f"   ❌ Erro ao converter em lista: {str(e)}")

        elif hasattr(value, '_meta'):
            # É um objeto de modelo
            print(f"   📊 Tipo: Objeto {value.__class__.__name__}")
            self.analyze_book_object(value, indent="   ")

        else:
            print(f"   📊 Tipo: {type(value)} - Valor: {str(value)[:100]}")

    def analyze_book_object(self, obj, indent=""):
        """Analisar um objeto de livro"""
        try:
            if hasattr(obj, 'titulo') or hasattr(obj, 'title'):
                title = getattr(obj, 'titulo', getattr(obj, 'title', 'Sem título'))
                print(f"{indent}📚 Título: {title}")

            if hasattr(obj, 'capa_url'):
                capa_url = obj.capa_url
                print(f"{indent}🖼️ capa_url: {capa_url}")

                if capa_url and 'books.google.com' in capa_url:
                    print(f"{indent}✅ É URL do Google Books")
                elif capa_url:
                    print(f"{indent}📋 URL local/outro: {capa_url[:50]}...")
                else:
                    print(f"{indent}❌ capa_url vazia")

            if hasattr(obj, 'get_capa_url'):
                get_capa_url = obj.get_capa_url()
                print(f"{indent}🔧 get_capa_url(): {get_capa_url}")

            if hasattr(obj, 'is_temporary'):
                print(f"{indent}⏳ is_temporary: {obj.is_temporary}")

            if hasattr(obj, 'external_id'):
                print(f"{indent}🆔 external_id: {obj.external_id}")

            # Se for dicionário (livro externo da API)
            if isinstance(obj, dict):
                print(f"{indent}📋 Objeto tipo dict")
                if 'volumeInfo' in obj:
                    volume_info = obj['volumeInfo']
                    if 'imageLinks' in volume_info:
                        image_links = volume_info['imageLinks']
                        print(f"{indent}🖼️ imageLinks: {image_links}")

        except Exception as e:
            print(f"{indent}❌ Erro ao analisar objeto: {str(e)}")

    def debug_recommendation_views(self):
        """Debug das views de recomendação"""
        self.print_header("3. DEBUG DAS VIEWS DE RECOMENDAÇÃO")

        # URLs de recomendação para testar
        recommendation_urls = [
            '/recommendations/',
            '/recommendations/mixed/',
            '/recommendations/personalized/',
        ]

        for url in recommendation_urls:
            print(f"\n🌐 Testando URL: {url}")

            try:
                response = self.client.get(url)
                print(f"   Status: {response.status_code}")

                if response.status_code == 200 and response.context:
                    context = response.context
                    print(f"   🔍 Chaves do contexto: {list(context.keys())}")

                    # Procurar especificamente por livros
                    for key in context.keys():
                        if any(word in key.lower() for word in ['book', 'livro', 'recommend']):
                            print(f"   📋 Analisando '{key}'...")
                            self.analyze_context_variable(key, context[key])

                elif response.status_code == 404:
                    print(f"   📋 URL não encontrada (normal se não existe)")
                else:
                    print(f"   ❌ Problema na view")

            except Exception as e:
                print(f"   ❌ Erro: {str(e)}")

    def check_recommendation_engine_directly(self):
        """Testar o engine de recomendação diretamente"""
        self.print_header("4. TESTE DIRETO DO ENGINE DE RECOMENDAÇÃO")

        try:
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

            user = User.objects.first()
            if not user:
                print("❌ Nenhum usuário encontrado")
                return

            print(f"👤 Testando recomendações para: {user.username}")

            engine = RecommendationEngine()
            recommendations = engine.get_recommendations_for_user(user, limit=5)

            print(f"📊 Recomendações retornadas: {len(recommendations) if recommendations else 0}")

            if recommendations:
                print(f"📋 Analisando recomendações:")
                for i, book in enumerate(recommendations[:3]):
                    print(f"\n   📖 Recomendação {i + 1}:")
                    self.analyze_book_object(book, indent="      ")

            self.results['recommendations_debug'] = {
                'user': user.username,
                'count': len(recommendations) if recommendations else 0,
                'has_google_books': any(
                    hasattr(book, 'capa_url') and book.capa_url and 'books.google.com' in book.capa_url
                    for book in (recommendations or [])
                )
            }

        except Exception as e:
            print(f"❌ Erro no teste do engine: {str(e)}")
            import traceback
            print(f"   Detalhes: {traceback.format_exc()}")

    def analyze_view_files(self):
        """Analisar arquivos de view relevantes"""
        self.print_header("5. ANÁLISE DOS ARQUIVOS DE VIEW")

        view_files = [
            "cgbookstore/apps/core/views/general.py",
            "cgbookstore/apps/core/views/recommendation_views.py",
            "cgbookstore/apps/core/views/__init__.py"
        ]

        for view_file in view_files:
            if Path(view_file).exists():
                print(f"\n📄 Analisando {view_file}:")

                try:
                    with open(view_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Procurar por padrões relevantes
                    patterns = [
                        (r'def\s+(\w*home\w*)', 'Função home'),
                        (r'def\s+(\w*recommend\w*)', 'Função de recomendação'),
                        (r'context\[.*\]\s*=', 'Atribuição de contexto'),
                        (r'capa_url', 'Referência a capa_url'),
                        (r'google.*books', 'Referência Google Books'),
                        (r'external.*id', 'Referência external_id'),
                    ]

                    for pattern, description in patterns:
                        import re
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            print(f"   🔍 {description}: {len(matches)} ocorrências")
                            for match in matches[:3]:
                                print(f"      • {match}")

                except Exception as e:
                    print(f"   ❌ Erro ao ler arquivo: {str(e)}")
            else:
                print(f"❌ Arquivo não encontrado: {view_file}")

    def check_recent_changes(self):
        """Verificar mudanças recentes que podem ter causado o problema"""
        self.print_header("6. VERIFICAÇÃO DE MUDANÇAS RECENTES")

        print("🔍 Verificando possíveis causas da regressão:")

        # Verificar se livros temporários estão sendo filtrados
        temp_books = Book.objects.filter(is_temporary=True)
        temp_with_covers = temp_books.exclude(capa_url='')

        print(f"⏳ Livros temporários total: {temp_books.count()}")
        print(f"🖼️ Livros temporários com capa_url: {temp_with_covers.count()}")

        if temp_books.count() > 0 and temp_with_covers.count() == 0:
            print("🚨 PROBLEMA: Livros temporários não têm capa_url!")
            self.results['issues_found'].append("Livros temporários sem capa_url")

        # Verificar se algum filtro está excluindo livros do Google Books
        all_google_books = Book.objects.filter(capa_url__icontains='books.google.com')
        print(f"📚 Total de livros Google Books no banco: {all_google_books.count()}")

        for book in all_google_books[:3]:
            print(f"   📖 {book.titulo}: temp={book.is_temporary}, external_id={book.external_id}")

    def generate_diagnosis(self):
        """Gerar diagnóstico final"""
        self.print_header("7. DIAGNÓSTICO FINAL")

        print("📊 Resumo da análise:")

        if self.results['books_analysis']:
            print(f"✅ Livros Google Books encontrados: {len(self.results['books_analysis'])}")
        else:
            print("❌ Nenhum livro Google Books encontrado nos dados")

        if self.results['recommendations_debug']:
            rec_data = self.results['recommendations_debug']
            print(f"📋 Engine de recomendação: {rec_data.get('count', 0)} recomendações")
            print(f"🖼️ Tem livros Google Books: {rec_data.get('has_google_books', False)}")

        if self.results['issues_found']:
            print(f"\n🚨 Problemas identificados:")
            for issue in self.results['issues_found']:
                print(f"   • {issue}")

        # Recomendações baseadas na análise
        print(f"\n💡 Próximos passos recomendados:")

        if not self.results['books_analysis']:
            print("   1. Verificar por que livros Google Books não estão no contexto")
            print("   2. Analisar filtros nas queries das views")

        if self.results['recommendations_debug'] and not self.results['recommendations_debug'].get('has_google_books'):
            print("   3. Engine de recomendação não está retornando livros Google Books")
            print("   4. Verificar se filtros de recomendação mudaram")

        print("   5. Comparar código atual com versão que funcionava")
        print("   6. Verificar se migrations recentes afetaram dados")

    def run_complete_debug(self):
        """Executar debug completo"""
        print("🔍 DEBUG COMPLETO DE CONTEXTOS E VIEWS")
        print("Investigando por que imagens Google Books não aparecem")

        self.analyze_book_data_in_db()
        self.debug_home_view_context()
        self.debug_recommendation_views()
        self.check_recommendation_engine_directly()
        self.analyze_view_files()
        self.check_recent_changes()
        self.generate_diagnosis()

        return self.results


if __name__ == "__main__":
    debugger = ViewContextDebugger()
    results = debugger.run_complete_debug()

    print("\n" + "=" * 70)
    print("Debug de contextos e views concluído.")
    print("Use os resultados para identificar onde os dados se perderam.")
    print("=" * 70)