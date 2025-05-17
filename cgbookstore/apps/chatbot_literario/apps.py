from django.apps import AppConfig

class ChatbotLiterarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cgbookstore.apps.chatbot_literario'  # Nome completo incluindo o caminho
    verbose_name = 'Chatbot Literário'
    app_label = 'chatbot_literario'  # Adicione isto para garantir o app_label correto
