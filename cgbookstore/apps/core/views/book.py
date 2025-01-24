import json
import logging
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse
from django.core.cache import cache
from django.core.files.storage import default_storage
import requests
from django.conf import settings

from cgbookstore.apps.core.models import UserBookShelf, Book

# Configuração do logger
logger = logging.getLogger(__name__)

__all__ = [
    'BookSearchView',
    'search_books',
    'add_to_shelf',
    'remove_from_shelf',
    'get_book_details',
    'update_book',
    'move_book',
    'add_book_manual',
]


class BookManagementMixin:
    """Mixin com métodos comuns para gerenciamento de livros"""

    @staticmethod
    def process_book_cover(cover_file):
        """Processa e valida arquivo de capa do livro"""
        try:
            if not cover_file:
                return None

            # Validar tipo do arquivo
            valid_image_types = ['image/jpeg', 'image/png', 'image/gif']
            if cover_file.content_type not in valid_image_types:
                logger.warning(f"Tipo de arquivo inválido: {cover_file.content_type}")
                return None

            # Validar tamanho do arquivo (max 5MB)
            if cover_file.size > 5 * 1024 * 1024:
                logger.warning(f"Arquivo muito grande: {cover_file.size} bytes")
                return None

            return cover_file
        except Exception as e:
            logger.error(f"Erro ao processar capa: {str(e)}")
            return None

    @staticmethod
    def save_cover_image(image_data, filename):
        """Salva imagem da capa no storage"""
        try:
            from django.core.files.base import ContentFile
            path = f'livros/capas/{filename}'
            content_file = ContentFile(image_data)
            path = default_storage.save(path, content_file)
            return path
        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {str(e)}")
            return None


class BookSearchView(TemplateView):
    template_name = 'core/book/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def search_books(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    page = int(request.GET.get('page', 1))
    items_per_page = 8

    # Verificar cache primeiro
    cache_key = f'books_search_{query}_{search_type}_{page}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)

    base_url = 'https://www.googleapis.com/books/v1/volumes'

    # Construir query baseado no tipo de busca
    if search_type == 'title':
        query = f'intitle:{query}'
    elif search_type == 'author':
        query = f'inauthor:{query}'
    elif search_type == 'category':
        query = f'subject:{query}'

    params = {
        'q': query,
        'key': settings.GOOGLE_BOOKS_API_KEY,
        'startIndex': (page - 1) * items_per_page,
        'maxResults': items_per_page,
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        books = []
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            books.append({
                'id': item.get('id'),
                'title': volume_info.get('title', 'Título não disponível'),
                'authors': volume_info.get('authors', ['Autor desconhecido']),
                'description': volume_info.get('description', 'Descrição não disponível'),
                'published_date': volume_info.get('publishedDate', 'Data não disponível'),
                'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                'publisher': volume_info.get('publisher', ''),
                'categories': volume_info.get('categories', [])
            })

        total_items = data.get('totalItems', 0)
        total_pages = (total_items + items_per_page - 1) // items_per_page

        result = {
            'books': books,
            'total_pages': total_pages,
            'current_page': page,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }

        # Cachear resultado por 1 hora
        cache.set(cache_key, result, 3600)

        return JsonResponse(result)

    except requests.RequestException as e:
        logger.error(f"Erro na busca de livros: {str(e)}")
        return JsonResponse({
            'error': 'Erro ao buscar livros',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_to_shelf(request):
    try:
        data = json.loads(request.body)
        book_data = data.get('book_data', {})
        shelf = data.get('shelf')

        if not book_data or not shelf:
            return JsonResponse({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)

        # Log detalhado para debug
        logger.info(f"Dados recebidos - Shelf: {shelf}")
        logger.info(f"Dados do livro: {json.dumps(book_data, indent=2)}")

        mixin = BookManagementMixin()
        volume_info = book_data.get('volumeInfo', {})
        sale_info = book_data.get('saleInfo', {})

        # Processamento seguro de preço
        price_info = {}
        try:
            list_price = sale_info.get('listPrice', {}) or {}
            price_info = {
                'moeda': list_price.get('currencyCode', 'BRL'),
                'valor': str(list_price.get('amount', '')),
                'valor_promocional': ''  # Você pode ajustar isso conforme necessário
            }
        except Exception as price_error:
            logger.warning(f"Erro ao processar preço: {str(price_error)}")

        # Processamento seguro da data de publicação
        published_date = None
        try:
            pub_date_str = volume_info.get('publishedDate', '')
            if pub_date_str:
                published_date = datetime.strptime(pub_date_str.split('-')[0], '%Y').date()
        except (ValueError, TypeError) as date_error:
            logger.warning(f"Data de publicação inválida: {pub_date_str}. Erro: {str(date_error)}")

        # Processamento de ISBN
        isbn = ''
        identifiers = volume_info.get('industryIdentifiers', [])
        for identifier in identifiers:
            if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                isbn = identifier.get('identifier', '')
                break

        # Processamento da miniatura
        thumbnail_url = volume_info.get('imageLinks', {}).get('thumbnail', '')
        capa = None
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    filename = f"book_{timezone.now().timestamp()}.jpg"
                    saved_path = mixin.save_cover_image(response.content, filename)
                    if saved_path:
                        capa = saved_path
            except Exception as e:
                logger.error(f"Erro ao baixar imagem: {str(e)}")

        # Preparação dos dados do livro
        book_defaults = {
            'titulo': volume_info.get('title', 'Título não disponível'),
            'subtitulo': volume_info.get('subtitle', ''),
            'autor': ', '.join(volume_info.get('authors', ['Autor desconhecido'])),
            'editora': volume_info.get('publisher', ''),
            'isbn': isbn,
            'data_publicacao': published_date,
            'descricao': volume_info.get('description', 'Descrição não disponível'),
            'categoria': ', '.join(volume_info.get('categories', [])),
            'preco': price_info,
        }

        # Adicionar capa se disponível
        if capa:
            book_defaults['capa'] = capa

        # Mapeamento das prateleiras
        shelf_mapping = {
            'favoritos': 'favorito',
            'lendo': 'lendo',
            'vou_ler': 'vou_ler',
            'lidos': 'lido'
        }

        shelf_type = shelf_mapping.get(shelf)
        if not shelf_type:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de prateleira inválido'
            }, status=400)

        # Criar ou atualizar o livro
        book, created = Book.objects.get_or_create(
            titulo=book_defaults['titulo'],
            defaults=book_defaults
        )

        # Se o livro já existe e tem uma nova capa, atualiza
        if not created and capa:
            book.capa = capa
            book.save()

        # Criar ou atualizar prateleira do usuário
        shelf_obj, _ = UserBookShelf.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={
                'shelf_type': shelf_type,
                'added_at': timezone.now()
            }
        )

        logger.info(f"Livro {book.titulo} adicionado/atualizado na prateleira {shelf_type} do usuário {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': f'Livro adicionado com sucesso à sua prateleira de {shelf_obj.get_shelf_type_display()}!'
        })

    except Exception as e:
        logger.error(f"Erro ao adicionar livro à prateleira: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro interno ao processar o livro',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_from_shelf(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        shelf_type = data.get('shelf_type')

        if not book_id or not shelf_type:
            return JsonResponse({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)

        shelf_item = UserBookShelf.objects.filter(
            user=request.user,
            book_id=book_id,
            shelf_type=shelf_type
        ).first()

        if shelf_item:
            logger.info(f"Removendo livro {shelf_item.book.titulo} da prateleira {shelf_type} do usuário {request.user.username}")
            shelf_item.delete()
            return JsonResponse({
                'success': True,
                'message': 'Livro removido com sucesso!'
            })

        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado na prateleira'
        }, status=404)

    except Exception as e:
        logger.error(f"Erro ao remover livro da prateleira: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def get_book_details(request, book_id):
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
    try:
        book = Book.objects.get(id=book_id)
        mixin = BookManagementMixin()

        # Atualizar informações básicas
        book.titulo = request.POST.get('titulo', book.titulo)
        book.autor = request.POST.get('autor', book.autor)
        book.descricao = request.POST.get('descricao', book.descricao)
        book.editora = request.POST.get('editora', book.editora)
        book.categoria = request.POST.get('categoria', book.categoria)

        if 'capa' in request.FILES:
            new_cover = mixin.process_book_cover(request.FILES['capa'])
            if new_cover:
                # Remover capa antiga se não for a default
                if book.capa and 'default.jpg' not in book.capa.name:
                    try:
                        default_storage.delete(book.capa.name)
                    except Exception as e:
                        logger.error(f"Erro ao deletar capa antiga: {str(e)}")

                book.capa = new_cover

        book.save()
        logger.info(f"Livro {book.titulo} (ID: {book_id}) atualizado pelo usuário {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': 'Livro atualizado com sucesso!'
        })
    except Exception as e:
        logger.error(f"Erro ao atualizar livro {book_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def move_book(request):
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        new_shelf = data.get('new_shelf')

        if not book_id or not new_shelf:
            return JsonResponse({
                'success': False,
                'error': 'Dados incompletos'
            }, status=400)

        shelf = UserBookShelf.objects.get(
            user=request.user,
            book_id=book_id
        )

        old_shelf = shelf.shelf_type
        shelf.shelf_type = new_shelf
        shelf.save()

        logger.info(f"Livro {shelf.book.titulo} movido da prateleira {old_shelf} para {new_shelf} pelo usuário {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': 'Livro movido com sucesso!'
        })
    except UserBookShelf.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado na prateleira'
        }, status=404)
    except Exception as e:
        logger.error(f"Erro ao mover livro: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def add_book_manual(request):
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
            cover = mixin.process_book_cover(request.FILES['capa'])
            if cover:
                book.capa = cover
                book.save()

        UserBookShelf.objects.create(
            user=request.user,
            book=book,
            shelf_type=request.POST['shelf_type']
        )

        logger.info(f"Livro {book.titulo} adicionado manualmente pelo usuário {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': 'Livro adicionado com sucesso!'
        })
    except Exception as e:
        logger.error(f"Erro ao adicionar livro manualmente: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'core/book/book_details.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        user = self.request.user

        # Obter prateleira atual do livro para este usuário
        user_shelf = UserBookShelf.objects.filter(user=user, book=book).first()

        context.update({
            'shelf': user_shelf.shelf_type if user_shelf else None,
            'shelf_display': user_shelf.get_shelf_type_display() if user_shelf else None,
        })

        return context