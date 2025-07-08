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
import requests
from decimal import Decimal
from django.conf import settings

from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.db import models
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse, Http404
from django.core.files.storage import default_storage
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from cgbookstore.apps.core.models import UserBookShelf, Book
from ..services.google_books_service import GoogleBooksClient

# Configuração do logger para rastreamento de eventos de livros
logger = logging.getLogger(__name__)

# Instância global do cliente Google Books com contexto de busca
google_books_client = GoogleBooksClient(
    cache_namespace="books_search",
    context="search"
)

__all__ = [
    'BookSearchView',
    'BookDetailView',
    'search_books',
    'add_to_shelf',
    'remove_from_shelf',
    'get_book_details',
    'update_book',
    'move_book',
    'add_book_manual',
    'CatalogueView',
    'NewReleasesView',
    'BestSellersView',
    'RecommendedBooksView',
    'CheckoutPremiumView',
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
    Aceita tanto dados em JSON quanto form-urlencoded.

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
        # Verifica o tipo de conteúdo para determinar como processar os dados
        if request.content_type == 'application/x-www-form-urlencoded':
            # Processamento para dados form-urlencoded
            book_id = request.POST.get('book_id')
            shelf = request.POST.get('shelf')

            if not book_id or not shelf:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Dados incompletos (book_id ou shelf ausentes)'
                }, status=400)

            try:
                # Obter o livro pelo ID
                book = Book.objects.get(id=book_id)

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
                        'status': 'error',
                        'message': f'Tipo de prateleira inválido: {shelf}'
                    }, status=400)

                # Adicionar ou atualizar na prateleira
                shelf_obj, created = UserBookShelf.objects.update_or_create(
                    user=request.user,
                    book=book,
                    defaults={'shelf_type': str(shelf), 'added_at': timezone.now()}
                )

                return JsonResponse({
                    'status': 'success',
                    'message': f'Livro adicionado com sucesso à sua prateleira de {shelf_obj.get_shelf_type_display()}!'
                })

            except Book.DoesNotExist:
                logger.error(f"Livro ID {book_id} não encontrado")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Livro não encontrado'
                }, status=404)

        else:
            # Processamento para JSON
            try:
                data = json.loads(request.body)

                # Para compatibilidade com o addToShelf no book-details.js
                book_id = data.get('book_id')
                shelf_type = data.get('shelf_type')

                if book_id and shelf_type:
                    # Processamento simples para formato do frontend atual
                    try:
                        # Obter o livro pelo ID
                        book = Book.objects.get(id=book_id)

                        # Validação do tipo de prateleira
                        valid_shelf_types = dict(UserBookShelf.SHELF_CHOICES).keys()
                        if str(shelf_type) not in valid_shelf_types:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Tipo de prateleira inválido: {shelf_type}'
                            }, status=400)

                        # Adicionar ou atualizar na prateleira
                        shelf_obj, created = UserBookShelf.objects.update_or_create(
                            user=request.user,
                            book=book,
                            defaults={'shelf_type': str(shelf_type), 'added_at': timezone.now()}
                        )

                        return JsonResponse({
                            'success': True,
                            'message': f'Livro adicionado com sucesso à prateleira {shelf_obj.get_shelf_type_display()}!'
                        })

                    except Book.DoesNotExist:
                        logger.error(f"Livro ID {book_id} não encontrado")
                        return JsonResponse({
                            'success': False,
                            'error': 'Livro não encontrado'
                        }, status=404)

                # Processamento para o formato completo com book_data
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

            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON: {str(e)}", exc_info=True)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato de dados inválido. Esperado JSON válido.'
                }, status=400)

    except Exception as e:
        logger.error(f"Erro ao adicionar livro: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao processar livro',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_from_shelf(request, book_id):
    """
    Remove um livro específico da prateleira do usuário com verificações de segurança aprimoradas.

    Características:
    - Valida existência do livro
    - Verifica tipo de prateleira
    - Verifica propriedade da prateleira
    - Remove item da prateleira

    Args:
        request: Requisição HTTP
        book_id: ID do livro a ser removido

    Returns:
        JsonResponse indicando sucesso ou falha
    """
    try:
        # Verificação do usuário
        if not request.user.is_authenticated:
            logger.warning(f"Tentativa de acesso não autenticado para remover livro {book_id}")
            return JsonResponse({
                'success': False,
                'error': 'Usuário não autenticado'
            }, status=401)

        # Verifica se o livro existe
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            logger.warning(f"Tentativa de remover livro inexistente ID: {book_id} por usuário {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Livro não encontrado'
            }, status=404)

        # Carrega os dados do corpo da requisição com validação
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error(f"Formato JSON inválido na requisição de remoção de livro {book_id}")
            return JsonResponse({
                'success': False,
                'error': 'Formato de dados inválido'
            }, status=400)

        # Validação do shelf_type
        shelf_type = data.get('shelf_type')
        if not shelf_type:
            logger.warning(f"Tipo de prateleira não especificado na requisição para livro {book_id}")
            return JsonResponse({
                'success': False,
                'error': 'Tipo de prateleira não especificado'
            }, status=400)

        # Validar tipo de prateleira
        valid_shelves = dict(UserBookShelf.SHELF_CHOICES).keys()
        if shelf_type not in valid_shelves:
            logger.warning(f"Tipo de prateleira inválido: {shelf_type} para livro {book_id}")
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
            logger.warning(
                f"Livro {book_id} não encontrado na prateleira {shelf_type} do usuário {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': f'Livro não encontrado na prateleira {shelf_type}'
            }, status=404)

        # Verificação adicional de propriedade (garantir que pertence ao usuário solicitante)
        if shelf_item.user.id != request.user.id:
            logger.error(
                f"Usuário {request.user.username} tentando remover livro {book_id} que pertence a outro usuário")
            return JsonResponse({
                'success': False,
                'error': 'Você não tem permissão para remover este livro'
            }, status=403)

        # Log antes da remoção
        logger.info(
            f"Usuário {request.user.username} removendo livro '{book.titulo}' (ID: {book_id}) da prateleira {shelf_type}")

        # Remove o item da prateleira
        shelf_item.delete()

        # Log após remoção bem-sucedida
        logger.info(
            f"Livro '{book.titulo}' (ID: {book_id}) removido com sucesso da prateleira {shelf_type} do usuário {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': f'Livro removido da prateleira {shelf_type} com sucesso!'
        })

    except Exception as e:
        logger.error(f"Erro não tratado ao remover livro {book_id} da prateleira: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor ao processar sua solicitação'
        }, status=500)


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
@login_required
@require_http_methods(["POST"])
def move_book(request, book_id=None):
    """
    Move um livro para outra prateleira com verificações de segurança aprimoradas.

    Características:
    - Suporta chamadas com book_id na URL ou no corpo da requisição
    - Valida existência do livro
    - Verifica tipo de prateleira
    - Verifica propriedade da prateleira
    - Registra movimento entre prateleiras

    Args:
        request: Requisição HTTP
        book_id: ID do livro a ser movido (opcional, pode vir no corpo da requisição)

    Returns:
        JsonResponse indicando sucesso ou falha no movimento
    """
    try:
        # Verificação do usuário
        if not request.user.is_authenticated:
            logger.warning(f"Tentativa de acesso não autenticado para mover livro")
            return JsonResponse({
                'success': False,
                'error': 'Usuário não autenticado'
            }, status=401)

        # Carrega os dados do corpo da requisição com validação
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error(f"Formato JSON inválido na requisição de movimento de livro")
            return JsonResponse({
                'success': False,
                'error': 'Formato de dados inválido'
            }, status=400)

        # Obter book_id do corpo da requisição se não estiver na URL
        if book_id is None:
            book_id = data.get('book_id')
            if not book_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID do livro não fornecido'
                }, status=400)

        # Verifica se o livro existe
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            logger.warning(f"Tentativa de mover livro inexistente ID: {book_id} por usuário {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Livro não encontrado'
            }, status=404)

        # Verificar qual é o campo para a nova prateleira no JSON
        # Suporta tanto 'new_shelf' quanto 'new_shelf_type' para compatibilidade
        new_shelf = data.get('new_shelf') or data.get('new_shelf_type')
        if not new_shelf:
            # Também verifica 'shelf_type' para compatibilidade com a UI
            new_shelf = data.get('shelf_type')

        if not new_shelf:
            logger.warning(f"Nova prateleira não especificada para livro {book_id}")
            return JsonResponse({
                'success': False,
                'error': 'Nova prateleira não especificada'
            }, status=400)

        # Validar tipo de prateleira
        valid_shelves = dict(UserBookShelf.SHELF_CHOICES).keys()
        if new_shelf not in valid_shelves:
            logger.warning(f"Tipo de prateleira inválido: {new_shelf} para livro {book_id}")
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
            logger.warning(
                f"Livro {book_id} não encontrado em nenhuma prateleira do usuário {request.user.username}")

            # Se o livro não estiver em nenhuma prateleira, cria uma nova entrada
            shelf_item = UserBookShelf.objects.create(
                user=request.user,
                book=book,
                shelf_type=new_shelf
            )

            logger.info(
                f"Usuário {request.user.username} adicionou o livro '{book.titulo}' (ID: {book_id}) " +
                f"à prateleira {new_shelf}"
            )

            return JsonResponse({
                'success': True,
                'message': f'Livro adicionado à prateleira {new_shelf} com sucesso!'
            })

        # Verificação adicional de propriedade
        if shelf_item.user.id != request.user.id:
            logger.error(
                f"Usuário {request.user.username} tentando mover livro {book_id} que pertence a outro usuário")
            return JsonResponse({
                'success': False,
                'error': 'Você não tem permissão para mover este livro'
            }, status=403)

        # Se o livro já está na prateleira de destino, retorne um aviso
        if shelf_item.shelf_type == new_shelf:
            logger.info(f"Livro {book_id} já está na prateleira {new_shelf}")
            return JsonResponse({
                'success': True,
                'message': f'O livro já está na prateleira {new_shelf}'
            })

        # Registre o movimento antigo para logs
        old_shelf = shelf_item.shelf_type

        # Atualize o tipo de prateleira
        shelf_item.shelf_type = new_shelf
        shelf_item.save()

        # Log do movimento
        logger.info(
            f"Usuário {request.user.username} moveu o livro '{book.titulo}' (ID: {book_id}) " +
            f"da prateleira {old_shelf} para {new_shelf}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Livro movido para {new_shelf} com sucesso!'
        })

    except Exception as e:
        logger.error(
            f"Erro não tratado ao mover livro {book_id if 'book_id' in locals() else 'desconhecido'}: {str(e)}",
            exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor ao processar sua solicitação'
        }, status=500)


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
        Adiciona informações da prateleira ao contexto com verificações de segurança aprimoradas.

        Returns:
            dict: Contexto estendido com informações da prateleira
        """
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        user = self.request.user

        # Verificar se o usuário está autenticado
        if not user.is_authenticated:
            logger.warning(f"Usuário não autenticado tentando acessar detalhes do livro {book.id}")
            context.update({
                'shelf': None,
                'shelf_display': 'Faça login para adicionar à sua prateleira',
                'is_external': False,
                'can_edit': False,
                'can_move': False,
                'can_remove': False,
            })
            return context

        # Busca informações da prateleira do usuário com tratamento de exceção
        try:
            # Otimização: Usar select_related para evitar N+1 query
            user_shelf = UserBookShelf.objects.filter(user=user, book=book).select_related('book').first()

            # Verificar se o livro é temporário e fazer ajustes necessários
            is_temporary = getattr(book, 'is_temporary', False)

            # Definir permissões com base no contexto
            can_edit = True  # Permite edição para todos os livros (pode ser ajustado conforme necessário)
            can_move = bool(user_shelf)  # Permite mover apenas se estiver em uma prateleira
            can_remove = bool(user_shelf)  # Permite remover apenas se estiver em uma prateleira

            # Ajustar permissões para livros temporários ou externos
            if is_temporary or book.external_id:
                # Pode limitar certas operações para livros externos ou temporários
                logger.info(f"Livro {book.id} é {'temporário' if is_temporary else 'externo'}")

            # Adiciona informações da prateleira ao contexto
            context.update({
                'shelf': user_shelf.shelf_type if user_shelf else None,
                'shelf_display': user_shelf.get_shelf_type_display() if user_shelf else 'Não está em sua prateleira',
                'is_external': bool(book.external_id),
                'can_edit': can_edit,
                'can_move': can_move,
                'can_remove': can_remove,
                'is_temporary': is_temporary,
            })

            # Registrar acesso para análise de uso
            logger.info(f"Usuário {user.username} (ID: {user.id}) acessou o livro {book.titulo} (ID: {book.id})")

        except Exception as e:
            # Em caso de erro, configurar para valores seguros
            logger.error(f"Erro ao obter informações da prateleira: {str(e)}", exc_info=True)
            context.update({
                'shelf': None,
                'shelf_display': 'Erro ao carregar informações da prateleira',
                'is_external': False,
                'can_edit': False,
                'can_move': False,
                'can_remove': False,
                'error': True,
            })

        return context


@login_required
@require_http_methods(["POST"])
def add_external_to_shelf(request):
    """
    Adiciona um livro externo diretamente à prateleira sem importá-lo
    completamente.

    Esta é uma alternativa para quando a importação completa falha.
    Cria um livro com dados mínimos a partir dos dados externos.

    Returns:
        JsonResponse: Resposta com status da operação
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Usuário não autenticado'}, status=401)

    try:
        # Carrega dados do corpo da requisição
        data = json.loads(request.body)
        external_id = data.get('external_id')
        shelf_type = data.get('shelf_type')

        if not external_id or not shelf_type:
            return JsonResponse({'status': 'error', 'message': 'Dados incompletos'}, status=400)

        # Verifica se o livro já existe pelo ID externo
        existing_book = Book.objects.filter(external_id=external_id).first()

        if existing_book:
            # Se existe, apenas adiciona à prateleira
            _, created = UserBookShelf.objects.get_or_create(
                user=request.user,
                book=existing_book,
                defaults={'shelf_type': shelf_type}
            )

            message = 'Livro adicionado à prateleira'
            if not created:
                message = 'Livro já estava na prateleira'

            return JsonResponse({
                'status': 'success',
                'message': message
            })

        # Se não existe, tenta criar a partir dos dados externos
        try:
            external_data = json.loads(data.get('external_data', '{}'))
            volume_info = external_data.get('volumeInfo', {})

            # Cria livro minimalista
            new_book = Book.objects.create(
                titulo=volume_info.get('title', 'Sem título'),
                autor=volume_info.get('authors', ['Autor desconhecido'])[0] if volume_info.get(
                    'authors') else 'Autor desconhecido',
                external_id=external_id,
                capa_url=volume_info.get('imageLinks', {}).get('thumbnail', '')
            )

            # Adiciona à prateleira
            UserBookShelf.objects.create(
                user=request.user,
                book=new_book,
                shelf_type=shelf_type
            )

            logger.info(f"Livro externo adicionado diretamente: {new_book.titulo} (ID: {new_book.id})")

            return JsonResponse({
                'status': 'success',
                'message': 'Livro adicionado à prateleira'
            })

        except Exception as e:
            logger.error(f"Erro ao processar dados externos: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Erro ao processar dados externos: {str(e)}'},
                                status=500)

    except Exception as e:
        logger.error(f"Erro ao adicionar livro externo à prateleira: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def external_book_details_view(request, external_id):
    """
    View para exibir detalhes de livros externos (Google Books API)

    Args:
        request: HttpRequest
        external_id: ID interno do livro no banco de dados

    Returns:
        HttpResponse com os detalhes do livro ou página de erro
    """
    try:
        # Log de debug para rastreamento
        print(f"[external_book_details_view] Processando livro ID interno: {external_id}")

        # Buscar o livro no banco de dados pelo ID interno
        try:
            book = Book.objects.get(id=external_id)
            print(f"[external_book_details_view] Livro encontrado: {book.titulo}")
        except Book.DoesNotExist:
            print(f"[external_book_details_view] Livro com ID {external_id} não encontrado no banco")
            raise Http404("Livro não encontrado")

        # Verificar se o livro tem external_id
        if not book.external_id:
            print(f"[external_book_details_view] Livro {book.titulo} não possui external_id")
            return render(request, 'core/error.html', {
                'error_message': "Este livro não possui informações externas disponíveis."
            })

        google_books_id = book.external_id
        print(f"[external_book_details_view] Usando Google Books ID: {google_books_id}")

        # Buscar informações detalhadas na API do Google Books
        try:
            google_books_service = GoogleBooksService()
            book_details = google_books_service.get_book_details(google_books_id)

            if not book_details:
                print(f"[external_book_details_view] Detalhes não encontrados para ID: {google_books_id}")
                raise Http404("Detalhes do livro não encontrados")

            print(f"[external_book_details_view] Detalhes obtidos com sucesso da API")

        except Exception as api_error:
            print(f"[external_book_details_view] Erro na API do Google Books: {str(api_error)}")
            return render(request, 'core/error.html', {
                'error_message': "Não foi possível obter informações atualizadas do livro. Tente novamente mais tarde."
            })

        # Verificar se o usuário já tem este livro em suas prateleiras
        user_book_shelf = None
        if request.user.is_authenticated:
            try:
                user_book_shelf = UserBookShelf.objects.get(
                    user=request.user,
                    book=book
                ).shelf_type
            except UserBookShelf.DoesNotExist:
                pass

        # Buscar livros relacionados/recomendados
        related_books = []
        if book_details.get('categories'):
            try:
                categories = book_details['categories']
                related_books = Book.objects.filter(
                    categoria__in=categories
                ).exclude(id=external_id)[:6]
            except Exception as related_error:
                print(f"[external_book_details_view] Erro ao buscar livros relacionados: {str(related_error)}")

        # Preparar contexto para o template
        context = {
            'book': book,
            'book_details': book_details,
            'user_book_shelf': user_book_shelf,
            'related_books': related_books,
            'google_books_id': google_books_id,
        }

        print(f"[external_book_details_view] Renderizando template com sucesso")
        return render(request, 'core/external_book_details.html', context)

    except Http404:
        # Re-raise Http404 para manter o comportamento esperado
        raise

    except Exception as e:
        # Log do erro completo
        import traceback
        print(f"[external_book_details_view] Erro inesperado: {str(e)}")
        print(f"[external_book_details_view] Traceback: {traceback.format_exc()}")

        # Retornar página de erro amigável
        return render(request, 'core/error.html', {
            'error_message': "Ocorreu um erro inesperado ao carregar os detalhes do livro. Por favor, tente novamente."
        })

class GoogleBooksService:
    """
    Serviço para interagir com a API do Google Books
    """

    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', None)
        self.base_url = 'https://www.googleapis.com/books/v1/volumes'

    def get_book_details(self, google_books_id):
        """
        Busca detalhes de um livro específico pelo Google Books ID

        Args:
            google_books_id: ID do livro no Google Books

        Returns:
            dict: Dados do livro ou None se não encontrado
        """
        try:
            import requests

            url = f"{self.base_url}/{google_books_id}"
            params = {}

            if self.api_key:
                params['key'] = self.api_key

            print(f"[GoogleBooksService] Fazendo requisição para: {url}")

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Verificar se os dados são válidos
            if 'volumeInfo' not in data:
                print(f"[GoogleBooksService] Resposta inválida da API: {data}")
                return None

            return data['volumeInfo']

        except requests.exceptions.RequestException as e:
            print(f"[GoogleBooksService] Erro na requisição: {str(e)}")
            raise
        except Exception as e:
            print(f"[GoogleBooksService] Erro inesperado: {str(e)}")
            raise


class CatalogueView(TemplateView):
    """
    View para página de catálogo completo de livros.

    Exibe todos os livros cadastrados no sistema.
    """
    template_name = 'core/book/catalogue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Configuração de paginação
        page = self.request.GET.get('page', 1)
        items_per_page = 12

        # Obter parâmetros de filtragem
        search_query = self.request.GET.get('search', '')
        sort_param = self.request.GET.get('sort', 'titulo')
        categoria_filter = self.request.GET.get('categoria', '')

        # Base query
        books = Book.objects.filter(is_temporary=False)

        # Aplicar filtros se fornecidos
        if search_query:
            books = books.filter(
                models.Q(titulo__icontains=search_query) |
                models.Q(autor__icontains=search_query) |
                models.Q(categoria__icontains=search_query)
            )

        if categoria_filter:
            # Tratamento especial para categorias armazenadas como listas
            # Busca tanto o nome exato quanto como parte de uma lista
            books = books.filter(
                models.Q(categoria=categoria_filter) |
                models.Q(categoria__icontains=f"'{categoria_filter}'")
            )

        # Aplicar ordenação
        valid_sort_fields = ['titulo', '-titulo', 'autor', '-autor', 'data_publicacao', '-data_publicacao']
        if sort_param in valid_sort_fields:
            books = books.order_by(sort_param)
        else:
            books = books.order_by('titulo')

        # Implementar paginação
        from django.core.paginator import Paginator
        paginator = Paginator(books, items_per_page)
        books_page = paginator.get_page(page)

        # Processamento especial para categorias
        # Obtém todas as categorias e processa para exibição limpa
        raw_categories = Book.objects.exclude(
            models.Q(categoria__isnull=True) |
            models.Q(categoria='')
        ).values_list('categoria', flat=True).distinct()

        # Processa as categorias para remover a formatação de lista
        processed_categories = set()
        for cat in raw_categories:
            # Se for uma lista em formato de string (ex: "['Fiction']")
            if cat.startswith('[') and cat.endswith(']'):
                try:
                    # Tenta extrair o conteúdo da lista
                    import ast
                    cat_list = ast.literal_eval(cat)
                    for item in cat_list:
                        if item:
                            processed_categories.add(item)
                except (ValueError, SyntaxError):
                    # Se falhar na conversão, usa o valor original
                    processed_categories.add(cat)
            else:
                # Categoria normal
                processed_categories.add(cat)

        # Converte para lista e ordena
        categories = sorted(list(processed_categories))

        context.update({
            'title': 'Catálogo Completo',
            'books': books_page,
            'page_obj': books_page,
            'categories': categories,
            'current_sort': sort_param,
            'current_search': search_query,
            'current_category': categoria_filter,
        })

        return context


class NewReleasesView(TemplateView):
    """
    View para página de novos lançamentos.

    Exibe os livros marcados como lançamentos.
    """
    template_name = 'core/book/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Otimização: Obter lançamentos com prefetch_related para relacionamentos M2M
        releases = Book.objects.filter(
            e_lancamento=True,
            is_temporary=False
        ).order_by('-data_publicacao', 'titulo')

        # Alternativa utilizando o campo tipo_shelf_especial
        if not releases.exists():
            releases = Book.objects.filter(
                tipo_shelf_especial='lancamentos',
                is_temporary=False
            ).order_by('-data_publicacao', 'titulo')

        context.update({
            'title': 'Novos Lançamentos',
            'books': releases,
            'description': 'Descubra os mais recentes lançamentos do mundo literário.'
        })

        return context


class BestSellersView(TemplateView):
    """
    View para página de livros mais vendidos.

    Exibe os livros com maior quantidade de vendas.
    """
    template_name = 'core/book/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Otimização: Obter os mais vendidos com select_related
        bestsellers = Book.objects.filter(
            tipo_shelf_especial='mais_vendidos',
            is_temporary=False
        ).order_by('-quantidade_vendida', 'titulo')

        # Caso não haja livros marcados especificamente como bestsellers
        if not bestsellers.exists():
            bestsellers = Book.objects.filter(
                is_temporary=False
            ).order_by('-quantidade_vendida', 'titulo')[:20]  # Limite para os 20 mais vendidos

        context.update({
            'title': 'Mais Vendidos',
            'books': bestsellers,
            'description': 'Os livros mais populares entre nossos leitores.'
        })

        return context


class RecommendedBooksView(LoginRequiredMixin, TemplateView):
    """
    View para página de livros recomendados.

    Exibe recomendações personalizadas para o usuário logado,
    utilizando o sistema de recomendações existente.
    """
    template_name = 'core/book/recommended.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Importa engine de recomendações
            from ..recommendations.engine import RecommendationEngine

            # Instancia o motor de recomendações
            engine = RecommendationEngine()

            # Obtém recomendações para o usuário atual
            # Otimização: Garantir que o engine de recomendações também use select_related/prefetch_related
            recommendations = engine.get_personalized_recommendations(
                user=self.request.user,
                limit=12  # Limite configurável pelo administrador
            )

            context.update({
                'title': 'Recomendados Para Você',
                'books': recommendations,
                'description': 'Seleções personalizadas com base no seu histórico de leitura e preferências.'
            })

        except Exception as e:
            logger.error(f"Erro ao obter recomendações: {str(e)}")
            context.update({
                'title': 'Recomendados Para Você',
                'books': [],
                'error': True,
                'error_message': 'Não foi possível carregar as recomendações. Por favor, tente novamente mais tarde.'
            })

        return context


class CheckoutPremiumView(TemplateView):
    """
    View temporária para o checkout do plano premium.

    Esta view será expandida quando você implementar
    a integração com sistemas de pagamento.

    Características:
    - Exibe página de placeholder para checkout
    - Mostra informações sobre o plano premium
    - Prepara usuário para futura integração de pagamentos
    """
    template_name = 'core/checkout_premium_placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Checkout Premium',
            'mensagem': 'Sistema de pagamento em implementação. Em breve você poderá finalizar sua assinatura Premium!',
            'user': self.request.user
        })
        logger.info(f"Usuário {self.request.user.username} acessou a página de checkout premium")
        return context