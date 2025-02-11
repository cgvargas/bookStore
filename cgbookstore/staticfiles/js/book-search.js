// Configuração inicial quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, iniciando configuração...');

    // Elementos do DOM
    const elements = {
        searchInput: document.getElementById('search-input'),
        searchType: document.getElementById('search-type'),
        searchButton: document.getElementById('search-button'),
        searchResults: document.getElementById('search-results'),
        pagination: document.getElementById('pagination'),
        pageNumbers: document.getElementById('page-numbers'),
        prevPageBtn: document.getElementById('prev-page'),
        nextPageBtn: document.getElementById('next-page'),
        shelfModal: document.getElementById('shelfModal'),
        selectedBookId: document.getElementById('selected-book-id')
    };

    // Estado da aplicação
    const state = {
        currentPage: 1,
        currentBooks: [],
        isProcessing: false
    };

    // Função para rastrear interações
    async function trackInteraction(bookId, interactionType, source, position = null) {
        try {
            const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const response = await fetch('/api/recommendations/analytics/track/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify({
                    book_id: bookId,
                    interaction_type: interactionType,
                    source: source,
                    position: position,
                    metadata: {
                        page: window.location.pathname,
                        timestamp: new Date().toISOString()
                    }
                })
            });

            if (!response.ok) {
                console.warn('Falha ao rastrear interação:', await response.text());
            }
        } catch (error) {
            console.warn('Erro ao rastrear interação:', error);
        }
    }

    // Função para mostrar alertas
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '1050';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }

    // Função para buscar livros
    async function searchBooks(page = 1) {
        const query = elements.searchInput.value.trim();
        if (!query) return;

        try {
            const response = await fetch(`/books/search/?q=${encodeURIComponent(query)}&type=${elements.searchType.value}&page=${page}`);

            // Verifica redirecionamento para login
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }

            // Verifica o tipo de conteúdo da resposta
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Você precisa estar autenticado para realizar a busca');
            }

            const data = await response.json();

            if (response.ok) {
                state.currentBooks = data.books;
                displayBooks(data.books);
                updatePagination(data);
                state.currentPage = page;
            } else {
                throw new Error(data.error || 'Erro ao buscar livros');
            }
        } catch (error) {
            console.error('Erro:', error);
            if (error.message.includes('autenticado')) {
                window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
            } else {
                showAlert('Erro ao buscar livros: ' + error.message, 'danger');
            }
        }
    }

    // Função para exibir os livros
    function displayBooks(books) {
    elements.searchResults.innerHTML = '';
    const template = document.getElementById('book-template');

    books.forEach((book, index) => {
        const clone = template.content.cloneNode(true);

        const img = clone.querySelector('.book-cover');
        img.loading = 'lazy';
        img.decoding = 'async';
        img.src = book.thumbnail || '/static/images/no-cover.svg';
        img.alt = `Capa do livro ${book.title}`;

        // Rastrear visualização do livro
        setTimeout(() => {
            if (isElementInViewport(img)) {
                trackInteraction(book.id, 'view', 'general', index + 1);
            }
        }, 1000);

        // Adiciona observer para rastrear visualização
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    trackInteraction(book.id, 'view', 'general', index + 1);
                    observer.unobserve(entry.target);
                }
            });
        });

        img.onerror = () => {
            img.src = '/static/images/no-cover.svg';
        };

        // Elementos existentes
        const titleElement = clone.querySelector('.book-title');
        titleElement.textContent = book.title;
        titleElement.addEventListener('click', () => {
            trackInteraction(book.id, 'click', 'general', index + 1);
        });

        clone.querySelector('.book-author').textContent = book.authors.join(', ');

        const publishedYear = book.published_date.split('-')[0];
        clone.querySelector('.book-date').textContent = `Publicado em ${publishedYear}`;
        clone.querySelector('.book-description').textContent = book.description;

        const addButton = clone.querySelector('.add-to-shelf');
        addButton.setAttribute('data-book-index', index);
        addButton.setAttribute('data-book-id', book.id);

        elements.searchResults.appendChild(clone);

        // Observa a imagem para rastrear visualização
        observer.observe(img);
    });

    setupShelfButtons();
}

    // Configurar botões de adicionar à prateleira
    function setupShelfButtons() {
        const addButtons = document.querySelectorAll('.add-to-shelf');

        addButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const bookIndex = this.getAttribute('data-book-index');
                const book = state.currentBooks[bookIndex];
                elements.selectedBookId.value = bookIndex;
            });
        });
    }

    // Função para adicionar livro à prateleira
    async function addToShelf(shelf, bookIndex) {
    if (state.isProcessing) return;
    state.isProcessing = true;

    try {
        const book = state.currentBooks[bookIndex];
        const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const bookData = {
            titulo: book.title || '',
            subtitulo: book.subtitle || '',
            autores: book.authors || ['Autor desconhecido'],
            descricao: book.description || 'Descrição não disponível',
            data_publicacao: book.published_date || '',
            capa_url: book.thumbnail || '',
            isbn: book.isbn || '',
            categorias: book.categories || [],
            editora: book.publisher || '',
            valor: parseFloat(book.valor) || 0,
            valor_promocional: parseFloat(book.valor_promocional) || 0,
            moeda: 'BRL'
        };

        const payload = {
            book_data: bookData,
            shelf: shelf
        };

        const response = await fetch('/books/add-to-shelf/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Rastrear adição à prateleira
            await trackInteraction(book.id, 'add_shelf', 'general', bookIndex + 1);

            const modalInstance = bootstrap.Modal.getInstance(elements.shelfModal);
            if (modalInstance) {
                modalInstance.hide();
            }

            showAlert(data.message || `Livro adicionado à prateleira ${shelf} com sucesso!`, 'success');

            setTimeout(() => {
                window.location.href = data.redirect_url || '/profile/';
            }, 1000);
        } else {
            throw new Error(data.error || 'Erro desconhecido ao adicionar livro');
        }
    } catch (error) {
        console.error('Erro detalhado:', error);
        showAlert('Erro ao adicionar livro à prateleira: ' + error.message, 'danger');
    } finally {
        state.isProcessing = false;
    }
}

    // Função para atualizar a paginação
    function updatePagination(data) {
        const { total_pages, current_page, has_previous, has_next } = data;
        elements.prevPageBtn.disabled = !has_previous;
        elements.nextPageBtn.disabled = !has_next;

        elements.pageNumbers.innerHTML = '';
        let pages = [];

        // Primeira página sempre visível
        pages.push(1);

        let start = Math.max(2, current_page - 2);
        let end = Math.min(total_pages - 1, current_page + 2);

        if (start > 2) pages.push('...');

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        if (end < total_pages - 1) pages.push('...');

        if (total_pages > 1) pages.push(total_pages);

        pages.forEach(page => {
            if (page === '...') {
                const span = document.createElement('span');
                span.className = 'page-ellipsis mx-2';
                span.textContent = '...';
                elements.pageNumbers.appendChild(span);
            } else {
                const button = document.createElement('button');
                button.className = `page-link ${page === current_page ? 'active' : ''}`;
                button.textContent = page;
                button.onclick = () => searchBooks(page);
                const li = document.createElement('li');
                li.className = 'page-item';
                li.appendChild(button);
                elements.pageNumbers.appendChild(li);
            }
        });
    }

    // Configuração dos event listeners
    function setupEventListeners() {
        // Eventos de busca
        elements.searchButton.addEventListener('click', () => searchBooks(1));
        elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchBooks(1);
        });

        // Eventos de paginação
        elements.prevPageBtn.addEventListener('click', () => {
            if (state.currentPage > 1) searchBooks(state.currentPage - 1);
        });

        elements.nextPageBtn.addEventListener('click', () => searchBooks(state.currentPage + 1));

        // Eventos de prateleira
        const shelfButtons = document.querySelectorAll('.shelf-option');
        shelfButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const shelf = this.getAttribute('data-shelf');
                const bookIndex = elements.selectedBookId.value;

                if (bookIndex === undefined || bookIndex === '') {
                    showAlert('Erro: livro não selecionado', 'danger');
                    return;
                }

                addToShelf(shelf, bookIndex);
            });
        });
    }

    // Inicialização
    setupEventListeners();

    // Função auxiliar para verificar se elemento está visível
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
});