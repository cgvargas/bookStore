# cgbookstore/apps/core/views/profile.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
import json
import os
from ..forms import UserProfileForm
from ..models import Profile, UserBookShelf


class ProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'core/profile/profile.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Buscar livros por tipo de prateleira
        context.update({
            'favoritos': UserBookShelf.get_shelf_books(user, 'favorito'),
            'lendo': UserBookShelf.get_shelf_books(user, 'lendo'),
            'vou_ler': UserBookShelf.get_shelf_books(user, 'vou_ler'),
            'lidos': UserBookShelf.get_shelf_books(user, 'lido'),
            'recomendacoes': [],  # Substituir quando o sistema de recomendação estiver pronto
            'total_livros': UserBookShelf.objects.filter(user=user).count(),
        })
        return context

    def get_object(self, queryset=None):
        return self.request.user.profile


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UserProfileForm
    template_name = 'core/profile/profile_form.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Perfil atualizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar perfil. Por favor, verifique os dados.')
        return super().form_invalid(form)


class ProfileCardStyleView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        """Retorna o estilo atual do card do perfil."""
        return JsonResponse(request.user.profile.get_card_style())

    def post(self, request, *args, **kwargs):
        """Atualiza o estilo do card do perfil."""
        try:
            data = json.loads(request.body.decode('utf-8'))
            profile = request.user.profile

            # Validar dados recebidos
            required_fields = ['background_color', 'text_color', 'border_color',
                               'image_style', 'hover_effect', 'icon_style']

            for field in required_fields:
                if field not in data:
                    data[field] = profile.get_card_style().get(field)

            profile.card_style = data
            profile.save()

            return JsonResponse({
                'success': True,
                'styles': profile.get_card_style()
            })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Erro ao decodificar JSON: ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ProfilePhotoUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            if 'profile_photo' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhuma foto enviada'
                }, status=400)

            photo = request.FILES['profile_photo']

            # Validar tipo do arquivo
            if not photo.content_type.startswith('image/'):
                return JsonResponse({
                    'success': False,
                    'error': 'O arquivo deve ser uma imagem'
                }, status=400)

            # Validar tamanho (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'A imagem deve ter no máximo 5MB'
                }, status=400)

            # Se já existir uma foto, remover
            if request.user.foto:
                if os.path.exists(request.user.foto.path):
                    os.remove(request.user.foto.path)

            # Salvar nova foto
            request.user.foto = photo
            request.user.save()

            return JsonResponse({
                'success': True,
                'message': 'Foto atualizada com sucesso'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)