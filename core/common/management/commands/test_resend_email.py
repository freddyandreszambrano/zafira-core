"""Envía un correo de prueba para validar la integración de correo (Resend).

Uso:
    python manage.py test_resend_email destino@dominio.com

Respeta settings.EMAIL_BACKEND: con el backend de Resend envía de verdad
(requiere RESEND_API_KEY); con el de consola solo lo imprime.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.common.services.email_service import send_email


class Command(BaseCommand):
    help = "Envía un correo de prueba usando el backend de correo configurado (Resend)."

    def add_arguments(self, parser):
        parser.add_argument("to", help="Correo destino")

    def handle(self, *args, **options):
        to = options["to"]
        self.stdout.write(f"Enviando correo de prueba a {to} vía {settings.EMAIL_BACKEND} ...")
        try:
            sent = send_email(
                subject="Prueba de Resend — ZAFIRA",
                to=to,
                html_body=(
                    "<h2>✅ Resend funciona</h2>"
                    "<p>Correo de prueba enviado con django-anymail desde ZAFIRA-CORE.</p>"
                ),
            )
        except Exception as exc:
            raise CommandError(f"Falló el envío: {exc}") from exc

        if sent:
            self.stdout.write(self.style.SUCCESS(f"Correo enviado correctamente a {to}."))
        else:
            self.stdout.write(self.style.WARNING("El backend reportó 0 envíos."))
