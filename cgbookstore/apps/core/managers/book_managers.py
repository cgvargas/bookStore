# cgbookstore/apps/core/managers/book_managers.py

from django.db import models


class BookQuerySet(models.QuerySet):
    def public(self):
        """Retorna apenas os livros com visibilidade PÚBLICA e que estão ativos."""
        # Acessa a enumeração 'Visibility' através do modelo.
        # A importação local evita importações circulares.
        from ..models.book import Book
        return self.filter(visibility=Book.Visibility.PUBLIC, ativo=True)

    def with_related(self):
        """Carrega os relacionamentos comuns para evitar consultas N+1"""
        return self.select_related(
            'categoria',
            'editora',
            'colecao',
        ).prefetch_related(
            'shelves',
            'genero',
            'autor',
        )

    def with_all_related(self):
        """Carrega todos os relacionamentos possíveis para operações detalhadas"""
        return self.with_related().prefetch_related(
            'adaptacoes',
            'temas',
            'personagens',
            'premios',
            'curiosidades',
            'citacoes',
            'recommendation_interactions',
        )

    def by_autor(self, autor_id):
        """Filtra livros por autor de forma otimizada"""
        return self.filter(autor__id=autor_id)

    def search_by_autor(self, nome_autor):
        """Pesquisa livros por nome de autor"""
        return self.filter(autor__nome__icontains=nome_autor)

    def destacados(self):
        """Retorna livros marcados como destaque"""
        return self.filter(e_destaque=True)

    def lancamentos(self):
        """Retorna livros marcados como lançamento"""
        return self.filter(e_lancamento=True)

    def mais_vendidos(self):
        """Retorna livros ordenados por quantidade de vendas"""
        return self.order_by('-quantidade_vendida')

    def mais_acessados(self):
        """Retorna livros ordenados por quantidade de acessos"""
        return self.order_by('-quantidade_acessos')


class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)

    def public(self):
        """Método de atalho para acessar o filtro de livros públicos."""
        return self.get_queryset().public()

    def with_related(self):
        return self.get_queryset().with_related()

    def with_all_related(self):
        return self.get_queryset().with_all_related()

    def by_autor(self, autor_id):
        return self.get_queryset().by_autor(autor_id)

    def search_by_autor(self, nome_autor):
        return self.get_queryset().search_by_autor(nome_autor)

    def destacados(self):
        return self.get_queryset().destacados()

    def lancamentos(self):
        return self.get_queryset().lancamentos()

    def mais_vendidos(self):
        return self.get_queryset().mais_vendidos()

    def mais_acessados(self):
        return self.get_queryset().mais_acessados()