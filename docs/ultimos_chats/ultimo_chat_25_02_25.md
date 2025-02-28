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

4. **Isolamento entre Módulos**
   - Criação de serviço centralizado para Google Books API
   - Cache isolado para diferentes contextos (busca e recomendações)
   - Compatibilidade com código existente

### Estrutura de Arquivos Principais

```
└── bookstore
   └── cgbookstore
       ├── apps
       │   └── core
       │       ├── management
       │       ├── migrations
       │       ├── models
       │       ├── services
       │       │   ├── __init__.py
       │       │   ├── google_books_client.py
       │       │   └── google_books_service.py
       │       └── recommendations
       │           ├── analytics
       │           │   ├── admin_dashboard
       │           │   ├── management
       │           │   │   └── commands
       │           │   │       ├── __init__.py
       │           │   │       ├── clean_test_data.py
       │           │   │       └── generate_test_data.py
       │           │   ├── migrations
       │           │   ├── tests
       │           │   ├── utils
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
       │           ├── tests
       │           ├── utils
       │           ├── __init__.py
       │           ├── engine.py
       │           └── urls.py
       └── __init__.py
```

### Implementação de Serviço Centralizado

#### 1. Criação de Google Books Service
- Implementação de serviço central unificado para ambos os módulos
- Suporte para contextos isolados (busca/recomendações)
- Sistema de cache aprimorado com namespaces

#### 2. Correção de Problemas de Conflito
- Resolução de conflitos entre módulo de busca e recomendações
- Isolamento de caches para evitar interferência
- Arquivos de compatibilidade para transição suave

#### 3. Aprimoramento da Filtragem de Livros Externos
- Correção no processamento de resultados da API
- Adaptação para diferentes formatos de resposta
- Verificação robusta das propriedades necessárias

### Próximos Passos
1. Aprimorar tratamento de erros
2. Expandir sistema de recomendações
3. Implementar machine learning para refinamento
4. Melhorar performance de caching
5. Remover arquivos de compatibilidade após período de teste

## Configuração e Instalação

### Dependências
- Django 5.1.4
- Biblioteca de requisições
- Cliente Google Books
- Papaparse
- Lodash

### Configurações de Cache
- `books_search`: Cache para módulo de busca (2 horas)
- `books_recommendations`: Cache para recomendações (24 horas)
- `google_books`: Cache compartilhado (24 horas)

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
- Conflitos entre módulo de busca e recomendações
- Falhas na integração do Google Books API
- Livros externos não sendo exibidos corretamente

#### Soluções Implementadas
1. **Centralização da API Google Books**
   - Novo serviço em `google_books_service.py`
   - Implementação de cache com contextos isolados
   - Compatibilidade com código existente

2. **Correção do Processamento de Livros Externos**
   - Aprimoramento do método `_search_with_pattern()`
   - Tratamento flexível para diferentes formatos de dados
   - Adaptação para o novo formato centralizado

3. **Configuração de Cache Isolado**
   - Configuração específica para cada módulo
   - Tempos de expiração otimizados
   - Prefixos de chave para evitar colisões

### Desafios de Implementação
- Integração com API do Google Books
- Isolamento entre módulos interdependentes
- Manutenção da compatibilidade durante a refatoração

## Notas Técnicas

### Estratégias de Recomendação
- Priorização de recomendações esternas
- Complementação com livros internos
- Análise contextual do histórico de leitura

### Otimizações
- Cache isolado por contexto
- Filtro adaptativo para formatos de resposta da API
- Sistema de compatibilidade para transição gradual

---

**Última Atualização**: 25 de Fevereiro de 2025
**Versão do Sistema**: 2.2
**Desenvolvido por**: Equipe CG.BookStore.Online