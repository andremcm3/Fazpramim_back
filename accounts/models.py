from django.db import models
from django.contrib.auth.models import User


class ClientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )
    full_name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=20)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    identity_document = models.FileField(
        upload_to="documents/clients/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"ClientProfile({self.user.username})"


class ProviderProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="provider_profile"
    )
    full_name = models.CharField(max_length=255)
    professional_email = models.EmailField()
    service_address = models.TextField(blank=True)
    technical_qualification = models.TextField(blank=True)
    identity_document = models.FileField(
        upload_to="documents/providers/identity/",
        blank=True,
        null=True,
    )
    certifications = models.FileField(
        upload_to="documents/providers/certifications/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"ProviderProfile({self.user.username})"
