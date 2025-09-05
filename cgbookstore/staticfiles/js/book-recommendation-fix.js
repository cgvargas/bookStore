/**
 * Solução corrigida para renderização de capas - NÃO interfere com proxy
 * Data: 03/06/2025 - Versão Corrigida
 * IMPORTANTE: Preserva URLs do proxy de imagem
 */
// book-recommendation-fix.js - Versão Corrigida (SEM LOOP INFINITO)
(function() {
    'use strict';

    let isProcessing = false;
    let processedImages = new Set();
    let verificationCount = 0;
    const MAX_VERIFICATIONS = 3; // Limitar verificações

    function log(message) {
        console.log(`[BookCoverFix] ${message}`);
    }

    function getProxyUrl(originalUrl) {
        if (!originalUrl) return null;

        // Se já é uma URL do proxy, não alterar
        if (originalUrl.includes('/image-proxy/')) {
            return originalUrl;
        }

        // Se é URL do Google Books, aplicar proxy
        if (originalUrl.includes('books.google.com') || originalUrl.includes('books.googleusercontent.com')) {
            return `/image-proxy/?url=${encodeURIComponent(originalUrl)}`;
        }

        return originalUrl;
    }

    function isGoogleBooksUrl(url) {
        return url && (url.includes('books.google.com') || url.includes('books.googleusercontent.com'));
    }

    function processImage(img, index) {
        const imageId = `img-${index}-${img.src?.substring(0, 20)}`;

        // Evitar processar a mesma imagem múltiplas vezes
        if (processedImages.has(imageId)) {
            return { processed: false, reason: 'already_processed' };
        }

        const originalSrc = img.src || img.dataset.originalSrc || '';

        if (!originalSrc) {
            return { processed: false, reason: 'no_src' };
        }

        // Categorizar imagem
        let category = 'local';
        let needsProxy = false;

        if (originalSrc.includes('/image-proxy/')) {
            category = 'proxy';
        } else if (isGoogleBooksUrl(originalSrc)) {
            category = 'external';
            needsProxy = true;
        }

        // Aplicar correção se necessário
        if (needsProxy) {
            const proxyUrl = getProxyUrl(originalSrc);
            if (proxyUrl && proxyUrl !== originalSrc) {
                img.src = proxyUrl;
                img.dataset.originalSrc = originalSrc;
                processedImages.add(imageId);
                log(`Imagem corrigida para usar proxy: ${originalSrc.substring(0, 50)}...`);
                return { processed: true, reason: 'proxy_applied', category };
            }
        }

        processedImages.add(imageId);
        return { processed: false, reason: 'no_change_needed', category };
    }

    function fixBookImages() {
        // Prevenir execução simultânea
        if (isProcessing) {
            log('Verificação já em andamento, ignorando...');
            return;
        }

        // Limitar número de verificações
        verificationCount++;
        if (verificationCount > MAX_VERIFICATIONS) {
            log(`Máximo de verificações (${MAX_VERIFICATIONS}) atingido. Parando verificações automáticas.`);
            return;
        }

        isProcessing = true;
        log(`Iniciando verificação ${verificationCount}/${MAX_VERIFICATIONS}...`);

        try {
            const bookImages = document.querySelectorAll('img[alt*="livro"], img[alt*="book"], .book-cover-img, .google-books-image');

            if (bookImages.length === 0) {
                log('Nenhuma imagem de livro encontrada');
                return;
            }

            let stats = {
                total: bookImages.length,
                proxy: 0,
                external: 0,
                local: 0,
                corrected: 0
            };

            const problematicUrls = [];

            bookImages.forEach((img, index) => {
                const result = processImage(img, index);

                if (result.category) {
                    stats[result.category]++;
                }

                if (result.processed && result.reason === 'proxy_applied') {
                    stats.corrected++;
                }

                // Coletar URLs problemáticas
                if (result.reason === 'no_change_needed' && result.category === 'external') {
                    const url = img.src || img.dataset.originalSrc || '';
                    if (url && !url.includes('/image-proxy/')) {
                        problematicUrls.push(url.substring(0, 80) + '...');
                    }
                }
            });

            log(`Estatísticas (Verificação ${verificationCount}): Proxy: ${stats.proxy}, Externas: ${stats.external}, Locais: ${stats.local}, Corrigidas: ${stats.corrected}`);

            if (problematicUrls.length > 0 && verificationCount === 1) {
                log(`URLs que precisam de atenção:`);
                problematicUrls.slice(0, 3).forEach((url, index) => {
                    log(`  ${index + 1}. ${url}`);
                });
            }

            if (stats.corrected > 0) {
                log(`✅ ${stats.corrected} imagem(ns) corrigida(s) para usar proxy`);
            }

        } catch (error) {
            log(`Erro durante verificação: ${error.message}`);
        } finally {
            isProcessing = false;
        }
    }

    function handleImageError(img) {
        const originalSrc = img.dataset.originalSrc || img.src;

        if (originalSrc && isGoogleBooksUrl(originalSrc)) {
            // Tentar fallback para imagem padrão
            const fallbackSrc = '/static/images/no-cover.svg';
            if (img.src !== fallbackSrc) {
                log(`Aplicando fallback para imagem com erro: ${originalSrc.substring(0, 50)}...`);
                img.src = fallbackSrc;
                img.classList.add('fallback-image');
            }
        }
    }

    function initializeImageFallbacks() {
        document.addEventListener('error', function(e) {
            if (e.target.tagName === 'IMG') {
                handleImageError(e.target);
            }
        }, true);
    }

    function initialize() {
        log('Iniciando correção de capas - Versão sem loop infinito');

        // Configurar fallbacks
        initializeImageFallbacks();

        // Verificação inicial
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fixBookImages);
        } else {
            fixBookImages();
        }

        // Verificação após carregamento completo
        if (document.readyState !== 'complete') {
            window.addEventListener('load', function() {
                setTimeout(fixBookImages, 500); // Pequeno delay
            });
        }

        // Verificação final após 2 segundos (UMA VEZ APENAS)
        setTimeout(function() {
            if (verificationCount < MAX_VERIFICATIONS) {
                log('Realizando verificação final...');
                fixBookImages();
            }
        }, 2000);

        log('Sistema de correção inicializado com proteção anti-loop');
    }

    // Função global para verificação manual (se necessário)
    window.manualBookImageCheck = function() {
        if (verificationCount < MAX_VERIFICATIONS) {
            log('Verificação manual solicitada');
            fixBookImages();
        } else {
            log('Máximo de verificações atingido. Recarregue a página se necessário.');
        }
    };

    // Função para resetar contadores (para debug)
    window.resetBookImageFix = function() {
        verificationCount = 0;
        processedImages.clear();
        isProcessing = false;
        log('Contadores resetados');
    };

    // Inicializar
    initialize();

})();