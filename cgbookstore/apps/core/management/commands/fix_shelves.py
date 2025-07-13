# Script de correção e recriação de prateleiras
# Salve este código em: cgbookstore/apps/core/management/commands/fix_shelves.py

from django.core.management.base import BaseCommand
from django.db import transaction
from cgbookstore.apps.core.models.home_content import (
    DefaultShelfType, HomeSection, BookShelfSection
)
from cgbookstore.apps.core.models.book import Book


class Command(BaseCommand):
    help = 'Corrige e recria as prateleiras do sistema baseado nos dados existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa em modo simulação (não salva no banco)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO SIMULAÇÃO - Nenhuma alteração será salva\n'))
        else:
            self.stdout.write(self.style.SUCCESS('🚀 MODO EXECUÇÃO - Alterações serão salvas no banco\n'))

        self.stdout.write(self.style.SUCCESS('=== CORREÇÃO E RECRIAÇÃO DE PRATELEIRAS ===\n'))

        with transaction.atomic():
            # 1. Corrigir prateleira existente problemática
            self.stdout.write('🔧 ETAPA 1: Corrigindo prateleira existente...')
            self.fix_existing_shelf(dry_run)

            # 2. Criar prateleiras baseadas nos dados de tipo_shelf_especial
            self.stdout.write('\n📚 ETAPA 2: Criando prateleiras baseadas em tipo_shelf_especial...')
            self.create_shelves_from_data(dry_run)

            # 3. Criar prateleiras baseadas em campos booleanos
            self.stdout.write('\n✨ ETAPA 3: Criando prateleiras baseadas em campos booleanos...')
            self.create_boolean_shelves(dry_run)

            # 4. Criar seções da home para prateleiras órfãs
            self.stdout.write('\n🏠 ETAPA 4: Criando seções da home...')
            self.create_home_sections(dry_run)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\n🔍 SIMULAÇÃO CONCLUÍDA - Execute sem --dry-run para aplicar as alterações'))
                # Rollback da transação em modo dry-run
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS('\n✅ CORREÇÃO CONCLUÍDA COM SUCESSO!'))

    def fix_existing_shelf(self, dry_run):
        """Corrige a prateleira existente com configuração problemática"""
        try:
            # Buscar prateleira com campo problemático
            problematic_shelf = DefaultShelfType.objects.get(
                nome='Mangás',
                filtro_campo='mangas'
            )

            self.stdout.write(f'   🎯 Encontrada prateleira problemática: {problematic_shelf.nome}')
            self.stdout.write(f'      Campo atual: {problematic_shelf.filtro_campo}')
            self.stdout.write(f'      Valor atual: {problematic_shelf.filtro_valor}')

            if not dry_run:
                # Corrigir configuração
                problematic_shelf.filtro_campo = 'e_manga'
                problematic_shelf.filtro_valor = 'True'
                problematic_shelf.save()

            self.stdout.write(f'   ✅ Corrigido: campo alterado para "e_manga"')

        except DefaultShelfType.DoesNotExist:
            self.stdout.write('   ℹ️  Nenhuma prateleira problemática encontrada')

    def create_shelves_from_data(self, dry_run):
        """Cria prateleiras baseadas nos dados de tipo_shelf_especial"""

        # Mapeamento de tipos encontrados para configurações de prateleira
        shelf_configs = {
            'ebooks': {
                'nome': 'eBooks',
                'identificador': 'ebooks',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'ebooks',
                'ordem': 10
            },
            'tecnologia': {
                'nome': 'Tecnologia',
                'identificador': 'tecnologia',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'tecnologia',
                'ordem': 20
            },
            'destaques': {
                'nome': 'Destaques',
                'identificador': 'destaques',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'destaques',
                'ordem': 30
            },
            'mais_vendidos': {
                'nome': 'Mais Vendidos',
                'identificador': 'mais_vendidos',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'mais_vendidos',
                'ordem': 40
            },
            'lancamentos': {
                'nome': 'Lançamentos',
                'identificador': 'lancamentos',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'lancamentos',
                'ordem': 50
            },
            'filmes': {
                'nome': 'Adaptados para Filmes',
                'identificador': 'filmes',
                'filtro_campo': 'tipo_shelf_especial',
                'filtro_valor': 'filmes',
                'ordem': 60
            }
        }

        # Verificar quais tipos existem nos dados
        existing_types = Book.objects.values_list('tipo_shelf_especial', flat=True).distinct()
        existing_types = [t for t in existing_types if t]  # Remove valores None/vazios

        for tipo in existing_types:
            if tipo in shelf_configs:
                config = shelf_configs[tipo]

                # Verificar quantos livros existem para este tipo
                book_count = Book.objects.filter(tipo_shelf_especial=tipo).count()

                if book_count > 0:
                    # Verificar se já existe
                    existing = DefaultShelfType.objects.filter(
                        identificador=config['identificador']
                    ).first()

                    if not existing:
                        self.stdout.write(f'   📖 Criando prateleira: {config["nome"]} ({book_count} livros)')

                        if not dry_run:
                            DefaultShelfType.objects.create(
                                nome=config['nome'],
                                identificador=config['identificador'],
                                filtro_campo=config['filtro_campo'],
                                filtro_valor=config['filtro_valor'],
                                ordem=config['ordem'],
                                ativo=True
                            )
                        self.stdout.write(f'      ✅ Criada com sucesso')
                    else:
                        self.stdout.write(f'   ℹ️  Prateleira {config["nome"]} já existe')

    def create_boolean_shelves(self, dry_run):
        """Cria prateleiras baseadas em campos booleanos se não existirem equivalentes"""

        boolean_configs = [
            {
                'nome': 'Últimos Lançamentos',
                'identificador': 'ultimos_lancamentos',
                'filtro_campo': 'e_lancamento',
                'filtro_valor': 'True',
                'ordem': 15,
                'condition': 'e_lancamento=True'
            },
            {
                'nome': 'Livros em Destaque',
                'identificador': 'livros_destaque',
                'filtro_campo': 'e_destaque',
                'filtro_valor': 'True',
                'ordem': 25,
                'condition': 'e_destaque=True'
            },
            {
                'nome': 'Adaptações Cinematográficas',
                'identificador': 'adaptacoes_cinema',
                'filtro_campo': 'adaptado_filme',
                'filtro_valor': 'True',
                'ordem': 35,
                'condition': 'adaptado_filme=True'
            }
        ]

        for config in boolean_configs:
            # Verificar quantos livros existem
            if config['condition'] == 'e_lancamento=True':
                book_count = Book.objects.filter(e_lancamento=True).count()
            elif config['condition'] == 'e_destaque=True':
                book_count = Book.objects.filter(e_destaque=True).count()
            elif config['condition'] == 'adaptado_filme=True':
                book_count = Book.objects.filter(adaptado_filme=True).count()
            else:
                book_count = 0

            if book_count > 0:
                # Verificar se já existe
                existing = DefaultShelfType.objects.filter(
                    identificador=config['identificador']
                ).first()

                if not existing:
                    self.stdout.write(f'   ⭐ Criando prateleira: {config["nome"]} ({book_count} livros)')

                    if not dry_run:
                        DefaultShelfType.objects.create(
                            nome=config['nome'],
                            identificador=config['identificador'],
                            filtro_campo=config['filtro_campo'],
                            filtro_valor=config['filtro_valor'],
                            ordem=config['ordem'],
                            ativo=True
                        )
                    self.stdout.write(f'      ✅ Criada com sucesso')
                else:
                    self.stdout.write(f'   ℹ️  Prateleira {config["nome"]} já existe')

    def create_home_sections(self, dry_run):
        """Cria seções da home para prateleiras que não têm"""

        # Buscar todas as prateleiras ativas
        shelves = DefaultShelfType.objects.filter(ativo=True)

        for shelf in shelves:
            # Verificar se já existe uma seção da home para esta prateleira
            existing_section = HomeSection.objects.filter(
                book_shelf__shelf_type=shelf
            ).first()

            if not existing_section:
                self.stdout.write(f'   🏠 Criando seção da home para: {shelf.nome}')

                if not dry_run:
                    # Criar seção da home
                    home_section = HomeSection.objects.create(
                        titulo=shelf.nome,
                        tipo='shelf',
                        ordem=shelf.ordem,
                        ativo=True
                    )

                    # Criar prateleira associada
                    BookShelfSection.objects.create(
                        section=home_section,
                        shelf_type=shelf,
                        max_livros=12
                    )

                self.stdout.write(f'      ✅ Seção criada com sucesso')
            else:
                self.stdout.write(f'   ℹ️  Seção para {shelf.nome} já existe')

        # Resumo final
        if not dry_run:
            total_sections = HomeSection.objects.filter(tipo='shelf', ativo=True).count()
            self.stdout.write(f'\n📊 RESUMO: {total_sections} seções de prateleiras ativas no sistema')