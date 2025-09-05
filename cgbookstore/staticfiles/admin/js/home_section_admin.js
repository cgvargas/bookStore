// Arquivo: cgbookstore/static/admin/js/home_section_admin.js
// VERSÃO FINAL COMPLETA COM TODAS AS OPÇÕES

document.addEventListener('DOMContentLoaded', function() {
    if (window.django && window.django.jQuery) {
        (function($) {

            // Mapeia o valor do 'tipo' de seção para a classe CSS do seu inline
            const typeToInlineClass = {
                'shelf': '.shelf-options',
                'author': '.author-options',
                'video': '.video-options',
                'ad': '.ad-options',
                'background': '.background-options',
                'link_grid': '.link_grid-options',
            };

            function toggleAllOptions() {
                const sectionType = $('#id_tipo').val();

                // Esconde todos os inlines e fieldsets específicos primeiro
                Object.values(typeToInlineClass).forEach(cls => $(cls).hide());
                $('.manual-books-inline').hide();

                // Mostra o inline/fieldset correto baseado no tipo de seção
                if (typeToInlineClass[sectionType]) {
                    $(typeToInlineClass[sectionType]).show();
                }

                // Lógica especial para prateleiras de livros (manual vs. automático)
                if (sectionType === 'shelf') {
                    const shelfBehavior = $('#id_shelf_behavior').val();
                    if (shelfBehavior === 'manual') {
                        $('.manual-books-inline').show();
                    }
                }
            }

            // Executa na carga e nas mudanças
            toggleAllOptions();
            $('#id_tipo, #id_shelf_behavior').on('change', toggleAllOptions);

        })(django.jQuery);
    }
});