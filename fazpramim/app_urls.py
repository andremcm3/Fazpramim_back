from django.urls import path
from . import views

urlpatterns = [
    path("pesquisar/", views.search_view, name="search"),
]
