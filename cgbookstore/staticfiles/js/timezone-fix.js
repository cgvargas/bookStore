/**
 * Script para corrigir o problema de fuso horário nas mensagens do chatbot
 * Adicione este script como um novo arquivo: timezone-fix.js
 */
document.addEventListener('DOMContentLoaded', function() {
    // Função para corrigir a exibição do horário no chatbot
    function fixTimezone() {
        console.log("Aplicando correção de fuso horário...");

        // Sobrescrever a função que formata a hora nas mensagens
        if (window.getCurrentTime) {
            // Guardar referência à função original
            const originalGetCurrentTime = window.getCurrentTime;

            // Sobrescrever com nova função que aplica o offset do Brasil
            window.getCurrentTime = function() {
                // Obter a data atual
                const now = new Date();

                // Calcular o fuso horário para o Brasil (UTC-3)
                // Isso ajusta a hora para o fuso horário brasileiro
                const brasilOffset = -3 * 60; // -3 horas em minutos
                const currentOffset = now.getTimezoneOffset(); // Offset local em minutos
                const adjustment = brasilOffset - currentOffset; // Ajuste necessário

                // Criar uma nova data com o ajuste
                const adjustedDate = new Date(now.getTime() + adjustment * 60 * 1000);

                // Formatar a hora no padrão HH:MM
                const hours = String(adjustedDate.getHours()).padStart(2, '0');
                const minutes = String(adjustedDate.getMinutes()).padStart(2, '0');

                return `${hours}:${minutes}`;
            };

            console.log("Função de formatação de hora substituída com sucesso!");
        }

        // Corrigir mensagens existentes
        function fixExistingMessages() {
            // Encontrar todas as mensagens no chatbot
            const timeElements = document.querySelectorAll('.message-time');

            timeElements.forEach(function(el) {
                // Verificar se o texto parece uma hora (formato HH:MM)
                const timeRegex = /^(\d{1,2}):(\d{2})$/;
                const match = timeRegex.exec(el.textContent.trim());

                if (match) {
                    // Extrair horas e minutos
                    let hours = parseInt(match[1], 10);
                    const minutes = match[2];

                    // Ajustar as horas (subtrair 3 horas para o fuso horário brasileiro)
                    hours = (hours - 3 + 24) % 24;

                    // Aplicar o novo horário
                    el.textContent = `${String(hours).padStart(2, '0')}:${minutes}`;
                }
            });
        }

        // Observar mudanças para corrigir novos horários
        const messagesContainer = document.getElementById('chatbotMessages');
        if (messagesContainer) {
            const observer = new MutationObserver(function(mutations) {
                fixExistingMessages();
            });

            observer.observe(messagesContainer, {
                childList: true,
                subtree: true
            });

            // Corrigir mensagens existentes
            fixExistingMessages();
        }
    }

    // Executar a correção de fuso horário
    fixTimezone();

    // Configurar para executar quando o widget for carregado
    const bodyObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1 &&
                        (node.id === 'chatbotWidget' ||
                         (node.querySelector && node.querySelector('#chatbotWidget')))) {
                        setTimeout(fixTimezone, 300);
                        break;
                    }
                }
            }
        });
    });

    bodyObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
});