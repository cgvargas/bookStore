/**
 * Prateleira Personalizada - CG.BookStore.Online
 * Script para gerenciar interações com a prateleira personalizada de recomendações
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

  // Elementos do modal de seleção de prateleira
  const shelfModal = document.getElementById('shelfModal');
  const shelfOptions = document.querySelectorAll('.shelf-option');

  // Variáveis de estado
  let currentExternalBook = null;
  let selectedShelf = null;
  let currentLocalBookId = null;

  // Inicialização de modais Bootstrap
  let externalBookModalInstance = null;
  let shelfModalInstance = null;

  if (externalBookModal) {
    externalBookModalInstance = new bootstrap.Modal(externalBookModal);
  }

  if (shelfModal) {
    shelfModalInstance = new bootstrap.Modal(shelfModal);
  }

  // Inicializar tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

  // Delegação de eventos para livros externos
  document.addEventListener('click', function(e) {
    // Livros externos - mostrar modal detalhado
    const externalBookLink = e.target.closest('.external-book');
    if (externalBookLink) {
      e.preventDefault();

      const externalId = externalBookLink.dataset.bookExternalId;
      if (!externalId) return;

      // Capturar dados básicos do livro da UI
      const bookCard = externalBookLink.closest('.card');
      const title = bookCard.querySelector('.card-title')?.textContent || '';
      const author = bookCard.querySelector('.text-muted')?.textContent?.trim() || '';
      const coverImg = bookCard.querySelector('img');
      const coverUrl = coverImg ? coverImg.src : '';

      // Mostrar modal com dados iniciais
      showExternalBookModal({
        title: title,
        author: author,
        coverUrl: coverUrl
      });

      // Buscar dados completos
      fetchExternalBookDetails(externalId);
    }

    // Botões de adicionar à prateleira
    const addToShelfBtn = e.target.closest('.add-to-shelf-btn');
    if (addToShelfBtn) {
      e.preventDefault();

      currentLocalBookId = addToShelfBtn.dataset.bookId;
      selectedShelf = null;

      // Resetar seleção visual no modal
      shelfOptions.forEach(option => {
        option.classList.remove('active', 'bg-light');
      });

      // Mostrar modal de seleção de prateleira
      if (shelfModalInstance) {
        shelfModalInstance.show();
      }
    }
  });

  // Inicializar eventos para opções de prateleira
  if (shelfOptions.length > 0) {
    shelfOptions.forEach(option => {
      option.addEventListener('click', function() {
        // Resetar seleção visual
        shelfOptions.forEach(opt => {
          opt.classList.remove('active', 'bg-light');
        });

        // Marcar como selecionado
        this.classList.add('active', 'bg-light');
        selectedShelf = this.dataset.shelf;

        // Se for para livro local, adicionar diretamente
        if (currentLocalBookId) {
          addBookToShelf(currentLocalBookId, selectedShelf);
          closeAllModals();
        }
      });
    });
  }

  // Botão para adicionar livro externo
  if (addExternalBookToShelf) {
    addExternalBookToShelf.addEventListener('click', function() {
      if (!currentExternalBook) {
        showNotification('Erro ao obter detalhes do livro', 'error');
        return;
      }

      // Fechar modal atual
      if (externalBookModalInstance) {
        externalBookModalInstance.hide();
      }

      // Resetar seleção visual
      shelfOptions.forEach(option => {
        option.classList.remove('active', 'bg-light');
      });

      // Mostrar modal de seleção de prateleira
      if (shelfModalInstance) {
        shelfModalInstance.show();
      }
    });
  }

  // Função para mostrar modal com dados iniciais
  function showExternalBookModal(data) {
    if (externalBookTitle) externalBookTitle.textContent = data.title || 'Carregando...';
    if (externalBookAuthor) externalBookAuthor.textContent = data.author || 'Carregando...';
    if (externalBookCover) externalBookCover.src = data.coverUrl || '/static/images/no-cover.svg';

    // Resetar outros campos
    if (externalBookCategories) externalBookCategories.textContent = '-';
    if (externalBookPublisher) externalBookPublisher.textContent = '-';
    if (externalBookYear) externalBookYear.textContent = '-';
    if (externalBookPages) externalBookPages.textContent = '-';
    if (externalBookDescription) externalBookDescription.textContent = 'Carregando descrição...';

    // Abrir modal
    if (externalBookModalInstance) {
      externalBookModalInstance.show();
    }
  }

  // Função para buscar detalhes do livro externo
  function fetchExternalBookDetails(externalId) {
    // Verificar se é um ID especial (identificador negativo)
    if (externalId.startsWith('-') || externalId.startsWith('temp_')) {
      // Livros temporários não têm endpoint de API, usar dados básicos
      showNotification('Usando dados limitados para este livro', 'info');
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
        updateExternalBookModal(data);
        currentExternalBook = data;
      })
      .catch(error => {
        console.error('Erro ao carregar detalhes:', error);
        showNotification('Erro ao carregar detalhes do livro', 'error');
      });
  }

  // Função para atualizar modal com dados completos
  function updateExternalBookModal(bookData) {
    const volumeInfo = bookData.volumeInfo || {};

    if (externalBookTitle) {
      externalBookTitle.textContent = volumeInfo.title || 'Título indisponível';
    }

    if (externalBookAuthor) {
      externalBookAuthor.textContent = volumeInfo.authors
        ? (Array.isArray(volumeInfo.authors) ? volumeInfo.authors.join(', ') : volumeInfo.authors)
        : 'Autor desconhecido';
    }

    if (externalBookCategories) {
      externalBookCategories.textContent = volumeInfo.categories
        ? (Array.isArray(volumeInfo.categories) ? volumeInfo.categories.join(', ') : volumeInfo.categories)
        : '-';
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
    }

    if (externalBookDescription) {
      externalBookDescription.textContent = volumeInfo.description
        || 'Descrição não disponível para este livro.';
    }
  }

  // Função para adicionar livro à prateleira
  function addBookToShelf(bookId, shelfType) {
    if (!bookId || !shelfType) return;

    // Mostrar notificação de processamento
    showNotification('Adicionando livro...', 'info');

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
      if (data.status === 'success' || data.success === true) {
        showNotification('Livro adicionado com sucesso!', 'success');

        // Atualizar UI - desabilitar botão
        const button = document.querySelector(`.add-to-shelf-btn[data-book-id="${bookId}"]`);
        if (button) {
          button.innerHTML = '<i class="bi bi-check-circle me-2"></i>Adicionado';
          button.classList.replace('btn-outline-primary', 'btn-success');
          button.disabled = true;
        }
      } else {
        showNotification(data.message || 'Erro ao adicionar livro', 'error');
      }
    })
    .catch(error => {
      console.error('Erro:', error);
      showNotification('Ocorreu um erro ao adicionar o livro', 'error');
    });
  }

  // Função para adicionar livro externo à prateleira
  function addExternalBookToShelf(externalBookData, shelfType) {
    if (!externalBookData || !shelfType) return;

    // Mostrar notificação de processamento
    showNotification('Processando livro externo...', 'info');

    // Verificar se temos dados completos
    if (!externalBookData.volumeInfo) {
      showNotification('Dados do livro incompletos', 'error');
      return;
    }

    // Preparar dados para a API
    const bookData = {
      external_id: externalBookData.id,
      external_data: JSON.stringify(externalBookData),
      shelf_type: shelfType
    };

    fetch('/api/recommendations/add-external-book/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(bookData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        showNotification('Livro externo adicionado com sucesso!', 'success');
      } else {
        showNotification(data.message || 'Erro ao adicionar livro externo', 'error');
      }
    })
    .catch(error => {
      console.error('Erro:', error);
      showNotification('Ocorreu um erro ao adicionar o livro externo', 'error');
    });
  }

  // Função para fechar todos os modais
  function closeAllModals() {
    if (externalBookModalInstance) {
      externalBookModalInstance.hide();
    }

    if (shelfModalInstance) {
      shelfModalInstance.hide();
    }

    // Resetar variáveis de estado
    currentExternalBook = null;
    selectedShelf = null;
    currentLocalBookId = null;
  }

  // Função para mostrar notificação
  function showNotification(message, type = 'info') {
    // Remover notificações existentes
    const existingNotifications = document.querySelectorAll('.notification-toast');
    existingNotifications.forEach(notification => notification.remove());

    // Criar nova notificação
    const notification = document.createElement('div');
    notification.className = `notification-toast ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    // Mostrar com animação
    setTimeout(() => {
      notification.classList.add('active');
    }, 10);

    // Auto-remover após 3 segundos
    setTimeout(() => {
      notification.classList.remove('active');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
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

  // Observador de mutações para inicializar componentes em conteúdo dinâmico
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.addedNodes && mutation.addedNodes.length > 0) {
        // Inicializar tooltips em qualquer novo conteúdo
        const newTooltips = mutation.target.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (newTooltips.length > 0) {
          [...newTooltips].map(tooltipEl => new bootstrap.Tooltip(tooltipEl));
        }
      }
    });
  });

  // Iniciar observação do documento
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});