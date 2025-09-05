// static/js/chatbot_page.js

document.addEventListener('DOMContentLoaded', function() {
    // Configuração para o ChatbotCore funcionar no contexto da PÁGINA DEDICADA
    const pageConfig = {
        formId: 'chatForm',
        inputId: 'userMessage',
        messagesId: 'chatMessages',
        typingIndicatorId: 'typingIndicator',
        suggestionBtnsSelector: '.card-footer .suggestion-btn' // Botões específicos da página
    };

    // Inicializa a lógica central do chatbot para a página
    const chat = new ChatbotCore(pageConfig);

    // Adiciona mensagem inicial apenas se o chat estiver vazio
    // (Verifica se há mais de 1 elemento, pois o indicador de digitação já está lá)
    if (chat.messagesContainer && chat.messagesContainer.children.length <= 1) {
        const initialBotMessage = "Olá! Sou o assistente literário da CG.BookStore. Como posso ajudar você hoje?";
        chat.addMessage(initialBotMessage, 'bot');
    }
});