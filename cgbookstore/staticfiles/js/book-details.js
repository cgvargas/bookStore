// cgbookstore/static/js/book-details.js

console.log('Carregando book-details.js...');

// Definir funções globais primeiro
window.openEditModal = function() {
    console.log('Função openEditModal chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.openEditModal();
    }
};

window.openMoveModal = function() {
    console.log('Função openMoveModal chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.openMoveModal();
    }
};

window.confirmRemove = function() {
    console.log('Função confirmRemove chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        if (confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
            BookDetailsApp.BookManager.removeBook();
        }
    }
};

window.saveBookEdit = function() {
    console.log('Função saveBookEdit chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.saveBookEdit();
    }
};

window.moveBook = function() {
    console.log('Função moveBook chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.moveBook();
    }
};

// Função global para abrir o modal de adicionar à prateleira
window.openShelfModal = function() {
    console.log('Função openShelfModal chamada globalmente');
    console.log('Estado atual da aplicação:', BookDetailsApp ? BookDetailsApp.state : 'BookDetailsApp não definido');

    if (!BookDetailsApp) {
        console.error('BookDetailsApp não está definido!');
        alert('Erro: O aplicativo não foi inicializado corretamente.');
        return;
    }

    // Verificações adicionais
    if (!BookDetailsApp.state.bookId) {
        console.error('ID do livro não definido');

        // Tentar recuperar ID da página
        const bookDetailsDiv = document.querySelector('.book-details');
        if (bookDetailsDiv && bookDetailsDiv.dataset.bookId) {
            BookDetailsApp.state.bookId = bookDetailsDiv.dataset.bookId;
            console.log('ID do livro recuperado do DOM:', BookDetailsApp.state.bookId);
        } else {
            console.error('Não foi possível recuperar o ID do livro do DOM');
            BookDetailsApp.utils.showAlert('Erro: ID do livro não encontrado', 'danger');
            return;
        }
    }

    if (BookDetailsApp?.BookManager) {
        console.log('Chamando BookManager.openShelfModal()');
        BookDetailsApp.BookManager.openShelfModal();
    } else {
        console.error('BookManager não disponível');
        BookDetailsApp.utils.showAlert('Erro: Sistema não inicializado corretamente', 'danger');
    }
};

// Função global para adicionar à prateleira
window.addToShelf = function() {
    console.log('Função addToShelf chamada globalmente');
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.addToShelf();
    } else {
        console.error('BookManager não disponível ou processamento em andamento');
    }
};

const BookDetailsApp = {
    // Estado inicial da aplicação
    state: {
        currentTab: 'basic',
        isTransitioning: false,
        bookId: null,
        currentShelf: null,
        isProcessing: false,
        modalOpened: false
    },

    // Utilitários
    utils: {
        // Verifica se o Bootstrap está disponível
        checkBootstrap() {
            const isAvailable = typeof bootstrap !== 'undefined';
            console.log('Bootstrap disponível?', isAvailable);
            return isAvailable;
        },

        // Obtém cookie pelo nome
        getCookie(name) {
            if (!document.cookie) return null;

            const cookies = document.cookie.split(';');
            const cookie = cookies.find(c => c.trim().startsWith(name + '='));

            return cookie
                ? decodeURIComponent(cookie.split('=')[1])
                : null;
        },

        // Exibe alerta na interface
        showAlert(message, type = 'success') {
            console.log(`Exibindo alerta: ${message} (tipo: ${type})`);
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
            alertDiv.style.zIndex = '1050';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            document.body.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        },

        // Valida resposta JSON
        async handleJsonResponse(response) {
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Resposta inválida do servidor');
            }
            return await response.json();
        }
    },

    // Gerenciador de abas
    TabManager: {
        init() {
            console.log('Inicializando TabManager');
            const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
            console.log(`Encontradas ${tabs.length} abas para inicializar`);

            tabs.forEach(tab => {
                tab.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.switchTab(e.currentTarget);
                });
            });
        },

        async switchTab(selectedTab, isInitial = false) {
            if (BookDetailsApp.state.isTransitioning) return;
            BookDetailsApp.state.isTransitioning = true;

            // Remove classes ativas
            document.querySelectorAll('[data-bs-toggle="tab"]')
                .forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-pane')
                .forEach(pane => {
                    pane.classList.remove('show', 'active');
                    pane.style.display = 'none';
                });

            // Ativa nova aba
            selectedTab.classList.add('active');
            const targetId = selectedTab.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);

            if (targetPane) {
                targetPane.style.display = 'block';
                targetPane.classList.add('active');
                await new Promise(resolve => setTimeout(resolve, 50));
                targetPane.classList.add('show');

                if (!isInitial) window.history.pushState(null, '', targetId);
            }

            setTimeout(() => {
                BookDetailsApp.state.isTransitioning = false;
            }, 300);
        }
    },

    // Gerenciador de livros
    BookManager: {
        // Nova função: Abre modal para adicionar à prateleira
        openShelfModal() {
            console.log('Método BookManager.openShelfModal() executado');
            console.log('Estado atual:', BookDetailsApp.state);

            // Verificar ID do livro
            if (!BookDetailsApp.state.bookId) {
                console.error('ID do livro não definido ao tentar abrir modal');

                // Tentar recuperar ID da página
                const bookDetailsDiv = document.querySelector('.book-details');
                if (bookDetailsDiv && bookDetailsDiv.hasAttribute('data-book-id')) {
                    BookDetailsApp.state.bookId = bookDetailsDiv.getAttribute('data-book-id');
                    console.log('ID do livro recuperado do DOM:', BookDetailsApp.state.bookId);
                } else {
                    console.error('Não foi possível recuperar o ID do livro do DOM');
                    BookDetailsApp.utils.showAlert('Erro: Não foi possível identificar o livro', 'danger');
                    return;
                }
            }

            // Verificar disponibilidade do Bootstrap
            if (!BookDetailsApp.utils.checkBootstrap()) {
                console.error('Bootstrap não está disponível!');
                BookDetailsApp.utils.showAlert('Erro: Componentes do sistema indisponíveis', 'danger');
                return;
            }

            // Verificar se o modal existe
            const shelfModal = document.getElementById('addToShelfModal');
            console.log('Modal encontrado?', shelfModal ? 'Sim' : 'Não');

            if (shelfModal) {
                console.log('Modal encontrado, preparando para exibir...');

                // Verificar a estrutura do modal
                console.log('Estrutura do modal:', shelfModal.innerHTML);

                try {
                    const modalInstance = new bootstrap.Modal(shelfModal);
                    console.log('Instância do modal criada com sucesso');
                    modalInstance.show();
                    console.log('Modal exibido');
                } catch (error) {
                    console.error('Erro ao exibir modal:', error);
                    BookDetailsApp.utils.showAlert('Erro ao abrir modal: ' + error.message, 'danger');
                }
            } else {
                console.error('Modal #addToShelfModal não encontrado!');

                // Verificar se há outros modais na página
                const allModals = document.querySelectorAll('.modal');
                console.log(`Encontrados ${allModals.length} modais na página:`);
                allModals.forEach(modal => {
                    console.log('- Modal ID:', modal.id);
                });

                BookDetailsApp.utils.showAlert('Modal não encontrado', 'danger');
            }
        },

        // Nova função: Adiciona livro à prateleira
        async addToShelf() {
        console.log('Método BookManager.addToShelf() executado');
        console.log('Estado atual da aplicação:', BookDetailsApp.state);

        if (BookDetailsApp.state.isProcessing) {
            console.warn('Operação já em andamento, ignorando clique');
            return;
        }

        BookDetailsApp.state.isProcessing = true;
        console.log('Iniciando processamento...');

        try {
            // Verificar se o formulário existe
            const form = document.getElementById('addToShelfForm');
            if (!form) {
                console.error('Formulário #addToShelfForm não encontrado!');
                throw new Error('Formulário de adição à prateleira não encontrado');
            }

            // Verificar se o select existe
            const selectElement = document.querySelector('#addToShelfForm [name="shelf_type"]');
            if (!selectElement) {
                console.error('Select [name="shelf_type"] não encontrado no formulário!');
                throw new Error('Seletor de prateleira não encontrado');
            }

            const shelfType = selectElement.value;
            console.log('Prateleira selecionada:', shelfType);

            // Verificar se temos o ID do livro
            if (!BookDetailsApp.state.bookId) {
                console.error('ID do livro não encontrado no estado da aplicação!');

                // Tentar obter o ID novamente
                const bookDetailsDiv = document.querySelector('.book-details');
                if (bookDetailsDiv && bookDetailsDiv.hasAttribute('data-book-id')) {
                    BookDetailsApp.state.bookId = bookDetailsDiv.getAttribute('data-book-id');
                    console.log('ID do livro recuperado da div:', BookDetailsApp.state.bookId);
                } else {
                    console.error('Não foi possível recuperar o ID do livro do DOM');
                    throw new Error('ID do livro não encontrado');
                }
            }

            // Preparar os dados para enviar (agora em formato JSON)
            const requestData = {
                book_id: BookDetailsApp.state.bookId,
                shelf_type: shelfType  // Alterado para o nome correto do campo
            };

            console.log('Dados preparados para envio:', requestData);

            // Verificar CSRF token
            const csrfToken = BookDetailsApp.utils.getCookie('csrftoken');
            if (!csrfToken) {
                console.error('Token CSRF não encontrado!');
                throw new Error('Token CSRF não disponível');
            }
            console.log('Token CSRF obtido');

            // Enviar requisição para adicionar à prateleira
            console.log('Enviando requisição para /books/add-to-shelf/...');
            const response = await fetch('/books/add-to-shelf/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(requestData)
            });

            console.log('Resposta recebida:', response);
            console.log('Status HTTP:', response.status);
            console.log('Headers:', response.headers);

            // Processar resposta
            const data = await BookDetailsApp.utils.handleJsonResponse(response);
            console.log('Dados da resposta:', data);

            if (data.success || data.status === 'success') {
                console.log('Operação bem-sucedida!');
                BookDetailsApp.utils.showAlert('Livro adicionado à prateleira com sucesso!');

                // Fechar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addToShelfModal'));
                if (modal) {
                    console.log('Fechando modal...');
                    modal.hide();
                } else {
                    console.warn('Não foi possível obter instância do modal para fechá-lo');
                }

                // Recarregar página
                console.log('Programando recarga da página em 1 segundo...');
                setTimeout(() => {
                    console.log('Recarregando página...');
                    window.location.reload();
                }, 1000);
            } else {
                console.error('Erro na resposta do servidor:', data);
                throw new Error(data.error || data.message || 'Erro ao adicionar livro à prateleira');
            }
        } catch (error) {
            console.error('Erro ao processar adição à prateleira:', error);
            BookDetailsApp.utils.showAlert(error.message, 'danger');
        } finally {
            console.log('Finalizando processamento');
            BookDetailsApp.state.isProcessing = false;
        }
    },

        // Abre modal de edição
        openEditModal() {
            console.log('Método BookManager.openEditModal() executado');
            if (!BookDetailsApp.utils.checkBootstrap()) return;

            const editModal = document.getElementById('editBookModal');
            if (!editModal) return;

            const bsModal = new bootstrap.Modal(editModal);

            if (BookDetailsApp.state.isProcessing) return;
            BookDetailsApp.state.isProcessing = true;

            // Carrega dados do livro
            fetch(`/books/${BookDetailsApp.state.bookId}/details/`)
                .then(response => BookDetailsApp.utils.handleJsonResponse(response))
                .then(data => {
                    if (data.success) {
                        const form = document.getElementById('editBookForm');
                        Object.entries(data).forEach(([key, value]) => {
                            const input = form.querySelector(`[name="${key}"]`);
                            if (input && value !== null) input.value = value;
                        });
                        bsModal.show();
                    } else {
                        throw new Error(data.error || 'Erro ao carregar dados do livro');
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
                    BookDetailsApp.utils.showAlert(error.message, 'danger');
                })
                .finally(() => {
                    BookDetailsApp.state.isProcessing = false;
                });
        },

        // Abre modal de movimentação
        openMoveModal() {
            console.log('Método BookManager.openMoveModal() executado');
            if (!BookDetailsApp.utils.checkBootstrap()) return;

            const moveModal = document.getElementById('moveBookModal');
            if (moveModal) {
                new bootstrap.Modal(moveModal).show();
            }
        },

        // Salva alterações do livro
        async saveBookEdit() {
            console.log('Método BookManager.saveBookEdit() executado');
            if (BookDetailsApp.state.isProcessing) return;
            BookDetailsApp.state.isProcessing = true;

            try {
                const form = document.getElementById('editBookForm');
                const formData = new FormData(form);

                // Validação de campos numéricos
                const numericFields = ['numero_paginas'];
                for (let field of numericFields) {
                    const value = formData.get(field);
                    if (value === '') {
                        formData.delete(field);
                    } else if (value && !Number.isInteger(Number(value))) {
                        throw new Error(`O campo ${field} deve ser um número inteiro válido`);
                    }
                }

                // Processa data de publicação
                this._processDate(formData);

                // Processa dados de preço
                this._processPrice(formData);

                const response = await fetch(`/books/${BookDetailsApp.state.bookId}/update/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': BookDetailsApp.utils.getCookie('csrftoken')
                    },
                    body: formData
                });

                const data = await BookDetailsApp.utils.handleJsonResponse(response);

                if (data.success) {
                    BookDetailsApp.utils.showAlert('Livro atualizado com sucesso!');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editBookModal'));
                    if (modal) modal.hide();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    throw new Error(data.error || 'Erro ao atualizar livro');
                }
            } catch (error) {
                console.error('Erro:', error);
                BookDetailsApp.utils.showAlert(error.message, 'danger');
            } finally {
                BookDetailsApp.state.isProcessing = false;
            }
        },

        // Move livro para outra prateleira
        async moveBook() {
            console.log('Método BookManager.moveBook() executado');
            if (BookDetailsApp.state.isProcessing) return;
            BookDetailsApp.state.isProcessing = true;

            try {
                const newShelf = document.querySelector('#moveBookForm [name="new_shelf"]').value;
                const response = await fetch(`/books/${BookDetailsApp.state.bookId}/move-to-shelf/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': BookDetailsApp.utils.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        new_shelf: newShelf
                    })
                });

                const data = await BookDetailsApp.utils.handleJsonResponse(response);

                if (data.success) {
                    BookDetailsApp.utils.showAlert('Livro movido com sucesso!');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('moveBookModal'));
                    if (modal) modal.hide();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    throw new Error(data.error || 'Erro ao mover livro');
                }
            } catch (error) {
                console.error('Erro:', error);
                BookDetailsApp.utils.showAlert(error.message, 'danger');
            } finally {
                BookDetailsApp.state.isProcessing = false;
            }
        },

        // Remove livro da prateleira
        async removeBook() {
            console.log('Método BookManager.removeBook() executado');
            if (BookDetailsApp.state.isProcessing) return;
            BookDetailsApp.state.isProcessing = true;

            try {
                const response = await fetch(`/books/${BookDetailsApp.state.bookId}/remove-from-shelf/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': BookDetailsApp.utils.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        shelf_type: BookDetailsApp.state.currentShelf
                    })
                });

                const data = await BookDetailsApp.utils.handleJsonResponse(response);

                if (data.success) {
                    BookDetailsApp.utils.showAlert('Livro removido com sucesso!');
                    setTimeout(() => window.location.href = '/profile/', 1000);
                } else {
                    throw new Error(data.error || 'Erro ao remover livro');
                }
            } catch (error) {
                console.error('Erro:', error);
                BookDetailsApp.utils.showAlert(error.message, 'danger');
            } finally {
                BookDetailsApp.state.isProcessing = false;
            }
        },

        // Métodos auxiliares privados
        _processDate(formData) {
            const pubDate = formData.get('data_publicacao');
            if (pubDate && pubDate !== 'None') {
                try {
                    formData.set('data_publicacao', new Date(pubDate).toISOString().split('T')[0]);
                } catch (e) {
                    formData.delete('data_publicacao');
                }
            } else {
                formData.delete('data_publicacao');
            }
        },

        _processPrice(formData) {
            // Obtém os valores dos campos
            const moeda = formData.get('preco_moeda') || 'BRL';
            const valor = formData.get('preco_valor') || '0';
            const valorPromocional = formData.get('preco_promocional') || '0';

            // Remove os campos antigos
            ['preco_moeda', 'preco_valor', 'preco_promocional'].forEach(key => formData.delete(key));

            // Converte os valores para decimal e adiciona ao formData
            formData.append('preco', parseFloat(valor.replace(',', '.')).toFixed(2));
            formData.append('preco_promocional', parseFloat(valorPromocional.replace(',', '.')).toFixed(2));
            formData.append('moeda', moeda);
        }
    }
};

// Inicializa aplicação quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded - Inicializando BookDetailsApp');

    // Verificar se o Bootstrap está disponível
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap não está disponível!');
        alert('Erro: Bootstrap não carregado. A funcionalidade pode estar limitada.');
    }

    // Verificar elementos críticos da página
    console.log('Verificando elementos críticos no DOM...');

    const bookDetailsDiv = document.querySelector('.book-details');
    console.log('Elemento .book-details encontrado?', bookDetailsDiv ? 'Sim' : 'Não');

    const editModal = document.getElementById('editBookModal');
    console.log('Elemento #editBookModal encontrado?', editModal ? 'Sim' : 'Não');

    const addToShelfModal = document.getElementById('addToShelfModal');
    console.log('Elemento #addToShelfModal encontrado?', addToShelfModal ? 'Sim' : 'Não');

    if (addToShelfModal) {
        console.log('Estrutura do modal de prateleira:', addToShelfModal.innerHTML);
    }

    // Verificar botão que chama o modal
    const addToShelfBtn = document.querySelector('button[onclick="window.openShelfModal && window.openShelfModal()"]');
    console.log('Botão de adicionar à prateleira encontrado?', addToShelfBtn ? 'Sim' : 'Não');

    if (addToShelfBtn) {
        console.log('Atributo onclick do botão:', addToShelfBtn.getAttribute('onclick'));
        // Adicionar evento de clique direto ao botão para depuração
        addToShelfBtn.addEventListener('click', function() {
            console.log('Botão de adicionar à prateleira clicado diretamente');
        });
    }

    // Recuperar ID do livro
    if (bookDetailsDiv && bookDetailsDiv.hasAttribute('data-book-id')) {
        BookDetailsApp.state.bookId = bookDetailsDiv.getAttribute('data-book-id');
        console.log('ID do livro obtido do elemento .book-details:', BookDetailsApp.state.bookId);
    } else if (editModal && editModal.hasAttribute('data-book-id')) {
        BookDetailsApp.state.bookId = editModal.getAttribute('data-book-id');
        console.log('ID do livro obtido do elemento #editBookModal:', BookDetailsApp.state.bookId);
    } else {
        console.error('Não foi possível obter o ID do livro do DOM');
    }

    // Tratar shelf como null se for 'None'
    const shelfValue = editModal?.getAttribute('data-shelf-type') || 'None';
    BookDetailsApp.state.currentShelf = shelfValue === 'None' ? null : shelfValue;
    console.log('Prateleira atual:', BookDetailsApp.state.currentShelf);

    // Adicionar log de diagnóstico
    console.log('Estado inicial da aplicação:', {
        bookId: BookDetailsApp.state.bookId,
        currentShelf: BookDetailsApp.state.currentShelf
    });

    // Inicializar gerenciador de abas
    BookDetailsApp.TabManager.init();

    console.log('Inicialização concluída');

    // Verificar se o botão de prateleira existe na página
    setTimeout(() => {
        console.log('Verificação posterior dos elementos do DOM');
        const shelfButton = document.querySelector('button[onclick*="openShelfModal"]');
        if (shelfButton) {
            console.log('Botão de prateleira encontrado após inicialização');
            console.log('HTML do botão:', shelfButton.outerHTML);

            // Testar click direto
            shelfButton.addEventListener('click', function(e) {
                console.log('Evento de clique direto no botão de prateleira');
                e.preventDefault();
                if (window.openShelfModal) {
                    console.log('Chamando openShelfModal diretamente do evento');
                    window.openShelfModal();
                }
            });
        } else {
            console.log('Botão de prateleira NÃO encontrado após inicialização');
        }
    }, 1000);
});