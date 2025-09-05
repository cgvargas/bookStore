// profile-card-themes.js
// Sistema de temas personalizados baseados em gêneros literários para o card de perfil

class ProfileCardThemes {
    constructor() {
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.currentTheme = 'default';
        this.themeData = {};

        // Definição dos temas baseados em gêneros literários
        this.themes = {
            default: {
                name: 'Padrão',
                icon: 'bi-circle',
                styles: {} // O tema padrão usa as configurações salvas pelo usuário
            },
            fantasy: {
                name: 'Fantasia',
                icon: 'bi-magic',
                styles: {
                    background_color: '#2a2160',
                    text_color: '#e8e4ff',
                    border_color: '#9370db',
                    image_style: 'hexagon',
                    hover_effect: 'glow',
                    icon_style: 'filled',
                    border_radius: '1rem',
                    shadow_style: 'colored',
                    background_image: 'gradient-stars',
                    font_family: 'fantasy-serif'
                }
            },
            scifi: {
                name: 'Ficção Científica',
                icon: 'bi-stars',
                styles: {
                    background_color: '#1c2331',
                    text_color: '#64ffda',
                    border_color: '#00b0ff',
                    image_style: 'square',
                    hover_effect: 'scale',
                    icon_style: 'outline',
                    border_radius: '0.25rem',
                    shadow_style: 'dark',
                    background_image: 'tech-circuit',
                    font_family: 'tech-mono'
                }
            },
            romance: {
                name: 'Romance',
                icon: 'bi-heart',
                styles: {
                    background_color: '#fff0f5',
                    text_color: '#ff69b4',
                    border_color: '#ffb6c1',
                    image_style: 'circle',
                    hover_effect: 'translate',
                    icon_style: 'filled',
                    border_radius: '2rem',
                    shadow_style: 'light',
                    background_image: 'soft-flowers',
                    font_family: 'elegant-serif'
                }
            },
            horror: {
                name: 'Horror',
                icon: 'bi-moon-stars-fill',
                styles: {
                    background_color: '#1a1a1a',
                    text_color: '#ff4d4d',
                    border_color: '#800000',
                    image_style: 'square',
                    hover_effect: 'glow',
                    icon_style: 'minimal',
                    border_radius: '0',
                    shadow_style: 'dark',
                    background_image: 'spooky-fog',
                    font_family: 'gothic-serif'
                }
            },
            mystery: {
                name: 'Mistério',
                icon: 'bi-question-circle',
                styles: {
                    background_color: '#2c3e50',
                    text_color: '#f39c12',
                    border_color: '#34495e',
                    image_style: 'circle',
                    hover_effect: 'scale',
                    icon_style: 'outline',
                    border_radius: '0.5rem',
                    shadow_style: 'medium',
                    background_image: 'subtle-pattern',
                    font_family: 'detective-serif'
                }
            },
            historical: {
                name: 'Histórico',
                icon: 'bi-book',
                styles: {
                    background_color: '#f5f5dc',
                    text_color: '#8b4513',
                    border_color: '#d2b48c',
                    image_style: 'square',
                    hover_effect: 'translate',
                    icon_style: 'filled',
                    border_radius: '0.25rem',
                    shadow_style: 'light',
                    background_image: 'old-paper',
                    font_family: 'antique-serif'
                }
            }
        };

        if (this.cardElement) {
            this.init();
        } else {
            console.error('Card de perfil não encontrado para sistema de temas');
        }
    }

    init() {
        // Carregar tema salvo, se houver
        this.loadSavedTheme();

        // Criar o seletor de temas
        this.createThemeSelector();

        // Carregar os estilos dos temas literários
        this.loadThemeStyles();
    }

    loadThemeStyles() {
        // Adicionar CSS adicional para os temas
        const styleElement = document.getElementById('profile-card-theme-styles');

        if (!styleElement) {
            const newStyleElement = document.createElement('style');
            newStyleElement.id = 'profile-card-theme-styles';

            newStyleElement.textContent = this.generateThemeCSS();

            document.head.appendChild(newStyleElement);
        }
    }

    async loadSavedTheme() {
        try {
            // Tentar carregar o tema salvo do usuário
            const response = await fetch('/profile/card-theme/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.themeData = await response.json();
            console.log('Tema carregado:', this.themeData);

            // Definir o tema atual com base nos dados carregados
            if (this.themeData.theme_name && this.themes[this.themeData.theme_name]) {
                this.currentTheme = this.themeData.theme_name;

                // Aplicar o tema
                this.applyTheme(this.currentTheme);
            }
        } catch (error) {
            console.error('Erro ao carregar tema:', error);
            // Usar o tema padrão
            this.currentTheme = 'default';
        }
    }

    createThemeSelector() {
        // Verificar se o seletor já existe e remover se estiver presente
        const existingSelector = this.cardElement.querySelector('.theme-selector');
        if (existingSelector) {
            existingSelector.remove();
        }

        // Não criar novo seletor no card, já que queremos removê-lo
        console.log('Seletor de temas removido do card de perfil');

        // Não criar nenhum dropdown ou elementos visuais no card
    }

    applyTheme(themeName) {
        if (!this.cardElement) return;

        // Remover classes de temas anteriores
        Object.keys(this.themes).forEach(key => {
            this.cardElement.classList.remove(`theme-${key}`);
        });

        // Adicionar a classe do tema atual
        if (themeName !== 'default') {
            this.cardElement.classList.add(`theme-${themeName}`);
            document.documentElement.classList.add(`theme-${themeName}`);
        } else {
            // Remover todas as classes de tema do HTML
            Object.keys(this.themes).forEach(key => {
                document.documentElement.classList.remove(`theme-${key}`);
            });
        }

        // Se não for o tema padrão, aplicar os estilos do tema
        if (themeName !== 'default') {
            const theme = this.themes[themeName];

            // Aplicar estilos específicos para cada tema
            const styleElement = document.getElementById('theme-specific-styles');
            if (!styleElement) {
                const newStyleElement = document.createElement('style');
                newStyleElement.id = 'theme-specific-styles';
                document.head.appendChild(newStyleElement);
            }

            // Adicionar estilos CSS específicos baseados no tema
            if (themeName === 'fantasy') {
                document.getElementById('theme-specific-styles').textContent = `
                    #profile-custom-card.theme-fantasy {
                        background-image: linear-gradient(to bottom right, #2a2160, #4b369b) !important;
                        position: relative !important;
                        overflow: hidden !important;
                    }
                    #profile-custom-card.theme-fantasy::before {
                        content: "" !important;
                        position: absolute !important;
                        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
                        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='10' cy='10' r='1' fill='white' opacity='0.3'/%3E%3Ccircle cx='25' cy='25' r='0.5' fill='white' opacity='0.2'/%3E%3Ccircle cx='40' cy='15' r='0.75' fill='white' opacity='0.3'/%3E%3C/svg%3E") !important;
                        z-index: 0 !important;
                        opacity: 0.3;
                    }
                    .theme-fantasy #profile-custom-card * {
                        font-family: 'Luminari', 'Georgia', fantasy, serif !important;
                    }
                `;
            } else if (themeName === 'scifi') {
                document.getElementById('theme-specific-styles').textContent = `
                    #profile-custom-card.theme-scifi {
                        background: #1c2331 !important;
                        position: relative !important;
                        overflow: hidden !important;
                    }
                    #profile-custom-card.theme-scifi::before {
                        content: "" !important;
                        position: absolute !important;
                        top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
                        background-image: radial-gradient(circle at 10% 20%, rgba(6, 190, 182, 0.2) 0%, transparent 20%),
                            radial-gradient(circle at 80% 40%, rgba(0, 176, 255, 0.2) 0%, transparent 20%) !important;
                        z-index: 0 !important;
                    }
                    .theme-scifi #profile-custom-card * {
                        font-family: 'Courier New', 'Monaco', monospace !important;
                    }
                `;
            }
            // Adicione condições para os outros temas...

            // Buscar a interface de customização do card
            if (window.customizer && theme.styles) {
                window.customizer.applyStyles(theme.styles);
            }
        } else {
            // Limpar estilos específicos se voltar ao tema padrão
            const styleElement = document.getElementById('theme-specific-styles');
            if (styleElement) {
                styleElement.textContent = '';
            }

            // Voltar para o estilo padrão do usuário
            if (window.customizer && this.themeData.default_styles) {
                window.customizer.applyStyles(this.themeData.default_styles);
            }
        }
    }

    async changeTheme(themeName) {
        if (!this.themes[themeName]) {
            console.error(`Tema '${themeName}' não encontrado`);
            return;
        }

        try {
            console.log(`Alterando para o tema: ${themeName}`);

            // Atualizar tema atual
            this.currentTheme = themeName;

            // Aplicar o tema
            this.applyTheme(themeName);

            // Não é mais necessário atualizar a interface do dropdown, já que ele foi removido
            // this.updateThemeUI();

            // Tentar salvar o tema no servidor
            try {
                await this.saveTheme(themeName);
            } catch (error) {
                console.warn('Não foi possível salvar o tema no servidor, mas o tema foi aplicado localmente:', error);
                // Não mostrar mensagem de erro para o usuário, já que o tema foi aplicado com sucesso localmente
            }

        } catch (error) {
            console.error('Erro ao alterar tema:', error);
        }
    }

    updateThemeUI() {
        // Atualizar o dropdown - marcar o item ativo
        const dropdownItems = this.cardElement.querySelectorAll('.theme-option');

        dropdownItems.forEach(item => {
            const itemTheme = item.getAttribute('data-theme');

            if (itemTheme === this.currentTheme) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    async saveTheme(themeName) {
        // Salvar o tema selecionado pelo usuário
        try {
            const response = await fetch('/profile/card-theme/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    theme_name: themeName
                })
            });

            if (!response.ok) {
                // Em vez de lançar um erro, apenas registramos e retornamos
                console.warn(`Resposta HTTP não-ok ao salvar tema: ${response.status}`);
                return { success: false, local: true };
            }

            const result = await response.json();
            return result;

        } catch (error) {
            console.warn('Erro ao salvar tema (provavelmente endpoint não implementado):', error);
            return { success: false, local: true };
        }
    }

    generateThemeCSS() {
        // Gerar o CSS para os fundos personalizados e fontes dos temas
        return `
            /* Estilos de fundo para temas */
            #profile-custom-card.theme-fantasy {
                background-image: linear-gradient(to bottom right, #2a2160, #4b369b) !important;
                background-size: cover !important;
                position: relative !important;
                overflow: hidden !important;
            }

            /* Outros estilos CSS para os temas */
            /* Pode ser um CSS simplificado */

            .theme-fantasy #profile-custom-card * {
                font-family: 'Luminari', 'Georgia', fantasy, serif !important;
            }

            .theme-scifi #profile-custom-card * {
                font-family: 'Courier New', 'Monaco', monospace !important;
            }

            .theme-romance #profile-custom-card * {
                font-family: 'Snell Roundhand', 'Brush Script MT', cursive !important;
            }

            .theme-horror #profile-custom-card * {
                font-family: 'Chiller', 'Copperplate Gothic', serif !important;
            }

            .theme-mystery #profile-custom-card * {
                font-family: 'Century Gothic', 'Futura', sans-serif !important;
            }

            .theme-historical #profile-custom-card * {
                font-family: 'Baskerville', 'Garamond', serif !important;
            }
        `;
    }

    showNotification(message, type = 'info') {
        // Criar uma notificação temporária
        const notificationElement = document.createElement('div');
        notificationElement.className = `theme-notification theme-notification-${type}`;
        notificationElement.textContent = message;

        // Adicionar ao documento
        document.body.appendChild(notificationElement);

        // Adicionar classe para animar a entrada
        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 10);

        // Remover após alguns segundos
        setTimeout(() => {
            notificationElement.classList.remove('show');
            setTimeout(() => {
                notificationElement.remove();
            }, 300);
        }, 3000);
    }

    getCsrfToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }

        // Fallback para cookie
        const name = 'csrftoken';
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
}

// Inicializar o sistema de temas
document.addEventListener('DOMContentLoaded', () => {
    try {
        const profileThemes = new ProfileCardThemes();

        // Expor para debugging e para integração com o customizador existente
        window.profileThemes = profileThemes;
    } catch (error) {
        console.error('Erro ao inicializar sistema de temas:', error);
    }
});