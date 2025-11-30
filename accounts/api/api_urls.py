from django.urls import path
from . import views

urlpatterns = [
   
    path("login/", views.LoginApi.as_view(), name="api-login"),
    path("logout/", views.LogoutApi.as_view(), name="api-logout"),
    path("register/client/", views.ClientRegisterAPIView.as_view(), name="api-register-client"),
    path("register/provider/", views.ProviderRegisterAPIView.as_view(), name="api-register-provider"),

    path("providers/", views.ProviderListAPIView.as_view(), name="api_provider_list"),
    

    path("providers/<int:pk>/", views.ProviderRetrieveAPIView.as_view(), name="api_provider_detail"),
    

    path("providers-edit/", views.ProviderRetrieveUpdateAPIView.as_view(), name="api_provider_update"),
    

    path("clients/<int:pk>/", views.ClientRetrieveUpdateAPIView.as_view(), name="api_client_detail"),

 
 
    path("providers/<int:pk>/requests/", views.CreateServiceRequestAPIView.as_view(), name="api_create_request"),
    

    path("provider/requests/", views.ProviderRequestsListAPIView.as_view(), name="api_provider_requests"),
    
  
    path("client/requests/", views.ClientRequestsListAPIView.as_view(), name="api_client_requests"),
    
 
    path("requests/<int:pk>/", views.ServiceRequestDetailAPIView.as_view(), name="api_request_detail"),
    
    
    path("requests/<int:pk>/accept/", views.AcceptServiceRequestAPIView.as_view(), name="api_accept_request"),
    

    path("requests/<int:pk>/reject/", views.RejectServiceRequestAPIView.as_view(), name="api_reject_request"),

 
    path("requests/<int:pk>/chat/", views.ChatAPIView.as_view(), name="api_chat"),
    path("requests/<int:pk>/complete/", views.CompleteServiceAPIView.as_view(), name="api_complete_service"),
    path("requests/<int:pk>/review/", views.ReviewCreateAPIView.as_view(), name="api_review_service"),
    path('provider/reviews/', views.ProviderReviewsListAPIView.as_view(), name='provider-reviews'),


    path("portfolio/add/", views.PortfolioAddAPIView.as_view(), name="api_portfolio_add"),
    path("portfolio/<int:pk>/delete/", views.PortfolioDeleteAPIView.as_view(), name="api_portfolio_delete"),
]