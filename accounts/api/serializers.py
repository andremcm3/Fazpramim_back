from rest_framework import serializers
from accounts.models import ServiceRequest, ProviderProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError # Importação adicional para garantir usernames únicos

# =======================================================
# 👤 SERIALIZERS DE USUÁRIO (Existentes e Renomeados)
# =======================================================

# Renomeado para UserSerializer para clareza na API (mas mantém o campo original)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")

# Alias para manter compatibilidade com o código original (ServiceRequest)
UserSummarySerializer = UserSerializer


class ProviderSummarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = ("id", "full_name", "user")

# =======================================================
# 🔒 SERIALIZERS DE AUTENTICAÇÃO (NOVOS)
# =======================================================

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de novo usuário."""
    # Garante que a senha seja write-only e não seja retornada na resposta
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }

    def validate(self, data):
        # Validação: Senhas devem ser iguais
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As duas senhas devem ser iguais."})
        
        # Validação: Email deve ser único (se o modelo User for customizado, verifique a implementação)
        if User.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": "Este email já está em uso."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2') # Remove a confirmação antes de criar
        
        try:
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            return user
        except IntegrityError:
            # Caso o username já exista (redundante, mas seguro)
            raise serializers.ValidationError({"username": "Este nome de usuário já está em uso."})


class LoginSerializer(serializers.Serializer):
    """Serializer para validar credenciais de login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user = UserSerializer(read_only=True) # Para retornar o usuário após o login

    def validate(self, data):
        user = authenticate(**data)
        
        if user and user.is_active:
            # O usuário autenticado é adicionado aos dados validados
            data['user'] = user
            return data
        
        raise serializers.ValidationError("Credenciais inválidas.")

# =======================================================
# ✉️ SERIALIZERS DE SOLICITAÇÃO DE SERVIÇO (Seu código original)
# =======================================================

class ServiceRequestSerializer(serializers.ModelSerializer):
    # Usando o novo/renomeado UserSummarySerializer
    client = UserSerializer(read_only=True) 
    provider = ProviderSummarySerializer(read_only=True)

    # optional in body, override if provided in context
    provider_id = serializers.IntegerField(write_only=True, required=False)
    
    # ... (Resto do seu código original para ServiceRequestSerializer) ...
    class Meta:
        model = ServiceRequest
        fields = (
            "id",
            "provider",
            "provider_id",
            "client",
            "description",
            "desired_datetime",
            "proposed_value",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at", "provider", "client")

    def create(self, validated_data):

        # URL param always has priority over serializer data
        provider_id = self.context.get('provider_id') or validated_data.pop('provider_id', None)

        if provider_id is None:
            raise serializers.ValidationError({"provider": "Provider id is required"})

        try:
            provider = ProviderProfile.objects.get(pk=provider_id)
        except ProviderProfile.DoesNotExist:
            raise serializers.ValidationError({"provider": "Provider not found"})

        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError({"auth": "Authentication required"})

        sr = ServiceRequest.objects.create(
            provider=provider,
            client=request.user,
            description=validated_data.get('description', ''),
            desired_datetime=validated_data.get('desired_datetime'),
            proposed_value=validated_data.get('proposed_value'),
        )

        return sr


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    # Usando o novo/renomeado UserSummarySerializer
    client = UserSerializer(read_only=True) 
    provider = ProviderSummarySerializer(read_only=True)

    # ... (Resto do seu código original para ServiceRequestDetailSerializer) ...
    class Meta:
        model = ServiceRequest
        fields = (
            "id",
            "provider",
            "client",
            "description",
            "desired_datetime",
            "proposed_value",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def update(self, instance, validated_data):

        # Only provider can change status (already validated in view)
        if "status" in validated_data:
            new_status = validated_data["status"]

            allowed = [
                ServiceRequest.STATUS_PENDING,
                ServiceRequest.STATUS_ACCEPTED,
                ServiceRequest.STATUS_REJECTED,
            ]

            if new_status not in allowed:
                raise serializers.ValidationError({"status": "Invalid value"})

            instance.status = new_status

        instance.save()
        return instance