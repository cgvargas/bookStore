"""
Views para gerenciar exibição de autores e seções de autores.

Este módulo contém views relacionadas à exibição de autores, incluindo
listas, detalhes e seções específicas na página inicial.
"""

import logging
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView
from django.http import Http404

from ..models.author import Author, AuthorSection

logger = logging.getLogger(__name__)


class AuthorSectionView(TemplateView):
    """
    View para processar e renderizar seções de autores na página inicial.
    """
    template_name = 'core/components/author_section.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obter a ID da seção do contexto passado pela template
        section_id = kwargs.get('section_id')

        if not section_id:
            logger.warning("Nenhum ID de seção fornecido para AuthorSectionView")
            raise Http404("Seção de autores não encontrada")

        try:
            # Obter a seção de autores - corrigido para buscar pelo ID correto
            section = get_object_or_404(AuthorSection, id=section_id, ativo=True)

            # Alternativamente, se section_id se refere ao HomeSection relacionado:
            # section = get_object_or_404(AuthorSection, section_id=section_id, ativo=True)

            # Obter os autores conforme configuração da seção
            authors = section.get_autores()

            # Adicionar ao contexto
            context['section'] = section
            context['authors'] = authors

            return context

        except Exception as e:
            logger.error(f"Erro ao processar seção de autores: {str(e)}")
            raise Http404("Erro ao processar seção de autores")


class AuthorListView(ListView):
    """
    View para listar todos os autores ativos.
    """
    model = Author
    template_name = 'core/author/author_list.html'
    context_object_name = 'authors'
    paginate_by = 12

    def get_queryset(self):
        """Retorna apenas autores ativos, ordenados por nome"""
        return Author.objects.filter(ativo=True).order_by('nome', 'sobrenome')


class AuthorDetailView(DetailView):
    """
    View para exibir detalhes de um autor específico e seus livros.
    """
    model = Author
    template_name = 'core/author/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adicionar livros do autor ao contexto
        context['livros'] = self.object.books.filter(ativo=True)  # Melhor filtrar por livros ativos
        return context