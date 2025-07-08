#!/usr/bin/env python
# check_cache_usage.py
"""
Verifica se os principais serviços estão usando corretamente os caches específicos do Redis.
"""
import os
import sys
import importlib
import inspect
import django
import re

# Configura o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


def check_file(file_path, expected_cache=None):
    """Verifica o uso de cache em um arquivo específico"""
    print(f"\n==== Verificando arquivo: {file_path} ====")

    try:
        # Lê o arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verifica as importações de cache
        if "from django.core.cache import cache" in content:
            print("✅ Importação de cache padrão encontrada")
        else:
            print("❓ Importação de cache padrão não encontrada")

        if "from django.core.cache import caches" in content:
            print("✅ Importação de caches (múltiplos) encontrada")
        else:
            print("❓ Importação de caches (múltiplos) não encontrada")

        # Verifica o uso de caches específicos
        cache_uses = re.findall(r"caches\['([^']+)'\]", content)
        if cache_uses:
            print(f"✅ Uso de caches específicos encontrado: {', '.join(set(cache_uses))}")

            if expected_cache and expected_cache in cache_uses:
                print(f"✅ Cache específico esperado '{expected_cache}' está sendo usado")
            elif expected_cache:
                print(f"❌ Cache específico esperado '{expected_cache}' NÃO está sendo usado")
        else:
            print("❓ Nenhum uso de caches específicos encontrado")

        # Verifica o uso do cache padrão
        default_cache_uses = len(re.findall(r"cache\.", content)) - len(re.findall(r"caches\.", content))
        if default_cache_uses > 0:
            print(f"ℹ️ Uso do cache padrão encontrado ({default_cache_uses} ocorrências)")
            if expected_cache:
                print(f"⚠️ Recomendação: Considere usar o cache específico '{expected_cache}' em vez do cache padrão")

        # Verifica chamadas específicas
        if "cache.set" in content:
            print("ℹ️ Operação cache.set encontrada")
        if "cache.get" in content:
            print("ℹ️ Operação cache.get encontrada")
        if "cache.delete" in content:
            print("ℹ️ Operação cache.delete encontrada")

        # Imprime as linhas mais relevantes
        print("\nLinhas relevantes:")
        for i, line in enumerate(content.split('\n')):
            if 'cache' in line and ('import' in line or '=' in line or 'cache.' in line or 'caches[' in line):
                print(f"  Linha {i + 1}: {line.strip()}")

    except Exception as e:
        print(f"❌ Erro ao verificar arquivo {file_path}: {str(e)}")


def main():
    # Arquivos principais para verificar (caminho, cache esperado)
    files_to_check = [
        ('cgbookstore/apps/core/services/google_books_service.py', 'google_books'),
        ('cgbookstore/apps/core/recommendations/engine.py', 'recommendations'),
        ('cgbookstore/apps/core/recommendations/utils/cache_manager.py', None),
        ('cgbookstore/apps/core/views/image_proxy.py', 'image_proxy'),
        ('cgbookstore/apps/core/views/weather.py', None)
    ]

    print("==== VERIFICAÇÃO DE USO DE CACHE NOS SERVIÇOS ====")

    for file_path, expected_cache in files_to_check:
        check_file(file_path, expected_cache)

    print("\n==== RECOMENDAÇÕES PARA OTIMIZAÇÃO ====")
    print("1. Todos os serviços devem importar tanto 'cache' quanto 'caches'")
    print("2. Para serviços Google Books, use cache específico: caches['google_books']")
    print("3. Para serviços de recomendação, use cache específico: caches['recommendations']")
    print("4. Para o proxy de imagens, use cache específico: caches['image_proxy']")
    print("5. Para meteorologia, considere usar um cache específico: caches['weather'] (ainda não configurado)")

    print("\n==== COMO ATUALIZAR UM SERVIÇO PARA USAR CACHE ESPECÍFICO ====")
    print("1. Adicione a importação: from django.core.cache import caches")
    print("2. Substitua 'cache.get(...)' por \"caches['nome_do_cache'].get(...)\"")
    print("3. Substitua 'cache.set(...)' por \"caches['nome_do_cache'].set(...)\"")
    print("4. Substitua 'cache.delete(...)' por \"caches['nome_do_cache'].delete(...)\"")


if __name__ == "__main__":
    main()