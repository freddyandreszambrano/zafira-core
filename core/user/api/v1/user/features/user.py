from django.db import transaction

from core.auth.models import User
from core.user.api.v1.user.serializer.user import UserCreateSerializerInput


class UserApi:
    valid_fields = {
        "username": ("username__iexact", "El nombre de usuario ya se encuentra registrado."),
        "email": ("email__iexact", "Este correo electronico ya esta asociado a una cuenta."),
        "dni": ("dni", "La cedula ingresada ya se encuentra registrada."),
    }

    def create_user(self, data):
        serializer = UserCreateSerializerInput(data=data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            return serializer.save()

    def validate_field(self, field, value):
        if field not in self.valid_fields:
            return None
        lookup, message = self.valid_fields[field]
        exists = User.objects.filter(**{lookup: value}).exists()
        return {
            "exists": exists,
            "message": message if exists else "",
        }
