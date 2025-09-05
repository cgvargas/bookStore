// cgbookstore/static/js/profile-customization.js

class ProfileCardCustomizer {
    // Construtor da classe ProfileCardCustomizer
    constructor() {
        // Localizar o card por seletor mais específico
        this.cardElement = document.querySelector('.profile-sidebar .profile-card-v2');
        this.currentStyles = {};
        this.undoStyles = null;
        this.presets = {
            classic: {
                background_color: '#ffffff',
                text_color: '#333333',
                border_color: '#dee2e6',
                image_style: 'circle',
                hover_effect: 'translate',
                icon_style: 'default',
                border_radius: '0.5rem',
                shadow_style: 'light'
            },
            dark: {
                background_color: '#343a40',
                text_color: '#f8f9fa',
                border_color: '#495057',
                image_style: 'circle',
                hover_effect: 'glow',
                icon_style: 'filled',
                border_radius: '0.5rem',
                shadow_style: 'dark'
            },
            minimalist: {
                background_color: '#f8f9fa',
                text_color: '#212529',
                border_color: '#f8f9fa',
                image_style: 'square',
                hover_effect: 'scale',
                icon_style: 'minimal',
                border_radius: '0.25rem',
                shadow_style: 'none'
            },
            vibrant: {
                background_color: '#f0f7ff',
                text_color: '#0d6efd',
                border_color: '#c7dbff',
                image_style: 'hexagon',
                hover_effect: 'glow',
                icon_style: 'filled',
                border_radius: '1rem',
                shadow_style: 'colored'
            },
            // Temas literários adicionados
            fantasy: {
                background_color: '#2a2160',
                text_color: '#e8e4ff',
                border_color: '#9370db',
                image_style: 'hexagon',
                hover_effect: 'glow',
                icon_style: 'filled',
                border_radius: '1rem',
                shadow_style: 'colored'
            },
            scifi: {
                background_color: '#1c2331',
                text_color: '#64ffda',
                border_color: '#00b0ff',
                image_style: 'square',
                hover_effect: 'scale',
                icon_style: 'outline',
                border_radius: '0.25rem',
                shadow_style: 'dark'
            },
            romance: {
                background_color: '#fff0f5',
                text_color: '#ff69b4',
                border_color: '#ffb6c1',
                image_style: 'circle',
                hover_effect: 'translate',
                icon_style: 'filled',
                border_radius: '2rem',
                shadow_style: 'light'
            },
            horror: {
                background_color: '#1a1a1a',
                text_color: '#ff4d4d',
                border_color: '#800000',
                image_style: 'square',
                hover_effect: 'glow',
                icon_style: 'minimal',
                border_radius: '0',
                shadow_style: 'dark'
            },
            mystery: {
                background_color: '#2c3e50',
                text_color: '#f39c12',
                border_color: '#34495e',
                image_style: 'circle',
                hover_effect: 'scale',
                icon_style: 'outline',
                border_radius: '0.5rem',
                shadow_style: 'medium'
            },
            historical: {
                background_color: '#f5f5dc',
                text_color: '#8b4513',
                border_color: '#d2b48c',
                image_style: 'square',
                hover_effect: 'translate',
                icon_style: 'filled',
                border_radius: '0.25rem',
                shadow_style: 'light'
            }
        };

        // Remover quaisquer estilos CSS do tema atual para permitir customizações
        this.resetThemeStyles();

        if (this.cardElement) {
            console.log('Card de perfil encontrado, inicializando customizador');
            this.init();
        } else {
            console.error('Card element not found - profile-customization.js');
        }
    }

    // Método para remover estilos aplicados pelo tema
    resetThemeStyles() {
        // Procurar se existe style tag do tema aplicada ao card
        const existingStyles = document.querySelectorAll('style[data-theme-styles]');
        existingStyles.forEach(style => style.remove());
    }

    init() {
        this.setupCustomizeButton();
        this.loadCurrentStyles();
        this.setupPreviewHandlers();
    }

    setupCustomizeButton() {
        console.log('Configurando botão de customização...');

        // Remover botões existentes para evitar duplicações
        const existingBtns = this.cardElement.querySelectorAll('.customize-button, #card-customize-btn, #direct-customize-btn');
        existingBtns.forEach(btn => btn.remove());

        // Criar novo botão redondo com ícone de pincel
        const customizeBtn = document.createElement('button');
        customizeBtn.id = 'card-customize-btn';
        customizeBtn.className = 'customize-button';
        customizeBtn.innerHTML = '<i class="bi bi-brush"></i>';
        customizeBtn.onclick = () => this.showCustomizationModal();

        // Aplicar estilos inline para garantir visibilidade em temas claros e escuros
        Object.assign(customizeBtn.style, {
            position: 'absolute',
            top: '10px',
            right: '10px',
            zIndex: '9999',
            width: '40px',
            height: '40px',
            padding: '0',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            backgroundColor: 'rgba(13, 110, 253, 0.8)',
            border: '2px solid rgba(255, 255, 255, 0.5)',
            boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
            color: 'white',
            fontSize: '18px'
        });

        // Adicionar efeitos hover usando eventos
        customizeBtn.addEventListener('mouseenter', () => {
            customizeBtn.style.transform = 'scale(1.1)';
            customizeBtn.style.backgroundColor = 'rgba(13, 110, 253, 1)';
        });

        customizeBtn.addEventListener('mouseleave', () => {
            customizeBtn.style.transform = 'scale(1)';
            customizeBtn.style.backgroundColor = 'rgba(13, 110, 253, 0.8)';
        });

        // Garantir que o card tenha posição relativa
        this.cardElement.style.position = 'relative';

        // Adicionar o botão ao card
        this.cardElement.appendChild(customizeBtn);

        console.log('Botão de customização criado e adicionado ao card');
    }

    async loadCurrentStyles() {
        try {
            console.log('Carregando estilos do card de perfil...');
            const response = await fetch('/profile/card-style/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const stylesData = await response.json();
            console.log('Estilos carregados:', stylesData);

            // Criar um novo objeto em vez de modificar o existente
            this.currentStyles = { ...stylesData };

            // Adicionar propriedades se não existirem
            if (!this.currentStyles.border_radius) {
                this.currentStyles.border_radius = '0.5rem';
            }

            if (!this.currentStyles.shadow_style) {
                this.currentStyles.shadow_style = 'light';
            }

            this.applyStyles(this.currentStyles);
        } catch (error) {
            console.error('Erro ao carregar estilos:', error);
            // Aplicar estilo padrão em caso de erro
            this.currentStyles = { ...this.presets.classic };
            this.applyStyles(this.currentStyles);
        }
    }

    applyStyles(styles) {
        if (!styles) {
            console.error('Nenhum estilo fornecido para aplicar');
            return;
        }

        // Adicionar um ID ao card para aumentar a especificidade dos seletores CSS
        const cardId = 'profile-custom-card';
        this.cardElement.id = cardId;

        // Criar ou obter o elemento de estilo para aplicar os estilos customizados
        let styleElem = document.getElementById('profile-card-custom-styles');
        if (!styleElem) {
            styleElem = document.createElement('style');
            styleElem.id = 'profile-card-custom-styles';
            document.head.appendChild(styleElem);
        }

        // Preparar seletor CSS
        const cardSelector = `#${cardId}`;

        // Definir sombra com base no estilo selecionado
        let shadowStyle;
        switch(styles.shadow_style) {
            case 'none':
                shadowStyle = 'none';
                break;
            case 'light':
                shadowStyle = '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)';
                break;
            case 'medium':
                shadowStyle = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
                break;
            case 'dark':
                shadowStyle = '0 1rem 3rem rgba(0, 0, 0, 0.175)';
                break;
            case 'colored':
                const shadowColor = this.adjustColorOpacity(styles.border_color || '#dee2e6', 0.5);
                shadowStyle = `0 0.5rem 1rem ${shadowColor}`;
                break;
            default:
                shadowStyle = '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)';
        }

        // Definir o efeito hover
        let hoverTransform;
        switch(styles.hover_effect) {
            case 'translate':
                hoverTransform = 'translateY(-5px)';
                break;
            case 'scale':
                hoverTransform = 'scale(1.02)';
                break;
            case 'glow':
                // O efeito glow será tratado no CSS com a sombra
                hoverTransform = 'translateY(-3px)';
                break;
            case 'none':
                hoverTransform = 'none';
                break;
            default:
                hoverTransform = 'translateY(-5px)';
        }

        // Definir o estilo dos ícones
        let iconStyle = '';
        switch(styles.icon_style) {
            case 'filled':
                iconStyle = `
                    ${cardSelector} .stat-item i {
                        background-color: ${this.adjustColorOpacity(styles.text_color, 0.1)} !important;
                        padding: 8px !important;
                        border-radius: 50% !important;
                        display: inline-flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                `;
                break;
            case 'outline':
                iconStyle = `
                    ${cardSelector} .stat-item i {
                        border: 2px solid ${styles.text_color} !important;
                        padding: 6px !important;
                        border-radius: 50% !important;
                        display: inline-flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                `;
                break;
            case 'minimal':
                iconStyle = `
                    ${cardSelector} .stat-item i {
                        font-size: 1.2rem !important;
                    }
                `;
                break;
            default:
                iconStyle = '';
        }

        // Criar o CSS completo
        const css = `
            ${cardSelector} {
                background-color: ${styles.background_color} !important;
                border-color: ${styles.border_color} !important;
                border-radius: ${styles.border_radius} !important;
                box-shadow: ${shadowStyle} !important;
                transition: all 0.3s ease !important;
            }

            ${cardSelector} .card-body {
                color: ${styles.text_color} !important;
            }

            ${cardSelector} h4.card-title,
            ${cardSelector} .stat-value,
            ${cardSelector} .stat-label {
                color: ${styles.text_color} !important;
            }

            ${cardSelector} .text-muted,
            ${cardSelector} p.text-muted {
                color: ${this.adjustColorOpacity(styles.text_color, 0.6)} !important;
            }

            ${cardSelector} .stat-item i {
                color: ${styles.text_color} !important;
            }

            ${cardSelector} .btn-outline-primary {
                color: ${styles.text_color} !important;
                border-color: ${styles.text_color} !important;
            }

            ${cardSelector} .btn-outline-primary:hover {
                background-color: ${styles.text_color} !important;
                color: ${this.getContrastColor(styles.text_color)} !important;
            }

            ${cardSelector}:hover {
                transform: ${hoverTransform} !important;
                ${styles.hover_effect === 'glow' ?
                    `box-shadow: 0 0 25px ${this.adjustColorOpacity(styles.border_color, 0.4)} !important;` : ''}
            }

            ${iconStyle}
        `;

        // Aplicar classe de estilo de imagem
        const imageContainer = this.cardElement.querySelector('.profile-image');
        if (imageContainer) {
            // Remover classes existentes
            imageContainer.classList.remove('profile-image-circle', 'profile-image-square', 'profile-image-hexagon');

            // Adicionar a nova classe
            imageContainer.classList.add(`profile-image-${styles.image_style}`);

            // Adicionar regras CSS específicas para o estilo da imagem
            let imageCSS = '';

            if (styles.image_style === 'hexagon') {
                imageCSS = `
                    ${cardSelector} .profile-image-hexagon img,
                    ${cardSelector} .profile-image-hexagon .avatar-placeholder {
                        clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%) !important;
                    }
                `;
            } else if (styles.image_style === 'square') {
                imageCSS = `
                    ${cardSelector} .profile-image-square img,
                    ${cardSelector} .profile-image-square .avatar-placeholder {
                        border-radius: 0.5rem !important;
                    }
                `;
            } else {
                imageCSS = `
                    ${cardSelector} .profile-image-circle img,
                    ${cardSelector} .profile-image-circle .avatar-placeholder {
                        border-radius: 50% !important;
                    }
                `;
            }

            // Adicionar CSS de imagem ao estilo geral
            styleElem.textContent = css + imageCSS;
        } else {
            styleElem.textContent = css;
        }

        console.log('Estilos aplicados com sucesso ao card do perfil');
    }

    showCustomizationModal() {
        const modalElement = document.getElementById('customizeCardModal');
        if (!modalElement) {
            console.error('Modal element not found');
            return;
        }

        // Guardar estilos atuais para possível cancelamento
        this.undoStyles = {...this.currentStyles};

        try {
            const modal = new bootstrap.Modal(modalElement);
            this.populateModalFields();
            modal.show();
        } catch (error) {
            console.error('Erro ao mostrar modal:', error);
            alert('Houve um erro ao abrir o modal de customização. Por favor, tente novamente.');
        }
    }

    populateModalFields() {
        console.log('Populando campos do modal com os estilos atuais:', this.currentStyles);

        const fields = [
            'background_color',
            'text_color',
            'border_color',
            'image_style',
            'hover_effect',
            'icon_style',
            'border_radius',
            'shadow_style'
        ];

        fields.forEach(field => {
            const input = document.getElementById(`style_${field}`);
            if (input && this.currentStyles[field]) {
                input.value = this.currentStyles[field];
            } else if (input) {
                // Usar valores padrão do preset classic
                input.value = this.presets.classic[field] || '';
            }
        });

        // Atualizar o select de presets
        const presetSelect = document.getElementById('style_preset');
        if (presetSelect) {
            // Limpar opções existentes
            presetSelect.innerHTML = '';

            // Adicionar a opção "Personalizado"
            const customOption = document.createElement('option');
            customOption.value = 'custom';
            customOption.textContent = 'Personalizado';
            presetSelect.appendChild(customOption);

            // Adicionar opções básicas
            const basicGroup = document.createElement('optgroup');
            basicGroup.label = 'Estilos Básicos';

            const basicStyles = [
                { value: 'classic', label: 'Clássico' },
                { value: 'dark', label: 'Escuro' },
                { value: 'minimalist', label: 'Minimalista' },
                { value: 'vibrant', label: 'Vibrante' }
            ];

            basicStyles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.value;
                option.textContent = style.label;
                basicGroup.appendChild(option);
            });

            presetSelect.appendChild(basicGroup);

            // Adicionar opções de temas literários
            const literaryGroup = document.createElement('optgroup');
            literaryGroup.label = 'Temas Literários';

            const literaryStyles = [
                { value: 'fantasy', label: 'Fantasia' },
                { value: 'scifi', label: 'Ficção Científica' },
                { value: 'romance', label: 'Romance' },
                { value: 'horror', label: 'Horror' },
                { value: 'mystery', label: 'Mistério' },
                { value: 'historical', label: 'Histórico' }
            ];

            literaryStyles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.value;
                option.textContent = style.label;
                literaryGroup.appendChild(option);
            });

            presetSelect.appendChild(literaryGroup);

            // Definir a opção selecionada
            presetSelect.value = 'custom'; // Valor padrão
        }
    }

    setupPreviewHandlers() {
        // Adicionar listener para mudanças nos campos de cor
        const colorInputs = ['background_color', 'text_color', 'border_color'];
        colorInputs.forEach(field => {
            const input = document.getElementById(`style_${field}`);
            if (input) {
                input.addEventListener('input', () => {
                    this.livePreview();
                });
            }
        });

        // Adicionar listeners para selects
        const selectInputs = ['image_style', 'hover_effect', 'icon_style', 'border_radius', 'shadow_style'];
        selectInputs.forEach(field => {
            const select = document.getElementById(`style_${field}`);
            if (select) {
                select.addEventListener('change', () => {
                    this.livePreview();
                });
            }
        });

        // Adicionar listener para o select de presets
        const presetSelect = document.getElementById('style_preset');
        if (presetSelect) {
            presetSelect.addEventListener('change', () => {
                this.applyPreset(presetSelect.value);
            });
        }
    }

    livePreview() {
        // Obter valores atuais dos campos
        const previewStyles = {
            background_color: document.getElementById('style_background_color')?.value || '#ffffff',
            text_color: document.getElementById('style_text_color')?.value || '#000000',
            border_color: document.getElementById('style_border_color')?.value || '#dee2e6',
            image_style: document.getElementById('style_image_style')?.value || 'circle',
            hover_effect: document.getElementById('style_hover_effect')?.value || 'translate',
            icon_style: document.getElementById('style_icon_style')?.value || 'default',
            border_radius: document.getElementById('style_border_radius')?.value || '0.5rem',
            shadow_style: document.getElementById('style_shadow_style')?.value || 'light'
        };

        // Aplicar estilos para preview
        this.applyStyles(previewStyles);
    }

    applyPreset(presetName) {
        if (presetName === 'custom') {
            return; // Manter valores atuais
        }

        const preset = this.presets[presetName];
        if (!preset) {
            console.error('Preset não encontrado:', presetName);
            return;
        }

        console.log('Aplicando preset:', presetName, preset);

        // Preencher campos do formulário com valores do preset
        Object.keys(preset).forEach(key => {
            const input = document.getElementById(`style_${key}`);
            if (input) {
                input.value = preset[key];
            }
        });

        // Se for um tema literário, adicionar classes especiais
        const literaryThemes = ['fantasy', 'scifi', 'romance', 'horror', 'mystery', 'historical'];
        if (literaryThemes.includes(presetName) && window.profileThemes) {
            // Notificar o sistema de temas
            try {
                window.profileThemes.changeTheme(presetName);
            } catch (error) {
                console.error('Erro ao sincronizar com o sistema de temas:', error);
            }
        }

        // Atualizar preview
        this.livePreview();
    }

    // Adicionado método cancelCustomization que estava faltando
    cancelCustomization() {
        if (this.undoStyles) {
            console.log('Cancelando customização e revertendo para estilos anteriores:', this.undoStyles);
            this.applyStyles(this.undoStyles);
            this.undoStyles = null;
        }
    }

    async saveCustomization() {
        try {
            const styleData = {
                background_color: document.getElementById('style_background_color')?.value || '#ffffff',
                text_color: document.getElementById('style_text_color')?.value || '#000000',
                border_color: document.getElementById('style_border_color')?.value || '#dee2e6',
                image_style: document.getElementById('style_image_style')?.value || 'circle',
                hover_effect: document.getElementById('style_hover_effect')?.value || 'translate',
                icon_style: document.getElementById('style_icon_style')?.value || 'default',
                border_radius: document.getElementById('style_border_radius')?.value || '0.5rem',
                shadow_style: document.getElementById('style_shadow_style')?.value || 'light'
            };

            console.log('Enviando dados para salvar:', styleData);

            const response = await fetch('/profile/card-style/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(styleData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Resposta do servidor:', result);

            if (result.success) {
                this.currentStyles = result.styles || styleData;
                this.applyStyles(this.currentStyles);
                this.undoStyles = null;
                console.log('Customização salva com sucesso');
                return true;
            }
            throw new Error(result.error || 'Erro ao salvar customização');
        } catch (error) {
            console.error('Erro ao salvar customização:', error);
            return false;
        }
    }

    adjustColorOpacity(color, opacity) {
        // Converte a cor para RGB se for hexadecimal
        try {
            let r, g, b;
            if (typeof color === 'string' && color.startsWith('#')) {
                r = parseInt(color.slice(1, 3), 16);
                g = parseInt(color.slice(3, 5), 16);
                b = parseInt(color.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, ${opacity})`;
            }
            return color; // Retorna a cor original se não for hexadecimal
        } catch (error) {
            console.error('Erro ao ajustar opacidade da cor:', error);
            return color; // Retorna a cor original em caso de erro
        }
    }

    adjustColorBrightness(color, percent) {
        try {
            // Converte a cor para RGB se for hexadecimal
            let r, g, b;
            if (typeof color !== 'string' || !color.startsWith('#')) {
                return color; // Retorna a cor original se não for hexadecimal
            }

            r = parseInt(color.slice(1, 3), 16);
            g = parseInt(color.slice(3, 5), 16);
            b = parseInt(color.slice(5, 7), 16);

            // Ajustar brilho
            r = Math.max(0, Math.min(255, r + percent));
            g = Math.max(0, Math.min(255, g + percent));
            b = Math.max(0, Math.min(255, b + percent));

            // Converter de volta para hexadecimal
            return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
        } catch (error) {
            console.error('Erro ao ajustar brilho da cor:', error);
            return color; // Retorna a cor original em caso de erro
        }
    }

    syncWithThemeSystem(themeName) {
        // Este método pode ser chamado pelo sistema de temas para sincronizar
        console.log('Sincronizando customizador com o tema:', themeName);

        // Atualizar o dropdown de presets se o modal estiver aberto
        const presetSelect = document.getElementById('style_preset');
        if (presetSelect) {
            presetSelect.value = themeName;
        }

        // Aplicar o preset correspondente
        this.applyPreset(themeName);
    }

    // Adicionado método que estava no final do arquivo, mas dentro da classe
    applyThemeFromProfileThemes(themeName) {
        // Esta função permite que o sistema de temas literários aplique um preset
        if (this.presets[themeName]) {
            console.log('Aplicando preset do sistema de temas literários:', themeName);
            this.applyStyles(this.presets[themeName]);

            // Atualizar o campo de preset, se o modal estiver aberto
            const presetSelect = document.getElementById('style_preset');
            if (presetSelect) {
                presetSelect.value = themeName;
            }
        }
    }

    getContrastColor(hexColor) {
        try {
            // Converte a cor para RGB se for hexadecimal
            let r, g, b;
            if (typeof hexColor !== 'string' || !hexColor.startsWith('#')) {
                return '#ffffff'; // Retorna branco como padrão
            }

            r = parseInt(hexColor.slice(1, 3), 16);
            g = parseInt(hexColor.slice(3, 5), 16);
            b = parseInt(hexColor.slice(5, 7), 16);

            // Calcular luminância
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

            // Retornar branco ou preto com base na luminância
            return luminance > 0.5 ? '#000000' : '#ffffff';
        } catch (error) {
            console.error('Erro ao determinar cor de contraste:', error);
            return '#ffffff'; // Retorna branco em caso de erro
        }
    }

    getCsrfToken() {
        try {
            // Primeiro, tentar obter diretamente de um elemento no DOM
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
        } catch (error) {
            console.error('Erro ao obter CSRF token:', error);
            return '';
        }
    }
}

// Variável global para o customizador
let customizer;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    console.log('Inicializando customizador de card de perfil...');

    try {
        customizer = new ProfileCardCustomizer();

        // Adicionar event listener para o botão de cancelar
        const cancelBtn = document.getElementById('cancelCustomizationBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                customizer.cancelCustomization();
            });
        }

        // Inicializar tooltips em toda a página
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } catch (error) {
        console.error('Erro durante inicialização do customizador de card:', error);
    }
});

// Função global para salvar customização
async function saveCardCustomization() {
    if (!customizer) {
        showAlert('Erro: Customizador não inicializado', 'danger');
        return;
    }

    // Mostrar indicador de carregamento
    const saveBtn = document.querySelector('#customizeCardModal .btn-primary');
    if (saveBtn) {
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';
        saveBtn.disabled = true;

        try {
            const success = await customizer.saveCustomization();

            // Restaurar botão
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;

            if (success) {
                const modalElement = document.getElementById('customizeCardModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                showAlert('Card personalizado com sucesso!');
            } else {
                showAlert('Erro ao personalizar o card', 'danger');
            }
        } catch (error) {
            console.error('Erro ao salvar customização:', error);
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            showAlert('Erro ao personalizar o card: ' + error.message, 'danger');
        }
    } else {
        try {
            const success = await customizer.saveCustomization();
            if (success) {
                const modalElement = document.getElementById('customizeCardModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                showAlert('Card personalizado com sucesso!');
            } else {
                showAlert('Erro ao personalizar o card', 'danger');
            }
        } catch (error) {
            console.error('Erro ao salvar customização:', error);
            showAlert('Erro ao personalizar o card: ' + error.message, 'danger');
        }
    }
}

// Função de alerta com animação
function showAlert(message, type = 'success') {
    try {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '1050';
        alertDiv.style.transition = 'all 0.3s ease';
        alertDiv.style.transform = 'translateY(-20px)';
        alertDiv.style.opacity = '0';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);

        // Adicionar efeito de entrada
        setTimeout(() => {
            alertDiv.classList.add('show');
            alertDiv.style.transform = 'translateY(0)';
            alertDiv.style.opacity = '1';
        }, 10);

        // Remover depois de alguns segundos
        setTimeout(() => {
            alertDiv.style.transform = 'translateY(-20px)';
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }, 3000);
    } catch (error) {
        console.error('Erro ao mostrar alerta:', error);
        // Fallback para alert nativo
        alert(message);
    }
}