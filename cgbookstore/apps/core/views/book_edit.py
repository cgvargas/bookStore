# cgbookstore/apps/core/views/book_edit.py
"""
View para edição de livros em uma página dedicada
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import UpdateView
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from ..models.book import Book, UserBookShelf
from ..forms import BookForm

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class BookEditView(UpdateView):
    """View para edição de livros em uma página dedicada"""
    model = Book
    form_class = BookForm
    template_name = 'core/book_edit.html'
    context_object_name = 'book'

    def dispatch(self, request, *args, **kwargs):
        """Verifica se o usuário tem permissão para editar o livro"""
        book = self.get_object()

        # Verifica se o usuário tem permissão para editar
        user_shelf = UserBookShelf.objects.filter(
            user=request.user,
            book=book
        ).first()

        # Apenas permite edição se o livro está na prateleira do usuário
        # ou se o usuário é staff
        if not user_shelf and not request.user.is_staff:
            messages.error(request, "Você não tem permissão para editar este livro.")
            return redirect('book_detail', pk=book.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)

        # Obtém a prateleira atual do livro
        user_shelf = UserBookShelf.objects.filter(
            user=self.request.user,
            book=self.object
        ).first()

        if user_shelf:
            context['shelf'] = user_shelf.shelf_type
            context['shelf_display'] = user_shelf.get_shelf_type_display()

        return context

    def form_valid(self, form):
        """Processa o formulário após validação"""
        try:
            # Processa a imagem de capa se foi enviada
            if 'capa' in self.request.FILES:
                self.object.capa = self.request.FILES['capa']

            # Salva o livro
            self.object = form.save()

            # Mensagem de sucesso
            messages.success(self.request, f'Livro "{self.object.titulo}" atualizado com sucesso!')

            # Redireciona para a página de detalhes
            return redirect('book_detail', pk=self.object.pk)

        except Exception as e:
            logger.error(f"Erro ao atualizar livro: {str(e)}")
            messages.error(self.request, "Ocorreu um erro ao atualizar o livro.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Trata formulário inválido"""
        messages.error(self.request, "Por favor, corrija os erros do formulário.")
        return super().form_invalid(form)

    def get_success_url(self):
        """URL de redirecionamento após sucesso"""
        return reverse('book_detail', kwargs={'pk': self.object.pk})