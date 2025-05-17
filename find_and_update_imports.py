# find_and_update_imports.py
import os
import re
from pathlib import Path


def find_google_books_client_imports(base_directory):
    """Localiza todos os arquivos que importam o cliente antigo do Google Books"""
    found_files = []

    # Padrão para buscar importações do cliente antigo
    import_pattern = re.compile(r'from\s+.*\.google_books_client\s+import')

    # Percorrer diretórios e arquivos
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if import_pattern.search(content):
                        found_files.append(file_path)
                        print(f"Encontrado em: {file_path}")
                except Exception as e:
                    print(f"Erro ao ler {file_path}: {str(e)}")

    return found_files


def update_import_in_file(file_path):
    """Atualiza a importação no arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Atualizar importação
        updated_content = re.sub(
            r'from\s+(.*?)\.google_books_client\s+import\s+(.*)',
            r'from \1.services.google_books_service import \2',
            content
        )

        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Atualizado: {file_path}")
            return True
        else:
            print(f"Nenhuma atualização necessária: {file_path}")
            return False

    except Exception as e:
        print(f"Erro ao atualizar {file_path}: {str(e)}")
        return False


if __name__ == "__main__":
    # Caminho do diretório do projeto
    base_dir = "cgbookstore"

    # Encontrar arquivos com importações
    print("Procurando arquivos com importações do cliente antigo...")
    files_with_imports = find_google_books_client_imports(base_dir)

    print(f"\nEncontrados {len(files_with_imports)} arquivos com importações do cliente antigo.")

    # Atualizar importações
    if files_with_imports:
        print("\nAtualizando importações...")
        for file_path in files_with_imports:
            update_import_in_file(file_path)

    print("\nProcesso concluído.")