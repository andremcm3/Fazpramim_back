from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # show the register choice at the main 'register/' path (client vs provider)
    path('register/', views.register_choice, name='register'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/provider/', views.register_provider, name='register_provider'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Use a simple view that accepts GET to perform logout and redirect to login.
    path('logout/', views.logout_view, name='logout'),
]
