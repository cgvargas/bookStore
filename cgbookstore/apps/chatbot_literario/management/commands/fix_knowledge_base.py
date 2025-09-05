from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem
from cgbookstore.apps.chatbot_literario.services import training_service
import json


class Command(BaseCommand):
    help = 'Corrige problemas na base de conhecimento do chatbot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--convert-embeddings',
            action='store_true',
            help='Converte embeddings de string para lista/JSON',
        )
        parser.add_argument(
            '--update-embeddings',
            action='store_true',
            help='Atualiza embeddings para itens sem embedding',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Executa todas as correções disponíveis',
        )

    def handle(self, *args, **options):
        # Inicializar serviço de treinamento
        if not training_service.initialized:
            training_service.initialize()

        if options['fix_all'] or options['convert_embeddings']:
            self.convert_embeddings()

        if options['fix_all'] or options['update_embeddings']:
            self.update_embeddings()

        # Exibir estatísticas após correções
        stats = training_service.generate_training_statistics()
        self.stdout.write("\nEstatísticas após correções:")
        self.stdout.write(f"  - Total de itens: {stats.get('total_knowledge', 0)}")
        self.stdout.write(f"  - Itens com embeddings: {stats.get('with_embeddings', 0)}")
        self.stdout.write(f"  - Itens sem embeddings: {stats.get('without_embeddings', 0)}")

    def convert_embeddings(self):
        """Converte embeddings de formato string para JSON/lista."""
        self.stdout.write("Verificando embeddings em formato incorreto...")

        count = 0
        items = KnowledgeItem.objects.all()

        for item in items:
            if item.embedding and isinstance(item.embedding, str):
                try:
                    # Tentar converter de string para lista
                    if item.embedding.startswith('[') and item.embedding.endswith(']'):
                        # Parece ser uma representação de lista em string
                        embedding_list = json.loads(item.embedding)
                        item.embedding = embedding_list
                        item.save(update_fields=['embedding'])
                        count += 1
                    else:
                        # Não é um formato reconhecível, definir como None para regenerar
                        item.embedding = None
                        item.save(update_fields=['embedding'])
                        count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"Erro ao converter embedding para item ID {item.id}: {str(e)}"
                    ))
                    # Definir como None para regenerar
                    item.embedding = None
                    item.save(update_fields=['embedding'])
                    count += 1

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Corrigidos {count} embeddings em formato incorreto."))
        else:
            self.stdout.write("Nenhum embedding em formato incorreto encontrado.")

    def update_embeddings(self):
        """Atualiza embeddings para itens sem embedding."""
        if not training_service.embedding_model:
            self.stdout.write(self.style.WARNING(
                "Modelo de embeddings não disponível. Instale sentence-transformers para habilitar esta funcionalidade."
            ))
            return

        self.stdout.write("Atualizando embeddings para itens sem embedding...")

        # Chamar o método do serviço de treinamento
        batch_size = 100
        updated_count = training_service.update_embeddings(batch_size=batch_size)

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Atualizados {updated_count} embeddings."))
        else:
            self.stdout.write("Nenhum item precisava de atualização de embedding.")