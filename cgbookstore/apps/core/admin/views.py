# cgbookstore/apps/core/admin/views.py

'''
"""
Views personalizadas para o módulo administrativo.

Este módulo contém funções de view utilizadas pelo site administrativo
e não associadas diretamente a uma classe de administração.
"""

import logging
import json
import csv
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Sum, Q
from django.contrib.auth.decorators import user_passes_test

from ..models import User, Book, UserBookShelf
from ..models.home_content import (
    DefaultShelfType, HomeSection, BookShelfSection, BookShelfItem
)

logger = logging.getLogger(__name__)


def is_staff_or_superuser(user):
    """
    Verifica se o usuário é staff ou superusuário.

    Args:
        user: Objeto de usuário

    Returns:
        bool: True se o usuário tem permissão
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_staff_or_superuser)
def dashboard_view(request):
    """
    View para o dashboard administrativo principal.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de dashboard renderizada
    """
    # Estatísticas de usuários
    users_count = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()

    last_week = timezone.now() - timedelta(days=7)
    new_users = User.objects.filter(date_joined__gte=last_week).count()

    # Estatísticas de livros
    books_count = Book.objects.count()
    featured_books = Book.objects.filter(e_destaque=True).count()
    new_releases = Book.objects.filter(e_lancamento=True).count()

    # Estatísticas de prateleiras
    shelf_types_count = DefaultShelfType.objects.filter(ativo=True).count()
    shelves_count = BookShelfSection.objects.count()

    # Estatísticas de interações
    interactions_count = UserBookShelf.objects.count()

    # Gráfico de atividades recentes (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_interactions = (
        UserBookShelf.objects
        .filter(added_at__gte=thirty_days_ago)
        .extra({'date': "date(added_at)"})
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    interaction_chart_data = {
        'labels': [data['date'] for data in daily_interactions],
        'counts': [data['count'] for data in daily_interactions]
    }

    # Top livros
    top_books = (
        Book.objects
        .filter(userbookshelf__isnull=False)
        .annotate(interaction_count=Count('userbookshelf'))
        .order_by('-interaction_count')[:5]
    )

    context = {
        'title': 'Dashboard Administrativo',
        'users_count': users_count,
        'active_users': active_users,
        'staff_users': staff_users,
        'new_users': new_users,
        'books_count': books_count,
        'featured_books': featured_books,
        'new_releases': new_releases,
        'shelf_types_count': shelf_types_count,
        'shelves_count': shelves_count,
        'interactions_count': interactions_count,
        'interaction_chart_data': interaction_chart_data,
        'top_books': top_books
    }

    return render(request, 'admin/dashboard.html', context)


@user_passes_test(is_staff_or_superuser)
def export_model_data(request, model_name):
    """
    Exporta dados de um modelo específico para CSV.

    Args:
        request: Requisição HTTP
        model_name: Nome do modelo a ser exportado

    Returns:
        HttpResponse: Arquivo CSV para download ou mensagem de erro
    """
    # Mapeia nomes de modelos para as classes reais
    models_map = {
        'user': User,
        'book': Book,
        'userbookshelf': UserBookShelf,
        'defaultshelftype': DefaultShelfType,
        'homesection': HomeSection,
        'bookshelfsection': BookShelfSection
    }

    # Verifica se o modelo solicitado existe
    if model_name not in models_map:
        messages.error(request, f"Modelo '{model_name}' não encontrado.")
        return redirect('admin:index')

    model = models_map[model_name]

    try:
        # Prepara o CSV
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="{model_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        # Cria um escritor CSV
        writer = csv.writer(response)

        # Obtém os campos do modelo
        fields = [field.name for field in model._meta.fields]
        writer.writerow(fields)  # Cabeçalho

        # Escreve os dados
        for obj in model.objects.all():
            row = []
            for field in fields:
                value = getattr(obj, field)
                row.append(str(value))
            writer.writerow(row)

        logger.info(f"Exportação de dados de {model_name} realizada com sucesso")
        return response

    except Exception as e:
        logger.error(f"Erro ao exportar dados de {model_name}: {str(e)}")
        messages.error(request, f"Erro ao exportar dados: {str(e)}")
        return redirect('admin:index')


@user_passes_test(is_staff_or_superuser)
def book_statistics_view(request):
    """
    View para exibir estatísticas detalhadas sobre livros.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de estatísticas renderizada
    """
    # Estatísticas gerais
    total_books = Book.objects.count()

    # Contagem por categorias
    categories = (
        Book.objects
        .values('categoria')
        .annotate(count=Count('categoria'))
        .order_by('-count')
    )

    # Preço médio por categoria
    avg_price_by_category = (
        Book.objects
        .values('categoria')
        .annotate(avg_price=Avg('preco'))
        .order_by('categoria')
    )

    # Total de livros por editora
    publishers = (
        Book.objects
        .values('editora')
        .annotate(count=Count('editora'))
        .order_by('-count')
    )

    # Livros mais acessados
    most_accessed = (
        Book.objects
        .order_by('-quantidade_acessos')[:10]
    )

    # Livros mais vendidos
    bestsellers = (
        Book.objects
        .order_by('-quantidade_vendida')[:10]
    )

    # Dados para gráficos
    category_chart_data = {
        'labels': [c['categoria'] for c in categories if c['categoria']],
        'counts': [c['count'] for c in categories if c['categoria']]
    }

    price_chart_data = {
        'labels': [c['categoria'] for c in avg_price_by_category if c['categoria']],
        'values': [float(c['avg_price']) if c['avg_price'] else 0 for c in avg_price_by_category if c['categoria']]
    }

    publisher_chart_data = {
        'labels': [p['editora'] for p in publishers[:10] if p['editora']],
        'counts': [p['count'] for p in publishers[:10] if p['editora']]
    }

    context = {
        'title': 'Estatísticas de Livros',
        'total_books': total_books,
        'categories': categories,
        'publishers': publishers,
        'most_accessed': most_accessed,
        'bestsellers': bestsellers,
        'category_chart_data': category_chart_data,
        'price_chart_data': price_chart_data,
        'publisher_chart_data': publisher_chart_data
    }

    return render(request, 'admin/book_statistics.html', context)


@user_passes_test(is_staff_or_superuser)
def user_activity_view(request):
    """
    View para exibir atividades e estatísticas de usuários.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de atividades de usuários renderizada
    """
    # Estatísticas gerais
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    # Usuários por data de registro
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()

    # Usuários por data de registro (últimos 30 dias)
    daily_registrations = (
        User.objects
        .filter(date_joined__gte=thirty_days_ago)
        .extra({'date': "date(date_joined)"})
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Estatísticas de interações
    user_interactions = (
        User.objects
        .annotate(shelf_count=Count('userbookshelf'))
        .order_by('-shelf_count')[:20]
    )

    # Usuários mais ativos (com mais interações)
    most_active_users = [
        {
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'interactions': user.shelf_count,
            'joined': user.date_joined
        }
        for user in user_interactions
    ]

    # Dados para gráficos
    registration_chart_data = {
        'labels': [str(reg['date']) for reg in daily_registrations],
        'counts': [reg['count'] for reg in daily_registrations]
    }

    context = {
        'title': 'Atividade de Usuários',
        'total_users': total_users,
        'active_users': active_users,
        'new_users_30d': new_users_30d,
        'most_active_users': most_active_users,
        'registration_chart_data': registration_chart_data
    }

    return render(request, 'admin/user_activity.html', context)


@user_passes_test(is_staff_or_superuser)
def shelf_management_statistics(request):
    """
    View para estatísticas e gerenciamento de prateleiras.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de estatísticas de prateleiras renderizada
    """
    # Estatísticas gerais
    total_shelves = BookShelfSection.objects.count()
    shelf_types = DefaultShelfType.objects.filter(ativo=True).count()

    # Livros por prateleira
    shelf_book_counts = (
        BookShelfSection.objects
        .annotate(book_count=Count('bookshelfitem'))
        .order_by('-book_count')
    )

    # Top prateleiras por número de livros
    top_shelves = [
        {
            'title': shelf.section.titulo if shelf.section else 'Sem título',
            'type': shelf.shelf_type.nome if shelf.shelf_type else 'Tipo padrão',
            'book_count': shelf.book_count
        }
        for shelf in shelf_book_counts[:10]
    ]

    # Prateleiras vazias
    empty_shelves = [
        {
            'title': shelf.section.titulo if shelf.section else 'Sem título',
            'type': shelf.shelf_type.nome if shelf.shelf_type else 'Tipo padrão',
            'id': shelf.id
        }
        for shelf in shelf_book_counts.filter(book_count=0)
    ]

    # Livros por tipo de prateleira
    shelf_type_stats = []
    for shelf_type in DefaultShelfType.objects.filter(ativo=True):
        book_count = BookShelfItem.objects.filter(shelf__shelf_type=shelf_type).count()
        shelf_type_stats.append({
            'name': shelf_type.nome,
            'identifier': shelf_type.identificador,
            'book_count': book_count
        })

    context = {
        'title': 'Estatísticas de Prateleiras',
        'total_shelves': total_shelves,
        'shelf_types': shelf_types,
        'top_shelves': top_shelves,
        'empty_shelves': empty_shelves,
        'shelf_type_stats': shelf_type_stats
    }

    return render(request, 'admin/shelf_statistics.html', context)


@user_passes_test(is_staff_or_superuser)
def cache_management_view(request):
    """
    View para gerenciamento de cache do sistema.

    Permite visualizar e limpar caches específicos ou todos.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de gerenciamento de cache renderizada
    """
    # Se a solicitação for para limpar o cache
    if request.method == 'POST':
        cache_key = request.POST.get('cache_key')

        if cache_key == 'all':
            # Limpa todo o cache
            cache.clear()
            messages.success(request, "Todo o cache foi limpo com sucesso.")
        elif cache_key:
            # Limpa um cache específico
            cache.delete(cache_key)
            messages.success(request, f"Cache '{cache_key}' limpo com sucesso.")

        # CORREÇÃO: Verifica o referer para decidir o redirecionamento correto
        referer = request.META.get('HTTP_REFERER', '')
        if 'diagnostics' in referer:
            return redirect('admin:diagnostics_dashboard')
        else:
            # Para outras páginas, redireciona de volta para onde veio ou para admin index
            return redirect('admin:index')

    # Lista de caches conhecidos
    known_caches = [
        {'key': 'book_category_config', 'description': 'Configurações de categorias de livros'},
        {'key': 'homepage_shelves', 'description': 'Prateleiras da página inicial'},
        {'key': 'recommended_books', 'description': 'Livros recomendados'},
        {'key': 'user_activity_stats', 'description': 'Estatísticas de atividade de usuários'},
        {'key': 'book_statistics', 'description': 'Estatísticas de livros'}
    ]

    # Verifica quais caches estão ativos
    for cache_info in known_caches:
        cache_info['active'] = cache.get(cache_info['key']) is not None

    context = {
        'title': 'Gerenciamento de Cache',
        'known_caches': known_caches
    }

    return render(request, 'admin/cache_management.html', context)


@user_passes_test(is_staff_or_superuser)
def admin_log_view(request):
    """
    View para visualização de logs administrativos.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página de logs renderizada
    """
    from django.contrib.admin.models import LogEntry

    # Limite de registros
    limit = int(request.GET.get('limit', 100))

    # Filtros
    action_filter = request.GET.get('action')
    user_filter = request.GET.get('user')
    model_filter = request.GET.get('model')

    # Busca registros de log
    logs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')

    # Aplica filtros
    if action_filter:
        logs = logs.filter(action_flag=action_filter)

    if user_filter:
        logs = logs.filter(user__username=user_filter)

    if model_filter:
        logs = logs.filter(content_type__model=model_filter)

    # Limita o número de registros
    logs = logs[:limit]

    # Obtém usuários e modelos para filtros
    users = User.objects.filter(
        pk__in=LogEntry.objects.values_list('user_id', flat=True).distinct()
    ).order_by('username')

    models = LogEntry.objects.values_list(
        'content_type__model', flat=True
    ).distinct().order_by('content_type__model')

    context = {
        'title': 'Logs Administrativos',
        'logs': logs,
        'users': users,
        'models': models,
        'limit': limit,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'model_filter': model_filter
    }

    return render(request, 'admin/admin_logs.html', context)


# Correção apenas para a função visual_shelf_manager
@user_passes_test(is_staff_or_superuser)
def visual_shelf_manager(request):
    """
    View para gerenciador visual de prateleiras.

    Permite arrastar e soltar livros entre prateleiras utilizando interface AJAX.
    Gerencia adição, remoção e reordenação de livros de forma visual.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Página do gerenciador visual renderizada ou
                     JsonResponse para requisições AJAX
    """

    # Processa requisições AJAX (POST)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Decodifica o corpo da requisição como JSON
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'add':
                # Adiciona um livro a uma prateleira
                book_id = data.get('book_id')
                shelf_id = data.get('shelf_id')

                # Verifica se os dados necessários estão presentes
                if not all([book_id, shelf_id]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parâmetros incompletos'
                    })

                # Busca os objetos
                try:
                    book = Book.objects.get(id=book_id)
                    shelf = BookShelfSection.objects.get(id=shelf_id)
                except (Book.DoesNotExist, BookShelfSection.DoesNotExist):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Livro ou prateleira não encontrado'
                    })

                # Verifica se o livro já está na prateleira
                if BookShelfItem.objects.filter(shelf=shelf, livro=book).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Este livro já está nesta prateleira'
                    })

                # Verifica quantos livros já estão na prateleira
                current_count = BookShelfItem.objects.filter(shelf=shelf).count()

                # Cria o novo item na prateleira com a ordem sendo a última posição
                next_position = current_count
                BookShelfItem.objects.create(
                    shelf=shelf,
                    livro=book,
                    ordem=next_position
                )

                # Avisa se ultrapassou o limite, mas permite adicionar mesmo assim
                warning = None
                if current_count >= shelf.max_livros:
                    warning = f"A prateleira ultrapassou o limite de {shelf.max_livros} livros."

                return JsonResponse({
                    'status': 'success',
                    'message': 'Livro adicionado com sucesso',
                    'warning': warning
                })

            elif action == 'remove':
                # Remove um livro de uma prateleira
                book_id = data.get('book_id')
                shelf_id = data.get('shelf_id')

                # Verifica se os dados necessários estão presentes
                if not all([book_id, shelf_id]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parâmetros incompletos'
                    })

                # Tenta excluir o item
                try:
                    BookShelfItem.objects.filter(
                        shelf_id=shelf_id,
                        livro_id=book_id
                    ).delete()

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Livro removido com sucesso'
                    })

                except Exception as e:
                    logger.error(f"Erro ao remover livro: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Erro ao remover livro da prateleira'
                    })

            elif action == 'reorder':
                # Reordena livros dentro de uma prateleira
                shelf_id = data.get('shelf_id')
                order = data.get('order')  # Lista de IDs de livros na nova ordem

                # Verifica se os dados necessários estão presentes
                if not all([shelf_id, order]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Parâmetros incompletos'
                    })

                # Processa a reordenação
                try:
                    for index, book_id in enumerate(order):
                        BookShelfItem.objects.filter(
                            shelf_id=shelf_id,
                            livro_id=book_id
                        ).update(ordem=index)

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Ordem atualizada com sucesso'
                    })

                except Exception as e:
                    logger.error(f"Erro ao reordenar prateleira: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Erro ao reordenar livros'
                    })

            # Ação desconhecida
            return JsonResponse({
                'status': 'error',
                'message': 'Ação desconhecida'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Formato JSON inválido'
            })
        except Exception as e:
            logger.error(f"Erro no gerenciador visual: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Erro interno do servidor'
            })

    # Renderiza a página para requisições GET
    try:
        # Busca apenas as prateleiras ativas para melhorar performance
        book_shelves = BookShelfSection.objects.select_related(
            'section', 'shelf_type'
        ).filter(
            section__ativo=True
        )

        # Filtro por título ou tipo
        q = request.GET.get('q', '')
        if q:
            from django.db.models import Q
            book_shelves = book_shelves.filter(
                Q(section__titulo__icontains=q) |
                Q(shelf_type__nome__icontains=q)
            )

        # Para cada prateleira, buscar seus itens
        for book_shelf in book_shelves:
            book_shelf.get_shelf_type_name = (
                book_shelf.shelf_type.nome if book_shelf.shelf_type
                else 'Não definido'
            )

            # Otimização: buscar direto os items ordenados com seus livros
            book_shelf.sorted_items = BookShelfItem.objects.filter(
                shelf=book_shelf
            ).select_related(
                'livro'
            ).order_by('ordem')

        # Busca livros não associados a prateleiras ou filtrados pela busca
        book_q = request.GET.get('book_q', '')

        # Limitar o número de livros para melhorar performance
        limit = 50

        if book_q:
            # Busca livros pelo filtro
            from django.db.models import Q
            unassigned_books = Book.objects.filter(
                Q(titulo__icontains=book_q) |
                Q(autor__icontains=book_q) |
                Q(isbn__icontains=book_q)
            )[:limit]
        else:
            # Busca livros que não estão em nenhuma prateleira
            # Use uma subconsulta mais eficiente
            used_book_ids = BookShelfItem.objects.values_list('livro_id', flat=True)
            unassigned_books = Book.objects.exclude(id__in=used_book_ids)[:limit]

        context = {
            'title': 'Gerenciador Visual de Prateleiras',
            'book_shelves': book_shelves,
            'unassigned_books': unassigned_books,
            'q': q,
            'book_q': book_q,
        }

        return render(request, 'admin/visual_shelf_manager.html', context)
    except Exception as e:
        logger.error(f"Erro ao renderizar gerenciador visual: {str(e)}")
        messages.error(request, f"Erro ao carregar gerenciador visual: {str(e)}")
        return redirect('admin:index')


@user_passes_test(is_staff_or_superuser)
def quick_shelf_creation(request):
    """
    View para criação rápida de prateleiras.

    Permite a criação de uma nova prateleira de forma simplificada,
    diretamente da interface administrativa.

    Args:
        request: Requisição HTTP

    Returns:
        HttpResponse: Formulário de criação ou redirecionamento após o sucesso
    """
    if request.method == 'POST':
        # Processa o formulário de criação
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao', '')
        shelf_type_id = request.POST.get('shelf_type')
        max_livros = request.POST.get('max_livros', 15)

        # Validação básica
        if not titulo:
            messages.error(request, 'O título da prateleira é obrigatório.')
            return redirect('admin:quick-shelf-creation')

        if not shelf_type_id:
            messages.error(request, 'O tipo de prateleira é obrigatório.')
            return redirect('admin:quick-shelf-creation')

        try:
            # Converte para inteiro
            max_livros = int(max_livros)
            if max_livros <= 0:
                max_livros = 15  # Valor padrão
        except (ValueError, TypeError):
            max_livros = 15

        try:
            # Busca o tipo de prateleira
            shelf_type = DefaultShelfType.objects.get(id=shelf_type_id)

            # Cria a seção principal
            home_section = HomeSection.objects.create(
                titulo=titulo,
                descricao=descricao,
                ativo=True
            )

            # Cria a prateleira
            shelf = BookShelfSection.objects.create(
                section=home_section,
                shelf_type=shelf_type,
                max_livros=max_livros,
                ativo=True
            )

            messages.success(request, f'Prateleira "{titulo}" criada com sucesso!')

            # Redireciona para o gerenciador visual com a nova prateleira
            return redirect('admin:visual-shelf-manager')

        except DefaultShelfType.DoesNotExist:
            messages.error(request, 'Tipo de prateleira não encontrado.')
            return redirect('admin:quick-shelf-creation')
        except Exception as e:
            logger.error(f"Erro ao criar prateleira: {str(e)}")
            messages.error(request, f'Erro ao criar prateleira: {str(e)}')
            return redirect('admin:quick-shelf-creation')

    # Carrega o formulário (GET)
    shelf_types = DefaultShelfType.objects.filter(ativo=True)

    context = {
        'title': 'Criação Rápida de Prateleira',
        'shelf_types': shelf_types
    }

    return render(request, 'admin/quick_shelf_creation.html', context)

    '''