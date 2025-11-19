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


class ServiceRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_ACCEPTED, 'Aceito'),
        (STATUS_REJECTED, 'Rejeitado'),
    ]

    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name='requests'
    )
    client = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='sent_requests'
    )
    description = models.TextField()
    desired_datetime = models.DateTimeField(blank=True, null=True)
    proposed_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ServiceRequest(provider={self.provider.user.username}, client={self.client.username}, status={self.status})"
