# CG.BookStore.Online - Sistema de Recomendações: Base de Conhecimento

## 1. Visão Geral do Projeto
- Livraria online com foco em personalização e descoberta
- Sistema de recomendações modular e personalizável
- Cache otimizado para performance
- Integração com Google Books API

## 2. Estrutura do Sistema de Recomendações
```plaintext
recommendations/
├── providers/
│   ├── history.py (recomendações baseadas em histórico)
│   ├── category.py (recomendações por categoria)
│   ├── similarity.py (recomendações por similaridade)
│   └── exclusion.py (filtros de exclusão)
├── engine.py (motor principal de recomendações)
└── utils/
    └── cache_manager.py (gerenciamento de cache)
```

## 3. Estado Atual do Sistema
### 3.1 Melhorias Implementadas
- Correção do problema de cache e invalidação
- Otimização do sistema de recomendações
- Aprimoramento da separação entre perfis de usuários
- Implementação de sistema de fallback
- Ajuste na exclusão de livros já na estante

### 3.2 Características Atuais
- Limite padrão de 20 recomendações por usuário
- Cache com invalidação apropriada
- Exclusão correta de livros já possuídos
- Uso de livros favoritos para melhorar recomendações
- Sistema de pesos ajustado para diferentes fontes

## 4. Componentes Críticos

### 4.1 Engine.py
- Gerencia recomendações personalizadas
- Combina diferentes providers
- Sistema de cache otimizado
- Tratamento melhorado de exclusões
- Pesos ajustados para diferentes fontes

### 4.2 Providers
- History: Baseado no histórico do usuário
- Category: Baseado em categorias
- Similarity: Baseado em similaridade entre livros
- Exclusion: Gerencia exclusões eficientemente

### 4.3 Cache
- Implementação usando Django cache framework
- Cache key baseada em user_id, shelf_hash e timestamp
- Sistema de invalidação otimizado

## 5. Configurações do Sistema
### 5.1 Pesos de Recomendação
- History Weight: 0.4
- Category Weight: 0.3
- Similarity Weight: 0.3
- Random Factor: 0.0-0.2
- Favorite Boost: 0.2

### 5.2 Exclusões
- Livros em 'lido'
- Livros em 'lendo'
- Livros em 'vou_ler'
- Livros em 'abandonei'
- Favoritos mantidos para influência positiva

## 6. Modelo de Dados Relevantes
```python
class Book:
    titulo: str
    autor: str
    genero: str
    categoria: str
    temas: str
    # outros campos...

class UserBookShelf:
    user: User
    book: Book
    shelf_type: str  # ['lido', 'lendo', 'vou_ler', 'favorito', 'abandonei']
    added_at: datetime
```

## 7. Futuras Melhorias Potenciais
1. Implementação de análise de tendências temporais
2. Ajuste dinâmico de pesos baseado em feedback
3. Integração com sistema de avaliações
4. Otimização do uso de memória do cache
5. Implementação de testes de performance

## 8. Considerações Técnicas
- DJANGO_ENV: 'development'
- Banco de dados: SQLite
- Cache: LocMemCache
- Testes via PowerShell no Windows

## 9. Arquivos Principais
1. `engine.py`
2. `test_recommendation_system.py`
3. `providers/history.py`
4. `providers/similarity.py`

## 10. Padrões a Seguir
- Seguir PEP 8
- Manter modularização atual
- Documentar alterações
- Evitar redundância de código
- Manter compatibilidade com sistema de cache existente

Este documento reflete o estado atual do sistema após as últimas atualizações e serve como base para futuras melhorias.