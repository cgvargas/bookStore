from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services import training_service
import os


class Command(BaseCommand):
    help = 'Exporta dados de treinamento do chatbot para formatos específicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            help='Formato de exportação (json ou csv)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Diretório de saída para os arquivos exportados',
        )

    def handle(self, *args, **options):
        # Inicializa o serviço de treinamento
        if not training_service.initialized:
            training_service.initialize()

        format_type = options['format'].lower()
        output_dir = options['output']

        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f"Criado diretório de saída: {output_dir}")

        # Configurar diretório de saída personalizado se especificado
        if output_dir:
            original_data_folder = training_service.data_folder
            training_service.data_folder = output_dir

        # Exportar os dados
        if format_type == 'json':
            self.stdout.write("Exportando dados no formato JSON...")
            export_path = training_service.export_training_data(format='json')
            self.stdout.write(self.style.SUCCESS(f"Dados exportados com sucesso para: {export_path}"))

        elif format_type == 'csv':
            self.stdout.write("Exportando dados no formato CSV...")
            export_paths = training_service.export_training_data(format='csv')
            self.stdout.write(self.style.SUCCESS(f"Dados exportados com sucesso para:"))
            for path in export_paths:
                self.stdout.write(f"  - {path}")

        else:
            self.stdout.write(self.style.ERROR(f"Formato não suportado: {format_type}"))
            self.stdout.write("Formatos suportados: json, csv")

        # Restaurar diretório de dados original
        if output_dir:
            training_service.data_folder = original_data_folder

        # Exibir estatísticas
        stats = training_service.generate_training_statistics()
        self.stdout.write("\nEstatísticas dos dados exportados:")
        self.stdout.write(f"  - Total de conversas: {stats['total_conversations']}")
        self.stdout.write(f"  - Total de itens na base de conhecimento: {stats['total_knowledge_items']}")
        self.stdout.write(f"  - Conversas com feedback: {stats['conversations_with_feedback']}")
        self.stdout.write(f"  - Feedback positivo: {stats['positive_feedback']}")
        self.stdout.write(f"  - Feedback negativo: {stats['negative_feedback']}")