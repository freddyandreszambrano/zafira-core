from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core.auth.models import User
from core.profiles.models import MobileProfile
from core.utils.enums import GenderChoices, UserTypeChoices


class UserCreateSerializerInput(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False)
    dni = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")

    gender = serializers.ChoiceField(choices=GenderChoices.choices, required=False, allow_blank=True,
                                     default=GenderChoices.UNDISCLOSED, )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    preferred_size = serializers.CharField(required=False, allow_blank=True, default="")
    style_preferences = serializers.JSONField(required=False, default=dict)
    language = serializers.CharField(required=False, allow_blank=True, default="es")
    country = serializers.CharField(required=False, allow_blank=True, default="Ecuador")
    push_token = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("El username ya se encuentra registrado.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("El correo ya se encuentra registrado.")
        return value

    def validate_dni(self, value):
        if User.objects.filter(dni__iexact=value).exists():
            raise serializers.ValidationError("La cedula ya se encuentra registrada.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        profile_data = {
            "gender": validated_data.pop("gender", GenderChoices.UNDISCLOSED),
            "date_of_birth": validated_data.pop("date_of_birth", None),
            "preferred_size": validated_data.pop("preferred_size", ""),
            "style_preferences": validated_data.pop("style_preferences", {}),
            "language": validated_data.pop("language", "es"),
            "country": validated_data.pop("country", "Ecuador"),
            "push_token": validated_data.pop("push_token", ""),
        }
        password = validated_data.pop("password")
        user = User.objects.create_user(
            password=password,
            user_type=UserTypeChoices.MOBILE,
            is_active=True,
            is_staff=False,
            **validated_data,
        )
        MobileProfile.objects.update_or_create(user=user, defaults=profile_data)
        return user
