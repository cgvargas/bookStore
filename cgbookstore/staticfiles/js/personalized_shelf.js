/**
 * Sistema de Recomendações - CG.BookStore.Online
 * Gerencia interações com livros recomendados e modais relacionados
 */
document.addEventListener('DOMContentLoaded', function() {
  // Elementos do modal de livro externo
  const externalBookModal = document.getElementById('externalBookModal');
  const externalBookCover = document.getElementById('externalBookCover');
  const externalBookTitle = document.getElementById('externalBookTitle');
  const externalBookAuthor = document.getElementById('externalBookAuthor');
  const externalBookCategories = document.getElementById('externalBookCategories');
  const externalBookPublisher = document.getElementById('externalBookPublisher');
  const externalBookYear = document.getElementById('externalBookYear');
  const externalBookPages = document.getElementById('externalBookPages');
  const externalBookDescription = document.getElementById('externalBookDescription');
  const addExternalBookToShelf = document.getElementById('addExternalBookToShelf');
  const externalBookIdInput = document.getElementById('externalBookId');

  // Elementos do modal de seleção de prateleira
  const shelfModal = document.getElementById('shelfModal');
  const shelfOptions = document.querySelectorAll('.shelf-option');
  const selectedBookIdInput = document.getElementById('selectedBookId');
  const isExternalBookInput = document.getElementById('isExternalBook');

  // Variáveis de estado
  let currentExternalBook = null;
  let selectedShelf = null;

  // Verificar se estamos na página com os modais inicializados
  const hasModals = externalBookModal && shelfModal;

  // Inicialização de Bootstrap Modals
  let externalBookModalInstance = null;
  let shelfModalInstance = null;

  if (hasModals) {
    externalBookModalInstance = new bootstrap.Modal(externalBookModal);
    shelfModalInstance = new bootstrap.Modal(shelfModal);
  }

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

  // Delegação de eventos para livros externos
  document.addEventListener('click', function(e) {
    // Livros externos - abrir modal de detalhes
    const externalBookLink = e.target.closest('.external-book');
    if (externalBookLink && hasModals) {
      e.preventDefault();

      // Obter ID do livro
      const externalId = externalBookLink.dataset.bookExternalId;
      console.log("Clicou em livro externo com ID:", externalId);

      if (!externalId) {
        console.error("ID do livro externo não encontrado");
        return;
      }

      // Dados básicos do livro do DOM para feedback imediato
      const bookCard = externalBookLink.closest('.card');
      const title = bookCard.querySelector('.card-title')?.textContent || 'Carregando...';
      const author = bookCard.querySelector('.card-body .text-muted')?.textContent?.trim() || 'Carregando...';
      const coverImg = bookCard.querySelector('img');
      const coverUrl = coverImg ? coverImg.src : '';

      // Mostrar modal com dados iniciais enquanto carrega os detalhes
      showExternalBookModal({
        title: title,
        author: author,
        coverUrl: coverUrl
      });

      // Armazenar ID do livro externo no campo oculto
      if (externalBookIdInput) {
        externalBookIdInput.value = externalId;
      }

      // Buscar detalhes completos do livro externo
      fetchExternalBookDetails(externalId);
    }

    // Botão para adicionar livro à prateleira
    const addToShelfBtn = e.target.closest('.add-to-shelf-btn');
    if (addToShelfBtn && hasModals) {
      e.preventDefault();

      // Armazenar ID do livro local
      if (selectedBookIdInput) {
        selectedBookIdInput.value = addToShelfBtn.dataset.bookId;
      }

      // Indicar que é um livro local (não externo)
      if (isExternalBookInput) {
        isExternalBookInput.value = '0';
      }

      // Resetar seleção de prateleira
      selectedShelf = null;
      resetShelfSelection();
    }
  });

  // Adicionar evento ao botão para adicionar livro externo à prateleira
  if (addExternalBookToShelf) {
    addExternalBookToShelf.addEventListener('click', function() {
      if (!currentExternalBook) {
        showNotification('Erro: Dados do livro não carregados', 'error');
        return;
      }

      // Fechar modal de detalhes
      if (externalBookModalInstance) {
        externalBookModalInstance.hide();
      }

      // Armazenar dados para o modal de seleção de prateleira
      if (selectedBookIdInput && externalBookIdInput) {
        selectedBookIdInput.value = externalBookIdInput.value;
      }

      if (isExternalBookInput) {
        isExternalBookInput.value = '1';
      }

      // Resetar seleção de prateleira
      selectedShelf = null;
      resetShelfSelection();

      // Abrir modal de seleção de prateleira
      if (shelfModalInstance) {
        shelfModalInstance.show();
      }
    });
  }

  // Inicializar eventos para opções de prateleira
  if (shelfOptions.length > 0) {
    shelfOptions.forEach(option => {
      option.addEventListener('click', function() {
        selectedShelf = this.dataset.shelf;

        // Atualizar visual
        shelfOptions.forEach(opt => {
          opt.classList.remove('active', 'bg-light');
        });
        this.classList.add('active', 'bg-light');

        // Para livros locais, adicionar diretamente
        if (selectedBookIdInput && isExternalBookInput &&
            selectedBookIdInput.value && isExternalBookInput.value === '0') {
          addBookToShelf(selectedBookIdInput.value, selectedShelf);
          closeAllModals();
        }
      });
    });
  }

  // Função para mostrar modal com dados iniciais
  function showExternalBookModal(data) {
    if (!hasModals) return;

    if (externalBookTitle) externalBookTitle.textContent = data.title || 'Carregando...';
    if (externalBookAuthor) externalBookAuthor.textContent = data.author || 'Carregando...';
    if (externalBookCover) {
      externalBookCover.src = data.coverUrl || '/static/images/no-cover.svg';
      externalBookCover.onerror = function() {
        this.src = '/static/images/no-cover.svg';
      };
    }

    // Resetar outros campos
    if (externalBookCategories) externalBookCategories.textContent = '-';
    if (externalBookPublisher) externalBookPublisher.textContent = '-';
    if (externalBookYear) externalBookYear.textContent = '-';
    if (externalBookPages) externalBookPages.textContent = '-';
    if (externalBookDescription) externalBookDescription.textContent = 'Carregando descrição...';

    // Mostrar modal
    if (externalBookModalInstance) {
      externalBookModalInstance.show();
    }
  }

  // Função para buscar detalhes do livro externo
  function fetchExternalBookDetails(externalId) {
    console.log("Buscando detalhes do livro:", externalId);

    // Verificar se é um ID válido
    if (!externalId) {
      console.error("ID externo inválido");
      return;
    }

    // Verificar se é um ID temporário
    if (externalId.startsWith('-') || externalId.startsWith('temp_')) {
      console.warn("ID temporário detectado, usando dados básicos");
      return;
    }

    fetch(`/api/recommendations/book/${externalId}/`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Dados do livro recebidos:", data);
        updateExternalBookModal(data);
        currentExternalBook = data;
      })
      .catch(error => {
        console.error("Erro ao carregar detalhes do livro:", error);
        showNotification("Não foi possível carregar todos os detalhes do livro", "error");
      });
  }

  // Função para atualizar modal com dados completos
  function updateExternalBookModal(bookData) {
    if (!hasModals) return;

    const volumeInfo = bookData.volumeInfo || bookData;

    if (externalBookTitle) {
      externalBookTitle.textContent = volumeInfo.title || 'Título indisponível';
    }

    if (externalBookAuthor) {
      if (volumeInfo.authors) {
        externalBookAuthor.textContent = Array.isArray(volumeInfo.authors)
          ? volumeInfo.authors.join(', ')
          : volumeInfo.authors;
      } else {
        externalBookAuthor.textContent = 'Autor desconhecido';
      }
    }

    if (externalBookCategories) {
      if (volumeInfo.categories) {
        externalBookCategories.textContent = Array.isArray(volumeInfo.categories)
          ? volumeInfo.categories.join(', ')
          : volumeInfo.categories;
      } else {
        externalBookCategories.textContent = '-';
      }
    }

    if (externalBookPublisher) {
      externalBookPublisher.textContent = volumeInfo.publisher || '-';
    }

    if (externalBookYear) {
      externalBookYear.textContent = volumeInfo.publishedDate
        ? volumeInfo.publishedDate.substring(0, 4)
        : '-';
    }

    if (externalBookPages) {
      externalBookPages.textContent = volumeInfo.pageCount
        ? `${volumeInfo.pageCount} páginas`
        : '-';
    }

    if (externalBookCover) {
      if (volumeInfo.imageLinks && volumeInfo.imageLinks.thumbnail) {
        externalBookCover.src = volumeInfo.imageLinks.thumbnail;
      }
      externalBookCover.onerror = function() {
        this.src = '/static/images/no-cover.svg';
      };
    }

    if (externalBookDescription) {
      externalBookDescription.textContent = volumeInfo.description
        || 'Sem descrição disponível.';
    }

    // Habilitar botão de adicionar
    if (addExternalBookToShelf) {
      addExternalBookToShelf.disabled = false;
    }
  }

  // Função para adicionar livro à prateleira
  function addBookToShelf(bookId, shelfType) {
    if (!bookId || !shelfType) {
      console.error("ID do livro ou tipo de prateleira inválido");
      return;
    }

    console.log("Adicionando livro à prateleira:", bookId, shelfType);

    fetch('/books/add-to-shelf/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: `book_id=${encodeURIComponent(bookId)}&shelf=${encodeURIComponent(shelfType)}`
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success' || data.success) {
        showNotification('Livro adicionado com sucesso!', 'success');

        // Atualizar UI - marcar botão como adicionado
        const button = document.querySelector(`.add-to-shelf-btn[data-book-id="${bookId}"]`);
        if (button) {
          button.innerHTML = '<i class="bi bi-check-circle me-2"></i>Adicionado';
          button.classList.remove('btn-outline-primary');
          button.classList.add('btn-success');
          button.disabled = true;
        }
      } else {
        showNotification(data.message || 'Erro ao adicionar livro', 'error');
      }
    })
    .catch(error => {
      console.error("Erro na requisição:", error);
      showNotification('Erro ao adicionar livro à prateleira', 'error');
    });
  }

  // Função para adicionar livro externo à prateleira
  function addExternalBookToShelf(externalBookData, shelfType) {
    if (!currentExternalBook || !selectedShelf) {
      showNotification("Dados insuficientes para adicionar o livro", "error");
      return;
    }

    console.log("Adicionando livro externo:", externalBookIdInput.value, shelfType);

    // Criar objeto com dados mínimos necessários
    const requestData = {
      external_id: externalBookIdInput.value,
      external_data: JSON.stringify(currentExternalBook),
      shelf_type: shelfType
    };

    fetch('/api/recommendations/add-external-book/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        showNotification('Livro externo adicionado com sucesso!', 'success');
        closeAllModals();
      } else {
        showNotification(data.message || 'Erro ao adicionar livro externo', 'error');
      }
    })
    .catch(error => {
      console.error("Erro na requisição:", error);
      showNotification('Erro ao adicionar livro externo', 'error');
    });
  }

  // Função para resetar seleção de prateleira
  function resetShelfSelection() {
    if (shelfOptions) {
      shelfOptions.forEach(option => {
        option.classList.remove('active', 'bg-light');
      });
    }
  }

  // Função para fechar todos os modais
  function closeAllModals() {
    if (externalBookModalInstance) {
      externalBookModalInstance.hide();
    }

    if (shelfModalInstance) {
      shelfModalInstance.hide();
    }

    // Resetar estado
    currentExternalBook = null;
    selectedShelf = null;
  }

  // Função para mostrar notificação
  function showNotification(message, type = 'info') {
    // Remove notificações existentes
    const existingNotifications = document.querySelectorAll('.notification-toast');
    existingNotifications.forEach(notification => notification.remove());

    // Criar nova notificação
    const notification = document.createElement('div');
    notification.className = `notification-toast ${type}`;
    notification.textContent = message;

    // Estilizar notificação
    notification.style.position = 'fixed';
    notification.style.bottom = '1rem';
    notification.style.right = '1rem';
    notification.style.padding = '0.75rem 1.25rem';
    notification.style.borderRadius = '0.375rem';
    notification.style.backgroundColor =
      type === 'success' ? '#10b981' :
      type === 'error' ? '#ef4444' :
      '#3b82f6';
    notification.style.color = 'white';
    notification.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    notification.style.zIndex = '9999';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    document.body.appendChild(notification);

    // Mostrar com animação
    setTimeout(() => {
      notification.style.opacity = '1';
    }, 10);

    // Auto-remover após 3 segundos
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
        }
      }, 300);
    }, 3000);
  }

  // Confirmar seleção de prateleira (para livros externos)
  const confirmShelfBtn = document.getElementById('confirmShelfSelection');
  if (confirmShelfBtn) {
    confirmShelfBtn.addEventListener('click', function() {
      if (!selectedShelf) {
        showNotification('Por favor, selecione uma prateleira', 'error');
        return;
      }

      if (isExternalBookInput && isExternalBookInput.value === '1') {
        addExternalBookToShelf(currentExternalBook, selectedShelf);
      }
    });
  }

  // Cancelar seleção
  const cancelShelfBtn = document.getElementById('cancelShelfSelection');
  if (cancelShelfBtn) {
    cancelShelfBtn.addEventListener('click', closeAllModals);
  }
});