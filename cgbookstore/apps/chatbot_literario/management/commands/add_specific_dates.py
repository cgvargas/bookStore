from django.core.management.base import BaseCommand
from cgbookstore.apps.chatbot_literario.services import training_service

class Command(BaseCommand):
    help = 'Adiciona ou atualiza um conjunto consolidado de datas de publicação para livros importantes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Adicionando/atualizando datas de publicação..."))

        if not training_service or not hasattr(training_service, 'initialized'):
            self.stdout.write(self.style.ERROR("ERRO: TrainingService não foi inicializado corretamente."))
            return

        # DADOS CONSOLIDADOS: Uma pergunta canônica por fato.
        publication_dates = [
            {
                'question': 'Qual a data de publicação do livro O Hobbit?',
                'answer': "O livro 'O Hobbit' foi publicado pela primeira vez em 21 de setembro de 1937."
            },
            {
                'question': 'Quando a série de livros O Senhor dos Anéis foi publicada?',
                'answer': "A trilogia 'O Senhor dos Anéis' foi publicada em volumes entre 1954 e 1955."
            },
            {
                'question': 'Quando o livro O Silmarillion foi publicado?',
                'answer': "A obra póstuma 'O Silmarillion', editada por Christopher Tolkien, foi publicada em 1977."
            },
            {
                'question': 'Qual o ano de publicação do livro Dom Casmurro?',
                'answer': "O romance 'Dom Casmurro', de Machado de Assis, foi publicado originalmente em 1899."
            },
            {
                'question': 'Em que ano o livro 1984 de George Orwell foi publicado?',
                'answer': "O livro '1984', de George Orwell, foi publicado em 8 de junho de 1949."
            }
        ]

        created_count = 0
        updated_count = 0

        # LÓGICA SIMPLIFICADA: Usa o serviço que já é idempotente.
        for item_data in publication_dates:
            result = training_service.add_knowledge(
                question=item_data['question'],
                answer=item_data['answer'],
                category='literatura_datas',
                source='comando_add_specific_dates'
            )
            if result.get('created'):
                created_count += 1
            elif result.get('success'):
                updated_count += 1

        # ATUALIZAÇÃO INTELIGENTE DE EMBEDDINGS: Só roda se algo novo foi criado.
        if created_count > 0:
            self.stdout.write(self.style.NOTICE(f"\nAtualizando embeddings para {created_count} novos itens..."))
            # Assumindo que seu training_service tem um método para atualizar todos os embeddings sem um.
            update_result = training_service.update_all_embeddings()
            updated_embeddings_count = update_result.get('updated_count', 0)
            self.stdout.write(f"Embeddings atualizados para {updated_embeddings_count} itens.")

        # Resumo final
        self.stdout.write(self.style.SUCCESS(f"\n✅ Processo concluído:"))
        self.stdout.write(f"  - 📝 Novos itens adicionados: {created_count}")
        self.stdout.write(f"  - 🔄 Itens atualizados: {updated_count}")