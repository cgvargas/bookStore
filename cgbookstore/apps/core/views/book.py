"""
Módulo responsável pelas views relacionadas a livros.
Inclui busca, gerenciamento de prateleiras e detalhes dos livros.
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

# Configuração do logger
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
    """Mixin com métodos comuns para gerenciamento de livros"""

    @staticmethod
    def process_book_cover(cover_file):
        """
        Processa, valida e gera preview do arquivo de capa do livro

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
        Salva imagem da capa e seu preview no storage

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
    """View para página de busca de livros"""
    template_name = 'core/book/search.html'


@login_required
@require_http_methods(["GET"])
def search_books(request):
    """
    Endpoint para busca de livros usando Google Books API
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
    Adiciona um livro à prateleira do usuário
    Processa dados do livro e imagem da capa
    """
    global pub_date_str
    try:
        data = json.loads(request.body)
        book_data = data.get('book_data', {})
        shelf = data.get('shelf')

        if not book_data or not shelf:
            return JsonResponse({'success': False, 'error': 'Dados incompletos'}, status=400)

        # Log detalhado
        logger.info(f"Dados recebidos - Shelf: {shelf}")
        logger.info(f"Dados do livro: {json.dumps(book_data, indent=2)}")

        mixin = BookManagementMixin()

        # Inicializa book_defaults fora do bloco try
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

        # Processamento de data
        try:
            pub_date_str = book_data.get('data_publicacao', '')
            if pub_date_str:
                book_defaults['data_publicacao'] = datetime.strptime(pub_date_str.split('-')[0], '%Y').date()
        except (ValueError, TypeError) as date_error:
            logger.warning(f"Data de publicação inválida: {pub_date_str}. Erro: {str(date_error)}")

        # Processamento de preço
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

        # Validar tipo de prateleira
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
def remove_from_shelf(request):
    """Remove um livro da prateleira do usuário"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        shelf_type = data.get('shelf_type')

        if not book_id or not shelf_type:
            return JsonResponse({'success': False, 'error': 'Dados incompletos'}, status=400)

        shelf_item = UserBookShelf.objects.filter(
            user=request.user,
            book_id=book_id,
            shelf_type=shelf_type
        ).first()

        if shelf_item:
            logger.info(f"Removendo livro {shelf_item.book.titulo} da prateleira {shelf_type}")
            shelf_item.delete()
            return JsonResponse({'success': True, 'message': 'Livro removido com sucesso!'})

        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado na prateleira'
        }, status=404)

    except Exception as e:
        logger.error(f"Erro ao remover livro: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_book_details(request, book_id):
    """Obtém detalhes de um livro específico"""
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


"""
Trecho corrigido da função update_book
"""
@login_required
@require_http_methods(["POST"])
def update_book(request, book_id):
    """Atualiza informações de um livro"""
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

        # Processar data
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
                book.preco = json.loads(preco_str)
            except json.JSONDecodeError:
                logger.error("Erro ao decodificar dados do preço")

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

    except Exception as e:
        logger.error(f'Erro ao atualizar livro: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def move_book(request):
    """Move um livro para outra prateleira"""
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

        logger.info(f"Livro movido de {old_shelf} para {new_shelf} - ID: {book_id}")

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
    """Adiciona um livro manualmente"""
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
    """View para detalhes do livro"""
    model = Book
    template_name = 'core/book/book_details.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        user = self.request.user

        user_shelf = UserBookShelf.objects.filter(user=user, book=book).first()

        context.update({
            'shelf': user_shelf.shelf_type if user_shelf else None,
            'shelf_display': user_shelf.get_shelf_type_display() if user_shelf else None,
        })

        return context