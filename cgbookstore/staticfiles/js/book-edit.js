// cgbookstore/static/js/book-edit.js

document.addEventListener('DOMContentLoaded', function() {
    // Inicialização
    initializeBookEdit();
});

function initializeBookEdit() {
    // Adiciona classes ao formulário para validação do Bootstrap
    const form = document.getElementById('editBookForm');
    if (form) {
        form.classList.add('needs-validation');
        initializeFormValidation(form);
    }

    // Inicializa preview de imagem
    initializeImagePreview();

    // Inicializa máscaras de input
    initializeInputMasks();

    // Inicializa contadores de caracteres
    initializeCharacterCounters();

    // Salva estado das abas
    initializeTabPersistence();
}

// Validação de formulário
function initializeFormValidation(form) {
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    }, false);
}

// Preview de imagem
function initializeImagePreview() {
    const capaInput = document.querySelector('input[type="file"][name="capa"]');
    if (capaInput) {
        capaInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Verifica o tamanho do arquivo
                if (file.size > 5 * 1024 * 1024) { // 5MB
                    showNotification('O arquivo deve ter no máximo 5MB', 'error');
                    this.value = '';
                    return;
                }

                // Verifica o tipo do arquivo
                if (!file.type.match(/image\/(jpeg|jpg|png|gif)/)) {
                    showNotification('Formato de arquivo não suportado. Use JPG, PNG ou GIF.', 'error');
                    this.value = '';
                    return;
                }

                // Cria preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    let currentCover = document.querySelector('.current-cover');
                    if (!currentCover) {
                        currentCover = document.createElement('div');
                        currentCover.className = 'current-cover mb-3';
                        capaInput.parentNode.insertBefore(currentCover, capaInput.nextSibling);
                    }

                    currentCover.innerHTML = `
                        <label class="form-label">Preview da Nova Capa</label>
                        <div>
                            <img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-height: 200px;">
                        </div>
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

// Máscaras de input
function initializeInputMasks() {
    // Máscara para ISBN
    const isbnInput = document.querySelector('input[name="isbn"]');
    if (isbnInput) {
        isbnInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9X]/g, '');
            if (value.length > 13) {
                value = value.slice(0, 13);
            }
            e.target.value = value;
        });
    }

    // Máscara para peso
    const pesoInput = document.querySelector('input[name="peso"]');
    if (pesoInput) {
        pesoInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9.,kg ]/g, '');
            e.target.value = value;
        });
    }

    // Máscara para dimensões
    const dimensoesInput = document.querySelector('input[name="dimensoes"]');
    if (dimensoesInput) {
        dimensoesInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9.,x cm]/g, '');
            e.target.value = value;
        });
    }

    // Máscara para preços
    const precoInputs = document.querySelectorAll('input[name*="preco"]');
    precoInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9.,]/g, '');
            // Aceita apenas números e ponto/vírgula
            e.target.value = value;
        });
    });
}

// Contadores de caracteres
function initializeCharacterCounters() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        const counter = document.createElement('div');
        counter.className = 'character-counter text-muted small mt-1';
        textarea.parentNode.appendChild(counter);

        function updateCounter() {
            const length = textarea.value.length;
            counter.textContent = `${length} caracteres`;
        }

        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
}

// Persistência de abas
function initializeTabPersistence() {
    // Salva a aba ativa no localStorage
    const tabs = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            localStorage.setItem('bookEditActiveTab', e.target.getAttribute('data-bs-target'));
        });
    });

    // Restaura a última aba ativa
    const activeTab = localStorage.getItem('bookEditActiveTab');
    if (activeTab) {
        const tabToActivate = document.querySelector(`.nav-link[data-bs-target="${activeTab}"]`);
        if (tabToActivate) {
            const tab = new bootstrap.Tab(tabToActivate);
            tab.show();
        }
    }
}

// Função de notificação
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Auto-save (opcional)
function initializeAutoSave() {
    const form = document.getElementById('editBookForm');
    if (form) {
        let autoSaveTimeout;

        form.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Salva os dados do formulário no localStorage
                const formData = new FormData(form);
                const formObject = {};

                formData.forEach((value, key) => {
                    if (key !== 'capa') { // Não salva arquivos
                        formObject[key] = value;
                    }
                });

                localStorage.setItem('bookEditAutoSave', JSON.stringify(formObject));
                showNotification('Rascunho salvo automaticamente', 'success');
            }, 2000);
        });

        // Restaura dados salvos
        const savedData = localStorage.getItem('bookEditAutoSave');
        if (savedData) {
            const formObject = JSON.parse(savedData);

            // Verifica se é o mesmo livro
            const bookId = form.dataset.bookId;
            if (formObject.bookId === bookId) {
                // Pergunta se quer restaurar
                if (confirm('Existe um rascunho salvo deste formulário. Deseja restaurá-lo?')) {
                    Object.keys(formObject).forEach(key => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input) {
                            input.value = formObject[key];
                        }
                    });
                }
            }
        }
    }
}

// Exporta funções para uso global
window.initializeBookEdit = initializeBookEdit;