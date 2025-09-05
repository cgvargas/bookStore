// static/js/chatbot_widget.js

document.addEventListener('DOMContentLoaded', function() {
    // Elementos específicos da UI do WIDGET
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWidget = document.getElementById('chatbotWidget');
    const chatbotClose = document.getElementById('chatbotClose');

    if (!chatbotToggle || !chatbotWidget || !chatbotClose) {
        console.error("Elementos do widget (toggle, widget, close) não encontrados.");
        return;
    }

    // Lógica para abrir e fechar o widget
    chatbotToggle.addEventListener('click', () => {
        chatbotToggle.style.display = 'none';
        chatbotWidget.classList.add('open');
        // Foca no input ao abrir
        document.getElementById('widgetUserMessage').focus();
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWidget.classList.remove('open');
        // Adiciona um delay para a transição CSS antes de mostrar o botão de toggle
        setTimeout(() => chatbotToggle.style.display = 'flex', 300);
    });

    // Configuração para o ChatbotCore funcionar no contexto do WIDGET
    const widgetConfig = {
        formId: 'widgetChatForm',
        inputId: 'widgetUserMessage',
        messagesId: 'chatbotMessages', // Note que o ID é o mesmo no seu HTML
        typingIndicatorId: 'typingIndicator', // O ID também é o mesmo
        suggestionBtnsSelector: '#chatbotWidget .suggestion-btn' // Seja específico para os botões do widget
    };

    // Inicializa a lógica central do chatbot para o widget
    new ChatbotCore(widgetConfig);
});