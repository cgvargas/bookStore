from django.urls import path
from . import views
from . import admin_views

app_name = 'chatbot_literario'

urlpatterns = [
    path('', views.chatbot_view, name='chat'),
    path('api/message/', views.chatbot_message, name='api_message'),
    path('api/feedback/', views.chatbot_feedback, name='api_feedback'),
    path('widget/', views.chatbot_widget, name='widget'),

    # URLs de treinamento - note que os nomes das URLs correspondem aos que são usados no template
    path('treinamento/', admin_views.training_interface, name='chatbot_literario_training'),
    path('treinamento/testar/', admin_views.test_chatbot, name='test_chatbot'),
    path('treinamento/adicionar-conhecimento/', admin_views.add_knowledge_item, name='add_knowledge_item'),
    path('treinamento/adicionar-da-conversa/', admin_views.add_to_knowledge, name='add_to_knowledge'),
    path('treinamento/importar/', admin_views.import_knowledge, name='import_knowledge'),
    path('treinamento/exportar/', admin_views.export_knowledge, name='export_knowledge'),
]