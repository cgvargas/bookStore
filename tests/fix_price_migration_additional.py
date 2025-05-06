import os
import re
from pathlib import Path

# Localizar arquivo de migração
project_dir = Path(__file__).resolve().parent
migration_file = project_dir / 'cgbookstore' / 'apps' / 'core' / 'migrations' / '0020_clean_price_data.py'

print(f"Verificando arquivo: {migration_file}")

if not migration_file.exists():
    print(f"Arquivo de migração não encontrado: {migration_file}")
    # Buscar recursivamente
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file == '0020_clean_price_data.py':
                migration_file = Path(root) / file
                print(f"Migração encontrada em: {migration_file}")
                break

if migration_file.exists():
    # Fazer backup do arquivo original
    backup_file = str(migration_file) + '.bak2'
    with open(migration_file, 'r', encoding='utf-8') as original, open(backup_file, 'w', encoding='utf-8') as backup:
        content = original.read()
        backup.write(content)

    print(f"Backup criado em: {backup_file}")

    # Modificar as consultas SQL:
    # 1. Primeiro, substituir todas as instâncias de "preco = '{}'" por "CAST(preco AS TEXT) = '{}'"
    modified_content = re.sub(
        r'(OR\s+)preco(\s*=\s*[\'"]\{\}[\'"]\s*)',
        r'\1CAST(preco AS TEXT)\2',
        content
    )

    # 2. Procurar por outras comparações potencialmente problemáticas
    modified_content = re.sub(
        r'(\s)preco(\s*=\s*[\'"].*?[\'"]\s*)',
        r'\1CAST(preco AS TEXT)\2',
        modified_content
    )

    # Salvando modificações
    if modified_content != content:
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print("✓ Arquivo de migração atualizado com as seguintes modificações:")
        print("  - 'OR preco = '\{\}'' -> 'OR CAST(preco AS TEXT) = '\{\}''")
        print("  - outras comparações de texto com 'preco'")
    else:
        print("⚠ Nenhuma modificação realizada. O padrão não foi encontrado exatamente como esperado.")

        # Abordagem mais direta - ler o arquivo e procurar a linha específica
        with open(migration_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        for i, line in enumerate(lines):
            if "OR preco = '{}'" in line:
                lines[i] = line.replace("OR preco = '{}'", "OR CAST(preco AS TEXT) = '{}'")
                modified = True
                print(f"Linha modificada: {i + 1}")
            elif "preco = '{}'" in line:
                lines[i] = line.replace("preco = '{}'", "CAST(preco AS TEXT) = '{}'")
                modified = True
                print(f"Linha modificada: {i + 1}")

        if modified:
            with open(migration_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("✓ Arquivo atualizado através da abordagem direta.")
        else:
            print("⚠ Não foi possível encontrar o padrão exato a ser substituído.")
            print("Conteúdo do arquivo para inspeção manual:")
            with open(migration_file, 'r', encoding='utf-8') as f:
                problematic_lines = [
                    (i + 1, line.strip()) for i, line in enumerate(f.readlines())
                    if "preco" in line and ("=" in line or "LIKE" in line)
                ]

            if problematic_lines:
                print("\nLinhas potencialmente problemáticas:")
                for line_num, line in problematic_lines:
                    print(f"Linha {line_num}: {line}")
                print("\nVocê precisará editar manualmente estas linhas.")
            else:
                print("Nenhuma linha problemática encontrada.")
else:
    print("⚠ Não foi possível encontrar o arquivo de migração.")