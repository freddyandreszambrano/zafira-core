"""Create the initial production administrator from environment variables."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

REQUIRED_ENVIRONMENT_VARIABLES = (
    "DJANGO_SUPERUSER_USERNAME",
    "DJANGO_SUPERUSER_EMAIL",
    "DJANGO_SUPERUSER_DNI",
    "DJANGO_SUPERUSER_PASSWORD",
)


class Command(BaseCommand):
    help = "Crea el superusuario inicial desde variables de entorno, de forma idempotente."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        dni = os.getenv("DJANGO_SUPERUSER_DNI", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        values = {
            "DJANGO_SUPERUSER_USERNAME": username,
            "DJANGO_SUPERUSER_EMAIL": email,
            "DJANGO_SUPERUSER_DNI": dni,
            "DJANGO_SUPERUSER_PASSWORD": password,
        }

        if not any(values.values()):
            self.stdout.write("Superusuario inicial no configurado; se omite su creación.")
            return

        missing = [name for name in REQUIRED_ENVIRONMENT_VARIABLES if not values[name]]
        if missing:
            missing_names = ", ".join(missing)
            raise CommandError(
                f"Configura todas las variables del superusuario. Faltan: {missing_names}"
            )

        user_model = get_user_model()
        email = user_model.objects.normalize_email(email)
        existing_user = user_model.objects.filter(username=username).first()

        if existing_user:
            self._validate_existing_user(existing_user, email, dni)
            self.stdout.write("El superusuario inicial ya existe; no se modificó su contraseña.")
            return

        conflicting_user = user_model.objects.filter(email=email).first()
        if not conflicting_user:
            conflicting_user = user_model.objects.filter(dni=dni).first()
        if conflicting_user:
            raise CommandError(
                "El email o DNI configurado ya pertenece a otro usuario; "
                "no se puede crear el superusuario inicial."
            )

        candidate = user_model(username=username, email=email, dni=dni)
        try:
            validate_password(password, user=candidate)
        except ValidationError as error:
            raise CommandError("Contraseña de superusuario insegura: " + " ".join(error.messages))

        user_model.objects.create_superuser(
            username=username,
            email=email,
            dni=dni,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS("Superusuario inicial creado correctamente."))

    @staticmethod
    def _validate_existing_user(user, email, dni):
        if not user.is_staff or not user.is_superuser:
            raise CommandError(
                "El username configurado ya existe, pero no corresponde a un superusuario."
            )
        if user.email != email or user.dni != dni:
            raise CommandError(
                "El username configurado ya existe, pero su email o DNI "
                "no coincide con la configuración."
            )
