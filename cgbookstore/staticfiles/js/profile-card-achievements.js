// profile-card-achievements.js
// Componente para exibir conquistas destacadas no card de perfil

class ProfileCardAchievements {
    constructor() {
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.achievementsData = null;
        this.maxAchievements = 3; // Número máximo de conquistas para exibir no card

        if (this.cardElement) {
            this.init();
        } else {
            console.error('Card de perfil não encontrado para widget de conquistas');
        }
    }

    init() {
        this.loadAchievementsData();
    }

    async loadAchievementsData() {
        try {
            // Carregar dados de conquistas da API
            const response = await fetch('/profile/featured-achievements/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.achievementsData = await response.json();
            console.log('Conquistas destacadas carregadas:', this.achievementsData);

            // Criar widget de conquistas após carregar os dados
            this.createAchievementsWidget();
        } catch (error) {
            console.error('Erro ao carregar conquistas destacadas:', error);

            // Dados de exemplo para desenvolvimento/teste
            this.achievementsData = this.getExampleData();
            this.createAchievementsWidget();
        }
    }

    // Dados de exemplo para desenvolvimento/demonstração
    getExampleData() {
        return {
            featured: [
                {
                    id: 1,
                    name: 'Devorador de Livros',
                    description: 'Leu mais de 100 livros',
                    icon: 'bi-book-fill',
                    color: '#6f42c1',
                    achieved_at: '2025-01-15T10:30:00Z',
                    tier: 3,
                    rarity: 'Raro'
                },
                {
                    id: 2,
                    name: 'Maratonista Literário',
                    description: 'Leu 10 livros em um mês',
                    icon: 'bi-lightning-fill',
                    color: '#fd7e14',
                    achieved_at: '2025-03-20T14:45:00Z',
                    tier: 2,
                    rarity: 'Incomum'
                },
                {
                    id: 3,
                    name: 'Explorador de Gêneros',
                    description: 'Leu livros de 15 gêneros diferentes',
                    icon: 'bi-compass-fill',
                    color: '#20c997',
                    achieved_at: '2025-02-05T09:15:00Z',
                    tier: 2,
                    rarity: 'Incomum'
                }
            ],
            total_achieved: 24,
            total_available: 50
        };
    }

    createAchievementsWidget() {
        // Verificar se já existe um widget de conquistas
        if (this.cardElement.querySelector('.achievements-widget')) {
            return;
        }

        // Criar o elemento que vai conter as conquistas destacadas
        const widget = document.createElement('div');
        widget.className = 'achievements-widget mt-3';

        // Montar o conteúdo do widget baseado nos dados
        widget.innerHTML = this.generateWidgetHTML();

        // Adicionar o widget ao card - logo após os stats ou antes do botão de editar perfil
        const cardBody = this.cardElement.querySelector('.card-body');
        const profileStats = cardBody.querySelector('.profile-stats');
        const editButton = cardBody.querySelector('.mt-3'); // O botão de editar perfil

        if (profileStats && profileStats.nextElementSibling) {
            cardBody.insertBefore(widget, profileStats.nextElementSibling);
        } else if (editButton) {
            cardBody.insertBefore(widget, editButton);
        } else {
            cardBody.appendChild(widget);
        }

        // Inicializar os tooltips para as conquistas
        this.initTooltips();

        // Adicionar event listeners
        this.addEventListeners();
    }

    generateWidgetHTML() {
        if (!this.achievementsData || !this.achievementsData.featured || this.achievementsData.featured.length === 0) {
            return `
                <div class="achievements-header">
                    <h6 class="mb-2">Conquistas</h6>
                </div>
                <div class="empty-achievements text-center py-2">
                    <small class="text-muted">Nenhuma conquista desbloqueada</small>
                </div>
            `;
        }

        // Limitar o número de conquistas exibidas
        const featuredAchievements = this.achievementsData.featured.slice(0, this.maxAchievements);

        let html = `
            <div class="achievements-header d-flex justify-content-between align-items-center">
                <h6 class="mb-2">Conquistas</h6>
                <span class="badge bg-secondary rounded-pill">${this.achievementsData.total_achieved}/${this.achievementsData.total_available}</span>
            </div>
            <div class="achievements-list d-flex justify-content-center gap-2 mb-2">
        `;

        // Adicionar cada conquista
        featuredAchievements.forEach(achievement => {
            // Determinar classe de tier
            const tierClass = `tier-${achievement.tier}`;

            html += `
                <div class="achievement-badge ${tierClass}"
                    data-achievement-id="${achievement.id}"
                    data-bs-toggle="tooltip"
                    data-bs-placement="top"
                    title="${achievement.name}: ${achievement.description}">
                    <div class="achievement-icon" style="background-color: ${achievement.color}">
                        <i class="bi ${achievement.icon}"></i>
                    </div>
                    <span class="achievement-name">${achievement.name}</span>
                </div>
            `;
        });

        html += `
            </div>
            <div class="achievements-footer text-center">
                <button class="btn btn-sm btn-link p-0 view-all-achievements">Ver todas</button>
            </div>
        `;

        return html;
    }

    initTooltips() {
        try {
            const tooltipTriggerList = this.cardElement.querySelectorAll('[data-bs-toggle="tooltip"]');
            [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        } catch (error) {
            console.error('Erro ao inicializar tooltips:', error);
        }
    }

    addEventListeners() {
        // Adicionar evento para ver detalhes da conquista
        const achievementBadges = this.cardElement.querySelectorAll('.achievement-badge');
        achievementBadges.forEach(badge => {
            badge.addEventListener('click', (e) => {
                const achievementId = badge.getAttribute('data-achievement-id');
                this.showAchievementDetails(achievementId);
            });
        });

        // Adicionar evento para ver todas as conquistas
        const viewAllButton = this.cardElement.querySelector('.view-all-achievements');
        if (viewAllButton) {
            viewAllButton.addEventListener('click', () => {
                this.viewAllAchievements();
            });
        }
    }

    showAchievementDetails(achievementId) {
        // Encontrar a conquista pelo ID
        const achievement = this.achievementsData.featured.find(ach => ach.id.toString() === achievementId.toString());

        if (!achievement) {
            console.error('Conquista não encontrada:', achievementId);
            return;
        }

        // Verificar se o modal de detalhes existe
        let modalElement = document.getElementById('achievementDetailsModal');

        // Se não existir, criar o modal
        if (!modalElement) {
            modalElement = document.createElement('div');
            modalElement.className = 'modal fade';
            modalElement.id = 'achievementDetailsModal';
            modalElement.setAttribute('tabindex', '-1');
            modalElement.setAttribute('aria-hidden', 'true');

            modalElement.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Detalhes da Conquista</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div class="achievement-modal-icon mb-3">
                                <i></i>
                            </div>
                            <h4 class="achievement-modal-title"></h4>
                            <p class="achievement-modal-description text-muted"></p>
                            <div class="achievement-modal-details mt-4">
                                <div class="row">
                                    <div class="col-6">
                                        <small class="text-muted d-block">Raridade</small>
                                        <span class="achievement-modal-rarity"></span>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted d-block">Conquistado em</small>
                                        <span class="achievement-modal-date"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modalElement);
        }

        // Preencher os dados da conquista no modal
        const iconElement = modalElement.querySelector('.achievement-modal-icon i');
        iconElement.className = `bi ${achievement.icon}`;
        iconElement.parentElement.style.backgroundColor = achievement.color;

        modalElement.querySelector('.achievement-modal-title').textContent = achievement.name;
        modalElement.querySelector('.achievement-modal-description').textContent = achievement.description;
        modalElement.querySelector('.achievement-modal-rarity').textContent = achievement.rarity;

        // Formatar a data
        const achievedDate = new Date(achievement.achieved_at);
        modalElement.querySelector('.achievement-modal-date').textContent = achievedDate.toLocaleDateString('pt-BR');

        // Abrir o modal
        try {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } catch (error) {
            console.error('Erro ao abrir modal de detalhes:', error);
        }
    }

    viewAllAchievements() {
        // Redirecionar para a página de conquistas ou abrir um modal maior
        window.location.href = '/profile/achievements/';
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

// Inicializar widget de conquistas
document.addEventListener('DOMContentLoaded', () => {
    try {
        const profileAchievementsWidget = new ProfileCardAchievements();
        // Expor para debugging
        window.profileAchievementsWidget = profileAchievementsWidget;
    } catch (error) {
        console.error('Erro ao inicializar widget de conquistas:', error);
    }
});