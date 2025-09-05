/**
 * book-details.js - VERSÃO FINAL CORRIGIDA E OTIMIZADA
 *
 * Responsável por toda a interatividade na página de detalhes do livro.
 *
 * Correções Implementadas:
 * - O script só é executado na página de detalhes do livro, prevenindo conflitos globais.
 * - Desativa o `backdrop` nativo do Bootstrap, que estava causando o congelamento da tela.
 * - Implementa um sistema de backdrop customizado que não bloqueia os cliques nos botões do modal.
 * - Gerencia o estado para prevenir ações duplicadas (ex: cliques múltiplos).
 * - Centraliza a lógica em um único objeto `BookDetailsApp` para organização e clareza.
 */

// Etapa 1: Garante que o script só execute na página correta
if (!window.location.pathname.match(/\/books\/\d+\/$/)) {
    console.log('[BookDetails] Não é a página de detalhes do livro. Script inativo.');
} else {
    console.log('[BookDetails] Página de detalhes detectada. Inicializando script...');

    const BookDetailsApp = {
        initialized: false,

        // Estado centralizado da aplicação na página
        state: {
            bookData: null,
            bookId: null,
            currentShelf: null,
            isProcessing: false,
            modals: new Map() // Armazena instâncias dos modais Bootstrap
        },

        // Funções utilitárias
        utils: {
            getCookie(name) {
                if (!document.cookie) return null;
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
            },

            getCSRFToken() {
                return this.getCookie('csrftoken') ||
                       document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                       document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            },

            showAlert(message, type = 'success') {
                const existingAlert = document.querySelector('.cg-alert-details');
                if (existingAlert) existingAlert.remove();

                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed cg-alert-details`;
                alertDiv.style.cssText = `top: 80px; right: 20px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15);`;
                alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
                document.body.appendChild(alertDiv);
                setTimeout(() => {
                    if (alertDiv.parentElement) new bootstrap.Alert(alertDiv).close();
                }, 5000);
            },

            setButtonLoading(button, isLoading = true) {
                if (!button) return;
                if (isLoading) {
                    button.disabled = true;
                    button.dataset.originalHtml = button.innerHTML;
                    button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...`;
                } else {
                    button.disabled = false;
                    if (button.dataset.originalHtml) {
                        button.innerHTML = button.dataset.originalHtml;
                    }
                }
            }
        },

        // ===== MÓDULO DE GERENCIAMENTO DE MODAIS (CORREÇÃO CRÍTICA APLICADA) =====
        ModalManager: {
            init() {
                this.waitForBootstrap(() => {
                    this.initializeModals();
                    this.setupCustomBackdrop();
                    this.setupEventListeners();
                });
            },

            waitForBootstrap(callback, attempts = 0) {
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    callback();
                } else if (attempts < 50) { // Tenta por 5 segundos
                    setTimeout(() => this.waitForBootstrap(callback, attempts + 1), 100);
                } else {
                    console.error('[BookDetails] Bootstrap não carregou. Funcionalidades de modal estão desativadas.');
                    BookDetailsApp.utils.showAlert('Erro ao carregar componentes da página. Por favor, recarregue.', 'danger');
                }
            },

            initializeModals() {
                const modalSelectors = ['#addToShelfModal', '#moveBookModal', '#imageModal'];
                modalSelectors.forEach(selector => {
                    const element = document.querySelector(selector);
                    if (element) {
                        try {
                            // ✅ CORREÇÃO CRÍTICA: Desativa o backdrop nativo do Bootstrap
                            const modal = new bootstrap.Modal(element, {
                                backdrop: false,
                                keyboard: true,
                                focus: true
                            });
                            BookDetailsApp.state.modals.set(selector, modal);
                            console.log(`[BookDetails] Modal ${selector} inicializado SEM backdrop nativo.`);
                        } catch (error) {
                            console.error(`[BookDetails] Erro ao inicializar modal ${selector}:`, error);
                        }
                    } else {
                         console.warn(`[BookDetails] Elemento de modal não encontrado: ${selector}`);
                    }
                });
            },

            // Sistema de backdrop customizado que não interfere nos eventos de clique
            setupCustomBackdrop() {
                if (document.getElementById('customModalBackdrop')) return;
                const backdrop = document.createElement('div');
                backdrop.id = 'customModalBackdrop';
                Object.assign(backdrop.style, {
                    position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
                    backgroundColor: 'rgba(0, 0, 0, 0.5)', zIndex: 1050,
                    opacity: 0, visibility: 'hidden', transition: 'opacity 0.15s linear'
                });
                backdrop.addEventListener('click', () => {
                    const openModal = document.querySelector('.modal.show');
                    if (openModal) this.closeModal(openModal);
                });
                document.body.appendChild(backdrop);
            },

            showCustomBackdrop() {
                const backdrop = document.getElementById('customModalBackdrop');
                if (backdrop) {
                    backdrop.style.visibility = 'visible';
                    backdrop.style.opacity = '1';
                }
            },

            hideCustomBackdrop() {
                const backdrop = document.getElementById('customModalBackdrop');
                if (backdrop) {
                    backdrop.style.opacity = '0';
                    setTimeout(() => { backdrop.style.visibility = 'hidden'; }, 150);
                }
            },

            openModal(selector) {
                const modalInstance = BookDetailsApp.state.modals.get(selector);
                if (modalInstance) {
                    this.showCustomBackdrop();
                    modalInstance.show();
                    document.body.classList.add('modal-open-custom');
                } else {
                    console.error(`[BookDetails] Tentativa de abrir modal não encontrado: ${selector}`);
                    BookDetailsApp.utils.showAlert('Ocorreu um erro ao tentar abrir a janela. Por favor, recarregue a página.', 'danger');
                }
            },

            closeModal(modalElement) {
                if (!modalElement) return;
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) {
                    modalInstance.hide();
                }
                this.hideCustomBackdrop();
                document.body.classList.remove('modal-open-custom');
            },

            setupEventListeners() {
                // Delegação de eventos para os botões de ação principais
                document.body.addEventListener('click', (e) => {
                    const actionButton = e.target.closest('[data-action]');
                    if (!actionButton) return;

                    if (BookDetailsApp.state.isProcessing) return;

                    const action = actionButton.getAttribute('data-action');
                    if (action === 'add-to-shelf') {
                        BookDetailsApp.BookManager.addToShelf(actionButton);
                    } else if (action === 'move-book') {
                        BookDetailsApp.BookManager.moveBook(actionButton);
                    }
                });

                // Botões de fechar e cancelar
                document.querySelectorAll('.modal [data-bs-dismiss="modal"]').forEach(btn => {
                    btn.addEventListener('click', () => this.closeModal(btn.closest('.modal')));
                });
            }
        },

        // Módulo para lógica de negócio (interação com o backend)
        BookManager: {
            async addToShelf(button) {
                if (BookDetailsApp.state.isProcessing) return;
                BookDetailsApp.state.isProcessing = true;
                BookDetailsApp.utils.setButtonLoading(button, true);

                try {
                    const form = document.getElementById('addToShelfForm');
                    const shelfType = form.querySelector('[name="shelf_type"]').value;
                    const book = BookDetailsApp.state.bookData;
                    const token = BookDetailsApp.utils.getCSRFToken();

                    const isExternal = !book.id;
                    const url = isExternal ? '/books/add-external-to-shelf/' : '/books/add-to-shelf/';
                    const payload = isExternal ? {
                        book_data: {
                            titulo: book.titulo, autores: [book.autor], descricao: book.descricao,
                            capa_url: book.capa_url, external_id: book.external_id,
                        },
                        shelf_type: shelfType
                    } : { book_id: book.id, shelf_type: shelfType };

                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
                        body: JSON.stringify(payload)
                    });

                    const data = await response.json();
                    if (data.success) {
                        BookDetailsApp.utils.showAlert(data.message || 'Livro adicionado com sucesso!');
                        BookDetailsApp.ModalManager.closeModal(button.closest('.modal'));
                        setTimeout(() => window.location.reload(), 1500);
                    } else {
                        throw new Error(data.error || 'Não foi possível adicionar o livro.');
                    }
                } catch (error) {
                    BookDetailsApp.utils.showAlert(error.message, 'danger');
                } finally {
                    BookDetailsApp.state.isProcessing = false;
                    BookDetailsApp.utils.setButtonLoading(button, false);
                }
            },

            async moveBook(button) {
                if (BookDetailsApp.state.isProcessing) return;
                BookDetailsApp.state.isProcessing = true;
                BookDetailsApp.utils.setButtonLoading(button, true);

                try {
                    const form = document.getElementById('moveBookForm');
                    const newShelf = form.querySelector('[name="new_shelf"]').value;
                    const bookId = BookDetailsApp.state.bookId;
                    const token = BookDetailsApp.utils.getCSRFToken();

                    const response = await fetch(`/books/${bookId}/move-shelf/`, {
                         method: 'POST',
                         headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
                         body: JSON.stringify({ new_shelf: newShelf })
                    });

                    const data = await response.json();
                    if (data.success) {
                        BookDetailsApp.utils.showAlert('Livro movido com sucesso!');
                        BookDetailsApp.ModalManager.closeModal(button.closest('.modal'));
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        throw new Error(data.error || 'Não foi possível mover o livro.');
                    }
                } catch (error) {
                    BookDetailsApp.utils.showAlert(error.message, 'danger');
                } finally {
                    BookDetailsApp.state.isProcessing = false;
                    BookDetailsApp.utils.setButtonLoading(button, false);
                }
            },

            async removeBook() {
                if (BookDetailsApp.state.isProcessing) return;
                if (!confirm('Tem certeza que deseja remover este livro da sua prateleira?')) return;

                BookDetailsApp.state.isProcessing = true;
                try {
                    const response = await fetch(`/books/${BookDetailsApp.state.bookId}/remove-from-shelf/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': BookDetailsApp.utils.getCSRFToken() },
                        body: JSON.stringify({ shelf_type: BookDetailsApp.state.currentShelf })
                    });
                    const data = await response.json();
                    if (data.success) {
                        BookDetailsApp.utils.showAlert('Livro removido com sucesso!');
                        setTimeout(() => window.location.href = '/profile/', 1500);
                    } else {
                         throw new Error(data.error || 'Não foi possível remover o livro.');
                    }
                } catch(error) {
                    BookDetailsApp.utils.showAlert(error.message, 'danger');
                } finally {
                     BookDetailsApp.state.isProcessing = false;
                }
            }
        },

        // Ponto de entrada da aplicação
        init() {
            if (this.initialized) return;
            this.initialized = true;

            // Carrega dados iniciais do DOM
            try {
                const bookDataElement = document.getElementById('book-data');
                this.state.bookData = JSON.parse(bookDataElement.textContent);
                this.state.bookId = this.state.bookData.id || window.bookId;
                this.state.currentShelf = this.state.bookData.current_shelf || window.bookShelf;
            } catch (e) {
                console.error('[BookDetails] Erro ao carregar dados do livro. Usando fallbacks.', e);
                this.state.bookId = window.bookId;
                this.state.currentShelf = window.bookShelf;
            }

            // Inicia os módulos
            this.ModalManager.init();

            console.log('[BookDetails] Aplicação inicializada com estado:', this.state);
        }
    };

    // Etapa 2: Adiciona as funções ao escopo global para compatibilidade com `onclick`
    window.openMoveModal = () => BookDetailsApp.ModalManager.openModal('#moveBookModal');
    window.openShelfModal = () => BookDetailsApp.ModalManager.openModal('#addToShelfModal');
    window.confirmRemove = () => BookDetailsApp.BookManager.removeBook();

    // Etapa 3: Inicializa a aplicação quando o DOM estiver pronto
    document.addEventListener('DOMContentLoaded', () => {
        BookDetailsApp.init();
    });
}