/**
 * Dashboard Analytics Scripts
 * Responsável pela inicialização e gerenciamento dos gráficos e animações do dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verifica se estamos na página de dashboard
    if (!document.querySelector('.dashboard-container')) return;

    /**
     * Configurações Globais
     * ======================================================================== */

    // Configuração do tema do gráfico para combinar com o tema escuro
    if (typeof Chart !== 'undefined') {
        setupChartDefaults();
        initDashboardCharts();
    }

    // Inicialização de componentes da UI
    initDashboardUI();

    /**
     * Configuração do Tema do Chart.js
     * ======================================================================== */
    function setupChartDefaults() {
        Chart.defaults.color = '#e0e0e0';
        Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    }

    /**
     * Inicialização dos Gráficos do Dashboard
     * ======================================================================== */
    function initDashboardCharts() {
        // Inicializar o gráfico de interações diárias se existir
        const dailyInteractionsChart = document.getElementById('dailyInteractionsChart');
        if (dailyInteractionsChart) {
            initDailyInteractionsChart(dailyInteractionsChart);
        }

        // Outros gráficos podem ser inicializados aqui
        // Exemplo: initCategoryDistributionChart();
    }

    /**
     * Gráfico de Interações Diárias
     * ======================================================================== */
    function initDailyInteractionsChart(canvas) {
        const ctx = canvas.getContext('2d');

        // Verificar se temos dados do gráfico no escopo global
        if (!window.chartData) {
            console.error('Dados do gráfico não encontrados. Verifique se window.chartData está definido.');
            return;
        }

        // Configuração do gradiente
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(54, 153, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(54, 153, 255, 0.1)');

        // Configuração do gráfico
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.chartData.labels,
                datasets: [{
                    label: 'Interações',
                    data: window.chartData.values,
                    borderColor: '#3699FF',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3699FF',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#3699FF',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(33, 37, 41, 0.9)',
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: {
                            padding: 10,
                            font: { size: 12, weight: '500' }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            padding: 10,
                            font: { size: 12, weight: '500' }
                        }
                    }
                }
            }
        });
    }

    /**
     * Animações e UI do Dashboard
     * ======================================================================== */
    function initDashboardUI() {
        // Animação dos números
        animateNumbers();

        // Inicialização dos tooltips (Bootstrap se estiver disponível)
        initTooltips();
    }

    /**
     * Animação dos Números
     * ======================================================================== */
    function animateNumbers() {
        const animateValue = (element, start, end, duration) => {
            if (!element || isNaN(end)) return;

            const range = end - start;
            const increment = range / (duration / 16);
            let current = start;
            const decimals = element.dataset.decimals ? parseInt(element.dataset.decimals) : 0;

            const timer = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                    clearInterval(timer);
                    current = end;
                }
                element.textContent = Number(current).toLocaleString('pt-BR', {
                    minimumFractionDigits: decimals,
                    maximumFractionDigits: decimals
                });
            }, 16);
        };

        document.querySelectorAll('[data-animate-number]').forEach(element => {
            const value = parseFloat(element.dataset.animateNumber);
            if (!isNaN(value)) {
                animateValue(element, 0, value, 1000);
            }
        });
    }

    /**
     * Inicialização de Tooltips
     * ======================================================================== */
    function initTooltips() {
        // Verificar se o Bootstrap está disponível
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
        // Implementação alternativa de tooltips caso o Bootstrap não esteja disponível
        else {
            console.log('Bootstrap não detectado. Tooltips não foram inicializados.');
        }
    }
});