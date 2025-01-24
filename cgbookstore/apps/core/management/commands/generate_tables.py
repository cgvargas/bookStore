# cgbookstore/apps/core/management/commands/generate_tables.py

import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
import sqlite3
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gera arquivos SQL com a estrutura das tabelas do banco de dados SQLite3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Diretório para salvar os arquivos SQL',
            default='database_schemas'
        )

    def create_directory(self, base_path, dir_name):
        dir_path = os.path.join(base_path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def handle(self, *args, **options):
        try:
            # Configuração dos diretórios
            base_dir = settings.BASE_DIR
            schemas_dir = self.create_directory(base_dir, options['output_dir'])

            # Cria subdiretório com data atual
            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            version_dir = self.create_directory(schemas_dir, current_date)

            # Caminho do banco de dados SQLite
            db_path = os.path.join(base_dir, 'db.sqlite3')

            if not os.path.exists(db_path):
                self.stdout.write(self.style.ERROR('Banco de dados não encontrado!'))
                return

            # Conecta ao banco de dados
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Lista todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            # Arquivo principal que conterá todo o schema
            full_schema_path = os.path.join(version_dir, 'full_schema.sql')
            tables_dir = self.create_directory(version_dir, 'tables')
            indexes_dir = self.create_directory(version_dir, 'indexes')

            # Arquivo de resumo
            with open(os.path.join(version_dir, 'README.md'), 'w', encoding='utf-8') as readme:
                readme.write(f'# Schema do Banco de Dados\n\n')
                readme.write(f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n')
                readme.write('## Estrutura de Diretórios\n\n')
                readme.write('- tables/: Contém os scripts de criação das tabelas\n')
                readme.write('- indexes/: Contém os scripts de criação dos índices\n')
                readme.write('- full_schema.sql: Schema completo do banco\n\n')
                readme.write('## Tabelas\n\n')

            # Gera os arquivos SQL
            with open(full_schema_path, 'w', encoding='utf-8') as full_schema:
                full_schema.write('-- Schema completo do banco de dados\n')
                full_schema.write(f'-- Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n')

                for table in tables:
                    table_name = table[0]

                    if table_name == 'sqlite_sequence':
                        continue

                    # Obtém o schema da tabela
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                    create_table = cursor.fetchone()[0]

                    if create_table:
                        # Arquivo individual para a tabela
                        with open(os.path.join(tables_dir, f'{table_name}.sql'), 'w', encoding='utf-8') as f:
                            f.write(f"-- Tabela: {table_name}\n")
                            f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                            f.write(f"{create_table};\n")

                        # Obtém os índices
                        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}';")
                        indexes = cursor.fetchall()

                        if indexes:
                            with open(os.path.join(indexes_dir, f'{table_name}_indexes.sql'), 'w',
                                      encoding='utf-8') as f:
                                f.write(f"-- Índices da tabela: {table_name}\n")
                                f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                                for index in indexes:
                                    if index[0]:
                                        f.write(f"{index[0]};\n")

                        # Adiciona ao schema completo
                        full_schema.write(f"\n-- Tabela: {table_name}\n")
                        full_schema.write(f"{create_table};\n")

                        if indexes:
                            full_schema.write(f"\n-- Índices da tabela {table_name}\n")
                            for index in indexes:
                                if index[0]:
                                    full_schema.write(f"{index[0]};\n")
                        full_schema.write("\n")

                        # Atualiza o README
                        with open(os.path.join(version_dir, 'README.md'), 'a', encoding='utf-8') as readme:
                            readme.write(f'- {table_name}\n')

            conn.close()

            self.stdout.write(
                self.style.SUCCESS(f'Schemas gerados com sucesso em: {version_dir}')
            )
            logger.info(f'Schemas do banco de dados gerados em: {version_dir}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao gerar schemas do banco de dados: {str(e)}')
            )
            logger.error(f'Erro ao gerar schemas do banco de dados: {str(e)}')