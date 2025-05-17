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
        updated_count = training_service.update_embeddings(batch_size=batch_size)

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"Embeddings atualizados com sucesso para {updated_count} itens."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Nenhum item precisava de atualização de embeddings."
            ))

        # Exibir estatísticas
        stats = training_service.generate_training_statistics()
        self.stdout.write("\nEstatísticas da base de conhecimento:")
        self.stdout.write(f"  - Total de itens: {stats.get('total_knowledge', 0)}")
        self.stdout.write(f"  - Itens com embeddings: {stats.get('with_embeddings', 0)}")
        self.stdout.write(f"  - Itens sem embeddings: {stats.get('without_embeddings', 0)}")