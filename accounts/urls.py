from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # escolha do tipo de cadastro
    path('register/', views.register_choice, name='register'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/provider/', views.register_provider, name='register_provider'),

    # autenticação
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),
    path('logout/', views.logout_view, name='logout'),

    # >>> NOVO: página "Meu Perfil"
    path('meu-perfil/', views.my_profile, name='my_profile'),
]
