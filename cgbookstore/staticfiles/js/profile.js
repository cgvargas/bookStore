// Estado da aplicação
const STATE = {
    isProcessing: false,
    booksBeingProcessed: new Set(),
    modalsInitialized: false,
    currentBookId: null,
    currentShelfType: null,
    swiperInstances: []
};

// Gerenciador de modais
const ModalManager = {
    modals: {},

    init() {
        const modalElements = {
            bookManager: document.getElementById('bookManagerModal'),
            shelfManager: document.getElementById('shelfManagerModal'),
            editBook: document.getElementById('editBookModal'),
            moveBook: document.getElementById('moveBookModal'),
            newBook: document.getElementById('newBookModal')
        };

        Object.entries(modalElements).forEach(([key, element]) => {
            if (element) {
                this.modals[key] = new bootstrap.Modal(element);
                this.setupModalEvents(element);
            }
        });

        STATE.modalsInitialized = true;
    },

    setupModalEvents(modalElement) {
        if (!modalElement) return;

        modalElement.addEventListener('hidden.bs.modal', () => {
            this.clearModalBackdrop();
            modalElement.removeAttribute('aria-hidden');
        });

        modalElement.addEventListener('show.bs.modal', () => {
            this.clearModalBackdrop();
        });
    },

    show(modalName) {
        if (this.modals[modalName]) {
            this.modals[modalName].show();
        } else {
            console.error(`Modal ${modalName} não encontrado`);
        }
    },

    hide(modalName) {
        if (this.modals[modalName]) {
            this.modals[modalName].hide();
        }
    },

    clearModalBackdrop() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
    }
};

// Gerenciador de Livros
const BookManager = {
    isProcessing(bookId) {
        return STATE.booksBeingProcessed.has(bookId);
    },

    markAsProcessing(bookId) {
        STATE.booksBeingProcessed.add(bookId);
        setTimeout(() => STATE.booksBeingProcessed.delete(bookId), 1000);
    },

    async removeBook(bookId, shelfType) {
        if (this.isProcessing(bookId)) return;
        this.markAsProcessing(bookId);

        try {
            const response = await fetch('/books/remove-from-shelf/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ book_id: bookId, shelf_type: shelfType })
            });

            const data = await response.json();

            if (data.success) {
                showAlert('Livro removido com sucesso!');
                ModalManager.hide('bookManager');
                setTimeout(() => window.location.reload(), 500);
            } else {
                throw new Error(data.error || 'Erro ao remover livro');
            }
        } catch (error) {
            console.error('Erro:', error);
            showAlert(error.message || 'Erro ao remover livro', 'danger');
        }
    }
};

// Gerenciador de Carrossel
const CarouselManager = {
    async init() {
        try {
            const { default: SwiperConfig } = await import('/static/js/swiper-config.js');
            STATE.swiperInstances = SwiperConfig.initAll();
        } catch (error) {
            console.error('Erro ao inicializar carrosséis:', error);
        }
    }
};

// Funções Utilitárias
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

function showAlert(message, type = 'success') {
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

// Funções de Navegação
function openBookManager(bookId, shelfType) {
    if (BookManager.isProcessing(bookId)) return;
    STATE.currentBookId = bookId;
    STATE.currentShelfType = shelfType;
    window.location.href = `/books/${bookId}/`;
}

function openShelfManager(shelfType) {
    if (!STATE.modalsInitialized) {
        console.error('Modais não inicializados');
        return;
    }
    STATE.currentShelfType = shelfType;
    ModalManager.show('shelfManager');
}

function openNewBookModal(shelfType) {
    if (!STATE.modalsInitialized) {
        console.error('Modais não inicializados');
        return;
    }

    // Atualiza o tipo de prateleira no estado
    STATE.currentShelfType = shelfType;

    // Atualiza o campo hidden do formulário
    document.getElementById('newBookShelfType').value = shelfType;

    // Exibe o modal
    ModalManager.show('newBook');
}

// Adicionar a função que será chamada ao clicar em "Adicionar" no modal
async function saveNewBook() {
    const form = document.getElementById('newBookForm');
    const bookData = {
        titulo: document.getElementById('newTitle').value,
        autor: document.getElementById('newAuthor').value,
        descricao: document.getElementById('newDescription').value,
        editora: document.getElementById('newPublisher').value,
        categoria: document.getElementById('newCategory').value,
        shelf_type: document.getElementById('newBookShelfType').value
    };

    try {
        const formData = new FormData();

        // Adicionar dados do livro
        Object.keys(bookData).forEach(key => {
            formData.append(key, bookData[key]);
        });

        // Adicionar arquivo de capa se existir
        const coverFile = document.getElementById('newCover').files[0];
        if (coverFile) {
            formData.append('capa', coverFile);
        }

        const response = await fetch('/books/add-book-manual/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showAlert('Livro adicionado com sucesso!');
            ModalManager.hide('newBook');
            setTimeout(() => window.location.reload(), 500);
        } else {
            throw new Error(data.error || 'Erro ao adicionar livro');
        }
    } catch (error) {
        console.error('Erro:', error);
        showAlert(error.message || 'Erro ao adicionar livro', 'danger');
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    ModalManager.init();
    CarouselManager.init();

    // Configurar eventos dos botões
    document.getElementById('editBookBtn')?.addEventListener('click', () => {
        ModalManager.hide('bookManager');
        window.location.href = `/books/${STATE.currentBookId}/`;
    });

    document.getElementById('moveBookBtn')?.addEventListener('click', () => {
        ModalManager.hide('bookManager');
        ModalManager.show('moveBook');
    });

    document.getElementById('deleteBookBtn')?.addEventListener('click', () => {
        if (confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
            BookManager.removeBook(STATE.currentBookId, STATE.currentShelfType);
        }
    });
});

// Adicionando handler para upload de foto
document.getElementById('avatarInput')?.addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('profile_photo', file);

    try {
        const response = await fetch('/profile/update-photo/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            window.location.reload();
        } else {
            showAlert(data.error || 'Erro ao atualizar foto', 'danger');
        }
    } catch (error) {
        console.error('Erro:', error);
        showAlert('Erro ao atualizar foto', 'danger');
    }
});

// Tratamento de Erros Global
window.addEventListener('error', function(event) {
    if (event.error?.toString().includes('Modal')) {
        console.error('Erro no gerenciamento de modais:', event.error);
        ModalManager.clearModalBackdrop();
    }
});