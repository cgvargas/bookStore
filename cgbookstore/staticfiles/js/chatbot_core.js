// static/js/chatbot_core.js

/**
 * ChatbotCore - Lógica central e reutilizável para o assistente.
 * Pode ser instanciado tanto para a página de chat dedicada quanto para o widget.
 */
class ChatbotCore {
    constructor(config) {
        // Mapeia os elementos do DOM com base na configuração fornecida
        this.chatForm = document.getElementById(config.formId);
        this.userInput = document.getElementById(config.inputId);
        this.messagesContainer = document.getElementById(config.messagesId);
        this.typingIndicator = document.getElementById(config.typingIndicatorId);
        this.suggestionBtns = document.querySelectorAll(config.suggestionBtnsSelector);

        // Estado interno
        this.isProcessing = false;
        this.apiUrl = '/chatbot/api/message/'; // URL central da API

        // Garante que os elementos essenciais existem antes de prosseguir
        if (!this.chatForm || !this.userInput || !this.messagesContainer || !this.typingIndicator) {
            console.error("ChatbotCore: Elementos essenciais do DOM não foram encontrados. Verifique a configuração.");
            return;
        }

        this.init();
    }

    /**
     * Inicializa os listeners de eventos.
     */
    init() {
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = this.userInput.value.trim();
            if (message) {
                this.handleRequest({ message: message }, message);
            }
        });

        this.suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.handleSuggestionClick(btn);
            });
        });

        this.scrollToBottom();
    }

    // --- Funções de Manipulação da UI ---

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    addMessage(content, sender, time) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        // Usar innerText previne XSS e renderiza quebras de linha com o CSS 'white-space: pre-wrap'
        contentDiv.innerText = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);

        this.messagesContainer.insertBefore(messageDiv, this.typingIndicator);
        this.scrollToBottom();
    }

    // --- Funções de Comunicação e Lógica ---

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    handleSuggestionClick(btn) {
        if (this.isProcessing) return;

        const suggestionText = btn.textContent.trim();
        let payload;
        let userDisplayMessage;

        // Centraliza a lógica de sugestões
        switch (suggestionText) {
            case 'Recomende livros':
                payload = { action: 'get_recommendations' };
                userDisplayMessage = 'Pode me recomendar alguns livros?';
                break;
            case 'Meus favoritos':
                payload = { action: 'get_favorites' };
                userDisplayMessage = 'Quero ver meus livros favoritos.';
                break;
            default:
                payload = { message: suggestionText };
                userDisplayMessage = suggestionText;
                break;
        }
        this.handleRequest(payload, userDisplayMessage);
    }

    async handleRequest(payload, userDisplayMessage) {
        if (this.isProcessing) return;
        this.isProcessing = true;

        if (userDisplayMessage) {
            this.addMessage(userDisplayMessage, 'user');
        }

        if (this.userInput.value) {
            this.userInput.value = '';
        }

        this.showTypingIndicator();

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });

            this.hideTypingIndicator();

            if (response.status === 401) {
                this.addMessage("Você precisa estar logado para usar esta função.", "bot");
                return;
            }
            if (!response.ok) {
                throw new Error(`Erro do servidor: ${response.status}`);
            }

            const data = await response.json();
            this.addMessage(data.response, 'bot', data.timestamp);

        } catch (error) {
            console.error("Erro ao processar a solicitação do chatbot:", error);
            this.hideTypingIndicator();
            this.addMessage("Desculpe, não consegui processar sua solicitação. Tente novamente.", "bot");
        } finally {
            this.isProcessing = false;
        }
    }
}