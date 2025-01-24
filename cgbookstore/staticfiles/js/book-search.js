document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, iniciando configuração...');
    const searchInput = document.getElementById('search-input');
    const searchType = document.getElementById('search-type');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    const pagination = document.getElementById('pagination');
    const pageNumbers = document.getElementById('page-numbers');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const shelfModal = document.getElementById('shelfModal');
    const selectedBookId = document.getElementById('selected-book-id');
    let currentPage = 1;
    let currentBooks = [];
    let currentModal = null;

    // Inicializar modal com configurações corretas
    const modal = new bootstrap.Modal(shelfModal, {
        backdrop: true,
        keyboard: true
    });

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

    // Função para adicionar livro à prateleira
    async function addToShelf(shelf, bookIndex) {
        try {
            const book = currentBooks[bookIndex];
            if (!book) {
                throw new Error('Livro não encontrado');
            }

            const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
            if (!token) {
                throw new Error('Token CSRF não encontrado');
            }

            const response = await fetch('/books/add-to-shelf/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify({
                    book_data: {
                        title: book.title,
                        authors: book.authors,
                        description: book.description,
                        published_date: book.published_date,
                        thumbnail: book.thumbnail,
                        publisher: book.publisher,
                        categories: book.categories
                    },
                    shelf: shelf
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro ao adicionar livro');
            }

            // Fechar o modal corretamente
            const modalInstance = bootstrap.Modal.getInstance(shelfModal);
            if (modalInstance) {
                modalInstance.hide();
            }

            showAlert(data.message || 'Livro adicionado com sucesso!', 'success');

        } catch (error) {
            console.error('Erro ao adicionar livro:', error);
            showAlert(error.message || 'Erro ao adicionar livro à prateleira', 'danger');
        }
    }

    // Configurar botões de prateleira
    function setupShelfButtons() {
        const addButtons = document.querySelectorAll('.add-to-shelf');

        addButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const bookIndex = this.getAttribute('data-book-index');
                selectedBookId.value = bookIndex;

                // Mostrar modal usando a instância Bootstrap
                const modalInstance = new bootstrap.Modal(shelfModal);
                modalInstance.show();
            });
        });
    }

    // Event listeners para botões da prateleira
    const shelfButtons = document.querySelectorAll('.shelf-option');
    shelfButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const shelf = this.getAttribute('data-shelf');
            const bookIndex = selectedBookId.value;

            if (bookIndex === undefined || bookIndex === '') {
                showAlert('Erro: livro não selecionado', 'danger');
                return;
            }

            addToShelf(shelf, bookIndex);
        });
    });

    // Função para exibir os livros
    function displayBooks(books) {
        searchResults.innerHTML = '';
        const template = document.getElementById('book-template');

        books.forEach((book, index) => {
            const clone = template.content.cloneNode(true);

            const img = clone.querySelector('.book-cover');
            img.src = book.thumbnail || '/static/images/no-cover.svg';
            img.alt = `Capa do livro ${book.title}`;

            clone.querySelector('.book-title').textContent = book.title;
            clone.querySelector('.book-author').textContent = book.authors.join(', ');

            const publishedYear = book.published_date ? book.published_date.split('-')[0] : 'Data não disponível';
            clone.querySelector('.book-date').textContent = `Publicado em ${publishedYear}`;

            const description = book.description || 'Descrição não disponível';
            clone.querySelector('.book-description').textContent =
                description.length > 200 ? description.substring(0, 200) + '...' : description;

            const addButton = clone.querySelector('.add-to-shelf');
            addButton.setAttribute('data-book-index', index);

            searchResults.appendChild(clone);
        });

        setupShelfButtons();
    }

    // Função para buscar livros
    async function searchBooks(page = 1) {
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            const response = await fetch(`/books/search/?q=${encodeURIComponent(query)}&type=${searchType.value}&page=${page}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro ao buscar livros');
            }

            currentBooks = data.books;
            displayBooks(data.books);
            updatePagination(data);
            currentPage = page;
        } catch (error) {
            console.error('Erro:', error);
            showAlert('Erro ao buscar livros: ' + error.message, 'danger');
        }
    }

    // Event listeners para busca
    searchButton.addEventListener('click', () => searchBooks(1));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBooks(1);
        }
    });

    // Event listeners para paginação
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            searchBooks(currentPage - 1);
        }
    });

    nextPageBtn.addEventListener('click', () => {
        searchBooks(currentPage + 1);
    });

    // Função para atualizar a paginação
    function updatePagination(data) {
        const { total_pages, current_page, has_previous, has_next } = data;
        prevPageBtn.disabled = !has_previous;
        nextPageBtn.disabled = !has_next;

        pageNumbers.innerHTML = '';
        let pages = [];

        pages.push(1);
        if (current_page > 3) pages.push('...');

        for (let i = Math.max(2, current_page - 1); i <= Math.min(total_pages - 1, current_page + 1); i++) {
            pages.push(i);
        }

        if (current_page < total_pages - 2) pages.push('...');
        if (total_pages > 1) pages.push(total_pages);

        pages.forEach(page => {
            if (page === '...') {
                const span = document.createElement('span');
                span.className = 'page-ellipsis mx-2';
                span.textContent = '...';
                pageNumbers.appendChild(span);
            } else {
                const button = document.createElement('button');
                button.className = `page-link ${page === current_page ? 'active' : ''}`;
                button.textContent = page;
                button.onclick = () => searchBooks(page);
                const li = document.createElement('li');
                li.className = 'page-item';
                li.appendChild(button);
                pageNumbers.appendChild(li);
            }
        });
    }

    // Limpar estado ao fechar modal
    shelfModal.addEventListener('hidden.bs.modal', function () {
        selectedBookId.value = '';
    });
});