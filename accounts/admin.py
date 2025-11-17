from django.contrib import admin
from .models import ClientProfile, ProviderProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'full_name', 'cpf')


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'full_name', 'professional_email')
