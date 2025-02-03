// cgbookstore/static/js/profile-customization.js

class ProfileCardCustomizer {
    constructor() {
        this.cardElement = document.querySelector('.customizable-card');
        this.currentStyles = {};
        if (this.cardElement) {
            this.init();
        } else {
            console.error('Card element not found');
        }
    }

    init() {
        this.setupCustomizeButton();
        this.loadCurrentStyles();
    }

    setupCustomizeButton() {
        const customizeBtn = document.createElement('button');
        customizeBtn.className = 'btn btn-light btn-sm customize-button';
        customizeBtn.innerHTML = '<i class="bi bi-brush"></i>';
        customizeBtn.onclick = () => this.showCustomizationModal();
        this.cardElement.appendChild(customizeBtn);
    }

    async loadCurrentStyles() {
        try {
            const response = await fetch('/profile/card-style/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.currentStyles = await response.json();
            this.applyStyles(this.currentStyles);
        } catch (error) {
            console.error('Erro ao carregar estilos:', error);
        }
    }

    applyStyles(styles) {
        if (!styles) return;

        const card = this.cardElement;
        const cardBody = card.querySelector('.card-body');

        // Aplicar cores no card e textos
        card.style.backgroundColor = styles.background_color || '#ffffff';
        cardBody.style.color = styles.text_color || '#000000';
        card.style.borderColor = styles.border_color || '#dee2e6';

        // Ajustar cor dos textos específicos incluindo @username e "Membro desde"
        const allTextElements = cardBody.querySelectorAll('h4, p, .stat-value, .stat-label, .text-muted, small');
        allTextElements.forEach(el => {
            if (el.classList.contains('text-muted')) {
                // Para elementos com text-muted, usar uma versão mais clara da cor do texto
                const color = styles.text_color || '#000000';
                el.style.color = this.adjustColorOpacity(color, 0.6);
            } else {
                el.style.color = styles.text_color || '#000000';
            }
            // Garantir que o estilo seja aplicado também ao conteúdo dentro do elemento
            const childElements = el.querySelectorAll('*');
            childElements.forEach(child => {
                if (child.classList.contains('text-muted')) {
                    const color = styles.text_color || '#000000';
                    child.style.color = this.adjustColorOpacity(color, 0.6);
                } else {
                    child.style.color = styles.text_color || '#000000';
                }
            });
        });

        // Aplicar cor ao texto do username
        const usernameText = cardBody.querySelector('p.text-muted');
        if (usernameText) {
            usernameText.style.setProperty('color', this.adjustColorOpacity(styles.text_color || '#000000', 0.6), 'important');
        }

        // Aplicar cor ao texto "Membro desde"
        const memberSinceText = cardBody.querySelector('small');
        if (memberSinceText) {
            memberSinceText.parentElement.style.setProperty('color', this.adjustColorOpacity(styles.text_color || '#000000', 0.6), 'important');
        }

        // Aplicar estilo da imagem
        const imageContainer = card.querySelector('.profile-image');
        if (imageContainer) {
            imageContainer.className = `profile-image mb-3 profile-image-${styles.image_style || 'circle'}`;
        }

        // Aplicar efeito hover
        card.className = `card customizable-card hover-effect-${styles.hover_effect || 'translate'}`;

        // Aplicar estilo dos ícones
        const icons = card.querySelectorAll('.stat-item i');
        icons.forEach(icon => {
            icon.className = `bi ${icon.className.split(' ')[1]} icon-style-${styles.icon_style || 'default'}`;
            icon.style.color = styles.text_color || '#000000';
        });
    }

    showCustomizationModal() {
        const modalElement = document.getElementById('customizeCardModal');
        if (!modalElement) {
            console.error('Modal element not found');
            return;
        }
        const modal = new bootstrap.Modal(modalElement);
        this.populateModalFields();
        modal.show();
    }

    populateModalFields() {
        const fields = [
            'background_color',
            'text_color',
            'border_color',
            'image_style',
            'hover_effect',
            'icon_style'
        ];

        fields.forEach(field => {
            const input = document.getElementById(`style_${field}`);
            if (input && this.currentStyles[field]) {
                input.value = this.currentStyles[field];
            }
        });
    }

    async saveCustomization() {
        try {
            const styleData = {
                background_color: document.getElementById('style_background_color')?.value || '#ffffff',
                text_color: document.getElementById('style_text_color')?.value || '#000000',
                border_color: document.getElementById('style_border_color')?.value || '#dee2e6',
                image_style: document.getElementById('style_image_style')?.value || 'circle',
                hover_effect: document.getElementById('style_hover_effect')?.value || 'translate',
                icon_style: document.getElementById('style_icon_style')?.value || 'default'
            };

            console.log('Enviando dados:', styleData); // Debug

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

            if (result.success) {
                this.currentStyles = result.styles;
                this.applyStyles(this.currentStyles);
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
        let r, g, b;
        if (color.startsWith('#')) {
            r = parseInt(color.slice(1, 3), 16);
            g = parseInt(color.slice(3, 5), 16);
            b = parseInt(color.slice(5, 7), 16);
        } else {
            return color; // Retorna a cor original se não for hexadecimal
        }

        // Retorna a cor com opacidade
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }

    getCsrfToken() {
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

// Variável global para o customizador
let customizer;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    customizer = new ProfileCardCustomizer();
});

// Função global para salvar customização
async function saveCardCustomization() {
    if (!customizer) {
        showAlert('Erro: Customizador não inicializado', 'danger');
        return;
    }

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
}

// Função de alerta
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}