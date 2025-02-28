# CG.BookStore.Online - Sistema de Recomendações: Base de Conhecimento (Atualizado 20/02/2025)

## 1. Visão Geral do Projeto
- Livraria online com foco em personalização e descoberta
- Sistema de recomendações modular e personalizável
- Cache otimizado para performance
- Integração com Google Books API implementada e funcional

## 2. Estrutura do Sistema de Recomendações
```plaintext
recommendations/
├── providers/
│   ├── history.py (recomendações baseadas em histórico)
│   ├── category.py (recomendações por categoria)
│   ├── similarity.py (recomendações por similaridade)
│   ├── temporal.py (recomendações por padrões temporais)
│   ├── exclusion.py (filtros de exclusão aprimorados)
│   └── external_api.py (integração com Google Books)
├── engine.py (motor principal de recomendações)
├── urls.py (rotas para as views de recomendações)
├── views/
│   └── recommendation_views.py (views para recomendações mistas)
└── utils/
    ├── cache_manager.py (gerenciamento de cache)
    └── google_books_cache.py (cache para API externa)
└── services/
    └── google_books_client.py (cliente API do Google Books)
```

## 3. Estado Atual do Sistema
### 3.1 Melhorias Implementadas
- Correção do problema de cache e invalidação
- Otimização do sistema de recomendações
- Aprimoramento da separação entre perfis de usuários
- Implementação de sistema de fallback
- Ajuste na exclusão de livros já na estante
- Implementação de análise de tendências temporais
- Correção de problemas com exibição redundante de livros
- Implementação de verificação multi-nível para garantir exclusão de livros já adquiridos
- Método para retornar prateleira personalizada organizada por categorias
- Correção do cálculo de scores de similaridade
- **[NOVO] Integração completa com API do Google Books**
- **[NOVO] Modal interativo para visualização de livros externos**
- **[NOVO] Implementação de endpoints para importação de livros externos**
- **[NOVO] Sistema para adicionar livros externos à prateleira**

### 3.2 Características Atuais
- Limite padrão de 20 recomendações por usuário
- Sistema de pesos usando slots de proporção (35/25/30/10)
- Exclusão rigorosa de livros já possuídos ou favoritados
- Uso de livros favoritos para melhorar recomendações
- Cache com invalidação na atualização das prateleiras
- Aleatoriedade controlada para variar recomendações
- Análise de padrões temporais (sazonais e períodos móveis)
- Verificação final de segurança após combinação de recomendações
- Recomendações organizadas por gênero e autor
- **[NOVO] Complemento de recomendações com API externa**
- **[NOVO] Distinção visual entre fontes locais e externas**
- **[NOVO] Interface para interação com livros externos**

### 3.3 Problemas Resolvidos
- [RESOLVIDO] Providers individuais ocasionalmente incluíam livros que deveriam ser excluídos
- [RESOLVIDO] Recomendações podiam mostrar redundância entre diferentes providers
- [RESOLVIDO] Alguns livros de outros perfis de usuário podiam aparecer nas recomendações
- **[RESOLVIDO] Erro na invalidação de cache ao adicionar livro à prateleira**
- **[RESOLVIDO] Recomendações limitadas quando o catálogo local é pequeno**
- **[RESOLVIDO] Visualização de detalhes de livros externos**

### 3.4 Problemas Conhecidos
- O `CategoryProvider` frequentemente retorna lista vazia
- `TemporalProvider` pode retornar lista vazia quando não há histórico suficiente
- **[NOVO] Possíveis timeouts em requisições à API externa**
- **[NOVO] Necessidade de ajustes no modelo Book para campos externos**

## 4. Componentes Críticos

### 4.1 Engine.py
- Gerencia recomendações personalizadas
- Combina diferentes providers usando sistema de slots
- Filtro de segurança multi-nível para exclusões
- Tratamento de erros por provider
- Sistema de fallback para garantir recomendações
- Método get_personalized_shelf para recomendações organizadas
- **[NOVO] Método get_mixed_recommendations para combinar fontes locais e externas**
- **[NOVO] Método _get_external_recommendations para obter recomendações da API**

### 4.2 Providers
- History: Baseado no histórico do usuário (peso: 35%)
- Category: Baseado em categorias (peso: 25%)
- Similarity: Baseado em similaridade entre livros (peso: 30%)
- Temporal: Baseado em padrões temporais (peso: 10%)
- Exclusion: Verificação rigorosa de exclusões em múltiplos níveis
- **[NOVO] ExternalApiProvider: Integração com Google Books API**

### 4.3 Views
- **[NOVO] get_recommendations_view**: Exibe recomendações mistas
- **[NOVO] get_personalized_shelf_view**: Exibe prateleira personalizada 
- **[NOVO] get_recommendations_json**: API JSON para recomendações
- **[NOVO] get_external_book_details**: API para detalhes de livros externos
- **[NOVO] import_external_book**: Importa livro externo para catálogo
- **[NOVO] add_external_book_to_shelf**: Adiciona livro externo à prateleira

### 4.4 Cache
- Implementação usando Django cache framework
- Cache key baseada em user_id, shelf_hash e timestamp
- Sistema de invalidação otimizado
- Rotação automática para garantir variedade
- **[NOVO] Cache especializado para chamadas à API externa**

## 5. Configurações do Sistema
### 5.1 Proporção de Recomendações
- History: 7 slots (35%)
- Category: 5 slots (25%)
- Similarity: 6 slots (30%)
- Temporal: 2 slots (10%)

### 5.2 Exclusões
- Livros em 'lido'
- Livros em 'lendo'
- Livros em 'vou_ler'
- Livros em 'abandonei'
- Livros em 'favorito' (mas usados para influência)

## 6. Modelo de Dados Relevantes
```python
class Book:
    titulo: str
    autor: str
    genero: str
    categoria: str
    temas: str
    # Campos adicionados
    external_id: str  # ID do livro na API externa
    capa_url: str  # URL da imagem da capa externa
    is_temporary: bool  # Indica se é um livro temporário/externo
    external_data: str  # JSON com dados originais da API externa
    # outros campos...

class UserBookShelf:
    user: User
    book: Book
    shelf_type: str  # ['lido', 'lendo', 'vou_ler', 'favorito', 'abandonei']
    added_at: datetime
```

## 7. Futuras Melhorias Potenciais
1. ✓ Implementação de análise de tendências temporais
2. ✓ Implementação de sistema de filtragem multi-nível para exclusões  
3. ✓ Integração com API externa (Google Books)
4. ✓ Interface para visualização de livros externos
5. Ajuste dinâmico de pesos baseado em feedback
6. Integração com sistema de avaliações
7. Otimização do uso de memória do cache
8. Implementação de testes de performance
9. Melhorar CategoryProvider para evitar retornos vazios
10. Aprimorar TemporalProvider para análise em históricos limitados
11. Implementar sistema de monitoramento de qualidade das recomendações
12. **[NOVO] Suporte para múltiplas APIs externas (Open Library, Amazon)**
13. **[NOVO] Sistema de importação direta de livros externos**

## 8. Considerações Técnicas
- DJANGO_ENV: 'development'
- Banco de dados: SQLite
- Cache: LocMemCache
- Testes via PowerShell no Windows
- **[NOVO] Controle de requisições à API externa para evitar rate limiting**
- **[NOVO] Tratamento de timeouts e erros de API**

## 9. Arquivos Principais
1. `engine.py`
2. `test_exclusions.py`
3. `providers/history.py`
4. `providers/similarity.py` 
5. `providers/temporal.py`
6. `providers/exclusion.py`
7. **[NOVO] providers/external_api.py**
8. **[NOVO] services/google_books_client.py**
9. **[NOVO] views/recommendation_views.py**
10. **[NOVO] templates/core/recommendations/mixed_recommendations.html**
11. **[NOVO] templates/core/recommendations/personalized_shelf.html**

## 10. Padrões a Seguir
- Seguir PEP 8
- Manter modularização atual
- Documentar alterações
- Evitar redundância de código
- Manter compatibilidade com sistema de cache existente
- Garantir exclusão completa de livros em todas as prateleiras
- Implementar verificações de segurança em múltiplos níveis
- Tratar exceções individualmente por provider
- **[NOVO] Validar dados externos antes de armazenamento**
- **[NOVO] Implementar timeouts em chamadas externas**
- **[NOVO] Garantir tratamento adequado de imagens externas**

Este documento reflete o estado atual do sistema após a implementação da integração com a API do Google Books e serve como base para futuras melhorias.