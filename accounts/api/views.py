from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from knox.views import LoginView as KnoxLoginView, LogoutView
from knox.models import AuthToken
from django.utils import timezone

from accounts.models import ProviderProfile, ClientProfile, ServiceRequest, ChatMessage, Review, PortfolioPhoto
from .serializers import (
    ReviewPublicSerializer, ServiceRequestSerializer, ServiceRequestDetailSerializer,
    ClientRegisterSerializer, ProviderRegisterSerializer,
    UserSerializer, LoginSerializer,
    ProviderListSerializer, ProviderDetailSerializer,
    ProviderProfileUpdateSerializer,
    ClientProfileSerializer,
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
        
        response = super(LoginApi, self).post(request, format=None)
        response.data['user'] = UserSerializer(user).data
        
        # Adiciona dados do provider_profile no login
        if hasattr(user, 'provider_profile'):
            response.data['provider_profile'] = ProviderProfileUpdateSerializer(user.provider_profile).data
        
        return response

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

class ProviderRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Recupera e atualiza o perfil do prestador autenticado."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProviderProfileUpdateSerializer
    # Garante suporte a upload de arquivos (certifications, profile_photo)
    parser_classes = (MultiPartParser, FormParser)
    
    def get_object(self):
        """Retorna o ProviderProfile do usuário autenticado."""
        try:
            return self.request.user.provider_profile
        except ProviderProfile.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Prestador não encontrado.")
    
    def update(self, request, *args, **kwargs):
        """Permite atualizar dados do prestador (service_address, technical_qualification, etc)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Suporte a multipart/form-data já feito pelos parsers acima
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class ClientRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """Recupera e atualiza o perfil do cliente autenticado."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClientProfileSerializer
    
    def get_object(self):
        """Retorna o ClientProfile do usuário autenticado."""
        try:
            return self.request.user.client_profile
        except ClientProfile.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Cliente não encontrado.")
    
    def update(self, request, *args, **kwargs):
        """Permite atualizar phone, address e profile_photo do cliente."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
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
        
        queryset = ServiceRequest.objects.filter(provider=user.provider_profile).order_by('-created_at')
        
        # Filtro opcional por status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

class ClientRequestsListAPIView(generics.ListAPIView):
    """Lista todas as solicitações feitas pelo cliente."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ServiceRequest.objects.filter(client=user).order_by('-created_at')
        
        # Filtro opcional por status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

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

class AcceptServiceRequestAPIView(APIView):
    """Aceitar solicitação de serviço (Apenas Prestador)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        
        # Verifica se o usuário é o prestador desta solicitação
        if not (hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider):
            return Response(
                {"error": "Apenas o prestador pode aceitar esta solicitação."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verifica se a solicitação está pendente
        if sr.status != ServiceRequest.STATUS_PENDING:
            return Response(
                {"error": f"Não é possível aceitar uma solicitação com status '{sr.get_status_display()}'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aceita a solicitação
        sr.status = ServiceRequest.STATUS_ACCEPTED
        sr.save()
        
        serializer = ServiceRequestDetailSerializer(sr)
        return Response({
            "message": "Solicitação aceita com sucesso!",
            "request": serializer.data
        }, status=status.HTTP_200_OK)

class RejectServiceRequestAPIView(APIView):
    """Rejeitar solicitação de serviço (Apenas Prestador)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        
        # Verifica se o usuário é o prestador desta solicitação
        if not (hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider):
            return Response(
                {"error": "Apenas o prestador pode rejeitar esta solicitação."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verifica se a solicitação está pendente
        if sr.status != ServiceRequest.STATUS_PENDING:
            return Response(
                {"error": f"Não é possível rejeitar uma solicitação com status '{sr.get_status_display()}'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rejeita a solicitação
        sr.status = ServiceRequest.STATUS_REJECTED
        sr.save()
        
        serializer = ServiceRequestDetailSerializer(sr)
        return Response({
            "message": "Solicitação rejeitada.",
            "request": serializer.data
        }, status=status.HTTP_200_OK)

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

class ProviderReviewsListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewPublicSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'provider_profile'):
            return Review.objects.none()
        return Review.objects.filter(
            service_request__provider=user.provider_profile,
            client_rating__isnull=False
        ).order_by('-client_reviewed_at')
