from django.urls import path
from . import views

app_name = 'chatbot_literario'

urlpatterns = [
    path('', views.chatbot_view, name='chat'),
    path('api/message/', views.chatbot_message, name='api_message'),
    path('api/feedback/', views.chatbot_feedback, name='api_feedback'),
    path('widget/', views.chatbot_widget, name='widget'),
]