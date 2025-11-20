from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Registro ---
    path('register/', views.register_choice, name='register'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/provider/', views.register_provider, name='register_provider'),

    # --- Autenticação ---
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),
    path('logout/', views.logout_view, name='logout'),

    # --- Perfis ---
    path('meu-perfil/', views.my_profile, name='my_profile'),

    # Perfil público de prestador
    path('prestador/<int:pk>/', views.provider_detail, name='provider_detail'),

    # Criar solicitação via formulário HTML (não API)
    path('prestador/<int:pk>/solicitar/', views.create_request, name='create_request'),

    # --- Solicitações ---
    path('meu-perfil/solicitacoes/', views.provider_requests, name='provider_requests'),
    path('minhas-solicitacoes/', views.client_requests, name='client_requests'),
    path('solicitacao/<int:pk>/', views.request_detail, name='request_detail'),

    # --- Chat HTML ---
    path('solicitacao/<int:pk>/chat/', views.chat_view, name='chat_view'),
]
