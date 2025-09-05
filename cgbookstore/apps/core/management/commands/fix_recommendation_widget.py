import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Corrige o widget de recomendações da página inicial'

    def handle(self, *args, **options):
        # Caminho para o arquivo de template do widget de recomendações
        widget_path = os.path.join(settings.BASE_DIR, 'cgbookstore', 'apps', 'core', 'templates', 'core', 'components',
                                   'recommendation_widget.html')

        if not os.path.exists(widget_path):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {widget_path}'))
            # Tentar encontrar o arquivo em caminho alternativo
            alt_path = os.path.join(settings.BASE_DIR, 'cgbookstore', 'templates', 'core', 'components',
                                    'recommendation_widget.html')
            if os.path.exists(alt_path):
                widget_path = alt_path
                self.stdout.write(self.style.SUCCESS(f'Arquivo encontrado em caminho alternativo: {widget_path}'))
            else:
                self.stdout.write(self.style.ERROR(f'Arquivo alternativo não encontrado: {alt_path}'))
                return

        # Backup do arquivo original
        backup_path = widget_path + '.bak'
        with open(widget_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())

        self.stdout.write(self.style.SUCCESS(f'Backup criado: {backup_path}'))

        # Conteúdo corrigido para o widget de recomendações
        corrected_content = '''{% load static %}

<section id="recommendations" class="recommendations-section py-5 mb-5">
    <div class="container">
        <h2 class="section-title">Recomendações Para Você</h2>

        <div class="swiper recommendationsSwiper">
            <div class="swiper-wrapper">
                {% for book in recommended_books %}
                <div class="swiper-slide">
                    <div class="book-card">
                        <a href="{% if book.is_external %}{% url 'external_book_details' book.external_id %}{% else %}{% url 'core:book_detail' book.id %}{% endif %}" class="book-link">
                            <div class="book-cover-container">
                                <img 
                                    src="{% if book.is_external %}{% if book.capa_url %}{{ book.capa_url }}{% else %}{% static 'images/no-cover.svg' %}{% endif %}{% else %}{% if book.capa %}{{ book.capa.url }}{% elif book.capa_url %}{{ book.capa_url }}{% else %}{% static 'images/no-cover.svg' %}{% endif %}{% endif %}" 
                                    alt="{{ book.titulo|default:'Título desconhecido' }}" 
                                    class="book-cover-image"
                                    loading="lazy"
                                    onerror="this.onerror=null; this.src='{% static "images/no-cover.svg" %}';">
                            </div>
                            <div class="book-info">
                                <h3 class="book-title">{{ book.titulo|default:'Título desconhecido' }}</h3>
                                <p class="book-author">{{ book.autor|default:'Autor desconhecido' }}</p>
                            </div>
                        </a>
                    </div>
                </div>
                {% empty %}
                <div class="swiper-slide">
                    <div class="no-recommendations">
                        <div class="icon"><i class="bi bi-book"></i></div>
                        <p>Adicione livros à sua prateleira para receber recomendações personalizadas</p>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="swiper-button-next"></div>
            <div class="swiper-button-prev"></div>
        </div>

        <div class="text-center mt-4">
            <a href="{% url 'recommendations' %}" class="btn btn-outline-primary">
                Ver Todas Recomendações <i class="bi bi-arrow-right"></i>
            </a>
        </div>
    </div>
</section>

<style>
/* Estilos específicos para corrigir problemas de exibição das recomendações */
.recommendations-section .book-cover-container {
    position: relative;
    width: 100%;
    height: 200px;
    overflow: hidden;
    border-radius: 5px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    background-color: #f5f5f5;
    display: flex;
    align-items: center;
    justify-content: center;
}

.recommendations-section .book-cover-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    background-color: #f5f5f5;
    border-radius: 5px;
    transition: transform 0.3s ease;
}

.recommendations-section .book-cover-image[src*="no-cover.svg"] {
    object-fit: contain;
    padding: 20px;
}

.recommendations-section .book-info {
    padding: 10px 0;
}

.recommendations-section .book-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.recommendations-section .book-author {
    font-size: 12px;
    color: #666;
    margin-bottom: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.recommendations-section .book-card {
    transition: transform 0.3s ease;
}

.recommendations-section .book-card:hover {
    transform: translateY(-5px);
}

.recommendations-section .book-card:hover .book-cover-image {
    transform: scale(1.05);
}

.dark-theme .recommendations-section .book-cover-container {
    background-color: #333;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.dark-theme .recommendations-section .book-cover-image {
    background-color: #333;
}

.dark-theme .recommendations-section .book-author {
    color: #ccc;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Swiper
    new Swiper('.recommendationsSwiper', {
        slidesPerView: 2,
        spaceBetween: 20,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        breakpoints: {
            640: {
                slidesPerView: 3,
                spaceBetween: 20,
            },
            768: {
                slidesPerView: 4,
                spaceBetween: 30,
            },
            1024: {
                slidesPerView: 5,
                spaceBetween: 30,
            },
        }
    });

    // Script para garantir que todas as imagens tenham fallback
    const bookCovers = document.querySelectorAll('.recommendations-section .book-cover-image');

    bookCovers.forEach(img => {
        // Verificar se a imagem já carregou e não tem dimensões válidas
        if (img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0)) {
            img.src = '{% static "images/no-cover.svg" %}';
        }

        // Certificar que todas as imagens têm handler de erro
        img.onerror = function() {
            this.onerror = null;
            this.src = '{% static "images/no-cover.svg" %}';
        };
    });
});
</script>
'''

        # Escrever o conteúdo corrigido
        with open(widget_path, 'w', encoding='utf-8') as file:
            file.write(corrected_content)

        self.stdout.write(self.style.SUCCESS(f'Widget de recomendações corrigido com sucesso!'))