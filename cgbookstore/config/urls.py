"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# cgbookstore/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cgbookstore.apps.core.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('cgbookstore.apps.core.urls')),

    # APIs
    path('api/recommendations/', include('cgbookstore.apps.core.recommendations.api.urls', namespace='recommendations')),
    path('api/analytics/', include('cgbookstore.apps.core.recommendations.analytics.urls', namespace='analytics')),
]

# Registro de arquivos estáticos e de mídia (somente em DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
