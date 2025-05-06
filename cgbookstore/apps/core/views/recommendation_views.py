import json
import logging
import uuid
import traceback
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.serializers.json import DjangoJSONEncoder

from cgbookstore.apps.core.recommendations.engine import RecommendationEngine
from cgbookstore.apps.core.recommendations.utils.image_utils import standardize_google_book_cover
from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient
from cgbookstore.apps.core.models.book import Book, UserBookShelf

logger = logging.getLogger(__name__)

@login_required
@require_GET
def get_recommendations_view(request):
    """
    View para exibir recomendações mistas (locais + externas) em uma página renderizada
    """
    try:
        engine = RecommendationEngine()
        mixed_data = engine.get_mixed_recommendations(request.user)

        # Processamento dos livros externos
        processed_external = []
        if mixed_data.get('has_external', False) and mixed_data.get('external', []):
            for book in mixed_data['external']:
                try:
                    # Verificar o tipo de objeto externo (dicionário ou modelo Book)
                    if isinstance(book, dict):
                        # Verifica se já tem a estrutura do Google Books
                        if 'volumeInfo' in book:
                            # Padroniza o tamanho da capa
                            if 'imageLinks' in book['volumeInfo'] and 'thumbnail' in book['volumeInfo']['imageLinks']:
                                book['volumeInfo']['imageLinks']['thumbnail'] = standardize_google_book_cover(
                                    book['volumeInfo']['imageLinks']['thumbnail'], 'M'
                                )
                            processed_external.append(book)
                        else:
                            # Constrói estrutura compatível
                            thumbnail = standardize_google_book_cover(
                                book.get('thumbnail', book.get('capa_url', '')), 'M'
                            )
                            book_info = {
                                'id': book.get('id', f"temp_{uuid.uuid4().hex}"),
                                'volumeInfo': {
                                    'title': book.get('title', book.get('titulo', 'Sem título')),
                                    'authors': book.get('authors', [book.get('autor', 'Autor desconhecido')]),
                                    'imageLinks': {'thumbnail': thumbnail},
                                    'description': book.get('description', book.get('descricao', '')),
                                    'categories': book.get('categories', [book.get('genero', '')])
                                }
                            }
                            processed_external.append(book_info)
                    elif hasattr(book, 'external_data') and book.external_data:
                        # É um objeto Book com dados externos em JSON
                        try:
                            # Carregar dados externos salvos
                            external_info = json.loads(book.external_data)

                            # Verificar se já tem a estrutura volumeInfo
                            if 'volumeInfo' not in external_info:
                                # Criar estrutura semelhante à API Google Books
                                thumbnail = standardize_google_book_cover(
                                    book.capa_url if hasattr(book, 'capa_url') and book.capa_url else '', 'M'
                                )
                                external_info['volumeInfo'] = {
                                    'title': book.titulo if hasattr(book, 'titulo') and book.titulo else 'Sem título',
                                    'authors': [book.autor] if hasattr(book, 'autor') and book.autor else [
                                        'Autor desconhecido'],
                                    'imageLinks': {'thumbnail': thumbnail},
                                    'description': book.descricao if hasattr(book,
                                        'descricao') and book.descricao else '',
                                    'categories': [book.genero] if hasattr(book, 'genero') and book.genero else []
                                }
                            else:
                                # Padroniza o tamanho da capa
                                if 'imageLinks' in external_info['volumeInfo'] and 'thumbnail' in external_info['volumeInfo']['imageLinks']:
                                    external_info['volumeInfo']['imageLinks']['thumbnail'] = standardize_google_book_cover(
                                        external_info['volumeInfo']['imageLinks']['thumbnail'], 'M'
                                    )

                            # Adicionar ID externo para referência
                            if not external_info.get('id') and hasattr(book, 'external_id') and book.external_id:
                                external_info['id'] = book.external_id
                            elif not external_info.get('id'):
                                external_info['id'] = f"temp_{getattr(book, 'id', uuid.uuid4().hex)}"

                            processed_external.append(external_info)
                        except (json.JSONDecodeError, TypeError, AttributeError) as e:
                            logger.error(f"Erro ao processar JSON de livro externo: {str(e)}")
                            # Fallback para dados básicos do modelo
                            thumbnail = standardize_google_book_cover(
                                getattr(book, 'capa_url', ''), 'M'
                            )
                            fallback_book = {
                                'id': getattr(book, 'external_id', f"temp_{getattr(book, 'id', uuid.uuid4().hex)}"),
                                'volumeInfo': {
                                    'title': getattr(book, 'titulo', 'Título indisponível'),
                                    'authors': [getattr(book, 'autor', 'Autor desconhecido')],
                                    'imageLinks': {'thumbnail': thumbnail},
                                    'description': getattr(book, 'descricao', ''),
                                    'categories': [getattr(book, 'genero', '')]
                                }
                            }
                            processed_external.append(fallback_book)
                    else:
                        # É um objeto Book sem dados externos estruturados
                        thumbnail = standardize_google_book_cover(
                            getattr(book, 'capa_url', ''), 'M'
                        )
                        fallback_book = {
                            'id': getattr(book, 'external_id', f"temp_{getattr(book, 'id', uuid.uuid4().hex)}"),
                            'volumeInfo': {
                                'title': getattr(book, 'titulo', 'Título indisponível'),
                                'authors': [getattr(book, 'autor', 'Autor desconhecido')],
                                'imageLinks': {'thumbnail': thumbnail},
                                'description': getattr(book, 'descricao', ''),
                                'categories': [getattr(book, 'genero', '')]
                            }
                        }
                        processed_external.append(fallback_book)
                except Exception as book_error:
                    logger.error(f"Erro ao processar livro individual: {str(book_error)}")
                    continue

        context = {
            'local_recommendations': mixed_data.get('local', []),
            'external_recommendations': processed_external,
            'has_external': bool(processed_external),
            'user': request.user,
        }

        return render(request, 'core/recommendations/mixed_recommendations.html', context)
    except Exception as e:
        logger.error(f"Erro na view de recomendações: {str(e)}")
        logger.error(traceback.format_exc())

        # Retorna uma resposta de fallback em caso de erro
        return render(request, 'core/recommendations/mixed_recommendations.html', {
            'local_recommendations': [],
            'external_recommendations': [],
            'has_external': False,
            'user': request.user,
            'error': 'Erro ao carregar recomendações'
        })

@login_required
@require_POST
@csrf_protect
def import_external_book(request):
    """
    Endpoint para importar um livro externo para o catálogo local
    """
    try:
        # Tenta extrair os dados do corpo da requisição
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'erro',
                'message': 'Formato de dados inválido'
            }, status=400)

        # Extrair dados básicos do livro
        external_id = data.get('external_id')
        title = data.get('title')
        author = data.get('author')
        cover_url = data.get('cover_url')
        publisher = data.get('publisher', '')
        published_date = data.get('published_date', '')
        description = data.get('description', '')
        page_count = data.get('page_count', 0)
        categories = data.get('categories', '')
        language = data.get('language', 'pt')
        shelf_type = data.get('shelf_type')

        # Validação de dados obrigatórios
        if not all([title, shelf_type]):
            return JsonResponse({
                'status': 'erro',
                'message': 'Título e tipo de prateleira são obrigatórios'
            }, status=400)

        # Usa valores de fallback para campos opcionais críticos
        if not author:
            author = 'Autor desconhecido'
        if not external_id:
            external_id = f"manual_{uuid.uuid4().hex}"

        # Verificar se o livro já existe no catálogo
        existing_book = Book.objects.filter(
            titulo__iexact=title,
            autor__iexact=author
        ).first()

        if existing_book:
            # Se o livro já existe, apenas adiciona à prateleira
            shelf, created = UserBookShelf.objects.get_or_create(
                user=request.user,
                book=existing_book,
                defaults={'shelf_type': shelf_type, 'added_at': datetime.now()}
            )

            if not created:
                shelf.shelf_type = shelf_type
                shelf.save()

            return JsonResponse({
                'status': 'sucesso',
                'message': 'Livro já existente adicionado à prateleira',
                'book_id': existing_book.id
            })

        # Criar novo livro no banco de dados
        try:
            # Tratamento para a data de publicação
            data_publicacao = None
            if published_date:
                try:
                    # Tenta converter para data
                    if len(published_date) >= 10: # Formato completo YYYY-MM-DD
                        data_publicacao = datetime.strptime(published_date[:10], '%Y-%m-%d').date()
                    elif len(published_date) >= 7: # Formato YYYY-MM
                        data_publicacao = datetime.strptime(published_date[:7], '%Y-%m').date()
                    elif len(published_date) >= 4: # Apenas ano YYYY
                        data_publicacao = datetime.strptime(f"{published_date[:4]}-01-01", '%Y-%m-%d').date()
                except ValueError:
                    # Se falhar na conversão, mantém como None
                    data_publicacao = None

            new_book = Book.objects.create(
                titulo=title,
                autor=author,
                editora=publisher,
                data_publicacao=data_publicacao,
                descricao=description,
                numero_paginas=page_count if isinstance(page_count, int) else 0,
                genero=categories.split(',')[0] if categories and ',' in categories else categories,
                idioma=language,
                capa_url=cover_url,
                external_id=external_id
            )
        except Exception as book_error:
            logger.error(f"Erro ao criar livro: {str(book_error)}")
            return JsonResponse({
                'status': 'erro',
                'message': f'Erro ao criar livro: {str(book_error)}'
            }, status=500)

        # Adicionar à prateleira do usuário
        try:
            UserBookShelf.objects.create(
                user=request.user,
                book=new_book,
                shelf_type=shelf_type,
                added_at=datetime.now()
            )
        except Exception as shelf_error:
            logger.error(f"Erro ao adicionar à prateleira: {str(shelf_error)}")
            # Remover o livro criado para evitar inconsistências
            new_book.delete()
            return JsonResponse({
                'status': 'erro',
                'message': f'Erro ao adicionar à prateleira: {str(shelf_error)}'
            }, status=500)

        return JsonResponse({
            'status': 'sucesso',
            'message': 'Livro importado com sucesso',
            'book_id': new_book.id
        })

    except Exception as e:
        logger.error(f"Erro ao importar livro externo: {str(e)}")
        return JsonResponse({
            'status': 'erro',
            'message': f'Erro ao importar livro: {str(e)}'
        }, status=500)

@login_required
@require_GET
def get_recommendations_json(request):
    """
    Endpoint JSON para recomendações mistas
    """
    try:
        engine = RecommendationEngine()
        mixed_data = engine.get_mixed_recommendations(request.user)

        # Converte QuerySet para lista de dicionários
        local_books = []
        for book in mixed_data.get('local', []):
            try:
                local_books.append({
                    'id': book.id,
                    'titulo': book.titulo if hasattr(book, 'titulo') else 'Sem título',
                    'autor': book.autor if hasattr(book, 'autor') else 'Autor desconhecido',
                    'genero': book.genero if hasattr(book, 'genero') else '',
                    'categoria': book.categoria if hasattr(book, 'categoria') else '',
                    'capa_url': book.get_capa_url() if hasattr(book, 'get_capa_url') else
                        (book.capa_url if hasattr(book, 'capa_url') else ''),
                    'origem': 'local'
                })
            except Exception as book_error:
                logger.warning(f"Erro ao processar livro local para JSON: {str(book_error)}")
                continue

        # Organiza os livros externos no mesmo formato
        external_books = []
        for book in mixed_data.get('external', []):
            try:
                # Verificar se o livro é um dicionário ou um objeto Book
                if isinstance(book, dict):
                    if 'volumeInfo' in book:
                        info = book.get('volumeInfo', {})
                        external_books.append({
                            'titulo': info.get('title', 'Sem título'),
                            'autor': ', '.join(info.get('authors', ['Autor desconhecido'])) if isinstance(
                                info.get('authors', []), list) else str(info.get('authors', 'Autor desconhecido')),
                            'genero': info.get('categories', [''])[0] if info.get('categories') and isinstance(
                                info.get('categories'), list) else '',
                            'capa_url': info.get('imageLinks', {}).get('thumbnail', ''),
                            'external_id': book.get('id', ''),
                            'origem': 'Google Books',
                            'is_external': True
                        })
                    else:
                        # Formato diferente do padrão volumeInfo
                        external_books.append({
                            'titulo': book.get('title', book.get('titulo', 'Sem título')),
                            'autor': book.get('author', book.get('autor', 'Autor desconhecido')),
                            'genero': book.get('category', book.get('genero', '')),
                            'capa_url': book.get('thumbnail', book.get('capa_url', '')),
                            'external_id': book.get('id', book.get('external_id', '')),
                            'origem': 'Google Books',
                            'is_external': True
                        })
                elif hasattr(book, 'external_id') or hasattr(book, 'external_data'):
                    # Livro do modelo com dados externos
                    external_data = {}

                    # Tenta carregar dados externos se disponíveis
                    if hasattr(book, 'external_data') and book.external_data:
                        try:
                            external_data = json.loads(book.external_data)
                        except (json.JSONDecodeError, TypeError):
                            external_data = {}

                    external_books.append({
                        'titulo': book.titulo if hasattr(book, 'titulo') else 'Sem título',
                        'autor': book.autor if hasattr(book, 'autor') else 'Autor desconhecido',
                        'genero': book.genero if hasattr(book, 'genero') else '',
                        'capa_url': book.capa_url if hasattr(book, 'capa_url') else '',
                        'external_id': book.external_id if hasattr(book,
                            'external_id') else f"temp_{book.id}" if hasattr(
                            book, 'id') else '',
                        'origem': 'Google Books',
                        'is_external': True
                    })
            except Exception as book_error:
                logger.warning(f"Erro ao processar livro externo para JSON: {str(book_error)}")
                continue

        # Combina os resultados
        response_data = {
            'local': local_books,
            'external': external_books,
            'has_external': mixed_data.get('has_external', False),
            'total': len(local_books) + len(external_books)
        }

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"Erro na API de recomendações: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'error': 'Erro ao processar recomendações',
            'local': [],
            'external': [],
            'has_external': False,
            'total': 0
        }, status=500)

@login_required
@require_GET
def get_external_book_details(request, external_id):
    """
    View para buscar detalhes de um livro externo específico
    """
    try:
        if not external_id:
            return JsonResponse({'error': 'ID externo não fornecido'}, status=400)

        # Tenta primeiro encontrar um livro local com este ID externo
        local_book = Book.objects.filter(external_id=external_id).first()
        if local_book:
            # Formata dados do livro local no formato da API
            book_data = {
                'id': external_id,
                'volumeInfo': {
                    'title': local_book.titulo,
                    'authors': [local_book.autor] if local_book.autor else ['Autor desconhecido'],
                    'description': local_book.descricao or '',
                    'publisher': local_book.editora or '',
                    'publishedDate': local_book.ano_publicacao or '',
                    'pageCount': local_book.paginas or 0,
                    'categories': [local_book.genero] if local_book.genero else [],
                    'language': local_book.idioma or 'pt',
                    'imageLinks': {
                        'thumbnail': local_book.capa_url or ''
                    }
                }
            }
            return JsonResponse(book_data, encoder=DjangoJSONEncoder, safe=False)

        # Se não encontrou localmente, busca na API
        client = GoogleBooksClient(context="recomendações")
        book_data = client.get_book_by_id(external_id)

        if not book_data:
            return JsonResponse({'error': 'Livro não encontrado'}, status=404)

        # Retorna os dados do livro como JSON
        return JsonResponse(book_data, encoder=DjangoJSONEncoder, safe=False)

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do livro externo: {str(e)}")
        return JsonResponse({'error': 'Erro ao buscar detalhes do livro'}, status=500)

@login_required
@require_GET
def get_personalized_shelf_view(request):
    """
    View para exibir uma prateleira personalizada completa
    """
    try:
        engine = RecommendationEngine()
        shelf_data = engine.get_personalized_shelf(request.user)

        # Prepara dados para paginação
        destaques = shelf_data.get('destaques', [])
        generos = shelf_data.get('por_genero', {})
        autores = shelf_data.get('por_autor', {})
        external_books = shelf_data.get('external_books', [])
        has_external = shelf_data.get('has_external', False)

        # Organiza os dados em seções
        secoes = []

        # Seção de destaques
        if destaques:
            secoes.append({
                'title': 'Destaques para você',
                'books': destaques,
                'type': 'destaques'
            })

        # Seções por gênero
        for genero, livros in generos.items():
            if livros:
                secoes.append({
                    'title': f'Livros de {genero}',
                    'books': livros,
                    'type': 'genero',
                    'genero': genero
                })

        # Seções por autor
        for autor, books in autores.items():
            if books:
                secoes.append({
                    'title': f'Obras de {autor}',
                    'books': books,
                    'type': 'autor',
                    'author': autor
                })

        # Seção de livros externos
        if has_external and external_books:
            # Processar livros externos para garantir formato consistente
            processed_external = []
            for book in external_books:
                try:
                    if isinstance(book, dict):
                        if 'volumeInfo' in book:
                            # Já está no formato correto
                            processed_external.append(book)
                        else:
                            # Converte para formato volumeInfo
                            book_data = {
                                'id': book.get('id', book.get('external_id', f"temp_{uuid.uuid4().hex}")),
                                'volumeInfo': {
                                    'title': book.get('title', book.get('titulo', 'Título desconhecido')),
                                    'authors': book.get('authors', [book.get('autor', 'Autor desconhecido')]),
                                    'imageLinks': {
                                        'thumbnail': book.get('thumbnail', book.get('capa_url', ''))
                                    },
                                    'categories': book.get('categories', [book.get('genero', '')])
                                }
                            }
                            processed_external.append(book_data)
                    elif hasattr(book, 'external_data'):
                        # Objeto Book com dados externos
                        try:
                            book_data = json.loads(book.external_data)
                            if 'volumeInfo' not in book_data:
                                book_data['volumeInfo'] = {
                                    'title': book.titulo if hasattr(book, 'titulo') else 'Título desconhecido',
                                    'authors': [book.autor] if hasattr(book, 'autor') and book.autor else [
                                        'Autor desconhecido'],
                                    'imageLinks': {
                                        'thumbnail': book.capa_url if hasattr(book, 'capa_url') else ''
                                    },
                                    'categories': [book.genero] if hasattr(book, 'genero') and book.genero else []
                                }
                            processed_external.append(book_data)
                        except (json.JSONDecodeError, AttributeError):
                            # Criar estrutura manualmente
                            fallback = {
                                'id': book.external_id if hasattr(book,
                                    'external_id') else f"temp_{book.id}" if hasattr(book,
                                    'id') else f"temp_{uuid.uuid4().hex}",
                                'volumeInfo': {
                                    'title': book.titulo if hasattr(book, 'titulo') else 'Título desconhecido',
                                    'authors': [book.autor] if hasattr(book, 'autor') and book.autor else [
                                        'Autor desconhecido'],
                                    'imageLinks': {
                                        'thumbnail': book.capa_url if hasattr(book, 'capa_url') else ''
                                    },
                                    'categories': [book.genero] if hasattr(book, 'genero') and book.genero else []
                                }
                            }
                            processed_external.append(fallback)
                    else:
                        # Criar estrutura manualmente para objeto Book sem dados externos
                        fallback = {
                            'id': book.external_id if hasattr(book, 'external_id') else f"temp_{book.id}" if hasattr(
                                book, 'id') else f"temp_{uuid.uuid4().hex}",
                            'volumeInfo': {
                                'title': book.titulo if hasattr(book, 'titulo') else 'Título desconhecido',
                                'authors': [book.autor] if hasattr(book, 'autor') and book.autor else [
                                    'Autor desconhecido'],
                                'imageLinks': {
                                    'thumbnail': book.capa_url if hasattr(book, 'capa_url') else ''
                                },
                                'categories': [book.genero] if hasattr(book, 'genero') and book.genero else []
                            }
                        }
                        processed_external.append(fallback)
                except Exception as book_error:
                    logger.warning(f"Erro ao processar livro externo para prateleira: {str(book_error)}")
                    continue

            if processed_external:
                secoes.append({
                    'title': 'Sugestões externas',
                    'books': processed_external,
                    'type': 'externo',
                    'fonte': 'Google Books'
                })

        context = {
            'secoes': secoes,
            'user': request.user,
            'total_recommendations': shelf_data.get('total', 0),
            'has_external': has_external,
        }

        return render(request, 'core/recommendations/personalized_shelf.html', context)
    except Exception as e:
        logger.error(f"Erro ao gerar prateleira personalizada: {str(e)}")
        logger.error(traceback.format_exc())

        # Retorna uma resposta de fallback em caso de erro
        return render(request, 'core/recommendations/personalized_shelf.html', {
            'secoes': [],
            'user': request.user,
            'total_recommendations': 0,
            'has_external': False,
            'error': 'Erro ao carregar prateleira personalizada'
        })

@login_required
@require_POST
@csrf_protect
def add_external_book_to_shelf(request):
    """
    Endpoint para adicionar livro externo diretamente à prateleira
    sem necessidade de importação completa
    """
    try:
        # Tenta desserializar os dados da requisição
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'erro',
                'message': 'Formato de dados inválido'
            }, status=400)

        external_id = data.get('external_id')
        external_data = data.get('external_data')
        shelf_type = data.get('shelf_type')

        # Validação básica
        if not shelf_type:
            return JsonResponse({
                'status': 'erro',
                'message': 'Tipo de prateleira é obrigatório'
            }, status=400)

        if not external_id and not external_data:
            return JsonResponse({
                'status': 'erro',
                'message': 'ID externo ou dados do livro são obrigatórios'
            }, status=400)

        # Se não temos dados externos, mas temos o ID, busca na API
        if not external_data and external_id:
            client = GoogleBooksClient(context="recomendações")
            book_api_data = client.get_book_by_id(external_id)
            if book_api_data:
                external_data = book_api_data

        # Verificar se já existe um livro temporário com este ID externo
        existing_temp = None
        if external_id:
            existing_temp = Book.objects.filter(
                external_id=external_id
            ).first()

        if existing_temp:
            # Se já existe um livro, apenas adiciona à prateleira
            shelf, created = UserBookShelf.objects.get_or_create(
                user=request.user,
                book=existing_temp,
                defaults={'shelf_type': shelf_type, 'added_at': datetime.now()}
            )

            if not created:
                shelf.shelf_type = shelf_type
                shelf.save()

            return JsonResponse({
                'status': 'sucesso',
                'message': 'Livro adicionado à prateleira',
                'book_id': existing_temp.id
            })

        # Extrair dados básicos do livro externo
        if isinstance(external_data, str):
            try:
                book_data = json.loads(external_data)
            except json.JSONDecodeError:
                book_data = {}
        else:
            book_data = external_data if isinstance(external_data, dict) else {}

        # Processar dados para diferentes formatos de resposta
        if 'volumeInfo' in book_data:
            volume_info = book_data.get('volumeInfo', {})

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
        else:
            # Formato alternativo (dados já processados)
            titulo = book_data.get('title', book_data.get('titulo', 'Título desconhecido'))
            autor = book_data.get('author', book_data.get('autor', 'Autor desconhecido'))
            editora = book_data.get('publisher', book_data.get('editora', ''))
            data_publicacao_str = book_data.get('publishedDate', book_data.get('data_publicacao', ''))
            descricao = book_data.get('description', book_data.get('descricao', ''))
            numero_paginas = book_data.get('pageCount', book_data.get('numero_paginas', 0))
            genero = book_data.get('category', book_data.get('genero', ''))
            idioma = book_data.get('language', book_data.get('idioma', 'pt'))
            capa_url = book_data.get('thumbnail', book_data.get('capa_url', ''))

        # Processar data de publicação
        data_publicacao = None
        if data_publicacao_str:
            try:
                # Tenta converter para data
                if len(data_publicacao_str) >= 10: # Formato completo YYYY-MM-DD
                    data_publicacao = datetime.strptime(data_publicacao_str[:10], '%Y-%m-%d').date()
                elif len(data_publicacao_str) >= 7: # Formato YYYY-MM
                    data_publicacao = datetime.strptime(data_publicacao_str[:7], '%Y-%m').date()
                elif len(data_publicacao_str) >= 4: # Apenas ano YYYY
                    data_publicacao = datetime.strptime(f"{data_publicacao_str[:4]}-01-01", '%Y-%m-%d').date()
            except ValueError:
                # Se falhar na conversão, mantém como None
                data_publicacao = None

        # Criar livro temporário ou permanente
        try:
            is_temporary = data.get('is_temporary', True) # Por padrão, considera temporário
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
                external_id=external_id or f"manual_{uuid.uuid4().hex}",
                is_temporary=is_temporary,
                external_data=external_data if isinstance(external_data, str) else json.dumps(book_data)
            )
        except Exception as create_error:
            logger.error(f"Erro ao criar livro temporário: {str(create_error)}")
            return JsonResponse({
                'status': 'erro',
                'message': f'Erro ao criar livro: {str(create_error)}'
            }, status=500)

        # Adicionar à prateleira do usuário
        try:
            UserBookShelf.objects.create(
                user=request.user,
                book=temp_book,
                shelf_type=shelf_type,
                added_at=datetime.now()
            )
        except Exception as shelf_error:
            logger.error(f"Erro ao adicionar à prateleira: {str(shelf_error)}")
            # Remover o livro criado para evitar inconsistências
            temp_book.delete()
            return JsonResponse({
                'status': 'erro',
                'message': f'Erro ao adicionar à prateleira: {str(shelf_error)}'
            }, status=500)

        return JsonResponse({
            'status': 'sucesso',
            'message': 'Livro externo adicionado à prateleira',
            'book_id': temp_book.id
        })

    except Exception as e:
        logger.error(f"Erro ao adicionar livro externo à prateleira: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'erro',
            'message': f'Erro ao processar dados externos: {str(e)}'
        }, status=500)