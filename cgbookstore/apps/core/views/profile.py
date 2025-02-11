# cgbookstore/apps/core/views/profile.py
"""
Módulo de views para gerenciamento de perfil de usuário.

Funcionalidades:
- Visualização de perfil
- Atualização de perfil
- Personalização de estilo de card
- Atualização de foto de perfil
"""

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
    """
    View para visualização do perfil do usuário.

    Características:
    - Requer login
    - Exibe informações detalhadas do perfil
    - Carrega livros por diferentes prateleiras
    """
    model = Profile
    template_name = 'core/profile/profile.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        """
        Prepara dados de contexto do perfil.

        Etapas:
        1. Carrega livros por prateleira
        2. Calcula total de livros

        Returns:
            dict: Contexto com informações do perfil e livros
        """
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
        """
        Retorna o perfil do usuário logado.

        Returns:
            Profile: Perfil do usuário atual
        """
        return self.request.user.profile


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
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        """
        Retorna o perfil do usuário logado para edição.

        Returns:
            Profile: Perfil do usuário atual
        """
        return self.request.user.profile

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
        messages.error(self.request, 'Erro ao atualizar perfil. Por favor, verifique os dados.')
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
        return JsonResponse(request.user.profile.get_card_style())

    def post(self, request, *args, **kwargs):
        """
        Atualiza o estilo do card do perfil.

        Etapas:
        1. Decodifica dados JSON
        2. Valida campos obrigatórios
        3. Atualiza estilo do perfil

        Returns:
            JsonResponse: Resultado da atualização
        """
        try:
            # Decodificar dados JSON
            data = json.loads(request.body.decode('utf-8'))
            profile = request.user.profile

            # Campos obrigatórios para estilo do card
            required_fields = ['background_color', 'text_color', 'border_color',
                               'image_style', 'hover_effect', 'icon_style']

            # Preencher campos ausentes com valores padrão
            for field in required_fields:
                if field not in data:
                    data[field] = profile.get_card_style().get(field)

            # Salvar novo estilo
            profile.card_style = data
            profile.save()

            return JsonResponse({
                'success': True,
                'styles': profile.get_card_style()
            })
        except json.JSONDecodeError as e:
            # Tratamento de erro de decodificação JSON
            return JsonResponse({
                'success': False,
                'error': 'Erro ao decodificar JSON: ' + str(e)
            }, status=400)
        except Exception as e:
            # Tratamento de erros gerais
            return JsonResponse({
                'success': False,
                'error': str(e)
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
            # Tratamento de erros gerais
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)