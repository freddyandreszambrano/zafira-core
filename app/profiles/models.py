"""User profile models for extended user data."""

from django.db import models
from django.utils import timezone
from django.conf import settings


class UserProfile(models.Model):
    """Extended user profile with corporate information."""

    DEPARTMENT_CHOICES = [
        ('HR', 'Recursos Humanos'),
        ('IT', 'Información y Tecnología'),
        ('FINANCE', 'Finanzas'),
        ('SALES', 'Ventas'),
        ('MARKETING', 'Marketing'),
        ('OPERATIONS', 'Operaciones'),
        ('OTHER', 'Otro'),
    ]

    # Relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )

    # Contact Information
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número telefónico'
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Dirección'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='Ecuador',
        verbose_name='País'
    )

    # Professional Information
    department = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        default='OTHER',
        verbose_name='Departamento'
    )
    job_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cargo'
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name='Gerente/Supervisor'
    )
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        verbose_name='ID de empleado'
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de contratación'
    )

    # Additional Information
    bio = models.TextField(
        blank=True,
        verbose_name='Biografía'
    )
    social_media = models.TextField(
        default=dict,
        blank=True,
        verbose_name='Redes sociales',
        help_text='JSON con enlaces a redes sociales'
    )

    # Status
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Verificado',
        help_text='Indica si el perfil ha sido verificado'
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

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
        """Get user's display name."""
        return self.user.get_full_name() or self.user.username

    def get_department_display_es(self):
        """Get department display in Spanish."""
        return dict(self.DEPARTMENT_CHOICES).get(self.department, self.department)

    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'department': self.department,
            'department_display': self.get_department_display_es(),
            'job_title': self.job_title,
            'manager': self.manager.get_full_name() if self.manager else None,
            'employee_id': self.employee_id,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'bio': self.bio,
            'social_media': self.social_media,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
