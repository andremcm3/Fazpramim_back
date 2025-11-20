from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from knox.views import LoginView as KnoxLoginView, LogoutView
from knox.models import AuthToken

from accounts.models import ProviderProfile, ServiceRequest
# CERTIFIQUE-SE que esses serializers existem no seu serializers.py
from .serializers import (
    ServiceRequestSerializer, 
    ServiceRequestDetailSerializer,
    # Necessários para Autenticação
    RegisterSerializer, 
    UserSerializer,     
    LoginSerializer     
)

# =======================================================
# 🔐 VIEWS DE AUTENTICAÇÃO
# =======================================================

class RegisterApi(generics.GenericAPIView):
    """View para registro de novos usuários. Retorna o token de autenticação."""
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            # Gera um novo token para o usuário registrado
            "token": AuthToken.objects.create(user)[1] 
        }, status=status.HTTP_201_CREATED)


class LoginApi(KnoxLoginView):
    """View para login. Usa o serializer personalizado para validar credenciais."""
    # Permite que qualquer usuário (autenticado ou não) acesse o login
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Faz o login do usuário no Django
        login(request, user)
        
        # Chama o post da classe base (KnoxLoginView) para gerar o token
        return super(LoginApi, self).post(request, format=None)


class LogoutApi(LogoutView):
    """Faz o logout do usuário, invalidando o token atual."""
    # Herda diretamente do Knox, não requer código adicional.
    pass


# =======================================================
# ⚙️ VIEWS DE SOLICITAÇÃO DE SERVIÇO
# =======================================================

class CreateServiceRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # pk = provider id
        data = request.data.copy()
        data['provider_id'] = pk

        serializer = ServiceRequestSerializer(
            data=data,
            context={'request': request, 'provider_id': pk}
        )

        if serializer.is_valid():
            sr = serializer.save()
            return Response(
                ServiceRequestDetailSerializer(sr).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProviderRequestsListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, 'provider_profile'):
            return ServiceRequest.objects.none()

        provider = user.provider_profile
        return ServiceRequest.objects.filter(provider=provider).order_by('-created_at')


class ServiceRequestDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRequestDetailSerializer
    queryset = ServiceRequest.objects.all()

    def get_object(self):
        sr = super().get_object()
        user = self.request.user

        is_provider = hasattr(user, 'provider_profile') and user.provider_profile == sr.provider
        is_client = (sr.client == user)

        if not (is_provider or is_client):
            raise PermissionDenied("Você não tem permissão para acessar esta solicitação.")

        return sr

    def update(self, request, *args, **kwargs):
        sr = self.get_object()
        user = request.user

        # Somente provider pode alterar status
        if not (hasattr(user, 'provider_profile') and user.provider_profile == sr.provider):
            return Response({'detail': 'Apenas o prestador pode alterar o status.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(sr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)