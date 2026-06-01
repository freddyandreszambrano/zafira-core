from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core.auth.models import User
from core.common.constants import MSG_PASSWORDS_MISMATCH


def _ensure_passwords_match(p1, p2, field='new_password'):
    if p1 != p2:
        raise serializers.ValidationError({field: MSG_PASSWORDS_MISMATCH})


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password],
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña antigua es incorrecta.')
        return value

    def validate(self, data):
        _ensure_passwords_match(data['new_password'], data.pop('new_password2'))
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'No existe un usuario con este correo electrónico.'
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password],
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        _ensure_passwords_match(data['new_password'], data.pop('new_password2'))
        return data
