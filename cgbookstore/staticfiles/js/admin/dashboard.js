/**
 * Dashboard Analytics Scripts
 * Responsável pela inicialização e gerenciamento dos gráficos e animações do dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Configurações Globais
     * ======================================================================== */

    // Configuração do tema do gráfico
    const setupChartDefaults = () => {
        Chart.defaults.color = '#e0e0e0';
        Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    };

    /**
     * Gráficos e Visualizações
     * ======================================================================== */

    // Inicialização do gráfico de interações diárias
    const initDailyInteractionsChart = () => {
        const ctx = document.getElementById('dailyInteractionsChart').getContext('2d');

        // Configuração do gradiente
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(13, 110, 253, 0.5)');
        gradient.addColorStop(1, 'rgba(13, 110, 253, 0.1)');

        // Configuração do gráfico
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.chartData.labels,
                datasets: [{
                    label: 'Interações',
                    data: window.chartData.values,
                    borderColor: '#0d6efd',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#0d6efd',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#0d6efd',
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
    };

    /**
     * Animações
     * ======================================================================== */

    // Animação dos números
    const animateNumbers = () => {
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
    };

    /**
     * Componentes de UI
     * ======================================================================== */

    // Inicialização dos tooltips do Bootstrap
    const initTooltips = () => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    };

    /**
     * Inicialização
     * ======================================================================== */
    setupChartDefaults();
    initDailyInteractionsChart();
    animateNumbers();
    initTooltips();
});