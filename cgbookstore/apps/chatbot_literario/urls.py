# chatbot_literario/urls.py - CONFIGURAÇÃO CORRIGIDA (SEM ADMIN URLs)

from django.urls import path
from . import views

app_name = 'chatbot_literario'

urlpatterns = [
    # ===== VIEWS PRINCIPAIS =====
    path('', views.chatbot_view, name='chatbot_view'),
    path('chat/', views.chatbot_view, name='chatbot_chat'),
    path('widget/', views.chatbot_widget, name='chatbot_widget'),

    # ===== APIs DO CHATBOT =====
    # API principal que processa as mensagens do usuário
    path('api/message/', views.chatbot_message, name='chatbot_message'),
    path('api/chat/', views.chatbot_message, name='chatbot_chat_api'),  # Alias

    # ===== APIs UTILITÁRIAS =====
    # API para submeter feedback
    path('api/feedback/', views.chatbot_feedback, name='chatbot_feedback'),
    # API para limpar o contexto da conversa
    path('api/clear-context/', views.clear_conversation_context, name='clear_conversation_context'),

    # As rotas abaixo foram comentadas porque as views correspondentes foram removidas
    # do arquivo views.py para centralizar a lógica e corrigir erros.
    # path('api/personalization/settings/', views.personalization_settings, name='personalization_settings'),
    # path('api/personalization/test/', views.test_personalization, name='test_personalization'),
    # path('api/get-context/', views.get_conversation_context, name='get_conversation_context'),
]

# REMOVIDO: + get_admin_urls()
# MOTIVO: URLs admin são registradas no site.py para evitar conflitos