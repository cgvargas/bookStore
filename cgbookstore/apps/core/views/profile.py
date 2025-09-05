# Arquivo: cgbookstore/apps/core/views/profile.py

import json
import logging
import math

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, View, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

from ..forms import UserProfileForm
from ..models import Profile, UserBookShelf, Book, ReadingProgress, ReadingStats

logger = logging.getLogger(__name__)


class ProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'core/profile/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        shelves = UserBookShelf.objects.filter(user=user, book__isnull=False).select_related('book')

        context.update({
            'favoritos': [s for s in shelves if s.book and s.book.pk and s.shelf_type == 'favorito'],
            'lendo': [s for s in shelves if s.book and s.book.pk and s.shelf_type == 'lendo'],
            'vou_ler': [s for s in shelves if s.book and s.book.pk and s.shelf_type == 'vou_ler'],
            'lidos': [s for s in shelves if s.book and s.book.pk and s.shelf_type == 'lido'],
            'total_livros': len(shelves),
        })

        # Manter gamificação desativada por enquanto
        context['stats'] = None
        context['achievements'] = None
        context['total_points'] = 0

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UserProfileForm
    template_name = 'core/profile/profile_form.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self, queryset=None):
        return Profile.objects.get_or_create(user=self.request.user)[0]

    def form_valid(self, form):
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)


class ProfileReadingStatusView(LoginRequiredMixin, ListView):
    """
    View unificada para exibir livros por status, incluindo a lógica de progresso para a prateleira "Lendo".
    """
    model = UserBookShelf
    template_name = 'core/profile/current_readings.html'
    # O template espera 'reading_progress_list' para a lógica completa, então vamos usar esse nome.
    context_object_name = 'reading_progress_list'
    paginate_by = 12

    def get_queryset(self):
        status = self.kwargs.get('status', 'lendo')
        return UserBookShelf.objects.filter(
            user=self.request.user,
            shelf_type=status,
            book__isnull=False
        ).select_related('book').order_by('-added_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        status = self.kwargs.get('status')
        shelves = context['reading_progress_list']  # A queryset já está aqui

        # Se a página for a de "Lendo", aplicamos a lógica de progresso
        if status == 'lendo':
            progress_list = []
            for shelf in shelves:
                if not shelf.book or not shelf.book.pk:
                    continue

                progress, _ = ReadingProgress.objects.get_or_create(
                    user=user,
                    book=shelf.book,
                    defaults={'started_at': timezone.now(), 'current_page': 1}
                )

                total_pages = shelf.book.numero_paginas or 100
                progress_percent = min(round((progress.current_page / total_pages) * 100), 100)

                avg_pages_per_day = 0
                estimated_completion = None

                if progress.started_at and progress.current_page > 1:
                    days_reading = max(1, (timezone.now() - progress.started_at).days)
                    if days_reading > 0:
                        avg_pages_per_day = round(progress.current_page / days_reading)
                        if avg_pages_per_day > 0:
                            pages_left = total_pages - progress.current_page
                            days_left = math.ceil(pages_left / avg_pages_per_day)
                            estimated_completion = timezone.now() + timezone.timedelta(days=days_left)

                progress_list.append({
                    'shelf': shelf,
                    'book': shelf.book,
                    'progress': progress,
                    'progress_percent': progress_percent,
                    'avg_pages_per_day': avg_pages_per_day,
                    'estimated_completion': estimated_completion,
                    'last_read_at': progress.updated_at
                })

            # Ordenar pela data de atualização mais recente
            progress_list.sort(key=lambda x: x.get('last_read_at', timezone.now()), reverse=True)
            context['reading_progress_list'] = progress_list

        # Para outros status, passamos a lista de prateleiras de forma simples
        # O template precisa ser adaptado para lidar com isso
        else:
            # O template espera um dicionário, então vamos simular a estrutura
            context['reading_progress_list'] = [{'book': shelf.book} for shelf in shelves]

        # Título da página
        status_titles = {
            'lendo': 'Lendo Atualmente', 'lido': 'Livros Lidos', 'vou_ler': 'Quero Ler',
            'favorito': 'Favoritos', 'abandonado': 'Abandonados'
        }
        context['title'] = status_titles.get(status, 'Minha Estante')
        context['current_status'] = status
        return context


class UpdateReadingProgressView(LoginRequiredMixin, View):
    """
    View reativada para atualizar o progresso de leitura de um livro.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user
            book_id = data.get('book_id')
            current_page = int(data.get('current_page'))
            started_at_str = data.get('started_at')
            mark_as_finished = data.get('mark_as_finished', False)

            if not all([book_id, current_page, started_at_str]):
                return JsonResponse({'success': False, 'error': 'Dados incompletos.'}, status=400)

            book = get_object_or_404(Book, id=book_id)
            shelf = get_object_or_404(UserBookShelf, user=user, book=book)

            started_at = timezone.datetime.strptime(started_at_str, '%Y-%m-%d').date()

            progress, _ = ReadingProgress.objects.get_or_create(user=user, book=book)

            progress.current_page = current_page
            progress.started_at = started_at
            progress.updated_at = timezone.now()
            progress.save()

            if mark_as_finished:
                shelf.shelf_type = 'lido'
                shelf.save()
                progress.finished_at = timezone.now()
                progress.save()

            return JsonResponse({'success': True, 'message': 'Progresso atualizado!'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso de leitura: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class ProfileCardStyleView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        profile = Profile.objects.get_or_create(user=request.user)[0]
        return JsonResponse(profile.get_card_style())

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            profile = Profile.objects.get_or_create(user=request.user)[0]

            style_fields = [
                'background_color', 'text_color', 'border_color', 'image_style',
                'hover_effect', 'icon_style', 'border_radius', 'shadow_style'
            ]
            current_style = profile.get_card_style()
            new_style = {field: data.get(field, current_style.get(field)) for field in style_fields}

            profile.card_style = new_style
            profile.save()
            return JsonResponse({'success': True, 'styles': profile.get_card_style()})
        except Exception as e:
            logger.error(f"Erro ao salvar estilo de card para {request.user.id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Erro ao salvar estilo'}, status=500)


class ProfilePhotoUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get_or_create(user=request.user)[0]
            if 'profile_photo' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado.'}, status=400)

            photo = request.FILES['profile_photo']
            if photo.size > 5 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'A imagem deve ter no máximo 5MB.'}, status=400)

            if profile.avatar:
                profile.avatar.delete(save=False)

            profile.avatar = photo
            profile.save()

            return JsonResponse({'success': True, 'message': 'Foto atualizada!', 'avatar_url': profile.avatar.url})
        except Exception as e:
            logger.error(f"Erro no upload de foto para {request.user.id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Erro inesperado no servidor.'}, status=500)


class FavoriteQuoteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        profile = Profile.objects.get_or_create(user=request.user)[0]
        return JsonResponse({
            'has_quote': bool(profile.favorite_quote),
            'quote': profile.favorite_quote or "",
            'author': profile.favorite_quote_author or "",
            'source': profile.favorite_quote_source or ""
        })

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            quote = data.get('quote', '').strip()
            author = data.get('author', '').strip()

            if not quote or not author:
                return JsonResponse({'success': False, 'error': 'Citação e autor são obrigatórios.'}, status=400)

            profile = Profile.objects.get_or_create(user=request.user)[0]
            profile.favorite_quote = quote[:500]
            profile.favorite_quote_author = author
            profile.favorite_quote_source = data.get('source', '').strip()
            profile.save()

            return JsonResponse({'success': True, 'message': 'Citação salva com sucesso.'})
        except Exception as e:
            logger.error(f"Erro ao salvar citação para {request.user.id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Erro ao salvar citação.'}, status=500)


class SetCurrentReadingView(LoginRequiredMixin, View):
    """
    View dedicada para definir um livro como a leitura mais recente.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')

            if not book_id:
                return JsonResponse({'success': False, 'error': 'ID do livro não fornecido.'}, status=400)

            # Encontra o registro de progresso para o usuário e o livro
            # Usar get_object_or_404 é uma boa prática aqui
            from django.shortcuts import get_object_or_404
            progress = get_object_or_404(ReadingProgress, user=request.user, book_id=book_id)

            # Apenas atualiza o timestamp. A ordenação na view principal fará o resto.
            progress.updated_at = timezone.now()
            progress.save()

            return JsonResponse({'success': True, 'message': 'Livro definido como leitura atual.'})

        except ReadingProgress.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Progresso de leitura não encontrado para este livro.'}, status=404)
        except Exception as e:
            logger.error(f"Erro ao definir livro atual: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_detailed_stats(request):
    """
    Atualiza e fornece as estatísticas detalhadas do usuário.
    """
    try:
        user = request.user
        reading_stats, created = ReadingStats.objects.get_or_create(user=user)

        # === CHAMADA PARA ATUALIZAR AS ESTATÍSTICAS ===
        reading_stats.update_stats()
        # ===============================================

        # Agora, os dados estarão atualizados no banco de dados
        total_livros_lidos = reading_stats.total_books_read
        total_paginas_lidas = reading_stats.total_pages_read
        books_by_month_data = reading_stats.books_by_month
        livros_por_mes = total_livros_lidos / 12 if total_livros_lidos > 0 else 0

        stats_data = {
            'reading_pace': {
                'yearly': total_livros_lidos,
                'monthly': round(livros_por_mes, 1),
                'weekly': round(livros_por_mes / 4, 1),
                'trend': '+5%'  # Exemplo
            },
            'total_pages_read': total_paginas_lidas,
            'favorite_genre': reading_stats.favorite_genre or 'Não definido',
            'books_by_month': books_by_month_data,
            # ... (outros campos que você queira manter) ...
        }

        return JsonResponse(stats_data)

    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas detalhadas para {request.user.username}: {e}", exc_info=True)
        return JsonResponse({'error': 'Erro ao gerar estatísticas.'}, status=500)


# === VIEW PARA STATUS DE LEITURA ATUAL (ERRO 404) ===
@login_required
def get_current_reading_status(request):
    """
    Fornece detalhes do livro que o usuário está lendo atualmente em formato JSON.
    """
    try:
        user = request.user
        current_reading = UserBookShelf.objects.filter(user=user, shelf_type='lendo').select_related('book').first()

        if current_reading:
            book = current_reading.book
            data = {
                'title': book.titulo,
                'author': book.autor,
                'coverUrl': book.get_capa_url(),
                'progress': 50,  # Exemplo: Implementar lógica de progresso
                'totalPages': book.numero_paginas or 0,
            }
            return JsonResponse(data)
        else:
            # Retorna 404 se o usuário não estiver lendo nada,
            # para que o frontend possa tratar isso corretamente.
            return JsonResponse({'error': 'Nenhum livro sendo lido no momento'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_user_achievements(request):
    """
    Fornece as conquistas do usuário em formato JSON.
    """
    user = request.user

    # Exemplo de dados - você precisará implementar a busca real no seu modelo
    # Supondo que você tenha um modelo UserAchievement

    # unlocked_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    # unlocked_list = []
    # for ua in unlocked_achievements:
    #     ach_dict = model_to_dict(ua.achievement)
    #     ach_dict['achieved_at'] = ua.achieved_at
    #     unlocked_list.append(ach_dict)

    # Usando dados de exemplo por enquanto
    unlocked_list = [
        {'name': 'Leitor Iniciante', 'description': 'Leu seu primeiro livro.', 'icon': 'bi-book', 'tier': 'Bronze',
         'achieved_at': '2025-08-01T10:00:00Z'},
        {'name': 'Rato de Biblioteca', 'description': 'Adicionou 10 livros à sua estante.', 'icon': 'bi-bookshelf',
         'tier': 'Bronze', 'achieved_at': '2025-08-15T12:30:00Z'},
    ]

    in_progress_list = [
        {'name': 'Maratonista', 'description': 'Leia 5 livros em um mês.', 'icon': 'bi-speedometer2', 'tier': 'Silver'},
    ]

    data = {
        'unlocked': unlocked_list,
        'in_progress': in_progress_list,
    }

    return JsonResponse(data)