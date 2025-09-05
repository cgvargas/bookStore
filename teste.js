// ✅ FUNÇÃO CORRIGIDA PARA ADICIONAR À PRATELEIRA
    async function addToShelf(shelf, bookIndex) {
        if (state.isProcessing) return;
        state.isProcessing = true;

        console.log(`[ADICIONAR] Tentando adicionar livro índice ${bookIndex} à prateleira "${shelf}"`);

        try {
            const book = state.currentBooks[bookIndex];
            const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

            if (!book) {
                throw new Error(`Livro não encontrado no índice ${bookIndex}`);
            }

            // ✅ VALIDAÇÃO ADICIONAL DOS DADOS DO LIVRO
            const validation = validateBookData(book);
            if (!validation.isValid) {
                throw new Error(`Dados do livro inválidos: ${validation.errors.join(', ')}`);
            }

            const sanitizedBook = validation.sanitized;
            console.log("[ADICIONAR] Dados do livro sanitizado:", sanitizedBook);

            let url;
            let payload;

            // ✅ CORREÇÃO: Usar dados sanitizados para decisão de rota
            if (sanitizedBook.source === 'local') {
                url = '/books/add-to-shelf/';
                payload = {
                    book_id: sanitizedBook.id,
                    shelf_type: shelf
                };
                console.log(`[LOCAL] Chamando URL: ${url} com payload:`, payload);

            } else if (sanitizedBook.source === 'google' || sanitizedBook.source === 'external') {
                url = '/books/add-external-to-shelf/';
                payload = {
                    book_data: {
                        titulo: sanitizedBook.titulo,
                        autores: sanitizedBook.autores,
                        descricao: sanitizedBook.descricao,
                        data_publicacao: sanitizedBook.data_publicacao !== 'N/A' ? sanitizedBook.data_publicacao : null,
                        capa_url: sanitizedBook.capa_url,
                        external_id: sanitizedBook.external_id,
                        editora: sanitizedBook.editora,
                    },
                    shelf_type: shelf
                };
                console.log(`[EXTERNO] Chamando URL: ${url} com payload:`, payload);

            } else {
                throw new Error(`Fonte do livro não reconhecida: "${sanitizedBook.source}"`);
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify(payload)
            });

            console.log("[RESPOSTA] Status:", response.status);
            const data = await response.json();
            console.log("[RESPOSTA] Dados:", data);

            if (response.ok && data.success) {
                const modalInstance = bootstrap.Modal.getInstance(elements.shelfModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                showAlert(data.message || 'Livro adicionado com sucesso!', 'success');
                setTimeout(() => { window.location.href = '/profile/'; }, 1500);
            } else {
                throw new Error(data.error || 'Erro desconhecido ao adicionar livro');
            }
        } catch (error) {
            console.error('[ERRO] Detalhes completos:', error);
            showAlert('Erro ao adicionar livro à prateleira: ' + error.message, 'danger');
        } finally {
            state.isProcessing = false;
        }
    }