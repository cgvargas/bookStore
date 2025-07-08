#!/usr/bin/env python
"""
Script para Encontrar Todos os Templates com Imagens
Arquivo: tests/find_all_templates_with_images.py
Objetivo: Localizar todos os templates que renderizam imagens de livros e identificar problemas
"""

import os
import re
from pathlib import Path


class TemplateImageFinder:
    def __init__(self):
        self.results = {
            'templates_with_direct_urls': [],
            'templates_with_proxy_urls': [],
            'templates_with_image_refs': [],
            'templates_to_fix': []
        }

    def print_header(self, title):
        """Imprimir cabeçalho formatado"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    def find_template_files(self):
        """Encontrar todos os arquivos de template"""
        template_dirs = [
            Path("cgbookstore/apps/core/templates"),
            Path("cgbookstore/apps/chatbot_literario/templates")
        ]

        template_files = []

        for template_dir in template_dirs:
            if template_dir.exists():
                # Buscar recursivamente por arquivos .html
                html_files = list(template_dir.rglob("*.html"))
                template_files.extend(html_files)

        return template_files

    def analyze_template_file(self, template_path):
        """Analisar um arquivo de template específico"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analysis = {
                'path': str(template_path),
                'relative_path': str(template_path).replace('cgbookstore/', ''),
                'has_images': False,
                'direct_url_issues': [],
                'proxy_urls': [],
                'image_references': [],
                'needs_fixing': False
            }

            # Procurar por referências de imagem relacionadas a livros
            image_patterns = [
                # Padrões de URL direta problemáticos
                (r'{{ *livro\.capa_url *}}', 'direct_livro_capa_url'),
                (r'{{ *book\.capa_url *}}', 'direct_book_capa_url'),
                (r'{{ *livro\.get_capa_url *}}', 'livro_get_capa_url'),
                (r'{{ *book\.get_capa_url *}}', 'book_get_capa_url'),

                # Padrões de proxy (corretos)
                (r'{% *url [\'"]image_proxy[\'"] *%}', 'proxy_url'),
                (r'/image-proxy/', 'proxy_direct'),

                # Outros padrões de imagem
                (r'<img[^>]*src=[\'"][^\'">]*livro[^\'">]*[\'"]', 'img_tag_livro'),
                (r'<img[^>]*src=[\'"][^\'">]*book[^\'">]*[\'"]', 'img_tag_book'),
                (r'books\.google\.com', 'google_books_direct'),
                (r'{{ *[^}]*imageLinks[^}]* *}}', 'image_links_var'),
                (r'{{ *[^}]*thumbnail[^}]* *}}', 'thumbnail_var'),
            ]

            for pattern, pattern_type in image_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis['has_images'] = True

                    if pattern_type in ['direct_livro_capa_url', 'direct_book_capa_url', 'google_books_direct']:
                        analysis['direct_url_issues'].append({
                            'type': pattern_type,
                            'matches': matches,
                            'pattern': pattern
                        })
                        analysis['needs_fixing'] = True

                    elif pattern_type in ['proxy_url', 'proxy_direct']:
                        analysis['proxy_urls'].append({
                            'type': pattern_type,
                            'matches': matches
                        })

                    analysis['image_references'].append({
                        'type': pattern_type,
                        'count': len(matches),
                        'matches': matches[:3]  # Primeiros 3 para não poluir
                    })

            return analysis

        except Exception as e:
            print(f"❌ Erro ao analisar {template_path}: {str(e)}")
            return None

    def extract_problematic_lines(self, template_path, issues):
        """Extrair linhas específicas com problemas"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            problematic_lines = []

            for issue in issues:
                pattern = issue['pattern']
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        problematic_lines.append({
                            'line_number': i,
                            'content': line.strip(),
                            'issue_type': issue['type']
                        })

            return problematic_lines

        except Exception as e:
            print(f"❌ Erro ao extrair linhas de {template_path}: {str(e)}")
            return []

    def run_analysis(self):
        """Executar análise completa"""
        self.print_header("BUSCA POR TEMPLATES COM PROBLEMAS DE IMAGEM")

        print("🔍 Procurando arquivos de template...")
        template_files = self.find_template_files()
        print(f"📋 Encontrados {len(template_files)} arquivos de template")

        templates_with_issues = []
        templates_with_images = []
        templates_using_proxy = []

        for template_file in template_files:
            analysis = self.analyze_template_file(template_file)

            if analysis and analysis['has_images']:
                templates_with_images.append(analysis)

                if analysis['needs_fixing']:
                    templates_with_issues.append(analysis)

                if analysis['proxy_urls']:
                    templates_using_proxy.append(analysis)

        # Resultados
        self.print_header("TEMPLATES COM REFERÊNCIAS DE IMAGEM")
        print(f"📊 Total de templates com imagens: {len(templates_with_images)}")
        print(f"🚨 Templates com problemas: {len(templates_with_issues)}")
        print(f"✅ Templates usando proxy: {len(templates_using_proxy)}")

        # Listar templates com problemas
        if templates_with_issues:
            self.print_header("TEMPLATES QUE PRECISAM DE CORREÇÃO")

            for analysis in templates_with_issues:
                print(f"\n📄 {analysis['relative_path']}")

                for issue in analysis['direct_url_issues']:
                    print(f"   🚨 {issue['type']}: {len(issue['matches'])} ocorrências")

                # Extrair linhas problemáticas
                problematic_lines = self.extract_problematic_lines(
                    Path(analysis['path']),
                    analysis['direct_url_issues']
                )

                if problematic_lines:
                    print(f"   📋 Linhas com problemas:")
                    for line_info in problematic_lines[:3]:  # Mostrar apenas as 3 primeiras
                        print(f"      Linha {line_info['line_number']}: {line_info['content'][:80]}...")

        # Listar templates já corretos
        if templates_using_proxy:
            self.print_header("TEMPLATES JÁ USANDO PROXY (CORRETOS)")

            for analysis in templates_using_proxy:
                print(f"✅ {analysis['relative_path']}")
                for proxy_info in analysis['proxy_urls']:
                    print(f"   📡 {proxy_info['type']}: {len(proxy_info['matches'])} usos")

        # Gerar lista de correções necessárias
        self.generate_fix_recommendations(templates_with_issues)

        return templates_with_issues

    def generate_fix_recommendations(self, templates_with_issues):
        """Gerar recomendações específicas de correção"""
        self.print_header("RECOMENDAÇÕES DE CORREÇÃO")

        if not templates_with_issues:
            print("✅ Nenhuma correção necessária encontrada!")
            return

        print(f"📝 {len(templates_with_issues)} templates precisam de correção:")

        for i, analysis in enumerate(templates_with_issues, 1):
            print(f"\n{i}. {analysis['relative_path']}")

            # Recomendações específicas por tipo de problema
            for issue in analysis['direct_url_issues']:
                if issue['type'] == 'direct_livro_capa_url':
                    print(f"   🔧 Substituir: {{ livro.capa_url }}")
                    print(f"   ✅ Por: {{% url 'image_proxy' %}}?url={{ livro.capa_url|urlencode }}")

                elif issue['type'] == 'direct_book_capa_url':
                    print(f"   🔧 Substituir: {{ book.capa_url }}")
                    print(f"   ✅ Por: {{% url 'image_proxy' %}}?url={{ book.capa_url|urlencode }}")

                elif issue['type'] == 'google_books_direct':
                    print(f"   🔧 URL direta do Google Books encontrada")
                    print(f"   ✅ Verificar se está usando proxy")

            print(f"   📋 Adicionar: onerror=\"this.src='{{% static 'images/no-cover.svg' %}}';\"")
            print(f"   📋 Adicionar: loading=\"lazy\" class=\"google-books-image\"")

        print(f"\n💡 Padrão de correção completo:")
        print(f"   <img src=\"{{% url 'image_proxy' %}}?url={{ livro.capa_url|urlencode }}\"")
        print(f"        alt=\"{{ livro.titulo }}\"")
        print(f"        class=\"book-image google-books-image\"")
        print(f"        loading=\"lazy\"")
        print(f"        onerror=\"this.onerror=null; this.src='{{% static 'images/no-cover.svg' %}}';\"")
        print(f"        data-original-src=\"{{ livro.capa_url }}\">")

    def generate_file_list(self, templates_with_issues):
        """Gerar lista de arquivos para correção"""
        self.print_header("LISTA DE ARQUIVOS PARA CORREÇÃO")

        if not templates_with_issues:
            print("✅ Nenhum arquivo precisa de correção!")
            return

        print("📝 Copie esta lista para corrigir os arquivos:")
        print("")

        for analysis in templates_with_issues:
            print(f"📄 {analysis['path']}")

        print(f"\n📊 Total: {len(templates_with_issues)} arquivos")


if __name__ == "__main__":
    finder = TemplateImageFinder()
    issues = finder.run_analysis()

    if issues:
        finder.generate_file_list(issues)

    print("\n" + "=" * 70)
    print("Análise concluída. Corrija os templates listados acima.")
    print("=" * 70)