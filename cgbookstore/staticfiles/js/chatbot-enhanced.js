// /static/js/chatbot-enhanced.js

class ChatbotEnhanced {
    constructor() {
        this.userSettings = {};
        this.isTyping = false;
        this.messageHistory = [];
        this.csrfToken = this.getCSRFToken();
        this.apiUrl = '/chatbot/api/message/';

        // ✅ CORREÇÃO 1: Adicionar a variável para armazenar o ID da conversa.
        this.conversationId = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.createQuickActions();
        this.showWelcomeMessage();
        this.loadUserSettings();
    }

    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        console.warn('⚠️ CSRF token não encontrado');
        return '';
    }

    setupEventListeners() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');

        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = input.scrollHeight + 'px';
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
    }

    createQuickActions() {
        const container = document.getElementById('chatbot-container');
        if (!container) return;
        if (document.getElementById('quick-actions')) return;
        const quickActionsHTML = `
            <div id="quick-actions" class="quick-actions mb-3">
                <div class="row g-2">
                    <div class="col-md-4"><button class="btn btn-outline-primary w-100 quick-action-btn" onclick="chatbot.sendQuickMessage('📚 Meus Favoritos', 'Mostre meus livros favoritos')"><i class="bi bi-heart-fill"></i> Meus Favoritos</button></div>
                    <div class="col-md-4"><button class="btn btn-outline-success w-100 quick-action-btn" onclick="chatbot.sendQuickMessage('⭐ Obter Recomendações', 'Me recomende alguns livros')"><i class="bi bi-star-fill"></i> Recomendações</button></div>
                    <div class="col-md-4"><button class="btn btn-outline-info w-100 quick-action-btn" onclick="chatbot.sendQuickMessage('📊 Meu Progresso', 'Mostre meu progresso de leitura')"><i class="bi bi-graph-up"></i> Meu Progresso</button></div>
                </div>
                <div class="row g-2 mt-2">
                    <div class="col-md-3"><button class="btn btn-outline-secondary btn-sm w-100" onclick="chatbot.sendQuickMessage('❓ Ajuda', 'O que você pode fazer?')">Ajuda</button></div>
                    <div class="col-md-3"><button class="btn btn-outline-secondary btn-sm w-100" onclick="chatbot.sendQuickMessage('🔍 Buscar', 'Quero buscar um livro')">Buscar</button></div>
                    <div class="col-md-3"><button class="btn btn-outline-secondary btn-sm w-100" onclick="chatbot.sendQuickMessage('💰 Preços', 'Ver preços e promoções')">Preços</button></div>
                    <div class="col-md-3"><button class="btn btn-outline-danger btn-sm w-100" onclick="chatbot.clearConversation()">Limpar</button></div>
                </div>
            </div>`;
        const inputArea = container.querySelector('.chat-input-area');
        if (inputArea) {
            inputArea.insertAdjacentHTML('beforebegin', quickActionsHTML);
        }
    }

    showWelcomeMessage() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer && messagesContainer.children.length === 0) {
            const userName = this.userSettings?.user_profile?.name || 'leitor';
            const welcomeMessage = `<div class="message bot-message show"><div class="message-content"><div class="message-text">Olá${userName !== 'leitor' ? ', ' + userName : ''}! 👋<br><br>Sou seu assistente literário personalizado. Posso ajudar com:<ul><li>📚 Recomendações de livros</li><li>🔍 Buscar títulos e autores</li><li>💰 Consultar preços</li><li>📊 Acompanhar seu progresso</li><li>❓ Responder dúvidas sobre literatura</li></ul>Como posso ajudar você hoje?</div><div class="message-meta"><span class="timestamp">${new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}</span></div></div></div>`;
            messagesContainer.innerHTML = welcomeMessage;
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input?.value?.trim();
        if (!message || this.isTyping) return;
        input.value = '';
        input.style.height = 'auto';
        this.addMessage(message, 'user');
        this.isTyping = true;
        this.showTypingIndicator();
        try {
            const response = await this.callAPI(message);
            this.handleResponse(response, message);
        } catch (error) {
            console.error('❌ Erro ao enviar mensagem:', error);
            this.handleError(error);
        } finally {
            this.isTyping = false;
            this.hideTypingIndicator();
        }
    }

    async sendQuickMessage(displayText, actualMessage) {
        this.addMessage(displayText, 'user');
        this.isTyping = true;
        this.showTypingIndicator();
        try {
            const response = await this.callAPI(actualMessage);
            this.handleResponse(response, actualMessage);
        } catch (error) {
            console.error('❌ Erro em ação rápida:', error);
            this.handleError(error);
        } finally {
            this.isTyping = false;
            this.hideTypingIndicator();
        }
    }

    async callAPI(message) {
        // ✅ CORREÇÃO 2: Montar o payload incluindo o `conversationId` da classe.
        const payload = {
            message: message,
            conversation_id: this.conversationId // Na primeira vez, será `null`.
        };

        const headers = { 'Content-Type': 'application/json' };
        if (this.csrfToken) {
            headers['X-CSRFToken'] = this.csrfToken;
        }

        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            if (response.status === 400) { throw new Error(`Requisição inválida: ${await response.text()}`); }
            else if (response.status === 401) { throw new Error('Você precisa estar logado para usar o chatbot'); }
            else if (response.status === 403) { throw new Error('Token CSRF inválido. Recarregue a página.'); }
            else { throw new Error(`Erro do servidor: ${response.status}`); }
        }

        return await response.json();
    }

    handleResponse(response, originalMessage) {
        // ✅ CORREÇÃO 3: Atualizar o `conversationId` da classe com o valor retornado.
        if (response.conversation_id) {
            this.conversationId = response.conversation_id;
        }

        const botResponse = response.response || 'Desculpe, não consegui processar sua mensagem.';
        const messageId = this.addMessage(botResponse, 'bot', response.message_id);
        if (response.suggestions && response.suggestions.length > 0) {
            this.addSuggestions(response.suggestions);
        }
        this.messageHistory.push({
            user: originalMessage,
            bot: botResponse,
            timestamp: new Date(),
            metadata: response
        });
    }

    handleError(error) {
        let errorMessage = 'Desculpe, ocorreu um erro. Tente novamente.';
        if (error.message.includes('401')) { errorMessage = 'Você precisa estar logado. <a href="/login/">Fazer login</a>'; }
        else if (error.message.includes('403')) { errorMessage = 'Sessão expirou. <a href="javascript:location.reload()">Recarregar página</a>'; }
        else if (error.message.includes('400')) { errorMessage = 'Formato de mensagem inválido. Verifique sua mensagem e tente novamente.'; }
        this.addMessage(errorMessage, 'bot', null, true);
    }

    addMessage(content, sender, messageId = null, isError = false) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return null;
        const timestamp = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        const messageClass = isError ? 'bot-message error-message' : `${sender}-message`;
        const messageHTML = `<div class="message ${messageClass} show"><div class="message-content"><div class="message-text">${content}</div><div class="message-meta"><span class="timestamp">${timestamp}</span>${sender === 'bot' && messageId ? `<div class="feedback-buttons ms-2"><button class="btn btn-sm btn-outline-success" onclick="chatbot.sendFeedback('${messageId}', true)">👍</button><button class="btn btn-sm btn-outline-danger" onclick="chatbot.sendFeedback('${messageId}', false)">👎</button></div>` : ''}</div></div></div>`;
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
        return messageId;
    }

    addSuggestions(suggestions) {
        // ... (esta função não precisa de alterações) ...
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer || !suggestions.length) return;
        const suggestionsHTML = suggestions.map(suggestion => `<button class="btn btn-outline-primary btn-sm me-2 mb-2" onclick="chatbot.sendQuickMessage('${suggestion}', '${suggestion}')">${suggestion}</button>`).join('');
        const suggestionContainer = `<div class="message bot-message show suggestions-message"><div class="message-content"><div class="message-text"><small class="text-muted">Sugestões:</small><br>${suggestionsHTML}</div></div></div>`;
        messagesContainer.insertAdjacentHTML('beforeend', suggestionContainer);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        // ... (esta função não precisa de alterações) ...
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        const typingHTML = `<div id="typing-indicator" class="message bot-message show"><div class="message-content"><div class="typing-animation"><span></span><span></span><span></span></div></div></div>`;
        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    async sendFeedback(messageId, helpful) {
        // ... (esta função não precisa de alterações) ...
        if (!messageId) return;
        try {
            const headers = { 'Content-Type': 'application/json', };
            if (this.csrfToken) { headers['X-CSRFToken'] = this.csrfToken; }
            const response = await fetch('/chatbot/api/feedback/', { method: 'POST', headers: headers, body: JSON.stringify({ message_id: messageId, helpful: helpful }), credentials: 'same-origin' });
            if (response.ok) {
                const feedbackButtons = document.querySelector(`[onclick*="${messageId}"]`)?.parentElement;
                if (feedbackButtons) { feedbackButtons.innerHTML = `<small class="text-success"><i class="bi bi-check-circle"></i> Obrigado pelo feedback!</small>`; }
            }
        } catch (error) { console.error('❌ Erro ao enviar feedback:', error); }
    }

    async clearConversation() {
        if (!confirm('Deseja limpar toda a conversa? Esta ação não pode ser desfeita.')) {
            return;
        }

        // ✅ CORREÇÃO 4: Ao limpar, resetar o conversationId local também.
        this.conversationId = null;

        // Limpa a UI imediatamente para uma melhor experiência do usuário
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.showWelcomeMessage();
        this.messageHistory = [];

        try {
            const headers = {};
            if (this.csrfToken) {
                headers['X-CSRFToken'] = this.csrfToken;
            }
            // Chama a API para limpar o contexto no backend (se houver alguma lógica lá)
            await fetch('/chatbot/api/clear-context/', {
                method: 'POST',
                headers: headers,
                credentials: 'same-origin'
            });
        } catch (error) {
            console.error('❌ Erro ao limpar conversa no backend:', error);
            // A UI já foi limpa, então o erro não precisa ser mostrado para o usuário
        }
    }

    loadUserSettings() {
        console.log('⚙️ Configurações do usuário carregadas:', this.userSettings);
    }

    testPersonalization() {
        console.log('🧪 Teste de personalização:', {
            userSettings: this.userSettings,
            messageHistory: this.messageHistory,
            csrfToken: this.csrfToken ? '✅ Presente' : '❌ Ausente',
            conversationId: this.conversationId // Adicionado para depuração
        });
    }
}

let chatbot;
document.addEventListener('DOMContentLoaded', function() {
    chatbot = new ChatbotEnhanced();
    console.log('🤖 Chatbot Enhanced inicializado');
});
window.chatbot = chatbot;