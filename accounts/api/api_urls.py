from django.urls import path
from . import views

urlpatterns = [
    # ======================
    # 🔐 Autenticação & Conta
    # ======================
    path("login/", views.LoginApi.as_view(), name="api-login"),
    path("logout/", views.LogoutApi.as_view(), name="api-logout"),
    path("register/client/", views.ClientRegisterAPIView.as_view(), name="api-register-client"),
    path("register/provider/", views.ProviderRegisterAPIView.as_view(), name="api-register-provider"),

    # ======================
    # 🔍 Busca Pública
    # ======================
    # Lista de prestadores para a tela de Search (Search.tsx)
    # Ex: GET /api/accounts/providers/?search=encanador
    path("providers/", views.ProviderListAPIView.as_view(), name="api_provider_list"),

    # ======================
    # 🛠️ Solicitações de Serviço
    # ======================
    
    # 1. Criar solicitação (Cliente -> Prestador)
    # Ex: POST /api/accounts/providers/5/requests/
    path("providers/<int:pk>/requests/", 
         views.CreateServiceRequestAPIView.as_view(), 
         name="api_create_request"),

    # 2. Listar solicitações (Painel do Prestador)
    # Ex: GET /api/accounts/provider/requests/
    path("provider/requests/", 
         views.ProviderRequestsListAPIView.as_view(), 
         name="api_provider_requests"),

    # 3. Detalhes e Atualização de Status (Aceitar/Rejeitar)
    # Ex: GET/PATCH /api/accounts/requests/10/
    path("requests/<int:pk>/", 
         views.ServiceRequestDetailAPIView.as_view(), 
         name="api_request_detail"),

    # ======================
    # 💬 Chat & Interações (NOVOS)
    # ======================
    
    # Chat: GET (mensagens) e POST (nova mensagem)
    # Ex: GET /api/accounts/requests/10/chat/
    path("requests/<int:pk>/chat/", 
         views.ChatAPIView.as_view(), 
         name="api_chat"),
    
    # Finalizar serviço (Dupla confirmação)
    # Ex: POST /api/accounts/requests/10/complete/
    path("requests/<int:pk>/complete/", 
         views.CompleteServiceAPIView.as_view(), 
         name="api_complete_service"),
    
    # Enviar Avaliação (Review) com foto
    # Ex: POST /api/accounts/requests/10/review/
    path("requests/<int:pk>/review/", 
         views.ReviewCreateAPIView.as_view(), 
         name="api_review_service"),
]