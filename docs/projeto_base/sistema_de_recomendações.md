# Sistema de Recomendações com Integração de API Externa
**CG.BookStore.Online**
**Versão 2.1 - Fevereiro/2025**

## 1. Visão Geral

O sistema de recomendações da CG.BookStore.Online foi aprimorado para integrar dados externos da API do Google Books, permitindo recomendações mais abrangentes mesmo quando o banco de dados local possui um catálogo limitado. Esta documentação descreve a implementação, arquitetura e funcionamento do sistema integrado.

## 2. Arquitetura do Sistema

### 2.1 Componentes Principais

```
recommendations/
├── providers/
│   ├── history.py (recomendações baseadas em histórico)
│   ├── category.py (recomendações por categoria)
│   ├── similarity.py (recomendações por similaridade)
│   ├── temporal.py (recomendações por padrões temporais)
│   ├── exclusion.py (filtros de exclusão)
│   └── external_api.py (IMPLEMENTADO: integração com Google Books)
├── engine.py (motor principal de recomendações - atualizado)
├── urls.py (IMPLEMENTADO: URLs para views de recomendações)

└── utils/
    ├── cache_manager.py (gerenciamento de cache)
    └── google_books_cache.py (IMPLEMENTADO: cache para API externa)
└── services/
    └── google_books_client.py (IMPLEMENTADO: cliente API do Google Books)
views/
└── recommendation_views.py (IMPLEMENTADO: views para recomendações mistas)
```

### 2.2 Fluxo de Dados

1. O usuário acessa a plataforma e solicita recomendações
2. O sistema verifica recomendações locais disponíveis através dos providers tradicionais
3. Se as recomendações locais forem insuficientes, o sistema complementa com dados da API externa
4. As recomendações são exibidas de forma integrada, com distinção visual entre fontes
5. O usuário pode interagir com as recomendações externas através de modais
6. Os livros externos podem ser adicionados às prateleiras do usuário

## 3. Implementações Realizadas

### 3.1 Correções de Bugs Anteriores

- Corrigido problema de livros favoritos sendo recomendados novamente
- Implementada verificação rigorosa de livros já na estante em todos os providers
- Corrigido bug de acesso ao atributo "serie" que não existia no modelo Book
- Aprimorado sistema de exclusão para garantir que todos os livros de qualquer prateleira sejam excluídos das recomendações
- Corrigido bug na invalidação de cache de recomendações após adicionar livro à prateleira

### 3.2 Novas Funcionalidades

#### 3.2.1 ExternalApiProvider
- Integração com API do Google Books para recomendações externas
- Extração de padrões do usuário para consultas relevantes
- Sistema de correspondência entre livros externos e locais
- Tratamento de dados externos para compatibilidade com o sistema
- Cache de chamadas à API para otimização de performance

#### 3.2.2 RecommendationEngine Aprimorado
- Adicionado suporte para recomendações mistas (locais + externas)
- Implementado limiar mínimo para acionar busca externa
- Armazenamento contextual de recomendações externas
- Método `get_mixed_recommendations` para acesso unificado
- Método `get_personalized_shelf` para prateleira personalizada

#### 3.2.3 Views para Recomendações Mistas (IMPLEMENTADAS)
- View renderizada para exibição de recomendações mistas
- Endpoint JSON para integração com frontend dinâmico
- View para prateleira personalizada completa
- Views para interação com livros externos:
  - Detalhes de livro externo
  - Importação de livro externo
  - Adição direta à prateleira

#### 3.2.4 Template Responsivo (IMPLEMENTADO)
- Design adaptativo para dispositivos móveis e desktop
- Distinção visual clara entre livros locais e externos
- Tratamento de erros para imagens externas
- Informações claras sobre origem dos dados
- Modal interativo para visualização de detalhes
- Modal para seleção de prateleira ao adicionar livro

#### 3.2.5 Serviços de API Externa (IMPLEMENTADOS)
- Cliente Google Books com métodos especializados
- Sistema de cache para requisições à API
- Tratamento de erros e timeout
- Conversão de formatos de dados

## 4. Modelo de Dados

### 4.1 Estruturas Principais

```python
class Book:
    # Campos existentes
    titulo: str
    autor: str
    genero: str
    categoria: str
    # ... outros campos

    # Campos adicionados para suporte a livros externos
    external_id: str  # ID do livro na API externa
    capa_url: str  # URL da imagem da capa externa
    is_temporary: bool  # Indica se é um livro temporário/externo
    external_data: str  # JSON com dados originais da API externa

class UserBookShelf:
    user: User
    book: Book
    shelf_type: str  # ['favorito', 'lendo', 'vou_ler', 'lido']
    added_at: datetime
```

### 4.2 Mudanças no Modelo
- Adicionados campos para suporte a livros externos
- Implementado suporte para armazenar metadados externos
- Manutenção de compatibilidade com estruturas existentes

## 5. Funcionamento do Sistema

### 5.1 Processo de Recomendação

1. **Recomendações Locais**:
   - History (35%): baseado no histórico de leitura
   - Category (25%): baseado em categorias preferidas
   - Similarity (30%): baseado em similaridade entre livros
   - Temporal (10%): baseado em padrões temporais

2. **Verificação de Suficiência**:
   - O sistema verifica se há pelo menos 5 recomendações locais
   - Se insuficiente, aciona o ExternalApiProvider

3. **Recomendações Externas**:
   - ExternalApiProvider analisa preferências do usuário
   - Consulta a API do Google Books com termos relevantes
   - Filtra resultados para evitar duplicidade com banco local
   - Converte dados para formato compatível

4. **Combinação de Resultados**:
   - Recomendações locais têm prioridade
   - Recomendações externas são claramente marcadas
   - Interface exibe ambas as fontes com distinção visual
   - Modal interativo permite visualizar detalhes e adicionar livros

### 5.2 Cache e Performance

- Cache baseado em chave única por usuário
- Invalidação automática quando usuário atualiza prateleiras
- Rotação de cache baseada em timestamp para variedade
- Chamadas à API externa são cacheadas separadamente
- Timeout configurável por tipo de operação

## 6. Interface do Usuário

### 6.1 Elementos Visuais

- **Livros Locais**: Exibidos normalmente
- **Livros Externos**: 
  - Exibidos com borda diferenciada
  - Badge indicando origem "Google Books"
  - Tratamento especial para imagens externas
  - Modal interativo para detalhes
  - Opções de adicionar à prateleira

### 6.2 Experiência do Usuário

- Transição suave entre fontes de dados
- Feedback claro sobre origem dos livros
- Recomendações sempre disponíveis, mesmo com catálogo limitado
- Descoberta de novos títulos além do catálogo existente
- Interação simplificada com livros externos

## 7. Objetivos e Benefícios

### 7.1 Problemas Resolvidos

- **Recomendações Limitadas**: Superado o problema de poucas recomendações quando o catálogo é pequeno
- **Experiência Incompleta**: Eliminada a experiência de "prateleira vazia" para novos usuários
- **Descoberta Limitada**: Ampliadas as possibilidades de descoberta de novos títulos
- **Interatividade**: Implementada interação com livros externos via modais

### 7.2 Benefícios para o Negócio

- **Retenção de Usuários**: Maior engajamento com recomendações sempre disponíveis
- **Experiência Enriquecida**: Descoberta de títulos além do catálogo atual
- **Dados para Aquisição**: Insights sobre interesses dos usuários para expandir catálogo
- **Redução de Custos**: Expansão virtual do catálogo sem custos de aquisição imediata

## 8. Implementações Realizadas

### 8.1 Rotas Adicionadas
```python
# Adicionado em urls.py
urlpatterns = [
    path('mixed/', get_recommendations_view, name='mixed_recommendations'),
    path('shelf/', get_personalized_shelf_view, name='personalized_shelf'),
    path('json/', get_recommendations_json, name='recommendations_api'),
    path('book/<str:external_id>/', get_external_book_details, name='external_book_details'),
    path('import-book/', import_external_book, name='import_external_book'),
    path('add-external-book/', add_external_book_to_shelf, name='add_external_book'),
]
```

### 8.2 Templates Implementados
- `mixed_recommendations.html` - Exibição de recomendações mistas
- `personalized_shelf.html` - Prateleira personalizada com seções

### 8.3 Melhorias no Modelo Book
- Campos para suporte a livros externos adicionados
- Tratamento para armazenamento de dados temporários

## 9. Considerações Técnicas

### 9.1 Segurança e Limitações

- Tratamento cuidadoso de URLs de imagens externas
- Caching para evitar excesso de requisições à API
- Validação de dados externos antes da exibição
- Tratamento de erros em caso de indisponibilidade da API
- Sanitização de dados externos antes de armazenamento

### 9.2 Manutenção

- Verificação periódica dos termos de serviço da API do Google Books
- Monitoramento de quotas e limites de requisição
- Atualização do cache para manter dados relevantes
- Análise de logs para identificar padrões de uso e otimizar chamadas

---

## Apêndice A: Exemplos de Código Principais

### A.1 ExternalApiProvider (Trecho Principal)

```python
def get_recommendations(self, user: User, limit: int = 8) -> QuerySet:
    """
    Obtém recomendações externas e as converte para formato compatível
    """
    # Obtém padrões do usuário para construir consultas relevantes
    user_patterns = self._get_user_patterns(user)
    
    if not user_patterns:
        return Book.objects.none()
    
    # Busca livros externos baseados nos padrões do usuário
    external_books = self._search_external_books(user_patterns)
    
    if not external_books:
        return Book.objects.none()
    
    # Verifica se já existem livros semelhantes no banco local
    existing_books = self._match_with_local_books(external_books)
    
    # Se houver correspondências suficientes, usa os livros locais
    if existing_books.count() >= limit:
        return existing_books.exclude(id__in=excluded_books)[:limit]
    
    # Caso contrário, converte recomendações externas em objetos temporários
    temp_books = self._convert_to_temp_books(external_books, limit)
    
    return temp_books
```

### A.2 RecommendationEngine (Trecho de Recomendações Mistas)

```python
def get_mixed_recommendations(self, user: User, limit: int = 20) -> Dict[str, Any]:
    """
    Obtém recomendações mistas (locais + externas)
    """
    # Obtém recomendações locais
    local_recommendations = self.get_recommendations(user, limit)
    local_count = local_recommendations.count()
    
    # Se temos poucas recomendações locais, adiciona externas
    if hasattr(self, '_external_recommendations') and local_count < limit:
        external_books = self._external_recommendations[:limit - local_count]
        return {
            'local': local_recommendations,
            'external': external_books,
            'has_external': len(external_books) > 0
        }
    
    return {
        'local': local_recommendations,
        'external': [],
        'has_external': False
    }
```

### A.3 View para Recomendações Mistas

```python
@login_required
@require_GET
def get_recommendations_view(request):
    """
    View para exibir recomendações mistas (locais + externas) em uma página renderizada
    """
    engine = RecommendationEngine()
    mixed_data = engine.get_mixed_recommendations(request.user)
    
    # Processamento dos livros externos para garantir que todos os campos necessários existam
    processed_external = []
    if mixed_data['has_external'] and mixed_data['external']:
        for book in mixed_data['external']:
            # Garantir que o livro tem a estrutura mínima necessária
            if 'volumeInfo' not in book:
                book['volumeInfo'] = {}
            
            # Garantir campos essenciais para evitar erros de template
            if 'title' not in book['volumeInfo']:
                book['volumeInfo']['title'] = 'Título desconhecido'
                
            if 'authors' not in book['volumeInfo'] or not book['volumeInfo']['authors']:
                book['volumeInfo']['authors'] = ['Autor desconhecido']
                
            if 'imageLinks' not in book['volumeInfo']:
                book['volumeInfo']['imageLinks'] = {'thumbnail': ''}
                
            processed_external.append(book)
    
    context = {
        'local_recommendations': mixed_data['local'],
        'external_recommendations': processed_external if mixed_data['has_external'] else [],
        'has_external': mixed_data['has_external'] and len(processed_external) > 0,
        'user': request.user,
    }
    
    return render(request, 'core/recommendations/mixed_recommendations.html', context)
```

## Apêndice B: Diagrama de Fluxo Atualizado

```
┌───────────────┐      ┌───────────────┐     ┌───────────────┐
│               │      │   Providers   │     │   External    │
│     User      │────▶ │ Tradicionais  │───▶│   Provider    │
│               │      │               │     │               │
└───────────────┘      └───────────────┘     └───────────────┘
        │                      │                     │
        │                      │                     │
        ▼                      ▼                     ▼
┌───────────────┐      ┌───────────────┐     ┌───────────────┐
│               │      │               │     │               │
│  Personalized │◀──── │Recommendation │◀───│  Google Books │
│     Shelf     │      │    Engine     │     │      API      │
│               │      │               │     │               │
└───────────────┘      └───────────────┘     └───────────────┘
        │                                            │
        │                                            │
        ▼                                            ▼
┌───────────────┐                           ┌───────────────┐
│               │                           │               │
│ Recomendações │                           │ Recomendações │
│    Locais     │                           │   Externas    │
│               │                           │               │
└───────────────┘                           └───────────────┘
        │                                            │
        │                                            │
        ▼                                            ▼
┌───────────────┐                           ┌───────────────┐
│               │                           │               │
│   Exibição    │                           │     Modal     │
│    Normal     │                           │  Interativo   │
│               │                           │               │
└───────────────┘                           └───────────────┘
                                                    │
                                                    │
                                                    ▼
                                           ┌───────────────┐
                                           │               │
                                           │  Adicionar à  │
                                           │  Prateleira   │
                                           │               │
                                           └───────────────┘
```

---

Documento atualizado por: Equipe de Desenvolvimento CG.BookStore.Online
Data: 20 de Fevereiro de 2025
Versão: 2.1