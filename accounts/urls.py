from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Estas rotas servem páginas HTML (Templates Django)
# A API REST (usada pelo React) está em accounts/api/api_urls.py

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
    
    # Perfil público de cliente (visualização por qualquer usuário)
    path('cliente/<str:username>/', views.client_detail, name='client_detail'),

    # --- Solicitações (HTML Forms) ---
    # Criar solicitação ao prestador
    path('prestador/<int:pk>/solicitar/', views.create_request, name='create_request'),

    path('meu-perfil/solicitacoes/', views.provider_requests, name='provider_requests'),
    path('minhas-solicitacoes/', views.client_requests, name='client_requests'),
    path('solicitacao/<int:pk>/', views.request_detail, name='request_detail'),

    # --- Chat & Ações (HTML) ---
    path('solicitacao/<int:pk>/chat/', views.chat_view, name='chat_view'),
    
    # Marcar serviço como concluído
    path('solicitacao/<int:pk>/concluir/', views.complete_service, name='complete_service'),
    
    # Avaliar serviço concluído
    path('solicitacao/<int:pk>/avaliar/', views.review_service, name='review_service'),
    
    # Gerenciar portfólio (prestador)
    path('portfolio/', views.manage_portfolio, name='manage_portfolio'),
]