from django.core.management.base import BaseCommand
import os
import re
import inspect
import sys
import traceback


class Command(BaseCommand):
    help = 'Correção abrangente para o problema do chatbot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplicar as correções (sem essa flag, apenas mostra o que seria alterado)',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Fazer backup dos arquivos antes de modificá-los',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        make_backup = options['backup']

        self.stdout.write(self.style.WARNING("\nCORREÇÃO ABRANGENTE DO CHATBOT"))
        self.stdout.write(self.style.WARNING("=" * 40))

        if not apply_changes:
            self.stdout.write(self.style.WARNING(
                "\nModo de simulação ativado. Nenhuma alteração será feita.\n"
                "Use --apply para aplicar as correções."
            ))

        # Localizar a raiz do projeto
        project_root = self.find_project_root()
        if not project_root:
            self.stdout.write(self.style.ERROR("Não foi possível localizar a raiz do projeto."))
            return

        self.stdout.write(f"Raiz do projeto: {project_root}")

        # Localizar diretório do aplicativo chatbot_literario
        chatbot_app_dir = os.path.join(project_root, 'cgbookstore', 'apps', 'chatbot_literario')
        if not os.path.exists(chatbot_app_dir):
            self.stdout.write(self.style.ERROR(f"Diretório do aplicativo não encontrado: {chatbot_app_dir}"))
            return

        self.stdout.write(f"Diretório do aplicativo: {chatbot_app_dir}")

        # Arquivos a verificar
        files_to_check = [
            os.path.join(chatbot_app_dir, 'services', 'chatbot_service.py'),
            os.path.join(chatbot_app_dir, 'services', 'training_service.py'),
            os.path.join(chatbot_app_dir, 'views.py'),
        ]

        # Verificar e corrigir cada arquivo
        for file_path in files_to_check:
            if os.path.exists(file_path):
                self.check_and_fix_file(file_path, apply_changes, make_backup)
            else:
                self.stdout.write(self.style.ERROR(f"Arquivo não encontrado: {file_path}"))

        if apply_changes:
            self.stdout.write(self.style.SUCCESS("\nCorreções aplicadas com sucesso!"))
            self.stdout.write(self.style.WARNING(
                "Reinicie o servidor Django para que as alterações tenham efeito."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "\nNenhuma alteração foi aplicada. Use --apply para aplicar as correções."
            ))

    def find_project_root(self):
        """Localiza a raiz do projeto Django."""
        # Verifica se estamos no diretório raiz
        if os.path.exists('manage.py'):
            return os.getcwd()

        # Verifica se estamos em um subdiretório
        current_dir = os.getcwd()
        while True:
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Chegamos à raiz do sistema
                break

            if os.path.exists(os.path.join(parent_dir, 'manage.py')):
                return parent_dir

            current_dir = parent_dir

        return None

    def check_and_fix_file(self, file_path, apply_changes, make_backup):
        """Verifica e corrige problemas no arquivo."""
        self.stdout.write(self.style.HTTP_INFO(f"\nVerificando: {os.path.basename(file_path)}"))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Buscar e corrigir problemas de acesso a itens de conhecimento
            patterns_to_fix = [
                # Padrão 1: Acesso direto a ['answer'] em resultado de knowledge_results
                (r'knowledge_results\[(\d+)\]\[[\'\"]answer[\'\"]\]', self.fix_knowledge_results_access),

                # Padrão 2: Acesso direto a ['answer'] em best_match ou similar
                (r'(best_match|item|result)\[[\'\"]answer[\'\"]\]', self.fix_item_access),

                # Padrão 3: Acesso direto usando índice e depois ['answer']
                (r'knowledge_results\[(\d+)\]\.answer', lambda m: f"knowledge_results[{m.group(1)}][0].answer"),
            ]

            for pattern, fix_func in patterns_to_fix:
                content = re.sub(pattern, fix_func, content)

            # Verificar se é necessário aplicar correções
            if content != original_content:
                changes_count = sum(1 for a, b in zip(original_content.splitlines(), content.splitlines()) if a != b)
                self.stdout.write(f"  Encontradas {changes_count} linhas para corrigir.")

                # Mostrar as diferenças
                self.show_diff(original_content, content)

                if apply_changes:
                    # Fazer backup se solicitado
                    if make_backup:
                        backup_path = f"{file_path}.bak"
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        self.stdout.write(f"  Backup criado: {backup_path}")

                    # Aplicar correções
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.stdout.write(self.style.SUCCESS(f"  Correções aplicadas ao arquivo."))
                else:
                    self.stdout.write(self.style.WARNING("  Correções não aplicadas (modo de simulação)."))
            else:
                self.stdout.write("  Nenhum problema encontrado neste arquivo.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar arquivo: {str(e)}"))
            self.stdout.write(traceback.format_exc())

    def fix_knowledge_results_access(self, match):
        """Corrige o acesso a knowledge_results[n]['answer']."""
        index = match.group(1)
        return f"knowledge_results[{index}][0].answer"

    def fix_item_access(self, match):
        """Corrige o acesso a item['answer']."""
        item_name = match.group(1)
        return f"{item_name}[0].answer" if item_name != 'item' else "item.answer"

    def show_diff(self, original, modified):
        """Mostra as diferenças entre duas strings."""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()

        # Encontrar linhas que mudaram
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
            if orig != mod:
                self.stdout.write(f"  Linha {i + 1}:")
                self.stdout.write(f"    - {orig}")
                self.stdout.write(f"    + {mod}")
                self.stdout.write("")

        # Mostrar linhas adicionadas/removidas, se houver diferença de tamanho
        if len(original_lines) != len(modified_lines):
            self.stdout.write(f"  Diferença no número de linhas: {len(original_lines)} -> {len(modified_lines)}")