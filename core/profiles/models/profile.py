from django.conf import settings
from django.db import models

from core.utils.enums import DepartmentChoices, GenderChoices


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Usuario",
    )

    phone = models.TextField(blank=True, verbose_name="Numero telefonico")
    address = models.TextField(blank=True, verbose_name="Direccion")
    city = models.TextField(blank=True, verbose_name="Ciudad")
    country = models.TextField(blank=True, default="Ecuador", verbose_name="Pais")

    department = models.TextField(
        choices=DepartmentChoices.choices,
        default=DepartmentChoices.OTHER,
        verbose_name="Departamento",
    )
    job_title = models.TextField(blank=True, verbose_name="Cargo")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name="Gerente/Supervisor",
    )
    employee_id = models.TextField(
        null=True,
        blank=True,
        unique=True,
        verbose_name="ID de empleado",
    )

    hire_date = models.DateField(null=True, blank=True, verbose_name="Fecha de contratacion")
    bio = models.TextField(blank=True, verbose_name="Biografia")
    social_media = models.JSONField(default=dict, blank=True, verbose_name="Redes sociales")
    is_verified = models.BooleanField(default=False, verbose_name="Verificado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
        ordering = ["user__first_name", "user__last_name"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["department"]),
            models.Index(fields=["employee_id"]),
        ]

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"

    def __repr__(self):
        return f"<UserProfile: {self.user.username}>"

    def get_display_name(self):
        return self.user.get_full_name() or self.user.username


class MobileProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mobile_profile",
        verbose_name="Usuario",
    )
    gender = models.TextField(
        choices=GenderChoices.choices,
        default=GenderChoices.UNDISCLOSED,
        blank=True,
        verbose_name="Genero",
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")
    preferred_size = models.TextField(blank=True, verbose_name="Talla preferida")
    style_preferences = models.JSONField(default=dict, blank=True, verbose_name="Preferencias")
    language = models.TextField(default="es", blank=True, verbose_name="Idioma")
    country = models.TextField(blank=True, default="Ecuador", verbose_name="Pais")
    push_token = models.TextField(blank=True, verbose_name="Token push")
    try_on_photo = models.ImageField(
        upload_to="try_on/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name="Foto para prueba virtual",
    )
    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding completado",
    )
    onboarding_force_show = models.BooleanField(
        default=False,
        verbose_name="Forzar mostrar onboarding",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Perfil mobile"
        verbose_name_plural = "Perfiles mobile"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["country"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return f"Perfil mobile de {self.user.get_full_name() or self.user.username}"

    ONBOARDING_STEPS = ("gender", "preferred_size")

    def onboarding_pending_steps(self):
        pending = []
        if self.gender in ("", GenderChoices.UNDISCLOSED):
            pending.append("gender")
        if not self.preferred_size:
            pending.append("preferred_size")
        return pending

    def onboarding_status(self):
        pending = self.onboarding_pending_steps()
        completed = (self.onboarding_completed or not pending) and not self.onboarding_force_show
        return {
            "completed": completed,
            "pending_steps": pending,
            "force_show": self.onboarding_force_show,
        }
