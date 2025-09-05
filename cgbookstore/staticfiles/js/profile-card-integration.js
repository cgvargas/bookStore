// profile-card-integration.js
// Integração de todos os componentes melhorados do card de perfil - SEM LOOP INFINITO

class ProfileCardIntegration {
    constructor() {
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.componentsLoaded = {
            stats: false,
            achievements: false,
            themes: false,
            quote: false,
            readingStatus: false
        };
        this.components = {};
        this.isReorganizing = false; // Flag para prevenir loops

        if (this.cardElement) {
            console.log('Iniciando integração dos componentes do card de perfil');
            this.init();
        } else {
            console.error('Card de perfil não encontrado para integração');
        }
    }

    init() {
        // Adicionar todos os estilos CSS necessários
        this.loadStyles();

        // Verificar dependências
        this.checkDependencies();

        // Garantir que o botão de customização esteja visível
        this.ensureCustomizeButtonVisible();

        // Inicializar componentes
        this.initializeComponents();

        // Observar modificações do DOM para reordenar widgets quando necessário
        // REMOVIDO TEMPORARIAMENTE PARA EVITAR LOOP
        // this.observeCardChanges();
    }

    loadStyles() {
        // Verificar se os estilos já estão carregados
        const stylesLoaded = {
            'profile-card-stats-styles': document.getElementById('profile-card-stats-styles'),
            'profile-card-achievements-styles': document.getElementById('profile-card-achievements-styles'),
            'profile-card-themes-styles': document.getElementById('profile-card-themes-styles'),
            'profile-card-quote-styles': document.getElementById('profile-card-quote-styles'),
            'profile-card-reading-status-styles': document.getElementById('profile-card-reading-status-styles')
        };

        // Lista de estilos a carregar
        const stylesToLoad = [
            { id: 'profile-card-stats-styles', href: '/static/css/profile-card-stats.css' },
            { id: 'profile-card-achievements-styles', href: '/static/css/profile-card-achievements.css' },
            { id: 'profile-card-themes-styles', href: '/static/css/profile-card-themes.css' },
            { id: 'profile-card-quote-styles', href: '/static/css/profile-card-quote.css' },
            { id: 'profile-card-reading-status-styles', href: '/static/css/profile-card-reading-status.css' }
        ];

        // Carregar estilos que ainda não estão presentes
        stylesToLoad.forEach(styleInfo => {
            if (!stylesLoaded[styleInfo.id]) {
                const linkElement = document.createElement('link');
                linkElement.id = styleInfo.id;
                linkElement.rel = 'stylesheet';
                linkElement.href = styleInfo.href;
                document.head.appendChild(linkElement);
                console.log(`Estilos carregados: ${styleInfo.id}`);
            }
        });
    }

    checkDependencies() {
        // Verificar se as dependências estão disponíveis
        const dependencies = {
            bootstrap: typeof bootstrap !== 'undefined',
            jQuery: typeof jQuery !== 'undefined'
        };

        // Reportar dependências faltantes
        const missingDependencies = Object.entries(dependencies)
            .filter(([_, available]) => !available)
            .map(([name]) => name);

        if (missingDependencies.length > 0) {
            console.warn(`Dependências faltantes para componentes do card de perfil: ${missingDependencies.join(', ')}`);
        }
    }

    initializeComponents() {
        // Detectar e integrar componentes existentes
        this.detectLoadedComponents();

        // Inicializar novos componentes conforme necessário
        this.initializeStats();
        this.initializeAchievements();
        this.initializeThemes();
        this.initializeQuote();
        this.initializeReadingStatus();

        // Verificar a ordem dos componentes após todos estarem inicializados
        // ÚNICA chamada controlada para organizar
        setTimeout(() => {
            this.organizeComponentsOrderOnce();
        }, 1000);
    }

    detectLoadedComponents() {
        // Verificar componentes já carregados
        if (window.profileStatsWidget) {
            this.componentsLoaded.stats = true;
            this.components.stats = window.profileStatsWidget;
            console.log('Componente de estatísticas detectado');
        }

        if (window.profileAchievementsWidget) {
            this.componentsLoaded.achievements = true;
            this.components.achievements = window.profileAchievementsWidget;
            console.log('Componente de conquistas detectado');
        }

        if (window.profileThemes) {
            this.componentsLoaded.themes = true;
            this.components.themes = window.profileThemes;
            console.log('Componente de temas detectado');
        }

        if (window.profileQuoteWidget) {
            this.componentsLoaded.quote = true;
            this.components.quote = window.profileQuoteWidget;
            console.log('Componente de citação detectado');
        }

        if (window.profileReadingStatus) {
            this.componentsLoaded.readingStatus = true;
            this.components.readingStatus = window.profileReadingStatus;
            console.log('Componente de status de leitura detectado');
        }
    }

    initializeStats() {
        if (!this.componentsLoaded.stats) {
            try {
                // Verificar se o script está carregado
                if (typeof ProfileCardStats === 'undefined') {
                    // Se não estiver carregado, injetar o script
                    this.loadScript('/static/js/profile-card-stats.js', () => {
                        // Callback após o carregamento do script
                        this.componentsLoaded.stats = true;
                        this.components.stats = window.profileStatsWidget;
                        console.log('Componente de estatísticas inicializado');
                    });
                } else {
                    // Se o script estiver carregado, mas o componente não foi inicializado
                    window.profileStatsWidget = new ProfileCardStats();
                    this.componentsLoaded.stats = true;
                    this.components.stats = window.profileStatsWidget;
                    console.log('Componente de estatísticas inicializado');
                }
            } catch (error) {
                console.error('Erro ao inicializar componente de estatísticas:', error);
            }
        }
    }

    initializeAchievements() {
        if (!this.componentsLoaded.achievements) {
            try {
                // Verificar se o script está carregado
                if (typeof ProfileCardAchievements === 'undefined') {
                    // Se não estiver carregado, injetar o script
                    this.loadScript('/static/js/profile-card-achievements.js', () => {
                        // Callback após o carregamento do script
                        this.componentsLoaded.achievements = true;
                        this.components.achievements = window.profileAchievementsWidget;
                        console.log('Componente de conquistas inicializado');
                    });
                } else {
                    // Se o script estiver carregado, mas o componente não foi inicializado
                    window.profileAchievementsWidget = new ProfileCardAchievements();
                    this.componentsLoaded.achievements = true;
                    this.components.achievements = window.profileAchievementsWidget;
                    console.log('Componente de conquistas inicializado');
                }
            } catch (error) {
                console.error('Erro ao inicializar componente de conquistas:', error);
            }
        }
    }

    initializeThemes() {
        if (!this.componentsLoaded.themes) {
            try {
                // Verificar se o script está carregado
                if (typeof ProfileCardThemes === 'undefined') {
                    // Se não estiver carregado, injetar o script
                    this.loadScript('/static/js/profile-card-themes.js', () => {
                        // Callback após o carregamento do script
                        this.componentsLoaded.themes = true;
                        this.components.themes = window.profileThemes;
                        console.log('Componente de temas inicializado');
                    });
                } else {
                    // Se o script estiver carregado, mas o componente não foi inicializado
                    window.profileThemes = new ProfileCardThemes();
                    this.componentsLoaded.themes = true;
                    this.components.themes = window.profileThemes;
                    console.log('Componente de temas inicializado');
                }
            } catch (error) {
                console.error('Erro ao inicializar componente de temas:', error);
            }
        }
    }

    initializeQuote() {
        if (!this.componentsLoaded.quote) {
            try {
                // Verificar se o script está carregado
                if (typeof ProfileCardQuote === 'undefined') {
                    // Se não estiver carregado, injetar o script
                    this.loadScript('/static/js/profile-card-quote.js', () => {
                        // Callback após o carregamento do script
                        this.componentsLoaded.quote = true;
                        this.components.quote = window.profileQuoteWidget;
                        console.log('Componente de citação inicializado');
                    });
                } else {
                    // Se o script estiver carregado, mas o componente não foi inicializado
                    window.profileQuoteWidget = new ProfileCardQuote();
                    this.componentsLoaded.quote = true;
                    this.components.quote = window.profileQuoteWidget;
                    console.log('Componente de citação inicializado');
                }
            } catch (error) {
                console.error('Erro ao inicializar componente de citação:', error);
            }
        }
    }

    initializeReadingStatus() {
        if (!this.componentsLoaded.readingStatus) {
            try {
                // Verificar se o script está carregado
                if (typeof ProfileCardReadingStatus === 'undefined') {
                    // Se não estiver carregado, injetar o script
                    this.loadScript('/static/js/profile-card-reading-status.js', () => {
                        // Callback após o carregamento do script
                        this.componentsLoaded.readingStatus = true;
                        this.components.readingStatus = window.profileReadingStatus;
                        console.log('Componente de status de leitura inicializado');
                    });
                } else {
                    // Se o script estiver carregado, mas o componente não foi inicializado
                    window.profileReadingStatus = new ProfileCardReadingStatus();
                    this.componentsLoaded.readingStatus = true;
                    this.components.readingStatus = window.profileReadingStatus;
                    console.log('Componente de status de leitura inicializado');
                }
            } catch (error) {
                console.error('Erro ao inicializar componente de status de leitura:', error);
            }
        }
    }

    loadScript(src, callback) {
        const script = document.createElement('script');
        script.src = src;
        script.onload = callback;
        script.onerror = (error) => {
            console.error(`Erro ao carregar script ${src}:`, error);
        };
        document.head.appendChild(script);
    }

    // VERSÃO SEM LOOP - executa apenas uma vez
    organizeComponentsOrderOnce() {
        if (this.isReorganizing) {
            console.log('Reorganização já em andamento, pulando...');
            return;
        }

        this.isReorganizing = true;

        try {
            const cardBody = this.cardElement.querySelector('.card-body');
            if (!cardBody) {
                console.warn('Card body não encontrado');
                return;
            }

            // Elementos de referência
            const profileStats = cardBody.querySelector('.profile-stats');
            const detailedStatsWidget = cardBody.querySelector('.detailed-stats-widget');
            const achievementsWidget = cardBody.querySelector('.achievements-widget');
            const quoteWidget = cardBody.querySelector('.quote-widget');
            const readingStatusWidget = cardBody.querySelector('.reading-status-widget');
            const themeSelector = cardBody.querySelector('.theme-selector');
            const editButton = cardBody.querySelector('.btn-outline-primary');

            console.log('Organizando componentes do card de perfil (execução única)');

            // Ordem desejada: profile-stats > detailed-stats > achievements > quote > reading-status > theme-selector > edit-button

            if (profileStats && detailedStatsWidget) {
                // Mover detailed-stats após profile-stats
                cardBody.insertBefore(detailedStatsWidget, profileStats.nextSibling);
            }

            if (detailedStatsWidget && achievementsWidget) {
                // Mover achievements após detailed-stats
                cardBody.insertBefore(achievementsWidget, detailedStatsWidget.nextSibling);
            } else if (profileStats && achievementsWidget) {
                // Se não houver detailed-stats, mover achievements após profile-stats
                cardBody.insertBefore(achievementsWidget, profileStats.nextSibling);
            }

            if (achievementsWidget && quoteWidget) {
                // Mover quote após achievements
                cardBody.insertBefore(quoteWidget, achievementsWidget.nextSibling);
            } else if (detailedStatsWidget && quoteWidget) {
                // Se não houver achievements, mover quote após detailed-stats
                cardBody.insertBefore(quoteWidget, detailedStatsWidget.nextSibling);
            } else if (profileStats && quoteWidget) {
                // Se não houver detailed-stats nem achievements, mover quote após profile-stats
                cardBody.insertBefore(quoteWidget, profileStats.nextSibling);
            }

            if (quoteWidget && readingStatusWidget) {
                // Mover reading-status após quote
                cardBody.insertBefore(readingStatusWidget, quoteWidget.nextSibling);
            } else if (achievementsWidget && readingStatusWidget) {
                // Se não houver quote, mover reading-status após achievements
                cardBody.insertBefore(readingStatusWidget, achievementsWidget.nextSibling);
            } else if (detailedStatsWidget && readingStatusWidget) {
                // Se não houver quote nem achievements, mover reading-status após detailed-stats
                cardBody.insertBefore(readingStatusWidget, detailedStatsWidget.nextSibling);
            } else if (profileStats && readingStatusWidget) {
                // Se não houver outros widgets, mover reading-status após profile-stats
                cardBody.insertBefore(readingStatusWidget, profileStats.nextSibling);
            }

            if (readingStatusWidget && themeSelector) {
                // Mover theme-selector após reading-status
                cardBody.insertBefore(themeSelector, readingStatusWidget.nextSibling);
            } else if (quoteWidget && themeSelector) {
                // Se não houver reading-status, mover theme-selector após quote
                cardBody.insertBefore(themeSelector, quoteWidget.nextSibling);
            } else if (achievementsWidget && themeSelector) {
                // Se não houver quote nem reading-status, mover theme-selector após achievements
                cardBody.insertBefore(themeSelector, achievementsWidget.nextSibling);
            } else if (detailedStatsWidget && themeSelector) {
                // Se não houver outros widgets, mover theme-selector após detailed-stats
                cardBody.insertBefore(themeSelector, detailedStatsWidget.nextSibling);
            } else if (profileStats && themeSelector) {
                // Se não houver outros widgets, mover theme-selector após profile-stats
                cardBody.insertBefore(themeSelector, profileStats.nextSibling);
            }

            if (editButton) {
                // Mover botão de edição para o final
                cardBody.appendChild(editButton);
            }

            console.log('Ordem dos componentes reorganizada com sucesso');

        } catch (error) {
            console.error('Erro ao reorganizar componentes:', error);
        } finally {
            // Liberar flag após um tempo para permitir futuras reorganizações se necessário
            setTimeout(() => {
                this.isReorganizing = false;
            }, 5000);
        }
    }

    // Método para garantir que o botão de customização seja visível
    ensureCustomizeButtonVisible() {
        console.log('Verificando botão de customização do card...');

        // Verificar se o botão já existe
        let customizeBtn = this.cardElement.querySelector('.customize-button, #direct-customize-btn');

        if (!customizeBtn) {
            console.log('Botão de customização não encontrado, criando novo...');

            // Criar um botão fixo que sempre será visível
            customizeBtn = document.createElement('button');
            customizeBtn.id = 'direct-customize-btn';
            customizeBtn.className = 'btn btn-sm btn-primary position-absolute';
            customizeBtn.style.top = '10px';
            customizeBtn.style.right = '10px';
            customizeBtn.style.zIndex = '1000';
            customizeBtn.innerHTML = '<i class="bi bi-brush"></i>';
            customizeBtn.setAttribute('data-bs-toggle', 'tooltip');
            customizeBtn.setAttribute('data-bs-placement', 'top');
            customizeBtn.setAttribute('title', 'Personalizar card');

            // Garantir que o card tenha posição relativa
            this.cardElement.style.position = 'relative';

            // Adicionar evento de clique
            customizeBtn.addEventListener('click', () => {
                try {
                    // Tentar usar o customizador existente se disponível
                    if (window.customizer && typeof window.customizer.showCustomizationModal === 'function') {
                        window.customizer.showCustomizationModal();
                    } else {
                        // Fallback para abrir o modal diretamente
                        const modal = new bootstrap.Modal(document.getElementById('customizeCardModal'));
                        if (modal) {
                            modal.show();
                        } else {
                            console.error('Modal de customização não encontrado');
                        }
                    }
                } catch (error) {
                    console.error('Erro ao abrir modal de customização:', error);
                    alert('Erro ao abrir o painel de customização. Por favor, tente novamente.');
                }
            });

            // Adicionar ao card
            this.cardElement.appendChild(customizeBtn);
            console.log('Botão de customização criado e adicionado ao card');

            // Inicializar tooltip
            try {
                new bootstrap.Tooltip(customizeBtn);
            } catch (error) {
                console.error('Erro ao inicializar tooltip:', error);
            }
        } else {
            console.log('Botão de customização encontrado, garantindo visibilidade');

            // Garantir que o botão esteja visível
            customizeBtn.style.opacity = '1';
            customizeBtn.style.display = 'block';
        }
    }

    // Método para sincronizar estados entre os diferentes componentes
    syncComponentStates() {
        if (Object.keys(this.components).length <= 1) {
            console.log('Não há múltiplos componentes para sincronizar');
            return;
        }

        console.log('Sincronizando estados entre componentes');

        // Se o tema mudar, notificar todos os outros componentes
        if (this.components.themes) {
            this.components.themes.onThemeChange = (newTheme) => {
                // Notificar cada componente sobre a mudança de tema
                Object.entries(this.components).forEach(([name, component]) => {
                    if (name !== 'themes' && component && typeof component.updateTheme === 'function') {
                        component.updateTheme(newTheme);
                        console.log(`Tema atualizado para componente: ${name}`);
                    }
                });
            };
        }
    }
}

// Inicializar a integração quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se já existe uma instância
    if (!window.profileCardIntegration) {
        window.profileCardIntegration = new ProfileCardIntegration();
        console.log('Integração de card de perfil iniciada (sem loop)');
    }
});

// Expor a classe globalmente
window.ProfileCardIntegration = ProfileCardIntegration;