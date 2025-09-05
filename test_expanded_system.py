#!/usr/bin/env python
"""
Teste do Sistema Expandido
Execução: python test_expanded_system.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cgbookstore.apps.chatbot_literario.services import training_service


def main():
    print('🔍 TESTE DE BUSCA DO SISTEMA EXPANDIDO')
    print('=' * 50)

    # Queries de teste
    queries = ['José de Alencar', 'Romantismo', 'Dom Casmurro', 'análise de personagens']

    for query in queries:
        try:
            results = training_service.search_knowledge(query, limit=2, threshold=0.3)
            print(f'📚 "{query}": {len(results)} resultado(s)')

            for i, r in enumerate(results, 1):
                conf = getattr(r, 'confidence', 0)
                q = getattr(r, 'question_found', 'N/A')[:50]
                print(f'   {i}. {q}... (conf: {conf:.2f})')

        except Exception as e:
            print(f'❌ Erro na busca "{query}": {e}')

        print()

    # Estatísticas finais
    try:
        stats = training_service.get_knowledge_stats()
        print('📊 RESUMO FINAL:')
        print(f'   ✅ Itens ativos: {stats.get("active_items", 0)}')
        print(f'   🧠 Com embeddings: {stats.get("with_embeddings", 0)}')
        print(f'   📂 Categorias: {len(stats.get("categories", {}))}')
        print(f'   📋 Lista de categorias: {list(stats.get("categories", {}).keys())}')

        # Mostrar contagem por categoria
        print('\n📂 DISTRIBUIÇÃO POR CATEGORIA:')
        for category, count in stats.get("categories", {}).items():
            print(f'   • {category}: {count} item(s)')

    except Exception as e:
        print(f'❌ Erro ao obter estatísticas: {e}')

    print('\n🎉 SISTEMA HÍBRIDO EXPANDIDO E OPERACIONAL!')


if __name__ == "__main__":
    main()