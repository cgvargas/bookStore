/**
 * cgbookstore/static/js/profile-stats-modal.js
 *
 * Gerenciador do Modal de Estatísticas Detalhadas
 *
 * Responsável por:
 * - Abrir modal ao clicar no botão "Ver Estatísticas"
 * - Carregar estatísticas detalhadas via API
 * - Renderizar gráficos e métricas
 * - Gerenciar estado do modal
 */

(function() {
    'use strict';

    // Estado do modal
    let statsModal = null;
    let chartInstance = null;
    let isLoadingStats = false;

    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        initializeStatsModal();
        setupStatsButtonHandler();
        console.log('Sistema de modal de estatísticas inicializado');
    });

    /**
     * Inicializa o modal de estatísticas
     */
    function initializeStatsModal() {
        const modalElement = document.getElementById('profileStatsModal');
        if (modalElement) {
            statsModal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true,
                size: 'lg'
            });

            // Eventos do modal
            modalElement.addEventListener('show.bs.modal', function() {
                loadDetailedStats();
            });

            modalElement.addEventListener('shown.bs.modal', function() {
                // Modal totalmente visível - hora de desenhar gráficos
                if (window.statsData) {
                    renderStatsChart(window.statsData);
                }
            });

            modalElement.addEventListener('hidden.bs.modal', function() {
                cleanupModal();
            });

            console.log('Modal de estatísticas configurado');
        } else {
            console.warn('Elemento do modal de estatísticas não encontrado');
        }
    }

    /**
     * Configura o clique no botão "Ver Estatísticas"
     */
    function setupStatsButtonHandler() {
        const statsButton = document.querySelector('.stats-modal-btn');
        if (statsButton) {
            statsButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                openStatsModal();
            });
            console.log('Handler do botão de estatísticas configurado');
        } else {
            console.warn('Botão de estatísticas não encontrado');
        }
    }

    /**
     * Abre o modal de estatísticas
     */
    function openStatsModal() {
        if (!statsModal) {
            showErrorMessage('Modal de estatísticas não disponível');
            return;
        }

        console.log('Abrindo modal de estatísticas...');
        statsModal.show();
    }

    /**
     * Carrega estatísticas detalhadas via API
     */
    async function loadDetailedStats() {
        if (isLoadingStats) return;

        isLoadingStats = true;
        showLoadingState();

        try {
            const response = await fetch('/profile/detailed-stats/');

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            const data = await response.json();
            window.statsData = data; // Armazenar para uso do gráfico
            renderStatsContent(data);

        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
            showErrorState('Não foi possível carregar as estatísticas');
        } finally {
            isLoadingStats = false;
        }
    }

    /**
     * Renderiza o conteúdo das estatísticas
     */
    function renderStatsContent(data) {
        const container = document.querySelector('#profileStatsModal .stats-modal-body');
        if (!container) {
            console.error('Container do modal de estatísticas não encontrado');
            return;
        }

        const statsHtml = `
            <div class="stats-list-container">
                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-books"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Livros Lidos</div>
                        <div class="stat-value">${data.reading_pace?.yearly || 0}</div>
                    </div>
                </div>

                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-file-earmark-text"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Páginas Lidas</div>
                        <div class="stat-value">${formatNumber(data.total_pages_read || 0)}</div>
                    </div>
                </div>

                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-calendar-month"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Média Mensal</div>
                        <div class="stat-value">${data.reading_pace?.monthly || 0} livros</div>
                    </div>
                </div>

                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-calendar-week"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Média Semanal</div>
                        <div class="stat-value">${data.reading_pace?.weekly || 0} livros</div>
                    </div>
                </div>

                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-heart-fill"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Gênero Favorito</div>
                        <div class="stat-value">${data.favorite_genre || 'N/A'}</div>
                    </div>
                </div>

                <div class="stat-card-v2">
                    <div class="stat-icon">
                        <i class="bi bi-graph-up-arrow"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-title">Tendência</div>
                        <div class="stat-value text-success">${data.reading_pace?.trend || 'N/A'}</div>
                    </div>
                </div>
            </div>

            <div class="chart-container-v2">
                <h6 class="mb-3 text-center">Leitura Mensal</h6>
                <div class="stats-chart-container">
                    <canvas id="profileStatsModalChart" width="400" height="300"></canvas>
                </div>
            </div>
        `;

        container.innerHTML = statsHtml;
        console.log('Conteúdo de estatísticas renderizado');
    }

    /**
     * Renderiza o gráfico de estatísticas
     */
    function renderStatsChart(data) {
        const canvas = document.getElementById('profileStatsModalChart');
        if (!canvas) {
            console.warn('Canvas do gráfico não encontrado');
            return;
        }

        // Destruir gráfico anterior se existir
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        const booksData = data.books_by_month || {};
        const years = Object.keys(booksData);
        const currentYear = years.length > 0 ? years[years.length - 1] : new Date().getFullYear().toString();
        const monthlyData = booksData[currentYear] || {};

        const labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
        const chartData = labels.map((_, index) => monthlyData[String(index + 1)] || 0);

        const ctx = canvas.getContext('2d');

        // Criar gradiente
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(13, 110, 253, 0.8)');
        gradient.addColorStop(1, 'rgba(13, 110, 253, 0.2)');

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Livros Lidos',
                    data: chartData,
                    backgroundColor: gradient,
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000,
                    easing: 'easeOutCubic'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: 'var(--cor-texto-secundario)'
                        },
                        grid: {
                            color: 'var(--cor-borda)'
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: 'var(--cor-texto-secundario)'
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'var(--cor-fundo-card)',
                        titleColor: 'var(--cor-texto-primario)',
                        bodyColor: 'var(--cor-texto-primario)',
                        borderColor: 'var(--cor-borda)',
                        borderWidth: 1,
                        callbacks: {
                            title: (tooltipItems) => `${tooltipItems[0].label} ${currentYear}`,
                            label: (context) => `${context.parsed.y} ${context.parsed.y === 1 ? 'livro' : 'livros'}`
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        console.log('Gráfico de estatísticas renderizado');
    }

    /**
     * Mostra estado de carregamento
     */
    function showLoadingState() {
        const container = document.querySelector('#profileStatsModal .stats-modal-body');
        if (container) {
            container.innerHTML = `
                <div class="loading-stats text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <h5 class="text-muted">Carregando Estatísticas</h5>
                    <p class="text-muted">Analisando seus dados de leitura...</p>
                </div>
            `;
        }
    }

    /**
     * Mostra estado de erro
     */
    function showErrorState(message) {
        const container = document.querySelector('#profileStatsModal .stats-modal-body');
        if (container) {
            container.innerHTML = `
                <div class="error-stats text-center py-5">
                    <i class="bi bi-graph-down display-1 text-danger mb-3"></i>
                    <h5 class="text-danger">Erro ao Carregar Estatísticas</h5>
                    <p class="text-muted">${message}</p>
                    <div class="mt-4">
                        <button class="btn btn-outline-primary me-2" onclick="StatsModal.reload()">
                            <i class="bi bi-arrow-clockwise me-2"></i>Tentar Novamente
                        </button>
                        <button class="btn btn-secondary" data-bs-dismiss="modal">
                            Fechar
                        </button>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Limpa o modal ao fechar
     */
    function cleanupModal() {
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        // Limpar dados temporários
        window.statsData = null;

        console.log('Modal de estatísticas limpo');
    }

    /**
     * Formata números grandes
     */
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Mostra mensagem de erro temporária
     */
    function showErrorMessage(message) {
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

        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }

    // Exposição de funções para uso externo
    window.StatsModal = {
        open: openStatsModal,
        reload: loadDetailedStats,
        cleanup: cleanupModal
    };

})();