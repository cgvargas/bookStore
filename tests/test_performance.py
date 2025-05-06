"""
Script para testar a performance das consultas com e sem otimização.
Execute com: python test_performance.py
"""
import os
import django
import time

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()

# Importar modelos e configurações
from cgbookstore.apps.core.models import Book
from django.db import connection, reset_queries

def run_test():
    print("Executando teste de performance de consultas N+1...")
    print("-" * 50)

    # Limpar queries anteriores
    reset_queries()

    # Testar sem otimização
    print("Testando consulta NÃO otimizada...")
    start_time = time.time()
    books = Book.objects.all()[:10]
    for book in books:
        # Força carregamento de relacionamentos
        shelves = list(book.shelves.all())
    non_optimized_queries = len(connection.queries)
    non_optimized_time = time.time() - start_time
    print(f"Não otimizado: {non_optimized_queries} queries em {non_optimized_time:.4f} segundos")

    # Limpar queries
    reset_queries()

    # Testar com otimização
    print("\nTestando consulta OTIMIZADA com prefetch_related...")
    start_time = time.time()
    books = Book.objects.prefetch_related('shelves').all()[:10]
    for book in books:
        # Força carregamento
        shelves = list(book.shelves.all())
    optimized_queries = len(connection.queries)
    optimized_time = time.time() - start_time
    print(f"Otimizado: {optimized_queries} queries em {optimized_time:.4f} segundos")

    # Calcular melhoria
    if optimized_time > 0 and non_optimized_time > 0:
        speed_improvement = ((non_optimized_time/optimized_time)-1)*100
        queries_reduction = non_optimized_queries - optimized_queries

        print("\nResultados:")
        print("-" * 50)
        print(f"Melhoria de velocidade: {speed_improvement:.1f}% mais rápido")
        print(f"Redução de consultas: {queries_reduction} consultas a menos")

        if queries_reduction > 0:
            print("\n✅ A otimização está funcionando corretamente!")
        else:
            print("\n⚠️ A otimização não mostrou redução no número de consultas.")
    else:
        print("\n⚠️ Erro ao calcular melhoria. Verifique se há dados suficientes para o teste.")

if __name__ == "__main__":
    run_test()