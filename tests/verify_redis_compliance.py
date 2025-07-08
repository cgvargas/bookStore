#!/usr/bin/env python
# verify_redis_compliance.py
"""
Verifica se a configuração atual do Redis está em conformidade com as recomendações
do documento de otimização do sistema de cache.
"""
import os
import sys
import django
from pprint import pprint

# Configura o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.conf import settings
from django.core.cache import caches


def get_recommended_config():
    """Retorna a configuração recomendada baseada na documentação"""
    return {
        'default': {
            'db': 0,
            'timeout': 600,  # 10 minutos
        },
        'books_search': {
            'db': 1,
            'timeout': 60 * 60 * 2,  # 2 horas
        },
        'recommendations': {
            'db': 2,
            'timeout': 60 * 60 * 6,  # 6 horas
        },
        'books_recommendations': {
            'db': 2,  # Mesmo DB do recommendations
            'timeout': 60 * 60 * 6,  # 6 horas
        },
        'google_books': {
            'db': 3,
            'timeout': 60 * 60 * 24 * 7,  # 7 dias
        },
        'image_proxy': {
            'db': 4,
            'timeout': 60 * 60 * 24 * 14,  # 14 dias
        }
    }


def check_redis_config():
    """Verifica se a configuração atual está em conformidade com as recomendações"""
    print("==== VERIFICAÇÃO DE CONFORMIDADE DA CONFIGURAÇÃO REDIS ====\n")

    # Verificar se CACHES existe em settings
    if not hasattr(settings, 'CACHES'):
        print("❌ Erro: Configuração CACHES não encontrada em settings.py")
        return

    # Verificar o ENGINE de sessão
    if hasattr(settings, 'SESSION_ENGINE'):
        if settings.SESSION_ENGINE == "django.contrib.sessions.backends.cache":
            print("✅ SESSION_ENGINE está configurado corretamente para usar cache")
        else:
            print(f"❌ SESSION_ENGINE não está usando cache: {settings.SESSION_ENGINE}")
    else:
        print("❌ SESSION_ENGINE não está definido")

    # Verificar SESSION_CACHE_ALIAS
    if hasattr(settings, 'SESSION_CACHE_ALIAS'):
        if settings.SESSION_CACHE_ALIAS == "default":
            print("✅ SESSION_CACHE_ALIAS está configurado corretamente para 'default'")
        else:
            print(f"❌ SESSION_CACHE_ALIAS não está usando 'default': {settings.SESSION_CACHE_ALIAS}")
    else:
        print("❌ SESSION_CACHE_ALIAS não está definido")

    recommended = get_recommended_config()

    # Verificar se todos os caches recomendados estão configurados
    print("\n-- Verificação de caches configurados --")
    for cache_name in recommended:
        if cache_name in settings.CACHES:
            print(f"✅ Cache '{cache_name}' está configurado")
        else:
            print(f"❌ Cache '{cache_name}' não está configurado")

    # Verificar se todos os caches estão usando Redis
    print("\n-- Verificação de backend Redis --")
    for cache_name, config in settings.CACHES.items():
        if 'BACKEND' in config and 'redis' in config['BACKEND'].lower():
            print(f"✅ Cache '{cache_name}' está usando Redis: {config['BACKEND']}")
        else:
            print(f"❌ Cache '{cache_name}' não está usando Redis: {config.get('BACKEND', 'Não definido')}")

    # Verificar os bancos de dados Redis (números DB)
    print("\n-- Verificação de bancos de dados Redis --")
    for cache_name, config in settings.CACHES.items():
        if cache_name in recommended:
            location = config.get('LOCATION', '')
            db_num = None

            # Extrair o número do banco
            if 'redis://' in location:
                try:
                    db_num = int(location.split('/')[-1])
                except (ValueError, IndexError):
                    db_num = None

            if db_num == recommended[cache_name]['db']:
                print(f"✅ Cache '{cache_name}' está usando o banco Redis correto: {db_num}")
            else:
                print(f"❌ Cache '{cache_name}' não está usando o banco Redis recomendado: "
                      f"Atual={db_num}, Recomendado={recommended[cache_name]['db']}")

    # Verificar os timeouts
    print("\n-- Verificação de timeouts --")
    for cache_name, config in settings.CACHES.items():
        if cache_name in recommended:
            timeout = config.get('TIMEOUT')
            if timeout == recommended[cache_name]['timeout']:
                print(f"✅ Cache '{cache_name}' está usando o timeout correto: {timeout} segundos")
            else:
                print(f"❌ Cache '{cache_name}' não está usando o timeout recomendado: "
                      f"Atual={timeout}, Recomendado={recommended[cache_name]['timeout']}")

    # Verificar opções específicas
    print("\n-- Verificação de opções especiais --")

    # Verificar compressão para image_proxy
    if 'image_proxy' in settings.CACHES and 'OPTIONS' in settings.CACHES['image_proxy']:
        options = settings.CACHES['image_proxy']['OPTIONS']
        if 'COMPRESSOR' in options and 'zlib' in options['COMPRESSOR']:
            print("✅ Cache 'image_proxy' está configurado com compressão zlib")
        else:
            print("❌ Cache 'image_proxy' não está configurado com compressão zlib")

    print("\n==== VERIFICAÇÃO CONCLUÍDA ====")


def test_redis_functionality():
    """Testa a funcionalidade básica do Redis para cada cache configurado"""
    print("\n==== TESTE DE FUNCIONALIDADE REDIS ====\n")

    for cache_name in settings.CACHES:
        try:
            cache = caches[cache_name]
            test_key = f"test_key_{cache_name}"
            test_value = f"Test value for {cache_name}"

            # Tentar definir um valor
            cache.set(test_key, test_value, 60)

            # Tentar recuperar o valor
            retrieved = cache.get(test_key)

            if retrieved == test_value:
                print(f"✅ Cache '{cache_name}' está funcionando corretamente")
            else:
                print(f"❌ Cache '{cache_name}' não está funcionando corretamente. "
                      f"Valor esperado: '{test_value}', Valor obtido: '{retrieved}'")

        except Exception as e:
            print(f"❌ Erro ao testar cache '{cache_name}': {str(e)}")

    print("\n==== TESTE DE FUNCIONALIDADE CONCLUÍDO ====")


if __name__ == "__main__":
    check_redis_config()
    test_redis_functionality()