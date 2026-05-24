"""User model for authentication system."""

import uuid
from secrets import compare_digest

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models, transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for corporate authentication system."""

    first_name = models.CharField(max_length=150, blank=True, verbose_name='Nombres')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='Apellidos')
    username = models.CharField(max_length=150, unique=True, verbose_name='Username', db_index=True)
    dni = models.CharField(max_length=20, unique=True, verbose_name='Número de cédula', db_index=True)
    email = models.EmailField(unique=True, verbose_name='Correo electrónico', db_index=True)
    image = models.ImageField(upload_to='users/%Y/%m/%d/', null=True, blank=True, verbose_name='Imagen de perfil')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Último acceso')
    last_password_change_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    force_password_change = models.BooleanField(default=False, verbose_name='Forzar cambio de contraseña')
    is_change_password = models.BooleanField(default=False, verbose_name='Cambio de contraseña requerido')
    email_reset_token = models.CharField(max_length=255, null=True, blank=True)
    token_notification = models.CharField(max_length=255, null=True, blank=True)

    objects = CustomUserManager()
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'dni']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['dni']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    def __repr__(self):
        return f'<User: {self.username} ({self.id})>'

    def get_full_name(self):
        first = (self.first_name or '').strip().upper()
        last = (self.last_name or '').strip().upper()
        return f'{first} {last}'.strip()

    def get_short_name(self):
        return self.last_name or self.username

    def get_image_url(self):
        if self.image:
            return self.image.url
        return '/static/img/default/empty.png'

    @staticmethod
    def generate_token():
        return str(uuid.uuid4())

    def get_or_create_token(self):
        token, _ = Token.objects.get_or_create(user=self)
        return f'Token {token.key}'

    def create_or_update_password(self, password):
        if self.pk is None:
            self.set_password(password)
        else:
            user = User.objects.get(pk=self.pk)
            if not compare_digest(user.password, password):
                self.set_password(password)
                self.last_password_change_at = timezone.now()

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.last_password_change_at = timezone.now()

    def get_user_groups(self):
        return [{'id': group.id, 'name': group.name} for group in self.groups.all()]

    def get_user_permissions(self):
        return [{'id': perm.id, 'codename': perm.codename, 'name': perm.name} for perm in self.user_permissions.all()]

    def to_dict(self, include_token=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'dni': self.dni,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'image': self.get_image_url(),
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'date_joined': self.date_joined.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'groups': self.get_user_groups(),
            'permissions': self.get_user_permissions(),
        }
        if include_token:
            data['token'] = self.get_or_create_token()
        return data

    @staticmethod
    def get_or_create_user(data, set_password=True):
        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    dni=data['dni'],
                    defaults={
                        'username': data.get('username', data['dni']),
                        'email': data.get('email', ''),
                        'first_name': data.get('first_name', ''),
                        'last_name': data.get('last_name', ''),
                    }
                )
                if not created:
                    user.first_name = data.get('first_name', user.first_name)
                    user.last_name = data.get('last_name', user.last_name)
                    user.email = data.get('email', user.email)
                    user.is_active = data.get('is_active', user.is_active)
                    user.save()
                if set_password and 'password' in data:
                    user.set_password(data['password'])
                    user.save()
                return user
        except Exception as e:
            raise Exception(f'Error creating/updating user: {str(e)}')

    @staticmethod
    def update_user(user_id, data):
        try:
            with transaction.atomic():
                user = User.objects.get(pk=user_id)
                allowed_fields = ['first_name', 'last_name', 'email', 'username']
                for field in allowed_fields:
                    if field in data:
                        setattr(user, field, data[field])
                user.save()
                return user
        except User.DoesNotExist:
            raise Exception('User not found')
        except Exception as e:
            raise Exception(f'Error updating user: {str(e)}')
