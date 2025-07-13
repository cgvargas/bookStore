# Script de diagnóstico de prateleiras
# Salve este código em: cgbookstore/apps/core/management/commands/diagnostic_shelves.py

from django.core.management.base import BaseCommand
from django.db.models import Count
from cgbookstore.apps.core.models.home_content import (
    DefaultShelfType, HomeSection, BookShelfSection
)
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Diagnóstica o estado atual das prateleiras do sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DIAGNÓSTICO COMPLETO DE PRATELEIRAS ===\n'))

        # 1. Verificar total de livros no sistema
        total_books = Book.objects.count()
        self.stdout.write(f'📚 Total de livros no sistema: {total_books}')

        # 2. Verificar distribuição de campos importantes
        self.stdout.write('\n📊 DISTRIBUIÇÃO DE CAMPOS BOOLEANOS:')
        self.stdout.write(f'   • e_manga=True: {Book.objects.filter(e_manga=True).count()}')
        self.stdout.write(f'   • e_lancamento=True: {Book.objects.filter(e_lancamento=True).count()}')
        self.stdout.write(f'   • e_destaque=True: {Book.objects.filter(e_destaque=True).count()}')
        self.stdout.write(f'   • adaptado_filme=True: {Book.objects.filter(adaptado_filme=True).count()}')
        self.stdout.write(f'   • quantidade_vendida > 0: {Book.objects.filter(quantidade_vendida__gt=0).count()}')

        # 3. Verificar campo tipo_shelf_especial
        self.stdout.write('\n📋 DISTRIBUIÇÃO DE tipo_shelf_especial:')
        shelf_types = Book.objects.values('tipo_shelf_especial').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in shelf_types:
            tipo = item['tipo_shelf_especial'] or '(vazio)'
            count = item['count']
            self.stdout.write(f'   • {tipo}: {count} livros')

        # 4. Verificar DefaultShelfType configurados
        self.stdout.write('\n🏷️  TIPOS DE PRATELEIRA PADRÃO CONFIGURADOS:')
        default_types = DefaultShelfType.objects.all().order_by('ordem')

        for shelf_type in default_types:
            status = '✅ ATIVO' if shelf_type.ativo else '❌ INATIVO'
            self.stdout.write(f'\n   📖 {shelf_type.nome} ({shelf_type.identificador}) - {status}')
            self.stdout.write(f'      Campo: {shelf_type.filtro_campo}')
            self.stdout.write(f'      Valor: {shelf_type.filtro_valor}')
            self.stdout.write(f'      Ordem: {shelf_type.ordem}')

            # Testar quantos livros este tipo retorna
            try:
                livros = shelf_type.get_livros()
                if hasattr(livros, 'count'):
                    count = livros.count()
                else:
                    count = len(list(livros)) if livros else 0
                self.stdout.write(f'      📚 Livros encontrados: {count}')
            except Exception as e:
                self.stdout.write(f'      ❌ ERRO: {str(e)}')

        # 5. Verificar seções da home
        self.stdout.write('\n🏠 SEÇÕES DA HOME CONFIGURADAS:')
        home_sections = HomeSection.objects.all().order_by('ordem')

        for section in home_sections:
            status = '✅ ATIVA' if section.ativo else '❌ INATIVA'
            self.stdout.write(f'\n   🏷️  {section.titulo} (Tipo: {section.tipo}) - {status}')
            self.stdout.write(f'      ID: {section.id}')
            self.stdout.write(f'      Ordem: {section.ordem}')

            # Se for do tipo shelf, verificar prateleira associada
            if section.tipo == 'shelf':
                try:
                    if hasattr(section, 'book_shelf') and section.book_shelf:
                        book_shelf = section.book_shelf
                        self.stdout.write(f'      📚 Prateleira associada: SIM')
                        self.stdout.write(f'         Max livros: {book_shelf.max_livros}')

                        if book_shelf.shelf_type:
                            self.stdout.write(f'         Tipo personalizado: {book_shelf.shelf_type.nome}')
                        else:
                            self.stdout.write(f'         Tipo legado: {book_shelf.tipo_shelf}')

                        # Testar quantos livros manualmente adicionados
                        manual_count = book_shelf.livros.count()
                        self.stdout.write(f'         Livros manuais: {manual_count}')

                        # Testar livros filtrados
                        try:
                            filtered_books = book_shelf.get_filtered_books()
                            if hasattr(filtered_books, 'count'):
                                filtered_count = filtered_books.count()
                            else:
                                filtered_count = len(list(filtered_books)) if filtered_books else 0
                            self.stdout.write(f'         Livros filtrados: {filtered_count}')
                        except Exception as e:
                            self.stdout.write(f'         ❌ ERRO filtro: {str(e)}')
                    else:
                        self.stdout.write(f'      📚 Prateleira associada: NÃO')
                except Exception as e:
                    self.stdout.write(f'      ❌ ERRO seção: {str(e)}')

        # 6. Verificar se há prateleiras órfãs
        self.stdout.write('\n🔍 VERIFICAÇÃO DE INCONSISTÊNCIAS:')

        # BookShelfSection sem HomeSection
        orphan_shelves = BookShelfSection.objects.filter(section__isnull=True)
        if orphan_shelves.exists():
            self.stdout.write(f'   ⚠️  Prateleiras órfãs (sem seção): {orphan_shelves.count()}')
            for shelf in orphan_shelves:
                self.stdout.write(f'      - ID: {shelf.id}')

        # HomeSection do tipo shelf sem BookShelfSection
        sections_without_shelf = HomeSection.objects.filter(
            tipo='shelf'
        ).exclude(
            id__in=BookShelfSection.objects.values_list('section_id', flat=True)
        )
        if sections_without_shelf.exists():
            self.stdout.write(f'   ⚠️  Seções shelf sem prateleira: {sections_without_shelf.count()}')
            for section in sections_without_shelf:
                self.stdout.write(f'      - {section.titulo} (ID: {section.id})')

        # 7. Sugestões de correção
        self.stdout.write('\n💡 SUGESTÕES DE CORREÇÃO:')

        # Verificar campos problemáticos
        problematic_fields = []
        for shelf_type in DefaultShelfType.objects.filter(ativo=True):
            if shelf_type.filtro_campo not in ['e_manga', 'e_lancamento', 'e_destaque', 'adaptado_filme',
                                               'quantidade_vendida', 'tipo_shelf_especial']:
                problematic_fields.append((shelf_type.nome, shelf_type.filtro_campo))

        if problematic_fields:
            self.stdout.write('   🔧 Campos que precisam de correção:')
            for nome, campo in problematic_fields:
                self.stdout.write(f'      - {nome}: campo "{campo}" não existe')

                # Sugerir correção
                suggestions = {
                    'mangas': 'e_manga',
                    'lancamentos': 'e_lancamento',
                    'destaques': 'e_destaque',
                    'mais_vendidos': 'quantidade_vendida',
                    'filmes': 'adaptado_filme'
                }
                if campo in suggestions:
                    self.stdout.write(f'        💡 Sugestão: alterar para "{suggestions[campo]}"')

        self.stdout.write(f'\n✅ Diagnóstico concluído!')
        self.stdout.write('📝 Use essas informações para corrigir as configurações das prateleiras.')