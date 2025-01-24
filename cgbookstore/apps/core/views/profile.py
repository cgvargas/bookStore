# cgbookstore/apps/core/views/profile.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
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