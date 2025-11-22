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
    # Perfil público de prestador (visualização por qualquer usuário)
    path('prestador/<int:pk>/', views.provider_detail, name='provider_detail'),
    # Perfil público de cliente (visualização por qualquer usuário)
    path('cliente/<str:username>/', views.client_detail, name='client_detail'),
    # Criar solicitação ao prestador
    path('prestador/<int:pk>/solicitar/', views.create_request, name='create_request'),
    # Área do prestador: ver solicitações recebidas
    path('meu-perfil/solicitacoes/', views.provider_requests, name='provider_requests'),
    # Área do cliente: ver solicitações enviadas
    path('minhas-solicitacoes/', views.client_requests, name='client_requests'),
    # Detalhe da solicitação (provider ou client podem ver)
    path('solicitacao/<int:pk>/', views.request_detail, name='request_detail'),
    # Chat para solicitação aceita
    path('solicitacao/<int:pk>/chat/', views.chat_view, name='chat_view'),
    # Marcar serviço como concluído
    path('solicitacao/<int:pk>/concluir/', views.complete_service, name='complete_service'),
    # Avaliar serviço concluído
    path('solicitacao/<int:pk>/avaliar/', views.review_service, name='review_service'),
    # API REST para solicitações (DRF)
    path('api/providers/<int:pk>/requests/', views.CreateServiceRequestAPIView.as_view(), name='api_create_request'),
    path('api/provider/requests/', views.ProviderRequestsListAPIView.as_view(), name='api_provider_requests'),
    path('api/requests/<int:pk>/', views.ServiceRequestDetailAPIView.as_view(), name='api_request_detail'),
]
