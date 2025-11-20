# accounts/api/api_urls.py

from django.urls import path
from . import views
# Importamos as views, agora assumindo que as novas estão no seu views.py
from .views import (
    LoginApi, 
    LogoutApi, 
    ClientRegisterAPIView,      # 🆕 NOVO
    ProviderRegisterAPIView,    # 🆕 NOVO
    CreateServiceRequestAPIView, 
    ProviderRequestsListAPIView, 
    ServiceRequestDetailAPIView
)

urlpatterns = [
    # ======================
    # Autenticação
    # ======================
    
    # 🆕 ROTAS ESPECÍFICAS (Substituindo a antiga 'register/')
    # O frontend chama esta URL: /api/accounts/register/client/
    path("register/client/", views.ClientRegisterAPIView.as_view(), name="api-register-client"),
    
    # Rota futura para prestadores
    path("register/provider/", views.ProviderRegisterAPIView.as_view(), name="api-register-provider"),
    
    # Login e Logout
    path("login/", views.LoginApi.as_view(), name="api-login"),
    path("logout/", views.LogoutApi.as_view(), name="api-logout"),

    # ======================
    # Solicitações de serviço (API)
    # ======================
    path("providers/<int:pk>/requests/", 
          views.CreateServiceRequestAPIView.as_view(), 
          name="api_create_request"),

    path("provider/requests/", 
          views.ProviderRequestsListAPIView.as_view(), 
          name="api_provider_requests"),

    path("requests/<int:pk>/", 
          views.ServiceRequestDetailAPIView.as_view(), 
          name="api_request_detail"),
]