/**
 * Script para renomear "Core" para "Organizador" no admin
 * e fazer ajustes na interface administrativa
 */
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // 1. Renomear "Core" para "Organizador" em todos os lugares
        renameCoreToOrganizador();

        // 2. Agrupar modelos no módulo Organizador (opcional)
        // É possível desabilitar esta parte se causar problemas
        groupOrganizadorModels();
    });

    /**
     * Renomeia todas as ocorrências de "Core" para "Organizador"
     */
    function renameCoreToOrganizador() {
        // Renomear no cabeçalho dos módulos
        document.querySelectorAll('.app-core caption a.section').forEach(function(element) {
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
    }

    /**
     * Agrupa visualmente os modelos no módulo Organizador
     * Esta função não altera a estrutura do DOM, apenas adiciona estilos
     */
    function groupOrganizadorModels() {
        // Verificar se estamos na página inicial do admin
        if (!document.querySelector('.app-core')) {
            return;
        }

        // Objetos para mapeamento e categorização
        const categoryMapping = {
            // Seções
            'HomeSection': 'secoes',
            'CustomSectionType': 'secoes',
            'CustomSectionLayout': 'secoes',
            'CustomSection': 'secoes',

            // Estantes
            'DefaultShelfType': 'estantes',
            'BookShelfSection': 'estantes',

            // Prateleiras
            'BookShelfItem': 'prateleiras',

            // Outros conteúdos
            'Advertisement': 'outros',
            'VideoSection': 'outros',
            'VideoItem': 'outros',
            'LinkGridItem': 'outros',
            'Banner': 'outros',
            'EventItem': 'outros'
        };

        // As classes CSS são adicionadas via JavaScript para evitar modificar o HTML
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .model-category-secoes::before {
                content: "Seções";
                display: block;
                background-color: #f2f2f2;
                padding: 8px 10px;
                font-weight: bold;
                color: #555;
                border-bottom: 1px solid #ddd;
                text-transform: uppercase;
                font-size: 0.85em;
            }

            .model-category-estantes::before {
                content: "Estantes";
                display: block;
                background-color: #f2f2f2;
                padding: 8px 10px;
                font-weight: bold;
                color: #555;
                border-bottom: 1px solid #ddd;
                text-transform: uppercase;
                font-size: 0.85em;
                margin-top: 10px;
            }

            .model-category-prateleiras::before {
                content: "Prateleiras";
                display: block;
                background-color: #f2f2f2;
                padding: 8px 10px;
                font-weight: bold;
                color: #555;
                border-bottom: 1px solid #ddd;
                text-transform: uppercase;
                font-size: 0.85em;
                margin-top: 10px;
            }

            .model-category-outros::before {
                content: "Outros Conteúdos";
                display: block;
                background-color: #f2f2f2;
                padding: 8px 10px;
                font-weight: bold;
                color: #555;
                border-bottom: 1px solid #ddd;
                text-transform: uppercase;
                font-size: 0.85em;
                margin-top: 10px;
            }
        `;
        document.head.appendChild(styleElement);

        // Adicionar classes para cada modelo
        document.querySelectorAll('.app-core tbody tr').forEach(function(row) {
            const modelName = row.className.split('-')[1];
            if (modelName && categoryMapping[modelName]) {
                row.classList.add(`model-category-${categoryMapping[modelName]}`);
            }
        });
    }
})();