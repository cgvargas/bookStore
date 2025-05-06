/**
 * Script para barra lateral de navegação no Admin Django
 * Versão: 3.0
 */

'use strict';
{
    document.addEventListener('DOMContentLoaded', function() {
        // Primeiro declarar as variáveis, depois usá-las
        const toggleNavSidebar = document.getElementById('toggle-nav-sidebar');
        const navSidebar = document.getElementById('nav-sidebar');
        const content = document.getElementById('content');

        // Depois de declarar as variáveis, podemos usá-las
        if (toggleNavSidebar) {
            // Garantir que o botão esteja visível
            toggleNavSidebar.style.display = 'flex';
            toggleNavSidebar.style.visibility = 'visible';
            toggleNavSidebar.style.opacity = '1';
        }

        if (toggleNavSidebar !== null && navSidebar !== null) {
            let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');

            // Função para atualizar o botão toggle
            function updateToggleButton() {
                if (navSidebar.classList.contains('hidden')) {
                    // Para barra lateral oculta - aplicar estilos com força total
                    toggleNavSidebar.style.cssText = 'position: fixed !important; display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 1001 !important; left: 10px !important; top: 120px !important; background-color: rgba(54, 153, 255, 0.9) !important; border-radius: 4px !important; transform: rotate(180deg) !important;';
                } else {
                    // Para barra lateral visível - aplicar estilos com força total
                    toggleNavSidebar.style.cssText = 'position: fixed !important; display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 1001 !important; left: 240px !important; top: 120px !important; background-color: transparent !important; transform: rotate(0deg) !important;';
                }
            }

            // Função para configurar estado inicial
            function setInitialState() {
                if (navSidebarIsOpen === null) {
                    // Definir valor inicial baseado na largura da viewport
                    const viewportWidth = window.innerWidth;
                    navSidebarIsOpen = viewportWidth > 767 ? 'true' : 'false';
                    localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
                }

                // Aplicar estado inicial
                if (navSidebarIsOpen === 'true') {
                    navSidebar.classList.remove('hidden');
                    if (content) content.style.marginLeft = 'var(--nav-sidebar-width, 280px)';
                    if (toggleNavSidebar) toggleNavSidebar.style.left = '240px';
                } else {
                    navSidebar.classList.add('hidden');
                    if (content) content.style.marginLeft = '0';
                    if (toggleNavSidebar) toggleNavSidebar.style.left = '10px';
                }

                // Atualizar o botão depois de configurar o estado inicial
                updateToggleButton();
            }

            // Configurar estado inicial ao carregar a página
            setInitialState();

            // APENAS UM evento para toggle da barra (removido o segundo event listener)
            toggleNavSidebar.addEventListener('click', function() {
                if (navSidebar.classList.contains('hidden')) {
                    navSidebar.classList.remove('hidden');
                    if (content) content.style.marginLeft = 'var(--nav-sidebar-width, 280px)';
                    localStorage.setItem('django.admin.navSidebarIsOpen', 'true');
                    localStorage.removeItem('django.admin.userClosedSidebar');
                } else {
                    navSidebar.classList.add('hidden');
                    if (content) content.style.marginLeft = '0';
                    localStorage.setItem('django.admin.navSidebarIsOpen', 'false');
                    localStorage.setItem('django.admin.userClosedSidebar', 'true');
                }

                // Atualiza o botão depois de mudar o estado
                updateToggleButton();
            });

            // Adiciona evento para fechar automaticamente em telas pequenas quando um link é clicado
            if (window.innerWidth <= 767) {
                const navLinks = navSidebar.querySelectorAll('a');
                navLinks.forEach(link => {
                    link.addEventListener('click', function() {
                        navSidebar.classList.add('hidden');
                        if (content) content.style.marginLeft = '0';
                        localStorage.setItem('django.admin.navSidebarIsOpen', 'false');

                        // Atualizar o botão após fechar a barra
                        updateToggleButton();
                    });
                });
            }

            // Função para ajustar a barra lateral em caso de mudança de tamanho da janela
            function handleResize() {
                const isUserClosed = localStorage.getItem('django.admin.userClosedSidebar') === 'true';

                if (window.innerWidth <= 767) {
                    // Em telas pequenas, fechar barra lateral por padrão ao redimensionar
                    navSidebar.classList.add('hidden');
                    if (content) content.style.marginLeft = '0';
                    localStorage.setItem('django.admin.navSidebarIsOpen', 'false');
                } else if (window.innerWidth > 767 && !isUserClosed) {
                    // Em telas grandes, reabrir se não foi fechada explicitamente pelo usuário
                    navSidebar.classList.remove('hidden');
                    if (content) content.style.marginLeft = 'var(--nav-sidebar-width, 280px)';
                    localStorage.setItem('django.admin.navSidebarIsOpen', 'true');
                }

                // Atualizar o botão após redimensionar
                updateToggleButton();
            }

            // Adicionar evento de redimensionamento
            window.addEventListener('resize', handleResize);

            // Garantir que todas as linhas tenham fundo preto
            setTimeout(function() {
                // Garantir que todas as linhas tenham fundo preto
                const allElements = document.querySelectorAll('#nav-sidebar *:not(caption):not(caption a)');
                allElements.forEach(function(el) {
                    el.style.backgroundColor = '#121212';
                    el.style.border = 'none';
                    el.style.boxShadow = 'none';
                    el.style.borderRadius = '0';
                });

                // Garantir que todos os links tenham primeira letra maiúscula
                const navLinks = document.querySelectorAll('#nav-sidebar th a');
                navLinks.forEach(function(link) {
                    const text = link.textContent.trim();
                    if (text) {
                        // Capitalizar primeira letra de cada palavra
                        link.textContent = text.split(' ').map(word =>
                            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                        ).join(' ');
                    }
                });

                // Aplicar borda branca aos módulos
                const appModules = document.querySelectorAll('.app-module');
                appModules.forEach(function(module) {
                    module.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                    module.style.borderRadius = '4px';
                    module.style.marginBottom = '8px';
                });
            }, 100);
        }
    });
}