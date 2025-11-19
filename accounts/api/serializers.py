from rest_framework import serializers
from accounts.models import ServiceRequest, ProviderProfile
from django.contrib.auth.models import User


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class ProviderSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = ProviderProfile
        fields = ("id", "full_name", "user")


class ServiceRequestSerializer(serializers.ModelSerializer):
    client = UserSummarySerializer(read_only=True)
    provider = ProviderSummarySerializer(read_only=True)
    provider_id = serializers.IntegerField(write_only=True, required=False)

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
        # provider_id can be provided via context or write-only field
        provider_id = validated_data.pop('provider_id', None) or self.context.get('provider_id')
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
    client = UserSummarySerializer(read_only=True)
    provider = ProviderSummarySerializer(read_only=True)

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
        # Only allow status change via this serializer; keep other fields writable if desired
        status = validated_data.get('status')
        if status:
            instance.status = status
            instance.save()
        return instance
