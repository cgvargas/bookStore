// profile.js

(function() {
    'use strict';

    const isBookDetailsPage = window.location.pathname.match(/\/books\/\d+\/$/);

    if (isBookDetailsPage) {
        console.log('Profile.js: PÃ¡gina de detalhes detectada. NÃ£o executando para evitar conflitos.');

        window.profileState = {
            isProcessing: false,
            booksBeingProcessed: new Set(),
            modalsInitialized: false,
            currentBookId: null,
            currentShelfType: null,
            swiperInstances: []
        };

        return;
    }

    console.log('Profile.js: Pagina de perfil detectada. Inicializando normalmente.');

    // Estado da aplicaÃ§Ã£o - verificar se jÃ¡ existe no escopo global
    if (typeof window.profileState === 'undefined') {
        window.profileState = {
            isProcessing: false,
            booksBeingProcessed: new Set(),
            modalsInitialized: false,
            currentBookId: null,
            currentShelfType: null,
            swiperInstances: []
        };
    }

    // Gerenciador de modais - PrevenÃ§Ã£o de declaraÃ§Ã£o duplicada
    if (typeof window.ModalManager === 'undefined') {
        window.ModalManager = {
            modals: {},

            init() {
                const modalElements = {
                    bookManager: document.getElementById('bookManagerModal'),
                    shelfManager: document.getElementById('shelfManagerModal'),
                    editBook: document.getElementById('editBookModal'),
                    moveBook: document.getElementById('moveBookModal'),
                    newBook: document.getElementById('newBookModal')
                };

                Object.entries(modalElements).forEach(([key, element]) => {
                    if (element) {
                        // ADICIONE A OPÃ‡ÃƒO { backdrop: false } AQUI
                        this.modals[key] = new bootstrap.Modal(element, {
                            backdrop: false
                        });
                        this.setupModalEvents(element);
                    }
                });

                window.profileState.modalsInitialized = true;
                console.log('Modais do Perfil inicializados com sucesso (SEM backdrop nativo)');
            },

            setupModalEvents(modalElement) {
                if (!modalElement) return;

                modalElement.addEventListener('hidden.bs.modal', () => {
                    this.clearModalBackdrop();
                    modalElement.removeAttribute('aria-hidden');
                });

                modalElement.addEventListener('show.bs.modal', () => {
                    this.clearModalBackdrop();
                });
            },

            show(modalName) {
                if (this.modals[modalName]) {
                    this.modals[modalName].show();
                } else {
                    console.error(`Modal ${modalName} nÃ£o encontrado`);
                }
            },

            hide(modalName) {
                if (this.modals[modalName]) {
                    this.modals[modalName].hide();
                }
            },

            clearModalBackdrop() {
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => backdrop.remove());
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
            }
        };
    }

    // Usar a instÃ¢ncia global para evitar conflitos
    const ModalManager = window.ModalManager;

    // Gerenciador de Livros
    const BookManager = {
        isProcessing(bookId) {
            return window.profileState.booksBeingProcessed.has(bookId);
        },

        markAsProcessing(bookId) {
            window.profileState.booksBeingProcessed.add(bookId);
            setTimeout(() => window.profileState.booksBeingProcessed.delete(bookId), 1000);
        },

        async removeBook(bookId, shelfType) {
            if (this.isProcessing(bookId)) return;
            this.markAsProcessing(bookId);

            try {
                const response = await fetch('/books/remove-from-shelf/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ book_id: bookId, shelf_type: shelfType })
                });

                const data = await response.json();

                if (data.success) {
                    showAlert('Livro removido com sucesso!');
                    ModalManager.hide('bookManager');
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    throw new Error(data.error || 'Erro ao remover livro');
                }
            } catch (error) {
                console.error('Erro:', error);
                showAlert(error.message || 'Erro ao remover livro', 'danger');
            }
        }
    };

    // Gerenciador de Upload de Foto - Sistema Melhorado
    const PhotoUploadManager = {
        isProcessing: false,

        init() {
            this.setupAvatarInput();
            this.setupProfileImageHover();
            console.log('Sistema de upload de foto inicializado');
        },

        setupAvatarInput() {
            const avatarInput = document.getElementById('avatarInput');
            if (avatarInput) {
                avatarInput.addEventListener('change', (e) => this.handleFileSelection(e));
            }
        },

        setupProfileImageHover() {
            // Encontrar o contÃªiner da imagem de perfil
            const profileImageContainer = document.querySelector('.profile-image');

            if (profileImageContainer) {
                // Remover o botÃ£o existente de alterar foto se houver
                const existingButton = profileImageContainer.querySelector('.camera-button');
                if (existingButton) {
                    existingButton.remove();
                }

                // Criar o novo botÃ£o discreto de cÃ¢mera
                const cameraButton = document.createElement('button');
                cameraButton.className = 'camera-button';
                cameraButton.innerHTML = '<i class="bi bi-camera"></i>';
                cameraButton.setAttribute('title', 'Alterar foto de perfil');
                cameraButton.type = 'button';

                // Adicionar evento de clique ao botÃ£o
                cameraButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('avatarInput').click();
                });

                // Aplicar estilos ao botÃ£o
                Object.assign(cameraButton.style, {
                    position: 'absolute',
                    bottom: '10px',
                    right: '10px',
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    color: 'white',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    zIndex: '10',
                    opacity: '0',
                    transition: 'opacity 0.3s ease'
                });

                // Tornar o contÃªiner relativo para posicionamento do botÃ£o
                profileImageContainer.style.position = 'relative';

                // Adicionar o botÃ£o ao contÃªiner da imagem
                profileImageContainer.appendChild(cameraButton);

                // Criar overlay
                const overlay = document.createElement('div');
                overlay.className = 'profile-image-overlay';

                Object.assign(overlay.style, {
                    position: 'absolute',
                    top: '0',
                    left: '0',
                    right: '0',
                    bottom: '0',
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '50%',
                    opacity: '0',
                    transition: 'opacity 0.3s ease',
                    zIndex: '5'
                });

                // Adicionar o overlay antes do botÃ£o de cÃ¢mera
                profileImageContainer.insertBefore(overlay, cameraButton);

                // Adicionar eventos de hover
                profileImageContainer.addEventListener('mouseenter', function() {
                    cameraButton.style.opacity = '1';
                    overlay.style.opacity = '1';
                });

                profileImageContainer.addEventListener('mouseleave', function() {
                    cameraButton.style.opacity = '0';
                    overlay.style.opacity = '0';
                });

                console.log('Interface de hover da foto de perfil configurada');
            }
        },

        async handleFileSelection(e) {
            const file = e.target.files[0];
            if (!file) return;

            // Verificar se jÃ¡ estÃ¡ processando
            if (this.isProcessing) {
                showAlert('Upload jÃ¡ em andamento. Aguarde...', 'warning');
                return;
            }

            // ValidaÃ§Ãµes
            if (!this.validateFile(file)) {
                return;
            }

            this.isProcessing = true;

            try {
                showAlert('Enviando foto...', 'info');
                const result = await this.uploadPhoto(file);

                if (result.success) {
                    showAlert('Foto atualizada com sucesso!', 'success');
                    // Atualizar a imagem na pÃ¡gina sem recarregar
                    this.updateProfileImage(result.avatar_url);
                } else {
                    throw new Error(result.error || 'Erro ao atualizar foto');
                }
            } catch (error) {
                console.error('Erro no upload:', error);
                showAlert(error.message || 'Erro ao atualizar foto', 'danger');
            } finally {
                this.isProcessing = false;
                // Limpar o input para permitir o mesmo arquivo novamente
                e.target.value = '';
            }
        },

        validateFile(file) {
            // Validar tipo de arquivo
            const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                showAlert('O arquivo deve ser uma imagem (JPEG, PNG, GIF ou WebP)', 'danger');
                return false;
            }

            // Validar tamanho (5MB)
            const maxSize = 5 * 1024 * 1024; // 5MB em bytes
            if (file.size > maxSize) {
                showAlert('A imagem deve ter no mÃ¡ximo 5MB', 'danger');
                return false;
            }

            return true;
        },

        async uploadPhoto(file) {
            const formData = new FormData();
            formData.append('profile_photo', file);

            const response = await fetch('/profile/update-photo/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }

            return await response.json();
        },

        updateProfileImage(newUrl) {
            console.log('=== ATUALIZANDO IMAGEM DE PERFIL ===');
            console.log('Nova URL:', newUrl);

            const urlWithTimestamp = newUrl.includes('?')
                ? `${newUrl}&t=${Date.now()}`
                : `${newUrl}?t=${Date.now()}`;

            console.log('URL com timestamp:', urlWithTimestamp);

            const profileContainer = document.querySelector('.profile-image');
            let profileImg = null; // Declarar a variÃ¡vel aqui para ter o escopo correto

            if (profileContainer) {
                console.log('Container .profile-image encontrado');

                const placeholder = profileContainer.querySelector('.avatar-placeholder');
                if (placeholder) {
                    placeholder.remove();
                }

                profileImg = profileContainer.querySelector('img.rounded-circle'); // Seletor simplificado

                if (!profileImg) {
                    console.log('Imagem nÃ£o existe no container, criando nova...');
                    profileImg = document.createElement('img');
                    profileImg.className = 'rounded-circle img-fluid';
                    profileImg.alt = 'Foto de perfil';
                    Object.assign(profileImg.style, {
                        width: '150px',
                        height: '150px',
                        objectFit: 'cover'
                    });

                    const avatarForm = profileContainer.querySelector('#avatarForm');
                    if (avatarForm) {
                        profileContainer.insertBefore(profileImg, avatarForm);
                    } else {
                        profileContainer.appendChild(profileImg);
                    }
                } else {
                    console.log('Imagem existente encontrada, atualizando...');
                }

                profileImg.src = urlWithTimestamp;
                profileImg.onload = () => console.log('âœ… Imagem de perfil carregada com sucesso!');
                profileImg.onerror = () => {
                    console.error('âŒ Erro ao carregar imagem:', urlWithTimestamp);
                    profileImg.src = '/static/images/default-avatar.png';
                };
            } else {
                console.error('Container .profile-image nÃ£o encontrado!');
            }

            // Atualiza outras imagens de avatar na pÃ¡gina (backup)
            document.querySelectorAll('img[alt*="perfil"], img[alt*="avatar"]').forEach(img => {
                img.src = urlWithTimestamp;
            });

            console.log('AtualizaÃ§Ã£o de imagens de backup concluÃ­da.');
            console.log('=== FIM DA ATUALIZAÃ‡ÃƒO ===');
        }
    };

    // Gerenciador de Carrossel
    const CarouselManager = {
        async init() {
            try {
                const { default: SwiperConfig } = await import('/static/js/swiper-config.js');
                window.profileState.swiperInstances = SwiperConfig.initAll();
                console.log('CarrossÃ©is inicializados');
            } catch (error) {
                console.error('Erro ao inicializar carrossÃ©is:', error);
            }
        }
    };

    // FunÃ§Ãµes UtilitÃ¡rias
    function getCookie(name) {
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

    function showAlert(message, type = 'success') {
        // Remover alertas existentes do mesmo tipo
        const existingAlerts = document.querySelectorAll(`.alert-${type}`);
        existingAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '1055';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);

        // Auto-remover apÃ³s 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // FunÃ§Ãµes de NavegaÃ§Ã£o
    function openBookManager(bookId, shelfType) {
        if (BookManager.isProcessing(bookId)) return;
        window.profileState.currentBookId = bookId;
        window.profileState.currentShelfType = shelfType;
        window.location.href = `/books/${bookId}/`;
    }

    function openShelfManager(shelfType) {
        if (!window.profileState.modalsInitialized) {
            console.error('Modais nÃ£o inicializados');
            return;
        }
        window.profileState.currentShelfType = shelfType;
        ModalManager.show('shelfManager');
    }

    function openNewBookModal(shelfType) {
        if (!window.profileState.modalsInitialized) {
            console.error('Modais nÃ£o inicializados');
            return;
        }

        // Atualiza o tipo de prateleira no estado
        window.profileState.currentShelfType = shelfType;

        // Atualiza o campo hidden do formulÃ¡rio
        const shelfTypeField = document.getElementById('newBookShelfType');
        if (shelfTypeField) {
            shelfTypeField.value = shelfType;
        }

        // Exibe o modal
        ModalManager.show('newBook');
    }

    // FunÃ§Ã£o para salvar novo livro
    async function saveNewBook() {
        const form = document.getElementById('newBookForm');
        if (!form) {
            showAlert('FormulÃ¡rio nÃ£o encontrado', 'danger');
            return;
        }

        const bookData = {
            titulo: document.getElementById('newTitle')?.value || '',
            autor: document.getElementById('newAuthor')?.value || '',
            descricao: document.getElementById('newDescription')?.value || '',
            editora: document.getElementById('newPublisher')?.value || '',
            categoria: document.getElementById('newCategory')?.value || '',
            shelf_type: document.getElementById('newBookShelfType')?.value || ''
        };

        // ValidaÃ§Ã£o bÃ¡sica
        if (!bookData.titulo || !bookData.autor) {
            showAlert('TÃ­tulo e autor sÃ£o obrigatÃ³rios', 'danger');
            return;
        }

        try {
            const formData = new FormData();

            // Adicionar dados do livro
            Object.keys(bookData).forEach(key => {
                formData.append(key, bookData[key]);
            });

            // Adicionar arquivo de capa se existir
            const coverFile = document.getElementById('newCover')?.files[0];
            if (coverFile) {
                formData.append('capa', coverFile);
            }

            const response = await fetch('/books/add-book-manual/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showAlert('Livro adicionado com sucesso!');
                ModalManager.hide('newBook');
                setTimeout(() => window.location.reload(), 500);
            } else {
                throw new Error(data.error || 'Erro ao adicionar livro');
            }
        } catch (error) {
            console.error('Erro:', error);
            showAlert(error.message || 'Erro ao adicionar livro', 'danger');
        }
    }

    // ExposiÃ§Ã£o de funÃ§Ãµes globais
    window.openBookManager = openBookManager;
    window.openShelfManager = openShelfManager;
    window.openNewBookModal = openNewBookModal;
    window.saveNewBook = saveNewBook;

    // InicializaÃ§Ã£o Principal
    document.addEventListener('DOMContentLoaded', function() {
        try {
            // Inicializar componentes principais
            ModalManager.init();
            PhotoUploadManager.init();
            CarouselManager.init();

            // Configurar eventos dos botÃµes
            setupButtonEvents();

            console.log('Sistema de perfil inicializado com sucesso');
        } catch (error) {
            console.error('Erro na inicializaÃ§Ã£o do profile.js:', error);
        }
    });

    // ConfiguraÃ§Ã£o de eventos dos botÃµes
    function setupButtonEvents() {
        const editBookBtn = document.getElementById('editBookBtn');
        if (editBookBtn) {
            editBookBtn.addEventListener('click', () => {
                ModalManager.hide('bookManager');
                window.location.href = `/books/${window.profileState.currentBookId}/`;
            });
        }

        const moveBookBtn = document.getElementById('moveBookBtn');
        if (moveBookBtn) {
            moveBookBtn.addEventListener('click', () => {
                ModalManager.hide('bookManager');
                ModalManager.show('moveBook');
            });
        }

        const deleteBookBtn = document.getElementById('deleteBookBtn');
        if (deleteBookBtn) {
            deleteBookBtn.addEventListener('click', () => {
                if (confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
                    BookManager.removeBook(window.profileState.currentBookId, window.profileState.currentShelfType);
                }
            });
        }
    }

    // Tratamento de Erros Global
    window.addEventListener('error', function(event) {
        if (event.error?.toString().includes('Modal')) {
            console.error('Erro no gerenciamento de modais:', event.error);
            ModalManager.clearModalBackdrop();
        }
    });

    // Debug - Expor objetos principais para debugging
    if (typeof window !== 'undefined') {
        window.ProfileDebug = {
            state: window.profileState,
            modalManager: ModalManager,
            bookManager: BookManager,
            photoManager: PhotoUploadManager,
            carouselManager: CarouselManager
        };
    }

    const statsModalElement = document.getElementById('statsModal');
    if (statsModalElement) {
        statsModalElement.addEventListener('shown.bs.modal', () => {
            console.log('Modal de estatatísticas exibido. Tentando desenhar o gráfico...');
            if (typeof initReadingChart === 'function') {
                initReadingChart('statsModalChart');
            } else {
                console.error('A função initReadingChart nÃ£o foi encontrada. Verifique se o script profile-stats.js estão sendo carregado corretamente no template.');
            }
        });
    }
})();