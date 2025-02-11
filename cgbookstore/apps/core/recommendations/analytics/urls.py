from django.urls import path, include
from . import endpoints

app_name = 'analytics'

urlpatterns = [
    path('track/', endpoints.track_interaction, name='track_interaction'),
    path('stats/user/', endpoints.get_user_stats, name='user_stats'),
    path('stats/global/', endpoints.get_global_stats, name='global_stats'),
    path('dashboard/', include('cgbookstore.apps.core.recommendations.analytics.admin_dashboard.urls', namespace='admin_dashboard')),
]