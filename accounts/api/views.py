from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions, filters
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from knox.views import LoginView as KnoxLoginView, LogoutView
from knox.models import AuthToken
from django.utils import timezone

from accounts.models import ProviderProfile, ServiceRequest, ChatMessage, Review, PortfolioPhoto
from .serializers import (
    ServiceRequestSerializer, ServiceRequestDetailSerializer,
    ClientRegisterSerializer, ProviderRegisterSerializer,
    UserSerializer, LoginSerializer,
    ProviderListSerializer, ProviderDetailSerializer, # <--- NOVO
    ChatMessageSerializer, ReviewSerializer, PortfolioPhotoSerializer
)

# =======================================================
# 🔐 VIEWS DE AUTENTICAÇÃO
# =======================================================

class LoginApi(KnoxLoginView):
    """Login e geração de Token."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginApi, self).post(request, format=None)

class LogoutApi(LogoutView):
    """Logout e invalidação de Token."""
    pass

class ClientRegisterAPIView(generics.GenericAPIView):
    """Cadastro de Cliente."""
    serializer_class = ClientRegisterSerializer
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1] 
        }, status=status.HTTP_201_CREATED)

class ProviderRegisterAPIView(generics.GenericAPIView):
    """Cadastro de Prestador."""
    serializer_class = ProviderRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1] 
        }, status=status.HTTP_201_CREATED)

# =======================================================
# 🔍 BUSCA DE PRESTADORES
# =======================================================

class ProviderListAPIView(generics.ListAPIView):
    """Lista pública de prestadores com busca."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ProviderListSerializer
    queryset = ProviderProfile.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'technical_qualification', 'service_address']


class ProviderRetrieveAPIView(generics.RetrieveAPIView):
    """Detalhes públicos do prestador (Portfolio, Reviews, etc)."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ProviderDetailSerializer
    queryset = ProviderProfile.objects.all()
# =======================================================
# 🛠️ SOLICITAÇÕES DE SERVIÇO
# =======================================================

class CreateServiceRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # pk = provider id
        data = request.data.copy()
        data['provider_id'] = pk
        serializer = ServiceRequestSerializer(data=data, context={'request': request, 'provider_id': pk})
        if serializer.is_valid():
            sr = serializer.save()
            return Response(ServiceRequestDetailSerializer(sr).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProviderRequestsListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'provider_profile'):
            return ServiceRequest.objects.none()
        return ServiceRequest.objects.filter(provider=user.provider_profile).order_by('-created_at')

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
            raise PermissionDenied("Sem permissão.")
        return sr

    def update(self, request, *args, **kwargs):
        sr = self.get_object()
        user = request.user
        # Apenas prestador altera status (aceitar/rejeitar)
        if not (hasattr(user, 'provider_profile') and user.provider_profile == sr.provider):
             # Se for cliente tentando mudar status, bloqueia (a menos que seja finalização, tratada abaixo)
             if 'status' in request.data:
                 return Response({'detail': 'Apenas o prestador pode alterar o status.'}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)

# =======================================================
# 💬 CHAT API
# =======================================================

class ChatAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Lista mensagens de uma solicitação."""
        sr = get_object_or_404(ServiceRequest, pk=pk)
        
        is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
        is_client = request.user == sr.client
        if not (is_provider or is_client):
            return Response({"error": "Não permitido"}, status=status.HTTP_403_FORBIDDEN)

        # Marcar lidas
        ChatMessage.objects.filter(service_request=sr).exclude(sender=request.user).update(is_read=True)

        messages = sr.messages.all().order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, pk):
        """Envia mensagem."""
        sr = get_object_or_404(ServiceRequest, pk=pk)
        
        is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
        is_client = request.user == sr.client
        if not (is_provider or is_client):
            return Response({"error": "Não permitido"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(service_request=sr, sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =======================================================
# ✅ FINALIZAÇÃO E AVALIAÇÃO
# =======================================================

class CompleteServiceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        
        is_provider = hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider
        is_client = request.user == sr.client

        if not (is_provider or is_client):
            return Response({"error": "Não permitido"}, status=status.HTTP_403_FORBIDDEN)

        # Lógica de dupla confirmação
        if is_client:
            sr.completed_by_client = True
        elif is_provider:
            sr.completed_by_provider = True
        
        msg = "Confirmação registrada."
        if sr.completed_by_client and sr.completed_by_provider:
            sr.status = ServiceRequest.STATUS_COMPLETED
            msg = "Serviço concluído com sucesso!"
        
        sr.save()
        return Response({"message": msg, "status": sr.status, "completed_by_client": sr.completed_by_client, "completed_by_provider": sr.completed_by_provider})

class ReviewCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        if sr.status != ServiceRequest.STATUS_COMPLETED:
            return Response({"error": "Serviço não concluído"}, status=status.HTTP_400_BAD_REQUEST)

        # Garante que a review existe ou cria
        review, _ = Review.objects.get_or_create(service_request=sr)
        
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            if request.user == sr.client:
                review.client_rating = data['rating']
                review.client_comment = data.get('comment', '')
                if 'photo' in request.FILES:
                    review.client_photo = request.FILES['photo']
                review.client_reviewed_at = timezone.now()
            
            elif hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider:
                review.provider_rating = data['rating']
                review.provider_comment = data.get('comment', '')
                review.provider_reviewed_at = timezone.now()
            else:
                return Response({"error": "Usuário inválido"}, status=status.HTTP_403_FORBIDDEN)

            review.save()
            return Response({"message": "Avaliação enviada!"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)