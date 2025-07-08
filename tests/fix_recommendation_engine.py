#!/usr/bin/env python
"""
Script de Correção do Sistema de Recomendações
Arquivo: tests/fix_recommendation_engine.py
Objetivo: Investigar e corrigir problemas no RecommendationEngine
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from cgbookstore.apps.core.models import Book, UserBookShelf
from django.contrib.auth import get_user_model
from django.db.models import Q
import inspect

User = get_user_model()


class RecommendationEngineAnalyzer:
    def __init__(self):
        self.results = {
            'engine_methods': [],
            'fallback_analysis': {},
            'user_shelf_analysis': {},
            'filter_issues': [],
            'recommendations': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    def analyze_recommendation_engine_api(self):
        """Analisar a API atual do RecommendationEngine"""
        self.print_header("1. ANÁLISE DA API DO RECOMMENDATION ENGINE")

        try:
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

            engine = RecommendationEngine()

            # Listar todos os métodos disponíveis
            methods = [method for method in dir(engine) if not method.startswith('_')]
            print(f"📋 Métodos disponíveis: {methods}")

            # Métodos que parecem ser de recomendação
            rec_methods = [m for m in methods if 'recommend' in m.lower() or 'get' in m.lower()]
            print(f"🎯 Métodos de recomendação: {rec_methods}")

            # Analisar assinatura de cada método
            for method_name in rec_methods:
                try:
                    method = getattr(engine, method_name)
                    if callable(method):
                        signature = inspect.signature(method)
                        print(f"   🔧 {method_name}{signature}")

                        # Tentar ver docstring
                        if method.__doc__:
                            doc_lines = method.__doc__.strip().split('\n')
                            print(f"      📋 {doc_lines[0][:80]}...")

                except Exception as e:
                    print(f"   ❌ Erro ao analisar {method_name}: {str(e)}")

            self.results['engine_methods'] = rec_methods

        except Exception as e:
            print(f"❌ Erro ao importar RecommendationEngine: {str(e)}")
            return False

        return True

    def test_recommendation_methods(self):
        """Testar diferentes métodos de recomendação"""
        self.print_header("2. TESTE DOS MÉTODOS DE RECOMENDAÇÃO")

        try:
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

            engine = RecommendationEngine()
            user = User.objects.first()

            if not user:
                print("❌ Nenhum usuário encontrado")
                return

            print(f"👤 Testando com usuário: {user.username}")

            # Tentar diferentes métodos
            test_methods = [
                ('get_recommendations', {'user': user, 'limit': 5}),
                ('get_recommendations', {'user_id': user.id, 'limit': 5}),
                ('get_mixed_recommendations', {'user': user, 'limit': 5}),
                ('get_user_recommendations', {'user': user}),
                ('generate_recommendations', {'user': user}),
                ('recommend_for_user', {'user': user}),
            ]

            for method_name, params in test_methods:
                if hasattr(engine, method_name):
                    print(f"\n🧪 Testando {method_name} com parâmetros: {list(params.keys())}")

                    try:
                        method = getattr(engine, method_name)

                        # Tentar diferentes formas de chamar
                        try:
                            result = method(**params)
                        except TypeError:
                            try:
                                result = method(user)
                            except TypeError:
                                try:
                                    result = method(user, 5)  # user, limit
                                except TypeError as e:
                                    print(f"      ❌ Erro de assinatura: {str(e)}")
                                    continue

                        print(f"      ✅ Método funcionou!")

                        if result:
                            print(f"      📊 Retornou {len(result) if hasattr(result, '__len__') else 'dados'}")

                            # Analisar resultado
                            self.analyze_recommendation_result(result, method_name)
                        else:
                            print(f"      ⚠️ Retornou vazio/None")

                    except Exception as e:
                        print(f"      ❌ Erro: {str(e)}")

        except Exception as e:
            print(f"❌ Erro no teste de métodos: {str(e)}")

    def analyze_recommendation_result(self, result, method_name):
        """Analisar resultado de uma recomendação"""
        try:
            if hasattr(result, '__iter__') and not isinstance(result, str):
                items = list(result)

                print(f"      📋 Analisando {len(items)} itens retornados:")

                google_books_count = 0
                local_books_count = 0

                for i, item in enumerate(items[:3]):  # Analisar primeiros 3
                    if hasattr(item, 'capa_url') and item.capa_url and 'books.google.com' in item.capa_url:
                        google_books_count += 1
                        print(f"         📖 Item {i + 1}: Google Books - {getattr(item, 'titulo', 'Sem título')}")
                    elif hasattr(item, 'titulo'):
                        local_books_count += 1
                        print(f"         📚 Item {i + 1}: Local - {item.titulo}")
                    else:
                        print(f"         📋 Item {i + 1}: Tipo desconhecido - {type(item)}")

                print(f"      📊 Google Books: {google_books_count}, Locais: {local_books_count}")

                self.results['recommendations'].append({
                    'method': method_name,
                    'total': len(items),
                    'google_books': google_books_count,
                    'local_books': local_books_count
                })

        except Exception as e:
            print(f"      ❌ Erro ao analisar resultado: {str(e)}")

    def analyze_user_shelves(self):
        """Analisar prateleiras do usuário"""
        self.print_header("3. ANÁLISE DAS PRATELEIRAS DO USUÁRIO")

        user = User.objects.first()
        if not user:
            print("❌ Nenhum usuário encontrado")
            return

        print(f"👤 Analisando prateleiras de: {user.username}")

        # Contar livros por prateleira
        shelves = UserBookShelf.objects.filter(user=user)
        print(f"📚 Total de livros nas prateleiras: {shelves.count()}")

        if shelves.count() == 0:
            print("🚨 PROBLEMA: Usuário não tem livros nas prateleiras!")
            print("   Isso explica por que só fallback está sendo usado")

            # Criar algumas prateleiras de exemplo
            self.create_sample_shelves(user)
        else:
            # Analisar prateleiras existentes
            for shelf_type in ['lendo', 'lido', 'vou_ler', 'favorito']:
                count = shelves.filter(shelf_type=shelf_type).count()
                print(f"   📋 {shelf_type}: {count} livros")

                if count > 0:
                    books = shelves.filter(shelf_type=shelf_type)[:3]
                    for book_shelf in books:
                        book = book_shelf.book
                        is_google = 'Google Books' if (
                                    book.capa_url and 'books.google.com' in book.capa_url) else 'Local'
                        print(f"      📖 {book.titulo} ({is_google})")

        self.results['user_shelf_analysis'] = {
            'user': user.username,
            'total_books': shelves.count(),
            'by_shelf': {
                shelf_type: shelves.filter(shelf_type=shelf_type).count()
                for shelf_type in ['lendo', 'lido', 'vou_ler', 'favorito']
            }
        }

    def create_sample_shelves(self, user):
        """Criar prateleiras de exemplo para testar"""
        print(f"\n🔧 Criando prateleiras de exemplo para {user.username}:")

        # Pegar alguns livros variados
        google_books = Book.objects.filter(capa_url__icontains='books.google.com')[:2]
        local_books = Book.objects.exclude(capa_url__icontains='books.google.com')[:2]

        sample_books = list(google_books) + list(local_books)

        if sample_books:
            shelf_types = ['lendo', 'lido', 'favorito', 'vou_ler']

            for i, book in enumerate(sample_books):
                shelf_type = shelf_types[i % len(shelf_types)]

                # Verificar se já existe
                existing = UserBookShelf.objects.filter(user=user, book=book).first()
                if not existing:
                    UserBookShelf.objects.create(
                        user=user,
                        book=book,
                        shelf_type=shelf_type
                    )

                    book_type = 'Google Books' if (book.capa_url and 'books.google.com' in book.capa_url) else 'Local'
                    print(f"   ✅ Adicionado: {book.titulo} ({book_type}) → {shelf_type}")

            print(f"   📊 Total adicionado: {len(sample_books)} livros")
        else:
            print("   ❌ Nenhum livro disponível para criar prateleiras")

    def analyze_fallback_behavior(self):
        """Analisar por que só fallback está sendo usado"""
        self.print_header("4. ANÁLISE DO COMPORTAMENTO FALLBACK")

        print("🔍 Investigando por que apenas fallback é usado:")

        # Verificar os IDs específicos do fallback
        fallback_ids = [440, 441, 459]

        for book_id in fallback_ids:
            try:
                book = Book.objects.get(id=book_id)
                book_type = 'Google Books' if (book.capa_url and 'books.google.com' in book.capa_url) else 'Local'
                print(f"   📖 ID {book_id}: {book.titulo} ({book_type})")

                if book.capa_url:
                    print(f"      🖼️ Tem capa_url: {book.capa_url[:50]}...")
                else:
                    print(f"      ❌ Sem capa_url")

            except Book.DoesNotExist:
                print(f"   ❌ ID {book_id}: Livro não encontrado")

        # Verificar configuração de fallback
        try:
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
            engine = RecommendationEngine()

            # Procurar por métodos de fallback
            fallback_methods = [m for m in dir(engine) if 'fallback' in m.lower()]
            print(f"\n🔧 Métodos de fallback: {fallback_methods}")

        except Exception as e:
            print(f"❌ Erro ao analisar fallback: {str(e)}")

    def check_filters_excluding_google_books(self):
        """Verificar se há filtros excluindo livros do Google Books"""
        self.print_header("5. VERIFICAÇÃO DE FILTROS")

        print("🔍 Verificando filtros que podem excluir livros Google Books:")

        # Verificar filtros comuns
        filters_to_test = [
            ("Todos os livros", Book.objects.all()),
            ("Livros não temporários", Book.objects.filter(is_temporary=False)),
            ("Livros temporários", Book.objects.filter(is_temporary=True)),
            ("Com external_id", Book.objects.exclude(Q(external_id='') | Q(external_id__isnull=True))),
            ("Com capa_url", Book.objects.exclude(Q(capa_url='') | Q(capa_url__isnull=True))),
            ("Google Books", Book.objects.filter(capa_url__icontains='books.google.com')),
        ]

        for filter_name, queryset in filters_to_test:
            count = queryset.count()
            google_count = queryset.filter(capa_url__icontains='books.google.com').count()

            print(f"   📊 {filter_name}: {count} total, {google_count} Google Books")

            if filter_name == "Livros não temporários" and google_count == 0:
                print(f"      🚨 PROBLEMA: Filtro exclui todos os Google Books!")
                self.results['filter_issues'].append("is_temporary=False exclui Google Books")

    def test_fixed_recommendation_call(self):
        """Testar chamada corrigida para recomendações"""
        self.print_header("6. TESTE COM CHAMADA CORRIGIDA")

        try:
            from cgbookstore.apps.core.recommendations.engine import RecommendationEngine

            engine = RecommendationEngine()
            user = User.objects.first()

            # Tentar o método mais provável baseado na análise anterior
            if hasattr(engine, 'get_recommendations'):
                print(f"🧪 Testando get_recommendations após adicionar livros às prateleiras:")

                try:
                    recommendations = engine.get_recommendations(user=user, limit=10)

                    if recommendations:
                        print(f"✅ Funcionou! {len(recommendations)} recomendações")

                        google_books = [r for r in recommendations if
                                        hasattr(r, 'capa_url') and r.capa_url and 'books.google.com' in r.capa_url]
                        print(f"📚 Livros Google Books nas recomendações: {len(google_books)}")

                        for book in google_books[:3]:
                            print(f"   🖼️ {book.titulo}")

                        if len(google_books) > 0:
                            print(f"🎉 SUCESSO: Google Books estão sendo recomendados!")
                        else:
                            print(f"⚠️ Ainda não há Google Books nas recomendações")

                    else:
                        print(f"❌ Ainda retornando vazio")

                except Exception as e:
                    print(f"❌ Erro: {str(e)}")

        except Exception as e:
            print(f"❌ Erro no teste: {str(e)}")

    def generate_fix_recommendations(self):
        """Gerar recomendações de correção"""
        self.print_header("7. RECOMENDAÇÕES DE CORREÇÃO")

        print("💡 Baseado na análise, aqui estão as correções necessárias:")

        # Baseado nos resultados da análise
        if self.results['user_shelf_analysis']['total_books'] == 0:
            print("1. 🚨 CRÍTICO: Usuário sem livros nas prateleiras")
            print("   - Isso causa fallback automático")
            print("   - Adicione livros às prateleiras do usuário de teste")

        if any('is_temporary=False' in issue for issue in self.results['filter_issues']):
            print("2. 🚨 CRÍTICO: Filtro is_temporary=False exclui Google Books")
            print("   - Remover ou ajustar filtro que exclui livros temporários")
            print("   - Google Books são salvos como is_temporary=True")

        if self.results['engine_methods']:
            working_methods = [r for r in self.results['recommendations'] if r['google_books'] > 0]
            if working_methods:
                best_method = working_methods[0]['method']
                print(f"3. ✅ Método que funciona: {best_method}")
                print(f"   - Use este método na view da home")
            else:
                print("3. ⚠️ Nenhum método retorna Google Books")
                print("   - Investigate filtros dentro do RecommendationEngine")

        print("\n🔧 Próximos passos:")
        print("   1. Adicionar livros às prateleiras do usuário")
        print("   2. Verificar filtros no RecommendationEngine")
        print("   3. Atualizar view da home com método correto")
        print("   4. Incluir livros temporários nas recomendações")

    def run_complete_analysis(self):
        """Executar análise completa"""
        print("🔧 ANÁLISE COMPLETA DO SISTEMA DE RECOMENDAÇÕES")
        print("Investigando por que Google Books não aparecem")

        self.analyze_recommendation_engine_api()
        self.test_recommendation_methods()
        self.analyze_user_shelves()
        self.analyze_fallback_behavior()
        self.check_filters_excluding_google_books()
        self.test_fixed_recommendation_call()
        self.generate_fix_recommendations()

        return self.results


if __name__ == "__main__":
    analyzer = RecommendationEngineAnalyzer()
    results = analyzer.run_complete_analysis()

    print("\n" + "=" * 70)
    print("Análise do sistema de recomendações concluída.")
    print("Implemente as correções recomendadas para resolver o problema.")
    print("=" * 70)