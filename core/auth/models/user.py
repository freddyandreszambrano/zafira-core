import uuid
from secrets import compare_digest

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone

from rest_framework.authtoken.models import Token

from crum import get_current_request

from core.utils.enums import UserTypeChoices

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    DEFAULT_IMAGE = "/static/img/default/empty.png"

    first_name = models.TextField(blank=True, verbose_name="Nombres")
    last_name = models.TextField(blank=True, verbose_name="Apellidos")
    username = models.TextField(unique=True, verbose_name="Username", db_index=True)
    dni = models.TextField(unique=True, verbose_name="Numero de cedula", db_index=True)
    email = models.TextField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Correo electronico",
        db_index=True,
    )
    image = models.ImageField(
        upload_to="users/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name="Imagen de perfil",
    )
    user_type = models.TextField(
        choices=UserTypeChoices.choices,
        default=UserTypeChoices.MOBILE,
        db_index=True,
        verbose_name="Tipo de usuario",
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Ultimo acceso")
    last_password_change_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    force_password_change = models.BooleanField(
        default=False, verbose_name="Forzar cambio de contrasena"
    )
    is_change_password = models.BooleanField(
        default=False, verbose_name="Cambio de contrasena requerido"
    )
    email_reset_token = models.TextField(null=True, blank=True)
    email_reset_expires_at = models.DateTimeField(null=True, blank=True)
    password_reset_pending = models.BooleanField(
        default=False, verbose_name="Restablecimiento de contrasena pendiente"
    )
    password_reset_count = models.PositiveIntegerField(
        default=0, verbose_name="Veces que restablecio la contrasena"
    )
    last_password_reset_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Ultimo restablecimiento de contrasena"
    )
    token_notification = models.TextField(null=True, blank=True)
    security_groups = models.ManyToManyField(
        "security.Group",
        blank=True,
        related_name="members",
        verbose_name="Grupos de seguridad",
    )

    objects = CustomUserManager()
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "dni"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["dni"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    def __repr__(self):
        return f"<User: {self.username} ({self.id})>"

    def get_full_name(self):
        first = (self.first_name or "").strip().upper()
        last = (self.last_name or "").strip().upper()
        return f"{first} {last}".strip()

    def get_short_name(self):
        return self.last_name or self.username

    def get_image_url(self):
        return self.image.url if self.image else self.DEFAULT_IMAGE

    def to_json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "dni": self.dni,
            "full_name": self.get_full_name(),
            "user_type": self.user_type,
            "is_active": self.is_active,
            "is_staff": self.is_staff,
            "image": self.get_image_url(),
            "date_joined": self.date_joined.strftime("%Y-%m-%d %H:%M"),
        }

    def to_json_api(self):
        request = get_current_request()
        mobile_profile = getattr(self, "mobile_profile", None)

        image_url = ""
        if self.image:
            image_url = request.build_absolute_uri(self.image.url) if request else self.image.url

        try_on_photo_url = ""
        if getattr(mobile_profile, "try_on_photo", None):
            url = mobile_profile.try_on_photo.url
            try_on_photo_url = request.build_absolute_uri(url) if request else url

        if mobile_profile is not None:
            onboarding = mobile_profile.onboarding_status()
        else:
            onboarding = {"completed": False, "pending_steps": ["gender", "preferred_size"]}

        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "dni": self.dni,
            "full_name": self.get_full_name(),
            "user_type": self.user_type,
            "image": image_url,
            "gender": getattr(mobile_profile, "gender", ""),
            "country": getattr(mobile_profile, "country", ""),
            "preferred_size": getattr(mobile_profile, "preferred_size", ""),
            "style_preferences": getattr(mobile_profile, "style_preferences", {}),
            "language": getattr(mobile_profile, "language", "es"),
            "try_on_photo": try_on_photo_url,
            "onboarding": onboarding,
            "token": self.get_or_create_token().replace("Token ", ""),
        }

    @staticmethod
    def generate_token():
        return str(uuid.uuid4())

    def get_or_create_token(self):
        token, _ = Token.objects.get_or_create(user=self)
        return f"Token {token.key}"

    def create_or_update_password(self, password):
        if self.pk is None:
            self.set_password(password)
            return
        existing = User.objects.get(pk=self.pk)
        if not compare_digest(existing.password, password):
            self.set_password(password)

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.last_password_change_at = timezone.now()

    def get_security_groups(self):
        return list(self.security_groups.filter(is_active=True))

    def set_group_session(self):
        request = get_current_request()
        if not request:
            return
        if request.session.get("group"):
            return
        first_group = self.security_groups.filter(is_active=True).first()
        if first_group:
            request.session["group"] = first_group.to_json()

    def get_group_id_session(self):
        request = get_current_request()
        if not request:
            return None
        group = request.session.get("group") or {}
        return group.get("id")
