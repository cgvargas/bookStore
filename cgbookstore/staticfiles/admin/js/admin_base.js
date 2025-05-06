/**
 * CGBookStore Admin Theme JavaScript
 * Este arquivo consolida as funcionalidades JavaScript necessárias para o admin
 * Version: 1.0
 */

(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // Verifica se estamos na página de admin
        if (!document.querySelector('#container')) return;

        // 1. Renomear "Core" para "Organizador" em todos os lugares
        renameCoreToOrganizador();

        // 2. Corrigir problema de contraste e texto branco em fundo branco
        fixTextContrast();

        // 3. Melhorar a estrutura de cards e elementos de UI
        enhanceUIElements();

        // 4. Aplicar classes para responsividade e alinhamento correto
        applyResponsiveClasses();

        // 5. Reordena os cards no dashboard se necessário
        reorderAdminCards();
    });

    /**
     * Renomeia todas as ocorrências de "Core" para "Organizador"
     */
    function renameCoreToOrganizador() {
        // Renomear no cabeçalho dos módulos
        document.querySelectorAll('.app-core caption a.section, .app-core .section').forEach(function(element) {
            if (element.textContent.trim() === 'Core') {
                element.textContent = 'Organizador';
            }
        });

        // Renomear nas breadcrumbs
        document.querySelectorAll('.breadcrumbs a').forEach(function(link) {
            if (link.textContent.trim() === 'Core') {
                link.textContent = 'Organizador';
            }
        });

        // Renomear no título da página
        if (document.title.includes('Core')) {
            document.title = document.title.replace('Core', 'Organizador');
        }

        // Renomear em outros elementos possíveis
        document.querySelectorAll('*').forEach(function(el) {
            if (el.childNodes && el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                if (el.childNodes[0].textContent.trim() === 'Core') {
                    el.childNodes[0].textContent = 'Organizador';
                }
            }
        });
    }

    /**
     * Corrige problemas de contraste de texto
     */
    function fixTextContrast() {
        // Verifica elementos que podem ter texto branco em fundo branco
        const elementsToCheck = [
            'p', 'label', 'div', 'span', 'li', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ];

        elementsToCheck.forEach(tag => {
            document.querySelectorAll(tag).forEach(element => {
                const style = window.getComputedStyle(element);
                const bgColor = style.backgroundColor;
                const color = style.color;

                // Se o fundo for claro e o texto for branco/muito claro
                if (
                    (bgColor.includes('rgb(255, 255, 255)') ||
                     bgColor.includes('rgba(255, 255, 255') ||
                     bgColor.includes('rgb(250, 250, 250)') ||
                     bgColor === 'white') &&
                    (color.includes('rgb(255, 255, 255)') ||
                     color.includes('rgba(255, 255, 255') ||
                     color === 'white')
                ) {
                    // Aplicar cor de texto escura para garantir visibilidade
                    element.style.color = '#333333';
                }
            });
        });

        // Fixar problemas de visibilidade em inputs
        document.querySelectorAll('input, select, textarea').forEach(input => {
            const style = window.getComputedStyle(input);
            if (style.backgroundColor === 'white' || style.backgroundColor.includes('rgb(255, 255, 255)')) {
                input.style.color = '#333333';
            }
        });
    }

    /**
     * Melhora a estrutura de elementos da UI
     */
    function enhanceUIElements() {
        // Melhorar aparência de tabelas
        document.querySelectorAll('table').forEach(table => {
            if (!table.classList.contains('enhanced')) {
                table.classList.add('enhanced');

                // Garantir que tabelas tenham largura completa
                if (!table.style.width) {
                    table.style.width = '100%';
                }

                // Garantir espaçamento correto em células
                table.querySelectorAll('td, th').forEach(cell => {
                    if (!cell.style.padding) {
                        cell.style.padding = '8px 12px';
                    }
                });
            }
        });

        // Melhorar aparência de módulos e cards
        document.querySelectorAll('.module').forEach(module => {
            if (!module.classList.contains('enhanced')) {
                module.classList.add('enhanced');

                // Garantir que módulos tenham padding adequado
                if (window.getComputedStyle(module).padding === '0px') {
                    module.style.padding = '0'; // Reseta padding para usar o do tema
                }

                // Garantir overflow adequado
                module.style.overflow = 'hidden';
            }
        });

        // Melhorar aparência de botões
        document.querySelectorAll('.button, input[type="submit"], input[type="button"]').forEach(button => {
            if (!button.classList.contains('enhanced')) {
                button.classList.add('enhanced');
                button.style.margin = '2px';
            }
        });
    }

    /**
     * Aplica classes para melhorar responsividade
     */
    function applyResponsiveClasses() {
        // Adiciona wrapper para conteúdo em telas pequenas
        const contentMain = document.getElementById('content-main');
        if (contentMain && !contentMain.classList.contains('responsive-ready')) {
            contentMain.classList.add('responsive-ready');

            // Verificar se estamos na página inicial do admin
            if (document.querySelector('.dashboard') || document.querySelector('#content-main .module')) {
                // Ajustar layout para grid em telas grandes, ou blocos em telas pequenas
                contentMain.style.display = 'grid';
                contentMain.style.gridTemplateColumns = 'repeat(auto-fill, minmax(350px, 1fr))';
                contentMain.style.gap = '20px';
                contentMain.style.padding = '20px';

                // Adicionar media query inline para dispositivos móveis
                if (!document.querySelector('#responsive-rules')) {
                    const style = document.createElement('style');
                    style.id = 'responsive-rules';
                    style.textContent = `
                        @media (max-width: 767px) {
                            #content-main {
                                display: block !important;
                                padding: 10px !important;
                            }

                            #content-main .module {
                                margin-bottom: 15px !important;
                            }

                            .form-row {
                                padding: 8px !important;
                            }

                            .submit-row {
                                padding: 10px !important;
                                text-align: center !important;
                            }

                            .submit-row a.deletelink {
                                display: block !important;
                                margin: 5px auto !important;
                            }
                        }
                    `;
                    document.head.appendChild(style);
                }
            }
        }
    }

    /**
     * Reordena cards no dashboard de admin
     */
    function reorderAdminCards() {
        // Verifica se estamos na página inicial do admin
        if (!document.querySelector('#content-main')) return;

        const contentMain = document.querySelector('#content-main');

        // Identificar os módulos/cards
        const coreModule = document.querySelector('.app-core');
        const authModule = document.querySelector('.app-auth');
        const systemTools = document.querySelector('.system-tools');

        // Se encontrou os elementos necessários, reorganiza
        if (coreModule && authModule) {
            // 1. Colocar o card de autenticação ao lado do Organizador
            if (coreModule.nextSibling !== authModule) {
                contentMain.insertBefore(authModule, coreModule.nextSibling);
            }
        }

        // 2. Posicionar Ferramentas do Sistema abaixo de autenticação
        if (authModule && systemTools) {
            // Verificar se já está em ordem correta
            if (systemTools.previousSibling !== authModule) {
                // Mover para depois da autenticação
                contentMain.insertBefore(systemTools, authModule.nextSibling);
            }
        }
    }
})();