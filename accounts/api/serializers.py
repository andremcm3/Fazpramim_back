from rest_framework import serializers
from accounts.models import ServiceRequest, ProviderProfile, ClientProfile, ChatMessage, Review, PortfolioPhoto
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.db.models import Avg

# =======================================================
# 👤 SERIALIZERS DE USUÁRIO
# =======================================================

class UserSerializer(serializers.ModelSerializer):
    is_provider = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_provider", "full_name")
    
    def get_is_provider(self, obj):
        return hasattr(obj, 'provider_profile')
    
    def get_full_name(self, obj):
        if hasattr(obj, 'provider_profile'):
            return obj.provider_profile.full_name
        elif hasattr(obj, 'client_profile'):
            return obj.client_profile.full_name
        return obj.username

UserSummarySerializer = UserSerializer

class ProviderSummarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = ProviderProfile
        fields = ("id", "full_name", "user")

# =======================================================
# 🔍 SERIALIZERS PARA BUSCA E DETALHES (ATUALIZADO)
# =======================================================

class PortfolioPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioPhoto
        fields = ['id', 'photo', 'title', 'description']

class ReviewPublicSerializer(serializers.ModelSerializer):
    """Mostra apenas o necessário da avaliação no perfil público."""
    client_name = serializers.ReadOnlyField(source='service_request.client.username') # ou first_name
    class Meta:
        model = Review
        fields = ['id', 'client_rating', 'client_comment', 'client_photo', 'client_reviewed_at', 'client_name']

class ProviderListSerializer(serializers.ModelSerializer):
    """Leve: Para a lista de busca."""
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')
    class Meta:
        model = ProviderProfile
        fields = ['id', 'full_name', 'username', 'email', 'professional_email', 'service_address', 'technical_qualification', 'profile_photo']

class ProviderDetailSerializer(serializers.ModelSerializer):
    """Completo: Para a página de detalhes (inclui Portfolio e Reviews)."""
    username = serializers.ReadOnlyField(source='user.username')
    email = serializers.ReadOnlyField(source='user.email')
    
    # Nested Relations
    portfolio_photos = PortfolioPhotoSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'full_name', 'username', 'email', 'professional_email', 
            'service_address', 'technical_qualification', 'profile_photo',
            'portfolio_photos', 'reviews', 'average_rating', 'total_reviews'
        ]

    def get_reviews(self, obj):
        # Pega reviews onde o cliente avaliou
        reviews = Review.objects.filter(service_request__provider=obj, client_rating__isnull=False).order_by('-client_reviewed_at')
        return ReviewPublicSerializer(reviews, many=True).data

    def get_average_rating(self, obj):
        avg = Review.objects.filter(service_request__provider=obj, client_rating__isnull=False).aggregate(Avg('client_rating'))
        return avg['client_rating__avg'] or 0

    def get_total_reviews(self, obj):
        return Review.objects.filter(service_request__provider=obj, client_rating__isnull=False).count()

# =======================================================
# 🔒 SERIALIZERS DE AUTENTICAÇÃO
# =======================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    profile_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'profile_data')
        extra_kwargs = {'username': {'required': True}, 'email': {'required': True}}

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As duas senhas devem ser iguais."})
        if User.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": "Este email já está em uso."})
        return data

    def get_profile_data(self, obj): return {}

    @transaction.atomic 
    def create(self, validated_data):
        validated_data.pop('password2') 
        try:
            return User.objects.create_user(
                username=validated_data['username'], email=validated_data['email'], password=validated_data['password']
            )
        except IntegrityError:
            raise serializers.ValidationError({"username": "Este nome de usuário já está em uso."})

class ClientRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(max_length=255, required=True)
    cpf = serializers.CharField(max_length=20, required=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    identity_document = serializers.FileField(required=False, allow_null=True)

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + ('full_name', 'cpf', 'phone', 'address', 'identity_document')

    @transaction.atomic
    def create(self, validated_data):
        user = super().create(validated_data) 
        ClientProfile.objects.create(
            user=user, full_name=validated_data.get('full_name'), cpf=validated_data.get('cpf'),
            phone=validated_data.get('phone'), address=validated_data.get('address'),
            identity_document=validated_data.get('identity_document'),
        )
        return user

class ProviderRegisterSerializer(RegisterSerializer):
    full_name = serializers.CharField(max_length=255, required=True)
    professional_email = serializers.EmailField(required=True)
    service_address = serializers.CharField(required=False, allow_blank=True)
    technical_qualification = serializers.CharField(required=False, allow_blank=True)
    identity_document = serializers.FileField(required=False, allow_null=True)
    certifications = serializers.FileField(required=False, allow_null=True)

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + (
            'full_name', 'professional_email', 'service_address', 
            'technical_qualification', 'identity_document', 'certifications'
        )

    @transaction.atomic
    def create(self, validated_data):
        user = super().create(validated_data)
        ProviderProfile.objects.create(
            user=user, full_name=validated_data.get('full_name'), professional_email=validated_data.get('professional_email'),
            service_address=validated_data.get('service_address'), technical_qualification=validated_data.get('technical_qualification'),
            identity_document=validated_data.get('identity_document'), certifications=validated_data.get('certifications'),
        )
        return user
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user = UserSerializer(read_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            data['user'] = user
            return data
        raise serializers.ValidationError("Credenciais inválidas.")

# =======================================================
# 💬 SERIALIZERS DE CHAT E REVIEW (INPUT)
# =======================================================

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    is_me = serializers.SerializerMethodField()
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_name', 'content', 'created_at', 'is_read', 'is_me']
        read_only_fields = ['id', 'sender', 'created_at', 'is_read']
    def get_is_me(self, obj):
        request = self.context.get('request')
        return obj.sender == request.user if (request and request.user) else False

class ReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.ImageField(required=False)

# =======================================================
# ✉️ SERIALIZERS DE SOLICITAÇÃO DE SERVIÇO
# =======================================================

class ServiceRequestSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True) 
    provider = ProviderSummarySerializer(read_only=True)
    provider_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ServiceRequest
        fields = ("id", "provider", "provider_id", "client", "description", "desired_datetime", "proposed_value", "status", "created_at")
        read_only_fields = ("id", "status", "created_at", "provider", "client")

    def create(self, validated_data):
        provider_id = self.context.get('provider_id') or validated_data.pop('provider_id', None)
        if provider_id is None: raise serializers.ValidationError({"provider": "Provider id is required"})
        try: provider = ProviderProfile.objects.get(pk=provider_id)
        except ProviderProfile.DoesNotExist: raise serializers.ValidationError({"provider": "Provider not found"})
        
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated: raise serializers.ValidationError({"auth": "Authentication required"})

        return ServiceRequest.objects.create(
            provider=provider, client=request.user, description=validated_data.get('description', ''),
            desired_datetime=validated_data.get('desired_datetime'), proposed_value=validated_data.get('proposed_value'),
        )

class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True) 
    provider = ProviderSummarySerializer(read_only=True)
    class Meta:
        model = ServiceRequest
        fields = ("id", "provider", "client", "description", "desired_datetime", "proposed_value", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def update(self, instance, validated_data):
        if "status" in validated_data:
            new_status = validated_data["status"]
            if new_status not in [ServiceRequest.STATUS_PENDING, ServiceRequest.STATUS_ACCEPTED, ServiceRequest.STATUS_REJECTED]:
                raise serializers.ValidationError({"status": "Invalid value"})
            instance.status = new_status
        instance.save()
        return instance