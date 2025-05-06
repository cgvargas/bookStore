# cgbookstore/apps/core/admin/mixins.py
"""
Mixins reutilizáveis para componentes administrativos.

Este módulo fornece classes mixins que podem ser utilizadas para adicionar
funcionalidades comuns a múltiplas classes de administração.
"""

import logging
from django.core.cache import cache
from django.db.models import Count

logger = logging.getLogger(__name__)


class LoggingAdminMixin:
    """
    Mixin para adicionar logs detalhados de operações administrativas.

    Estende os métodos padrão de log do ModelAdmin para adicionar
    informações mais detalhadas e consistentes sobre as operações.
    """

    def log_addition(self, request, object, message):
        """
        Registra a adição de um novo objeto com detalhes.

        Args:
            request: Requisição HTTP
            object: Objeto adicionado
            message: Mensagem de log
        """
        super().log_addition(request, object, message)

        # Registro adicional com mais detalhes
        logger.info(
            f"[ADMIN] Novo {object._meta.model_name} criado (ID: {object.pk}) "
            f"por {request.user.username} ({request.user.email})"
        )

    def log_change(self, request, object, message):
        """
        Registra a alteração de um objeto com detalhes.

        Args:
            request: Requisição HTTP
            object: Objeto alterado
            message: Mensagem de log
        """
        super().log_change(request, object, message)

        # Registro adicional com mais detalhes
        logger.info(
            f"[ADMIN] {object._meta.model_name} modificado (ID: {object.pk}) "
            f"por {request.user.username} ({request.user.email})"
        )

    def log_deletion(self, request, object, object_repr):
        """
        Registra a exclusão de um objeto com detalhes.

        Args:
            request: Requisição HTTP
            object: Objeto excluído
            object_repr: Representação textual do objeto
        """
        super().log_deletion(request, object, object_repr)

        # Registro adicional com mais detalhes
        logger.warning(
            f"[ADMIN] {object._meta.model_name} excluído (ID: {object.pk}, Repr: {object_repr}) "
            f"por {request.user.username} ({request.user.email})"
        )


class CachedCountersMixin:
    """
    Mixin para implementar cache em contadores comuns para melhorar a performance.
    """

    @staticmethod
    def get_cache_key(model_name, obj_id, counter_name):
        """
        Gera uma chave para o cache.

        Args:
            model_name: Nome do modelo
            obj_id: ID do objeto
            counter_name: Nome do contador

        Returns:
            str: Chave para o cache
        """
        return f"{model_name}_{obj_id}_{counter_name}"

    def get_cached_count(self, obj, counter_name, queryset_func, timeout=3600):
        """
        Obtém um contador em cache ou calcula se não estiver disponível.

        Args:
            obj: Objeto relacionado
            counter_name: Nome do contador
            queryset_func: Função que retorna o queryset para cálculo
            timeout: Tempo de expiração do cache em segundos

        Returns:
            int: Valor do contador
        """
        model_name = obj._meta.model_name
        obj_id = obj.pk
        cache_key = self.get_cache_key(model_name, obj_id, counter_name)

        # Tenta obter do cache
        count = cache.get(cache_key)

        # Se não estiver em cache, calcula e armazena
        if count is None:
            count = queryset_func(obj).count()
            cache.set(cache_key, count, timeout)

        return count


class BookShelfManagerMixin:
    """
    Mixin com métodos compartilhados para gerenciamento de prateleiras.
    """

    def get_filtered_books(self, request, shelf_type):
        """
        Obtém livros filtrados para um tipo de prateleira.

        Args:
            request: Requisição HTTP
            shelf_type: Objeto DefaultShelfType

        Returns:
            QuerySet: Livros filtrados conforme tipo de prateleira
        """
        from ..models.book import Book

        # Inicia com todos os livros
        books = Book.objects.all()

        # Aplica filtro conforme configuração
        if shelf_type.filtro_campo and shelf_type.filtro_valor:
            filter_kwargs = {}

            # Converte valor do filtro para o tipo adequado
            if shelf_type.filtro_valor.lower() in ['true', 'yes', 'sim', '1']:
                filter_value = True
            elif shelf_type.filtro_valor.lower() in ['false', 'no', 'não', '0']:
                filter_value = False
            elif shelf_type.filtro_valor.isdigit():
                filter_value = int(shelf_type.filtro_valor)
            else:
                filter_value = shelf_type.filtro_valor

            # Filtra baseado no campo e valor
            if shelf_type.filtro_campo == 'tipo_shelf_especial':
                filter_kwargs[shelf_type.filtro_campo] = shelf_type.identificador
            else:
                filter_kwargs[shelf_type.filtro_campo] = filter_value

            books = books.filter(**filter_kwargs)

        return books

    def get_shelf_statistics(self, request, shelf_type=None):
        """
        Obtém estatísticas de prateleiras.

        Args:
            request: Requisição HTTP
            shelf_type: Objeto DefaultShelfType opcional

        Returns:
            dict: Estatísticas sobre prateleiras e livros
        """
        from ..models.home_content import BookShelfSection, BookShelfItem
        from ..models.book import Book

        stats = {
            'total_shelves': 0,
            'total_books': 0,
            'active_shelves': 0,
            'empty_shelves': 0,
            'most_popular_book': None,
            'last_updated': None
        }

        # Filtra por tipo específico se solicitado
        if shelf_type:
            sections = BookShelfSection.objects.filter(shelf_type=shelf_type)
        else:
            sections = BookShelfSection.objects.all()

        sections = sections.select_related('section', 'shelf_type')
        stats['total_shelves'] = sections.count()
        stats['active_shelves'] = sections.filter(section__ativo=True).count()

        # Contagem de prateleiras vazias
        empty_shelves = []
        for section in sections:
            if not BookShelfItem.objects.filter(shelf=section).exists():
                empty_shelves.append(section)
        stats['empty_shelves'] = len(empty_shelves)

        # Total de livros em prateleiras
        stats['total_books'] = BookShelfItem.objects.count()

        # Livro mais popular (presente em mais prateleiras)
        most_popular = Book.objects.annotate(
            shelf_count=Count('bookshelfitem')
        ).order_by('-shelf_count').first()

        if most_popular and most_popular.shelf_count > 0:
            stats['most_popular_book'] = {
                'id': most_popular.id,
                'titulo': most_popular.titulo,
                'autor': most_popular.autor,
                'shelf_count': most_popular.shelf_count
            }

        # Data da última atualização
        last_item = BookShelfItem.objects.order_by('-updated_at').first()
        if last_item:
            stats['last_updated'] = last_item.updated_at

        return stats


class PermissionControlledAdmin:
    """
    Mixin para controle granular de permissões administrativas.
    """

    def has_export_permission(self, request):
        """
        Verifica se o usuário pode exportar dados.

        Args:
            request: Requisição HTTP

        Returns:
            bool: True se o usuário tem permissão
        """
        return request.user.has_perm('core.export_data')

    def has_import_permission(self, request):
        """
        Verifica se o usuário pode importar dados.

        Args:
            request: Requisição HTTP

        Returns:
            bool: True se o usuário tem permissão
        """
        return request.user.has_perm('core.import_data')

    def has_advanced_options_permission(self, request):
        """
        Verifica se o usuário pode acessar opções avançadas.

        Args:
            request: Requisição HTTP

        Returns:
            bool: True se o usuário tem permissão
        """
        return request.user.has_perm('core.advanced_options')


class HelpTextAdminMixin:
    """
    Adiciona textos de ajuda contextual ao admin.
    """

    help_texts = {
        'shelf_management': """
            O gerenciador de prateleiras permite organizar livros para exibição na home.
            1. Selecione um tipo de prateleira no painel esquerdo
            2. Arraste livros do catálogo para a prateleira
            3. Reorganize os livros na ordem desejada
        """,
        'book_category': """
            A configuração de categorias permite definir como os livros são filtrados e exibidos.
            Configure limites, algoritmos de recomendação e opções de exibição.
        """,
        'visual_shelf': """
            O gerenciador visual de prateleiras permite adicionar e reorganizar livros
            em cada prateleira usando uma interface de arrastar e soltar.
        """
    }

    def get_help_text(self, view_name):
        """
        Obtém texto de ajuda para uma view específica.

        Args:
            view_name: Nome da view

        Returns:
            str: Texto de ajuda ou string vazia se não encontrado
        """
        return self.help_texts.get(view_name, '')


class OptimizedQuerysetMixin:
    """
    Mixin para otimizar queries administrativas.
    """

    select_related_fields = []
    prefetch_related_fields = []

    def get_queryset(self, request):
        """
        Retorna um queryset otimizado com select_related e prefetch_related.

        Args:
            request: Requisição HTTP

        Returns:
            QuerySet: Queryset otimizado
        """
        queryset = super().get_queryset(request)

        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        return queryset