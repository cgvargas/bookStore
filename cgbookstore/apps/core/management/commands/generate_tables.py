# cgbookstore/apps/core/management/commands/generate_tables.py

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
import logging
import importlib.util
import sys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Gera arquivos SQL com a estrutura das tabelas do banco de dados PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Diretório para salvar os arquivos SQL',
            default='database_schemas'
        )
        parser.add_argument(
            '--visualize',
            action='store_true',
            help='Gera um arquivo HTML com visualização das tabelas'
        )
        parser.add_argument(
            '--show-data',
            action='store_true',
            help='Inclui dados das tabelas na visualização HTML'
        )
        parser.add_argument(
            '--max-rows',
            type=int,
            default=100,
            help='Número máximo de linhas a serem exibidas por tabela (padrão: 100)'
        )

    def create_directory(self, base_path, dir_name):
        dir_path = os.path.join(base_path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def ensure_table_visualizer(self):
        """
        Garante que o módulo TableVisualizer exista.
        Se não existir, cria o arquivo do módulo.
        """
        # Caminho para o diretório utils em management
        utils_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
        if not os.path.exists(utils_dir):
            os.makedirs(utils_dir)

        # Arquivo de inicialização para o pacote
        init_file = os.path.join(utils_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# Package initialization\n')

        # Caminho para o arquivo table_visualizer.py
        visualizer_path = os.path.join(utils_dir, 'table_visualizer.py')

        # Se o arquivo não existir, cria-o
        if not os.path.exists(visualizer_path):
            with open(visualizer_path, 'w', encoding='utf-8') as f:
                f.write(self.get_table_visualizer_code())

        # Adiciona o diretório ao path para importação
        sys.path.append(os.path.dirname(utils_dir))

        return visualizer_path

    def handle(self, *args, **options):
        try:
            # Configuração dos diretórios
            base_dir = settings.BASE_DIR
            schemas_dir = self.create_directory(base_dir, options['output_dir'])

            # Cria subdiretório com data atual
            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            version_dir = self.create_directory(schemas_dir, current_date)

            # Verifica tipo de banco em uso
            db_engine = settings.DATABASES['default']['ENGINE']

            if 'sqlite3' in db_engine:
                self.stdout.write(
                    self.style.WARNING('Este comando foi atualizado para PostgreSQL. SQLite não é mais suportado.'))
                return

            if 'postgresql' not in db_engine:
                self.stdout.write(self.style.ERROR(f'Banco de dados não suportado: {db_engine}'))
                return

            # Diretórios para diferentes partes do schema
            tables_dir = self.create_directory(version_dir, 'tables')
            indexes_dir = self.create_directory(version_dir, 'indexes')
            constraints_dir = self.create_directory(version_dir, 'constraints')
            functions_dir = self.create_directory(version_dir, 'functions')

            # Obter conexão ao PostgreSQL
            connection = connections['default']
            cursor = connection.cursor()

            # Arquivo de resumo
            with open(os.path.join(version_dir, 'README.md'), 'w', encoding='utf-8') as readme:
                readme.write(f'# Schema do Banco de Dados PostgreSQL\n\n')
                readme.write(f'Data de geração: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n')
                readme.write('## Estrutura de Diretórios\n\n')
                readme.write('- tables/: Contém os scripts de criação das tabelas\n')
                readme.write('- indexes/: Contém os scripts de criação dos índices\n')
                readme.write('- constraints/: Contém os scripts de criação das constraints\n')
                readme.write('- functions/: Contém as funções e procedimentos\n')
                readme.write('- full_schema.sql: Schema completo do banco\n\n')
                readme.write('## Tabelas\n\n')

            # Arquivo principal que conterá todo o schema
            full_schema_path = os.path.join(version_dir, 'full_schema.sql')
            with open(full_schema_path, 'w', encoding='utf-8') as full_schema:
                full_schema.write('-- Schema completo do banco de dados PostgreSQL\n')
                full_schema.write(f'-- Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n')

                # Obter todas as tabelas de esquemas públicos
                cursor.execute("""
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_schema, table_name;
                """)
                tables = cursor.fetchall()

                for schema, table_name in tables:
                    # Gera script de criação da tabela
                    cursor.execute(f"""
                        SELECT 
                            'CREATE TABLE ' || 
                            quote_ident(table_schema) || '.' || quote_ident(table_name) || ' (' ||
                            string_agg(
                                quote_ident(column_name) || ' ' ||
                                data_type || 
                                CASE 
                                    WHEN character_maximum_length IS NOT NULL 
                                    THEN '(' || character_maximum_length || ')'
                                    ELSE ''
                                END ||
                                CASE 
                                    WHEN is_nullable = 'NO' THEN ' NOT NULL'
                                    ELSE ''
                                END,
                                ', '
                            ) ||
                            ');'
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        AND table_name = %s
                        GROUP BY table_schema, table_name;
                    """, [schema, table_name])

                    create_table_result = cursor.fetchone()
                    create_table = create_table_result[0] if create_table_result else None

                    if create_table:
                        # Arquivo individual para a tabela
                        with open(os.path.join(tables_dir, f'{table_name}.sql'), 'w', encoding='utf-8') as f:
                            f.write(f"-- Tabela: {schema}.{table_name}\n")
                            f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                            f.write(f"{create_table}\n")

                        # Adiciona ao schema completo
                        full_schema.write(f"\n-- Tabela: {schema}.{table_name}\n")
                        full_schema.write(f"{create_table}\n\n")

                        # Obtém as constraints da tabela
                        cursor.execute("""
                            SELECT
                                pg_get_constraintdef(c.oid)
                            FROM
                                pg_constraint c
                            JOIN
                                pg_class t ON c.conrelid = t.oid
                            JOIN
                                pg_namespace n ON t.relnamespace = n.oid
                            WHERE
                                t.relname = %s
                                AND n.nspname = %s
                        """, [table_name, schema])

                        constraints = cursor.fetchall()
                        if constraints:
                            with open(os.path.join(constraints_dir, f'{table_name}_constraints.sql'), 'w',
                                      encoding='utf-8') as f:
                                f.write(f"-- Constraints da tabela: {schema}.{table_name}\n")
                                f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                                for constraint in constraints:
                                    f.write(f"ALTER TABLE {schema}.{table_name} ADD CONSTRAINT {constraint[0]};\n")

                            full_schema.write(f"-- Constraints da tabela {schema}.{table_name}\n")
                            for constraint in constraints:
                                full_schema.write(
                                    f"ALTER TABLE {schema}.{table_name} ADD CONSTRAINT {constraint[0]};\n")
                            full_schema.write("\n")

                        # Obtém os índices da tabela
                        cursor.execute("""
                            SELECT
                                indexdef
                            FROM
                                pg_indexes
                            WHERE
                                tablename = %s
                                AND schemaname = %s
                        """, [table_name, schema])

                        indexes = cursor.fetchall()
                        if indexes:
                            with open(os.path.join(indexes_dir, f'{table_name}_indexes.sql'), 'w',
                                      encoding='utf-8') as f:
                                f.write(f"-- Índices da tabela: {schema}.{table_name}\n")
                                f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                                for index in indexes:
                                    f.write(f"{index[0]};\n")

                            full_schema.write(f"-- Índices da tabela {schema}.{table_name}\n")
                            for index in indexes:
                                full_schema.write(f"{index[0]};\n")
                            full_schema.write("\n")

                        # Atualiza o README
                        with open(os.path.join(version_dir, 'README.md'), 'a', encoding='utf-8') as readme:
                            readme.write(f'- {schema}.{table_name}\n')

                # Gerar visualização HTML se solicitado
                visualize = options.get('visualize', False)
                show_data = options.get('show_data', False)
                max_rows = options.get('max_rows', 100)

                if visualize:
                    self.stdout.write(self.style.SUCCESS("Gerando visualização HTML..."))

                    # Garantir que o módulo TableVisualizer esteja disponível
                    visualizer_path = self.ensure_table_visualizer()

                    # Importar o módulo TableVisualizer
                    spec = importlib.util.spec_from_file_location("table_visualizer", visualizer_path)
                    table_visualizer_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(table_visualizer_module)

                    # Criar uma instância do TableVisualizer
                    visualizer = table_visualizer_module.TableVisualizer(cursor)

                    # Gerar a visualização HTML
                    html_path = visualizer.generate_html(version_dir, show_data, max_rows)

                    if html_path:
                        self.stdout.write(self.style.SUCCESS(f"Visualização HTML gerada em: {html_path}"))
                    else:
                        self.stdout.write(self.style.WARNING("Não foi possível gerar a visualização HTML"))

                # Obtém as funções
                cursor.execute("""
                    SELECT
                        n.nspname as schema_name,
                        p.proname as function_name,
                        pg_get_functiondef(p.oid) as function_def
                    FROM
                        pg_proc p
                    JOIN
                        pg_namespace n ON p.pronamespace = n.oid
                    WHERE
                        n.nspname = 'public'
                    ORDER BY
                        n.nspname, p.proname;
                """)

                functions = cursor.fetchall()
                if functions:
                    full_schema.write("\n-- Funções\n")
                    for schema, function_name, function_def in functions:
                        with open(os.path.join(functions_dir, f'{function_name}.sql'), 'w',
                                  encoding='utf-8') as f:
                            f.write(f"-- Função: {schema}.{function_name}\n")
                            f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                            f.write(f"{function_def};\n")

                        full_schema.write(f"\n-- Função: {schema}.{function_name}\n")
                        full_schema.write(f"{function_def};\n")

            self.stdout.write(
                self.style.SUCCESS(f'Schemas gerados com sucesso em: {version_dir}')
            )
            logger.info(f'Schemas do banco de dados PostgreSQL gerados em: {version_dir}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao gerar schemas do banco de dados: {str(e)}')
            )
            logger.error(f'Erro ao gerar schemas do banco de dados: {str(e)}')

    def get_table_visualizer_code(self):
        """
        Retorna o código fonte do módulo TableVisualizer.
        Este código é utilizado para criar o arquivo table_visualizer.py
        caso ele não exista.
        """
        return '''# cgbookstore/apps/core/management/utils/table_visualizer.py'''

import os
from datetime import datetime
import html
import json
from decimal import Decimal

class TableVisualizer:
    """
    Classe auxiliar para gerar visualização HTML das tabelas do banco de dados.
    """

    def __init__(self, cursor):
        """
        Inicializa o visualizador.

        Args:
            cursor: Cursor do banco de dados
        """
        self.cursor = cursor

    def json_serializer(self, obj):
        """Helper para serializar tipos especiais para JSON"""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)

    def generate_html(self, output_dir, show_data=False, max_rows=100):
        """
        Gera um arquivo HTML com visualização das tabelas e seus relacionamentos

        Args:
            output_dir: Diretório onde salvar o arquivo HTML
            show_data: Se True, inclui os dados das tabelas na visualização
            max_rows: Número máximo de linhas a exibir por tabela

        Returns:
            str: Caminho para o arquivo HTML gerado ou None em caso de erro
        """
        try:
            # Obter todas as tabelas
            self.cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = self.cursor.fetchall()

            # Estrutura inicial do HTML
            html_content = self._generate_html_header()

            # Adicionar links de navegação
            html_content += '<div class="nav-content">\\n'
            for schema, table_name in tables:
                html_content += f'<a href="#{table_name}">{table_name}</a>\\n'
            html_content += '</div></div>\\n'

            # Para cada tabela
            for schema, table_name in tables:
                html_content += self._generate_table_section(schema, table_name, show_data, max_rows)

            # Adicionar seção de relacionamentos
            html_content += self._generate_relationships_section()

            # Finalização do HTML
            html_content += f"""
                <div class="timestamp">
                    Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            </body>
            </html>
            """

            # Salvar o arquivo HTML
            html_file_path = os.path.join(output_dir, 'database_visualization.html')
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return html_file_path

        except Exception as e:
            print(f'Erro ao gerar visualização HTML: {str(e)}')
            return None

    def _generate_html_header(self):
        """Gera o cabeçalho do HTML com estilos e scripts"""
        return """
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Visualização do Banco de Dados PostgreSQL</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #2980b9;
                    margin-top: 30px;
                }
                .table-container {
                    margin-bottom: 30px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    overflow: hidden;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                .table-header {
                    background-color: #3498db;
                    color: white;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 1.1em;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .table-content {
                    padding: 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    text-align: left;
                    padding: 12px 15px;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                tr:hover {
                    background-color: #e9f7fe;
                }
                .primary-key {
                    color: #e74c3c;
                    font-weight: bold;
                }
                .foreign-key {
                    color: #27ae60;
                    font-weight: bold;
                }
                .null {
                    color: #7f8c8d;
                    font-style: italic;
                }
                .relationship-section {
                    margin-top: 50px;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }
                .index-section {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #f8f8f8;
                    border-left: 3px solid #3498db;
                }
                .timestamp {
                    text-align: right;
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin: 40px 0 20px;
                }
                .nav {
                    position: sticky;
                    top: 0;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    z-index: 100;
                }
                .nav-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .nav a {
                    display: inline-block;
                    margin: 5px 10px 5px 0;
                    text-decoration: none;
                    color: #3498db;
                }
                .nav a:hover {
                    text-decoration: underline;
                }
                .tab-container {
                    margin-top: 10px;
                }
                .tab-buttons {
                    display: flex;
                    border-bottom: 1px solid #ddd;
                }
                .tab-button {
                    padding: 10px 15px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-bottom: none;
                    border-radius: 5px 5px 0 0;
                    margin-right: 5px;
                    cursor: pointer;
                }
                .tab-button.active {
                    background-color: white;
                    border-bottom: 1px solid white;
                    margin-bottom: -1px;
                }
                .tab-content {
                    display: none;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-top: none;
                }
                .tab-content.active {
                    display: block;
                }
                .data-table {
                    overflow-x: auto;
                    max-height: 500px;
                    overflow-y: auto;
                }
                .data-hint {
                    padding: 10px;
                    background-color: #ffffcc;
                    border-left: 4px solid #ffcc00;
                    margin-bottom: 15px;
                }
                .toggle-button {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.8em;
                }
                .json-view {
                    font-family: monospace;
                    white-space: pre-wrap;
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 4px;
                    border: 1px solid #ddd;
                    max-height: 200px;
                    overflow: auto;
                }
                .pagination {
                    display: flex;
                    justify-content: center;
                    margin-top: 15px;
                }
                .pagination button {
                    margin: 0 5px;
                    padding: 5px 10px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .pagination button:hover {
                    background-color: #e5e5e5;
                }
                .pagination button:disabled {
                    cursor: not-allowed;
                    opacity: 0.5;
                }
            </style>
            <script>
                // Script JavaScript para interatividade da página
                document.addEventListener('DOMContentLoaded', function() {
                    // Função para alternar abas
                    function setupTabs() {
                        const tabButtons = document.querySelectorAll('.tab-button');

                        tabButtons.forEach(button => {
                            button.addEventListener('click', function() {
                                // Remove a classe ativa de todos os botões e conteúdos
                                const parent = this.closest('.tab-container');
                                parent.querySelectorAll('.tab-button').forEach(btn => {
                                    btn.classList.remove('active');
                                });
                                parent.querySelectorAll('.tab-content').forEach(content => {
                                    content.classList.remove('active');
                                });

                                // Adiciona a classe ativa ao botão clicado e ao conteúdo correspondente
                                this.classList.add('active');
                                const target = this.getAttribute('data-target');
                                document.getElementById(target).classList.add('active');
                            });
                        });
                    }

                    // Funções para paginação de dados
                    function setupPagination() {
                        // Para cada tabela de dados
                        document.querySelectorAll('.paginated-table').forEach(table => {
                            const tableId = table.getAttribute('id');
                            const rows = table.querySelectorAll('tbody tr');
                            const rowsPerPage = 20;
                            const pageCount = Math.ceil(rows.length / rowsPerPage);

                            // Criar navegação de páginas
                            const paginationContainer = document.createElement('div');
                            paginationContainer.className = 'pagination';
                            paginationContainer.innerHTML = `
                                <button class="prev-page" disabled>Anterior</button>
                                <span class="page-info">Página 1 de ${pageCount}</span>
                                <button class="next-page" ${pageCount <= 1 ? 'disabled' : ''}>Próxima</button>
                            `;

                            // Adicionar depois da tabela
                            table.parentNode.insertBefore(paginationContainer, table.nextSibling);

                            // Esconder todas as linhas exceto as primeiras rowsPerPage
                            rows.forEach((row, index) => {
                                if (index >= rowsPerPage) {
                                    row.style.display = 'none';
                                }
                            });

                            // Gerenciar estado da paginação
                            let currentPage = 1;
                            const prevButton = paginationContainer.querySelector('.prev-page');
                            const nextButton = paginationContainer.querySelector('.next-page');
                            const pageInfo = paginationContainer.querySelector('.page-info');

                            // Função para mudar de página
                            function goToPage(page) {
                                rows.forEach((row, index) => {
                                    const startRow = (page - 1) * rowsPerPage;
                                    const endRow = startRow + rowsPerPage - 1;

                                    if (index >= startRow && index <= endRow) {
                                        row.style.display = '';
                                    } else {
                                        row.style.display = 'none';
                                    }
                                });

                                // Atualizar botões e informações
                                prevButton.disabled = page === 1;
                                nextButton.disabled = page === pageCount;
                                pageInfo.textContent = `Página ${page} de ${pageCount}`;
                            }

                            // Adicionar event listeners
                            prevButton.addEventListener('click', () => {
                                if (currentPage > 1) {
                                    currentPage--;
                                    goToPage(currentPage);
                                }
                            });

                            nextButton.addEventListener('click', () => {
                                if (currentPage < pageCount) {
                                    currentPage++;
                                    goToPage(currentPage);
                                }
                            });
                        });
                    }

                    // Função para formatar JSON
                    function prettifyJson() {
                        document.querySelectorAll('.json-view').forEach(element => {
                            try {
                                const jsonText = element.textContent.trim();
                                if (jsonText && jsonText !== 'null') {
                                    const jsonObj = JSON.parse(jsonText);
                                    element.textContent = JSON.stringify(jsonObj, null, 2);
                                }
                            } catch (e) {
                                console.error('Erro ao formatar JSON:', e);
                            }
                        });
                    }

                    // Inicializar todas as funções
                    setupTabs();
                    setupPagination();
                    prettifyJson();

                    // Tornar todas as abas "Estrutura" ativas por padrão
                    document.querySelectorAll('.tab-container').forEach(container => {
                        const structureTab = container.querySelector('.tab-button[data-target$="-structure"]');
                        if (structureTab) {
                            structureTab.click();
                        }
                    });
                });
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Visualização do Banco de Dados PostgreSQL</h1>
                <div class="nav">
                    <div class="nav-title">Navegação:</div>
        """

    def _generate_table_section(self, schema, table_name, show_data, max_rows):
        """Gera o HTML para cada tabela do banco de dados"""
        html_content = f"""
            <div class="table-container" id="{table_name}">
                <div class="table-header">
                    <span>{html.escape(table_name)}</span>
                    <span>({schema})</span>
                </div>
                <div class="tab-container">
                    <div class="tab-buttons">
                        <button class="tab-button active" data-target="{table_name}-structure">Estrutura</button>
        """
        
        if show_data:
            html_content += f'<button class="tab-button" data-target="{table_name}-data">Dados</button>\n'
        
        html_content += f"""
                    </div>
                    <div id="{table_name}-structure" class="tab-content active">
                        <table>
                            <thead>
                                <tr>
                                    <th>Coluna</th>
                                    <th>Tipo</th>
                                    <th>Nullable</th>
                                    <th>Default</th>
                                    <th>Descrição</th>
                                </tr>
                            </thead>
                            <tbody>
        """
        
        # Obter colunas da tabela
        self.cursor.execute("""
            SELECT 
                column_name, 
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                NULL as description
            FROM 
                information_schema.columns c
            WHERE 
                table_schema = %s
                AND table_name = %s
            ORDER BY 
                ordinal_position;
        """, [schema, table_name])
        
        columns = self.cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        # Obter chaves primárias
        self.cursor.execute("""
            SELECT 
                kcu.column_name
            FROM 
                information_schema.table_constraints tc
            JOIN 
                information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name 
                AND tc.table_schema = kcu.table_schema
            WHERE 
                tc.constraint_type = 'PRIMARY KEY' 
                AND tc.table_schema = %s
                AND tc.table_name = %s;
        """, [schema, table_name])
        
        primary_keys = [pk[0] for pk in self.cursor.fetchall()]
        
        # Obter chaves estrangeiras
        self.cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
            JOIN
                information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN
                information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s;
        """, [schema, table_name])
        
        foreign_keys = {}
        for fk in self.cursor.fetchall():
            foreign_keys[fk[0]] = {
                'foreign_table': fk[1],
                'foreign_column': fk[2]
            }
        
        # Adicionar linhas para cada coluna
        for column in columns:
            column_name, data_type, max_length, is_nullable, default_value, description = column
            
            # Formatar tipo de dados com comprimento máximo, se aplicável
            formatted_type = data_type
            if max_length is not None:
                formatted_type += f"({max_length})"
            
            # Adicionar classe CSS baseada no tipo de chave
            column_class = ""
            column_description = description or ""
            
            if column_name in primary_keys:
                column_class = "primary-key"
                column_description = "Chave Primária" + (f": {column_description}" if column_description else "")
            elif column_name in foreign_keys:
                column_class = "foreign-key"
                fk_info = foreign_keys[column_name]
                column_description = f"Chave Estrangeira → {fk_info['foreign_table']}.{fk_info['foreign_column']}" + (f": {column_description}" if column_description else "")
            
            html_content += f"""
                <tr>
                    <td class="{column_class}">{html.escape(column_name)}</td>
                    <td>{html.escape(formatted_type)}</td>
                    <td>{"No" if is_nullable == "NO" else "Yes"}</td>
                    <td>{html.escape(str(default_value)) if default_value is not None else ""}</td>
                    <td>{html.escape(column_description)}</td>
                </tr>
            """
        
        html_content += """
                            </tbody>
                        </table>
        """
        
        # Adicionar índices
        self.cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s
            AND tablename = %s
        """, [schema, table_name])
        
        indexes = self.cursor.fetchall()
        if indexes:
            html_content += """
                <div class="index-section">
                    <h3>Índices</h3>
                    <ul>
            """
            
            for idx_name, idx_def in indexes:
                html_content += f"<li><code>{html.escape(idx_def)}</code></li>\n"
            
            html_content += """
                    </ul>
                </div>
            """
        
        html_content += """
                    </div>
        """
        
        # Adicionar dados da tabela, se solicitado
        if show_data:
            html_content += f"""
                <div id="{table_name}-data" class="tab-content">
                    <div class="data-hint">
                        Mostrando até {max_rows} registros da tabela {table_name}.
                    </div>
                    <div class="data-table">
            """
            
            try:
                # Consultar dados da tabela
                self.cursor.execute(f"""
                    SELECT * FROM {schema}.{table_name} LIMIT %s;
                """, [max_rows])
                rows = self.cursor.fetchall()
                
                if rows:
                    # Obter nomes das colunas
                    col_names = [desc[0] for desc in self.cursor.description]
                    
                    html_content += f"""
                        <table class="paginated-table" id="{table_name}-data-table">
                            <thead>
                                <tr>
                    """
                    
                    # Cabeçalhos da tabela
                    for col_name in col_names:
                        html_content += f"<th>{html.escape(col_name)}</th>\n"
                    
                    html_content += """
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    # Linhas de dados
                    for row in rows:
                        html_content += "<tr>\n"
                        for i, value in enumerate(row):
                            cell_value = value
                            
                            # Tratar valores especiais
                            if value is None:
                                cell_value = '<span class="null">NULL</span>'
                            elif isinstance(value, (dict, list)) or (isinstance(value, str) and value.startswith('{') and value.endswith('}')):
                                try:
                                    if isinstance(value, str):
                                        # Tenta converter string de JSON para objeto
                                        json_obj = json.loads(value)
                                        cell_value = f'<div class="json-view">{html.escape(json.dumps(json_obj))}</div>'
                                    else:
                                        cell_value = f'<div class="json-view">{html.escape(json.dumps(value, default=self.json_serializer))}</div>'
                                except:
                                    cell_value = html.escape(str(value))
                            else:
                                cell_value = html.escape(str(value))
                            
                            html_content += f"<td>{cell_value}</td>\n"
                        html_content += "</tr>\n"
                    
                    html_content += """
                            </tbody>
                        </table>
                    """
                else:
                    html_content += "<p>Esta tabela não contém dados.</p>"
            except Exception as e:
                html_content += f"""
                    <p>Erro ao obter dados: {html.escape(str(e))}</p>
                """
            
            html_content += """
                    </div>
                </div>
            """
        
        html_content += """
                </div>
            </div>
        """
        
        return html_content