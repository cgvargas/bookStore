"""
Módulo responsável pelas views relacionadas a livros.
Inclui busca, gerenciamento de prateleiras e detalhes dos livros.

Principais funcionalidades:
- Pesquisa de livros via Google Books API
- Gerenciamento de prateleiras de usuário
- Processamento de capas de livros
- Adição e remoção de livros
"""
import decimal
import json
import logging
from decimal import Decimal

import requests
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse
from django.core.files.storage import default_storage
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from ..models import UserBookShelf, Book
from ..services.google_books_client import GoogleBooksClient

# Configuração do logger para rastreamento de eventos de livros
logger = logging.getLogger(__name__)

# Instância global do cliente Google Books
google_books_client = GoogleBooksClient()

__all__ = [
    'BookSearchView',
    'BookDetailView',
    'search_books',
    'add_to_shelf',
    'remove_from_shelf',
    'get_book_details',
    'update_book',
    'move_book',
    'add_book_manual'
]


class BookManagementMixin:
    """
    Mixin com métodos utilitários para gerenciamento de livros.

    Fornece funcionalidades para processamento e manipulação de imagens de capas,
    com validações de tipo, tamanho e otimização.
    """

    @staticmethod
    def process_book_cover(cover_file):
        """
        Processa e valida o arquivo de capa do livro.

        Características:
        - Validação de tipo de arquivo (JPEG, PNG, GIF)
        - Limite de tamanho de arquivo (5MB)
        - Geração de preview otimizado

        Args:
            cover_file: Arquivo de imagem enviado

        Returns:
            tuple: (arquivo_processado, preview) ou (None, None) em caso de erro
        """
        try:
            if not cover_file:
                logger.warning("Arquivo de capa vazio")
                return None, None

            # Validações de tipo e tamanho
            valid_image_types = ['image/jpeg', 'image/png', 'image/gif']
            if cover_file.content_type not in valid_image_types:
                logger.warning(f"Tipo de arquivo inválido: {cover_file.content_type}")
                return None, None

            if cover_file.size > 5 * 1024 * 1024:  # 5MB
                logger.warning(f"Arquivo muito grande: {cover_file.size} bytes")
                return None, None

            # Processar imagem
            img = Image.open(cover_file)
            preview_size = (500, 750)
            img.thumbnail(preview_size, resample=Image.LANCZOS)

            # Gerar preview
            preview_buffer = BytesIO()
            img.save(preview_buffer, format=img.format or 'JPEG')
            preview_file = ContentFile(preview_buffer.getvalue())

            cover_file.seek(0)
            return cover_file, preview_file

        except Exception as e:
            logger.error(f"Erro ao processar capa: {str(e)}")
            return None, None

    @staticmethod
    def save_cover_image(image_data, filename):
        """
        Salva imagem da capa e seu preview no armazenamento.

        Funcionalidades:
        - Converte imagem para RGB
        - Redimensiona mantendo proporções
        - Salva imagem original e preview

        Args:
            image_data: Dados binários da imagem
            filename: Nome do arquivo

        Returns:
            tuple: (caminho_capa, caminho_preview) ou (None, None) em caso de erro
        """
        try:
            img = Image.open(BytesIO(image_data))

            # Converte para RGB se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Processar imagem original em alta qualidade
            max_size = (1200, 1800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Salvar original
            output_buffer = BytesIO()
            img.save(output_buffer, format='JPEG', quality=95, optimize=True)

            path = f'livros/capas/{filename}'
            content_file = ContentFile(output_buffer.getvalue())
            path = default_storage.save(path, content_file)

            # Gerar e salvar preview otimizado
            preview_size = (500, 750)
            preview = img.copy()
            preview.thumbnail(preview_size, Image.Resampling.LANCZOS)

            preview_buffer = BytesIO()
            preview.save(preview_buffer, format='JPEG', quality=85, optimize=True)

            preview_filename = f'preview_{filename}'
            preview_path = f'livros/capas/previews/{preview_filename}'
            preview_content = ContentFile(preview_buffer.getvalue())
            preview_path = default_storage.save(preview_path, preview_content)

            return path, preview_path

        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {str(e)}")
            return None, None


class BookSearchView(TemplateView):
    """
    View para página de busca de livros.

    Renderiza o template de busca de livros.
    """
    template_name = 'core/book/search.html'


@login_required
@require_http_methods(["GET"])
def search_books(request):
    """
    Endpoint para busca de livros usando Google Books API.

    Características:
    - Suporta busca por diferentes tipos
    - Paginação de resultados
    - Retorna resultados em formato JSON

    Returns:
        JsonResponse com resultados da busca
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    page = int(request.GET.get('page', 1))
    items_per_page = 8
    client = GoogleBooksClient()

    try:
        return JsonResponse(client.search_books(
            query=query,
            search_type=search_type,
            page=page,
            items_per_page=items_per_page
        ))
    except Exception as e:
        logger.error(f"Erro na busca de livros: {str(e)}")
        return JsonResponse({
            'error': 'Erro ao buscar livros',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_to_shelf(request):
    """
    Adiciona um livro à prateleira do usuário.

    Fluxo de processamento:
    1. Valida dados do livro
    2. Processa informações do livro
    3. Salva imagem de capa (se disponível)
    4. Cria/atualiza registro do livro
    5. Adiciona à prateleira do usuário

    Returns:
        JsonResponse indicando sucesso ou falha
    """
    global pub_date_str
    try:
        data = json.loads(request.body)
        book_data = data.get('book_data', {})
        shelf = data.get('shelf')

        if not book_data or not shelf:
            return JsonResponse({'success': False, 'error': 'Dados incompletos'}, status=400)

        # Log detalhado dos dados recebidos
        logger.info(f"Dados recebidos - Shelf: {shelf}")
        logger.info(f"Dados do livro: {json.dumps(book_data, indent=2)}")

        mixin = BookManagementMixin()

        # Preparação de defaults para o livro
        book_defaults = {
            'titulo': book_data.get('titulo', 'Título não disponível'),
            'subtitulo': book_data.get('subtitulo', ''),
            'autor': book_data.get('autores', ['Autor desconhecido'])[0],
            'editora': book_data.get('editora', ''),
            'isbn': book_data.get('isbn', ''),
            'data_publicacao': None,
            'descricao': book_data.get('descricao', 'Descrição não disponível'),
            'categoria': book_data.get('categorias', []),
            'preco': Decimal('0'),
            'preco_promocional': Decimal('0')
        }

        # Processamento de data de publicação
        try:
            pub_date_str = book_data.get('data_publicacao', '')
            if pub_date_str:
                book_defaults['data_publicacao'] = datetime.strptime(pub_date_str.split('-')[0], '%Y').date()
        except (ValueError, TypeError) as date_error:
            logger.warning(f"Data de publicação inválida: {pub_date_str}. Erro: {str(date_error)}")

        # Processamento de preço com tratamento de erro
        try:
            book_defaults['preco'] = Decimal(str(book_data.get('valor', 0)))
            book_defaults['preco_promocional'] = Decimal(str(book_data.get('valor_promocional', 0)))
        except (TypeError, ValueError, decimal.InvalidOperation) as e:
            logger.error(f"Erro ao converter valores de preço para decimal: {e}")
            return JsonResponse({'success': False, 'error': 'Erro ao processar o preço do livro'}, status=400)

        # Processamento de capa
        capa = None
        thumbnail_url = book_data.get('capa_url')
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    filename = f"book_{timezone.now().timestamp()}.jpg"
                    saved_paths = mixin.save_cover_image(response.content, filename)
                    if saved_paths and isinstance(saved_paths, tuple):
                        capa = saved_paths[0]
            except Exception as e:
                logger.error(f"Erro ao baixar imagem: {str(e)}")

        if capa:
            book_defaults['capa'] = capa

        # Criar ou atualizar livro
        book, created = Book.objects.get_or_create(
            titulo=book_defaults['titulo'],
            defaults=book_defaults
        )

        if not created and capa:
            book.capa = capa
            book.save()

        # Validação e mapeamento do tipo de prateleira
        valid_shelf_types = dict(UserBookShelf.SHELF_CHOICES).keys()
        shelf_mapping = {
            'favoritos': 'favorito',
            'lidos': 'lido',
            'lendo': 'lendo',
            'vou_ler': 'vou_ler'
        }
        shelf = shelf_mapping.get(shelf, shelf)

        if str(shelf) not in valid_shelf_types:
            return JsonResponse({
                'success': False,
                'error': f'Tipo de prateleira inválido: {shelf}'
            }, status=400)

        # Atualizar prateleira
        shelf_obj, created = UserBookShelf.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={'shelf_type': str(shelf), 'added_at': timezone.now()}
        )

        return JsonResponse({
            'success': True,
            'message': f'Livro adicionado com sucesso à sua prateleira de {shelf_obj.get_shelf_type_display()}!'
        })

    except Exception as e:
        logger.error(f"Erro ao adicionar livro: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar livro',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_from_shelf(request, book_id):
    """
    Remove um livro específico da prateleira do usuário.

    Características:
    - Valida existência do livro
    - Verifica tipo de prateleira
    - Remove item da prateleira

    Args:
        request: Requisição HTTP
        book_id: ID do livro a ser removido

    Returns:
        JsonResponse indicando sucesso ou falha
    """
    try:
        # Primeiro, verifique se o livro existe
        book = Book.objects.get(id=book_id)

        # Carregue os dados do corpo da requisição
        data = json.loads(request.body)
        shelf_type = data.get('shelf_type')

        if not shelf_type:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de prateleira não especificado'
            }, status=400)

        # Validar tipo de prateleira
        valid_shelves = dict(UserBookShelf.SHELF_CHOICES).keys()
        if shelf_type not in valid_shelves:
            return JsonResponse({
                'success': False,
                'error': f'Prateleira inválida: {shelf_type}'
            }, status=400)

        # Busque o item da prateleira do usuário
        shelf_item = UserBookShelf.objects.filter(
            user=request.user,
            book=book,
            shelf_type=shelf_type
        ).first()

        if not shelf_item:
            return JsonResponse({
                'success': False,
                'error': f'Livro não encontrado na prateleira {shelf_type}'
            }, status=404)

        # Log antes da remoção
        logger.info(f"Usuário {request.user.username} removendo livro '{book.titulo}' da prateleira {shelf_type}")

        # Remove o item da prateleira
        shelf_item.delete()

        return JsonResponse({
            'success': True,
            'message': f'Livro removido da prateleira {shelf_type} com sucesso!'
        })

    except Book.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro ao remover livro da prateleira: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# Continuação do arquivo book.py

@login_required
@require_http_methods(["GET"])
def get_book_details(request, book_id):
    """
    Obtém detalhes de um livro específico.

    Características:
    - Busca livro por ID
    - Retorna informações básicas do livro
    - Tratamento de livro não encontrado

    Args:
        request: Requisição HTTP
        book_id: ID do livro a ser detalhado

    Returns:
        JsonResponse com detalhes do livro ou erro
    """
    try:
        book = Book.objects.get(id=book_id)
        return JsonResponse({
            'success': True,
            'titulo': book.titulo,
            'autor': book.autor,
            'descricao': book.descricao,
            'editora': book.editora,
            'categoria': book.categoria,
            'data_publicacao': book.data_publicacao.strftime('%Y-%m-%d') if book.data_publicacao else None,
        })
    except Book.DoesNotExist:
        logger.warning(f"Tentativa de acesso a livro inexistente ID: {book_id}")
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado'
        }, status=404)


@login_required
@require_http_methods(["POST"])
def update_book(request, book_id):
    """
    Atualiza informações de um livro existente.

    Características:
    - Atualização de múltiplos campos
    - Processamento de capa de livro
    - Remoção de capa antiga
    - Log de atualizações

    Args:
        request: Requisição HTTP com dados de atualização
        book_id: ID do livro a ser atualizado

    Returns:
        JsonResponse indicando sucesso ou falha na atualização
    """
    try:
        logger.info(f'Recebendo atualização para livro {book_id}')
        book = Book.objects.get(id=book_id)
        mixin = BookManagementMixin()

        # Lista de campos para atualização
        fields = [
            'titulo', 'subtitulo', 'autor', 'descricao', 'editora', 'categoria',
            'tradutor', 'ilustrador', 'isbn', 'edicao', 'numero_paginas',
            'idioma', 'formato', 'dimensoes', 'peso', 'genero', 'temas',
            'personagens', 'enredo', 'publico_alvo', 'premios', 'adaptacoes',
            'colecao', 'classificacao', 'citacoes', 'curiosidades', 'website'
        ]

        # Atualizar campos
        for field in fields:
            value = request.POST.get(field)
            if value is not None:
                setattr(book, field, value)

        # Processar data de publicação
        data_pub = request.POST.get('data_publicacao')
        if data_pub:
            try:
                book.data_publicacao = datetime.strptime(data_pub, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Data inválida recebida: {data_pub}")

        # Processar preço
        preco_str = request.POST.get('preco')
        if preco_str:
            try:
                book.preco = Decimal(preco_str)
            except (decimal.InvalidOperation, ValueError):
                logger.error("Erro ao converter valor do preço")

        # Processar capa
        if 'capa' in request.FILES:
            new_cover, preview = mixin.process_book_cover(request.FILES['capa'])
            if new_cover and preview:
                # Remover capa antiga
                if book.capa and 'default.jpg' not in book.capa.name:
                    try:
                        default_storage.delete(book.capa.name)
                        preview_name = f'previews/preview_{book.capa.name.split("/")[-1]}'
                        default_storage.delete(f'livros/capas/{preview_name}')
                    except Exception as e:
                        logger.error(f"Erro ao deletar capa antiga: {str(e)}")

                # Salvar nova capa
                timestamp = timezone.now().timestamp()
                filename = f"book_{timestamp}.jpg"
                capa_path, preview_path = mixin.save_cover_image(new_cover.read(), filename)
                if capa_path and preview_path:
                    book.capa = capa_path
                    book.capa_preview = preview_path

        book.save()
        logger.info(f"Livro {book.titulo} (ID: {book_id}) atualizado")

        return JsonResponse({
            'success': True,
            'message': 'Livro atualizado com sucesso!'
        })

    except Book.DoesNotExist:
        logger.error(f'Livro não encontrado: {book_id}')
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f'Erro ao atualizar livro: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def move_book(request, book_id):
    """
    Move um livro para outra prateleira.

    Características:
    - Valida existência do livro
    - Verifica tipo de prateleira
    - Registra movimento entre prateleiras

    Args:
        request: Requisição HTTP
        book_id: ID do livro a ser movido

    Returns:
        JsonResponse indicando sucesso ou falha no movimento
    """
    try:
        # Primeiro, verifique se o livro existe
        book = Book.objects.get(id=book_id)

        # Carregue os dados do corpo da requisição
        data = json.loads(request.body)
        new_shelf = data.get('new_shelf')

        if not new_shelf:
            return JsonResponse({
                'success': False,
                'error': 'Nova prateleira não especificada'
            }, status=400)

        # Validar tipo de prateleira
        valid_shelves = dict(UserBookShelf.SHELF_CHOICES).keys()
        if new_shelf not in valid_shelves:
            return JsonResponse({
                'success': False,
                'error': f'Prateleira inválida: {new_shelf}'
            }, status=400)

        # Busque o item da prateleira atual do usuário
        shelf_item = UserBookShelf.objects.filter(
            user=request.user,
            book=book
        ).first()

        if not shelf_item:
            return JsonResponse({
                'success': False,
                'error': 'Livro não encontrado em nenhuma prateleira'
            }, status=404)

        # Registre o movimento antigo para logs
        old_shelf = shelf_item.shelf_type

        # Atualize o tipo de prateleira
        shelf_item.shelf_type = new_shelf
        shelf_item.save()

        # Log do movimento
        logger.info(
            f"Usuário {request.user.username} moveu o livro '{book.titulo}' da prateleira {old_shelf} para {new_shelf}")

        return JsonResponse({
            'success': True,
            'message': f'Livro movido para {new_shelf} com sucesso!'
        })

    except Book.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro ao mover livro: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def add_book_manual(request):
    """
    Adiciona um livro manualmente pelo usuário.

    Características:
    - Criação de livro com informações básicas
    - Processamento opcional de capa
    - Adição à prateleira do usuário

    Args:
        request: Requisição HTTP com dados do livro

    Returns:
        JsonResponse indicando sucesso ou falha na adição
    """
    try:
        mixin = BookManagementMixin()

        book = Book.objects.create(
            titulo=request.POST['titulo'],
            autor=request.POST['autor'],
            descricao=request.POST.get('descricao', ''),
            editora=request.POST.get('editora', ''),
            categoria=request.POST.get('categoria', '')
        )

        if 'capa' in request.FILES:
            cover, preview = mixin.process_book_cover(request.FILES['capa'])
            if cover and preview:
                # Salvar capa
                timestamp = timezone.now().timestamp()
                filename = f"book_{timestamp}.jpg"
                capa_path, preview_path = mixin.save_cover_image(cover.read(), filename)
                if capa_path and preview_path:
                    book.capa = capa_path
                    book.capa_preview = preview_path
                    book.save()

        UserBookShelf.objects.create(
            user=request.user,
            book=book,
            shelf_type=request.POST['shelf_type']
        )

        logger.info(f"Livro {book.titulo} adicionado manualmente")

        return JsonResponse({
            'success': True,
            'message': 'Livro adicionado com sucesso!'
        })
    except Exception as e:
        logger.error(f"Erro ao adicionar livro: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


class BookDetailView(LoginRequiredMixin, DetailView):
    """
    View para detalhes do livro.

    Características:
    - Requer login para acesso
    - Fornece contexto detalhado do livro
    - Inclui informações da prateleira do usuário
    """
    model = Book
    template_name = 'core/book/book_details.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        """
        Adiciona informações da prateleira ao contexto.

        Returns:
            dict: Contexto estendido com informações da prateleira
        """
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        user = self.request.user

        user_shelf = UserBookShelf.objects.filter(user=user, book=book).first()

        context.update({
            'shelf': user_shelf.shelf_type if user_shelf else None,
            'shelf_display': user_shelf.get_shelf_type_display() if user_shelf else None,
        })

        return context