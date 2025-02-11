// cgbookstore/static/js/book-details.js

// Definir funções globais primeiro
window.openEditModal = function() {
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.openEditModal();
    }
};

window.openMoveModal = function() {
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.openMoveModal();
    }
};

window.confirmRemove = function() {
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        if (confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
            BookDetailsApp.BookManager.removeBook();
        }
    }
};

window.saveBookEdit = function() {
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.saveBookEdit();
    }
};

window.moveBook = function() {
    if (BookDetailsApp?.BookManager && !BookDetailsApp.state.isProcessing) {
        BookDetailsApp.BookManager.moveBook();
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
            return typeof bootstrap !== 'undefined';
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
            const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
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
        // Abre modal de edição
        openEditModal() {
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
            if (!BookDetailsApp.utils.checkBootstrap()) return;

            const moveModal = document.getElementById('moveBookModal');
            if (moveModal) {
                new bootstrap.Modal(moveModal).show();
            }
        },

        // Salva alterações do livro
        async saveBookEdit() {
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
    const editModal = document.getElementById('editBookModal');
    if (editModal) {
        BookDetailsApp.state.bookId = editModal.getAttribute('data-book-id');
        BookDetailsApp.state.currentShelf = editModal.getAttribute('data-shelf-type');
        BookDetailsApp.TabManager.init();

        console.log('BookDetailsApp initialized:', {
            bookId: BookDetailsApp.state.bookId,
            currentShelf: BookDetailsApp.state.currentShelf
        });
    }
});