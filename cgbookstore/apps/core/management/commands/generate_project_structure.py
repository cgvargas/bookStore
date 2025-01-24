# cgbookstore/apps/core/management/commands/generate_project_structure.py

import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import csv
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gera um arquivo CSV com a estrutura do projeto Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Diretório para salvar o arquivo CSV',
            default='project_structure'
        )
        parser.add_argument(
            '--ignore-dirs',
            nargs='+',
            help='Lista de diretórios para ignorar',
            default=['.git', '.venv', '__pycache__', 'migrations', 'node_modules', 'staticfiles', 'media']
        )
        parser.add_argument(
            '--ignore-files',
            nargs='+',
            help='Lista de extensões de arquivos para ignorar',
            default=['.pyc', '.pyo', '.pyd', '.so', '.dll']
        )

    def create_directory(self, base_path, dir_name):
        dir_path = os.path.join(base_path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def get_file_info(self, filepath):
        """Obtém informações básicas do arquivo"""
        stats = os.stat(filepath)
        return {
            'size': stats.st_size,
            'created': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_file_type(self, filename):
        """Determina o tipo do arquivo baseado na extensão"""
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.py': 'Python',
            '.html': 'Template HTML',
            '.js': 'JavaScript',
            '.css': 'CSS',
            '.sql': 'SQL',
            '.md': 'Markdown',
            '.txt': 'Texto',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.env': 'Environment',
            '.gitignore': 'Git Config',
            'requirements.txt': 'Dependencies'
        }
        if ext in type_map:
            return type_map[ext]
        return 'Outro'

    def handle(self, *args, **options):
        try:
            # Configuração dos diretórios
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = options.get('output_dir', os.path.join(base_dir, 'project_structure'))

            # Garante que o diretório existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Define o nome do arquivo com timestamp
            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'project_structure_{current_date}.csv'
            csv_path = os.path.join(output_dir, csv_filename)

            # Lista para armazenar as linhas do CSV
            structure_data = []

            # Log do processo
            self.stdout.write(f'Gerando estrutura do projeto em: {csv_path}')

            # Percorre a estrutura do projeto
            for root, dirs, files in os.walk(base_dir):
                # Remove diretórios ignorados
                dirs[:] = [d for d in dirs if d not in options['ignore_dirs']]

                # Processa cada arquivo
                for file in files:
                    if any(file.endswith(ext) for ext in options['ignore_files']):
                        continue

                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, base_dir)
                    file_info = self.get_file_info(filepath)

                    structure_data.append({
                        'Nome do Arquivo': file,
                        'Diretório': os.path.dirname(relative_path),
                        'Tipo': self.get_file_type(file),
                        'Tamanho (bytes)': file_info['size'],
                        'Data Criação': file_info['created'],
                        'Última Modificação': file_info['modified'],
                        'Caminho Completo': relative_path
                    })

            # Ordena os dados por diretório e nome do arquivo
            structure_data.sort(key=lambda x: (x['Diretório'], x['Nome do Arquivo']))

            # Escreve o arquivo CSV com BOM para Excel
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [
                    'Nome do Arquivo',
                    'Diretório',
                    'Tipo',
                    'Tamanho (bytes)',
                    'Data Criação',
                    'Última Modificação',
                    'Caminho Completo'
                ]
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=';'  # Usar ponto e vírgula como delimitador para Excel
                )
                writer.writeheader()
                writer.writerows(structure_data)

            # Cria o README
            readme_path = os.path.join(output_dir, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as readme:
                readme.write('# Estrutura do Projeto\n\n')
                readme.write(f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n')
                readme.write(f'Arquivo CSV: {csv_filename}\n\n')
                readme.write('## Informações\n\n')
                readme.write(f'- Total de arquivos: {len(structure_data)}\n')
                readme.write('- Tipos de arquivo encontrados:\n')

                file_types = {}
                for item in structure_data:
                    file_type = item['Tipo']
                    file_types[file_type] = file_types.get(file_type, 0) + 1

                for file_type, count in sorted(file_types.items()):
                    readme.write(f'  - {file_type}: {count}\n')

            self.stdout.write(
                self.style.SUCCESS(f'Estrutura do projeto gerada com sucesso em:\n{csv_path}')
            )
            logger.info(f'Estrutura do projeto gerada em: {csv_path}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao gerar estrutura do projeto: {str(e)}')
            )
            logger.error(f'Erro ao gerar estrutura do projeto: {str(e)}')