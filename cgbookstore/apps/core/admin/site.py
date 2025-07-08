# cgbookstore/apps/core/admin/site.py
"""
Definição do site administrativo personalizado para o projeto CG BookStore.

Este módulo contém a classe DatabaseAdminSite que estende admin.AdminSite
para fornecer funcionalidades personalizadas como geração de schema,
exportação de dados, limpeza de pastas e visualização de dados do banco.
"""

import os
import json
import logging
from datetime import datetime
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.core import management
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from . import views

from ..models.home_content import DefaultShelfType, HomeSection, BookShelfSection, BookShelfItem
from cgbookstore.apps.chatbot_literario import admin_views as chatbot_views

# Configuração de logger para rastreamento de eventos administrativos
logger = logging.getLogger(__name__)


class DatabaseAdminSite(admin.AdminSite):
    """
    Site administrativo personalizado com funcionalidades avançadas.

    Recursos adicionais:
    - Geração de schema de banco de dados
    - Exportação de dados
    - Limpeza de pastas
    - Visualização de dados do banco
    - Configuração de categorias de livros
    - Gerenciador visual de prateleiras
    """
    site_header = 'Administração CG BookStore'
    site_title = 'Portal Administrativo CG BookStore'
    index_title = 'Gerenciamento do Sistema'
    module_name = 'Organizador'

    def generate_schema_view(self, request):
        """
        Gera schema do banco de dados em diretório específico.

        Características:
        - Cria diretório de schemas se não existir
        - Usa comando de gerenciamento para gerar schema
        - Adiciona mensagens de status

        Returns:
            HttpResponse: Resposta com script de retorno ou mensagem de erro
        """
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'database_schemas')

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            management.call_command('generate_tables', output_dir=output_dir)

            messages.success(request, 'Schema do banco de dados gerado com sucesso!')
            logger.info(f'Schema gerado com sucesso em: {output_dir}')
        except Exception as e:
            logger.error(f'Erro ao gerar schema: {str(e)}')
            messages.error(request, f'Erro ao gerar schema: {str(e)}')

        return HttpResponse('<script>window.history.back()</script>')

    def generate_structure_view(self, request):
        """
        Gera estrutura do projeto em arquivo CSV.

        Características:
        - Cria diretório de estrutura se não existir
        - Usa comando de gerenciamento para gerar estrutura
        - Adiciona mensagens de status

        Returns:
            HttpResponse: Resposta com script de retorno ou mensagem de status
        """
        try:
            base_dir = os.path.dirname(settings.BASE_DIR)
            output_dir = os.path.join(base_dir, 'project_structure')

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'project_structure_{current_date}.csv'
            csv_path = os.path.join(output_dir, csv_filename)

            management.call_command('generate_project_structure', output_dir=output_dir)

            if os.path.exists(csv_path):
                messages.success(
                    request,
                    f'Estrutura do projeto gerada com sucesso em: {csv_path}'
                )
            else:
                messages.warning(
                    request,
                    f'Arquivo gerado mas não encontrado no caminho esperado: {csv_path}'
                )

            logger.info(f'Tentando gerar estrutura em: {output_dir}')
            logger.info(f'Arquivo CSV esperado em: {csv_path}')
        except Exception as e:
            logger.error(f'Erro ao gerar estrutura: {str(e)}')
            messages.error(
                request,
                f'Erro ao gerar estrutura do projeto: {str(e)}'
            )
        return HttpResponse('<script>window.history.back()</script>')

    def export_data_json(self, request):
        """
        Exporta todos os dados do banco de dados em formato JSON.

        Características:
        - Coleta dados de todos os modelos registrados
        - Gera arquivo JSON para download
        - Adiciona mensagens de status

        Returns:
            HttpResponse: Arquivo JSON ou mensagem de erro
        """
        data = {}
        try:
            for model, model_admin in self._registry.items():
                model_name = model.__name__
                data[model_name] = list(model.objects.all().values())

            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="database_dump.json"'
            response.write(json.dumps(data, indent=4, ensure_ascii=False))

            messages.success(request, "Dados exportados com sucesso para JSON!")
            return response
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            messages.error(request, f"Erro ao exportar dados: {str(e)}")
            return HttpResponse('<script>window.history.back()</script>')

    def _clear_folder_content(self, folder_path, folder_name):
        """
        Remove recursivamente o conteúdo de uma pasta.

        Características:
        - Remove arquivos e subpastas
        - Registra arquivos removidos e erros

        Args:
            folder_path (str): Caminho da pasta
            folder_name (str): Nome da pasta para logs

        Returns:
            dict: Estatísticas de remoção
        """
        folder_status = {'files_removed': 0, 'errors': []}

        if not os.path.exists(folder_path):
            logger.warning(f'Pasta {folder_name} não encontrada em: {folder_path}')
            return folder_status

        def remove_recursive(path):
            try:
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.chmod(file_path, 0o777)
                            os.unlink(file_path)
                            folder_status['files_removed'] += 1
                            logger.info(f'Arquivo removido: {file_path}')
                        except Exception as e:
                            folder_status['errors'].append(f'Erro ao remover arquivo {file}: {e}')
                            logger.error(f'Erro ao remover arquivo {file}: {e}')

                    for dir_name in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir_name))
                        except Exception as e:
                            folder_status['errors'].append(f'Erro ao remover pasta {dir_name}: {e}')
                            logger.error(f'Erro ao remover pasta {dir_name}: {e}')

            except Exception as e:
                folder_status['errors'].append(f'Erro ao processar {path}: {e}')
                logger.error(f'Erro ao processar {path}: {e}')

        remove_recursive(folder_path)
        return folder_status

    def clear_schema_folder_view(self, request):
        """
        Limpa pasta de schemas do banco de dados.

        Returns:
            HttpResponse: Script de retorno com mensagens de status
        """
        base_dir = os.path.dirname(settings.BASE_DIR)
        schema_dir = os.path.join(base_dir, 'database_schemas')
        status = self._clear_folder_content(schema_dir, 'database_schemas')

        if status['files_removed'] > 0:
            messages.success(request, f"Schema: {status['files_removed']} arquivo(s) removido(s)")
        if status['errors']:
            for error in status['errors']:
                messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def clear_structure_folder_view(self, request):
        """
        Limpa pasta de estrutura do projeto.

        Returns:
            HttpResponse: Script de retorno com mensagens de status
        """
        base_dir = os.path.dirname(settings.BASE_DIR)
        structure_dir = os.path.join(base_dir, 'project_structure')
        status = self._clear_folder_content(structure_dir, 'project_structure')

        if status['files_removed'] > 0:
            messages.success(request, f"Estrutura: {status['files_removed']} arquivo(s) removido(s)")
        if status['errors']:
            for error in status['errors']:
                messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def clear_folders_view(self, request):
        """
        Limpa pastas de schemas e estrutura simultaneamente.

        Returns:
            HttpResponse: Script de retorno com mensagens de status
        """
        base_dir = os.path.dirname(settings.BASE_DIR)
        schema_dir = os.path.join(base_dir, 'database_schemas')
        structure_dir = os.path.join(base_dir, 'project_structure')

        schema_status = self._clear_folder_content(schema_dir, 'database_schemas')
        structure_status = self._clear_folder_content(structure_dir, 'project_structure')

        for name, status in [('Schema', schema_status), ('Estrutura', structure_status)]:
            if status['files_removed'] > 0:
                messages.success(request, f"{name}: {status['files_removed']} arquivo(s) removido(s)")
            if status['errors']:
                for error in status['errors']:
                    messages.error(request, error)

        return HttpResponse('<script>window.history.back()</script>')

    def view_database(self, request):
        """
        Visualiza dados de tabelas do banco de dados.

        Características:
        - Lista todas as tabelas registradas
        - Permite filtro por tabela específica
        - Renderiza visualização de dados

        Returns:
            HttpResponse: Página de visualização de dados
        """
        try:
            # Lista todas as tabelas registradas no admin.
            tables = {model._meta.model_name: model for model in self._registry}

            # Caso um filtro por tabela seja solicitado.
            table_name = request.GET.get('table')
            if table_name:
                model = tables.get(table_name)
                if model:
                    objects = model.objects.all().values()
                    context = {
                        'table_name': table_name,
                        'data': objects,  # Dados retornados como lista
                        'columns': [field.name for field in model._meta.fields]
                    }
                    return render(request, 'admin/database_table_view.html', context)

                messages.error(request, f'Tabela "{table_name}" não encontrada.')
                return HttpResponse('<script>window.history.back()</script>')

            # Renderizar a tela inicial com as tabelas registradas.
            context = {'tables': tables.keys()}
            return render(request, 'admin/database_overview.html', context)

        except Exception as e:
            logger.error(f'Erro ao visualizar banco de dados: {str(e)}')
            messages.error(request, f'Erro ao visualizar banco de dados: {str(e)}')
            return HttpResponse('<script>window.history.back()</script>')

    def book_category_config_view(self, request):
        """
        View para configurar parâmetros das modalidades de livros.

        Permite configurar:
        - Limites de exibição para cada modalidade
        - Configurações de algoritmos de recomendação
        - Opções de filtro e ordenação do catálogo
        """
        from ..models.book import Book
        from ..models import UserBookShelf
        from django.db.models import Count, Avg, Max
        from django.core.cache import cache
        from datetime import timedelta
        import re

        # Carrega configurações existentes ou usa padrões
        try:
            config = getattr(settings, 'BOOK_CATEGORY_CONFIG', {})
        except AttributeError:
            config = {}

        # Valores padrão para as configurações
        default_config = {
            'new_releases_limit': 12,
            'new_releases_days': 90,
            'new_releases_active': True,
            'bestsellers_limit': 12,
            'bestsellers_threshold': 1,
            'bestsellers_active': True,
            'recommended_limit': 12,
            'recommended_algorithm': 'hybrid',
            'recommended_external_ratio': 30,
            'recommended_active': True,
            'catalogue_per_page': 24,
            'catalogue_default_sort': 'title',
            'catalogue_filters': ['category', 'author', 'publisher']
        }

        # Mescla as configurações existentes com os padrões
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        # Processa formulário de submissão
        if request.method == 'POST':
            try:
                # Atualiza valores da configuração com base no formulário
                config['new_releases_limit'] = int(request.POST.get('new_releases_limit', 12))
                config['new_releases_days'] = int(request.POST.get('new_releases_days', 90))
                config['new_releases_active'] = 'new_releases_active' in request.POST

                config['bestsellers_limit'] = int(request.POST.get('bestsellers_limit', 12))
                config['bestsellers_threshold'] = int(request.POST.get('bestsellers_threshold', 1))
                config['bestsellers_active'] = 'bestsellers_active' in request.POST

                config['recommended_limit'] = int(request.POST.get('recommended_limit', 12))
                config['recommended_algorithm'] = request.POST.get('recommended_algorithm', 'hybrid')
                config['recommended_external_ratio'] = int(request.POST.get('recommended_external_ratio', 30))
                config['recommended_active'] = 'recommended_active' in request.POST

                config['catalogue_per_page'] = int(request.POST.get('catalogue_per_page', 24))
                config['catalogue_default_sort'] = request.POST.get('catalogue_default_sort', 'title')

                # Processa os filtros do catálogo (enviados como JSON)
                filters_json = request.POST.get('catalogue_filters_json', '[]')
                try:
                    config['catalogue_filters'] = json.loads(filters_json)
                except json.JSONDecodeError:
                    config['catalogue_filters'] = ['category', 'author', 'publisher']

                # Salva as configurações atualizadas
                cache.set('book_category_config', config, 60 * 60 * 24 * 30)  # Cache por 30 dias

                # Atualiza o arquivo settings_local.py se possível
                try:
                    settings_path = os.path.join(settings.BASE_DIR, 'config', 'settings_local.py')

                    if os.path.exists(settings_path):
                        with open(settings_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Verifica se já existe a configuração
                        if re.search(r'BOOK_CATEGORY_CONFIG\s*=', content):
                            # Substitui configuração existente
                            content = re.sub(
                                r'BOOK_CATEGORY_CONFIG\s*=\s*{[^}]*}',
                                f'BOOK_CATEGORY_CONFIG = {repr(config)}',
                                content
                            )
                        else:
                            # Adiciona nova configuração
                            content += f'\n\n# Configurações de categorias de livros\nBOOK_CATEGORY_CONFIG = {repr(config)}\n'

                        with open(settings_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        messages.success(request, 'Configurações de categorias de livros atualizadas com sucesso!')
                    else:
                        # Se settings_local.py não existir, cria apenas o cache
                        messages.success(request, 'Configurações salvas em cache temporário.')
                except Exception as e:
                    logger.error(f'Erro ao salvar configurações: {str(e)}')
                    messages.warning(
                        request,
                        'Configurações salvas em cache temporário, mas não foi possível salvar no arquivo de configuração.'
                    )

            except Exception as e:
                logger.error(f'Erro ao processar formulário: {str(e)}')
                messages.error(request, f'Erro ao salvar configurações: {str(e)}')

        # Estatísticas para exibição
        stats = {}

        # Estatísticas de lançamentos
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # Contagem de lançamentos
        stats['new_releases_count'] = Book.objects.filter(e_lancamento=True).count()

        # Último lançamento
        last_release = Book.objects.filter(e_lancamento=True).order_by('-data_publicacao').first()
        stats['new_releases_last'] = f"{last_release.titulo} - {last_release.autor}" if last_release else None

        # Lançamentos nos últimos 30 dias
        stats['new_releases_last_30'] = Book.objects.filter(
            e_lancamento=True,
            data_publicacao__gte=thirty_days_ago
        ).count()

        # Estatísticas de mais vendidos
        stats['bestsellers_with_sales'] = Book.objects.filter(quantidade_vendida__gt=0).count()

        top_seller = Book.objects.filter(quantidade_vendida__gt=0).order_by('-quantidade_vendida').first()
        stats[
            'bestsellers_top'] = f"{top_seller.titulo} ({top_seller.quantidade_vendida} vendas)" if top_seller else None

        avg_sales = Book.objects.filter(quantidade_vendida__gt=0).aggregate(avg=Avg('quantidade_vendida'))
        stats['bestsellers_avg'] = round(avg_sales['avg'], 1) if avg_sales['avg'] else 0

        # Estatísticas de recomendações
        interaction_count = UserBookShelf.objects.count()
        user_count = UserBookShelf.objects.values('user').distinct().count()

        stats['recommended_users'] = user_count
        stats['recommended_interactions'] = interaction_count
        stats['recommended_avg_interactions'] = round(interaction_count / user_count, 1) if user_count > 0 else 0

        # Estatísticas do catálogo
        stats['catalogue_count'] = Book.objects.count()

        # Contagem por categoria
        category_counts = Book.objects.values('categoria').annotate(
            count=Count('categoria')
        ).order_by('-count')

        stats['categories'] = {item['categoria']: item['count'] for item in category_counts if item['categoria']}

        context = {
            'config': config,
            'stats': stats,
            'title': 'Configurações de Modalidades de Livros',
        }

        return render(request, 'admin/book_category_config.html', context)

    def quick_shelf_creation_view(self, request):
        """
        View para criação rápida de prateleira completa.

        Esta view apresenta um formulário simplificado que permite criar:
        - Um tipo de prateleira (DefaultShelfType)
        - Uma seção na home (HomeSection)
        - Uma prateleira associada (BookShelfSection)

        Tudo em um único passo.
        """
        from ..forms import QuickShelfCreationForm

        if request.method == 'POST':
            form = QuickShelfCreationForm(request.POST)
            if form.is_valid():
                try:
                    result = form.save()
                    messages.success(
                        request,
                        f"Prateleira '{result['section'].titulo}' criada com sucesso!"
                    )
                    # Redireciona para a página de gerenciamento de prateleiras
                    return redirect('admin:shelf-management')
                except Exception as e:
                    messages.error(request, f"Erro ao criar prateleira: {str(e)}")
        else:
            form = QuickShelfCreationForm()

        context = {
            'title': 'Criação Rápida de Prateleira',
            'form': form,
            'is_nav_sidebar_enabled': True,
            'has_permission': True,
        }

        return render(request, 'admin/quick_shelf_creation.html', context)

    def visual_shelf_manager(self, request):
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
        from django.http import JsonResponse
        import json
        from ..models.book import Book

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
                        }, status=400)

                    # Busca os objetos
                    try:
                        book = Book.objects.get(id=book_id)
                        shelf = BookShelfSection.objects.get(id=shelf_id)
                    except (Book.DoesNotExist, BookShelfSection.DoesNotExist):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Livro ou prateleira não encontrado'
                        }, status=404)

                    # Verifica quantos livros já estão na prateleira
                    current_count = BookShelfItem.objects.filter(shelf=shelf).count()

                    # Avisa se ultrapassar o limite, mas permite adicionar mesmo assim
                    warning = None
                    if current_count >= shelf.max_livros:
                        warning = f"A prateleira já ultrapassou o limite de {shelf.max_livros} livros."

                    # Verifica se o livro já está na prateleira
                    if BookShelfItem.objects.filter(shelf=shelf, livro=book).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Este livro já está nesta prateleira'
                        }, status=400)

                    # Cria o novo item na prateleira com a ordem sendo a última posição
                    next_position = current_count
                    BookShelfItem.objects.create(
                        shelf=shelf,
                        livro=book,
                        ordem=next_position
                    )

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
                        }, status=400)

                    # Tenta excluir o item
                    try:
                        item = BookShelfItem.objects.get(
                            shelf_id=shelf_id,
                            livro_id=book_id
                        )
                        ordem_removida = item.ordem
                        item.delete()

                        # Reordena os itens restantes para manter a sequência
                        items_para_atualizar = BookShelfItem.objects.filter(
                            shelf_id=shelf_id,
                            ordem__gt=ordem_removida
                        ).order_by('ordem')

                        for item in items_para_atualizar:
                            item.ordem -= 1
                            item.save(update_fields=['ordem'])

                        return JsonResponse({
                            'status': 'success',
                            'message': 'Livro removido com sucesso'
                        })

                    except BookShelfItem.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Item não encontrado na prateleira'
                        }, status=404)

                elif action == 'reorder':
                    # Reordena livros dentro de uma prateleira
                    shelf_id = data.get('shelf_id')
                    order = data.get('order')  # Lista de IDs de livros na nova ordem

                    # Verifica se os dados necessários estão presentes
                    if not all([shelf_id, order]):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Parâmetros incompletos'
                        }, status=400)

                    # Processa a reordenação
                    try:
                        for index, book_id in enumerate(order):
                            try:
                                item = BookShelfItem.objects.get(
                                    shelf_id=shelf_id,
                                    livro_id=book_id
                                )
                                if item.ordem != index:
                                    item.ordem = index
                                    item.save(update_fields=['ordem'])
                            except BookShelfItem.DoesNotExist:
                                # Ignora itens não encontrados
                                continue

                        return JsonResponse({
                            'status': 'success',
                            'message': 'Ordem atualizada com sucesso'
                        })

                    except Exception as e:
                        logger.error(f"Erro ao reordenar prateleira: {str(e)}")
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Erro ao reordenar: {str(e)}'
                        }, status=500)

                # Ação desconhecida
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ação desconhecida'
                }, status=400)

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato JSON inválido'
                }, status=400)
            except Exception as e:
                logger.error(f"Erro no gerenciador visual: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erro interno: {str(e)}'
                }, status=500)

        # Renderiza a página para requisições GET
        try:
            # Busca todas as prateleiras ativas
            book_shelves = BookShelfSection.objects.select_related(
                'section', 'shelf_type'
            ).prefetch_related(
                'bookshelfitem_set', 'bookshelfitem_set__livro'
            )

            # Filtro por título ou tipo
            q = request.GET.get('q', '')
            if q:
                from django.db.models import Q
                book_shelves = book_shelves.filter(
                    Q(section__titulo__icontains=q) |
                    Q(shelf_type__nome__icontains=q)
                )

            # Busca livros não associados a prateleiras ou filtrados pela busca
            book_q = request.GET.get('book_q', '')

            # Preparar a consulta de livros
            from django.db.models import Q
            if book_q:
                # Busca livros pelo filtro
                unassigned_books = Book.objects.filter(
                    Q(titulo__icontains=book_q) |
                    Q(autor__icontains=book_q) |
                    Q(isbn__icontains=book_q)
                )[:100]  # Limita para não sobrecarregar
            else:
                # Busca livros que não estão em nenhuma prateleira
                used_book_ids = BookShelfItem.objects.values_list('livro_id', flat=True)
                unassigned_books = Book.objects.exclude(id__in=used_book_ids)[:100]

            # Adiciona nome do tipo para cada prateleira
            for book_shelf in book_shelves:
                book_shelf.get_shelf_type_name = (
                    book_shelf.shelf_type.nome if book_shelf.shelf_type
                    else book_shelf.get_tipo_shelf_display() if hasattr(book_shelf,
                                                                        'get_tipo_shelf_display') and book_shelf.tipo_shelf
                    else 'Não definido'
                )

                # Adiciona ordenação aos itens
                book_shelf.sorted_items = book_shelf.bookshelfitem_set.all().order_by('ordem')

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

    def get_shelf_management_view(self, request):
        """
        View para gerenciar toda a estrutura hierárquica de seções, estantes e prateleiras.

        Exibe uma visão geral das prateleiras existentes e permite gerenciá-las.

        Args:
            request: Requisição HTTP

        Returns:
            HttpResponse: Página de gerenciamento de prateleiras
        """
        try:
            section_q = request.GET.get('section_q', '')
            shelf_type_q = request.GET.get('shelf_type_q', '')
            book_shelf_q = request.GET.get('book_shelf_q', '')

            # Consulta os tipos de prateleira
            shelf_types = DefaultShelfType.objects.filter(ativo=True)
            if shelf_type_q:
                from django.db.models import Q
                shelf_types = shelf_types.filter(
                    Q(nome__icontains=shelf_type_q) |
                    Q(identificador__icontains=shelf_type_q)
                )
            shelf_types = shelf_types.order_by('ordem')

            # Consulta as seções da home do tipo shelf
            sections = HomeSection.objects.filter(tipo='shelf')
            if section_q:
                sections = sections.filter(titulo__icontains=section_q)

            # Adiciona informação se a seção tem prateleira
            for section in sections:
                section.prateleira_status = hasattr(section, 'book_shelf')
                if section.prateleira_status:
                    section.book_shelf.get_shelf_type_name = (
                        section.book_shelf.shelf_type.nome if section.book_shelf.shelf_type
                        else section.book_shelf.get_tipo_shelf_display() if hasattr(section.book_shelf,
                                                                                    'get_tipo_shelf_display') and section.book_shelf.tipo_shelf
                        else 'Não definido'
                    )

            # Consulta as prateleiras
            book_shelves = BookShelfSection.objects.select_related(
                'section', 'shelf_type'
            ).prefetch_related(
                'bookshelfitem_set', 'bookshelfitem_set__livro'
            )

            if book_shelf_q:
                from django.db.models import Q
                book_shelves = book_shelves.filter(
                    Q(section__titulo__icontains=book_shelf_q) |
                    Q(shelf_type__nome__icontains=book_shelf_q)
                )

            # Adiciona nome do tipo para cada prateleira
            for book_shelf in book_shelves:
                book_shelf.get_shelf_type_name = (
                    book_shelf.shelf_type.nome if book_shelf.shelf_type
                    else book_shelf.get_tipo_shelf_display() if hasattr(book_shelf,
                                                                        'get_tipo_shelf_display') and book_shelf.tipo_shelf
                    else 'Não definido'
                )

                # Conta quantos livros tem em cada prateleira
                book_shelf.book_count = book_shelf.bookshelfitem_set.count()

            context = {
                'title': 'Gerenciamento de Prateleiras',
                'shelf_types': shelf_types,
                'sections': sections,
                'book_shelves': book_shelves,
                'section_q': section_q,
                'shelf_type_q': shelf_type_q,
                'book_shelf_q': book_shelf_q
            }

            return render(request, 'admin/shelf_management.html', context)
        except Exception as e:
            logger.error(f"Erro no gerenciamento de prateleiras: {str(e)}")
            messages.error(request, f"Erro ao carregar gerenciamento de prateleiras: {str(e)}")
            return redirect('admin:index')

    def view_shelf_books(self, request):
        """
        View para visualizar livros de um tipo de prateleira específico.

        Redireciona para a lista filtrada de livros no admin com base no tipo de prateleira selecionado.

        Args:
            request: Requisição HTTP

        Returns:
            HttpResponse: Redirecionamento para a lista de livros filtrada
        """
        try:
            shelf_type_id = request.GET.get('shelf_type')

            if not shelf_type_id:
                messages.warning(request, "Nenhum tipo de prateleira especificado.")
                return redirect('admin:index')

            shelf_type = DefaultShelfType.objects.get(id=shelf_type_id)

            # Redireciona para a lista de livros com filtro apropriado
            if shelf_type.filtro_campo == 'e_lancamento':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_lancamento__exact=1")
            elif shelf_type.filtro_campo == 'e_destaque':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_destaque__exact=1")
            elif shelf_type.filtro_campo == 'adaptado_filme':
                return redirect(f"{reverse('admin:core_book_changelist')}?adaptado_filme__exact=1")
            elif shelf_type.filtro_campo == 'e_manga':
                return redirect(f"{reverse('admin:core_book_changelist')}?e_manga__exact=1")
            elif shelf_type.filtro_campo in ['categoria', 'autor', 'editora',
                                             'ano_publicacao'] and shelf_type.filtro_valor:
                # Para campos com valores específicos
                campo = shelf_type.filtro_campo
                valor = shelf_type.filtro_valor
                return redirect(f"{reverse('admin:core_book_changelist')}?{campo}__iexact={valor}")
            else:
                # Filtro genérico ou tipo sem filtro definido
                return redirect(reverse('admin:core_book_changelist'))

        except DefaultShelfType.DoesNotExist:
            messages.error(request, "Tipo de prateleira não encontrado.")
            return redirect('admin:index')
        except Exception as e:
            logger.error(f"Erro ao visualizar livros da prateleira: {str(e)}")
            messages.error(request, f"Erro ao visualizar livros: {str(e)}")
            return redirect('admin:index')

    def chatbot_conversations_view(self, request):
        """
        View para redirecionar para a lista de conversas do chatbot.
        """
        # Importar o modelo Conversation para obter a lista
        from cgbookstore.apps.chatbot_literario.models import Conversation

        # Obter todas as conversas ou apresentar uma mensagem se não existir
        conversations = Conversation.objects.all().order_by('-updated_at')

        context = {
            'title': 'Conversas do Chatbot',
            'conversations': conversations,
        }

        return render(request, 'admin/chatbot_literario/conversation_list.html', context)

    def chatbot_feedbacks_view(self, request):
        """
        View para redirecionar para a lista de feedbacks do chatbot.
        """
        # Importar o modelo ConversationFeedback para obter a lista
        from cgbookstore.apps.chatbot_literario.models import ConversationFeedback

        # Obter todos os feedbacks ou apresentar uma mensagem se não existir
        feedbacks = ConversationFeedback.objects.all().order_by('-timestamp')

        context = {
            'title': 'Feedbacks do Chatbot',
            'feedbacks': feedbacks,
        }

        return render(request, 'admin/chatbot_literario/feedback_list.html', context)

    def get_urls(self):
        """
        Adiciona URLs personalizadas ao admin.
        """
        urls = super().get_urls()

        # Importa as ferramentas de diagnóstico
        from .diagnostics_admin import diagnostics_admin

        custom_urls = [
            # URLs existentes...
            path('view-database/', self.admin_view(self.view_database), name='view-database'),
            path('generate-schema/', self.admin_view(self.generate_schema_view), name='generate-schema'),
            path('generate-structure/', self.admin_view(self.generate_structure_view), name='generate-structure'),
            path('export-data/json/', self.admin_view(self.export_data_json), name='export-data-json'),
            path('clear-folders/all/', self.admin_view(self.clear_folders_view), name='clear-folders'),
            path('clear-folders/schema/', self.admin_view(self.clear_schema_folder_view), name='clear-schema-folder'),
            path('clear-folders/structure/', self.admin_view(self.clear_structure_folder_view),
                 name='clear-structure-folder'),
            path('book-category-config/', self.admin_view(self.book_category_config_view), name='book-category-config'),

            # URLs para gerenciamento de prateleiras
            path('shelf-management/', self.admin_view(views.shelf_management_statistics), name='shelf-management'),
            path('shelf-management-stats/', self.admin_view(views.shelf_management_statistics),
                 name='shelf-management-stats'),
            path('view-shelf-books/', self.admin_view(self.view_shelf_books), name='view_shelf_books'),
            path('quick-shelf-creation/', self.admin_view(self.quick_shelf_creation_view), name='quick-shelf-creation'),
            path('visual-shelf-manager/', self.admin_view(self.visual_shelf_manager), name='visual-shelf-manager'),

            # URLs para o treinamento do chatbot
            path('chatbot/treinamento/', self.admin_view(chatbot_views.training_interface),
                 name='chatbot_literario_training'),
            path('chatbot/treinamento/testar/', self.admin_view(chatbot_views.test_chatbot),
                 name='test_chatbot'),
            path('chatbot/treinamento/adicionar-conhecimento/', self.admin_view(chatbot_views.add_knowledge_item),
                 name='add_knowledge_item'),
            path('chatbot/treinamento/adicionar-da-conversa/', self.admin_view(chatbot_views.add_to_knowledge),
                 name='add_to_knowledge'),
            path('chatbot/treinamento/importar/', self.admin_view(chatbot_views.import_knowledge),
                 name='import_knowledge'),
            path('chatbot/treinamento/exportar/', self.admin_view(chatbot_views.export_knowledge),
                 name='export_knowledge'),
            path('chatbot/treinamento/update-embeddings/', self.admin_view(chatbot_views.update_embeddings),
                 name='update_embeddings'),

            # ✅ NOVAS URLs DAS FERRAMENTAS (ADICIONAR APÓS AS URLs EXISTENTES)
            path('chatbot/treinamento/add-specific-dates/', self.admin_view(chatbot_views.run_add_specific_dates),
                 name='run_add_specific_dates'),
            path('chatbot/treinamento/debug-chatbot/', self.admin_view(chatbot_views.run_debug_chatbot),
                 name='run_debug_chatbot'),
            path('chatbot/treinamento/clean-knowledge/', self.admin_view(chatbot_views.clean_knowledge_base),
                 name='clean_knowledge_base'),
            path('chatbot/treinamento/statistics/', self.admin_view(chatbot_views.system_statistics),
                 name='system_statistics'),
            path('chatbot/treinamento/config/', self.admin_view(chatbot_views.system_config),
                 name='system_config'),

            # URLs diretas para conversas e feedbacks
            path('chatbot/conversas/',
                 self.admin_view(self.chatbot_conversations_view),
                 name='chatbot_conversations'),
            path('chatbot/feedbacks/',
                 self.admin_view(self.chatbot_feedbacks_view),
                 name='chatbot_feedbacks'),

            # 🚀 NOVAS URLs DE DIAGNÓSTICOS
            path('diagnostics/', self.admin_view(diagnostics_admin.diagnostics_dashboard),
                 name='diagnostics_dashboard'),
            path('diagnostics/performance/', self.admin_view(diagnostics_admin.performance_diagnostics),
                 name='performance_diagnostics'),
            path('diagnostics/redis-info/', self.admin_view(diagnostics_admin.redis_info), name='redis_info'),
            path('diagnostics/fix-covers/', self.admin_view(diagnostics_admin.fix_corrupted_covers),
                 name='fix_corrupted_covers'),
            path('diagnostics/debug-books/', self.admin_view(diagnostics_admin.debug_book_images),
                 name='debug_book_images'),
            path('diagnostics/debug-recommendations/', self.admin_view(diagnostics_admin.debug_recommendations),
                 name='debug_recommendations'),
            path('diagnostics/system-health/', self.admin_view(diagnostics_admin.system_health_check),
                 name='system_health_check'),
            path('diagnostics/clear-cache/', self.admin_view(diagnostics_admin.clear_cache), name='clear_cache'),
            path('diagnostics/task-status/<str:task_id>/', self.admin_view(diagnostics_admin.task_status),
                 name='task_status'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """
        Sobrescreve o método index para adicionar links do Chatbot Literário
        """
        if extra_context is None:
            extra_context = {}

        # URLs personalizadas para as páginas do chatbot
        chatbot_links = [
            {
                'name': 'Treinamento do Chatbot',
                'url': '/admin/chatbot/treinamento/',
                'icon': 'bi bi-robot'
            },
            {
                'name': 'Conversas',
                'url': '/admin/chatbot/conversas/',
                'icon': 'bi bi-chat-dots'
            },
            {
                'name': 'Feedbacks',
                'url': '/admin/chatbot/feedbacks/',
                'icon': 'bi bi-star'
            }
        ]

        extra_context['chatbot_links'] = chatbot_links

        # Reordenar as aplicações administrativas
        # Obter a lista de aplicativos original
        response = super().index(request, extra_context)

        # Mantenha a estrutura original dos templates
        # mas apenas reordene as seções
        context_data = response.context_data
        if 'app_list' in context_data:
            app_list = context_data['app_list']

            # Identificar e reordenar as seções por seus nomes
            app_sections = {}
            for i, app in enumerate(app_list):
                app_name = app.get('name', '')

                # Classificar as aplicações em seções
                if 'Chatbot' in app_name:
                    section = 'CHATBOT'
                    order = 1
                elif 'Auth' in app_name or 'Autenticação' in app_name:
                    section = 'AUTH'
                    order = 2
                elif 'Core' in app_name or 'Organizador' in app_name:
                    section = 'ORG'
                    order = 3
                else:
                    section = 'OTHER'
                    order = 4 + i  # Manter a ordem original para outras seções

                # Adicionar ordem e seção ao app
                app['section'] = section
                app['order'] = order

            # Reordenar a lista
            app_list.sort(key=lambda x: x.get('order', 999))

            # Atualizar o contexto
            context_data['app_list'] = app_list

        return response