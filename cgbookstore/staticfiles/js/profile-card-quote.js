// profile-card-quote.js
// Componente para exibir uma citação literária favorita no card de perfil

class ProfileCardQuote {
    constructor() {
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.quoteData = null;
        this.isEditing = false;

        if (this.cardElement) {
            this.init();
        } else {
            console.error('Card de perfil não encontrado para widget de citação');
        }
    }

    init() {
        this.loadQuoteData();
    }

    async loadQuoteData() {
        try {
            // Carregar dados da citação favorita da API
            const response = await fetch('/profile/favorite-quote/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.quoteData = await response.json();
            console.log('Citação favorita carregada:', this.quoteData);

            // Criar widget de citação após carregar os dados
            this.createQuoteWidget();
        } catch (error) {
            console.error('Erro ao carregar citação favorita:', error);

            // Dados de exemplo para desenvolvimento/teste
            this.quoteData = this.getExampleData();
            this.createQuoteWidget();
        }
    }

    // Dados de exemplo para desenvolvimento/demonstração
    getExampleData() {
        return {
            quote: "A mente que se abre a uma nova ideia jamais voltará ao seu tamanho original.",
            author: "Albert Einstein",
            source: "",
            has_quote: true
        };
    }

    createQuoteWidget() {
        // Verificar se o widget já existe
        if (this.cardElement.querySelector('.quote-widget')) {
            return;
        }

        // Criar o elemento que vai conter a citação favorita
        const widget = document.createElement('div');
        widget.className = 'quote-widget mt-3';

        // Montar o conteúdo do widget baseado nos dados
        widget.innerHTML = this.generateWidgetHTML();

        // Adicionar o widget ao card - logo após as estatísticas ou antes do botão de editar perfil
        const cardBody = this.cardElement.querySelector('.card-body');
        const profileStats = cardBody.querySelector('.profile-stats');
        const achievementsWidget = cardBody.querySelector('.achievements-widget');
        const editButton = cardBody.querySelector('.mt-3'); // O botão de editar perfil

        // Determinar onde inserir o widget
        let insertBefore = editButton;

        if (achievementsWidget) {
            insertBefore = achievementsWidget.nextElementSibling || editButton;
        } else if (profileStats) {
            insertBefore = profileStats.nextElementSibling || editButton;
        }

        if (insertBefore) {
            cardBody.insertBefore(widget, insertBefore);
        } else {
            cardBody.appendChild(widget);
        }

        // Adicionar event listeners
        this.addEventListeners();
    }

    generateWidgetHTML() {
        // Se não houver dados de citação ou se o usuário não tiver uma citação salva
        if (!this.quoteData || !this.quoteData.has_quote) {
            return `
                <div class="quote-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-2">Citação Favorita</h6>
                    <button class="btn btn-sm btn-link p-0 add-quote-btn">
                        <i class="bi bi-plus-circle"></i>
                    </button>
                </div>
                <div class="empty-quote text-center py-2">
                    <small class="text-muted">Adicione sua citação literária favorita</small>
                </div>
            `;
        }

        // Se o usuário tiver uma citação
        const quote = this.quoteData.quote;
        const author = this.quoteData.author;
        const source = this.quoteData.source;

        return `
            <div class="quote-header d-flex justify-content-between align-items-center">
                <h6 class="mb-2">Citação Favorita</h6>
                <div class="quote-actions">
                    <button class="btn btn-sm btn-link p-0 edit-quote-btn">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
            </div>
            <div class="quote-content">
                <blockquote class="blockquote mb-0">
                    <p class="quote-text">"${quote}"</p>
                    <footer class="blockquote-footer">
                        ${author}${source ? ` em <cite title="${source}">${source}</cite>` : ''}
                    </footer>
                </blockquote>
            </div>
        `;
    }

    generateEditFormHTML() {
        return `
            <div class="quote-edit-form">
                <div class="mb-2">
                    <label for="quoteText" class="form-label small">Citação</label>
                    <textarea class="form-control form-control-sm" id="quoteText" rows="2" placeholder="Digite sua citação favorita">${this.quoteData && this.quoteData.quote ? this.quoteData.quote : ''}</textarea>
                </div>
                <div class="mb-2">
                    <label for="quoteAuthor" class="form-label small">Autor</label>
                    <input type="text" class="form-control form-control-sm" id="quoteAuthor" placeholder="Nome do autor" value="${this.quoteData && this.quoteData.author ? this.quoteData.author : ''}">
                </div>
                <div class="mb-2">
                    <label for="quoteSource" class="form-label small">Fonte (opcional)</label>
                    <input type="text" class="form-control form-control-sm" id="quoteSource" placeholder="Livro, poema, etc." value="${this.quoteData && this.quoteData.source ? this.quoteData.source : ''}">
                </div>
                <div class="d-flex justify-content-end gap-2 mt-2">
                    <button class="btn btn-sm btn-outline-secondary cancel-edit-btn">Cancelar</button>
                    <button class="btn btn-sm btn-primary save-quote-btn">Salvar</button>
                </div>
            </div>
        `;
    }

    addEventListeners() {
        // Botão para adicionar citação
        const addButton = this.cardElement.querySelector('.add-quote-btn');
        if (addButton) {
            addButton.addEventListener('click', () => this.showEditForm());
        }

        // Botão para editar citação
        const editButton = this.cardElement.querySelector('.edit-quote-btn');
        if (editButton) {
            editButton.addEventListener('click', () => this.showEditForm());
        }
    }

    showEditForm() {
        this.isEditing = true;

        // Obter o widget de citação
        const quoteWidget = this.cardElement.querySelector('.quote-widget');

        // Salvar o conteúdo atual para possível cancelamento
        this.savedContent = quoteWidget.innerHTML;

        // Substituir o conteúdo pelo formulário de edição
        quoteWidget.innerHTML = this.generateEditFormHTML();

        // Adicionar event listeners para os botões do formulário
        const cancelButton = quoteWidget.querySelector('.cancel-edit-btn');
        const saveButton = quoteWidget.querySelector('.save-quote-btn');

        if (cancelButton) {
            cancelButton.addEventListener('click', () => this.cancelEdit());
        }

        if (saveButton) {
            saveButton.addEventListener('click', () => this.saveQuote());
        }
    }

    cancelEdit() {
        this.isEditing = false;

        // Restaurar o conteúdo original
        const quoteWidget = this.cardElement.querySelector('.quote-widget');
        quoteWidget.innerHTML = this.savedContent;

        // Readicionar event listeners
        this.addEventListeners();
    }

    async saveQuote() {
        try {
            // Obter valores do formulário
            const quoteText = document.getElementById('quoteText').value.trim();
            const quoteAuthor = document.getElementById('quoteAuthor').value.trim();
            const quoteSource = document.getElementById('quoteSource').value.trim();

            // Verificar se a citação e o autor estão preenchidos
            if (!quoteText || !quoteAuthor) {
                this.showError('Por favor, preencha a citação e o autor.');
                return;
            }

            // Preparar dados para envio
            const quoteData = {
                quote: quoteText,
                author: quoteAuthor,
                source: quoteSource
            };

            // Mostrar indicador de carregamento
            this.showLoading();

            // Enviar dados para o servidor
            const response = await fetch('/profile/favorite-quote/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(quoteData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                // Atualizar os dados locais
                this.quoteData = {
                    ...quoteData,
                    has_quote: true
                };

                // Atualizar a interface
                this.isEditing = false;

                // Atualizar o widget
                const quoteWidget = this.cardElement.querySelector('.quote-widget');
                quoteWidget.innerHTML = this.generateWidgetHTML();

                // Readicionar event listeners
                this.addEventListeners();

                // Mostrar mensagem de sucesso
                this.showSuccess('Citação salva com sucesso!');
            } else {
                throw new Error(result.error || 'Erro ao salvar citação');
            }
        } catch (error) {
            console.error('Erro ao salvar citação:', error);
            this.showError('Erro ao salvar citação. Tente novamente mais tarde.');
        } finally {
            // Esconder indicador de carregamento
            this.hideLoading();
        }
    }

    showLoading() {
        // Desabilitar o botão de salvar e mostrar indicador de carregamento
        const saveButton = this.cardElement.querySelector('.save-quote-btn');
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';
        }
    }

    hideLoading() {
        // Reativar o botão de salvar
        const saveButton = this.cardElement.querySelector('.save-quote-btn');
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = 'Salvar';
        }
    }

    showError(message) {
        // Mostrar mensagem de erro
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        // Mostrar mensagem de sucesso
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Criar uma notificação temporária
        const notificationElement = document.createElement('div');
        notificationElement.className = `quote-notification quote-notification-${type}`;
        notificationElement.textContent = message;

        // Adicionar ao documento
        document.body.appendChild(notificationElement);

        // Adicionar classe para animar a entrada
        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 10);

        // Remover após alguns segundos
        setTimeout(() => {
            notificationElement.classList.remove('show');
            setTimeout(() => {
                notificationElement.remove();
            }, 300);
        }, 3000);
    }

    getCsrfToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }

        // Fallback para cookie
        const name = 'csrftoken';
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
}

// Inicializar widget de citação
document.addEventListener('DOMContentLoaded', () => {
    try {
        const profileQuoteWidget = new ProfileCardQuote();
        // Expor para debugging
        window.profileQuoteWidget = profileQuoteWidget;
    } catch (error) {
        console.error('Erro ao inicializar widget de citação:', error);
    }
});