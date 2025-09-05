"""
Módulo responsável pelas views relacionadas a livros.
Inclui busca, gerenciamento de prateleiras e detalhes dos livros.

Principais funcionalidades:
- Pesquisa de livros (híbrida: local + externa)
- Gerenciamento de prateleiras de usuário
- Lógica de curadoria com livros públicos e privados
- Adição e remoção de livros
"""
import decimal
import json
import logging
import requests
from decimal import Decimal
from django.conf import settings

from types import SimpleNamespace
from django.templatetags.static import static
from django.urls import reverse
from django.utils.http import urlencode
from django.db.models import Q
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
from django.core.paginator import Paginator

from cgbookstore.apps.core.models import UserBookShelf, Book
from ..services.google_books_service import GoogleBooksClient

logger = logging.getLogger(__name__)

__all__ = [
    'BookSearchView', 'BookDetailView', 'search_books', 'add_to_shelf',
    'remove_from_shelf', 'get_book_details', 'update_book', 'move_book',
    'add_book_manual', 'CatalogueView', 'NewReleasesView', 'BestSellersView',
    'RecommendedBooksView', 'CheckoutPremiumView', 'add_external_book_to_shelf',
    'external_book_details_view'
]


# ==============================================================================
# NOVA ARQUITETURA DE CURADORIA E LÓGICA DE VIEWS
# ==============================================================================

@login_required
@require_http_methods(["GET"])
def search_books(request):
    """
    Endpoint HÍBRIDO e ROBUSTO para busca de livros.
    """
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))

    if not query:
        return JsonResponse({
            'books': [], 'total_pages': 1, 'current_page': 1,
            'has_previous': False, 'has_next': False
        })

    # --- Busca Local (apenas na página 1) ---
    processed_local_results = []
    if page == 1:
        local_books = Book.objects.public().filter(
            Q(titulo__icontains=query) | Q(authors__nome__icontains=query)
        ).distinct()[:5]
        processed_local_results = [
            {
                'id': book.id, 'external_id': book.external_id, 'titulo': book.titulo,
                'autores': [author.get_nome_completo() for author in book.authors.all()],
                'capa_url': book.get_display_cover_url(),
                'data_publicacao': book.data_publicacao.year if book.data_publicacao else 'N/A',
                'descricao': book.descricao or 'Descrição não disponível', 'source': 'local'
            } for book in local_books
        ]

    # --- Busca Externa com Paginação ---
    google_client = GoogleBooksClient(context="search")
    processed_external_results = []
    external_data = {}

    try:
        external_data = google_client.search_books(
            query, search_type='title', page=page, items_per_page=10
        )

        # ✅ MELHORIA: Se a busca externa retornar um erro (ex: página inválida), registramos
        if external_data.get('error'):
            logger.warning(
                f"API do Google retornou um erro para query '{query}' na página {page}: {external_data['error']}")

        local_external_ids = {book['external_id'] for book in processed_local_results if book['external_id']}

        for item in external_data.get('books', []):
            external_id = item.get('id')
            if page == 1 and external_id in local_external_ids:
                continue

            data_publicacao = item.get('published_date', 'N/A')

            processed_external_results.append({
                'id': None, 'external_id': external_id,
                'titulo': item.get('title', 'Título não disponível'),
                'autores': item.get('authors', ['Autor desconhecido']),
                'capa_url': item.get('thumbnail', static('images/no-cover.svg')),
                'data_publicacao': data_publicacao,
                'descricao': item.get('description', 'Descrição não disponível'),
                'source': 'google'
            })

    except Exception as e:
        logger.error(f"Erro na busca externa de livros: {e}", exc_info=True)

    # --- Combinação e Resposta Final ---
    combined_results = processed_local_results + processed_external_results

    # ✅ LÓGICA ANTI-ERRO: Se a busca não encontrou NADA (nem local, nem externo)
    # e estamos além da primeira página, significa que chegamos ao fim.
    if not combined_results and page > 1:
        return JsonResponse({
            'books': [],  # Retorna lista vazia para o JS parar de pedir mais páginas
            'total_pages': page,  # Informa que a página atual é a última
            'current_page': page,
            'has_previous': True,
            'has_next': False  # Garante que não há próxima página
        })

    return JsonResponse({
        'books': combined_results,
        'total_pages': external_data.get('total_pages', 1 if combined_results else 0),
        'current_page': external_data.get('current_page', 1),
        'has_previous': external_data.get('has_previous', False),
        'has_next': external_data.get('has_next', False)
    })


@login_required
def external_book_details_view(request, external_id):
    """
    (VERSÃO ROBUSTA - COM VERIFICAÇÃO DE TEMPLATE)
    Exibe detalhes de um livro, buscando na API e passando um dicionário para o template.
    """
    from django.template.loader import get_template
    from django.template.exceptions import TemplateDoesNotExist

    book_in_db = None
    try:
        # 1. Busca sempre na API primeiro para ter os dados mais recentes
        google_client = GoogleBooksClient()
        api_data = google_client.get_book_by_id(external_id)

        if not api_data:
            raise Http404("Detalhes do livro não encontrados na API externa.")

        # 2. Verifica se o livro já existe no nosso banco de dados
        book_in_db = Book.objects.filter(external_id=external_id).first()

        # 3. Monta um dicionário com os dados para o template
        volume_info = api_data.get('volumeInfo', {})

        # Constrói o nosso objeto de livro para o template
        book_context = {
            'id': book_in_db.id if book_in_db else None,
            'titulo': volume_info.get('title', 'Título não disponível'),
            'subtitulo': volume_info.get('subtitle', ''),
            'autor': ', '.join(volume_info.get('authors', ['Autor desconhecido'])),
            'editora': volume_info.get('publisher', ''),
            'descricao': volume_info.get('description', ''),
            'numero_paginas': volume_info.get('pageCount'),
            'capa_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
            'external_id': external_id,
            'is_temporary': not bool(book_in_db),
            # Adiciona campos necessários para compatibilidade com template
            'isbn': volume_info.get('industryIdentifiers', [{}])[0].get('identifier', ''),
            'idioma': volume_info.get('language', ''),
            'categoria': volume_info.get('categories', []),
            'genero': ', '.join(volume_info.get('categories', [])) if volume_info.get('categories') else '',
        }

        # Adiciona métodos "mock" para compatibilidade com o template
        def get_display_cover_url():
            return book_context['capa_url'] if book_context['capa_url'] else static('images/no-cover.svg')

        def get_preview_url():
            # Para livros externos, usar a mesma URL da capa
            return get_display_cover_url()

        def get_capa_url():
            return get_display_cover_url()

        # Adiciona os métodos ao contexto
        book_context['get_display_cover_url'] = get_display_cover_url
        book_context['get_capa_url'] = get_capa_url
        book_context['get_preview_url'] = get_preview_url

        # Processa data de publicação
        data_pub_str = volume_info.get('publishedDate')
        if data_pub_str:
            try:
                if len(data_pub_str) == 4:  # Apenas ano
                    book_context['data_publicacao'] = datetime.strptime(data_pub_str, '%Y').date()
                elif len(data_pub_str) == 7:  # Ano-Mês
                    book_context['data_publicacao'] = datetime.strptime(data_pub_str + '-01', '%Y-%m-%d').date()
                else:  # Data completa
                    book_context['data_publicacao'] = datetime.strptime(data_pub_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    book_context['data_publicacao'] = datetime.strptime(data_pub_str[:4], '%Y').date()
                except ValueError:
                    book_context['data_publicacao'] = None
        else:
            book_context['data_publicacao'] = None

        # 4. Determina o status da prateleira do usuário
        user_shelf = None
        shelf_display = 'Não está em sua prateleira'

        if request.user.is_authenticated and book_in_db:
            shelf_entry = UserBookShelf.objects.filter(user=request.user, book=book_in_db).first()
            if shelf_entry:
                user_shelf = shelf_entry.shelf_type
                shelf_display = shelf_entry.get_shelf_type_display()

        # 5. Prepara o contexto final
        context = {
            'book': book_context,
            'book_json': json.dumps(book_context, default=str),
            'shelf': user_shelf,
            'shelf_display': shelf_display,
            'is_from_recommendation': request.GET.get('from') == 'recommendations',
        }

        # ✅ CORREÇÃO: Tenta diferentes caminhos de template
        template_paths = [
            'core/book/book_details.html',
            'core/book_details.html',
            'book_details.html',
            'core/book/details.html'
        ]

        template_to_use = None
        for template_path in template_paths:
            try:
                get_template(template_path)
                template_to_use = template_path
                logger.info(f"[external_book_details_view] Template encontrado: {template_path}")
                break
            except TemplateDoesNotExist:
                continue

        if not template_to_use:
            logger.error(f"[external_book_details_view] Nenhum template encontrado. Testados: {template_paths}")
            raise TemplateDoesNotExist("Nenhum template de detalhes de livro encontrado")

        logger.info(
            f"[external_book_details_view] Renderizando template {template_to_use} para livro: {book_context['titulo']}")
        return render(request, template_to_use, context)

    except Http404 as e:
        logger.warning(f"Http404 em external_book_details_view para ID {external_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado em external_book_details_view para ID {external_id}: {e}", exc_info=True)
        return render(request, 'core/error.html', {'error_message': 'Ocorreu um erro inesperado.'})


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
@require_http_methods(["POST"])
def add_to_shelf(request):
    """
    Adiciona um livro à prateleira do usuário.
    Versão simplificada e corrigida com melhor tratamento de erros.

    Aceita tanto dados JSON quanto form-urlencoded.
    Suporta tanto livros existentes quanto criação de novos livros a partir de dados externos.
    """
    try:
        # Determinar o tipo de conteúdo e extrair dados
        if request.content_type == 'application/json' or request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                # Fallback para form data se JSON falhar
                data = dict(request.POST.items())
        else:
            data = dict(request.POST.items())

        logger.info(f"[add_to_shelf] Dados recebidos: {json.dumps(data, indent=2)}")

        # Extrair parâmetros com múltiplas tentativas para compatibilidade
        book_id = data.get('book_id')
        shelf_type = data.get('shelf_type') or data.get('shelf')
        book_data = data.get('book_data', {})

        # Log dos parâmetros extraídos
        logger.info(f"[add_to_shelf] Parâmetros: book_id={book_id}, shelf_type={shelf_type}")

        # Validação de parâmetros básicos
        if not shelf_type:
            logger.error("[add_to_shelf] Tipo de prateleira não fornecido")
            return JsonResponse({
                'success': False,
                'error': 'Tipo de prateleira é obrigatório'
            }, status=400)

        # Normalizar e validar o tipo de prateleira
        shelf_type = normalize_shelf_type(shelf_type)
        if not shelf_type:
            logger.error(f"[add_to_shelf] Tipo de prateleira inválido após normalização")
            return JsonResponse({
                'success': False,
                'error': 'Tipo de prateleira inválido'
            }, status=400)

        # Cenário 1: Livro existente (book_id fornecido)
        if book_id:
            return handle_existing_book(request.user, book_id, shelf_type)

        # Cenário 2: Criar livro a partir de dados externos
        elif book_data:
            return handle_external_book_creation(request.user, book_data, shelf_type)

        else:
            logger.error("[add_to_shelf] Nem book_id nem book_data fornecidos")
            return JsonResponse({
                'success': False,
                'error': 'ID do livro ou dados do livro são obrigatórios'
            }, status=400)

    except Exception as e:
        logger.error(f"[add_to_shelf] Erro não tratado: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)


def normalize_shelf_type(shelf_type):
    """
    Normaliza o tipo de prateleira para garantir compatibilidade.

    Args:
        shelf_type: Tipo de prateleira recebido

    Returns:
        str: Tipo normalizado ou None se inválido
    """
    # Mapeamento de compatibilidade
    shelf_mapping = {
        'favoritos': 'favorito',
        'lidos': 'lido',
        'lendo': 'lendo',
        'vou_ler': 'vou_ler',
        'quero_ler': 'vou_ler',
        'want_to_read': 'vou_ler',
        'reading': 'lendo',
        'read': 'lido',
        'favorites': 'favorito',
        'favorite': 'favorito'
    }

    # Normalizar para minúsculo e tentar mapear
    shelf_normalized = str(shelf_type).lower().strip()
    shelf_final = shelf_mapping.get(shelf_normalized, shelf_normalized)

    # Validar contra os tipos válidos
    valid_types = dict(UserBookShelf.SHELF_CHOICES).keys()

    if shelf_final in valid_types:
        logger.info(f"[normalize_shelf_type] '{shelf_type}' normalizado para '{shelf_final}'")
        return shelf_final

    logger.error(f"[normalize_shelf_type] Tipo inválido: '{shelf_type}' -> '{shelf_final}'")
    return None


def handle_existing_book(user, book_id, shelf_type):
    """
    Lida com adição de livro existente à prateleira.

    Args:
        user: Usuário
        book_id: ID do livro
        shelf_type: Tipo de prateleira normalizado

    Returns:
        JsonResponse
    """
    try:
        logger.info(f"[handle_existing_book] Processando livro ID: {book_id}")

        # Buscar o livro
        book = Book.objects.get(id=book_id)
        logger.info(f"[handle_existing_book] Livro encontrado: '{book.titulo}'")

        # Usar o método otimizado do modelo para adicionar à prateleira
        shelf_obj, created, moved_from = UserBookShelf.add_to_shelf(user, book, shelf_type)

        # Preparar mensagem de resposta
        if created:
            message = f'Livro adicionado à prateleira "{shelf_obj.get_shelf_type_display()}" com sucesso!'
        elif moved_from:
            message = f'Livro movido de "{moved_from}" para "{shelf_obj.get_shelf_type_display()}"!'
        else:
            message = f'Livro já estava na prateleira "{shelf_obj.get_shelf_type_display()}"'

        logger.info(f"[handle_existing_book] Sucesso: {message}")

        return JsonResponse({
            'success': True,
            'message': message,
            'created': created,
            'moved_from': moved_from
        })

    except Book.DoesNotExist:
        logger.error(f"[handle_existing_book] Livro ID {book_id} não encontrado")
        return JsonResponse({
            'success': False,
            'error': 'Livro não encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"[handle_existing_book] Erro: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar livro existente'
        }, status=500)


def handle_external_book_creation(user, book_data, shelf_type):
    """
    Cria um novo livro a partir de dados externos e adiciona à prateleira.

    Args:
        user: Usuário
        book_data: Dados do livro
        shelf_type: Tipo de prateleira normalizado

    Returns:
        JsonResponse
    """
    try:
        logger.info("[handle_external_book_creation] Iniciando criação de livro externo")

        # Validar dados essenciais
        external_id = book_data.get('external_id')
        titulo = book_data.get('titulo')

        if not titulo:
            return JsonResponse({
                'success': False,
                'error': 'Título do livro é obrigatório'
            }, status=400)

        # Verificar se o livro já existe (por external_id se disponível)
        book = None
        if external_id:
            book = Book.objects.filter(external_id=external_id).first()
            if book:
                logger.info(f"[handle_external_book_creation] Livro já existe: {book.titulo}")
                return handle_existing_book(user, book.id, shelf_type)

        # Preparar dados do livro
        book_defaults = prepare_book_data(book_data, user)

        # Criar o livro
        book, created = Book.objects.get_or_create(
            titulo=titulo,
            autor=book_defaults.get('autor', 'Autor desconhecido'),
            defaults=book_defaults
        )

        if created:
            logger.info(f"[handle_external_book_creation] Novo livro criado: {book.titulo}")
        else:
            logger.info(f"[handle_external_book_creation] Livro existente encontrado: {book.titulo}")

        # Processar e salvar capa se disponível
        process_book_cover(book, book_data)

        # Adicionar à prateleira
        shelf_obj, shelf_created, moved_from = UserBookShelf.add_to_shelf(user, book, shelf_type)

        message = f'Livro "{book.titulo}" adicionado à prateleira "{shelf_obj.get_shelf_type_display()}" com sucesso!'

        return JsonResponse({
            'success': True,
            'message': message,
            'book_created': created,
            'shelf_created': shelf_created
        })

    except Exception as e:
        logger.error(f"[handle_external_book_creation] Erro: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Erro ao criar livro a partir de dados externos'
        }, status=500)


def prepare_book_data(book_data, user):
    """
    Prepara os dados do livro para criação.

    Args:
        book_data: Dados brutos do livro
        user: Usuário que está criando

    Returns:
        dict: Dados preparados para criação do livro
    """
    from decimal import Decimal
    from datetime import datetime

    # Dados básicos
    defaults = {
        'visibility': Book.Visibility.PRIVATE,  # Livros criados por usuários são privados por padrão
        'created_by': user,
        'titulo': book_data.get('titulo', 'Título não disponível'),
        'subtitulo': book_data.get('subtitulo', ''),
        'autor': ', '.join(book_data.get('autores', ['Autor desconhecido'])),
        'editora': book_data.get('editora', ''),
        'isbn': book_data.get('isbn', ''),
        'descricao': book_data.get('descricao', ''),
        'categoria': ', '.join(book_data.get('categorias', [])) if book_data.get('categorias') else '',
        'external_id': book_data.get('external_id'),
        'capa_url': book_data.get('capa_url', ''),
        'origem': 'user_import'
    }

    # Processar data de publicação
    data_pub_str = book_data.get('data_publicacao')
    if data_pub_str:
        try:
            if len(str(data_pub_str)) == 4:  # Apenas ano
                defaults['data_publicacao'] = datetime.strptime(str(data_pub_str), '%Y').date()
            else:  # Data completa
                defaults['data_publicacao'] = datetime.strptime(str(data_pub_str)[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            logger.warning(f"[prepare_book_data] Data inválida '{data_pub_str}': {e}")

    # Processar preços
    try:
        if book_data.get('preco'):
            defaults['preco'] = Decimal(str(book_data['preco']))
        if book_data.get('preco_promocional'):
            defaults['preco_promocional'] = Decimal(str(book_data['preco_promocional']))
    except (ValueError, TypeError) as e:
        logger.warning(f"[prepare_book_data] Erro ao processar preços: {e}")

    return defaults


def process_book_cover(book, book_data):
    """
    Processa e salva a capa do livro se disponível.

    Args:
        book: Instância do livro
        book_data: Dados do livro com URL da capa
    """
    thumbnail_url = book_data.get('capa_url')
    if not thumbnail_url:
        return

    try:
        logger.info(f"[process_book_cover] Baixando capa de: {thumbnail_url}")

        response = requests.get(thumbnail_url, timeout=10)
        response.raise_for_status()

        # Usar o mixin para salvar a imagem
        mixin = BookManagementMixin()
        filename = f"book_{book.id}_{timezone.now().timestamp()}.jpg"
        saved_paths = mixin.save_cover_image(response.content, filename)

        if saved_paths and isinstance(saved_paths, tuple):
            capa_path, preview_path = saved_paths
            book.capa = capa_path
            book.capa_preview = preview_path
            book.save(update_fields=['capa', 'capa_preview'])
            logger.info(f"[process_book_cover] Capa salva: {capa_path}")

    except requests.RequestException as e:
        logger.error(f"[process_book_cover] Erro ao baixar capa: {e}")
    except Exception as e:
        logger.error(f"[process_book_cover] Erro ao processar capa: {e}")


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

    def get_queryset(self):
        # Garante que só se possa ver detalhes de livros públicos
        # ou livros privados que o próprio usuário adicionou.
        return Book.objects.filter(
            Q(visibility=Book.Visibility.PUBLIC) |
            (Q(visibility=Book.Visibility.PRIVATE) & Q(created_by=self.request.user))
        ).distinct()

    def get_context_data(self, **kwargs):
        """
        Adiciona informações da prateleira ao contexto com verificações de segurança aprimoradas.

        Returns:
            dict: Contexto estendido com informações da prateleira
        """
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        # >>>>> CORREÇÃO APLICADA AQUI <<<<<
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
def add_external_book_to_shelf(request):
    """
    Cria um livro 'privado' a partir de dados externos e o adiciona à prateleira.
    AGORA COM DOWNLOAD E SALVAMENTO DA CAPA.
    """
    try:
        data = json.loads(request.body)
        book_data = data.get('book_data', {})
        shelf_type = data.get('shelf_type')

        if not all([book_data, shelf_type, book_data.get('external_id')]):
            return JsonResponse({'success': False, 'error': 'Dados incompletos.'}, status=400)

        external_id = book_data['external_id']
        book = Book.objects.filter(external_id=external_id).first()

        if not book:
            data_pub = None
            if book_data.get('data_publicacao'):
                try:
                    pub_date_str = str(book_data['data_publicacao'])
                    if len(pub_date_str) == 4:
                        data_pub = datetime.strptime(pub_date_str, '%Y').date()
                    else:
                        data_pub = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    data_pub = None

            # >>>>> INÍCIO DA LÓGICA DE SALVAR A IMAGEM <<<<<
            capa_path = None
            capa_preview_path = None
            mixin = BookManagementMixin()
            thumbnail_url = book_data.get('capa_url')

            if thumbnail_url:
                try:
                    response = requests.get(thumbnail_url, timeout=10)
                    response.raise_for_status()

                    filename = f"book_{external_id}.jpg"
                    saved_paths = mixin.save_cover_image(response.content, filename)

                    if saved_paths and isinstance(saved_paths, tuple):
                        capa_path, capa_preview_path = saved_paths
                        logger.info(f"Capa para {external_id} salva em: {capa_path}")

                except requests.RequestException as e:
                    logger.error(f"Erro ao baixar a imagem da capa de {thumbnail_url}: {e}")
                except Exception as e:
                    logger.error(f"Erro ao processar e salvar a capa: {e}", exc_info=True)
            # >>>>> FIM DA LÓGICA DE SALVAR A IMAGEM <<<<<

            book = Book.objects.create(
                visibility=Book.Visibility.PRIVATE,
                created_by=request.user,
                titulo=book_data.get('titulo', 'Título não disponível'),
                autor=', '.join(book_data.get('autores', ['Autor desconhecido'])),
                editora=book_data.get('editora', ''),
                data_publicacao=data_pub,
                descricao=book_data.get('descricao', ''),
                capa_url=thumbnail_url,
                capa=capa_path,  # SALVANDO O CAMINHO DA IMAGEM LOCAL
                capa_preview=capa_preview_path,  # SALVANDO O CAMINHO DO PREVIEW
                external_id=external_id,
                origem='google_books_user'
            )

        shelf_obj, created = UserBookShelf.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={'shelf_type': shelf_type}
        )

        message = 'Livro adicionado à sua prateleira com sucesso!'
        if not created:
            message = f'Livro movido para a prateleira "{shelf_obj.get_shelf_type_display()}"'

        return JsonResponse({'success': True, 'message': message})

    except Exception as e:
        logger.error(f"Erro em add_external_book_to_shelf: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Ocorreu um erro interno.'}, status=500)


class CatalogueView(TemplateView):
    """
    View para página de catálogo completo de livros.

    Exibe todos os livros PÚBLICOS cadastrados no sistema.
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

        # Base query agora usa nosso manager para pegar apenas livros públicos.
        # A filtragem de 'is_temporary' não é mais necessária se livros
        # temporários também forem 'private'.
        books = Book.objects.public()

        # Aplicar filtros se fornecidos (esta lógica continua a mesma)
        if search_query:
            books = books.filter(
                Q(titulo__icontains=search_query) |
                Q(autor__icontains=search_query) |
                Q(categoria__icontains=search_query)
            )

        if categoria_filter:
            books = books.filter(
                Q(categoria=categoria_filter) |
                Q(categoria__icontains=f"'{categoria_filter}'")
            )

        # Aplicar ordenação (esta lógica continua a mesma)
        valid_sort_fields = ['titulo', '-titulo', 'autor', '-autor', 'data_publicacao', '-data_publicacao']
        if sort_param in valid_sort_fields:
            books = books.order_by(sort_param)
        else:
            # A ordenação padrão já está no meta do modelo, mas podemos garantir aqui
            books = books.order_by('titulo')

        # Implementar paginação (esta lógica continua a mesma)
        paginator = Paginator(books, items_per_page)
        books_page = paginator.get_page(page)

        # A busca por categorias também deve ser feita apenas em livros públicos
        raw_categories = Book.objects.public().exclude(
            Q(categoria__isnull=True) | Q(categoria='')
        ).values_list('categoria', flat=True).distinct()

        # Processa as categorias (esta lógica continua a mesma)
        processed_categories = set()
        for cat in raw_categories:
            if cat.startswith('[') and cat.endswith(']'):
                try:
                    import ast
                    cat_list = ast.literal_eval(cat)
                    for item in cat_list:
                        if item:
                            processed_categories.add(item)
                except (ValueError, SyntaxError):
                    processed_categories.add(cat)
            else:
                processed_categories.add(cat)

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

    Exibe os livros PÚBLICOS marcados como lançamentos.
    """
    template_name = 'core/book/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # A consulta base agora começa com os livros públicos.
        base_query = Book.objects.public()

        # Primeiro, tentamos a busca pelo campo booleano, que é o mais direto.
        releases = base_query.filter(e_lancamento=True).order_by('-data_publicacao', 'titulo')

        # Se a primeira busca não retornar nada, tentamos a busca alternativa
        # pelo campo de texto 'tipo_shelf_especial'.
        if not releases.exists():
            releases = base_query.filter(tipo_shelf_especial='lancamentos').order_by('-data_publicacao', 'titulo')

        context.update({
            'title': 'Novos Lançamentos',
            'books': releases,
            'description': 'Descubra os mais recentes lançamentos do mundo literário.'
        })

        return context


class BestSellersView(TemplateView):
    """
    View para página de livros mais vendidos.

    Exibe os livros PÚBLICOS com maior quantidade de vendas.
    """
    template_name = 'core/book/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # A consulta base agora começa com os livros públicos.
        base_query = Book.objects.public()

        # Primeiro, tentamos buscar livros especificamente marcados como 'mais_vendidos'.
        bestsellers = base_query.filter(
            tipo_shelf_especial='mais_vendidos'
        ).order_by('-quantidade_vendida', 'titulo')

        # Se a busca específica não retornar resultados, pegamos o ranking geral dos 20
        # livros públicos mais vendidos (com quantidade_vendida > 0).
        if not bestsellers.exists():
            bestsellers = base_query.filter(
                quantidade_vendida__gt=0
            ).order_by('-quantidade_vendida', 'titulo')[:20]

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