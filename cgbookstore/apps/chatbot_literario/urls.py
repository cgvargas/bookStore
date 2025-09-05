# cgbookstore/apps/chatbot_literario/urls.py

from django.urls import path, include
from . import admin_views
from . import views


# URLs administrativas para o sistema de treinamento do chatbot
def get_admin_urls():
    """
    Retorna as URLs administrativas do chatbot para serem incluídas no admin do Django.
    Essas URLs são utilizadas pela interface de treinamento e gerenciamento do chatbot.
    """
    return [
        # Interface principal de treinamento - CORREÇÃO: usar training_interface
        path('chatbot/treinamento/', admin_views.training_interface, name='chatbot_training_dashboard'),

        # APIs do simulador de chat - CORREÇÃO: usar test_chatbot
        path('chatbot/treinamento/testar/', admin_views.test_chatbot, name='chatbot_test_api'),

        # Gerenciamento da base de conhecimento
        path('chatbot/treinamento/adicionar-conhecimento/', admin_views.add_knowledge_item, name='add_knowledge_item'),
        path('chatbot/treinamento/adicionar-da-conversa/', admin_views.add_to_knowledge, name='add_from_conversation'),

        # Sistema de embeddings
        path('chatbot/treinamento/update-embeddings/', admin_views.update_embeddings, name='update_embeddings'),

        # Importação e exportação de dados
        path('chatbot/treinamento/importar/', admin_views.import_knowledge, name='import_knowledge'),
        path('chatbot/treinamento/exportar/', admin_views.export_knowledge, name='export_knowledge'),

        # Ferramentas administrativas - CORREÇÃO: usar nomes corretos das funções
        path('chatbot/treinamento/add-specific-dates/', admin_views.run_add_specific_dates, name='add_specific_dates'),
        path('chatbot/treinamento/debug-chatbot/', admin_views.run_debug_chatbot, name='debug_chatbot'),
        path('chatbot/treinamento/clean-knowledge/', admin_views.clean_knowledge_base, name='clean_knowledge'),

        # Relatórios e estatísticas - CORREÇÃO: usar nomes corretos das funções
        path('chatbot/treinamento/statistics/', admin_views.system_statistics, name='advanced_statistics'),
        path('chatbot/treinamento/config/', admin_views.system_config, name='system_config'),
    ]


# URLs padrão da aplicação
app_name = 'chatbot_literario'

urlpatterns = [
    # 2. Definir a URL para a página completa do chat, que estava faltando
    path('', views.chatbot_view, name='chatbot_view'),

    # 3. Agrupar as URLs administrativas sob um prefixo para melhor organização
    path('treinamento/', include(get_admin_urls())),
]