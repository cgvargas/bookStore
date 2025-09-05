// Carrega a API do YouTube de forma assíncrona
let youtubePlayer;

function loadYouTubeAPI() {
    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
}

function onYouTubeIframeAPIReady() {
    console.log('YouTube API Ready');
}

// Função simples para corrigir thumbnails que possam ter falhado
function fixBrokenThumbnails() {
    const thumbnails = document.querySelectorAll('.video-thumbnail');

    thumbnails.forEach(img => {
        // Adicionar handler para caso a imagem não carregue
        if (img.complete && img.naturalHeight === 0) {
            const videoId = img.closest('.video-link')?.getAttribute('data-video-id');
            if (videoId) {
                img.src = `https://img.youtube.com/vi/${videoId}/default.jpg`;
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Carrega a API do YouTube
    loadYouTubeAPI();

    // Tenta corrigir thumbnails quebrados após tudo carregar
    window.addEventListener('load', fixBrokenThumbnails);

    // Inicializa o Swiper para os vídeos após um pequeno delay
    setTimeout(() => {
        const videoSwipers = document.querySelectorAll('.videoSwiper');
        videoSwipers.forEach(function(element) {
            new Swiper(element, {
                slidesPerView: 1,
                spaceBetween: 16,
                navigation: {
                    nextEl: element.querySelector('.swiper-button-next'),
                    prevEl: element.querySelector('.swiper-button-prev'),
                },
                breakpoints: {
                    640: {
                        slidesPerView: 2,
                        spaceBetween: 16,
                    },
                    768: {
                        slidesPerView: 3,
                        spaceBetween: 24,
                    },
                    1024: {
                        slidesPerView: 4,
                        spaceBetween: 24,
                        preventInteractionOnTransition: true,
                    }
                }
            });
        });
    }, 500);

    const modal = document.getElementById('videoModal');
    const modalContent = modal?.querySelector('.modal-content');
    const closeBtn = modal?.querySelector('.close-modal');
    const videoContainer = document.getElementById('modalVideoPlayer');

    // Se os elementos necessários não existirem, não configuramos os handlers
    if (!modal || !closeBtn || !videoContainer) return;

    // Função para abrir o modal e iniciar o vídeo
    function openVideoModal(videoId) {
        modal.style.display = 'flex';
        if (youtubePlayer) {
            youtubePlayer.destroy();
        }

        youtubePlayer = new YT.Player('modalVideoPlayer', {
            height: '360',
            width: '640',
            videoId: videoId,
            playerVars: {
                'autoplay': 1,
                'rel': 0,
                'modestbranding': 1
            },
            events: {
                'onReady': onPlayerReady,
                'onError': function(event) {
                    // Se houver erro ao carregar o vídeo, redireciona para o YouTube
                    closeVideoModal();
                    window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
                },
                'onStateChange': function(event) {
                    // Se o vídeo não puder ser reproduzido (código de erro)
                    if (event.data === -1) {
                        setTimeout(() => {
                            if (event.target.getPlayerState() === -1) {
                                closeVideoModal();
                                window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
                            }
                        }, 2000); // Aguarda 2 segundos para verificar se o vídeo iniciou
                    }
                }
            }
        });
    }

    function onPlayerReady(event) {
        try {
            event.target.playVideo();
        } catch (error) {
            console.error('Erro ao iniciar o vídeo:', error);
            closeVideoModal();
            window.open(`https://www.youtube.com/watch?v=${event.target.getVideoData().video_id}`, '_blank');
        }
    }

    function closeVideoModal() {
        if (youtubePlayer) {
            youtubePlayer.destroy();
        }
        modal.style.display = 'none';
        videoContainer.innerHTML = '';
    }

    // Event listeners para os links de vídeo
    document.querySelectorAll('.video-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const videoId = this.getAttribute('data-video-id');
            openVideoModal(videoId);
        });
    });

    closeBtn.addEventListener('click', closeVideoModal);

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeVideoModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeVideoModal();
        }
    });
});