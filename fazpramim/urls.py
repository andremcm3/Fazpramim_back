from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from . import views

def home(request):
    return render(request, 'home.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),   # HTML
    path('api/accounts/', include('accounts.api.api_urls')),  # REST API (apenas isso)
    path('', include('fazpramim.app_urls')),
    path("pesquisar/", views.search_view, name="search"),
]   

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
