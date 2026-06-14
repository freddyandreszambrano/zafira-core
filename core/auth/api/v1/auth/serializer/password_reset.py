from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class PasswordResetRequestSerializerInput(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)


class PasswordResetConfirmSerializerInput(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    code = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value
