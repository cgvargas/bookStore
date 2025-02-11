/**
 * Metrics Analytics Scripts
 * Responsável pela inicialização e gerenciamento dos gráficos de métricas detalhadas
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Heatmap de Atividades
     * ======================================================================== */

    // Inicialização do gráfico de calor para horários
    const initHeatmap = () => {
        // Constantes e configurações
        const periods = ['Madrugada', 'Manhã', 'Tarde', 'Noite'];
        const colors = {
            'low': 'rgba(13, 110, 253, 0.2)',
            'medium': 'rgba(13, 110, 253, 0.4)',
            'high': 'rgba(13, 110, 253, 0.6)',
            'very-high': 'rgba(13, 110, 253, 0.8)'
        };

        // Seleção e validação do container
        const heatmapContainer = document.querySelector('.heatmap-grid');
        if (!heatmapContainer) return;

        // Limpa o container
        heatmapContainer.innerHTML = '';

        /**
         * Geração do grid do heatmap
         * Cria uma coluna para cada período do dia
         */
        periods.forEach(period => {
            // Filtra dados por período
            const periodData = window.activityData.filter(data => {
                const hour = data.hour;
                if (period === 'Madrugada') return hour >= 0 && hour < 6;
                if (period === 'Manhã') return hour >= 6 && hour < 12;
                if (period === 'Tarde') return hour >= 12 && hour < 18;
                return hour >= 18 && hour < 24;
            });

            // Cria elemento de período
            const periodElement = document.createElement('div');
            periodElement.className = 'period-column';
            periodElement.innerHTML = `
                <h6 class="period-title">${period}</h6>
                <div class="period-cells"></div>
            `;

            // Adiciona células de horário
            const cellsContainer = periodElement.querySelector('.period-cells');
            periodData.forEach(data => {
                const cell = document.createElement('div');
                cell.className = `heatmap-cell activity-${data.intensity}`;
                cell.setAttribute('data-bs-toggle', 'tooltip');
                cell.setAttribute('data-bs-title', `${data.hour}:00 - ${data.count} interações`);
                cell.innerHTML = `
                    <span class="time">${String(data.hour).padStart(2, '0')}:00</span>
                    <span class="count">${data.count}</span>
                `;
                cellsContainer.appendChild(cell);
            });

            heatmapContainer.appendChild(periodElement);
        });

        // Inicializa tooltips do Bootstrap
        initTooltips();
    };

    /**
     * Gráfico de Atividade Semanal
     * ======================================================================== */

    // Inicialização do gráfico de atividade semanal
    const initWeeklyChart = () => {
        // Validação do elemento e dados
        const ctx = document.getElementById('weeklyActivityChart');
        if (!ctx || !window.weeklyData?.labels || !window.weeklyData?.values) {
            console.error('Elemento ou dados do gráfico semanal não encontrados');
            return;
        }

        // Configuração do gráfico
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: window.weeklyData.labels,
                datasets: [{
                    label: 'Interações',
                    data: window.weeklyData.values,
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#e0e0e0' }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 12
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: {
                            color: '#e0e0e0',
                            font: { size: 12 }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#e0e0e0',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    };

    /**
     * DataTables Inicialização
     * ======================================================================== */

    // Configuração das tabelas com DataTables
    const initTables = () => {
        if (!$.fn.DataTable) return;

        $('.table-datatable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Portuguese-Brasil.json'
            },
            pageLength: 10,
            responsive: true,
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            buttons: ['copy', 'excel', 'pdf'],
            order: [[0, 'desc']],
            initComplete: function () {
                $('.dataTables_wrapper').addClass('pb-3');
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
    initHeatmap();
    initWeeklyChart();
    initTables();
});