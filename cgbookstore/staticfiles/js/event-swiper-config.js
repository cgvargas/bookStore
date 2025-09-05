/**
 * Widget de Eventos - JavaScript
 * Gerencia a funcionalidade do carrossel de eventos e botão de navegação
 */

class EventWidget {
    constructor() {
        this.swiper = null;
        this.initialized = false;
        this.init();
    }

    /**
     * Inicializa o widget de eventos
     */
    init() {
        // Aguardar o DOM estar carregado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    /**
     * Configura o widget após o DOM estar pronto
     */
    setup() {
        this.initializeSwiper();
        this.setupEventListeners();
        this.handleImageErrors();
        this.setupAccessibility();
        this.initialized = true;
    }

    /**
     * Inicializa o carrossel Swiper
     */
    initializeSwiper() {
        const swiperElement = document.querySelector('.event-swiper');

        if (!swiperElement) {
            console.warn('Event widget: Elemento swiper não encontrado');
            return;
        }

        if (typeof Swiper === 'undefined') {
            console.warn('Event widget: Swiper não está disponível');
            return;
        }

        // Contar slides disponíveis
        const slideCount = swiperElement.querySelectorAll('.swiper-slide').length;

        // Configuração do Swiper
        const swiperConfig = {
            // Configurações básicas
            loop: slideCount > 1,
            slidesPerView: 1,
            spaceBetween: 0,

            // Navegação
            pagination: {
                el: '.event-swiper .swiper-pagination',
                clickable: true,
                dynamicBullets: true,
                renderBullet: function (index, className) {
                    return `<span class="${className}" aria-label="Ir para evento ${index + 1}"></span>`;
                }
            },

            navigation: {
                nextEl: '.event-swiper .swiper-button-next',
                prevEl: '.event-swiper .swiper-button-prev',
            },

            // Efeitos
            effect: 'slide',
            speed: 600,

            // Autoplay apenas se houver múltiplos slides
            autoplay: slideCount > 1 ? {
                delay: 5000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true
            } : false,

            // Acessibilidade
            a11y: {
                enabled: true,
                prevSlideMessage: 'Slide anterior',
                nextSlideMessage: 'Próximo slide',
                paginationBulletMessage: 'Ir para slide {{index}}'
            },

            // Keyboard
            keyboard: {
                enabled: true,
                onlyInViewport: true
            },

            // Eventos
            on: {
                init: () => {
                    swiperElement.classList.add('swiper-initialized');
                    this.onSwiperInit();
                },

                slideChange: (swiper) => {
                    this.onSlideChange(swiper);
                },

                reachEnd: () => {
                    this.onReachEnd();
                },

                reachBeginning: () => {
                    this.onReachBeginning();
                }
            }
        };

        try {
            this.swiper = new Swiper('.event-swiper', swiperConfig);
        } catch (error) {
            console.error('Event widget: Erro ao inicializar Swiper:', error);
        }
    }

    /**
     * Configura os event listeners
     */
    setupEventListeners() {
        // Botão "Ver todos os eventos"
        this.setupViewAllButton();

        // Navegação por teclado
        this.setupKeyboardNavigation();

        // Pausar autoplay ao passar mouse
        this.setupMouseEvents();
    }

    /**
     * Configura o botão "Ver todos os eventos"
     */
    setupViewAllButton() {
        const viewAllButton = document.querySelector('.btn-view-all');

        if (!viewAllButton) {
            return;
        }

        // Efeito visual de clique
        viewAllButton.addEventListener('click', (e) => {
            this.handleViewAllClick(e, viewAllButton);
        });

        // Suporte para teclado
        viewAllButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.handleViewAllClick(e, viewAllButton);
            }
        });

        // Adicionar indicador de loading ao clicar
        viewAllButton.addEventListener('click', () => {
            this.addLoadingState(viewAllButton);
        });
    }

    /**
     * Manipula o clique no botão "Ver todos os eventos"
     */
    handleViewAllClick(event, button) {
        // Efeito visual
        button.style.transform = 'scale(0.95)';

        setTimeout(() => {
            button.style.transform = '';
        }, 100);

        // Analytics ou tracking
        this.trackEvent('view_all_events_clicked', {
            widget_location: 'sidebar',
            event_count: document.querySelectorAll('.swiper-slide').length
        });
    }

    /**
     * Adiciona estado de loading ao botão
     */
    addLoadingState(button) {
        const originalText = button.innerHTML;
        button.classList.add('loading');

        // Restaurar estado após navegação ou timeout
        setTimeout(() => {
            button.classList.remove('loading');
        }, 3000);
    }

    /**
     * Configura navegação por teclado
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (!this.swiper || !this.isWidgetFocused()) {
                return;
            }

            switch (e.key) {
                case 'ArrowLeft':
                    this.swiper.slidePrev();
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    this.swiper.slideNext();
                    e.preventDefault();
                    break;
                case 'Home':
                    this.swiper.slideTo(0);
                    e.preventDefault();
                    break;
                case 'End':
                    this.swiper.slideTo(this.swiper.slides.length - 1);
                    e.preventDefault();
                    break;
            }
        });
    }

    /**
     * Verifica se o widget está em foco
     */
    isWidgetFocused() {
        const activeElement = document.activeElement;
        return activeElement && activeElement.closest('.event-widget-wrapper');
    }

    /**
     * Configura eventos do mouse
     */
    setupMouseEvents() {
        const widgetWrapper = document.querySelector('.event-widget-wrapper');

        if (!widgetWrapper || !this.swiper) {
            return;
        }

        // Pausar autoplay ao passar mouse
        widgetWrapper.addEventListener('mouseenter', () => {
            if (this.swiper.autoplay) {
                this.swiper.autoplay.stop();
            }
        });

        // Retomar autoplay ao sair com mouse
        widgetWrapper.addEventListener('mouseleave', () => {
            if (this.swiper.autoplay) {
                this.swiper.autoplay.start();
            }
        });
    }

    /**
     * Trata erros de carregamento de imagens
     */
    handleImageErrors() {
        const eventImages = document.querySelectorAll('.event-image');

        eventImages.forEach((img) => {
            img.addEventListener('error', () => {
                this.replaceFailedImage(img);
            });

            // Verificar se já falhou no carregamento
            if (img.complete && img.naturalWidth === 0) {
                this.replaceFailedImage(img);
            }
        });
    }

    /**
     * Substitui imagem que falhou no carregamento
     */
    replaceFailedImage(img) {
        const placeholder = document.createElement('div');
        placeholder.className = 'event-image-placeholder';
        placeholder.innerHTML = '<i class="bi bi-calendar-event"></i>';
        placeholder.setAttribute('aria-label', 'Imagem do evento indisponível');

        // Aplicar estilos
        Object.assign(placeholder.style, {
            width: '100%',
            height: '150px',
            background: 'var(--cor-fundo-hover)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--cor-texto-secundario)',
            fontSize: '2rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--spacing-md)'
        });

        img.parentNode.replaceChild(placeholder, img);
    }

    /**
     * Configura melhorias de acessibilidade
     */
    setupAccessibility() {
        // Adicionar role e aria-label ao carrossel
        const swiperElement = document.querySelector('.event-swiper');
        if (swiperElement) {
            swiperElement.setAttribute('role', 'region');
            swiperElement.setAttribute('aria-label', 'Carrossel de eventos em destaque');
        }

        // Melhorar botões de navegação
        const prevButton = document.querySelector('.swiper-button-prev');
        const nextButton = document.querySelector('.swiper-button-next');

        if (prevButton) {
            prevButton.setAttribute('tabindex', '0');
            prevButton.setAttribute('role', 'button');
        }

        if (nextButton) {
            nextButton.setAttribute('tabindex', '0');
            nextButton.setAttribute('role', 'button');
        }
    }

    /**
     * Callbacks do Swiper
     */
    onSwiperInit() {
        console.log('Event widget: Swiper inicializado');
        this.trackEvent('event_widget_loaded', {
            slide_count: this.swiper.slides.length
        });
    }

    onSlideChange(swiper) {
        console.log(`Event widget: Slide mudou para ${swiper.activeIndex}`);
        this.trackEvent('event_slide_changed', {
            slide_index: swiper.activeIndex
        });
    }

    onReachEnd() {
        console.log('Event widget: Chegou ao último slide');
    }

    onReachBeginning() {
        console.log('Event widget: Voltou ao primeiro slide');
    }

    /**
     * Função para tracking/analytics
     */
    trackEvent(eventName, properties = {}) {
        // Implementar tracking de analytics aqui
        // Exemplo: Google Analytics, Mixpanel, etc.
        console.log(`Event tracked: ${eventName}`, properties);

        // Exemplo com Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, properties);
        }
    }

    /**
     * Método público para atualizar o widget
     */
    refresh() {
        if (this.swiper) {
            this.swiper.update();
        }
    }

    /**
     * Método público para destruir o widget
     */
    destroy() {
        if (this.swiper) {
            this.swiper.destroy(true, true);
            this.swiper = null;
        }
        this.initialized = false;
    }
}

// Inicializar automaticamente quando o script for carregado
let eventWidgetInstance = null;

// Função para inicializar o widget
function initEventWidget() {
    if (!eventWidgetInstance) {
        eventWidgetInstance = new EventWidget();
    }
    return eventWidgetInstance;
}

// Auto-inicialização
initEventWidget();

// Exportar para uso global
window.EventWidget = EventWidget;
window.eventWidgetInstance = eventWidgetInstance;