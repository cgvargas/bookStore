# urls.py (apps/core/urls.py)
from django.urls import path
from django.contrib.auth import views as auth_views
from .views.general import (
    register,
    index,
    sobre,
    contato,
    politica_privacidade,
    termos_uso
)

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('sobre/', sobre, name='sobre'),
    path('contato/', contato, name='contato'),
    path('politica-privacidade/', politica_privacidade, name='politica_privacidade'),
    path('termos-uso/', termos_uso, name='termos_uso'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
