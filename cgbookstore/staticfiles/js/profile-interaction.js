// Descrição: Adiciona interações e animações à página de perfil

class ProfileInteractions {
    constructor() {
        console.log('Inicializando profile-interaction.js');
        this.isInitialized = false;
        this.loadingIndicators = new Set();
        this.tooltips = [];
        this.observer = null;
    }

    init() {
        if (this.isInitialized) return;

        this.setupBookHoverEffects();
        this.enhanceModals();
        this.setupIntersectionObserver();
        this.setupForms();
        this.initializeTooltips();

        this.isInitialized = true;
        console.log('Interações de perfil inicializadas');
    }

    setupBookHoverEffects() {
        const bookItems = document.querySelectorAll('.book-item');

        bookItems.forEach(book => {
            // Verificar e garantir que o data-book-id existe
            if (!book.dataset.bookId) {
                const bookId = this.extractBookIdFromUrl(book.onclick?.toString() || '');
                if (bookId) {
                    book.setAttribute('data-book-id', bookId);
                    console.log('Atribuído ID do livro:', bookId);
                } else {
                    console.warn('Não foi possível determinar o ID do livro para:', book);
                    return; // Pular este livro se não conseguirmos determinar o ID
                }
            }

            // Adicionar botões de ação
            if (!book.querySelector('.book-actions')) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'book-actions';

                // Garantir que estamos usando o ID correto
                const bookId = book.dataset.bookId;
                if (!bookId) {
                    console.warn('Ignorando livro sem ID');
                    return;
                }

                console.log('Adicionando ações para livro ID:', bookId);

                actionsDiv.innerHTML = `
                    <button type="button" class="book-action-btn view-btn" title="Ver detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="book-action-btn edit-btn" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="book-action-btn move-btn" title="Mover">
                        <i class="bi bi-arrows-move"></i>
                    </button>
                `;
                book.appendChild(actionsDiv);

                // Adicionar eventos aos botões
                const viewBtn = actionsDiv.querySelector('.view-btn');
                const editBtn = actionsDiv.querySelector('.edit-btn');
                const moveBtn = actionsDiv.querySelector('.move-btn');

                if (viewBtn) {
                    viewBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        window.location.href = `/books/${bookId}/`;
                    });
                }

                if (editBtn) {
                    editBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const shelfType = book.closest('.card')?.dataset.shelfType;
                        this.openEditBookModal(bookId, shelfType);
                    });
                }

                if (moveBtn) {
                    moveBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const shelfType = book.closest('.card')?.dataset.shelfType;
                        this.openMoveBookModal(bookId, shelfType);
                    });
                }
            }
        });
    }

    // Função auxiliar para extrair o ID do livro da URL
    extractBookIdFromUrl(str) {
        if (!str) return null;
        const match = str.match(/\/books\/(\d+)/);
        return match ? match[1] : null;
    }

    enhanceModals() {
        // Melhorar a experiência dos modais
        const modals = document.querySelectorAll('.modal');

        modals.forEach(modal => {
            // Animação de entrada
            modal.addEventListener('show.bs.modal', function() {
                this.style.animation = 'none';
                setTimeout(() => {
                    this.style.animation = '';
                }, 10);
            });

            // Limpar campos ao fechar
            modal.addEventListener('hidden.bs.modal', function() {
                const form = this.querySelector('form');
                if (form) form.reset();

                // Remover classes de validação
                const inputs = form?.querySelectorAll('.form-control');
                inputs?.forEach(input => {
                    input.classList.remove('is-invalid', 'is-valid');
                });
            });
        });
    }

    setupIntersectionObserver() {
        // Adicionar lazy loading nas imagens
        const options = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        this.observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    if (entry.target.tagName === 'IMG') {
                        // Carregar imagem com efeito
                        this.loadImage(entry.target);
                        observer.unobserve(entry.target);
                    } else {
                        // Animar entrada de outros elementos
                        entry.target.classList.add('animated-in');
                        observer.unobserve(entry.target);
                    }
                }
            });
        }, options);

        // Observar imagens de livros
        const bookCovers = document.querySelectorAll('.book-cover');
        bookCovers.forEach(cover => {
            this.observer.observe(cover);
        });

        // Observar cards
        const cards = document.querySelectorAll('.card.mb-4');
        cards.forEach(card => {
            this.observer.observe(card);
        });
    }

    loadImage(img) {
        // Efeito de carregamento suave
        if (!img.complete) {
            img.style.opacity = '0';
            img.onload = function() {
                img.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {
                    img.style.opacity = '1';
                }, 100);
            };
        }
    }

    setupForms() {
        // Melhorar validação de formulários
        const forms = document.querySelectorAll('form');

        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');

            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    if (input.value.trim()) {
                        input.classList.add('is-valid');
                        input.classList.remove('is-invalid');
                    } else if (input.required) {
                        input.classList.add('is-invalid');
                        input.classList.remove('is-valid');
                    }
                });
            });

            // Adicionar feedback ao submeter
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();

                    inputs.forEach(input => {
                        if (!input.value.trim() && input.required) {
                            input.classList.add('is-invalid');
                        }
                    });

                    // Rolar até o primeiro erro
                    const firstError = form.querySelector('.is-invalid');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstError.focus();
                    }
                } else {
                    this.showLoading(form.querySelector('[type="submit"]'));
                }
            });
        });
    }

    initializeTooltips() {
        // Inicializar todos os tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        this.tooltips = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                delay: { show: 300, hide: 100 }
            });
        });
    }

    openEditBookModal(bookId, shelfType) {
        // Implementação do método para abrir o modal de edição
        console.log('Abrindo modal de edição para livro:', bookId, 'na prateleira:', shelfType);
        // Implementação completa seria adicionada aqui
    }

    openMoveBookModal(bookId, shelfType) {
        // Implementação do método para abrir o modal de movimento
        console.log('Abrindo modal de movimento para livro:', bookId, 'na prateleira:', shelfType);
        // Implementação completa seria adicionada aqui
    }

    showLoading(button) {
        if (!button) return;

        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...';

        this.loadingIndicators.add({
            element: button,
            originalText: originalText
        });
    }

    hideLoading(button) {
        if (!button) return;

        for (const indicator of this.loadingIndicators) {
            if (indicator.element === button) {
                button.disabled = false;
                button.innerHTML = indicator.originalText;
                this.loadingIndicators.delete(indicator);
                break;
            }
        }
    }

    // Métodos para expor funcionalidades globalmente
    getOpenEditBookModal() {
        return this.openEditBookModal.bind(this);
    }

    getOpenMoveBookModal() {
        return this.openMoveBookModal.bind(this);
    }

    getShowLoading() {
        return this.showLoading.bind(this);
    }

    getHideLoading() {
        return this.hideLoading.bind(this);
    }
}

// Instância global
let profileInteractions;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    profileInteractions = new ProfileInteractions();
    profileInteractions.init();

    // Exportar funções para o escopo global
    window.openEditBookModal = profileInteractions.getOpenEditBookModal();
    window.openMoveBookModal = profileInteractions.getOpenMoveBookModal();
    window.showLoadingIndicator = profileInteractions.getShowLoading();
    window.hideLoadingIndicator = profileInteractions.getHideLoading();
});

// Versão corrigida sem botão X
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    // Remova a classe alert-dismissible - mantém apenas fade
    alertDiv.className = `alert alert-${type} fade position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.style.transition = 'all 0.3s ease';
    alertDiv.style.transform = 'translateY(-20px)';
    alertDiv.style.opacity = '0';
    alertDiv.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.maxWidth = '500px';

    // Determinar ícone baseado no tipo
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'danger') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';

    // HTML sem o botão de fechar
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${icon} me-2" style="font-size: 1.25rem;"></i>
            <div>${message}</div>
        </div>
    `;

    document.body.appendChild(alertDiv);

    // Adicionar efeito de entrada
    setTimeout(() => {
        alertDiv.classList.add('show');
        alertDiv.style.transform = 'translateY(0)';
        alertDiv.style.opacity = '1';
    }, 10);

    // Remover depois de alguns segundos
    const removeTimeout = setTimeout(() => {
        removeAlert();
    }, 4000);

    function removeAlert() {
        alertDiv.style.transform = 'translateY(-20px)';
        alertDiv.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(alertDiv)) {
                document.body.removeChild(alertDiv);
            }
        }, 300);
    }

    // Pausar o timer quando mouse estiver sobre o alerta
    alertDiv.addEventListener('mouseenter', () => {
        clearTimeout(removeTimeout);
        alertDiv.style.transition = 'none';
    });

    alertDiv.addEventListener('mouseleave', () => {
        alertDiv.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            removeAlert();
        }, 1000);
    });
}