#!/usr/bin/env python
# test_weather_cache.py
"""
Testa o cache específico para o serviço de meteorologia.
"""
import os
import sys
import django
import time

# Configura o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

from django.core.cache import caches


def test_weather_cache():
    """Testa o cache específico para meteorologia"""
    print("==== TESTE DO CACHE DE METEOROLOGIA ====")

    # Obtém o cache específico
    try:
        weather_cache = caches['weather']
        print("✅ Cache 'weather' encontrado")
    except Exception as e:
        print(f"❌ Erro ao obter o cache 'weather': {str(e)}")
        return

    # Testa operações básicas
    test_key = 'test_weather_cache_key'
    test_value = {
        'city': 'São Paulo',
        'temperature': 25.5,
        'humidity': 80,
        'last_updated': '2025-04-16 14:30'
    }

    # Set
    try:
        weather_cache.set(test_key, test_value, 60)
        print("✅ Operação SET bem-sucedida")
    except Exception as e:
        print(f"❌ Erro na operação SET: {str(e)}")

    # Get
    try:
        retrieved = weather_cache.get(test_key)
        if retrieved == test_value:
            print("✅ Operação GET bem-sucedida")
            print(f"   Valor armazenado: {retrieved}")
        else:
            print("❌ Erro na operação GET: valor diferente do esperado")
            print(f"   Valor esperado: {test_value}")
            print(f"   Valor obtido: {retrieved}")
    except Exception as e:
        print(f"❌ Erro na operação GET: {str(e)}")

    # Delete
    try:
        weather_cache.delete(test_key)
        print("✅ Operação DELETE bem-sucedida")

        # Verifica se foi realmente excluído
        if weather_cache.get(test_key) is None:
            print("✅ Valor foi excluído corretamente")
        else:
            print("❌ Valor ainda existe após DELETE")
    except Exception as e:
        print(f"❌ Erro na operação DELETE: {str(e)}")

    print("\n==== TESTE COMPLETO ====")


if __name__ == "__main__":
    test_weather_cache()