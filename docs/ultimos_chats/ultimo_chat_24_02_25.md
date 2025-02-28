# CG.BookStore.Online - Sistema de Recomendações

## Histórico de Desenvolvimento

### Contexto Inicial
O projeto CG.BookStore.Online é uma plataforma de gerenciamento de livros com um sistema de recomendações avançado, que integra o catálogo local com a API do Google Books.

### Desafios do Sistema de Recomendações
- Integração de recomendações locais e externas
- Personalização baseada no histórico de leitura do usuário
- Tratamento de livros de diferentes fontes
- Flexibilidade na descoberta de novos títulos

### Componentes Principais
1. **RecommendationEngine**: Motor principal de recomendações
2. **ExternalApiProvider**: Integração com Google Books
3. **CategoryMapping**: Normalização de categorias
4. **Providers de Recomendação**: 
   - HistoryBasedProvider
   - CategoryBasedProvider
   - SimilarityBasedProvider
   - TemporalProvider

### Problemas Resolvidos

#### 1. Geração de Recomendações Mistas
- Implementação de método `get_mixed_recommendations()`
- Priorização de recomendações locais
- Complementação com livros externos

#### 2. Tratamento de Livros Externos
- Criação de modelo temporário para livros do Google Books
- Conversão e normalização de dados externos
- Gerenciamento de metadados de livros

#### 3. Mapeamento e Normalização de Categorias
- Criação de sistema de mapeamento de categorias
- Normalização de termos de gênero e categoria
- Identificação de categorias relacionadas

### Melhorias Implementadas

#### Na Engine de Recomendações
- Tratamento de erros robusto
- Fallback para recomendações genéricas
- Distribuição de pesos entre diferentes providers

#### No Provider Externo
- Extração inteligente de padrões de interesse do usuário
- Filtro de livros já existentes
- Cache de recomendações

### Desafios Técnicos Resolvidos

1. **Integração de Fontes Múltiplas**
   - Combinação de recomendações locais e externas
   - Tratamento de metadados diferentes

2. **Performance e Caching**
   - Implementação de estratégias de cache
   - Otimização de consultas à API externa

3. **Personalização**
   - Análise do histórico de leitura
   - Ponderação de preferências do usuário

### Estrutura de Arquivos Principais

```
└── bookstore
   └── cgbookstore
       ├── apps
       │   └── core
       │       ├── management
       │       ├── migrations
       │       ├── models
       │       └── recommendations
       │           ├── analytics
       │           │   ├── admin_dashboard
       │           │   ├── management
       │           │   │   └── commands
       │           │   │       ├── __init__.py
       │           │   │       ├── clean_test_data.py
       │           │   │       └── generate_test_data.py
       │           │   ├── migrations
       │           │   │   ├── 0001_create_recommendation_interaction.py
       │           │   │   ├── 0002_rename_analytics_r_user_id_99fba4_idx_core_analyt_user_id_df7e22_idx_and_more.py
       │           │   │   └── __init__.py
       │           │   ├── tests
       │           │   │   ├── __init__.py
       │           │   │   └── generate_test_data.py
       │           │   ├── utils
       │           │   │   ├── __init__.py
       │           │   │   └── processors.py
       │           │   ├── __init__.py
       │           │   ├── apps.py
       │           │   ├── endpoints.py
       │           │   ├── models.py
       │           │   ├── serializers.py
       │           │   ├── tracker.py
       │           │   └── urls.py
       │           ├── api
       │           │   ├── __init__.py
       │           │   ├── endpoints.py
       │           │   ├── performance.py
       │           │   ├── README.md
       │           │   ├── serializers.py
       │           │   └── urls.py
       │           ├── management
       │           │   ├── commands
       │           │   │   ├── __init__.py
       │           │   │   └── benchmark_recommendations.py
       │           │   └── __init__.py
       │           ├── providers
       │           │   ├── __init__.py
       │           │   ├── category.py
       │           │   ├── exclusion.py
       │           │   ├── external_api.py
       │           │   ├── history.py
       │           │   ├── mapping.py
       │           │   ├── similarity.py
       │           │   └── temporal.py
       │           ├── services
       │           │   ├── __init__.py
       │           │   └── calculator.py
       │           ├── tests
       │           │   ├── __init__.py
       │           │   ├── conftest.py
       │           │   ├── test_api.py
       │           │   ├── test_cache.py
       │           │   ├── test_category.py
       │           │   ├── test_engine.py
       │           │   ├── test_exclusions.py
       │           │   ├── test_history_temporal.py
       │           │   ├── test_load.py
       │           │   ├── test_logging.py
       │           │   ├── test_processors.py
       │           │   ├── test_providers.py
       │           │   ├── test_recommendation_cache.py
       │           │   ├── test_recommendation_system.py
       │           │   ├── test_search_tracking.py
       │           │   └── test_similarity_provider.py
       │           ├── utils
       │           │   ├── __init__.py
       │           │   ├── cache_manager.py
       │           │   ├── google_books_cache.py
       │           │   ├── processors.py
       │           │   └── search_tracker.py
       │           ├── __init__.py
       │           ├── engine.py
       │           └── urls.py
       └── __init__.py
```

### Próximos Passos
1. Aprimorar tratamento de erros
2. Expandir sistema de recomendações
3. Implementar machine learning para refinamento
4. Melhorar performance de caching

## Configuração e Instalação

### Dependências
- Django 5.1.4
- Biblioteca de requisições
- Cliente Google Books
- Papaparse
- Lodash

### Variáveis de Ambiente
- `GOOGLE_BOOKS_API_KEY`: Chave de API do Google Books
- Configurações de cache
- Credenciais de banco de dados

## Contribuição
- Siga as diretrizes de código
- Mantenha a modularidade
- Adicione testes para novas funcionalidades

## Histórico Recente de Desenvolvimento

### Últimos Ajustes no Sistema de Recomendações

#### Problemas Identificados
- Inconsistências na geração de recomendações
- Erros no tratamento de livros externos
- Limitações no mapeamento de categorias

#### Soluções Implementadas
1. **Atualização do ExternalApiProvider**
   - Método `_get_user_patterns()` aprimorado
   - Melhoria na extração de padrões de interesse
   - Inclusão explícita de categorias de espiritualidade/canções

2. **Modificações no Motor de Recomendações**
   - Tratamento robusto de `_get_local_recommendations()`
   - Distribuição de pesos entre providers
   - Fallback para recomendações genéricas

3. **Tratamento de Livros Temporários**
   - Criação de função `get_external_book_details()` 
   - Suporte a livros com IDs negativos
   - Armazenamento de recomendações externas

### Desafios de Implementação
- Integração com API do Google Books
- Manutenção da performance
- Personalização precisa de recomendações

## Notas Técnicas

### Estratégias de Recomendação
- Priorização de recomendações esternas
- Complementação com livros externos
- Análise contextual do histórico de leitura

### Otimizações
- Cache de recomendações
- Filtro de livros duplicados
- Normalização de metadados

---

**Última Atualização**: 24 de Fevereiro de 2025
**Versão do Sistema**: 2.1
**Desenvolvido por**: Equipe CG.BookStore.Online