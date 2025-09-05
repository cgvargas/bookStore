/**
 * Script para corrigir os botões de sugestão do chatbot
 * Adicione este script como um novo arquivo: suggestion-buttons-fix.js
 */
document.addEventListener('DOMContentLoaded', function() {
    function fixSuggestionButtons() {
        console.log("Corrigindo botões de sugestão...");

        // Encontrar os botões de sugestão
        const suggestionButtons = document.querySelectorAll('.suggestion-btn');
        if (suggestionButtons.length === 0) {
            console.log("Nenhum botão de sugestão encontrado. Tentando novamente em 1 segundo...");
            setTimeout(fixSuggestionButtons, 1000);
            return;
        }

        console.log(`Encontrados ${suggestionButtons.length} botões de sugestão.`);

        // Para cada botão
        suggestionButtons.forEach(function(btn) {
            // Adicionar um novo evento de clique
            btn.onclick = function(event) {
                // Prevenir comportamento padrão
                event.preventDefault();
                event.stopPropagation();

                // Obter o texto do botão
                const message = this.textContent.trim();
                console.log("Botão de sugestão clicado:", message);

                // Encontrar o campo de entrada
                const messageInput = document.getElementById('widgetUserMessage');
                if (messageInput) {
                    // Preencher o campo com a mensagem
                    messageInput.value = message;

                    // Encontrar o formulário
                    const form = document.getElementById('widgetChatForm');
                    if (form && typeof form.onsubmit === 'function') {
                        // Se o formulário tem um manipulador onsubmit, chamar diretamente
                        form.onsubmit(new Event('submit'));
                    } else if (form) {
                        // Caso contrário, disparar um evento de submit
                        form.dispatchEvent(new Event('submit', {
                            bubbles: true,
                            cancelable: true
                        }));
                    }
                }

                // Retornar false para evitar propagação
                return false;
            };
        });

        console.log("Botões de sugestão corrigidos!");
    }

    // Executar agora e também depois que o DOM estiver completamente carregado
    fixSuggestionButtons();

    // Também executar quando o chatbot widget for carregado
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                setTimeout(fixSuggestionButtons, 500);
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Executar novamente após 3 segundos para garantir
    setTimeout(fixSuggestionButtons, 3000);
});