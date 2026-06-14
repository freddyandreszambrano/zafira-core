from django.contrib.auth.models import UserManager
from django.db import transaction
from django.utils import timezone

from rest_framework.authtoken.models import Token

from core.utils.enums import UserTypeChoices

UPDATABLE_FIELDS = ("first_name", "last_name", "email", "username")


class CustomUserManager(UserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("El campo username es obligatorio.")

        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        Token.objects.get_or_create(user=user)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", UserTypeChoices.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)

    @transaction.atomic
    def get_or_create_from_data(self, data, set_password=True):
        user, created = self.get_or_create(
            dni=data["dni"],
            defaults={
                "username": data.get("username", data["dni"]),
                "email": data.get("email", ""),
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
            },
        )
        if not created:
            for field in ("first_name", "last_name", "email", "is_active"):
                if field in data:
                    setattr(user, field, data[field])
            user.save()

        if set_password and "password" in data:
            user.set_password(data["password"])
            user.last_password_change_at = timezone.now()
            user.save()
        return user

    @transaction.atomic
    def update_fields(self, user_id, data, allowed_fields=UPDATABLE_FIELDS):
        user = self.get(pk=user_id)
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        user.save()
        return user
