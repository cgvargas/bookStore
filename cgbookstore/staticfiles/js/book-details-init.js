// Inicialização rápida para evitar erros de carregamento
document.addEventListener('DOMContentLoaded', function() {
    // Garantir que o body existe antes de aplicar classes
    if (document.body) {
        document.body.classList.add('book-details-page');
    }

    // Prevenir erros de undefined
    window.BookDetailsApp = window.BookDetailsApp || {};
});

// Prevenir erros durante o carregamento
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.warn('Erro global capturado:', msg);
    // Continuar execução normal
    return false;
};