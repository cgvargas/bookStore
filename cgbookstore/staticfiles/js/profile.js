// Funções que precisam ser acessíveis globalmente
window.confirmDeleteBook = confirmDeleteBook;
window.openBookManager = openBookManager;
window.openShelfManager = openShelfManager;
window.openEditBookModal = openEditBookModal;
window.openMoveBookModal = openMoveBookModal;
window.saveBookEdit = saveBookEdit;
window.saveBookMove = saveBookMove;
window.openNewBookModal = openNewBookModal;
window.saveNewBook = saveNewBook;

// Inicialização dos modais
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar todos os modais
    const modals = {
        bookManager: new bootstrap.Modal(document.getElementById('bookManagerModal')),
        shelfManager: new bootstrap.Modal(document.getElementById('shelfManagerModal')),
        editBook: new bootstrap.Modal(document.getElementById('editBookModal')),
        moveBook: new bootstrap.Modal(document.getElementById('moveBookModal')),
        newBook: new bootstrap.Modal(document.getElementById('newBookModal'))
    };

    // Expor modais globalmente
    window.bookModals = modals;

    // Adicionar listeners para limpar estado ao fechar modais
    Object.values(modals).forEach(modal => {
        modal._element.addEventListener('hidden.bs.modal', clearModalBackdrop);
    });
});

// Variáveis globais para controle
let currentBookId = null;
let currentShelfType = null;

// Função para limpar backdrop e estado do modal
function clearModalBackdrop() {
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}

// Função para mostrar alertas
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

// Função para obter o token CSRF
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

// Funções de gerenciamento
function openBookManager(bookId, shelfType) {
    currentBookId = bookId;
    currentShelfType = shelfType;
    window.bookModals.bookManager.show();
}

function openShelfManager(shelfType) {
    currentShelfType = shelfType;
    document.getElementById('newBookShelfType').value = shelfType;
    window.bookModals.shelfManager.show();
}

// Função para confirmar exclusão
function confirmDeleteBook() {
    console.log('Confirmando exclusão do livro:', currentBookId);
    if (confirm('Tem certeza que deseja remover este livro da sua prateleira?')) {
        removeBook(currentBookId, currentShelfType);
    }
}

// Função para remover livro
function removeBook(bookId, shelfType) {
    console.log('Removendo livro:', bookId, 'da prateleira:', shelfType);
    fetch('/books/remove-from-shelf/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            book_id: bookId,
            shelf_type: shelfType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Livro removido com sucesso!');
            window.bookModals.bookManager.hide();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.error || 'Erro ao remover livro', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('Erro ao remover livro', 'danger');
    });
}

// Funções de edição
function openEditBookModal() {
    window.bookModals.bookManager.hide();
    fetch(`/books/${currentBookId}/details/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('editBookId').value = currentBookId;
                document.getElementById('editTitle').value = data.titulo;
                document.getElementById('editAuthor').value = data.autor;
                document.getElementById('editDescription').value = data.descricao;
                document.getElementById('editPublisher').value = data.editora;
                document.getElementById('editCategory').value = data.categoria;
                window.bookModals.editBook.show();
            } else {
                showAlert(data.error || 'Erro ao carregar dados do livro', 'danger');
            }
        })
        .catch(error => {
            console.error('Erro ao carregar dados do livro:', error);
            showAlert('Erro ao carregar dados do livro', 'danger');
        });
}

// Função para salvar edição
function saveBookEdit() {
    const formData = new FormData();
    formData.append('titulo', document.getElementById('editTitle').value);
    formData.append('autor', document.getElementById('editAuthor').value);
    formData.append('descricao', document.getElementById('editDescription').value);
    formData.append('editora', document.getElementById('editPublisher').value);
    formData.append('categoria', document.getElementById('editCategory').value);

    const coverFile = document.getElementById('editCover').files[0];
    if (coverFile) {
        formData.append('capa', coverFile);
    }

    fetch(`/books/${currentBookId}/update/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Livro atualizado com sucesso!');
            window.bookModals.editBook.hide();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.error || 'Erro ao atualizar livro', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('Erro ao atualizar livro', 'danger');
    });
}

// Funções de transferência
function openMoveBookModal() {
    window.bookModals.bookManager.hide();
    document.getElementById('moveBookId').value = currentBookId;
    document.getElementById('newShelfType').value = currentShelfType;
    window.bookModals.moveBook.show();
}

function saveBookMove() {
    fetch('/books/move-book/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            book_id: currentBookId,
            new_shelf: document.getElementById('newShelfType').value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Livro movido com sucesso!');
            window.bookModals.moveBook.hide();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.error || 'Erro ao mover livro', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('Erro ao mover livro', 'danger');
    });
}

// Funções de novo livro
function openNewBookModal() {
    window.bookModals.shelfManager.hide();
    document.getElementById('newBookShelfType').value = currentShelfType;
    document.getElementById('newBookForm').reset();
    window.bookModals.newBook.show();
}

function saveNewBook() {
    const formData = new FormData();
    formData.append('titulo', document.getElementById('newTitle').value);
    formData.append('autor', document.getElementById('newAuthor').value);
    formData.append('descricao', document.getElementById('newDescription').value);
    formData.append('editora', document.getElementById('newPublisher').value);
    formData.append('categoria', document.getElementById('newCategory').value);
    formData.append('shelf_type', document.getElementById('newBookShelfType').value);

    const coverFile = document.getElementById('newCover').files[0];
    if (coverFile) {
        formData.append('capa', coverFile);
    }

    fetch('/books/add-manual/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Livro adicionado com sucesso!');
            window.bookModals.newBook.hide();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.error || 'Erro ao adicionar livro', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('Erro ao adicionar livro', 'danger');
    });
}