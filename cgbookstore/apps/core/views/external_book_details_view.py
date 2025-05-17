import json
import uuid
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import gettext as _

from cgbookstore.apps.core.models.book import Book
# Importação corrigida para usar o serviço centralizado
from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient

import logging

logger = logging.getLogger(__name__)


@login_required
def external_book_details_view(request, external_id):
    """
    View para exibir detalhes de um livro externo (Google Books).
    Cria uma entrada temporária no banco de dados para exibição.
    """
    if not external_id:
        raise Http404(_("ID do livro externo não fornecido"))

    try:
        # Verificar se já existe um livro com este ID externo
        existing_book = Book.objects.filter(external_id=external_id).first()

        if existing_book:
            # Se o livro já existe, simplesmente redireciona para a página de detalhes
            return redirect('book_details', book_id=existing_book.id)

        # Buscar detalhes do livro externo
        client = GoogleBooksClient(context="recommendations")
        external_data = client.get_book_by_id(external_id)

        if not external_data:
            raise Http404(_("Livro externo não encontrado"))

        # Processar os dados para criar um livro temporário
        volume_info = external_data.get('volumeInfo', {})

        # Extrair campos do formato volumeInfo
        titulo = volume_info.get('title', 'Título desconhecido')

        if 'authors' in volume_info:
            if isinstance(volume_info['authors'], list):
                autor = ', '.join(volume_info['authors'])
            else:
                autor = str(volume_info['authors'])
        else:
            autor = 'Autor desconhecido'

        editora = volume_info.get('publisher', '')
        data_publicacao_str = volume_info.get('publishedDate', '')
        descricao = volume_info.get('description', '')
        numero_paginas = volume_info.get('pageCount', 0)

        if 'categories' in volume_info:
            if isinstance(volume_info['categories'], list):
                genero = volume_info['categories'][0] if volume_info['categories'] else ''
            else:
                genero = str(volume_info['categories'])
        else:
            genero = ''

        idioma = volume_info.get('language', 'pt')
        capa_url = volume_info.get('imageLinks', {}).get('thumbnail', '')

        # Processar data de publicação
        data_publicacao = None
        if data_publicacao_str:
            try:
                # Tenta converter para data
                if len(data_publicacao_str) >= 10:  # Formato completo YYYY-MM-DD
                    data_publicacao = datetime.strptime(data_publicacao_str[:10], '%Y-%m-%d').date()
                elif len(data_publicacao_str) >= 7:  # Formato YYYY-MM
                    data_publicacao = datetime.strptime(data_publicacao_str[:7], '%Y-%m').date()
                elif len(data_publicacao_str) >= 4:  # Apenas ano YYYY
                    data_publicacao = datetime.strptime(f"{data_publicacao_str[:4]}-01-01", '%Y-%m-%d').date()
            except ValueError:
                # Se falhar na conversão, mantém como None
                data_publicacao = None

        # Criar livro temporário no banco de dados
        temp_book = Book.objects.create(
            titulo=titulo,
            autor=autor,
            editora=editora,
            data_publicacao=data_publicacao,
            descricao=descricao,
            numero_paginas=numero_paginas if isinstance(numero_paginas, int) else 0,
            genero=genero,
            idioma=idioma,
            capa_url=capa_url,
            external_id=external_id,
            is_temporary=True,
            external_data=json.dumps(external_data),
            origem='Google Books'
        )

        # Redirecionar para a página de detalhes do livro
        return redirect('book_details', book_id=temp_book.id)

    except Exception as e:
        logger.error(f"Erro ao processar livro externo: {str(e)}")
        # Trate o erro e exiba uma mensagem para o usuário
        return render(request, 'core/error.html', {
            'error_message': _(
                "Não foi possível carregar os detalhes do livro externo. Por favor, tente novamente mais tarde.")
        })