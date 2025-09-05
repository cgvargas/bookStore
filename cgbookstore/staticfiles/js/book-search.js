// ============================================================================
// BOOK SEARCH SCRIPT - VERSÃO COMPLETA E ROBUSTA
// ============================================================================

// Executa apenas quando todo o conteúdo do DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Init] DOM carregado. Iniciando script de busca de livros...');

    // ------------------------------------------------------------------------
    // 1. ESTADO DA APLICAÇÃO E ELEMENTOS DO DOM
    // ------------------------------------------------------------------------
    const elements = {
        searchInput: document.getElementById('search-input'),
        searchButton: document.getElementById('search-button'),
        searchResults: document.getElementById('search-results'),
        pagination: document.getElementById('pagination'),
        pageNumbers: document.getElementById('page-numbers'),
        prevPageBtn: document.getElementById('prev-page'),
        nextPageBtn: document.getElementById('next-page'),
        shelfModal: document.getElementById('shelfModal'),
        selectedBookId: document.getElementById('selected-book-id'),
        bookTemplate: document.getElementById('book-template') // Referência para o template
    };

    // Verificação de elementos essenciais
    if (!elements.searchInput || !elements.searchButton || !elements.searchResults || !elements.bookTemplate) {
        console.error('[Init] Erro Crítico: Um ou mais elementos essenciais (searchInput, searchButton, searchResults, bookTemplate) não foram encontrados no DOM. O script não pode continuar.');
        return; // Interrompe a execução se elementos vitais estiverem faltando
    }

    const state = {
        currentPage: 1,
        currentQuery: '',
        currentBooks: [],
        isProcessing: false,
        has_next: false,
        has_previous: false
    };

    // ------------------------------------------------------------------------
    // 2. FUNÇÕES PRINCIPAIS (Busca, Exibição, Paginação)
    // ------------------------------------------------------------------------

    async function searchBooks(page = 1) {
        const query = elements.searchInput.value.trim();
        if (!query) {
            elements.searchResults.innerHTML = '';
            if(elements.pagination) elements.pagination.style.display = 'none';
            return;
        }

        console.log(`[Search] Iniciando busca por "${query}" na página ${page}...`);
        elements.searchResults.innerHTML = '<div class="text-center p-5"><span class="spinner-border" role="status" aria-hidden="true"></span> Buscando...</div>';

        try {
            const response = await fetch(`/books/search/?q=${encodeURIComponent(query)}&page=${page}`);
            if (response.redirected && response.url.includes('/login/')) {
                window.location.href = response.url;
                return;
            }
            if (!response.ok) throw new Error(`Erro na rede: ${response.statusText}`);

            const data = await response.json();
            state.has_next = data.has_next;
            state.has_previous = data.has_previous;
            state.currentBooks = data.books;
            state.currentPage = page;
            state.currentQuery = query;

            displayBooks(data.books);
            if (elements.pagination) updatePagination(data);

            // Rola para o topo apenas se não for a primeira busca na página
            if (page > 1 || document.referrer.includes(window.location.pathname)) {
                 elements.searchResults.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('[Search] Falha na busca:', error);
            elements.searchResults.innerHTML = `<p class="text-center text-danger">Falha ao buscar livros. Verifique o console para mais detalhes.</p>`;
        }
    }

    function displayBooks(books) {
        elements.searchResults.innerHTML = '';
        if (!books || books.length === 0) {
            elements.searchResults.innerHTML = '<p class="text-center text-muted">Nenhum livro encontrado.</p>';
            return;
        }

        const fragment = document.createDocumentFragment();
        books.forEach((book, index) => {
            const validation = validateBookData(book);
            if (!validation.isValid) return;

            const sanitizedBook = validation.sanitized;
            const clone = elements.bookTemplate.content.cloneNode(true);

            clone.querySelector('.book-cover').src = sanitizedBook.capa_url;
            clone.querySelector('.book-cover').alt = `Capa de ${sanitizedBook.titulo}`;
            clone.querySelector('.book-title').textContent = sanitizedBook.titulo;
            clone.querySelector('.book-author').textContent = sanitizedBook.autores.join(', ');

            const description = sanitizedBook.descricao;
            clone.querySelector('.book-description').textContent = description.length > 150 ? description.substring(0, 150) + '...' : description;

            const dateElement = clone.querySelector('.book-date');
            if (sanitizedBook.data_publicacao !== 'Data não disponível') {
                dateElement.textContent = `Publicado em ${sanitizedBook.data_publicacao}`;
            } else {
                dateElement.style.display = 'none';
            }

            const addButton = clone.querySelector('.add-to-shelf');
            addButton.setAttribute('data-book-index', index);

            fragment.appendChild(clone);
        });

        elements.searchResults.appendChild(fragment);
        setupDynamicShelfButtons();
    }

    function updatePagination(data) {
        const { books, total_pages, current_page, has_previous, has_next } = data;

        if (!has_next && !has_previous) {
            if(elements.pagination) elements.pagination.style.display = 'none';
            return;
        }

        if (current_page > 1 && (!books || books.length === 0)) {
            if(elements.pagination) elements.pagination.style.display = 'none';
            return;
        }

        if(elements.pagination) elements.pagination.style.display = 'flex';

        // Controle dos botões principais
        elements.prevPageBtn.parentElement.classList.toggle('disabled', !has_previous);
        elements.nextPageBtn.parentElement.classList.toggle('disabled', !has_next);

        // Limpa números antigos
        elements.pageNumbers.innerHTML = '';

        // Função auxiliar para criar botões
        const createPageItem = (page, isActive = false) => {
            const li = document.createElement('li');
            li.className = `page-item ${isActive ? 'active' : ''}`;
            const button = document.createElement('button');
            button.className = 'page-link';
            button.textContent = page;
            button.onclick = () => searchBooks(page);
            li.appendChild(button);
            return li;
        };

        // Lógica de exibição dos números
        if (has_previous) {
            elements.pageNumbers.appendChild(createPageItem(current_page - 1));
        }

        elements.pageNumbers.appendChild(createPageItem(current_page, true));

        if (has_next) {
            elements.pageNumbers.appendChild(createPageItem(current_page + 1));
        }
    }

    // ------------------------------------------------------------------------
    // 3. FUNÇÕES UTILITÁRIAS E DE APOIO
    // ------------------------------------------------------------------------

    function validateBookData(book) {
        const sanitized = {
            id: book.id || null,
            external_id: book.external_id || book.id || null,
            titulo: book.titulo || book.title || 'Título não disponível',
            autores: [],
            capa_url: book.capa_url || static('images/no-cover.svg'),
            data_publicacao_raw: book.data_publicacao || null,
            data_publicacao: 'Data não disponível',
            descricao: book.descricao || 'Descrição não disponível',
            source: book.source || 'unknown',
        };

        if (Array.isArray(book.autores)) sanitized.autores = book.autores.filter(a => a);
        else if (Array.isArray(book.authors)) sanitized.autores = book.authors.filter(a => a);
        if (sanitized.autores.length === 0) sanitized.autores = ['Autor desconhecido'];

        const rawDate = sanitized.data_publicacao_raw;
        if (rawDate) {
            if (rawDate.length === 4) sanitized.data_publicacao = rawDate;
            else if (rawDate.length === 7) {
                const [y, m] = rawDate.split('-');
                sanitized.data_publicacao = new Date(y, m - 1).toLocaleDateString('pt-BR', { year: 'numeric', month: 'long' });
            } else if (rawDate.length >= 10) {
                const [y, m, d] = rawDate.split('T')[0].split('-');
                sanitized.data_publicacao = new Date(y, m - 1, d).toLocaleDateString('pt-BR', { year: 'numeric', month: 'long', day: 'numeric' });
            }
        }
        return { isValid: true, sanitized };
    }

    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '1050';
        alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.body.appendChild(alertDiv);
        setTimeout(() => bootstrap.Alert.getOrCreateInstance(alertDiv).close(), 5000);
    }

    // ✅ FUNÇÃO CORRIGIDA PARA ADICIONAR À PRATELEIRA
    async function addToShelf(shelf, bookIndex) {
        if (state.isProcessing) return;
        state.isProcessing = true;

        console.log(`[ADICIONAR] Tentando adicionar livro índice ${bookIndex} à prateleira "${shelf}"`);

        try {
            const book = state.currentBooks[bookIndex];
            const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

            if (!book) {
                throw new Error(`Livro não encontrado no índice ${bookIndex}`);
            }

            // ✅ VALIDAÇÃO ADICIONAL DOS DADOS DO LIVRO
            const validation = validateBookData(book);
            if (!validation.isValid) {
                throw new Error(`Dados do livro inválidos: ${validation.errors.join(', ')}`);
            }

            const sanitizedBook = validation.sanitized;
            console.log("[ADICIONAR] Dados do livro sanitizado:", sanitizedBook);

            let url;
            let payload;

            // ✅ CORREÇÃO: Usar dados sanitizados para decisão de rota
            if (sanitizedBook.source === 'local') {
                url = '/books/add-to-shelf/';
                payload = {
                    book_id: sanitizedBook.id,
                    shelf_type: shelf
                };
                console.log(`[LOCAL] Chamando URL: ${url} com payload:`, payload);

            } else if (sanitizedBook.source === 'google' || sanitizedBook.source === 'external') {
                url = '/books/add-external-to-shelf/';
                payload = {
                    book_data: {
                        titulo: sanitizedBook.titulo,
                        autores: sanitizedBook.autores,
                        descricao: sanitizedBook.descricao,
                        data_publicacao: sanitizedBook.data_publicacao !== 'N/A' ? sanitizedBook.data_publicacao : null,
                        capa_url: sanitizedBook.capa_url,
                        external_id: sanitizedBook.external_id,
                        editora: sanitizedBook.editora,
                    },
                    shelf_type: shelf
                };
                console.log(`[EXTERNO] Chamando URL: ${url} com payload:`, payload);

            } else {
                throw new Error(`Fonte do livro não reconhecida: "${sanitizedBook.source}"`);
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify(payload)
            });

            console.log("[RESPOSTA] Status:", response.status);
            const data = await response.json();
            console.log("[RESPOSTA] Dados:", data);

            if (response.ok && data.success) {
                const modalInstance = bootstrap.Modal.getInstance(elements.shelfModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                showAlert(data.message || 'Livro adicionado com sucesso!', 'success');
                setTimeout(() => { window.location.href = '/profile/'; }, 1500);
            } else {
                throw new Error(data.error || 'Erro desconhecido ao adicionar livro');
            }
        } catch (error) {
            console.error('[ERRO] Detalhes completos:', error);
            showAlert('Erro ao adicionar livro à prateleira: ' + error.message, 'danger');
        } finally {
            state.isProcessing = false;
        }
    }

    function setupDynamicShelfButtons() {
        // Esta função delega o evento, funcionando para botões criados dinamicamente
        elements.searchResults.addEventListener('click', function(e) {
            // Verifica se o elemento clicado é o botão que queremos
            if (e.target && e.target.closest('.add-to-shelf')) {
                e.preventDefault();
                const button = e.target.closest('.add-to-shelf');
                const bookIndex = button.getAttribute('data-book-index');

                if (elements.selectedBookId) {
                    elements.selectedBookId.value = bookIndex;
                }

                // Dispara o modal do Bootstrap
                if (elements.shelfModal) {
                    // Garante que não haja instâncias antigas presas
                    const modalInstance = bootstrap.Modal.getInstance(elements.shelfModal) || new bootstrap.Modal(elements.shelfModal);
                    modalInstance.show();
                }
            }
        });

        // Configura os botões DENTRO do modal uma única vez.
        // Isso evita adicionar múltiplos listeners.
        document.querySelectorAll('.shelf-option').forEach(button => {
            // Remove listeners antigos para evitar chamadas duplicadas
            button.replaceWith(button.cloneNode(true));
        });

        document.querySelectorAll('.shelf-option').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const shelf = this.getAttribute('data-shelf');
                const bookIndex = elements.selectedBookId.value;

                if (bookIndex !== null && bookIndex !== '') {
                    addToShelf(shelf, bookIndex);
                     // Opcional: fecha o modal após o clique
                    const modalInstance = bootstrap.Modal.getInstance(elements.shelfModal);
                    if(modalInstance) modalInstance.hide();
                } else {
                    showAlert('Erro: livro não selecionado. Tente clicar no botão novamente.', 'danger');
                }
            });
        });

        console.log("[Setup] Event listeners dinâmicos para prateleiras configurados.");
    }

    // ------------------------------------------------------------------------
    // 4. INICIALIZAÇÃO DOS EVENT LISTENERS
    // ------------------------------------------------------------------------

    function setupInitialEventListeners() {
        console.log('[Init] Configurando event listeners iniciais...');

        elements.searchButton.addEventListener('click', (e) => {
            e.preventDefault();
            searchBooks(1);
        });

        elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchBooks(1);
            }
        });

        // ✅ MUDANÇA CRÍTICA AQUI:
        // A verificação agora usa o ESTADO da aplicação, não o DOM.
        if(elements.prevPageBtn) {
            elements.prevPageBtn.addEventListener('click', (e) => {
                e.preventDefault();
                // Verifica o estado 'has_previous' que guardamos
                if (state.has_previous) {
                    searchBooks(state.currentPage - 1);
                } else {
                    console.log("[DEBUG] Clique em 'Anterior' ignorado. state.has_previous é falso.");
                }
            });
        }

        if(elements.nextPageBtn) {
            elements.nextPageBtn.addEventListener('click', (e) => {
                e.preventDefault();
                // Verifica o estado 'has_next' que guardamos
                if (state.has_next) {
                    searchBooks(state.currentPage + 1);
                } else {
                    console.log("[DEBUG] Clique em 'Próximo' ignorado. state.has_next é falso.");
                }
            });
        }
        console.log('[Init] Event listeners de busca e paginação configurados.');
    }

    // Ponto de entrada
    setupInitialEventListeners();
});

// Função para retornar a URL estática (exemplo)
function static(path) {
    return `/static/${path}`;
}