from rest_framework import serializers

from core.auth.models import User


class AuthTokenSerializerInput(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "password"]


class MobileProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    preferred_size = serializers.CharField(required=False, allow_blank=True)
    style_preferences = serializers.JSONField(required=False)
    language = serializers.CharField(required=False, allow_blank=True)
    onboarding_completed = serializers.BooleanField(required=False)
    onboarding_force_show = serializers.BooleanField(required=False)
