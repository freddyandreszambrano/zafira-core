from django.conf import settings
from django.db import models

from app.common.choices import Department


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario',
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name='Número telefónico')
    address = models.CharField(max_length=255, blank=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    country = models.CharField(
        max_length=100, blank=True, default='Ecuador', verbose_name='País',
    )

    department = models.CharField(
        max_length=50,
        choices=Department.choices,
        default=Department.OTHER,
        verbose_name='Departamento',
    )
    job_title = models.CharField(max_length=100, blank=True, verbose_name='Cargo')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name='Gerente/Supervisor',
    )
    employee_id = models.CharField(
        max_length=50, blank=True, unique=True, verbose_name='ID de empleado',
    )
    hire_date = models.DateField(null=True, blank=True, verbose_name='Fecha de contratación')

    bio = models.TextField(blank=True, verbose_name='Biografía')
    social_media = models.TextField(default=dict, blank=True, verbose_name='Redes sociales')

    is_verified = models.BooleanField(default=False, verbose_name='Verificado')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['department']),
            models.Index(fields=['employee_id']),
        ]

    def __str__(self):
        return f'Perfil de {self.user.get_full_name() or self.user.username}'

    def __repr__(self):
        return f'<UserProfile: {self.user.username}>'

    def get_display_name(self):
        return self.user.get_full_name() or self.user.username
