import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

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

    gender = serializers.ChoiceField(
        choices=GenderChoices.choices,
        required=False,
        allow_blank=True,
        default=GenderChoices.UNDISCLOSED,
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    preferred_size = serializers.CharField(required=False, allow_blank=True, default="")
    style_preferences = serializers.JSONField(required=False, default=dict)
    language = serializers.CharField(required=False, allow_blank=True, default="es")
    country = serializers.CharField(required=False, allow_blank=True, default="Ecuador")
    push_token = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_username(self, value):
        username = value.strip()

        if len(username) < 4:
            raise serializers.ValidationError(
                "El usuario debe tener al menos 4 caracteres."
            )

        if len(username) > 20:
            raise serializers.ValidationError(
                "El usuario no puede superar los 20 caracteres."
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise serializers.ValidationError(
                "El usuario solo puede contener letras, números y guion bajo."
            )

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                "El nombre de usuario ya se encuentra registrado."
            )

        return username

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Este correo electrónico ya está asociado a una cuenta."
            )

        return email

    def validate_dni(self, value):
        dni = value.strip()

        if not dni.isdigit():
            raise serializers.ValidationError(
                "La cédula solo debe contener números."
            )

        if len(dni) != 10:
            raise serializers.ValidationError(
                "La cédula debe tener exactamente 10 dígitos."
            )

        if User.objects.filter(dni__iexact=dni).exists():
            raise serializers.ValidationError(
                "La cédula ingresada ya se encuentra registrada."
            )

        return dni

    def validate_password(self, value):
        common_passwords = {
            "12345678",
            "123456789",
            "1234567890",
            "password",
            "password123",
            "qwerty",
            "qwerty123",
            "admin123",
            "admin1234",
            "abcdefghi",
            "juandaniel08",
        }

        password = value.strip()

        if len(password) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )

        if password.lower() in common_passwords:
            raise serializers.ValidationError(
                "Contraseña demasiado fácil. Usa una contraseña más segura."
            )

        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra mayúscula."
            )

        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra minúscula."
            )

        if not re.search(r"\d", password):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\];']", password):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial."
            )

        try:
            validate_password(password)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)

        return password

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
