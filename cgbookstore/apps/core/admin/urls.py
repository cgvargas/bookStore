# cgbookstore/apps/core/admin/urls.py
"""
Configuração de URLs para o módulo administrativo personalizado.

Este arquivo contém os patterns de URL para as views administrativas
customizadas, complementando as URLs geradas automaticamente pelo
site admin do Django.
"""

from django.urls import path, include
from . import views
from .diagnostics_admin import diagnostics_admin

# URLs dentro do namespace 'admin:'
urlpatterns = [
    # URLs existentes
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('export/<str:model_name>/', views.export_model_data, name='export-model-data'),
    path('book-statistics/', views.book_statistics_view, name='book-statistics'),
    path('user-activity/', views.user_activity_view, name='user-activity'),
    path('shelf-management/', views.shelf_management_statistics, name='shelf-management'),
    path('cache-management/', views.cache_management_view, name='cache-management'),
    path('admin-logs/', views.admin_log_view, name='admin-logs'),
    path('visual-shelf-manager/', views.visual_shelf_manager, name='visual-shelf-manager'),
    path('quick-shelf-creation/', views.quick_shelf_creation, name='quick-shelf-creation'),

    # URLs de Diagnósticos
    path('diagnostics/', diagnostics_admin.diagnostics_dashboard, name='diagnostics_dashboard'),
    path('diagnostics/performance/', diagnostics_admin.performance_diagnostics, name='performance_diagnostics'),
    path('diagnostics/redis-info/', diagnostics_admin.redis_info, name='redis_info'),
    path('diagnostics/fix-covers/', diagnostics_admin.fix_corrupted_covers, name='fix_corrupted_covers'),
    path('diagnostics/debug-books/', diagnostics_admin.debug_book_images, name='debug_book_images'),
    path('diagnostics/debug-recommendations/', diagnostics_admin.debug_recommendations, name='debug_recommendations'),
    path('diagnostics/system-health/', diagnostics_admin.system_health_check, name='system_health_check'),
    path('diagnostics/clear-cache/', diagnostics_admin.clear_cache, name='clear_cache'),
    path('diagnostics/task-status/<str:task_id>/', diagnostics_admin.task_status, name='task_status'),
]