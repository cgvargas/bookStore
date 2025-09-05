// profile-card-reading-status.js
// Componente para exibir o status de leitura atual no card de perfil - VERSÃO V2

class ProfileCardReadingStatus {
    constructor() {
        // Alvo: O novo container dedicado
        this.containerElement = document.getElementById('readingStatusWidgetContainer');
        this.statusData = null;

        if (this.containerElement) {
            this.init();
        }
    }

    init() {
        this.loadStatusData();
    }

    async loadStatusData() {
        try {
            const response = await fetch('/profile/current-reading/');
            this.statusData = await response.json();

            // O endpoint retorna 404 se não houver livro, então tratamos o erro.
            if (response.status === 404) {
                this.statusData = { has_current_book: false };
            } else if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.createStatusWidget();
        } catch (error) {
            console.error('Erro ao carregar status de leitura atual:', error);
            this.statusData = { has_current_book: false };
            this.createStatusWidget();
        }
    }

    createStatusWidget() {
        if (!this.containerElement) return;
        this.containerElement.innerHTML = this.generateWidgetHTML();

        // Adicionar event listeners para os botões internos
        this.addEventListeners();
    }

    generateWidgetHTML() {
        if (!this.statusData || this.statusData.error || !this.statusData.title) {
            return `
                <div class="reading-status-widget-v2 empty">
                    <h6 class="reading-status-title">Lendo Atualmente</h6>
                    <p class="text-muted small">Nenhum livro sendo lido no momento.</p>
                </div>
            `;
        }

        const { title, author, coverUrl, progress, totalPages } = this.statusData;
        const progressPercent = totalPages > 0 ? Math.round((progress / totalPages) * 100) : 0;

        return `
            <div class="reading-status-widget-v2">
                <h6 class="reading-status-title">Lendo Atualmente</h6>
                <a href="/profile/lendo/" class="current-book-link">
                    <div class="current-book-info">
                        <img src="${coverUrl}" alt="Capa de ${title}" class="current-book-cover">
                        <div class="current-book-details">
                            <p class="current-book-title" title="${title}">${title}</p>
                            <p class="current-book-author text-muted">${author}</p>
                        </div>
                    </div>
                    <div class="current-book-progress">
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar" role="progressbar" style="width: ${progressPercent}%;" aria-valuenow="${progressPercent}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                        <span class="progress-text text-muted">${progressPercent}%</span>
                    </div>
                </a>
            </div>
        `;
    }

    addEventListeners() {
        // Eventos futuros, como botão de atualizar progresso rápido, podem ser adicionados aqui.
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('readingStatusWidgetContainer')) {
        new ProfileCardReadingStatus();
    }
});