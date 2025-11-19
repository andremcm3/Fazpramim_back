from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.shortcuts import get_object_or_404
from accounts.models import ProviderProfile, ServiceRequest
from .serializers import ServiceRequestSerializer, ServiceRequestDetailSerializer


class CreateServiceRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # pk is provider id
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
        # ensure user is a provider
        if not hasattr(user, 'provider_profile'):
            return ServiceRequest.objects.none()
        provider = user.provider_profile
        return ServiceRequest.objects.filter(provider=provider).order_by('-created_at')


class ServiceRequestDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRequestDetailSerializer
    queryset = ServiceRequest.objects.all()

    def update(self, request, *args, **kwargs):
        sr = self.get_object()
        user = request.user
        # only provider owner can change status
        if not hasattr(user, 'provider_profile') or user.provider_profile != sr.provider:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        # allow status change via payload e.g. {"status": "accepted"}
        serializer = self.get_serializer(sr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
