import os
import django
from django.db import connection
from tabulate import tabulate  # Biblioteca para exibir as tabelas no terminal
import csv
import json

# Configurar o ambiente Django manualmente
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgbookstore.config.settings")
django.setup()

IGNORAR_TABELAS = ['core_book']  # Tabelas a serem ignoradas na listagem geral


def listar_tabelas_e_conteudo(linhas_por_pagina=10):
    """
    Lista todas as tabelas no banco de dados, com suporte à paginação
    e ignorando tabelas configuradas.
    """
    with connection.cursor() as cursor:
        # Detectar o backend do banco de dados
        vendor = connection.vendor

        if vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        elif vendor == 'postgresql':
            cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        elif vendor == 'mysql':
            cursor.execute("SHOW TABLES;")
        else:
            print(f"Banco de dados {vendor} não é suportado.")
            return

        tabelas = cursor.fetchall()  # Buscar tabelas

    # Iterar pelas tabelas disponíveis
    for tabela in tabelas:
        nome_tabela = tabela[0]

        if nome_tabela in IGNORAR_TABELAS:
            print(f"\nTabela '{nome_tabela}' ignorada. Use outra opção para visualizá-la.")
            continue

        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {nome_tabela} LIMIT {linhas_por_pagina};")
                colunas = [col[0] for col in cursor.description]
                dados = cursor.fetchall()

            print(f"\nConteúdo da tabela: {nome_tabela} (mostrando os primeiros {linhas_por_pagina} registros)")
            print(tabulate(dados, headers=colunas, tablefmt="grid"))

        except Exception as e:
            print(f"(Erro ao acessar a tabela '{nome_tabela}'): {e}")


def visualizar_tabela_core_book(exportar_para=None):
    """
    Exibe ou exporta os dados da tabela `core_book`.
    """
    print("\nVisualizando conteúdo da tabela: core_book")
    print("-" * 40)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM core_book;")  # Consulta todos os dados
            colunas = [col[0] for col in cursor.description]  # Nome das colunas
            dados = cursor.fetchall()  # Dados da tabela

        if not dados:
            print("(Tabela core_book vazia)\n")
            return

        # Exibe os primeiros 10 registros no terminal
        print("Primeiros 10 registros da tabela core_book:")
        print(tabulate(dados[:10], headers=colunas, tablefmt="grid"))

        # Opções de exportação
        if exportar_para == 'csv':
            salvar_em_csv(colunas, dados, 'core_book.csv')
        elif exportar_para == 'json':
            salvar_em_json(colunas, dados, 'core_book.json')
    except Exception as e:
        print(f"(Erro ao acessar a tabela 'core_book'): {e}")

def exportar_tabela_generica(nome_tabela, exportar_para, limite=None):
    """
    Exporta qualquer tabela informada (em formato CSV ou JSON).
    """
    try:
        with connection.cursor() as cursor:
            query = f"SELECT * FROM {nome_tabela}"
            if limite:
                query += f" LIMIT {limite}"

            cursor.execute(query)
            colunas = [col[0] for col in cursor.description]
            dados = cursor.fetchall()

        if not dados:
            print(f"(Tabela {nome_tabela} vazia)\n")
            return

        if exportar_para == 'csv':
            salvar_em_csv(colunas, dados, f"{nome_tabela}.csv")
        elif exportar_para == 'json':
            salvar_em_json(colunas, dados, f"{nome_tabela}.json")
        else:
            print(f"(Formato {exportar_para} não suportado)")
    except Exception as e:
        print(f"(Erro ao acessar a tabela '{nome_tabela}'): {e}")

def salvar_em_csv(colunas, dados, nome_arquivo):
    """
    Salva os dados em um arquivo CSV.
    """
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as arquivo_csv:
        escritor = csv.writer(arquivo_csv)
        escritor.writerow(colunas)  # Escreve os nomes das colunas
        escritor.writerows(dados)  # Escreve os dados das linhas
    print(f"Dados da tabela core_book foram exportados para o arquivo: {nome_arquivo}")


def salvar_em_json(colunas, dados, nome_arquivo):
    """
    Salva os dados em um arquivo JSON.
    """
    registros = [dict(zip(colunas, linha)) for linha in dados]  # Cria uma lista de dicionários
    with open(nome_arquivo, mode='w', encoding='utf-8') as arquivo_json:
        json.dump(registros, arquivo_json, indent=4, ensure_ascii=False)
    print(f"Dados da tabela core_book foram exportados para o arquivo: {nome_arquivo}")


if __name__ == "__main__":
    print("\nEscolha uma das opções disponíveis:")
    print("1 - Listar todas as tabelas e conteúdos (exceto ignoradas)")
    print("2 - Exibir conteúdo completo da tabela core_book")
    print("3 - Exportar core_book em CSV")
    print("4 - Exportar core_book em JSON")
    print("5 - Exportar uma tabela específica (em CSV/JSON)")

    opcao = input("\nDigite o número da opção desejada: ").strip()

    if opcao == '1':
        linhas = input("\nDigite o limite de linhas por tabela (padrão = 10): ").strip()
        linhas = int(linhas) if linhas.isdigit() else 10
        listar_tabelas_e_conteudo(linhas_por_pagina=linhas)
    elif opcao == '2':
        visualizar_tabela_core_book()
    elif opcao == '3':
        visualizar_tabela_core_book(exportar_para='csv')
    elif opcao == '4':
        visualizar_tabela_core_book(exportar_para='json')
    elif opcao == '5':
        tabela = input("\nDigite o nome da tabela que deseja exportar: ").strip()
        formato = input("Escolha o formato de exportação (csv/json): ").strip().lower()
        limite = input("Digite o limite de linhas (ou pressione Enter para todos): ").strip()
        limite = int(limite) if limite.isdigit() else None
        exportar_tabela_generica(tabela, exportar_para=formato, limite=limite)
    else:
        print("\nOpção inválida.")