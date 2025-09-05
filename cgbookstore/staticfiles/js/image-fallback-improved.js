/**
 * Sistema de Fallback de Imagens - Versão Corrigida
 * Correção: Preserva URLs do proxy e evita interferência com Google Books
 * Data: 07/08/2025
 */

class ImageFallbackSystem {
    constructor() {
        this.processed = new Set();
        this.retryAttempts = new Map();
        this.maxRetries = 2;
        this.observer = null;
        this.fallbackSvg = '/static/images/no-cover.svg';

        // URLs que NUNCA devem sofrer fallback
        this.protectedUrls = [
            '/image-proxy/',
            'books.google.com',
            'googleusercontent.com'
        ];

        console.log('[ImageFallback] Sistema inicializado com proteção para proxy URLs');
    }

    /**
     * Verifica se uma URL deve ser protegida do fallback
     */
    isProtectedUrl(url) {
        if (!url) return false;

        return this.protectedUrls.some(pattern => {
            return url.includes(pattern);
        });
    }

    /**
     * Processa capas de livros com proteção aprimorada
     */
    processBookCovers(books) {
        if (!books || books.length === 0) {
            console.log('[ImageFallback] Processando 0 capas de livros');
            return;
        }

        console.log(`[ImageFallback] Processando ${books.length} capas de livros`);

        books.forEach(img => {
            const src = img.getAttribute('src') || img.getAttribute('data-src');
            const imgId = img.getAttribute('data-book-id') || src;

            // Pula se já foi processada
            if (this.processed.has(imgId)) return;

            // PROTEÇÃO CRÍTICA: URLs do proxy nunca sofrem fallback
            if (this.isProtectedUrl(src)) {
                console.log(`[ImageFallback] URL protegida ignorada: ${src?.substring(0, 50)}...`);
                this.processed.add(imgId);
                return;
            }

            // Só aplica fallback se a imagem realmente falhou
            if (!img.complete || img.naturalWidth === 0) {
                this.setupFallback(img, imgId);
            }

            this.processed.add(imgId);
        });
    }

    /**
     * Configura fallback apenas quando necessário
     */
    setupFallback(img, imgId) {
        const currentAttempts = this.retryAttempts.get(imgId) || 0;

        if (currentAttempts >= this.maxRetries) {
            console.log(`[ImageFallback] Aplicando fallback após ${currentAttempts} tentativas: ${imgId}`);
            img.src = this.fallbackSvg;
            img.alt = 'Capa não disponível';
            return;
        }

        // Incrementa tentativas e tenta recarregar
        this.retryAttempts.set(imgId, currentAttempts + 1);

        img.onerror = () => {
            setTimeout(() => {
                this.setupFallback(img, imgId);
            }, 1000 * (currentAttempts + 1)); // Delay progressivo
        };

        img.onload = () => {
            console.log(`[ImageFallback] Imagem carregada com sucesso: ${imgId}`);
            this.retryAttempts.delete(imgId);
        };
    }

    /**
     * Inicia observador de DOM com proteção
     */
    startDOMObserver() {
        if (this.observer) return;

        this.observer = new MutationObserver((mutations) => {
            let hasNewImages = false;

            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const images = node.querySelectorAll ?
                                node.querySelectorAll('.book-cover-img, .book-cover, [data-book-id]') : [];

                            if (images.length > 0) {
                                hasNewImages = true;
                            }
                        }
                    });
                }
            });

            if (hasNewImages) {
                setTimeout(() => {
                    this.runCheck();
                }, 100);
            }
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('[ImageFallback] Observador de DOM iniciado');
    }

    /**
     * Executa verificação das imagens
     */
    runCheck() {
        const books = document.querySelectorAll('.book-cover-img, .book-cover, [data-book-id]');
        this.processBookCovers(Array.from(books));
    }

    /**
     * Inicializa o sistema
     */
    init() {
        console.log('[ImageFallback] Inicializando sistema de fallback de imagens');

        // Verificação inicial
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.runCheck();
                this.startDOMObserver();
            });
        } else {
            this.runCheck();
            this.startDOMObserver();
        }

        // Verificações adicionais para garantir cobertura
        setTimeout(() => {
            console.log('[ImageFallback] Realizando verificação após carregamento');
            this.runCheck();
        }, 1000);

        setTimeout(() => {
            console.log('[ImageFallback] Realizando verificação secundária');
            this.runCheck();
        }, 3000);
    }

    /**
     * Cleanup do sistema
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
        this.processed.clear();
        this.retryAttempts.clear();
    }
}

// Inicialização global
const imageFallbackSystem = new ImageFallbackSystem();
imageFallbackSystem.init();

// Compatibilidade com código existente
window.ImageFallback = {
    init: () => imageFallbackSystem.init(),
    runCheck: () => imageFallbackSystem.runCheck(),
    destroy: () => imageFallbackSystem.destroy()
};