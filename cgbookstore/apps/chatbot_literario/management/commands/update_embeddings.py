from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services.training_service import training_service


class Command(BaseCommand):
    help = 'Atualiza embeddings para itens da base de conhecimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamanho do lote para processamento',
        )

    def handle(self, *args, **options):
        # Inicializa o serviço de treinamento
        if not training_service.initialized:
            training_service.initialize()

        batch_size = options['batch_size']

        self.stdout.write("Atualizando embeddings para itens da base de conhecimento...")

        if not training_service.embedding_model:
            self.stdout.write(self.style.WARNING(
                "Modelo de embeddings não disponível. Certifique-se de que a biblioteca sentence-transformers está instalada."
            ))
            self.stdout.write(self.style.WARNING(
                "Execute: pip install sentence-transformers scikit-learn"
            ))
            return

        # Atualizar embeddings
        update_stats = training_service.update_embeddings(batch_size=batch_size)

        # Verificar se ocorreu um erro retornado pelo serviço
        if 'error' in update_stats:
            self.stdout.write(self.style.ERROR(f"Ocorreu um erro: {update_stats['error']}"))
            return

        updated_count = update_stats.get('updated', 0)
        error_count = update_stats.get('errors', 0)

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"Embeddings atualizados com sucesso para {updated_count} itens."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Nenhum item precisava de atualização de embeddings."
            ))

        if error_count > 0:
            self.stdout.write(self.style.WARNING(
                f"{error_count} erro(s) ocorreram. Verifique os logs do sistema."
            ))

        # Exibir estatísticas gerais
        stats = training_service.generate_training_statistics()
        knowledge_stats = stats.get('knowledge_base', {})
        embedding_stats = stats.get('embeddings', {})

        self.stdout.write("\nEstatísticas da base de conhecimento:")
        self.stdout.write(f"  - Total de itens: {knowledge_stats.get('total', 0)}")
        self.stdout.write(f"  - Itens com embeddings: {embedding_stats.get('with_embeddings', 0)}")
        self.stdout.write(f"  - Itens sem embeddings: {embedding_stats.get('without_embeddings', 0)}")