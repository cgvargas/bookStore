// theme-switcher.js (VERSÃO REATORADA)
document.addEventListener('DOMContentLoaded', function () {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;

    function applyTheme(theme) {
        // Se o tema for 'auto', detecta o sistema
        if (theme === 'auto') {
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            htmlElement.setAttribute('data-theme', systemPrefersDark ? 'dark' : 'light');
        } else {
            htmlElement.setAttribute('data-theme', theme);
        }
        // Atualiza o ícone do botão
        updateUI(theme);
    }

    function setTheme(theme) {
        localStorage.setItem('theme', theme);
        applyTheme(theme);
    }

    function updateUI(theme) {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (!icon) return;

        icon.className = 'bi'; // Limpa classes existentes
        switch (theme) {
            case 'light':
                icon.classList.add('bi-sun-fill');
                themeToggle.setAttribute('title', 'Tema Claro');
                break;
            case 'dark':
                icon.classList.add('bi-moon-fill');
                themeToggle.setAttribute('title', 'Tema Escuro');
                break;
            default: // auto
                icon.classList.add('bi-circle-half');
                themeToggle.setAttribute('title', 'Tema do Sistema');
                break;
        }
    }

    // Evento de clique no botão
    if (themeToggle) {
        themeToggle.addEventListener('click', function (e) {
            e.preventDefault();
            const themes = ['auto', 'light', 'dark'];
            const currentTheme = localStorage.getItem('theme') || 'auto';
            const nextThemeIndex = (themes.indexOf(currentTheme) + 1) % themes.length;
            setTheme(themes[nextThemeIndex]);
        });
    }

    // Ouve mudanças no tema do sistema operacional
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (localStorage.getItem('theme') === 'auto') {
            applyTheme('auto');
        }
    });

    // Aplica o tema inicial ao carregar a página
    // (Ainda melhorado no Passo 5)
    const savedTheme = localStorage.getItem('theme') || 'auto';
    applyTheme(savedTheme);
});