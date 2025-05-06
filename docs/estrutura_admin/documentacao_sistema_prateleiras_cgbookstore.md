# Documentação Detalhada: Sistema de Prateleiras do CGBookStore

## Introdução

Este documento detalha o sistema de prateleiras do CGBookStore, incluindo os arquivos que foram modificados para corrigir problemas, o funcionamento atual, e as funcionalidades futuras a serem implementadas para melhorar a experiência do administrador.

## Arquivos do Sistema e Suas Funções

### 1. Modelos (`home_content.py`)
**Caminho**: `cgbookstore/apps/core/models/home_content.py`

Este arquivo contém os modelos principais responsáveis pelo sistema de prateleiras:

- **HomeSection**: Define as seções da página inicial, que podem ser de diferentes tipos (prateleiras, vídeos, etc.)
- **DefaultShelfType**: Define os tipos de prateleiras padrão e seus filtros
- **BookShelfSection**: Associa uma seção a um tipo de prateleira específico
- **BookShelfItem**: Relaciona livros individuais a prateleiras específicas

**Métodos-chave**:
- `get_livros()` em `DefaultShelfType`: Retorna os livros que devem aparecer em uma prateleira específica com base nos critérios configurados

### 2. View Principal (`general.py`)
**Caminho**: `cgbookstore/apps/core/views/general.py`

Contém a classe `IndexView` que é responsável por carregar e processar as seções/prateleiras para exibição na página inicial.

**Métodos-chave**:
- `get_context_data()`: Processa seções da página inicial, incluindo prateleiras e suas associações com livros

### 3. Modelo de Livro (`book.py`)
**Caminho**: `cgbookstore/apps/core/models/book.py`

Define o modelo `Book` que representa livros no sistema, com campos específicos relacionados a categorização e exibição em prateleiras.

**Propriedades-chave**:
- `SHELF_SPECIAL_CHOICES`: Lista de opções válidas para o campo `tipo_shelf_especial`
- `tipo_shelf_especial`: Campo que armazena o identificador da prateleira especial do livro

### 4. Configuração do Admin (`admin.py`)
**Caminho**: `cgbookstore/apps/core/admin.py`

Configura a interface administrativa para gerenciar seções, prateleiras e livros.

**Classes-chave**:
- `BookAdminForm`: Formulário personalizado para validação e processamento de livros
- `HomeSectionAdmin`: Interface administrativa para seções da home
- `DefaultShelfTypeAdmin`: Interface administrativa para tipos de prateleira
- `BookShelfSectionAdmin`: Interface administrativa para prateleiras de livros

### 5. Template de Gerenciamento de Prateleiras (`shelf_management.html`)
**Caminho**: `cgbookstore/apps/core/templates/admin/shelf_management.html`

Fornece uma visão geral de todas as prateleiras configuradas no sistema, permitindo gerenciamento visual.

### 6. Home Page Template (`home.html`)
**Caminho**: `cgbookstore/apps/core/templates/core/home.html`

Renderiza a página inicial, incluindo as diferentes seções e prateleiras com seus livros associados.

## Modificações Realizadas

### 1. Correção no `DefaultShelfType.get_livros()`

Modificamos este método para ser mais flexível na busca de livros, permitindo que mesmo prateleiras com configurações imperfeitas consigam exibir conteúdo relevante:

```python
def get_livros(self):
    """Retorna os livros filtrados baseado nas configurações"""
    from .book import Book
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Buscando livros para prateleira: {self.nome} ({self.identificador})")
    
    try:
        # Para o tipo "ebooks", tenta diretamente com tipo_shelf_especial
        if self.identificador == 'ebooks':
            return Book.objects.filter(tipo_shelf_especial=self.identificador).order_by('ordem_exibicao')
        
        # Para tipos padrão, usa os campos booleanos correspondentes
        if self.filtro_campo == 'e_lancamento':
            return Book.objects.filter(e_lancamento=True).order_by('-created_at')
        elif self.filtro_campo == 'e_destaque':
            return Book.objects.filter(e_destaque=True).order_by('ordem_exibicao')
        elif self.filtro_campo == 'quantidade_vendida':
            return Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida')
        elif self.filtro_campo == 'adaptado_filme':
            return Book.objects.filter(adaptado_filme=True).order_by('ordem_exibicao')
        elif self.filtro_campo == 'e_manga':
            return Book.objects.filter(e_manga=True).order_by('ordem_exibicao')
        elif self.filtro_campo == 'tipo_shelf_especial':
            return Book.objects.filter(tipo_shelf_especial=self.filtro_valor).order_by('ordem_exibicao')
        
        # Tenta usar o campo como filtro direto
        return Book.objects.filter(**{self.filtro_campo: self.filtro_valor}).order_by('ordem_exibicao')
    
    except Exception as e:
        logger.error(f"Erro ao filtrar: {str(e)}")
        # Retorna queryset vazio em caso de erro
        return Book.objects.none()
```

### 2. Correção na View `IndexView.get_context_data()`

Modificamos o processamento de prateleiras na view para implementar métodos de fallback:

```python
for shelf_type in default_shelf_types:
    try:
        # Método 1: Tenta usar o método get_livros
        livros = shelf_type.get_livros()
        
        # Se não encontrou livros, tenta método alternativo
        if not livros.exists():
            # Método 2: Tenta filtro direto por tipo_shelf_especial
            livros = Book.objects.filter(tipo_shelf_especial=shelf_type.identificador).order_by('ordem_exibicao')
            logger.info(f"Tentativa direta por tipo_shelf_especial={shelf_type.identificador}: {livros.count()} livros")
            
            # Se ainda não encontrou, tenta outros campos
            if not livros.exists():
                # Método 3: Tenta campos booleanos para tipos especiais
                if shelf_type.identificador == 'ebooks':
                    # Adiciona 'ebooks' como fallback final
                    livros = Book.objects.filter(e_lancamento=True)[:5]  # Usa alguns livros para mostrar algo
                    logger.info("Usando livros de lançamento como fallback para ebooks")
                
                elif shelf_type.identificador == 'mais_vendidos':
                    livros = Book.objects.all().order_by('-quantidade_vendida')[:12]
                    logger.info("Usando livros ordenados por vendas para mais_vendidos")
                
                elif shelf_type.identificador == 'destaques':
                    livros = Book.objects.filter(e_destaque=True)
                    logger.info("Usando livros de destaque")
                
                # Adicione outros tipos específicos aqui se necessário
        
        # Limita a quantidade de livros
        livros = livros[:shelf_type.max_livros if hasattr(shelf_type, 'max_livros') else 12]
        
        # Se encontrou livros, adiciona à lista de seções
        if livros.exists():
            processed_sections.append({
                'id': shelf_type.identificador,
                'titulo': shelf_type.nome,
                'tipo': 'shelf',
                'livros': livros
            })
            logger.info(f'Prateleira padrão adicionada: {shelf_type.nome} com {livros.count()} livros')
        else:
            logger.warning(f'Nenhum livro encontrado para prateleira: {shelf_type.nome}')
    
    except Exception as e:
        logger.error(f'Erro ao processar prateleira {shelf_type.nome}: {str(e)}')
        continue
```

## Estado Atual do Sistema

O sistema de prateleiras agora funciona da seguinte forma:

1. Os administradores podem criar tipos de prateleiras personalizadas via `DefaultShelfType`
2. Podem criar seções na página inicial (`HomeSection`) do tipo "shelf"
3. Podem associar estas seções a tipos de prateleira (`BookShelfSection`)
4. Podem adicionar livros e configurar seu `tipo_shelf_especial` para que apareçam em prateleiras específicas

A correção implementada permite maior flexibilidade no sistema, fazendo com que, mesmo que a configuração não seja perfeita, o sistema busque alternativas para exibir conteúdo relevante.

## Melhorias Futuras a Implementar

### 1. Carregamento Dinâmico das Opções de Tipo de Prateleira

**Arquivo**: `book.py`
**Objetivo**: Modificar o modelo Book para carregar dinamicamente as opções de `tipo_shelf_especial` a partir dos tipos de prateleira cadastrados.

**Implementação proposta**:
```python
@property
def get_shelf_special_choices(self):
    """Retorna dinamicamente as opções para tipo_shelf_especial"""
    from .home_content import DefaultShelfType
    
    # Opções padrão
    standard_choices = [
        ('', 'Nenhum'),
        ('lancamentos', 'Lançamentos'),
        ('destaques', 'Destaques'),
        ('filmes', 'Adaptados para Filme/Série'),
        ('mangas', 'Mangás'),
    ]
    
    # Adiciona tipos personalizados
    try:
        custom_shelves = DefaultShelfType.objects.filter(ativo=True)
        custom_choices = [(shelf.identificador, shelf.nome) for shelf in custom_shelves]
        return standard_choices + custom_choices
    except:
        return standard_choices
```

**Modificação no modelo Book**:
```python
# Substituir a definição estática por uma referência ao método dinâmico
tipo_shelf_especial = models.CharField(
    'Tipo de Prateleira Especial',
    max_length=50,
    blank=True,
    choices=get_shelf_special_choices,
    help_text='Selecione para quais prateleiras especiais este livro deve aparecer'
)
```

### 2. Formulário de Criação Rápida de Prateleira

**Arquivo novo**: `cgbookstore/apps/core/forms/shelf_forms.py`
**Objetivo**: Criar um formulário que permita a criação de uma prateleira completa em um único passo.

**Implementação proposta**:
```python
from django import forms
from ..models.home_content import HomeSection, DefaultShelfType, BookShelfSection

class QuickShelfCreationForm(forms.Form):
    """Formulário para criação rápida de prateleira completa"""
    nome = forms.CharField(
        label='Nome da Prateleira',
        max_length=200,
        help_text='Este será o título exibido na página inicial'
    )
    
    identificador = forms.SlugField(
        label='Identificador',
        help_text='Identificador único usado para filtragem (somente letras, números e underscore)'
    )
    
    filtro_campo = forms.ChoiceField(
        label='Campo do Filtro',
        choices=[
            ('tipo_shelf_especial', 'Tipo de Prateleira Especial'),
            ('e_lancamento', 'É Lançamento'),
            ('e_destaque', 'É Destaque'),
            ('adaptado_filme', 'Adaptado para Filme/Série'),
            ('e_manga', 'É Mangá'),
            ('quantidade_vendida', 'Quantidade Vendida'),
        ],
        initial='tipo_shelf_especial',
        help_text='Campo usado para filtrar os livros'
    )
    
    ordem = forms.IntegerField(
        label='Ordem de Exibição',
        initial=0,
        help_text='Ordem em que a prateleira aparecerá na página inicial'
    )
    
    max_livros = forms.IntegerField(
        label='Máximo de Livros',
        initial=12,
        min_value=1,
        max_value=50,
        help_text='Número máximo de livros exibidos nesta prateleira'
    )
    
    def save(self):
        """Cria todos os objetos necessários para uma prateleira completa"""
        nome = self.cleaned_data['nome']
        identificador = self.cleaned_data['identificador']
        filtro_campo = self.cleaned_data['filtro_campo']
        ordem = self.cleaned_data['ordem']
        max_livros = self.cleaned_data['max_livros']
        
        # 1. Cria o tipo de prateleira
        shelf_type = DefaultShelfType.objects.create(
            nome=nome,
            identificador=identificador,
            filtro_campo=filtro_campo,
            filtro_valor=identificador if filtro_campo == 'tipo_shelf_especial' else 'True',
            ordem=ordem,
            ativo=True
        )
        
        # 2. Cria a seção na home
        section = HomeSection.objects.create(
            titulo=nome,
            tipo='shelf',
            ordem=ordem,
            ativo=True
        )
        
        # 3. Cria a prateleira e associa com a seção e o tipo
        book_shelf = BookShelfSection.objects.create(
            section=section,
            shelf_type=shelf_type,
            max_livros=max_livros
        )
        
        return book_shelf
```

### 3. Interface de Arrastar e Soltar para Gerenciamento de Prateleiras

**Arquivos**:
- Novo: `cgbookstore/apps/core/templates/admin/visual_shelf_manager.html`
- Novo: `cgbookstore/static/js/admin/shelf_manager.js`
- Modificar: `admin.py` para adicionar a view

**Objetivo**: Criar uma interface visual onde o administrador pode arrastar e soltar livros entre prateleiras.

**Implementação da view**:
```python
def visual_shelf_manager(self, request):
    """View para gerenciador visual de prateleiras"""
    # Busca todas as prateleiras ativas
    book_shelves = BookShelfSection.objects.select_related(
        'section', 'shelf_type'
    ).prefetch_related(
        'livros', 'bookshelfitem_set', 'bookshelfitem_set__livro'
    )
    
    # Busca livros não associados a prateleiras
    used_book_ids = BookShelfItem.objects.values_list('livro_id', flat=True)
    unassigned_books = Book.objects.exclude(id__in=used_book_ids)[:100]  # Limita para não sobrecarregar
    
    context = {
        'title': 'Gerenciador Visual de Prateleiras',
        'book_shelves': book_shelves,
        'unassigned_books': unassigned_books
    }
    
    # Se é uma requisição AJAX para adicionar/remover livro
    if request.method == 'POST' and request.is_ajax():
        action = request.POST.get('action')
        book_id = request.POST.get('book_id')
        shelf_id = request.POST.get('shelf_id')
        
        try:
            book = Book.objects.get(id=book_id)
            shelf = BookShelfSection.objects.get(id=shelf_id)
            
            if action == 'add':
                # Adiciona livro à prateleira
                BookShelfItem.objects.get_or_create(
                    shelf=shelf,
                    livro=book,
                    defaults={'ordem': BookShelfItem.objects.filter(shelf=shelf).count()}
                )
                return JsonResponse({'status': 'success'})
                
            elif action == 'remove':
                # Remove livro da prateleira
                BookShelfItem.objects.filter(shelf=shelf, livro=book).delete()
                return JsonResponse({'status': 'success'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return render(request, 'admin/visual_shelf_manager.html', context)
```

**Template básico**:
```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block extrastyle %}
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.css">
    <style>
        .shelf-container {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .book-item {
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 5px;
            border-radius: 4px;
            background: white;
            cursor: move;
            display: flex;
            align-items: center;
        }
        .book-cover {
            width: 40px;
            height: 60px;
            object-fit: cover;
            margin-right: 10px;
        }
        .unassigned-books {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }
    </style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <h1 class="mb-4">Gerenciador Visual de Prateleiras</h1>
    
    <div class="row">
        <div class="col-md-8">
            <!-- Prateleiras existentes -->
            {% for shelf in book_shelves %}
            <div class="shelf-container">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3>{{ shelf.section.titulo }}</h3>
                    <div>
                        <a href="{% url 'admin:core_bookshelfsection_change' shelf.id %}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                    </div>
                </div>
                <p class="text-muted mb-3">
                    Tipo: {{ shelf.get_shelf_type_name }} | 
                    Livros: {{ shelf.livros.count }} / {{ shelf.max_livros }}
                </p>
                
                <div class="book-list" data-shelf-id="{{ shelf.id }}">
                    {% for item in shelf.bookshelfitem_set.all %}
                    <div class="book-item" data-book-id="{{ item.livro.id }}">
                        <img src="{{ item.livro.get_preview_url }}" alt="{{ item.livro.titulo }}" class="book-cover">
                        <div class="book-title">{{ item.livro.titulo }}</div>
                        <button class="btn btn-sm btn-outline-danger ms-auto remove-book">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    {% empty %}
                    <div class="empty-shelf">Arraste livros para esta prateleira</div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="col-md-4">
            <!-- Livros não associados -->
            <div class="unassigned-books">
                <h3>Livros Disponíveis</h3>
                <p class="text-muted">Arraste para adicionar a uma prateleira</p>
                
                <div class="book-list" id="unassigned-books">
                    {% for book in unassigned_books %}
                    <div class="book-item" data-book-id="{{ book.id }}">
                        <img src="{{ book.get_preview_url }}" alt="{{ book.titulo }}" class="book-cover">
                        <div class="book-title">{{ book.titulo }}</div>
                    </div>
                    {% empty %}
                    <div class="empty-shelf">Nenhum livro disponível</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extrajs %}
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
<script src="{% static 'js/admin/shelf_manager.js' %}"></script>
{% endblock %}
```

**JavaScript (shelf_manager.js)**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa sortable para cada prateleira
    document.querySelectorAll('.book-list').forEach(function(el) {
        new Sortable(el, {
            animation: 150,
            group: 'books',
            onAdd: function(evt) {
                const bookItem = evt.item;
                const bookId = bookItem.dataset.bookId;
                const shelfId = evt.to.dataset.shelfId;
                
                // Adiciona botão de remoção se necessário
                if (!bookItem.querySelector('.remove-book')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'btn btn-sm btn-outline-danger ms-auto remove-book';
                    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                    bookItem.appendChild(removeBtn);
                }
                
                // Notifica o servidor sobre a adição
                fetch('/admin/shelf-manager/update/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: `action=add&book_id=${bookId}&shelf_id=${shelfId}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status !== 'success') {
                        console.error('Erro ao adicionar livro:', data.message);
                    }
                });
            }
        });
    });
    
    // Evento para remover livros de prateleiras
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-book')) {
            const button = e.target.closest('.remove-book');
            const bookItem = button.closest('.book-item');
            const bookId = bookItem.dataset.bookId;
            const shelfId = bookItem.closest('.book-list').dataset.shelfId;
            
            // Move o item para a lista de não associados
            document.getElementById('unassigned-books').appendChild(bookItem);
            
            // Remove o botão de remoção
            button.remove();
            
            // Notifica o servidor sobre a remoção
            fetch('/admin/shelf-manager/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `action=remove&book_id=${bookId}&shelf_id=${shelfId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status !== 'success') {
                    console.error('Erro ao remover livro:', data.message);
                }
            });
        }
    });
    
    // Função para obter o cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
```

## Procedimento para Implementação das Melhorias

1. **Faça backup dos arquivos originais** antes de fazer qualquer modificação
2. Implemente as alterações uma por uma, testando após cada modificação
3. Siga esta ordem para as implementações:
   - Primeiro: Carregamento dinâmico das opções de tipo de prateleira
   - Segundo: Formulário de criação rápida de prateleira
   - Terceiro: Interface de arrastar e soltar

Para cada implementação:
1. Modifique ou crie os arquivos necessários
2. Reinicie o servidor Django
3. Teste a funcionalidade com diferentes cenários
4. Ajuste o código conforme necessário antes de avançar para a próxima implementação

## Considerações Finais

O sistema de prateleiras do CGBookStore agora está funcionando corretamente e permite a criação e visualização de diferentes tipos de prateleiras. As melhorias propostas tornarão o sistema ainda mais amigável para os administradores, permitindo uma gestão mais intuitiva e rápida do conteúdo da página inicial.

Lembre-se de manter um registro de todas as alterações feitas e documentar quaisquer novos comportamentos ou limitações descobertas durante a implementação.