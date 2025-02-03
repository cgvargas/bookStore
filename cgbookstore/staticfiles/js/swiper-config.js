// Configuração do Swiper para carrosséis de livros
const SwiperConfig = {
    // Configuração base
    init(element) {
        return new Swiper(element, {
            slidesPerView: 'auto',
            spaceBetween: 20,
            centeredSlides: false,
            watchOverflow: true,
            autoHeight: true,
            observer: true,
            observeParents: true,

            // Navegação
            navigation: {
                nextEl: element.querySelector('.swiper-button-next'),
                prevEl: element.querySelector('.swiper-button-prev'),
            },

            // Paginação
            pagination: {
                el: element.querySelector('.swiper-pagination'),
                clickable: true,
            },

            // Responsividade
            breakpoints: {
                320: {
                    slidesPerView: 2,
                    spaceBetween: 15
                },
                480: {
                    slidesPerView: 3,
                    spaceBetween: 20
                },
                768: {
                    slidesPerView: 4,
                    spaceBetween: 25
                },
                1024: {
                    slidesPerView: 5,
                    spaceBetween: 30
                }
            },

            // Eventos
            on: {
                init: function() {
                    this.update();
                },
                resize: function() {
                    this.update();
                }
            }
        });
    },

    // Inicializa todos os carrosséis na página
    initAll() {
        const swiperElements = document.querySelectorAll('.swiper-container');
        const swiperInstances = [];

        swiperElements.forEach(element => {
            const swiper = this.init(element);
            swiperInstances.push(swiper);
        });

        return swiperInstances;
    }
};

export default SwiperConfig;