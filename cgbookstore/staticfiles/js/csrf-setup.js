// csrf-setup-improved.js
// Solução robusta para problemas de CSRF

(function() {
    'use strict';

    // Função para obter o CSRF token de várias fontes
    function getCSRFToken() {
        // Método 1: Cookie
        let token = getCookieValue('csrftoken');
        if (token) {
            console.log('🔐 CSRF token obtido do cookie:', token.substring(0, 10) + '...');
            return token;
        }

        // Método 2: Meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            token = metaTag.getAttribute('content');
            console.log('🔐 CSRF token obtido da meta tag:', token.substring(0, 10) + '...');
            return token;
        }

        // Método 3: Input hidden (formulários)
        const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (hiddenInput) {
            token = hiddenInput.value;
            console.log('🔐 CSRF token obtido do input hidden:', token.substring(0, 10) + '...');
            return token;
        }

        console.error('❌ Nenhum CSRF token encontrado!');
        return null;
    }

    // Função para obter valor do cookie
    function getCookieValue(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Função para renovar o CSRF token
    async function renewCSRFToken() {
        try {
            console.log('🔄 Renovando CSRF token...');

            const response = await fetch('/csrf-token/', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.csrf_token) {
                    // Atualizar cookie manualmente se necessário
                    document.cookie = `csrftoken=${data.csrf_token}; path=/`;
                    console.log('✅ CSRF token renovado com sucesso');
                    return data.csrf_token;
                }
            }
        } catch (error) {
            console.error('❌ Erro ao renovar CSRF token:', error);
        }
        return null;
    }

    // Configurar CSRF para jQuery (se disponível)
    if (window.jQuery) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!this.crossDomain && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !settings.url.match(/^https?:/)) {
                    const token = getCSRFToken();
                    if (token) {
                        xhr.setRequestHeader("X-CSRFToken", token);
                    }
                }
            }
        });
        console.log('✅ CSRF configurado para jQuery');
    }

    // Configurar CSRF para fetch API
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Verificar se é uma requisição POST/PUT/DELETE para URLs internas
        const method = (options.method || 'GET').toUpperCase();
        const isInternal = !url.match(/^https?:\/\//);
        const needsCSRF = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method);

        if (isInternal && needsCSRF) {
            const token = getCSRFToken();
            if (token) {
                options.headers = options.headers || {};
                options.headers['X-CSRFToken'] = token;
                console.log('🔐 CSRF token adicionado ao fetch para:', method, url);
            }

            // Garantir que as credenciais sejam enviadas
            if (!options.credentials) {
                options.credentials = 'same-origin';
            }
        }

        return originalFetch(url, options);
    };

    // Interceptar erros 403 e tentar renovar o token
    window.addEventListener('unhandledrejection', async function(event) {
        if (event.reason && event.reason.status === 403) {
            console.log('🔄 Erro 403 detectado, tentando renovar CSRF token...');
            const newToken = await renewCSRFToken();
            if (newToken) {
                console.log('✅ Token renovado, você pode tentar a operação novamente');
            }
        }
    });

    // Função global para verificar e renovar token manualmente
    window.checkCSRFToken = function() {
        const token = getCSRFToken();
        if (!token) {
            console.log('❌ Token não encontrado, tentando renovar...');
            return renewCSRFToken();
        } else {
            console.log('✅ Token CSRF válido encontrado');
            return Promise.resolve(token);
        }
    };

    // Função para atualizar todos os formulários com o novo token
    function updateAllForms(newToken) {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            let csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                csrfInput.value = newToken;
            } else {
                // Criar input se não existir
                csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = newToken;
                form.appendChild(csrfInput);
            }
        });
        console.log(`✅ ${forms.length} formulários atualizados com novo token`);
    }

    // Verificar token periodicamente (opcional)
    function startTokenCheck() {
        setInterval(async () => {
            const token = getCSRFToken();
            if (!token) {
                console.log('⚠️ Token CSRF perdido, renovando...');
                const newToken = await renewCSRFToken();
                if (newToken) {
                    updateAllForms(newToken);
                }
            }
        }, 5 * 60 * 1000); // Verificar a cada 5 minutos
    }

    // Inicializar quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔐 Sistema CSRF robusto inicializado');
        const token = getCSRFToken();
        if (token) {
            console.log('✅ CSRF token inicial encontrado');
        } else {
            console.log('⚠️ CSRF token inicial não encontrado');
            renewCSRFToken().then(newToken => {
                if (newToken) {
                    updateAllForms(newToken);
                }
            });
        }

        // Iniciar verificação periódica (opcional)
        // startTokenCheck();
    });

    // Função para debug - use no console se necessário
    window.csrfDebug = function() {
        console.log('=== DEBUG CSRF ===');
        console.log('Cookie:', getCookieValue('csrftoken'));
        console.log('Meta tag:', document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'));
        console.log('Hidden input:', document.querySelector('input[name="csrfmiddlewaretoken"]')?.value);
        console.log('==================');
    };

})();