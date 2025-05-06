# cgbookstore/apps/core/admin/urls.py
"""
Configuração de URLs para o módulo administrativo personalizado.

Este arquivo contém os patterns de URL para as views administrativas
customizadas, complementando as URLs geradas automaticamente pelo
site admin do Django.
"""

from django.urls import path
from . import views

# URLs dentro do namespace 'admin:'
urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('export/<str:model_name>/', views.export_model_data, name='export-model-data'),
    path('book-statistics/', views.book_statistics_view, name='book-statistics'),
    path('user-activity/', views.user_activity_view, name='user-activity'),
    path('shelf-management/', views.shelf_management_statistics, name='shelf-management'),
    path('cache-management/', views.cache_management_view, name='cache-management'),
    path('admin-logs/', views.admin_log_view, name='admin-logs'),
    path('visual-shelf-manager/', views.visual_shelf_manager, name='visual-shelf-manager'),
    path('quick-shelf-creation/', views.quick_shelf_creation, name='quick-shelf-creation'),
]