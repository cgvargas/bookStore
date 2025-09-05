// profile-card-stats.js
// Widget de estatísticas detalhadas para o card de perfil

class ProfileCardStats {
    constructor() {
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.statsData = null;
        this.isExpanded = false;
        this.userTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';

        if (this.cardElement) {
            this.init();
        } else {
            console.error('Card de perfil não encontrado para widget de estatísticas');
        }
    }

    init() {
        this.loadStatsData();
        this.createToggleButton();

        // Observer para detectar mudanças no tema
        this.setupThemeObserver();
    }

    setupThemeObserver() {
        // Observar mudanças de classe no body para detectar alterações de tema
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class') {
                    const newTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
                    if (this.userTheme !== newTheme) {
                        this.userTheme = newTheme;
                        this.updateWidgetColors();
                    }
                }
            });
        });

        observer.observe(document.body, { attributes: true });
    }

    async loadStatsData() {
        try {
            // Carregar dados de estatísticas da API - Usar a API do Django para obter dados reais
            const response = await fetch('/profile/detailed-stats/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.statsData = await response.json();
            console.log('Estatísticas detalhadas carregadas:', this.statsData);

            // Criar widget de estatísticas após carregar os dados
            this.createStatsWidget();
        } catch (error) {
            console.error('Erro ao carregar estatísticas detalhadas:', error);

            // Tentar usar dados da página em vez de fazer fallback para dados fictícios
            this.statsData = this.getPageStatsData() || this.getExampleData();
            this.createStatsWidget();
        }
    }

    // Extrair dados de estatísticas que já existem na página
    getPageStatsData() {
        try {
            const pageStats = {};

            // Ler informações do DOM
            const totalLidosEl = document.querySelector('.stats-info h5:first-child');
            const totalPaginasEl = document.querySelector('.stats-info:nth-child(2) h5');
            const sequenciaEl = document.querySelector('.stats-info:nth-child(3) h5');
            const generoEl = document.querySelector('.stats-info:nth-child(4) h5');

            // Compor estrutura similar à API
            if (totalLidosEl && totalPaginasEl && sequenciaEl) {
                const readingChartCanvas = document.getElementById('readingChart');
                const monthlyData = readingChartCanvas && readingChartCanvas.dataset.books ?
                                    JSON.parse(readingChartCanvas.dataset.books) : {};

                pageStats.reading_pace = {
                    weekly: Math.round((parseInt(totalLidosEl.textContent) || 0) / 52 * 10) / 10,
                    monthly: Math.round((parseInt(totalLidosEl.textContent) || 0) / 12 * 10) / 10,
                    yearly: parseInt(totalLidosEl.textContent) || 0,
                    trend: '+0%'
                };

                pageStats.reading_time = {
                    total_hours: Math.round((parseInt(totalPaginasEl.textContent) || 0) / 30),
                    average_per_book: Math.round(((parseInt(totalPaginasEl.textContent) || 1) /
                                     (parseInt(totalLidosEl.textContent) || 1)) * 0.3 * 10) / 10,
                    average_per_day: Math.round(((parseInt(totalPaginasEl.textContent) || 0) / 365) * 0.3 * 10) / 10
                };

                pageStats.activity_streak = {
                    current: parseInt(sequenciaEl.textContent) || 0,
                    longest: 0,
                    weekly_active_days: 0
                };

                // Compilar gêneros e autores
                pageStats.top_genres = [];
                pageStats.top_authors = [];

                return pageStats;
            }
            return null;
        } catch (error) {
            console.error('Erro ao extrair dados da página:', error);
            return null;
        }
    }

    // Dados de exemplo para desenvolvimento/demonstração com valores mais realistas
    getExampleData() {
        return {
            reading_pace: {
                weekly: 1.2,     // livros por semana
                monthly: 5,      // livros por mês
                yearly: 60,      // projeção anual
                trend: '+5%'     // aumento em relação ao período anterior
            },
            top_genres: [
                { name: 'Fantasia', count: 12, percentage: 30 },
                { name: 'Ficção Científica', count: 8, percentage: 20 },
                { name: 'Romance', count: 6, percentage: 15 }
            ],
            top_authors: [
                { name: 'J.R.R. Tolkien', count: 4 },
                { name: 'Jane Austen', count: 3 },
                { name: 'Neil Gaiman', count: 2 }
            ],
            reading_time: {
                total_hours: 240,
                average_per_book: 4.0,    // horas
                average_per_day: 0.7      // horas
            },
            activity_streak: {
                current: 8,
                longest: 21,
                weekly_active_days: 3
            }
        };
    }

    createToggleButton() {
        // Criar botão para exibir/esconder estatísticas detalhadas
        const cardBody = this.cardElement.querySelector('.card-body');
        const profileStats = cardBody.querySelector('.profile-stats');

        // Verificar se já existe o botão
        if (cardBody.querySelector('.stats-toggle-btn')) {
            return;
        }

        // Criar o botão
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'btn btn-sm btn-outline-secondary stats-toggle-btn mt-2';
        toggleBtn.innerHTML = '<i class="bi bi-bar-chart-line"></i> <span>Ver estatísticas detalhadas</span>';
        toggleBtn.setAttribute('data-bs-toggle', 'tooltip');
        toggleBtn.setAttribute('data-bs-placement', 'bottom');
        toggleBtn.setAttribute('title', 'Expandir estatísticas de leitura');

        // Inserir o botão logo após as estatísticas atuais
        if (profileStats && profileStats.nextElementSibling) {
            cardBody.insertBefore(toggleBtn, profileStats.nextElementSibling);
        } else if (profileStats) {
            cardBody.insertBefore(toggleBtn, profileStats.nextSibling);
        }

        // Adicionar evento de clique
        toggleBtn.addEventListener('click', () => this.toggleStats());

        // Inicializar tooltip
        try {
            new bootstrap.Tooltip(toggleBtn);
        } catch (error) {
            console.error('Erro ao inicializar tooltip:', error);
        }
    }

    createStatsWidget() {
        // Verificar se o widget já existe
        if (this.cardElement.querySelector('.detailed-stats-widget')) {
            return;
        }

        // Criar o elemento que vai conter as estatísticas detalhadas
        const widget = document.createElement('div');
        widget.className = 'detailed-stats-widget mt-3';
        widget.style.display = 'none'; // Inicialmente oculto

        // Aplicar estilo base ao widget
        widget.style.border = '1px solid rgba(0,0,0,0.1)';
        widget.style.borderRadius = '0.5rem';
        widget.style.padding = '1rem';
        widget.style.backgroundColor = 'rgba(255,255,255,0.6)';
        widget.style.backdropFilter = 'blur(5px)';
        widget.style.transition = 'all 0.3s ease';

        // Montar o conteúdo do widget baseado nos dados
        this.populateWidgetContent(widget);

        // Adicionar o widget ao card
        const cardBody = this.cardElement.querySelector('.card-body');
        const toggleBtn = cardBody.querySelector('.stats-toggle-btn');

        if (toggleBtn) {
            cardBody.insertBefore(widget, toggleBtn.nextSibling);
        } else {
            cardBody.appendChild(widget);
        }

        // Aplicar ajustes para tema atual
        this.updateWidgetColors();
    }

    populateWidgetContent(widget) {
        if (!this.statsData) {
            widget.innerHTML = '<div class="text-center text-muted">Nenhum dado disponível</div>';
            return;
        }

        // Estrutura das abas
        let content = `
            <ul class="nav nav-tabs nav-justified" id="statsTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="pace-tab" data-bs-toggle="tab" data-bs-target="#paceStats"
                        type="button" role="tab" aria-controls="paceStats" aria-selected="true">
                        <i class="bi bi-speedometer2"></i>
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="genres-tab" data-bs-toggle="tab" data-bs-target="#genresStats"
                        type="button" role="tab" aria-controls="genresStats" aria-selected="false">
                        <i class="bi bi-tags"></i>
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="authors-tab" data-bs-toggle="tab" data-bs-target="#authorsStats"
                        type="button" role="tab" aria-controls="authorsStats" aria-selected="false">
                        <i class="bi bi-person"></i>
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="time-tab" data-bs-toggle="tab" data-bs-target="#timeStats"
                        type="button" role="tab" aria-controls="timeStats" aria-selected="false">
                        <i class="bi bi-clock"></i>
                    </button>
                </li>
            </ul>
            <div class="tab-content p-2" id="statsTabContent">
                <!-- Conteúdo da aba de Ritmo de Leitura -->
                <div class="tab-pane fade show active" id="paceStats" role="tabpanel" aria-labelledby="pace-tab">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Livros por Semana</small>
                        <span class="fw-bold">${this.statsData.reading_pace.weekly}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Livros por Mês</small>
                        <span class="fw-bold">${this.statsData.reading_pace.monthly}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Projeção Anual</small>
                        <span class="fw-bold">${this.statsData.reading_pace.yearly} livros</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-0">
                        <small class="text-muted">Tendência</small>
                        <span class="fw-bold ${this.statsData.reading_pace.trend.startsWith('+') ? 'text-success' : 'text-danger'}">${this.statsData.reading_pace.trend}</span>
                    </div>
                </div>

                <!-- Conteúdo da aba de Gêneros -->
                <div class="tab-pane fade" id="genresStats" role="tabpanel" aria-labelledby="genres-tab">
                    ${this.generateGenresContent()}
                </div>

                <!-- Conteúdo da aba de Autores -->
                <div class="tab-pane fade" id="authorsStats" role="tabpanel" aria-labelledby="authors-tab">
                    ${this.generateAuthorsContent()}
                </div>

                <!-- Conteúdo da aba de Tempo de Leitura -->
                <div class="tab-pane fade" id="timeStats" role="tabpanel" aria-labelledby="time-tab">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Tempo Total</small>
                        <span class="fw-bold">${this.statsData.reading_time.total_hours} horas</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Média por Livro</small>
                        <span class="fw-bold">${this.statsData.reading_time.average_per_book} horas</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">Média Diária</small>
                        <span class="fw-bold">${this.statsData.reading_time.average_per_day} horas</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-0">
                        <small class="text-muted">Sequência Atual</small>
                        <span class="fw-bold">${this.statsData.activity_streak.current} dias</span>
                    </div>
                </div>
            </div>
        `;

        widget.innerHTML = content;

        // Inicializar as abas após adicionar ao DOM
        setTimeout(() => {
            try {
                const tabEls = widget.querySelectorAll('[data-bs-toggle="tab"]');
                tabEls.forEach(tabEl => {
                    new bootstrap.Tab(tabEl);
                });
            } catch (error) {
                console.error('Erro ao inicializar abas:', error);
            }
        }, 100);
    }

    generateGenresContent() {
        let content = '';

        if (this.statsData.top_genres && this.statsData.top_genres.length > 0) {
            this.statsData.top_genres.forEach((genre, index) => {
                // Array de cores para barras de progresso para garantir contraste
                const progressColors = ['#0d6efd', '#6f42c1', '#fd7e14', '#198754', '#dc3545'];
                const colorIndex = index % progressColors.length;

                content += `
                    <div class="mb-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <small>${genre.name}</small>
                            <small class="text-muted">${genre.count} livros (${genre.percentage}%)</small>
                        </div>
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar" role="progressbar"
                                style="width: ${genre.percentage}%; background-color: ${progressColors[colorIndex]};"
                                aria-valuenow="${genre.percentage}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </div>
                `;
            });
        } else {
            content = '<div class="text-center text-muted">Nenhum gênero registrado</div>';
        }

        return content;
    }

    generateAuthorsContent() {
        let content = '';

        if (this.statsData.top_authors && this.statsData.top_authors.length > 0) {
            content = '<ul class="list-group list-group-flush">';

            this.statsData.top_authors.forEach((author, index) => {
                let medalClass = '';
                let medalIcon = '';

                // Adicionar medalhas para os 3 primeiros
                if (index === 0) {
                    medalClass = 'text-warning';
                    medalIcon = '<i class="bi bi-trophy-fill me-1"></i>';
                } else if (index === 1) {
                    medalClass = 'text-secondary';
                    medalIcon = '<i class="bi bi-trophy-fill me-1"></i>';
                } else if (index === 2) {
                    medalClass = 'text-bronze'; // Precisaremos adicionar esta classe CSS
                    medalIcon = '<i class="bi bi-trophy-fill me-1"></i>';
                }

                content += `
                    <li class="list-group-item bg-transparent px-0 py-1 border-0">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="${medalClass}">${medalIcon}${author.name}</span>
                            <span class="badge bg-primary rounded-pill">${author.count}</span>
                        </div>
                    </li>
                `;
            });

            content += '</ul>';
        } else {
            content = '<div class="text-center text-muted">Nenhum autor registrado</div>';
        }

        return content;
    }

    toggleStats() {
        const widget = this.cardElement.querySelector('.detailed-stats-widget');
        const toggleBtn = this.cardElement.querySelector('.stats-toggle-btn');

        if (!widget || !toggleBtn) return;

        this.isExpanded = !this.isExpanded;

        if (this.isExpanded) {
            widget.style.display = 'block';
            // Adicionar uma pequena animação
            setTimeout(() => {
                widget.style.opacity = '1';
                widget.style.transform = 'translateY(0)';
            }, 10);

            toggleBtn.querySelector('span').textContent = 'Ocultar estatísticas';
            toggleBtn.querySelector('i').className = 'bi bi-chevron-up';
        } else {
            widget.style.opacity = '0';
            widget.style.transform = 'translateY(-10px)';

            setTimeout(() => {
                widget.style.display = 'none';
            }, 300);

            toggleBtn.querySelector('span').textContent = 'Ver estatísticas detalhadas';
            toggleBtn.querySelector('i').className = 'bi bi-bar-chart-line';
        }
    }

    // Atualiza as cores do widget baseado no tema e nas cores do cartão do usuário
    updateWidgetColors() {
        const widget = this.cardElement.querySelector('.detailed-stats-widget');
        if (!widget) return;

        // Obter cores do card do usuário
        const cardStyle = window.getComputedStyle(this.cardElement);
        const cardBgColor = cardStyle.backgroundColor;
        const cardTextColor = cardStyle.color;

        // Verificar se o tema é escuro
        const isDarkTheme = this.userTheme === 'dark' ||
                           document.body.classList.contains('dark-mode');

        // Calcular cores apropriadas baseadas no tema atual e no card
        let widgetBgColor, widgetTextColor, widgetBorderColor;

        if (isDarkTheme) {
            // Tema escuro
            widgetBgColor = this.lightenDarkenColor(this.rgbaToHex(cardBgColor), 10);
            widgetTextColor = this.ensureContrast(cardTextColor, widgetBgColor);
            widgetBorderColor = 'rgba(255, 255, 255, 0.1)';
        } else {
            // Tema claro
            widgetBgColor = this.lightenDarkenColor(this.rgbaToHex(cardBgColor), -5);
            widgetTextColor = this.ensureContrast(cardTextColor, widgetBgColor);
            widgetBorderColor = 'rgba(0, 0, 0, 0.1)';
        }

        // Aplicar cores ao widget
        widget.style.backgroundColor = widgetBgColor;
        widget.style.color = widgetTextColor;
        widget.style.borderColor = widgetBorderColor;

        // Atualizar cores das abas e outros elementos internos
        const tabLinks = widget.querySelectorAll('.nav-link');
        tabLinks.forEach(tab => {
            if (tab.classList.contains('active')) {
                tab.style.color = '#0d6efd'; // Manter azul para aba ativa
            } else {
                tab.style.color = this.lightenDarkenColor(widgetTextColor, isDarkTheme ? 40 : -40);
            }
        });

        // Ajustar cor do texto muted para garantir legibilidade
        const mutedTexts = widget.querySelectorAll('.text-muted');
        const mutedColor = isDarkTheme ? 'rgba(255,255,255,0.6)' : 'rgba(108,117,125,0.8)';

        mutedTexts.forEach(el => {
            el.style.color = mutedColor + ' !important';
        });
    }

    // Função para garantir contraste adequado entre texto e fundo
    ensureContrast(textColor, bgColor) {
        // Converter cores para RGB
        const textRgb = this.hexToRgb(this.rgbaToHex(textColor));
        const bgRgb = this.hexToRgb(this.rgbaToHex(bgColor));

        if (!textRgb || !bgRgb) return textColor;

        // Calcular luminância
        const textLum = this.calculateLuminance(textRgb.r, textRgb.g, textRgb.b);
        const bgLum = this.calculateLuminance(bgRgb.r, bgRgb.g, bgRgb.b);

        // Calcular contraste (WCAG 2.0)
        const contrast = (Math.max(textLum, bgLum) + 0.05) / (Math.min(textLum, bgLum) + 0.05);

        // Se o contraste for menor que 4.5:1, ajustar a cor do texto
        if (contrast < 4.5) {
            // Determinar se o fundo é claro ou escuro
            if (bgLum > 0.5) {
                // Fundo claro, texto deve ser escuro
                return '#000000';
            } else {
                // Fundo escuro, texto deve ser claro
                return '#ffffff';
            }
        }

        return textColor;
    }

    // Calcular luminância de cor RGB
    calculateLuminance(r, g, b) {
        const a = [r, g, b].map(v => {
            v /= 255;
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
    }

    // Converter hex para rgb
    hexToRgb(hex) {
        if (!hex) return null;

        // Expandir shorthand form (e.g. "03F") para full form (e.g. "0033FF")
        const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
        hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    // Converter rgba para hex
    rgbaToHex(rgba) {
        if (!rgba || rgba === 'transparent') return '#ffffff';

        // Extrair valores r, g, b de uma string rgba
        const matches = rgba.match(/rgba?\((\d+), ?(\d+), ?(\d+)(?:, ?(\d+(?:\.\d+)?))?\)/i);
        if (!matches) return rgba; // Retornar original se não for formato válido

        const r = parseInt(matches[1], 10);
        const g = parseInt(matches[2], 10);
        const b = parseInt(matches[3], 10);

        // Converter para hex
        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }

    // Clarear ou escurecer uma cor hex
    lightenDarkenColor(hex, percent) {
        if (!hex) return '#ffffff';

        // Converter para rgb
        const rgb = this.hexToRgb(hex);
        if (!rgb) return hex;

        // Ajustar valores
        rgb.r = Math.min(255, Math.max(0, rgb.r + percent));
        rgb.g = Math.min(255, Math.max(0, rgb.g + percent));
        rgb.b = Math.min(255, Math.max(0, rgb.b + percent));

        // Converter de volta para hex
        return `#${((1 << 24) + (rgb.r << 16) + (rgb.g << 8) + rgb.b).toString(16).slice(1)}`;
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

// Inicializar widget de estatísticas
document.addEventListener('DOMContentLoaded', () => {
    try {
        const profileStatsWidget = new ProfileCardStats();
        // Expor para debugging
        window.profileStatsWidget = profileStatsWidget;

        // Observar mudanças no card do perfil (para quando o usuário customizar as cores)
        const profileCard = document.querySelector('.customizable-card');
        if (profileCard) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'style' && window.profileStatsWidget) {
                        // Atualizar cores do widget quando o card for estilizado
                        setTimeout(() => window.profileStatsWidget.updateWidgetColors(), 300);
                    }
                });
            });

            observer.observe(profileCard, { attributes: true });
        }
    } catch (error) {
        console.error('Erro ao inicializar widget de estatísticas:', error);
    }
});