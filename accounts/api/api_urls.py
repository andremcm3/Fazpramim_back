from django.urls import path
from . import views

urlpatterns = [
    # ======================
    # Autenticação
    # ======================
    path("register/", views.RegisterApi.as_view(), name="api-register"),
    path("login/", views.LoginApi.as_view(), name="api-login"),
    path("logout/", views.LogoutApi.as_view(), name="api-logout"),

    # ======================
    # Solicitações de serviço (API)
    # ======================
    # Cliente cria solicitação para um prestador
    path("providers/<int:pk>/requests/", 
         views.CreateServiceRequestAPIView.as_view(), 
         name="api_create_request"),

    # Prestador vê as solicitações recebidas
    path("provider/requests/", 
         views.ProviderRequestsListAPIView.as_view(), 
         name="api_provider_requests"),

    # Ver detalhes de uma solicitação (e permitir aceitar/rejeitar via API)
    path("requests/<int:pk>/", 
         views.ServiceRequestDetailAPIView.as_view(), 
         name="api_request_detail"),
]
