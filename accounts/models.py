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
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(
        upload_to="profile_photos/clients/",
        blank=True,
        null=True,
        help_text="Foto de perfil"
    )
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
    phone = models.CharField(max_length=30, blank=True)
    service_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    technical_qualification = models.TextField(blank=True)
    profile_photo = models.ImageField(
        upload_to="profile_photos/providers/",
        blank=True,
        null=True,
        help_text="Foto de perfil"
    )
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


class PortfolioPhoto(models.Model):
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name='portfolio_photos'
    )
    photo = models.ImageField(
        upload_to="portfolio/",
        help_text="Foto do portfólio"
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Portfolio({self.provider.full_name} - {self.created_at.date()})"


class ServiceRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_ACCEPTED, 'Aceito'),
        (STATUS_REJECTED, 'Rejeitado'),
        (STATUS_COMPLETED, 'Concluído'),
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
    completed_by_client = models.BooleanField(default=False)
    completed_by_provider = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ServiceRequest(provider={self.provider.user.username}, client={self.client.username}, status={self.status})"


class ChatMessage(models.Model):
    service_request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"ChatMessage(request={self.service_request.id}, sender={self.sender.username}, at={self.created_at})"


class Review(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest, on_delete=models.CASCADE, related_name='review'
    )
    # Avaliação do cliente sobre o prestador
    client_rating = models.IntegerField(null=True, blank=True, help_text="Avaliação do cliente (0-5 estrelas)")
    client_comment = models.TextField(blank=True, help_text="Comentário do cliente")
    client_photo = models.ImageField(
        upload_to="review_photos/",
        blank=True,
        null=True,
        help_text="Foto do trabalho realizado"
    )
    client_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Avaliação do prestador sobre o cliente
    provider_rating = models.IntegerField(null=True, blank=True, help_text="Avaliação do prestador (0-5 estrelas)")
    provider_comment = models.TextField(blank=True, help_text="Comentário do prestador")
    provider_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review(request={self.service_request.id})"
    
    @property
    def client_has_reviewed(self):
        return self.client_rating is not None
    
    @property
    def provider_has_reviewed(self):
        return self.provider_rating is not None
