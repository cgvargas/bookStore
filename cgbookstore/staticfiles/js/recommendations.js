/**
 * Sistema de Recomendações - CG.BookStore.Online
 * Gerencia interações com livros recomendados e modais relacionados
 * Versão corrigida para tratar bugs específicos
 */
document.addEventListener('DOMContentLoaded', function() {
  // Elementos do modal de livro externo
  const externalBookModal = document.getElementById('externalBookModal');
  const externalBookCover = document.getElementById('externalBookCover');
  const externalBookTitle = document.getElementById('externalBookTitle');
  const externalBookAuthor = document.getElementById('externalBookAuthor')?.querySelector('span');
  const externalBookCategories = document.getElementById('externalBookCategories')?.querySelector('span');
  const externalBookPublisher = document.getElementById('externalBookPublisher')?.querySelector('span');
  const externalBookYear = document.getElementById('externalBookYear')?.querySelector('span');
  const externalBookPages = document.getElementById('externalBookPages')?.querySelector('span');
  const externalBookDescription = document.getElementById('externalBookDescription');
  const closeExternalModalBtn = document.getElementById('closeExternalModal');
  const addExternalBookBtn = document.getElementById('addExternalBookToShelf');

  // Elementos do modal de seleção de prateleira
  const shelfSelectionModal = document.getElementById('shelfSelectionModal');
  const shelfOptions = document.querySelectorAll('.shelf-option');
  const confirmShelfSelectionBtn = document.getElementById('confirmShelfSelection');
  const cancelShelfSelectionBtn = document.getElementById('cancelShelfSelection');

  // Variáveis de estado
  let selectedShelf = null;
  let currentExternalBook = null;

  // Verificar se estamos na página com os modais inicializados
  const hasModals = externalBookModal && shelfSelectionModal;

  // Inicializar componentes
  initializeComponents();

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

  // Inicializar componentes e eventos da página
  function initializeComponents() {
    // Adicionar livro à prateleira
    const addToShelfButtons = document.querySelectorAll('.add-to-shelf-btn');
    if (addToShelfButtons.length > 0) {
      addToShelfButtons.forEach(button => {
        button.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();

          // Feedback visual imediato
          this.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Adicionando...';
          this.disabled = true;

          const bookId = this.dataset.bookId;
          const shelfType = this.dataset.shelfType;

          addBookToShelf(bookId, shelfType, this);
        });
      });
    }

    // Configurar eventos dos modais se estiverem presentes
    if (hasModals) {
      // Fechar modal
      if (closeExternalModalBtn) {
        closeExternalModalBtn.addEventListener('click', function(e) {
          e.preventDefault();
          closeAllModals();
        });
      }

      // Iniciar processo de adicionar à prateleira
      if (addExternalBookBtn) {
        addExternalBookBtn.addEventListener('click', function(e) {
          e.preventDefault();

          // Feedback visual
          this.disabled = true;
          this.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processando...';

          // Transição entre modais
          externalBookModal.classList.remove('active');
          setTimeout(() => {
            externalBookModal.style.display = 'none';

            // Resetar botão
            this.innerHTML = 'Adicionar à minha prateleira';
            this.disabled = false;

            // Mostrar seleção de prateleira
            shelfSelectionModal.style.display = 'flex';
            setTimeout(() => {
              shelfSelectionModal.classList.add('active');
            }, 10);
          }, 300);
        });
      }

      // Opções de prateleira
      if (shelfOptions.length > 0) {
        shelfOptions.forEach(option => {
          option.addEventListener('click', function(e) {
            e.preventDefault();

            selectedShelf = this.dataset.shelf;

            // Atualizar visual
            shelfOptions.forEach(opt => {
              opt.classList.remove('ring-2', 'ring-indigo-500', 'bg-indigo-50');
            });
            this.classList.add('ring-2', 'ring-indigo-500', 'bg-indigo-50');
          });
        });
      }

      // Confirmar seleção
      if (confirmShelfSelectionBtn) {
        confirmShelfSelectionBtn.addEventListener('click', function(e) {
          e.preventDefault();

          if (!selectedShelf) {
            showNotification('Por favor, selecione uma prateleira', 'error');
            return;
          }

          // Feedback visual
          this.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processando...';
          this.disabled = true;

          if (currentExternalBook) {
            importExternalBook(currentExternalBook, selectedShelf);
          }
        });
      }

      // Cancelar
      if (cancelShelfSelectionBtn) {
        cancelShelfSelectionBtn.addEventListener('click', function(e) {
          e.preventDefault();
          closeAllModals();
        });
      }

      // Fechar ao clicar fora
      window.addEventListener('click', function(event) {
        if (event.target === externalBookModal) {
          closeAllModals();
        }
        if (event.target === shelfSelectionModal) {
          closeAllModals();
        }
      });

      // Fechar com ESC
      document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
          closeAllModals();
        }
      });
    }

    // Marcar todos livros externos com badge visual
    const externalLinks = document.querySelectorAll('.external-book');
    if (externalLinks.length > 0) {
      externalLinks.forEach(link => {
        if (!link.querySelector('.external-badge')) {
          const badge = document.createElement('span');
          badge.className = 'external-badge';
          badge.textContent = 'Google Books';
          link.appendChild(badge);
        }
      });
    }
  }

  // Delegação de eventos para livros externos (inclui livros carregados dinamicamente)
  document.addEventListener('click', function(e) {
    const externalBookLink = e.target.closest('.external-book');
    if (externalBookLink) {
      e.preventDefault();
      e.stopPropagation();

      const externalId = externalBookLink.dataset.bookExternalId;
      if (!externalId) return;

      // Captura dados básicos do livro do DOM
      const bookCard = externalBookLink.closest('.book-card');
      const title = bookCard.querySelector('.book-title')?.textContent || '';
      const author = bookCard.querySelector('.book-author')?.textContent || '';
      const coverImg = externalBookLink.querySelector('img');
      const coverUrl = coverImg ? coverImg.src : '';

      // Mostrar modal com dados iniciais
      showExternalBookModal({
        title: title,
        author: author,
        coverUrl: coverUrl
      });

      // Tratamento especial para IDs negativos
      if (externalId.startsWith('-')) {
        console.log("Livro com ID negativo detectado: " + externalId + ". Usando dados locais.");

        // Criar objeto com dados mínimos existentes no DOM
        const bookData = {
          id: externalId,
          volumeInfo: {
            title: title,
            authors: author.split(',').map(a => a.trim()),
            description: "Detalhes completos indisponíveis para este livro. Você pode adicioná-lo à sua prateleira mesmo assim.",
            imageLinks: { thumbnail: coverUrl },
            categories: []
          }
        };

        // Extrair categorias, se disponíveis
        const genreElement = bookCard.querySelector('.book-genre');
        if (genreElement && genreElement.textContent) {
          bookData.volumeInfo.categories = [genreElement.textContent.trim()];
        }

        updateExternalBookModal(bookData);
        currentExternalBook = bookData;
      } else {
        // Para IDs normais, buscar na API
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

            // Fallback para dados locais
            const fallbackData = {
              id: externalId,
              volumeInfo: {
                title: title,
                authors: author ? [author] : ['Autor desconhecido'],
                imageLinks: { thumbnail: coverUrl },
                description: "Não foi possível carregar detalhes completos. Você ainda pode adicionar o livro à sua prateleira."
              }
            };

            updateExternalBookModal(fallbackData);
            currentExternalBook = fallbackData;

            showNotification('Usando informações limitadas para este livro', 'info');
          });
      }
    }
  });

  // Função para mostrar modal com dados iniciais
  function showExternalBookModal(data) {
    if (!hasModals) return;

    if (externalBookTitle) {
      externalBookTitle.textContent = data.title || 'Carregando detalhes...';
    }

    if (externalBookAuthor) {
      externalBookAuthor.textContent = data.author || 'Carregando...';
    }

    if (externalBookCover) {
      externalBookCover.src = data.coverUrl || '/static/images/no-cover.svg';

      externalBookCover.onerror = function() {
        this.src = '/static/images/no-cover.svg';
      };
    }

    // Resetar outros campos
    if (externalBookCategories) externalBookCategories.textContent = 'Carregando...';
    if (externalBookPublisher) externalBookPublisher.textContent = 'Carregando...';
    if (externalBookYear) externalBookYear.textContent = 'Carregando...';
    if (externalBookPages) externalBookPages.textContent = 'Carregando...';
    if (externalBookDescription) externalBookDescription.textContent = 'Carregando descrição...';

    // Mostrar modal
    externalBookModal.classList.remove('d-none');
    externalBookModal.style.display = 'flex';
    setTimeout(() => {
      externalBookModal.classList.add('active');
    }, 10);
  }

  // Função para atualizar modal com dados completos
  function updateExternalBookModal(bookData) {
    if (!hasModals) return;

    const volumeInfo = bookData.volumeInfo || {};

    if (externalBookTitle) {
      externalBookTitle.textContent = volumeInfo.title || 'Título indisponível';
    }

    if (externalBookAuthor) {
      externalBookAuthor.textContent = volumeInfo.authors
        ? volumeInfo.authors.join(', ')
        : 'Autor desconhecido';
    }

    if (externalBookCategories) {
      externalBookCategories.textContent = volumeInfo.categories
        ? volumeInfo.categories.join(', ')
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
      externalBookPages.textContent = volumeInfo.pageCount || '-';
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
        || 'Sem descrição disponível para este livro.';
    }

    if (addExternalBookBtn) {
      addExternalBookBtn.disabled = false;
      addExternalBookBtn.innerHTML = 'Adicionar à minha prateleira';
    }
  }

  // Função para adicionar livro à prateleira - CORRIGIDO
  function addBookToShelf(bookId, shelfType, buttonElement = null) {
    if (!bookId || !shelfType) {
      console.error("ID do livro ou tipo de prateleira inválido");
      return;
    }

    // Feedback visual
    if (buttonElement) {
      buttonElement.disabled = true;
      buttonElement.classList.add('opacity-75');
      buttonElement.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Adicionando...';
    }

    // IMPORTANTE: Enviar como form-urlencoded e não como JSON
    // Isso corrige o erro "Expecting value: line 1 column 1 (char 0)"
    fetch('/books/add-to-shelf/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: `book_id=${encodeURIComponent(bookId)}&shelf=${encodeURIComponent(shelfType)}`
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success' || data.success === true) {
        if (buttonElement) {
          buttonElement.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg> Adicionado';
          buttonElement.classList.remove('bg-indigo-600', 'hover:bg-indigo-700', 'opacity-75');
          buttonElement.classList.add('bg-green-600', 'hover:bg-green-700', 'added');
          buttonElement.disabled = true;
        } else {
          closeAllModals();
          showNotification(data.message || 'Livro adicionado com sucesso!', 'success');
        }
      } else {
        if (buttonElement) {
          buttonElement.disabled = false;
          buttonElement.classList.remove('opacity-75');
          buttonElement.innerHTML = 'Adicionar à prateleira';
        }
        showNotification(data.message || data.error || 'Erro ao adicionar livro', 'error');
      }
    })
    .catch(error => {
      console.error('Erro:', error);
      if (buttonElement) {
        buttonElement.disabled = false;
        buttonElement.classList.remove('opacity-75');
        buttonElement.innerHTML = 'Adicionar à prateleira';
      }
      showNotification('Ocorreu um erro ao adicionar o livro. Tente novamente.', 'error');
    });
  }

  // Função para importar livro externo - CORRIGIDO
  function importExternalBook(externalBookData, shelfType) {
    if (!confirmShelfSelectionBtn) return;

    // Feedback visual
    confirmShelfSelectionBtn.disabled = true;
    confirmShelfSelectionBtn.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Processando...';

    // Validação
    if (!externalBookData || !externalBookData.id) {
      showNotification('Dados do livro inválidos ou incompletos', 'error');
      resetConfirmButton();
      return;
    }

    // CORREÇÃO: Ajustar os nomes dos campos para corresponder ao modelo Book
    const bookData = {
      external_id: externalBookData.id,
      titulo: externalBookData.volumeInfo?.title || 'Livro sem título',
      autor: externalBookData.volumeInfo?.authors ? externalBookData.volumeInfo.authors[0] : 'Desconhecido',
      capa_url: externalBookData.volumeInfo?.imageLinks ? externalBookData.volumeInfo.imageLinks.thumbnail : '',
      editora: externalBookData.volumeInfo?.publisher || '',
      data_publicacao: externalBookData.volumeInfo?.publishedDate || '',
      descricao: externalBookData.volumeInfo?.description || '',
      numero_paginas: externalBookData.volumeInfo?.pageCount || 0,
      categoria: externalBookData.volumeInfo?.categories ? externalBookData.volumeInfo.categories.join(',') : '',
      idioma: externalBookData.volumeInfo?.language || 'pt',
      shelf_type: shelfType
    };

    fetch('/books/import-external/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(bookData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success') {
        closeAllModals();
        showNotification('Livro importado com sucesso!', 'success');

        // Adicionar à prateleira
        if (data.book_id) {
          addBookToShelf(data.book_id, shelfType);
        }
      } else {
        showNotification(data.message || 'Erro ao importar livro', 'error');
        resetConfirmButton();

        // Tentar alternativa
        setTimeout(() => {
          addExternalToShelfDirect(externalBookData, shelfType);
        }, 1000);
      }
    })
    .catch(error => {
      console.error('Erro ao importar livro:', error);
      resetConfirmButton();

      showNotification('Erro ao importar livro. Tentando método alternativo...', 'info');

      // Tentar método alternativo
      setTimeout(() => {
        addExternalToShelfDirect(externalBookData, shelfType);
      }, 1000);
    });
  }

  // Função para adicionar livro externo diretamente - CORRIGIDO
  function addExternalToShelfDirect(externalBookData, shelfType) {
    // Validar dados
    if (!externalBookData || !externalBookData.id || !shelfType) {
      showNotification('Dados insuficientes para adicionar o livro', 'error');
      resetConfirmButton();
      return;
    }

    // Cópia segura dos dados
    const safeBookData = {
      id: externalBookData.id,
      volumeInfo: {
        title: externalBookData.volumeInfo?.title || 'Livro sem título',
        authors: externalBookData.volumeInfo?.authors || ['Autor desconhecido'],
        description: externalBookData.volumeInfo?.description || '',
        publisher: externalBookData.volumeInfo?.publisher || '',
        publishedDate: externalBookData.volumeInfo?.publishedDate || '',
        pageCount: externalBookData.volumeInfo?.pageCount || 0,
        categories: externalBookData.volumeInfo?.categories || [],
        imageLinks: externalBookData.volumeInfo?.imageLinks || {}
      }
    };

    // CORREÇÃO: Usar external_id em vez de google_books_id
    const bookData = {
      external_id: externalBookData.id,
      external_data: JSON.stringify(safeBookData),
      shelf_type: shelfType
    };

    fetch('/books/add-external-to-shelf/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(bookData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.status === 'success') {
        closeAllModals();
        showNotification('Livro adicionado com sucesso!', 'success');
      } else {
        showNotification(data.message || 'Erro ao adicionar livro externo', 'error');
      }
    })
    .catch(error => {
      console.error('Erro ao adicionar livro externo:', error);
      showNotification('Não foi possível adicionar o livro. Por favor, tente novamente mais tarde.', 'error');
    })
    .finally(() => {
      resetConfirmButton();
    });
  }

  // Função para fechar todos os modais
  function closeAllModals() {
    if (!hasModals) return;

    // Remover classes ativas
    if (externalBookModal) externalBookModal.classList.remove('active');
    if (shelfSelectionModal) shelfSelectionModal.classList.remove('active');

    // Fechar modais após animação
    setTimeout(() => {
      if (externalBookModal) {
        externalBookModal.style.display = 'none';
        externalBookModal.classList.add('d-none');
      }

      if (shelfSelectionModal) {
        shelfSelectionModal.style.display = 'none';
        shelfSelectionModal.classList.add('d-none');
      }

      // Resetar estados
      selectedShelf = null;
      currentExternalBook = null;

      // Resetar seleção visual
      if (shelfOptions && shelfOptions.length) {
        shelfOptions.forEach(opt => {
          opt.classList.remove('ring-2', 'ring-indigo-500', 'bg-indigo-50');
        });
      }

      // Resetar botões
      resetConfirmButton();

      if (addExternalBookBtn) {
        addExternalBookBtn.disabled = false;
        addExternalBookBtn.innerHTML = 'Adicionar à minha prateleira';
      }
    }, 300);
  }

  // Função para resetar botão de confirmação
  function resetConfirmButton() {
    if (!confirmShelfSelectionBtn) return;

    confirmShelfSelectionBtn.disabled = false;
    confirmShelfSelectionBtn.innerHTML = 'Confirmar';
  }

  // Função para mostrar notificação
  function showNotification(message, type = 'info') {
    if (!message) return;

    // Remover notificações existentes
    const existingNotifications = document.querySelectorAll('.notification-toast');
    existingNotifications.forEach(notification => notification.remove());

    // Criar notificação
    const notification = document.createElement('div');
    notification.className = `notification-toast ${type}`;
    notification.textContent = message;

    // Adicionar botão de fechar
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.className = 'ml-3 font-bold hover:text-white';
    closeBtn.onclick = function() {
      notification.classList.remove('active');
      setTimeout(() => notification.remove(), 300);
    };
    notification.appendChild(closeBtn);

    // Estilizar notificação
    notification.style.position = 'fixed';
    notification.style.bottom = '1rem';
    notification.style.right = '1rem';
    notification.style.padding = '0.75rem 1.25rem';
    notification.style.borderRadius = '0.375rem';
    notification.style.backgroundColor =
      type === 'success' ? '#10b981' :
      type === 'error' ? '#ef4444' :
      type === 'info' ? '#3b82f6' : '#3b82f6';
    notification.style.color = 'white';
    notification.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    notification.style.zIndex = '100';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    notification.style.display = 'flex';
    notification.style.alignItems = 'center';
    notification.style.justifyContent = 'space-between';
    document.body.appendChild(notification);

    // Mostrar com animação
    setTimeout(() => {
      notification.style.opacity = '1';
    }, 10);

    // Auto-remover após 4 segundos
    const timeout = setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        if (document.body.contains(notification)) {
          notification.remove();
        }
      }, 300);
    }, 4000);

    // Pausar timeout ao passar o mouse
    notification.addEventListener('mouseenter', () => {
      clearTimeout(timeout);
    });

    // Reiniciar timeout ao tirar o mouse
    notification.addEventListener('mouseleave', () => {
      setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
          if (document.body.contains(notification)) {
            notification.remove();
          }
        }, 300);
      }, 2000);
    });
  }
});