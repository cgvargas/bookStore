"""
Provedor de recomendações baseado em API externa (Google Books)
"""
from typing import List, Dict, Any, Set, Optional, Union
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
import logging

# Importação correta do serviço GoogleBooks atualizado
from cgbookstore.apps.core.services.google_books_service import GoogleBooksClient
from cgbookstore.apps.core.models.book import Book, UserBookShelf
from cgbookstore.apps.core.recommendations.providers.mapping import CategoryMapping

User = get_user_model()
logger = logging.getLogger(__name__)

class ExternalApiProvider:
    """
    Provedor de recomendações baseado na API do Google Books.
    Complementa as recomendações locais quando necessário.
    """

    def __init__(self):
        """Inicializa o provedor externo"""
        # Use o cliente centralizado com namespace específico
        self.client = GoogleBooksClient(
            cache_namespace="books_recommendations",
            context="recommendations"
        )
        self.max_patterns = 5
        self.category_mapping = CategoryMapping()
        self.max_results_per_query = 10
        self.last_external_recommendations = []
        # Cache de resultados para reduzir chamadas API repetidas
        self._results_cache = {}

    def get_recommendations(self, user: User, limit: int = 8) -> List[Dict]:
        """
        Obtém recomendações externas baseadas nas preferências do usuário.
        Retorna lista de dicionários no formato da API Google Books.
        """
        try:
            # Verificar se já temos recomendações em cache para este usuário
            user_id = user.id if user else 'anonymous'
            user_cache_key = f"ext_recommendations:{user_id}"
            if user_cache_key in self._results_cache:
                cached_results = self._results_cache[user_cache_key]
                logger.info(f"Usando cache de recomendações externas para usuário {user.id}")
                return cached_results[:limit]

            logger.info("=== Buscando recomendações externas ===")

            # Obtém padrões de interesse do usuário
            user_patterns = self._get_user_patterns(user)
            if not user_patterns:
                logger.info("Nenhum padrão encontrado para busca externa")
                return []

            # Busca livros por cada padrão
            all_results = []
            for pattern in user_patterns:
                # Log para depuração
                logger.info(f"[recommendations] Iniciando busca com: {pattern}, tipo: None, max_results: {self.max_results_per_query}")

                # Busca com query específica
                results = self._search_with_pattern(pattern)
                if results:
                    all_results.extend(results)
                    logger.info(f"Encontrados {len(results)} livros para o padrão '{pattern}'")

            if not all_results:
                logger.info("Nenhum resultado encontrado na API externa")
                return []

            # Filtra livros já existentes
            filtered_books = self._filter_existing_books(all_results, user)
            logger.info(f"Livros filtrados (removendo existentes): {len(filtered_books)}")

            # Limita o número de resultados
            final_results = filtered_books[:limit]
            logger.info(f"Recomendações externas finais: {len(final_results)}")

            # Armazena em cache para reduzir chamadas repetidas
            self._results_cache[user_cache_key] = filtered_books

            # Garante formato consistente
            self.last_external_recommendations = final_results

            return final_results

        except Exception as e:
            logger.error(f"Erro ao obter recomendações externas: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _get_user_patterns(self, user: User) -> List[str]:
        """Extrai padrões de interesse do usuário"""
        patterns = set()
        weights = {'favorito': 3, 'lido': 2, 'lendo': 2, 'vou_ler': 1}

        try:
            if not user:
                # Se não há usuário, retorna categorias padrão
                return ['fiction', 'fantasy', 'thriller', 'romance'][:self.max_patterns]

            # Consulta otimizada para prateleiras do usuário
            shelves = UserBookShelf.objects.filter(
                user=user,
                shelf_type__in=weights.keys()
            ).select_related('book').order_by('-added_at')[:50]  # Limita para evitar sobrecarga

            # Conjunto de categorias já processadas para evitar duplicatas
            processed_categories = set()

            for shelf in shelves:
                try:
                    weight = weights.get(shelf.shelf_type, 0)
                    book = shelf.book

                    # Verifica se o objeto book é válido
                    if not book or not hasattr(book, 'id'):
                        continue

                    # Processamento de categorias
                    if hasattr(book, 'categoria') and book.categoria:
                        # Normaliza o formato da categoria para processamento
                        categoria_str = book.categoria
                        if categoria_str.startswith('[') and categoria_str.endswith(']'):
                            # Remove caracteres de lista
                            categories = categoria_str.strip("[]'").replace("'", "").split(',')
                        else:
                            categories = categoria_str.split(',')

                        # Processa cada categoria
                        for categoria in categories:
                            categoria_limpa = categoria.strip().lower()
                            if categoria_limpa and categoria_limpa not in processed_categories:
                                normalized = self.category_mapping.normalize_category(categoria_limpa)
                                if normalized:
                                    patterns.add(normalized)
                                    processed_categories.add(categoria_limpa)

                    # Processamento de gêneros
                    if hasattr(book, 'genero') and book.genero:
                        genero_limpo = book.genero.strip().lower()
                        if genero_limpo and genero_limpo not in processed_categories:
                            normalized = self.category_mapping.normalize_category(genero_limpo)
                            if normalized:
                                patterns.add(normalized)
                                processed_categories.add(genero_limpo)

                    # Adiciona autor (apenas dos favoritos/lendo)
                    if shelf.shelf_type in ['favorito', 'lendo'] and hasattr(book, 'autor') and book.autor:
                        author_parts = book.autor.split(',')
                        if author_parts:
                            author = author_parts[0].strip()
                            if len(author) > 3:  # Evita autores muito curtos
                                patterns.add(f'inauthor:"{author}"')
                except Exception as item_error:
                    logger.warning(f"Erro ao processar livro do usuário: {str(item_error)}")
                    continue

            # Se não encontrou padrões, use categorias populares
            if not patterns:
                patterns.update(['fiction', 'fantasy', 'thriller', 'romance'])

            # Limitamos para reduzir chamadas API
            return list(patterns)[:self.max_patterns]

        except Exception as e:
            logger.error(f"Erro ao extrair padrões do usuário: {str(e)}")
            # Fallback para categorias padrão
            return ['fiction', 'fantasy', 'thriller', 'romance'][:self.max_patterns]

    def _search_with_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """Busca livros usando um padrão específico"""
        try:
            # Verifica se já temos este padrão em cache
            cache_key = f"pattern_search:{pattern}"
            if cache_key in self._results_cache:
                # Usar cache para evitar chamadas API desnecessárias
                return self._results_cache[cache_key]

            # Ajusta query baseado no tipo de padrão
            if pattern.startswith('inauthor:'):
                query = pattern
            else:
                query = f'subject:"{pattern}"'

            # Chama a API
            results = self.client.search_books(
                query=query,
                max_results=self.max_results_per_query
            )

            # Processar resultado da API
            formatted_books = self._process_api_results(results)

            # Armazena em cache
            self._results_cache[cache_key] = formatted_books

            return formatted_books

        except Exception as e:
            logger.error(f"Erro na busca com padrão '{pattern}': {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    def _process_api_results(self, results: Union[Dict, List]) -> List[Dict]:
        """Processa resultados da API em um formato consistente"""
        try:
            # Verificar o formato da resposta
            if isinstance(results, dict):
                # Novo formato da API centralizada
                if 'books' in results:
                    # Extrair lista de livros do dicionário de resposta
                    books_list = results.get('books', [])
                    # Converter para formato esperado pelo restante do código
                    formatted_books = []
                    for book in books_list:
                        try:
                            # Verifica se já está no formato volumeInfo
                            if 'volumeInfo' in book:
                                formatted_books.append(book)
                            else:
                                # Converter para formato compatível com antigo Google Books API
                                formatted_book = {
                                    'id': book.get('id', ''),
                                    'volumeInfo': {
                                        'title': book.get('title', ''),
                                        'authors': book.get('authors', []) if isinstance(book.get('authors', []), list) else [book.get('authors', '')],
                                        'description': book.get('description', ''),
                                        'categories': book.get('categories', []) if isinstance(book.get('categories', []), list) else [book.get('categories', '')],
                                        'publisher': book.get('publisher', ''),
                                        'publishedDate': book.get('published_date', ''),
                                        'pageCount': book.get('page_count', 0),
                                        'language': book.get('language', ''),
                                        'imageLinks': {
                                            'thumbnail': book.get('thumbnail', '')
                                        }
                                    }
                                }
                                # Verifica e corrige campos obrigatórios
                                if not formatted_book['volumeInfo']['title']:
                                    formatted_book['volumeInfo']['title'] = 'Título desconhecido'

                                formatted_books.append(formatted_book)
                        except Exception as book_error:
                            logger.warning(f"Erro ao processar livro individual: {str(book_error)}")
                            continue

                    return formatted_books
                else:
                    # Formato inesperado, retornar vazio
                    logger.warning("Resposta da API não contém campo 'books'")
                    return []
            elif isinstance(results, list):
                # Formato de lista direta (antigo)
                # Verificar e corrigir cada item da lista
                formatted_books = []
                for book in results:
                    try:
                        if isinstance(book, dict):
                            # Verifica se tem volumeInfo e campos essenciais
                            if 'volumeInfo' in book:
                                if not book['volumeInfo'].get('title'):
                                    book['volumeInfo']['title'] = 'Título desconhecido'
                                formatted_books.append(book)
                        else:
                            logger.warning(f"Item da lista de resultados não é um dicionário: {type(book)}")
                    except Exception as book_error:
                        logger.warning(f"Erro ao processar item da lista: {str(book_error)}")
                        continue

                return formatted_books
            else:
                # Tipo desconhecido, retornar vazio
                logger.error(f"Formato de resposta inesperado: {type(results)}")
                return []

        except Exception as e:
            logger.error(f"Erro ao processar resultados da API: {str(e)}")
            return []

    def _filter_existing_books(self, external_books: List[Dict], user: User) -> List[Dict]:
        """Filtra livros que já existem nas prateleiras do usuário"""
        # Obtém títulos e autores dos livros do usuário
        user_books = set()

        try:
            if user:
                user_shelves = UserBookShelf.objects.filter(user=user).select_related('book')
            else:
                user_shelves = UserBookShelf.objects.none()

            for shelf in user_shelves:
                try:
                    if hasattr(shelf, 'book') and shelf.book:
                        title = shelf.book.titulo.lower() if hasattr(shelf.book, 'titulo') and shelf.book.titulo else ''
                        author = shelf.book.autor.lower() if hasattr(shelf.book, 'autor') and shelf.book.autor else ''

                        if title or author:
                            user_books.add((title, author))
                except Exception as book_error:
                    logger.warning(f"Erro ao processar livro do usuário para filtragem: {str(book_error)}")
                    continue
        except Exception as e:
            logger.error(f"Erro ao obter livros do usuário: {str(e)}")

        # Filtra livros únicos
        filtered = []
        seen = set()

        for book in external_books:
            try:
                # Obter informações do livro com tratamento para diferentes formatos
                if isinstance(book, dict):
                    if 'volumeInfo' in book:
                        info = book['volumeInfo']
                    else:
                        # Assumir que o próprio livro tem os campos
                        info = book

                    # Extrair título com tratamento de tipo
                    title = ''
                    if 'title' in info and info['title']:
                        title = str(info['title']).lower()

                    # Extrair autor com tratamento de tipo
                    author = ''
                    if 'authors' in info and info['authors']:
                        if isinstance(info['authors'], list):
                            author = ', '.join(str(a) for a in info['authors']).lower()
                        else:
                            author = str(info['authors']).lower()

                    # Validação mínima
                    if not title:
                        continue

                    # Cria chave única para o livro
                    key = f"{title}|{author}"

                    # Verifica se é único e não está nas prateleiras
                    if key not in seen and (title, author) not in user_books:
                        seen.add(key)
                        filtered.append(book)
            except Exception as e:
                logger.warning(f"Erro ao processar livro para filtragem: {str(e)}")
                continue

        return filtered

    def _convert_to_temp_books(self, external_books: List[Dict]) -> List[Book]:
        """Converte livros da API externa em objetos Book temporários"""
        temp_books = []

        for idx, book in enumerate(external_books):
            try:
                # Verifica se tem a estrutura necessária
                if not isinstance(book, dict) or 'volumeInfo' not in book:
                    logger.warning(f"Livro externo sem estrutura volumeInfo: {book}")
                    continue

                info = book['volumeInfo']

                # Cria objeto Book temporário
                temp_book = Book(
                    # Usa ID negativo para livros temporários
                    id=-(idx + 1),
                    # Dados básicos do livro
                    titulo=info.get('title', 'Título não disponível'),
                    autor=', '.join(info.get('authors', ['Autor desconhecido'])) if isinstance(info.get('authors', []), list) else str(info.get('authors', 'Autor desconhecido')),
                    editora=info.get('publisher', ''),
                    descricao=info.get('description', ''),
                    paginas=info.get('pageCount', 0),
                    idioma=info.get('language', 'pt'),
                    isbn=info.get('industryIdentifiers', [{}])[0].get('identifier', '') if isinstance(info.get('industryIdentifiers', []), list) and info.get('industryIdentifiers', []) else '',
                    categoria=', '.join(info.get('categories', [])) if isinstance(info.get('categories', []), list) else str(info.get('categories', '')),

                    # Campos para livros externos
                    capa_url=info.get('imageLinks', {}).get('thumbnail', ''),
                    external_id=book.get('id', ''),
                    is_temporary=True,
                    external_data=json.dumps(book),
                    origem='Google Books'
                )

                # Define data de publicação se disponível
                pub_date = info.get('publishedDate', '')
                if pub_date:
                    try:
                        if '-' in pub_date:
                            # Formato YYYY-MM-DD ou YYYY-MM
                            temp_book.data_publicacao = timezone.datetime.strptime(
                                pub_date.split('-')[0],
                                '%Y'
                            ).date()
                        elif len(pub_date) >= 4:
                            # Apenas o ano
                            temp_book.data_publicacao = timezone.datetime.strptime(
                                pub_date[:4],
                                '%Y'
                            ).date()
                    except ValueError:
                        pass

                temp_books.append(temp_book)

            except Exception as e:
                logger.error(f"Erro ao converter livro externo: {str(e)}")
                continue

        return temp_books