// cgbookstore/static/js/profile-stats.js

/**
 * Gerenciador de estatísticas e conquistas do perfil do usuário.
 *
 * Responsável por:
 * - Renderizar gráficos de estatísticas
 * - Animar e gerenciar interações das conquistas
 * - Mostrar detalhes de conquistas
 */

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando gerenciador de estatísticas e conquistas...');

    // Inicializar o gráfico de leitura
    initReadingChart();

    // Inicializar animações das conquistas
    initAchievementAnimations();

    // Configurar tooltips e popovers
    setupTooltips();
});

/**
 * Inicializa um gráfico de leitura mensal em um canvas específico.
 * @param {string} canvasId - O ID do elemento <canvas> onde o gráfico será renderizado.
 */
function initReadingChart(canvasId = 'readingChart') { // Valor padrão para compatibilidade
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        return; // Sai silenciosamente se o canvas não for encontrado
    }

    const booksDataRaw = canvas.getAttribute('data-books') || '{}';
    let booksData;
    try {
        const parsedData = JSON.parse(booksDataRaw);
        booksData = parsedData.books_by_month || parsedData;
    } catch (e) {
        console.error('Erro ao parsear dados do gráfico:', e);
        booksData = {};
    }

    const years = Object.keys(booksData);
    const currentYear = years.length > 0 ? years[years.length - 1] : new Date().getFullYear().toString();
    const monthlyData = booksData[currentYear] || {};

    const labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    const data = labels.map((_, index) => monthlyData[String(index + 1)] || 0);

    const gradientColors = createGradient(canvas, [
        { offset: 0, color: 'rgba(13, 110, 253, 0.8)' },
        { offset: 1, color: 'rgba(13, 110, 253, 0.2)' }
    ]);

    // Destrói uma instância de gráfico anterior se ela existir no mesmo canvas
    if (canvas.chartInstance) {
        canvas.chartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    canvas.chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Livros Lidos',
                data: data,
                backgroundColor: gradientColors,
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => `${tooltipItems[0].label} ${currentYear}`,
                        label: (context) => `${context.parsed.y} ${context.parsed.y === 1 ? 'livro' : 'livros'}`
                    }
                }
            }
        }
    });
    console.log(`Gráfico de leitura inicializado com sucesso em #${canvasId}`);
}

/**
 * Cria um gradiente para uso no gráfico.
 *
 * @param {HTMLCanvasElement} canvas - Elemento canvas do gráfico
 * @param {Array} colorStops - Array de objetos com offset e color
 * @returns {CanvasGradient} Gradiente configurado
 */
function createGradient(canvas, colorStops) {
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);

    colorStops.forEach(stop => {
        gradient.addColorStop(stop.offset, stop.color);
    });

    return gradient;
}

/**
 * Inicializa animações e interações das conquistas.
 */
function initAchievementAnimations() {
    const achievementCards = document.querySelectorAll('.achievement-card');

    if (achievementCards.length === 0) {
        console.log('Nenhuma conquista encontrada para animar');
        return;
    }

    console.log(`Inicializando animações para ${achievementCards.length} conquistas`);

    // Configurar observador de interseção para animar entrada das conquistas
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Adicionar atraso baseado no índice para efeito cascata
                const delay = Array.from(achievementCards).indexOf(entry.target) * 100;
                setTimeout(() => {
                    entry.target.classList.add('animated-in');
                }, delay);

                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    });

    // Observar todos os cards de conquistas
    achievementCards.forEach(card => {
        observer.observe(card);

        // Adicionar evento de clique para mostrar detalhes
        card.addEventListener('click', function() {
            const achievementId = this.getAttribute('data-achievement-id');
            if (achievementId) {
                showAchievementDetails(achievementId);
            }
        });
    });
}

/**
 * Configura tooltips nos elementos da página.
 */
function setupTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl, {
        delay: { show: 300, hide: 100 }
    }));

    console.log('Tooltips configurados');
}

/**
 * Mostra detalhes de uma conquista específica.
 *
 * @param {string} achievementId - ID da conquista
 */
function showAchievementDetails(achievementId) {
    console.log(`Mostrando detalhes da conquista ID: ${achievementId}`);

    // Verificar se o modal existe
    const modalElement = document.getElementById('achievementDetailsModal');
    if (!modalElement) {
        console.error('Modal para detalhes de conquistas não encontrado');
        return;
    }

    // Inicializar modal Bootstrap
    const modal = new bootstrap.Modal(modalElement);

    // Buscar detalhes da conquista via API
    fetch(`/profile/achievement/${achievementId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Preencher conteúdo do modal
            document.getElementById('achievementModalTitle').textContent = data.name;
            document.getElementById('achievementModalDescription').textContent = data.description;
            document.getElementById('achievementModalIcon').className = `bi ${data.icon}`;

            // Formatar data
            const date = new Date(data.achieved_at);
            document.getElementById('achievementModalDate').textContent = date.toLocaleDateString('pt-BR');

            // Mostrar o modal
            modal.show();
        })
        .catch(error => {
            console.error('Erro ao buscar detalhes da conquista:', error);
            // Mostrar uma mensagem de erro
            showErrorNotification('Não foi possível carregar os detalhes da conquista');
        });
}

/**
 * Mostra uma notificação de erro temporária.
 *
 * @param {string} message - Mensagem de erro
 */
function showErrorNotification(message) {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = 'achievement-notification error';
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="bi bi-exclamation-circle"></i>
        </div>
        <div class="notification-content">
            <p>${message}</p>
        </div>
    `;

    // Adicionar ao DOM
    document.body.appendChild(notification);

    // Animar entrada
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remover após alguns segundos
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 4000);
}