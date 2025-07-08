import pytest
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem


@pytest.mark.django_db
class TestAddSpecificDatesCommand:
    """
    Testes para a versão REVISADA do comando add_specific_dates.
    """

    def test_command_creates_consolidated_items(self):
        """
        Verifica se o comando cria um conjunto consolidado e não redundante de itens.
        """
        assert KnowledgeItem.objects.count() == 0
        out = StringIO()

        with patch('cgbookstore.apps.chatbot_literario.services.TrainingService.update_all_embeddings') as mock_update:
            mock_update.return_value = {'updated_count': 5}
            call_command('add_specific_dates', stdout=out)

        assert KnowledgeItem.objects.count() == 5
        output = out.getvalue()

        # ✅ CORREÇÃO: A asserção agora corresponde exatamente à saída.
        assert "✅ Processo concluído:" in output
        assert "📝 Novos itens adicionados: 5" in output
        assert "Embeddings atualizados para 5 itens." in output
        mock_update.assert_called_once()

    def test_command_is_idempotent(self):
        """
        Verifica se rodar o comando duas vezes não cria duplicatas.
        """
        assert KnowledgeItem.objects.count() == 0

        with patch('cgbookstore.apps.chatbot_literario.services.TrainingService.update_all_embeddings'):
            call_command('add_specific_dates')
        assert KnowledgeItem.objects.count() == 5

        out = StringIO()
        with patch('cgbookstore.apps.chatbot_literario.services.TrainingService.update_all_embeddings') as mock_update:
            call_command('add_specific_dates', stdout=out)

        assert KnowledgeItem.objects.count() == 5
        output = out.getvalue()

        # ✅ CORREÇÃO: As asserções agora correspondem exatamente à formatação da saída.
        assert "📝 Novos itens adicionados: 0" in output
        assert "🔄 Itens atualizados: 5" in output
        mock_update.assert_not_called()

    def test_data_is_correct(self):
        """
        Verifica se os dados de um dos itens foram gravados corretamente.
        """
        # Este teste já estava passando, não precisa de alterações.
        with patch('cgbookstore.apps.chatbot_literario.services.TrainingService.update_all_embeddings'):
            call_command('add_specific_dates')

        item_hobbit = KnowledgeItem.objects.get(question__icontains="hobbit")
        assert item_hobbit.answer == "O livro 'O Hobbit' foi publicado pela primeira vez em 21 de setembro de 1937."
        assert item_hobbit.category == "literatura_datas"
        assert item_hobbit.source == "comando_add_specific_dates"