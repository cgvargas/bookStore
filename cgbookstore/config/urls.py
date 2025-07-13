# cgbookstore/config/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cgbookstore.apps.core.admin import admin_site
from cgbookstore.apps.chatbot_literario.admin_views import get_admin_urls

# A linha "app_name = 'core'" foi removida daqui, pois não tem efeito e pode causar confusão.

urlpatterns = [
    path('admin/', admin_site.urls),
    path('admin/chatbot/', include(get_admin_urls())),

    # CORREÇÃO: Usando o método padrão e mais limpo para incluir as URLs
    # do aplicativo 'core' e atribuir a elas o namespace 'core'.
    path('', include('cgbookstore.apps.core.urls', namespace='core')),

    # APIs (Mantidas separadas para organização)
    path('api/recommendations/',
         include('cgbookstore.apps.core.recommendations.api.urls', namespace='recommendations')),
    path('api/analytics/', include('cgbookstore.apps.core.recommendations.analytics.urls', namespace='analytics')),

    path('chatbot/', include('cgbookstore.apps.chatbot_literario.urls', namespace='chatbot_literario')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)