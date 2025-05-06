from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()

@register.simple_tag
def chatbot_widget_url():
    """Retorna a URL do endpoint do widget do chatbot."""
    return reverse('chatbot_literario:widget')

@register.simple_tag
def chatbot_api_url():
    """Retorna a URL do endpoint da API do chatbot."""
    return reverse('chatbot_literario:api_message')

@register.filter
def truncate_message(message, length=50):
    """Trunca uma mensagem para exibição no widget."""
    if len(message) <= length:
        return message
    return message[:length] + '...'

@register.inclusion_tag('chatbot_literario/tags/botao_chatbot.html')
def botao_chatbot():
    """Renderiza apenas o botão flutuante do chatbot."""
    return {
        'widget_url': reverse('chatbot_literario:widget')
    }