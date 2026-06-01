from django.contrib.auth import authenticate
from rest_framework import serializers

from core.common.constants import MSG_INACTIVE_ACCOUNT, MSG_INVALID_CREDENTIALS

from .user import UserDetailSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError(MSG_INVALID_CREDENTIALS)
        if not user.is_active:
            raise serializers.ValidationError(MSG_INACTIVE_ACCOUNT)
        data['user'] = user
        return data


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserDetailSerializer()


class JWTTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserDetailSerializer()
