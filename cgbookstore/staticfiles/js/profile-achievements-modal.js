/**
 * cgbookstore/static/js/profile-achievements-modal.js
 *
 * Gerenciador do Modal de Conquistas do Usuário
 *
 * Responsável por:
 * - Abrir modal ao clicar na estatística "Pontos"
 * - Carregar conquistas via API
 * - Renderizar conquistas desbloqueadas e em progresso
 * - Gerenciar interações do modal
 */

(function() {
    'use strict';

    // Estado do modal
    let achievementsModal = null;
    let isLoadingAchievements = false;

    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        initializeAchievementsModal();
        setupPointsClickHandler();
        console.log('Sistema de modal de conquistas inicializado');
    });

    /**
     * Inicializa o modal de conquistas
     */
    function initializeAchievementsModal() {
        const modalElement = document.getElementById('userAchievementsModal');
        if (modalElement) {
            achievementsModal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true
            });

            // Evento para carregar dados quando modal abrir
            modalElement.addEventListener('show.bs.modal', function() {
                loadUserAchievements();
            });

            console.log('Modal de conquistas configurado');
        } else {
            console.warn('Elemento do modal de conquistas não encontrado');
        }
    }

    /**
     * Configura o clique na estatística de "Pontos"
     */
    function setupPointsClickHandler() {
        // Procurar pela estatística de pontos no card de perfil
        const pointsStats = document.querySelectorAll('.stat-item-v2');

        pointsStats.forEach(statItem => {
            const statLabel = statItem.querySelector('.stat-label');
            if (statLabel && statLabel.textContent.toLowerCase().includes('pontos')) {
                statItem.style.cursor = 'pointer';
                statItem.title = 'Clique para ver suas conquistas';

                statItem.addEventListener('click', function() {
                    openAchievementsModal();
                });

                // Adicionar classe para hover effect
                statItem.classList.add('clickable-stat');
                console.log('Handler de clique configurado para estatística de pontos');
            }
        });
    }

    /**
     * Abre o modal de conquistas
     */
    function openAchievementsModal() {
        if (!achievementsModal) {
            showErrorMessage('Modal de conquistas não disponível');
            return;
        }

        console.log('Abrindo modal de conquistas...');
        achievementsModal.show();
    }

    /**
     * Carrega as conquistas do usuário via API
     */
    async function loadUserAchievements() {
        if (isLoadingAchievements) return;

        isLoadingAchievements = true;
        showLoadingState();

        try {
            const response = await fetch('/profile/api/achievements/');

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            const data = await response.json();
            renderAchievements(data);

        } catch (error) {
            console.error('Erro ao carregar conquistas:', error);
            showErrorState('Não foi possível carregar as conquistas');
        } finally {
            isLoadingAchievements = false;
        }
    }

    /**
     * Renderiza as conquistas no modal
     */
    function renderAchievements(data) {
        const container = document.querySelector('#userAchievementsModal .user-achievements-modal-body');
        if (!container) {
            console.error('Container do modal de conquistas não encontrado');
            return;
        }

        const unlockedAchievements = data.unlocked || [];
        const inProgressAchievements = data.in_progress || [];

        let html = '';

        // Seção de Conquistas Desbloqueadas
        if (unlockedAchievements.length > 0) {
            html += `
                <div class="achievements-section">
                    <h6 class="achievements-section-title">
                        <i class="bi bi-trophy-fill text-warning me-2"></i>
                        Conquistas Desbloqueadas (${unlockedAchievements.length})
                    </h6>
                    <div class="achievements-grid-v2">
                        ${unlockedAchievements.map(achievement => renderAchievementCard(achievement, 'unlocked')).join('')}
                    </div>
                </div>
            `;
        }

        // Seção de Conquistas em Progresso
        if (inProgressAchievements.length > 0) {
            html += `
                <div class="achievements-section mt-4">
                    <h6 class="achievements-section-title">
                        <i class="bi bi-clock-history text-info me-2"></i>
                        Em Progresso (${inProgressAchievements.length})
                    </h6>
                    <div class="achievements-grid-v2">
                        ${inProgressAchievements.map(achievement => renderAchievementCard(achievement, 'in_progress')).join('')}
                    </div>
                </div>
            `;
        }

        // Estado vazio
        if (unlockedAchievements.length === 0 && inProgressAchievements.length === 0) {
            html = `
                <div class="empty-achievements text-center py-5">
                    <i class="bi bi-award display-1 text-muted mb-3"></i>
                    <h5 class="text-muted">Nenhuma conquista encontrada</h5>
                    <p class="text-muted">Continue lendo para desbloquear suas primeiras conquistas!</p>
                </div>
            `;
        }

        container.innerHTML = html;
        console.log('Conquistas renderizadas:', unlockedAchievements.length + inProgressAchievements.length);
    }

    /**
     * Renderiza um card individual de conquista
     */
    function renderAchievementCard(achievement, status) {
        const isUnlocked = status === 'unlocked';
        const tierClass = getTierClass(achievement.tier);
        const achievedDate = achievement.achieved_at ? new Date(achievement.achieved_at).toLocaleDateString('pt-BR') : '';

        return `
            <div class="achievement-card-v2 ${!isUnlocked ? 'in-progress' : ''}" data-achievement="${achievement.name}">
                <div class="ach-icon ${tierClass}">
                    <i class="${achievement.icon}"></i>
                </div>
                <div class="ach-info">
                    <div class="ach-title">${achievement.name}</div>
                    <div class="ach-description">${achievement.description}</div>
                    ${isUnlocked && achievedDate ? `<div class="ach-date">Conquistado em ${achievedDate}</div>` : ''}
                    ${!isUnlocked ? '<div class="ach-progress">Em andamento...</div>' : ''}
                </div>
            </div>
        `;
    }

    /**
     * Retorna a classe CSS para o tier da conquista
     */
    function getTierClass(tier) {
        const tierMap = {
            'Bronze': 'tier-bronze',
            'Silver': 'tier-silver',
            'Gold': 'tier-gold',
            'Platinum': 'tier-platinum'
        };
        return tierMap[tier] || 'tier-bronze';
    }

    /**
     * Mostra estado de carregamento
     */
    function showLoadingState() {
        const container = document.querySelector('#achievementsModal .achievements-modal-body');
        if (container) {
            container.innerHTML = `
                <div class="loading-achievements text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="text-muted">Carregando suas conquistas...</p>
                </div>
            `;
        }
    }

    /**
     * Mostra estado de erro
     */
    function showErrorState(message) {
        const container = document.querySelector('#achievementsModal .achievements-modal-body');
        if (container) {
            container.innerHTML = `
                <div class="error-achievements text-center py-5">
                    <i class="bi bi-exclamation-triangle display-1 text-danger mb-3"></i>
                    <h5 class="text-danger">Erro ao Carregar</h5>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-outline-primary" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-2"></i>Tentar Novamente
                    </button>
                </div>
            `;
        }
    }

    /**
     * Mostra mensagem de erro temporária
     */
    function showErrorMessage(message) {
        // Criar toast de erro
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.style.zIndex = '1060';

        toast.innerHTML = `
            <div class="toast-header bg-danger text-white">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong class="me-auto">Erro</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        document.body.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();

        // Remover elemento após ocultar
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }

    // Exposição de funções para uso externo
    window.AchievementsModal = {
        open: openAchievementsModal,
        reload: loadUserAchievements
    };

})();