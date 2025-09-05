/**
 * CORREÇÃO COMPLETA DOS MODAIS - PÁGINA DE DETALHES DO LIVRO
 * Soluciona travamentos e problemas de funcionalidade
 */

(function() {
    'use strict';

    console.log('🔧 Iniciando correção completa dos modais...');

    /**
     * Classe para gerenciar modais com segurança
     */
    class ModalManager {
        constructor() {
            this.modals = new Map();
            this.isInitialized = false;
            this.bookData = null;
            this.init();
        }

        /**
         * Inicialização principal
         */
        init() {
            console.log('📋 Inicializando ModalManager...');

            // Aguarda DOM estar pronto
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setup());
            } else {
                this.setup();
            }
        }

        /**
         * Configuração após DOM pronto
         */
        setup() {
            try {
                // Carrega dados do livro de forma segura
                this.loadBookData();

                // Aguarda Bootstrap estar disponível
                this.waitForBootstrap(() => {
                    this.initializeModals();
                    this.setupEventListeners();
                    this.replaceGlobalFunctions();
                    this.isInitialized = true;
                    console.log('✅ ModalManager inicializado com sucesso');
                });

            } catch (error) {
                console.error('❌ Erro na configuração do ModalManager:', error);
                this.setupFallbackHandlers();
            }
        }

        /**
         * Carrega dados do livro de forma mais robusta
         */
        loadBookData() {
            try {
                // Tenta múltiplas fontes de dados
                const sources = [
                    () => {
                        const element = document.getElementById('book-data');
                        return element ? JSON.parse(element.textContent) : null;
                    },
                    () => {
                        const detailsDiv = document.querySelector('.book-details');
                        if (detailsDiv) {
                            return {
                                id: detailsDiv.getAttribute('data-book-id'),
                                external_id: detailsDiv.getAttribute('data-external-id'),
                                current_shelf: detailsDiv.getAttribute('data-current-shelf')
                            };
                        }
                        return null;
                    },
                    () => {
                        // Fallback: extrai do console.log do template
                        if (window.bookId) {
                            return { id: window.bookId };
                        }
                        return null;
                    }
                ];

                for (const source of sources) {
                    try {
                        const data = source();
                        if (data) {
                            this.bookData = data;
                            console.log('📚 Dados do livro carregados:', this.bookData);
                            break;
                        }
                    } catch (e) {
                        console.warn('⚠️ Fonte de dados falhou:', e.message);
                    }
                }

                if (!this.bookData) {
                    console.warn('⚠️ Nenhuma fonte de dados válida encontrada');
                    this.bookData = { id: null };
                }

            } catch (error) {
                console.error('❌ Erro ao carregar dados do livro:', error);
                this.bookData = { id: null };
            }
        }

        /**
         * Aguarda Bootstrap estar disponível
         */
        waitForBootstrap(callback, attempts = 0) {
            if (typeof bootstrap !== 'undefined') {
                callback();
            } else if (attempts < 50) { // 5 segundos máximo
                setTimeout(() => this.waitForBootstrap(callback, attempts + 1), 100);
            } else {
                console.error('❌ Bootstrap não carregou, usando fallback');
                this.setupFallbackHandlers();
            }
        }

        /**
         * Inicializa todos os modais
         */
        initializeModals() {
            const modalSelectors = [
                '#addToShelfModal',
                '#moveBookModal',
                '#imageModal'
            ];

            modalSelectors.forEach(selector => {
                const element = document.querySelector(selector);
                if (element) {
                    try {
                        // Destroi instância existente se houver
                        const existingInstance = bootstrap.Modal.getInstance(element);
                        if (existingInstance) {
                            existingInstance.dispose();
                        }

                        // Cria nova instância
                        const modal = new bootstrap.Modal(element, {
                            backdrop: true,
                            keyboard: true,
                            focus: true
                        });

                        this.modals.set(selector, modal);
                        console.log(`✅ Modal ${selector} inicializado`);

                    } catch (error) {
                        console.error(`❌ Erro ao inicializar modal ${selector}:`, error);
                    }
                }
            });
        }

        /**
         * Configura event listeners
         */
        setupEventListeners() {
            // Event listeners para botões de fechar
            document.querySelectorAll('.modal .btn-close, .modal [data-bs-dismiss="modal"]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeModal(e.target.closest('.modal'));
                });
            });

            // Event listeners para clique no backdrop
            document.querySelectorAll('.modal').forEach(modal => {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        this.closeModal(modal);
                    }
                });
            });

            // Event listeners para ESC key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const openModal = document.querySelector('.modal.show');
                    if (openModal) {
                        this.closeModal(openModal);
                    }
                }
            });
        }

        /**
         * Substitui funções globais por versões seguras
         */
        replaceGlobalFunctions() {
            // Substitui openShelfModal
            window.openShelfModal = () => {
                console.log('📖 Abrindo modal de prateleira...');
                this.openModal('#addToShelfModal');
            };

            // Substitui openMoveModal
            window.openMoveModal = () => {
                console.log('🔄 Abrindo modal de mover...');
                this.openModal('#moveBookModal');
            };

            // Substitui addToShelf
            window.addToShelf = () => {
                console.log('➕ Adicionando à prateleira...');
                this.handleAddToShelf();
            };

            // Substitui moveBook
            window.moveBook = () => {
                console.log('🔄 Movendo livro...');
                this.handleMoveBook();
            };

            // Substitui confirmRemove
            window.confirmRemove = () => {
                console.log('🗑️ Confirmando remoção...');
                this.handleRemoveBook();
            };

            console.log('🔄 Funções globais substituídas');
        }

        /**
         * Abre modal de forma segura
         */
        openModal(selector) {
            try {
                console.log(`🔓 Tentando abrir modal: ${selector}`);

                const modal = this.modals.get(selector);
                if (modal) {
                    modal.show();
                    console.log(`✅ Modal ${selector} aberto com sucesso`);
                } else {
                    // Fallback: tenta abrir diretamente
                    const element = document.querySelector(selector);
                    if (element) {
                        const fallbackModal = new bootstrap.Modal(element);
                        fallbackModal.show();
                        console.log(`✅ Modal ${selector} aberto via fallback`);
                    } else {
                        console.error(`❌ Modal ${selector} não encontrado`);
                    }
                }
            } catch (error) {
                console.error(`❌ Erro ao abrir modal ${selector}:`, error);
                this.showErrorMessage('Erro ao abrir modal. Tente novamente.');
            }
        }

        /**
         * Fecha modal de forma segura
         */
        closeModal(modalElement) {
            try {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    modalElement.classList.remove('show');
                    modalElement.style.display = 'none';
                    document.body.classList.remove('modal-open');

                    // Remove backdrop
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                }
                console.log('✅ Modal fechado com sucesso');
            } catch (error) {
                console.error('❌ Erro ao fechar modal:', error);
            }
        }

        /**
         * Manipula adição à prateleira
         */
        async handleAddToShelf() {
            try {
                const form = document.querySelector('#addToShelfForm');
                const select = form.querySelector('select[name="shelf_type"]');
                const shelfType = select.value;

                if (!shelfType) {
                    this.showErrorMessage('Por favor, selecione uma prateleira.');
                    return;
                }

                console.log('📚 Adicionando à prateleira:', shelfType);

                // Prepara payload baseado no tipo de livro
                let payload, url;

                if (this.bookData && this.bookData.id) {
                    // Livro já existe no banco
                    url = '/books/add-to-shelf/';
                    payload = {
                        book_id: this.bookData.id,
                        shelf_type: shelfType
                    };
                } else {
                    // Livro externo
                    url = '/books/add-external-to-shelf/';
                    payload = {
                        book_data: this.bookData || {},
                        shelf_type: shelfType
                    };
                }

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && (data.success || data.status === 'success')) {
                    this.closeModal(document.querySelector('#addToShelfModal'));
                    this.showSuccessMessage(data.message || 'Livro adicionado com sucesso!');

                    // Recarrega página após sucesso
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    throw new Error(data.error || data.message || 'Erro desconhecido');
                }

            } catch (error) {
                console.error('❌ Erro ao adicionar à prateleira:', error);
                this.showErrorMessage(error.message || 'Erro ao adicionar livro à prateleira');
            }
        }

        /**
         * Manipula movimentação entre prateleiras
         */
        async handleMoveBook() {
            try {
                const form = document.querySelector('#moveBookForm');
                const select = form.querySelector('select[name="new_shelf"]');
                const newShelf = select.value;

                if (!newShelf) {
                    this.showErrorMessage('Por favor, selecione uma nova prateleira.');
                    return;
                }

                if (!this.bookData || !this.bookData.id) {
                    this.showErrorMessage('Erro: ID do livro não encontrado.');
                    return;
                }

                console.log('🔄 Movendo livro para:', newShelf);

                const response = await fetch(`/books/${this.bookData.id}/move/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        new_shelf: newShelf
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.closeModal(document.querySelector('#moveBookModal'));
                    this.showSuccessMessage('Livro movido com sucesso!');

                    // Recarrega página após sucesso
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(data.error || 'Erro ao mover livro');
                }

            } catch (error) {
                console.error('❌ Erro ao mover livro:', error);
                this.showErrorMessage(error.message || 'Erro ao mover livro');
            }
        }

        /**
         * Manipula remoção de livro
         */
        async handleRemoveBook() {
            if (!confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
                return;
            }

            try {
                if (!this.bookData || !this.bookData.id) {
                    this.showErrorMessage('Erro: ID do livro não encontrado.');
                    return;
                }

                console.log('🗑️ Removendo livro...');

                const response = await fetch(`/books/${this.bookData.id}/remove-from-shelf/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        shelf_type: this.bookData.current_shelf
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showSuccessMessage('Livro removido com sucesso!');
                    setTimeout(() => {
                        window.location.href = '/profile/';
                    }, 1000);
                } else {
                    throw new Error(data.error || 'Erro ao remover livro');
                }

            } catch (error) {
                console.error('❌ Erro ao remover livro:', error);
                this.showErrorMessage(error.message || 'Erro ao remover livro');
            }
        }

        /**
         * Obtém token CSRF
         */
        getCSRFToken() {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    return decodeURIComponent(value);
                }
            }

            // Fallback: tenta pegar do meta tag
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            return metaTag ? metaTag.getAttribute('content') : '';
        }

        /**
         * Mostra mensagem de sucesso
         */
        showSuccessMessage(message) {
            this.showMessage(message, 'success');
        }

        /**
         * Mostra mensagem de erro
         */
        showErrorMessage(message) {
            this.showMessage(message, 'danger');
        }

        /**
         * Mostra mensagem toast
         */
        showMessage(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            toast.style.cssText = `
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
            `;

            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            document.body.appendChild(toast);

            // Remove automaticamente após 5 segundos
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 5000);
        }

        /**
         * Configura handlers de fallback para casos extremos
         */
        setupFallbackHandlers() {
            console.log('⚠️ Configurando handlers de fallback...');

            window.openShelfModal = () => {
                alert('Funcionalidade temporariamente indisponível. Recarregue a página.');
            };

            window.openMoveModal = () => {
                alert('Funcionalidade temporariamente indisponível. Recarregue a página.');
            };

            window.addToShelf = () => {
                alert('Funcionalidade temporariamente indisponível. Recarregue a página.');
            };

            window.moveBook = () => {
                alert('Funcionalidade temporariamente indisponível. Recarregue a página.');
            };

            window.confirmRemove = () => {
                alert('Funcionalidade temporariamente indisponível. Recarregue a página.');
            };
        }

        /**
         * Método público para debug
         */
        debug() {
            console.log('🔍 Debug ModalManager:', {
                isInitialized: this.isInitialized,
                bookData: this.bookData,
                modals: Array.from(this.modals.keys()),
                bootstrapAvailable: typeof bootstrap !== 'undefined'
            });
        }
    }

    // Variável global para o gerenciador
    let modalManager = null;

    /**
     * Função de inicialização
     */
    function initializeModalManager() {
        try {
            if (modalManager) {
                console.log('🔄 ModalManager já existe, reinicializando...');
            }

            modalManager = new ModalManager();

            // Disponibiliza globalmente para debug
            window.modalManager = modalManager;

            console.log('✅ ModalManager criado e disponível globalmente');

        } catch (error) {
            console.error('❌ Erro crítico na inicialização:', error);
        }
    }

    // Inicialização baseada no estado do documento
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeModalManager);
    } else {
        // DOM já carregado, inicializa com delay para garantir outros scripts
        setTimeout(initializeModalManager, 100);
    }

    // Função de emergência disponível globalmente
    window.emergencyModalFix = function() {
        console.log('🚨 Executando correção de emergência...');

        // Remove event listeners problemáticos
        document.querySelectorAll('.modal').forEach(modal => {
            const newModal = modal.cloneNode(true);
            modal.parentNode.replaceChild(newModal, modal);
        });

        // Reinicializa
        setTimeout(initializeModalManager, 500);
    };

    console.log('🔧 Sistema de correção de modais carregado');

})();