// static/admin/js/dashboard_modern.js

class DashboardModern {
    constructor() {
        this.init();
        this.bindEvents();
        this.loadStats();
        this.setupAnimations();
    }

    init() {
        // Inicializar componentes do dashboard
        this.setupTooltips();
        this.setupLoadingStates();
        this.setupKeyboardNavigation();

        // Detectar tema do sistema
        this.detectSystemTheme();

        // Configurar observer para animações
        this.setupIntersectionObserver();
    }

    bindEvents() {
        // Event listeners para interações
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('keydown', this.handleKeydown.bind(this));

        // Listeners para botões de ação
        this.setupActionButtons();

        // Listener para mudanças de tema
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.detectSystemTheme.bind(this));
        }
    }

    handleClick(event) {
        const target = event.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        const moduleId = target.dataset.module;

        switch (action) {
            case 'quick-access':
                this.handleQuickAccess(moduleId);
                break;
            case 'refresh-stats':
                this.refreshStats();
                break;
            case 'toggle-module':
                this.toggleModule(moduleId);
                break;
        }
    }

    handleKeydown(event) {
        // Navegação por teclado
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'k':
                    event.preventDefault();
                    this.openQuickSearch();
                    break;
                case 'r':
                    event.preventDefault();
                    this.refreshDashboard();
                    break;
            }
        }
    }

    setupActionButtons() {
        // Adicionar estados de loading aos botões
        const actionButtons = document.querySelectorAll('.action-btn, .btn');

        actionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (this.classList.contains('loading')) {
                    e.preventDefault();
                    return;
                }

                this.classList.add('loading');
                this.dataset.originalText = this.innerHTML;
                this.innerHTML = '<span class="loading-indicator"></span>';

                // Remover loading após 2 segundos (ou quando a página carregar)
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = this.dataset.originalText;
                }, 2000);
            });
        });
    }

    setupTooltips() {
        // Adicionar tooltips dinâmicos
        const elements = document.querySelectorAll('.action-btn, .stat-card, .model-icon');

        elements.forEach(element => {
            if (!element.title && !element.dataset.tooltip) {
                // Adicionar tooltips baseados no contexto
                if (element.classList.contains('add-btn')) {
                    element.dataset.tooltip = 'Adicionar novo item';
                } else if (element.classList.contains('edit-btn')) {
                    element.dataset.tooltip = 'Gerenciar e editar';
                }
            }
        });
    }

    loadStats() {
        // Simular carregamento de estatísticas dinâmicas
        this.animateNumbers();

        // Em produção, fazer chamada AJAX para buscar dados reais
        // this.fetchRealTimeStats();
    }

    animateNumbers() {
        const statNumbers = document.querySelectorAll('.stat-number');

        statNumbers.forEach(element => {
            const finalValue = parseInt(element.textContent.replace(/,/g, ''));
            let currentValue = 0;
            const increment = finalValue / 50; // 50 steps
            const duration = 1500; // 1.5 segundos
            const stepTime = duration / 50;

            element.textContent = '0';

            const timer = setInterval(() => {
                currentValue += increment;
                if (currentValue >= finalValue) {
                    currentValue = finalValue;
                    clearInterval(timer);
                }
                element.textContent = this.formatNumber(Math.floor(currentValue));
            }, stepTime);
        });
    }

    formatNumber(num) {
        return num.toLocaleString('pt-BR');
    }

    fetchRealTimeStats() {
        // Exemplo de chamada AJAX para dados reais
        fetch('/admin/api/dashboard-stats/')
            .then(response => response.json())
            .then(data => {
                this.updateStatCards(data);
            })
            .catch(error => {
                console.warn('Erro ao carregar estatísticas:', error);
            });
    }

    updateStatCards(data) {
        const statCards = document.querySelectorAll('.stat-card');

        statCards.forEach((card, index) => {
            const number = card.querySelector('.stat-number');
            if (number && data[index]) {
                number.textContent = this.formatNumber(data[index].value);
            }
        });
    }

    setupAnimations() {
        // Configurar animações de entrada
        const cards = document.querySelectorAll('.module-card');

        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    setupIntersectionObserver() {
        // Observer para animações quando elementos entram na viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        // Observar todos os cards
        document.querySelectorAll('.module-card').forEach(card => {
            observer.observe(card);
        });
    }

    detectSystemTheme() {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (prefersDark) {
            document.body.classList.add('theme-dark');
            document.body.classList.remove('theme-light');
        } else {
            document.body.classList.add('theme-light');
            document.body.classList.remove('theme-dark');
        }
    }

    setupKeyboardNavigation() {
        // Melhorar navegação por teclado
        const focusableElements = document.querySelectorAll('.action-btn, .btn, a[href]');

        focusableElements.forEach(element => {
            element.addEventListener('focus', function() {
                this.closest('.model-item')?.classList.add('focused');
            });

            element.addEventListener('blur', function() {
                this.closest('.model-item')?.classList.remove('focused');
            });
        });
    }

    handleQuickAccess(moduleId) {
        // Implementar acesso rápido a módulos
        const module = document.querySelector(`[data-module="${moduleId}"]`);
        if (module) {
            module.scrollIntoView({ behavior: 'smooth', block: 'center' });
            module.classList.add('highlighted');

            setTimeout(() => {
                module.classList.remove('highlighted');
            }, 2000);
        }
    }

    openQuickSearch() {
        // Implementar busca rápida (modal ou dropdown)
        console.log('Abrir busca rápida - Ctrl+K');
        // Aqui seria implementado um modal de busca
    }

    refreshDashboard() {
        // Atualizar dados do dashboard
        this.loadStats();

        // Mostrar feedback visual
        const header = document.querySelector('.dashboard-header');
        if (header) {
            header.classList.add('refreshing');
            setTimeout(() => {
                header.classList.remove('refreshing');
            }, 1000);
        }
    }

    refreshStats() {
        // Recarregar apenas as estatísticas
        this.animateNumbers();
        // this.fetchRealTimeStats();
    }

    toggleModule(moduleId) {
        // Expandir/colapsar módulo
        const module = document.querySelector(`[data-module="${moduleId}"]`);
        if (module) {
            module.classList.toggle('collapsed');
        }
    }

    // Utility methods
    showNotification(message, type = 'info') {
        // Mostrar notificação toast
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Performance monitoring
    measurePerformance() {
        if ('performance' in window) {
            const navigation = performance.getEntriesByType('navigation')[0];
            const loadTime = navigation.loadEventEnd - navigation.loadEventStart;

            if (loadTime > 3000) {
                console.warn(`Dashboard carregou em ${loadTime}ms - considere otimizações`);
            }
        }
    }
}

// Estilos CSS para estados dinâmicos
const dynamicStyles = `
<style>
.module-card.highlighted {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(54, 153, 255, 0.3) !important;
}

.model-item.focused {
    background: rgba(54, 153, 255, 0.1) !important;
    border-color: var(--primary-color) !important;
}

.dashboard-header.refreshing {
    opacity: 0.7;
    transform: scale(0.99);
    transition: all 0.3s ease;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 10000;
    transform: translateX(100%);
    transition: transform 0.3s ease;
}

.notification.show {
    transform: translateX(0);
}

.notification-info {
    background: var(--primary-color);
}

.notification-success {
    background: #0BB783;
}

.notification-warning {
    background: var(--warning-color);
}

.notification-error {
    background: var(--danger-color);
}

.action-btn.loading {
    pointer-events: none;
    opacity: 0.7;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading-indicator {
    animation: pulse 1.5s ease-in-out infinite;
}
</style>
`;

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar estilos dinâmicos
    document.head.insertAdjacentHTML('beforeend', dynamicStyles);

    // Inicializar dashboard moderno
    window.dashboardModern = new DashboardModern();

    // Medir performance
    window.dashboardModern.measurePerformance();
});

// Exportar para uso global
window.DashboardModern = DashboardModern;