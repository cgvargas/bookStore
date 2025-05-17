# cgbookstore/apps/core/apps.py
"""
Configuração do aplicativo core para o projeto CG BookStore.

Este módulo define a configuração do aplicativo Django,
incluindo configurações padrão e importação de sinais.
"""

from django.apps import AppConfig
from django.db import connection


class CoreConfig(AppConfig):
    """
    Configuração do aplicativo Core.

    Características:
    - Define campo de chave primária padrão
    - Configura nome do aplicativo
    - Importa sinais quando o aplicativo está pronto
    - Limpa cache de imagens e corrige URLs automaticamente na inicialização
    """
    # Tipo de campo de chave primária padrão para novos modelos
    default_auto_field = 'django.db.models.BigAutoField'

    # Caminho completo do aplicativo
    name = 'cgbookstore.apps.core'

    # Nome legível do aplicativo
    verbose_name = 'Organização'

    def ready(self):
        """
        Método chamado quando o aplicativo está pronto.

        Importa os sinais do aplicativo para registrar
        manipuladores de eventos e outras configurações iniciais.
        Também inicializa a limpeza de cache e correção de URLs de imagens.
        """
        # Importa os sinais definidos no módulo de sinais
        import cgbookstore.apps.core.signals

        # Realiza limpeza de cache e correção de URLs automaticamente
        import os

        # Verifica se está em um processo de servidor web
        # Evita execução duplicada em processos como 'migrate'
        if os.environ.get('RUN_MAIN') == 'true':
            self.clean_image_cache()
            self.update_image_urls()

            # Registra a inicialização
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Aplicativo Core inicializado - Cache de imagens limpo e URLs corrigidas.")

    def clean_image_cache(self):
        """Limpa o cache de imagens para forçar novo carregamento"""
        try:
            from django.conf import settings
            from django.core.cache import cache
            import logging
            logger = logging.getLogger(__name__)

            # Limpar cache de banco de dados
            cache_table = settings.CACHES['default'].get('LOCATION', 'django_cache')
            logger.info(f"Limpando cache da tabela: {cache_table}")

            with connection.cursor() as cursor:
                # Contar registros antes da limpeza
                cursor.execute(
                    f"SELECT COUNT(*) FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s OR cache_key LIKE %s",
                    ['%img_proxy%', '%image_proxy%', '%books.google%']
                )
                count_before = cursor.fetchone()[0]

                # Remover entradas de cache relacionadas a imagens
                cursor.execute(
                    f"DELETE FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s OR cache_key LIKE %s",
                    ['%img_proxy%', '%image_proxy%', '%books.google%']
                )

                # Remover entradas de cache relacionadas a recomendações
                cursor.execute(
                    f"DELETE FROM {cache_table} "
                    f"WHERE cache_key LIKE %s OR cache_key LIKE %s",
                    ['%recommendations%', '%book_%']
                )

                logger.info(f"Limpeza de cache concluída. Removidos {count_before} registros relacionados a imagens.")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao limpar cache na inicialização: {str(e)}")

    def update_image_urls(self):
        """Normaliza URLs de imagens do Google Books no banco de dados"""
        try:
            # Importa o modelo aqui para evitar importações circulares
            from cgbookstore.apps.core.models.book import Book
            from django.db.models import Q
            import re
            import logging
            logger = logging.getLogger(__name__)

            # Encontrar livros com URLs do Google Books
            google_books_urls = Book.objects.filter(
                Q(capa_url__icontains='books.google.com') |
                Q(capa_url__icontains='googleusercontent.com')
            )

            logger.info(f"Verificando {google_books_urls.count()} URLs de capas do Google Books")

            # Número de URLs atualizadas
            updated_count = 0

            # Processar cada livro
            for book in google_books_urls:
                original_url = book.capa_url

                # Extrair o ID do livro
                id_match = re.search(r'id=([^&]+)', original_url)
                if not id_match:
                    continue

                book_id = id_match.group(1)

                # Verificar se a URL já está no formato correto
                if original_url.startswith('https://books.google.com/books/content') and 'imgtk=' not in original_url:
                    continue

                # Construir nova URL em formato padronizado
                new_url = f"https://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1&source=gbs_api"

                # Verificar se a URL original tem edge=curl e adicionar se necessário
                if 'edge=curl' in original_url:
                    new_url += '&edge=curl'

                # Atualizar se diferente
                if original_url != new_url:
                    book.capa_url = new_url
                    book.save(update_fields=['capa_url'])
                    updated_count += 1

            # Registra resultado
            if updated_count > 0:
                logger.info(f"Atualizadas {updated_count} URLs de imagens na inicialização")
            else:
                logger.info("Nenhuma URL precisou ser atualizada")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao atualizar URLs de imagens na inicialização: {str(e)}")