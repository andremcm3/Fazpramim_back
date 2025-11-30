from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
   
    path('register/', views.register_choice, name='register'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/provider/', views.register_provider, name='register_provider'),

 
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),
    path('logout/', views.logout_view, name='logout'),

    
    path('meu-perfil/', views.my_profile, name='my_profile'),

    
    path('prestador/<int:pk>/', views.provider_detail, name='provider_detail'),
    
    
    path('cliente/<str:username>/', views.client_detail, name='client_detail'),


    path('prestador/<int:pk>/solicitar/', views.create_request, name='create_request'),

    path('meu-perfil/solicitacoes/', views.provider_requests, name='provider_requests'),
    path('minhas-solicitacoes/', views.client_requests, name='client_requests'),
    path('solicitacao/<int:pk>/', views.request_detail, name='request_detail'),


    path('solicitacao/<int:pk>/chat/', views.chat_view, name='chat_view'),
    
  
    path('solicitacao/<int:pk>/concluir/', views.complete_service, name='complete_service'),
    
  
    path('solicitacao/<int:pk>/avaliar/', views.review_service, name='review_service'),
    

    path('portfolio/', views.manage_portfolio, name='manage_portfolio'),
]