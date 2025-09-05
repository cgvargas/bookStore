# cgbookstore/config/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cgbookstore.apps.core.admin import admin_site

urlpatterns = [
    # Django Admin customizado - DEVE ESTAR PRIMEIRO
    path('admin/', admin_site.urls),

    # URLs das aplicações principais (mantendo estrutura original)
    path('', include('cgbookstore.apps.core.urls', namespace='core')),

    path('api/recommendations/',
         include('cgbookstore.apps.core.recommendations.api.urls', namespace='recommendations')),
    path('api/analytics/', include('cgbookstore.apps.core.recommendations.analytics.urls', namespace='analytics')),

    path('chatbot/', include('cgbookstore.apps.chatbot_literario.urls', namespace='chatbot_literario')),
]

# Adicionar URLs administrativas do chatbot DE FORMA SEGURA
try:
    # Importar apenas quando necessário para evitar circular import
    from cgbookstore.apps.chatbot_literario.urls import get_admin_urls

    # URLs administrativas customizadas do chatbot
    # Essas URLs são incluídas diretamente para funcionarem no admin customizado
    admin_chatbot_urls = [path('admin/', include([url])) for url in get_admin_urls()]
    urlpatterns.extend(admin_chatbot_urls)

except ImportError as e:
    # Log do erro mas não quebra a aplicação
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(f"Não foi possível carregar URLs administrativas do chatbot: {e}")

# URLs de desenvolvimento (apenas em DEBUG)
if settings.DEBUG:
    # Servir arquivos de mídia em desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)