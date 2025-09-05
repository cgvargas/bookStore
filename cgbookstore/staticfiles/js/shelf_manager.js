/* Gerenciador visual de prateleiras */

document.addEventListener('DOMContentLoaded', function() {
    // Função para obter o cookie CSRF
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

    function showNotification(message, type = 'success') {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';

        const alertElement = document.createElement('div');
        // Remova qualquer menção a alert-dismissible
        alertElement.className = `alert ${alertClass} position-fixed top-0 start-50 translate-middle-x mt-4`;
        alertElement.style.zIndex = '9999';
        alertElement.style.transition = 'all 0.3s ease';
        alertElement.style.transform = 'translateY(-20px)';
        alertElement.style.opacity = '0';
        alertElement.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        alertElement.style.minWidth = '300px';
        alertElement.style.maxWidth = '500px';

        // Determinar ícone baseado no tipo
        let icon = type === 'success' ? 'check-circle' : 'exclamation-circle';

        // HTML sem o botão de fechar
        alertElement.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-${icon} me-2" style="font-size: 1.25rem;"></i>
                <div>${message}</div>
            </div>
        `;

        document.body.appendChild(alertElement);

        // Adicionar efeito de entrada
        setTimeout(() => {
            alertElement.style.transform = 'translateY(0)';
            alertElement.style.opacity = '1';
        }, 10);

        function removeAlert() {
            alertElement.style.transform = 'translateY(-20px)';
            alertElement.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(alertElement)) {
                    document.body.removeChild(alertElement);
                }
            }, 300);
        }

        // Remover após 3 segundos
        const removeTimeout = setTimeout(() => {
            removeAlert();
        }, 3000);

        // Pausar o timer quando mouse estiver sobre o alerta
        alertElement.addEventListener('mouseenter', () => {
            clearTimeout(removeTimeout);
        });

        alertElement.addEventListener('mouseleave', () => {
            setTimeout(() => {
                removeAlert();
            }, 1000);
        });
    }

    // Inicializa sortable para cada prateleira
    document.querySelectorAll('.book-list.dropzone').forEach(function(el) {
        new Sortable(el, {
            animation: 150,
            group: {
                name: 'books',
                pull: true,
                put: true
            },
            onAdd: function(evt) {
                const bookItem = evt.item;
                const bookId = bookItem.dataset.bookId;
                const shelfId = evt.to.dataset.shelfId;

                // Adiciona botão de remoção se necessário
                if (!bookItem.querySelector('.remove-book')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'btn btn-sm btn-outline-danger ms-auto remove-book';
                    removeBtn.title = 'Remover da prateleira';
                    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                    bookItem.appendChild(removeBtn);
                }

                // Atualiza contador de livros
                updateShelfCounter(shelfId);

                // Notifica o servidor sobre a adição
                fetch('/admin/visual-shelf-manager/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        action: 'add',
                        book_id: bookId,
                        shelf_id: shelfId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification('Livro adicionado com sucesso!');
                    } else {
                        console.error('Erro ao adicionar livro:', data.message);
                        // Reverte a ação em caso de erro
                        document.getElementById('unassigned-books').appendChild(bookItem);
                        showNotification('Erro ao adicionar livro: ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Erro na requisição:', error);
                    // Reverte a ação em caso de erro
                    document.getElementById('unassigned-books').appendChild(bookItem);
                    showNotification('Erro na requisição ao servidor', 'error');
                });
            },
            onUpdate: function(evt) {
                const shelfId = evt.to.dataset.shelfId;
                const items = evt.to.querySelectorAll('.book-item');
                const order = Array.from(items).map(item => item.dataset.bookId);

                // Notifica o servidor sobre a reordenação
                fetch('/admin/visual-shelf-manager/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        action: 'reorder',
                        shelf_id: shelfId,
                        order: order
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification('Ordem atualizada com sucesso!');
                    } else {
                        console.error('Erro ao reordenar livros:', data.message);
                        showNotification('Erro ao reordenar livros: ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Erro na requisição:', error);
                    showNotification('Erro na requisição ao servidor', 'error');
                });
            }
        });
    });

    // Inicializa sortable para livros não associados
    new Sortable(document.getElementById('unassigned-books'), {
        animation: 150,
        group: {
            name: 'books',
            pull: true,
            put: true
        }
    });

    // Função para atualizar contador de livros em uma prateleira
    function updateShelfCounter(shelfId) {
        const shelfContainer = document.querySelector(`.book-list[data-shelf-id="${shelfId}"]`).closest('.shelf-container');
        const shelfStats = shelfContainer.querySelector('.shelf-stats');
        const maxLivrosText = shelfStats.textContent.split('/')[1].trim();
        const maxLivros = parseInt(maxLivrosText.match(/\d+/)[0], 10);
        const currentCount = shelfContainer.querySelectorAll('.book-item').length;

        // Atualiza contagem
        shelfStats.querySelector('.badge').textContent = `Livros: ${currentCount} / ${maxLivros}`;

        // Alerta visual se exceder o limite
        if (currentCount > maxLivros) {
            shelfStats.querySelector('.badge').classList.remove('bg-info');
            shelfStats.querySelector('.badge').classList.add('bg-warning');
        } else {
            shelfStats.querySelector('.badge').classList.remove('bg-warning');
            shelfStats.querySelector('.badge').classList.add('bg-info');
        }
    }

    // Evento para remover livros de prateleiras
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-book')) {
            const button = e.target.closest('.remove-book');
            const bookItem = button.closest('.book-item');
            const bookId = bookItem.dataset.bookId;
            const shelfContainer = bookItem.closest('.book-list');
            const shelfId = shelfContainer.dataset.shelfId;

            // Remove o botão de remoção
            button.remove();

            // Move o item para a lista de não associados
            document.getElementById('unassigned-books').appendChild(bookItem);

            // Atualiza contador de livros
            updateShelfCounter(shelfId);

            // Notifica o servidor sobre a remoção
            fetch('/admin/visual-shelf-manager/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    action: 'remove',
                    book_id: bookId,
                    shelf_id: shelfId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification('Livro removido com sucesso!');
                } else {
                    console.error('Erro ao remover livro:', data.message);
                    // Tenta reverter a ação
                    shelfContainer.appendChild(bookItem);
                    showNotification('Erro ao remover livro: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                showNotification('Erro na requisição ao servidor', 'error');
            });
        }
    });

    // Corrige os problemas de atributos 'for' nos formulários
    function fixFormLabels() {
        // Para o formulário de busca de prateleiras
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput && !searchInput.id) {
            searchInput.id = 'shelf-search-input';
            const searchLabel = searchInput.closest('form').querySelector('label');
            if (searchLabel) {
                searchLabel.htmlFor = 'shelf-search-input';
            }
        }

        // Para o formulário de busca de livros
        const bookSearchInput = document.querySelector('input[name="book_q"]');
        if (bookSearchInput && !bookSearchInput.id) {
            bookSearchInput.id = 'book-search-input';
            const bookSearchLabel = bookSearchInput.closest('form').querySelector('label');
            if (bookSearchLabel) {
                bookSearchLabel.htmlFor = 'book-search-input';
            }
        }
    }

    // Inicializa contadores e corrige os formulários
    document.querySelectorAll('.book-list.dropzone').forEach(function(shelf) {
        updateShelfCounter(shelf.dataset.shelfId);
    });

    // Corrige os problemas de atributos 'for'
    fixFormLabels();
});