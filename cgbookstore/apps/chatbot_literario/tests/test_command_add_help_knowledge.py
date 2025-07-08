# cgbookstore/apps/chatbot_literario/tests/test_command_add_help_knowledge.py

import pytest
from io import StringIO
from django.core.management import call_command
from cgbookstore.apps.chatbot_literario.models import KnowledgeItem


@pytest.mark.django_db
class TestAddHelpKnowledgeCommand:
    """
    Testes para o comando de gerenciamento `add_help_knowledge`.
    """

    def test_command_runs_successfully_and_creates_items(self):
        """
        Verifica se o comando executa sem erros e cria o número esperado de itens de conhecimento.
        """
        assert KnowledgeItem.objects.count() == 0
        out = StringIO()
        call_command('add_help_knowledge', stdout=out)

        assert KnowledgeItem.objects.count() == 13, "O número de itens criados não corresponde ao esperado."

        output = out.getvalue()
        # ✅ CORREÇÃO: Verifica uma parte da nova mensagem de sucesso que é mais genérica.
        assert "✅ Processo concluído." in output, "A mensagem de sucesso não foi encontrada na saída."
        assert "13 novos itens adicionados" in output, "A contagem de itens criados na saída está incorreta."
        assert "📊 Estatísticas atuais da base:" in output, "As estatísticas não foram exibidas."

    def test_created_items_have_correct_data(self):
        """
        Verifica se os dados gravados no banco de dados correspondem exatamente
        aos dados definidos no script do comando.
        """
        call_command('add_help_knowledge')

        help_item = KnowledgeItem.objects.get(question="O que você pode fazer?")
        assert help_item.category == "ajuda"
        # ✅ CORREÇÃO: Esta asserção passará assim que a resposta "..." for corrigida no comando.
        assert "• 📚 Informações sobre livros" in help_item.answer
        assert help_item.source == "manual"

        rec_item = KnowledgeItem.objects.get(question="Me recomenda um livro de ficção científica")
        assert rec_item.category == "recomendacao"
        assert "• Duna - Frank Herbert" in rec_item.answer
        assert rec_item.source == "manual"

        nav_item = KnowledgeItem.objects.get(question="Como adiciono um livro ao carrinho?")
        assert nav_item.category == "navegacao"
        assert "Clique no botão 'Adicionar ao Carrinho'" in nav_item.answer
        assert nav_item.source == "manual"

    # ❌ AÇÃO: O teste `test_running_command_twice_creates_duplicates` foi REMOVIDO.

    def test_command_is_idempotent(self):
        """
        Verifica se o comando é idempotente, ou seja, executá-lo
        mais de uma vez não cria novos registros após a primeira execução.
        """
        assert KnowledgeItem.objects.count() == 0

        # Primeira execução
        out1 = StringIO()
        call_command('add_help_knowledge', stdout=out1)
        assert KnowledgeItem.objects.count() == 13
        assert "13 novos itens adicionados" in out1.getvalue()

        # Segunda execução
        out2 = StringIO()
        call_command('add_help_knowledge', stdout=out2)
        assert KnowledgeItem.objects.count() == 13, "O comando não é idempotente, criou duplicatas."
        # ✅ CORREÇÃO: Verifica a saída da segunda execução.
        assert "0 novos itens adicionados" in out2.getvalue(), "A saída da segunda execução deveria indicar 0 criações."
        assert "13 itens atualizados" in out2.getvalue(), "A saída da segunda execução deveria indicar 13 atualizações."