import datetime
import math
import json
import logging
import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, View, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum

from ..forms import UserProfileForm
from ..models import Profile, UserBookShelf, UserAchievement, ReadingStats, Achievement
from ..models.profile import ReadingProgress

# Configuração de logging
logger = logging.getLogger(__name__)


class ProfileView(LoginRequiredMixin, DetailView):
    """
    View para visualização do perfil do usuário.
    """
    model = Profile
    template_name = 'core/profile/profile.html'
    context_object_name = 'core:profile'

    def get_object(self, queryset=None):
        """
        Retorna o perfil do usuário logado.

        Para DetailView, precisamos sobrescrever get_object
        para retornar o perfil do usuário atual em vez de
        tentar buscar por pk ou slug.
        """
        # Verificar se o usuário tem um perfil
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            # Se não existir, cria um perfil para o usuário
            logger.info(f"Criando perfil para usuário {self.request.user.username}")
            return Profile.objects.create(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Prepara dados de contexto do perfil, incluindo estatísticas e conquistas.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            # Buscar prateleiras com livros válidos
            shelves = UserBookShelf.objects.filter(
                user=user,
                book__isnull=False  # Apenas prateleiras com livros
            ).select_related('book')

            # Filtrar livros por tipo de prateleira e garantir que tenham IDs válidos
            favoritos = []
            lendo = []
            vou_ler = []
            lidos = []

            for shelf in shelves:
                if shelf.book and shelf.book.pk:
                    if shelf.shelf_type == 'favorito':
                        favoritos.append(shelf)
                    elif shelf.shelf_type == 'lendo':
                        lendo.append(shelf)
                    elif shelf.shelf_type == 'vou_ler':
                        vou_ler.append(shelf)
                    elif shelf.shelf_type == 'lido':
                        lidos.append(shelf)
                else:
                    logger.warning(f"Livro inválido na prateleira {shelf.shelf_type}: shelf_id={shelf.id}")

            # Adicionar ao contexto
            context.update({
                'favoritos': favoritos,
                'lendo': lendo,
                'vou_ler': vou_ler,
                'lidos': lidos,
                'recomendacoes': [],
                'total_livros': len(favoritos) + len(lendo) + len(vou_ler) + len(lidos),
            })

        except Exception as e:
            logger.error(f"Erro ao processar prateleiras: {str(e)}")
            context.update({
                'favoritos': [],
                'lendo': [],
                'vou_ler': [],
                'lidos': [],
                'recomendacoes': [],
                'total_livros': 0,
            })

        # Obter ou criar estatísticas do usuário
        try:
            stats, created = ReadingStats.objects.get_or_create(user=user)

            # Se as estatísticas foram criadas agora, atualizá-las
            if created:
                stats.update_stats()

            # Adicionar estatísticas ao contexto
            context['stats'] = {
                'total_lidos': stats.total_books_read,
                'total_paginas': stats.total_pages_read,
                'sequencia_atual': stats.reading_streak,
                'maior_sequencia': stats.longest_streak,
                'genero_favorito': stats.favorite_genre or 'Não definido',
                'velocidade_leitura': stats.reading_velocity or 0,
                'livros_por_mes': stats.books_by_month or {}
            }
        except Exception as e:
            logger.error(f"Erro ao processar estatísticas: {str(e)}")
            context['stats'] = {
                'total_lidos': 0,
                'total_paginas': 0,
                'sequencia_atual': 0,
                'maior_sequencia': 0,
                'genero_favorito': 'Não definido',
                'velocidade_leitura': 0,
                'livros_por_mes': {}
            }

        # Obter conquistas
        try:
            user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')

            # Adicionar conquistas ao contexto
            context['achievements'] = {
                'total': user_achievements.count(),
                'unlocked': list(user_achievements.values(
                    'achievement__name', 'achievement__description',
                    'achievement__icon', 'achievement__tier',
                    'achievement__points', 'achieved_at'
                )),
                'in_progress': self.get_in_progress_achievements(user, shelves)
            }

            # Calcular pontuação total (otimizado usando aggregate)
            total_points = UserAchievement.objects.filter(user=user).aggregate(
                total=Sum('achievement__points')
            )['total'] or 0
            context['total_points'] = total_points

        except Exception as e:
            logger.error(f"Erro ao processar conquistas: {str(e)}")
            context['achievements'] = {
                'total': 0,
                'unlocked': [],
                'in_progress': []
            }
            context['total_points'] = 0

        return context

    def get_in_progress_achievements(self, user, shelves=None):
        """
        Retorna as próximas conquistas que o usuário está perto de alcançar.

        Args:
            user: Usuário atual
            shelves: Coleção de prateleiras (opcional, para otimização)

        Returns:
            Lista de conquistas em andamento com progresso calculado
        """
        try:
            # Garantir que temos apenas livros válidos para cálculos
            valid_shelves = []
            if shelves is None:
                shelves = UserBookShelf.objects.filter(user=user).select_related('book')

            # Filtrar apenas shelves com livros válidos
            valid_shelves = [shelf for shelf in shelves if shelf.book and shelf.book.pk]

            # Obter todas as conquistas
            all_achievements = Achievement.objects.all()

            # Obter conquistas que o usuário já tem em uma única consulta
            user_achievement_ids = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)

            # Conquistas que o usuário ainda não tem
            pending_achievements = all_achievements.exclude(id__in=user_achievement_ids)

            # Cálculo de progresso de conquistas
            total_books = len(valid_shelves)
            books_read = sum(1 for shelf in valid_shelves if shelf.shelf_type == 'lido')

            # Mapeamento de código de conquista para critério e meta
            achievement_criteria = {
                'book_collector_i': ('total_books', 5),
                'book_collector_ii': ('total_books', 25),
                'bookworm_i': ('books_read', 5),
                'bookworm_ii': ('books_read', 15)
            }

            # Lista para armazenar conquistas em andamento
            in_progress = []

            # Calcular progresso de forma genérica
            for achievement in pending_achievements:
                if achievement.code in achievement_criteria:
                    metric_type, target = achievement_criteria[achievement.code]
                    current_value = total_books if metric_type == 'total_books' else books_read

                    # Só incluir se ainda não atingiu a meta
                    if current_value < target:
                        progress = min(int(current_value / target * 100), 99)

                        in_progress.append({
                            'id': achievement.id,
                            'name': achievement.name,
                            'description': achievement.description,
                            'progress': progress,
                            'icon': achievement.icon,
                            'tier': achievement.tier
                        })

            # Limitar a 3 conquistas em progresso
            return sorted(in_progress, key=lambda x: x['progress'], reverse=True)[:3]

        except Exception as e:
            logger.error(f"Erro ao calcular conquistas em andamento: {str(e)}")
            return []


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para atualização do perfil do usuário.

    Características:
    - Requer login
    - Utiliza formulário de perfil
    - Adiciona mensagens de status
    """
    model = Profile
    form_class = UserProfileForm
    template_name = 'core/profile/profile_form.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self, queryset=None):
        """
        Retorna o perfil do usuário logado para edição.

        Returns:
            Profile: Perfil do usuário atual
        """
        # Verificar se o usuário tem um perfil
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            # Manter consistência com ProfileView criando um perfil se não existir
            logger.info(f"Criando perfil para usuário {self.request.user.username} durante atualização")
            return Profile.objects.create(user=self.request.user)

    def form_valid(self, form):
        """
        Processa atualização de perfil bem-sucedida.

        Args:
            form: Formulário de perfil validado

        Returns:
            HttpResponse: Redireciona com mensagem de sucesso
        """
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Trata erros na atualização do perfil.

        Args:
            form: Formulário de perfil inválido

        Returns:
            HttpResponse: Renderiza formulário com mensagem de erro
        """
        # Mensagem mais específica sobre os erros
        erro_msg = 'Erro ao atualizar perfil. '
        for field, errors in form.errors.items():
            erro_msg += f"Problema em '{field}': {', '.join(errors)}. "

        messages.error(self.request, erro_msg)
        return super().form_invalid(form)


class ProfileCardStyleView(LoginRequiredMixin, View):
    """
    View para gerenciamento do estilo de card do perfil.

    Características:
    - Requer login
    - Recupera e atualiza estilo personalizado do card
    """

    def get(self, request, *args, **kwargs):
        """
        Recupera o estilo atual do card do perfil.

        Returns:
            JsonResponse: Estilo do card em formato JSON
        """
        try:
            return JsonResponse(request.user.profile.get_card_style())
        except Exception as e:
            logger.error(f"Erro ao recuperar estilo de card: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erro ao recuperar estilo do card'
            }, status=400)

    def post(self, request, *args, **kwargs):
        """
        Atualiza o estilo do card do perfil.

        Etapas:
        1. Decodifica dados JSON
        2. Atualiza estilo do perfil

        Returns:
            JsonResponse: Resultado da atualização
        """
        try:
            # Decodificar dados JSON
            # Tentar obter dados tanto do body quanto de form-data
            try:
                if request.body:
                    data = json.loads(request.body.decode('utf-8'))
                else:
                    # Se não houver dados JSON, tentar obter de POST
                    data = {}
                    for key, value in request.POST.items():
                        # Tentar converter possíveis strings JSON
                        if key.startswith('{') and key.endswith('}'):
                            try:
                                # Se o próprio key for um JSON
                                json_data = json.loads(key)
                                data = json_data
                                break
                            except:
                                pass
                        data[key] = value
            except json.JSONDecodeError:
                # Se falhar, tentar obter do POST
                data = dict(request.POST.items())

            # Log para depuração
            logger.debug(f"Dados recebidos para estilo de card: {data}")

            profile = request.user.profile

            # Se estiver vazio, retornar erro
            if not data:
                return JsonResponse({
                    'success': False,
                    'error': 'Dados não fornecidos'
                }, status=400)

            # Campos para o estilo do card
            style_fields = [
                'background_color', 'text_color', 'border_color',
                'image_style', 'hover_effect', 'icon_style',
                'border_radius', 'shadow_style'
            ]

            # Criar dicionário com valores válidos
            style_data = {}

            # Obter estilo atual para campos ausentes
            current_style = profile.get_card_style() or {}

            # Processar os campos
            for field in style_fields:
                if field in data and data[field]:
                    style_data[field] = data[field]
                else:
                    style_data[field] = current_style.get(field, '')

            # Salvar o estilo atualizado
            profile.card_style = style_data
            profile.save()

            return JsonResponse({
                'success': True,
                'styles': profile.get_card_style()
            })

        except Exception as e:
            # Log detalhado para depuração
            logger.error(f"Erro ao salvar estilo de card: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Erro ao salvar: {str(e)}'
            }, status=400)


class ProfilePhotoUpdateView(LoginRequiredMixin, View):
    """
    View para atualização da foto de perfil.

    Características:
    - Requer login
    - Valida tipo e tamanho da imagem
    - Gerencia remoção de foto anterior
    """

    def post(self, request, *args, **kwargs):
        """
        Atualiza a foto de perfil do usuário.

        Etapas:
        1. Valida existência de arquivo
        2. Verifica tipo de imagem
        3. Valida tamanho do arquivo
        4. Remove foto anterior (se existir)
        5. Salva nova foto

        Returns:
            JsonResponse: Resultado da atualização
        """
        try:
            # Verificar se foto foi enviada
            if 'profile_photo' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhuma foto enviada'
                }, status=400)

            photo = request.FILES['profile_photo']

            # Validar tipo do arquivo - verificação mais rigorosa
            valid_image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if photo.content_type not in valid_image_types:
                return JsonResponse({
                    'success': False,
                    'error': 'O arquivo deve ser uma imagem (JPEG, PNG, GIF ou WebP)'
                }, status=400)

            # Validar tamanho (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'A imagem deve ter no máximo 5MB'
                }, status=400)

            # Se já existir uma foto, remover com proteção contra path traversal
            if request.user.foto:
                old_photo_path = request.user.foto.path
                if os.path.exists(old_photo_path) and os.path.isfile(old_photo_path):
                    # Verificar se o caminho está dentro do diretório de mídia
                    try:
                        os.remove(old_photo_path)
                    except OSError as e:
                        logger.error(f"Erro ao remover foto antiga: {str(e)}")

            # Salvar nova foto
            request.user.foto = photo
            request.user.save()

            return JsonResponse({
                'success': True,
                'message': 'Foto atualizada com sucesso'
            })

        except Exception as e:
            # Tratamento de erros gerais
            logger.error(f"Erro ao processar upload de foto: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class CurrentReadingView(LoginRequiredMixin, View):
    """
    View para obter informações sobre o livro atual que o usuário está lendo.
    """

    def get(self, request, *args, **kwargs):
        try:
            user = request.user

            # Buscar o progresso mais recente (último livro lido)
            progress = ReadingProgress.objects.filter(
                user=user
            ).order_by('-last_read_at').select_related('book').first()

            # Se não encontrar progresso, buscar qualquer livro na prateleira 'lendo'
            if not progress:
                shelf = UserBookShelf.objects.filter(
                    user=user,
                    shelf_type='lendo'
                ).select_related('book').first()

                if not shelf or not shelf.book:
                    return JsonResponse({
                        'has_current_book': False
                    })

                # Criar progresso para este livro
                progress = ReadingProgress.objects.create(
                    user=user,
                    book=shelf.book,
                    started_at=timezone.now(),
                    current_page=1
                )

            # Obter dados do livro
            book = progress.book

            # Preparar dados de progresso
            total_pages = book.numero_paginas or 100
            progress_percent = min(
                round((progress.current_page / total_pages) * 100),
                100
            )

            # Calcular média de páginas por dia e data estimada de conclusão
            avg_pages_per_day = 0
            estimated_completion = None

            if progress.started_at and progress.current_page > 1:
                days_reading = max(1, (timezone.now() - progress.started_at).days)
                avg_pages_per_day = round(progress.current_page / days_reading)

                if avg_pages_per_day > 0:
                    pages_left = total_pages - progress.current_page
                    days_left = math.ceil(pages_left / avg_pages_per_day)
                    estimated_completion = timezone.now() + timezone.timedelta(days=days_left)

            # Montar resposta com dados do livro e progresso
            response_data = {
                'has_current_book': True,
                'book': {
                    'id': book.id,
                    'title': book.titulo,
                    'author': book.autor,
                    'cover_url': book.get_capa_url(),
                    'total_pages': total_pages,
                    'current_page': progress.current_page,
                    'progress_percent': progress_percent,
                    'started_at': progress.started_at.isoformat() if progress.started_at else timezone.now().isoformat(),
                    'avg_pages_per_day': avg_pages_per_day,
                    'estimated_completion': estimated_completion.isoformat() if estimated_completion else None
                }
            }

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Erro ao obter livro atual: {str(e)}", exc_info=True)
            return JsonResponse({
                'has_current_book': False,
                'error': 'Erro ao obter informações do livro atual'
            })

    def post(self, request, *args, **kwargs):
        """
        Define um livro específico como ativo para exibição no card.
        """
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')

            if not book_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID do livro não fornecido'
                }, status=400)

            user = request.user

            # Buscar o progresso do livro
            try:
                progress = ReadingProgress.objects.get(
                    user=user,
                    book_id=book_id
                )

                # Atualizar o timestamp e marcar como ativo
                progress.last_read_at = timezone.now()
                progress.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Livro definido como atual'
                })

            except ReadingProgress.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Progresso de leitura não encontrado para este livro'
                }, status=404)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao definir livro atual: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Erro ao definir livro atual'
            }, status=500)


class CurrentReadingsView(LoginRequiredMixin, TemplateView):
    """
    View para gerenciar todos os livros sendo lidos atualmente.
    """
    template_name = 'core/profile/current_readings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Buscar todos os livros na prateleira 'lendo'
        reading_shelves = UserBookShelf.objects.filter(
            user=user,
            shelf_type='lendo'
        ).select_related('book')

        # Buscar o progresso de cada livro
        reading_progress_list = []

        for shelf in reading_shelves:
            if not shelf.book or not shelf.book.pk:
                continue

            # Buscar ou criar progresso para este livro
            progress, created = ReadingProgress.objects.get_or_create(
                user=user,
                book=shelf.book,
                defaults={
                    'started_at': timezone.now(),
                    'current_page': 1
                }
            )

            # Calcular dados de progresso
            total_pages = shelf.book.numero_paginas or 100
            progress_percent = min(
                round((progress.current_page / total_pages) * 100),
                100
            )

            # Calcular média de páginas por dia e data estimada de conclusão
            avg_pages_per_day = 0
            estimated_completion = None

            if progress.started_at and progress.current_page > 1:
                days_reading = max(1, (timezone.now() - progress.started_at).days)
                avg_pages_per_day = round(progress.current_page / days_reading)

                if avg_pages_per_day > 0:
                    pages_left = total_pages - progress.current_page
                    days_left = math.ceil(pages_left / avg_pages_per_day)
                    estimated_completion = timezone.now() + timezone.timedelta(days=days_left)

            # Adicionar à lista
            reading_progress_list.append({
                'shelf': shelf,
                'book': shelf.book,
                'progress': progress,
                'progress_percent': progress_percent,
                'avg_pages_per_day': avg_pages_per_day,
                'estimated_completion': estimated_completion,
                'last_read_at': progress.last_read_at if hasattr(progress, 'last_read_at') else progress.updated_at
            })

        # Ordenar por último lido (mais recente primeiro)
        reading_progress_list.sort(key=lambda x: x.get('last_read_at', timezone.now()), reverse=True)

        context['reading_progress_list'] = reading_progress_list
        return context


class UpdateReadingProgressView(LoginRequiredMixin, View):
    """
    View para atualizar o progresso de leitura de um livro.
    Endpoint: /profile/update-reading-progress/
    Método: POST
    Dados esperados: book_id, current_page, mark_as_finished
    """

    def post(self, request, *args, **kwargs):
        """
        Atualiza o progresso de leitura de um livro.
        """
        try:
            data = json.loads(request.body)
            user = request.user

            book_id = data.get('book_id')
            current_page = data.get('current_page')
            started_at = data.get('started_at')
            mark_as_finished = data.get('mark_as_finished', False)

            # Validar dados
            if not book_id or not current_page:
                return JsonResponse({
                    'success': False,
                    'error': 'Dados incompletos. Informe o ID do livro e a página atual.'
                }, status=400)

            # Verificar data válida
            if started_at:
                try:
                    # Converter string para objeto datetime (formato YYYY-MM-DD)
                    started_at_date = timezone.datetime.strptime(started_at, '%Y-%m-%d')
                    # Adicionar timezone
                    started_at_date = timezone.make_aware(started_at_date)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Formato de data inválido. Use o formato YYYY-MM-DD.'
                    }, status=400)
            else:
                # Se não fornecida, usar data atual
                started_at_date = timezone.now()

            # Verificar se o livro existe
            from ..models import Book
            try:
                book = Book.objects.get(id=book_id)
            except Book.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Livro não encontrado.'
                }, status=404)

            # Verificar se o livro está na prateleira do usuário
            shelf = UserBookShelf.objects.filter(
                user=user,
                book=book
            ).first()

            if not shelf:
                return JsonResponse({
                    'success': False,
                    'error': 'Este livro não está na sua prateleira.'
                }, status=403)

            # Buscar ou criar registro de progresso
            progress, created = ReadingProgress.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'started_at': started_at_date,
                    'current_page': 1
                }
            )

            # Atualizar página atual
            progress.current_page = current_page

            # Atualizar data de início se fornecida
            if started_at:
                progress.started_at = started_at_date

            progress.updated_at = timezone.now()

            # Salvar progresso
            progress.save()

            # Se marcado como concluído, mover para a prateleira 'lido'
            if mark_as_finished:
                # Se estava na prateleira 'lendo', mover para 'lido'
                if shelf.shelf_type == 'lendo':
                    shelf.shelf_type = 'lido'
                    shelf.save()

                    # Atualizar estatísticas de leitura (se existir)
                    try:
                        stats, _ = ReadingStats.objects.get_or_create(user=user)
                        stats.update_stats()
                    except Exception as stats_error:
                        logger.warning(f"Erro ao atualizar estatísticas: {str(stats_error)}")

            return JsonResponse({
                'success': True,
                'message': 'Progresso atualizado com sucesso!'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos.'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Erro ao atualizar progresso. Tente novamente mais tarde.'
            }, status=500)


class FavoriteQuoteView(LoginRequiredMixin, View):
    """
    View para gerenciar a citação favorita do usuário.

    Métodos:
    - GET: Retorna a citação atual
    - POST: Salva uma nova citação
    """

    def get(self, request, *args, **kwargs):
        """
        Recupera a citação favorita do usuário.

        Returns:
            JsonResponse: Dados da citação em formato JSON
        """
        try:
            profile = request.user.profile

            # Verificar se o usuário tem uma citação
            has_quote = bool(profile.favorite_quote and profile.favorite_quote_author)

            # Preparar resposta
            quote_data = {
                'has_quote': has_quote,
                'quote': profile.favorite_quote or "",
                'author': profile.favorite_quote_author or "",
                'source': profile.favorite_quote_source or ""
            }

            return JsonResponse(quote_data)

        except Exception as e:
            logger.error(f"Erro ao recuperar citação favorita: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Erro ao recuperar citação favorita',
                'has_quote': False
            }, status=400)

    def post(self, request, *args, **kwargs):
        """
        Salva uma nova citação favorita.

        Espera um payload JSON com:
        - quote: Texto da citação
        - author: Autor da citação
        - source: Fonte da citação (opcional)

        Returns:
            JsonResponse: Resultado da operação
        """
        try:
            # Decodificar dados JSON
            data = json.loads(request.body.decode('utf-8'))

            # Validar campos obrigatórios
            quote = data.get('quote', '').strip()
            author = data.get('author', '').strip()
            source = data.get('source', '').strip()

            if not quote or not author:
                return JsonResponse({
                    'success': False,
                    'error': 'Citação e autor são campos obrigatórios'
                }, status=400)

            # Limitar tamanho da citação
            if len(quote) > 500:
                quote = quote[:497] + '...'

            # Salvar na instância do perfil
            profile = request.user.profile
            profile.favorite_quote = quote
            profile.favorite_quote_author = author
            profile.favorite_quote_source = source
            profile.save()

            # Retornar resposta de sucesso
            return JsonResponse({
                'success': True,
                'message': 'Citação salva com sucesso'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao salvar citação favorita: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao salvar citação: {str(e)}'
            }, status=500)



class DetailedStatsView(LoginRequiredMixin, View):
    """
    View para fornecer estatísticas detalhadas para o widget do card de perfil.
    Endpoint: /profile/detailed-stats/
    """

    def get(self, request, *args, **kwargs):
        """
        Retorna estatísticas detalhadas do usuário em formato JSON.
        """
        try:
            user = request.user

            # Obter estatísticas básicas do usuário
            stats, created = ReadingStats.objects.get_or_create(user=user)

            # Se as estatísticas foram criadas agora, atualizá-las
            if created:
                stats.update_stats()

            # Obter prateleiras
            reading_shelves = UserBookShelf.objects.filter(
                user=user,
                shelf_type='lendo'
            ).select_related('book')

            read_shelves = UserBookShelf.objects.filter(
                user=user,
                shelf_type='lido'
            ).select_related('book')

            # Calcular ritmo de leitura
            total_books = read_shelves.count()
            now = timezone.now()
            start_of_year = timezone.make_aware(datetime.datetime(now.year, 1, 1))

            # Livros lidos este ano
            books_this_year = read_shelves.filter(
                added_at__gte=start_of_year
            ).count()

            # Calcular estatísticas por mês (últimos 12 meses)
            books_by_month = {}
            for i in range(12):
                month_start = now - timezone.timedelta(days=30 * i)
                month_end = now - timezone.timedelta(days=30 * (i - 1)) if i > 0 else now
                count = read_shelves.filter(
                    added_at__gte=month_start,
                    added_at__lte=month_end
                ).count()
                month_key = month_start.strftime('%m/%Y')
                books_by_month[month_key] = count

            # Calcular projeção anual
            days_passed = (now - start_of_year).days
            days_in_year = 366 if now.year % 4 == 0 else 365
            yearly_projection = int(books_this_year * (days_in_year / max(days_passed, 1)))

            # Tendência (comparação com ano anterior)
            last_year = now.year - 1
            start_of_last_year = timezone.make_aware(datetime.datetime(last_year, 1, 1))
            end_of_last_year = timezone.make_aware(datetime.datetime(last_year, 12, 31, 23, 59, 59))

            books_last_year = read_shelves.filter(
                added_at__gte=start_of_last_year,
                added_at__lte=end_of_last_year
            ).count()

            # Calcular tendência
            if books_last_year > 0:
                trend_percentage = int((yearly_projection - books_last_year) / books_last_year * 100)
            else:
                trend_percentage = 100  # Se não havia livros no ano anterior, considerar 100% de aumento

            trend = f"+{trend_percentage}%" if trend_percentage >= 0 else f"{trend_percentage}%"

            # Calcular média semanal e mensal
            weekly_pace = round(books_this_year / max((days_passed / 7), 1), 1)
            monthly_pace = round(books_this_year / max((days_passed / 30), 1), 1)

            # Análise de gêneros
            genres = {}
            for shelf in read_shelves:
                if shelf.book and shelf.book.categoria:
                    genre = shelf.book.categoria
                    genres[genre] = genres.get(genre, 0) + 1

            # Ordenar gêneros por contagem
            top_genres = []
            if genres:
                sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
                total_genre_count = sum(genres.values())

                # Pegar os 5 principais gêneros
                for genre, count in sorted_genres[:5]:
                    percentage = int((count / total_genre_count) * 100)
                    top_genres.append({
                        'name': genre,
                        'count': count,
                        'percentage': percentage
                    })

            # Análise de autores
            authors = {}
            for shelf in read_shelves:
                if shelf.book and shelf.book.autor:
                    author = shelf.book.autor
                    authors[author] = authors.get(author, 0) + 1

            # Ordenar autores por contagem
            top_authors = []
            if authors:
                sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)

                # Pegar os 5 principais autores
                for author, count in sorted_authors[:5]:
                    top_authors.append({
                        'name': author,
                        'count': count
                    })

            # Calcular estatísticas de tempo
            total_pages = sum(shelf.book.numero_paginas or 0 for shelf in read_shelves if shelf.book)
            avg_reading_time = 0.3  # Assumindo 0.3 horas (18 minutos) por página em média
            total_hours = int(total_pages * avg_reading_time)

            # Média por livro
            avg_per_book = round((total_hours / total_books) if total_books > 0 else 0, 1)

            # Média diária (considerando apenas os dias em que o usuário leu)
            reading_progress = ReadingProgress.objects.filter(user=user)
            unique_days = set()
            for progress in reading_progress:
                if progress.last_read_at:
                    unique_days.add(progress.last_read_at.date())

            total_reading_days = len(unique_days) or 1  # Evitar divisão por zero
            avg_per_day = round(total_hours / total_reading_days, 1)

            # Sequência de atividade
            progress_days = list(sorted(unique_days, reverse=True))

            current_streak = 0
            longest_streak = 0
            current_count = 0

            if progress_days:
                # Verificar sequência atual
                today = timezone.now().date()
                yesterday = today - timezone.timedelta(days=1)

                # Se leu hoje ou ontem, começar sequência
                if today in progress_days or yesterday in progress_days:
                    current_streak = 1
                    last_date = progress_days[0] if progress_days[0] == today else None

                    # Contar dias consecutivos
                    for i in range(1, len(progress_days)):
                        if last_date and (last_date - progress_days[i]).days == 1:
                            current_streak += 1
                            last_date = progress_days[i]
                        else:
                            break

                # Encontrar maior sequência histórica
                for i in range(len(progress_days)):
                    if i == 0:
                        current_count = 1
                    else:
                        if (progress_days[i - 1] - progress_days[i]).days == 1:
                            current_count += 1
                        else:
                            longest_streak = max(longest_streak, current_count)
                            current_count = 1

                longest_streak = max(longest_streak, current_count)

            # Calcular dias ativos na semana
            last_week_start = today - timezone.timedelta(days=7)
            last_week_days = [day for day in progress_days if day >= last_week_start]
            weekly_active_days = len(last_week_days)

            # Estruturar resposta com as estatísticas detalhadas
            detailed_stats = {
                'reading_pace': {
                    'weekly': weekly_pace,
                    'monthly': monthly_pace,
                    'yearly': yearly_projection,
                    'trend': trend
                },
                'top_genres': top_genres,
                'top_authors': top_authors,
                'reading_time': {
                    'total_hours': total_hours,
                    'average_per_book': avg_per_book,
                    'average_per_day': avg_per_day
                },
                'activity_streak': {
                    'current': current_streak,
                    'longest': longest_streak,
                    'weekly_active_days': weekly_active_days
                }
            }

            return JsonResponse(detailed_stats)

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas detalhadas: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Erro ao processar estatísticas',
                'message': str(e)
            }, status=500)