"""Servicio de correo desacoplado.

Usa el sistema nativo de Django (``EmailMultiAlternatives``), por lo que el backend
real lo define ``settings.EMAIL_BACKEND`` (Resend vía django-anymail en este proyecto).

Pensado para moverse luego a una task de Celery sin tocar la lógica: basta envolver
``send_email`` / ``send_templated_email`` en una ``@shared_task``.

Variables de entorno requeridas (ver .env.example):
    RESEND_API_KEY      API key de Resend → settings.ANYMAIL["RESEND_API_KEY"].
    DEFAULT_FROM_EMAIL  Remitente por defecto, ej. "ZAFIRA <no-reply@dominio.com>".
"""
from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email(
    *,
    subject: str,
    to: list[str] | str,
    html_body: str,
    text_body: str | None = None,
    from_email: str | None = None,
    reply_to: list[str] | None = None,
    fail_silently: bool = False,
) -> int:
    """Envía un correo HTML con su alternativa de texto plano.

    Si no se pasa ``text_body`` se deriva del HTML. Devuelve cuántos mensajes
    se enviaron (0 o 1).
    """
    recipients = [to] if isinstance(to, str) else list(to)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body or strip_tags(html_body),
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        reply_to=reply_to,
    )
    message.attach_alternative(html_body, "text/html")
    return message.send(fail_silently=fail_silently)


def send_templated_email(
    *,
    subject: str,
    to: list[str] | str,
    template_name: str,
    context: dict | None = None,
    text_template_name: str | None = None,
    from_email: str | None = None,
    reply_to: list[str] | None = None,
    fail_silently: bool = False,
) -> int:
    """Renderiza un template HTML (y opcionalmente uno de texto) y lo envía."""
    ctx = context or {}
    html_body = render_to_string(template_name, ctx)
    text_body = render_to_string(text_template_name, ctx) if text_template_name else None
    return send_email(
        subject=subject,
        to=to,
        html_body=html_body,
        text_body=text_body,
        from_email=from_email,
        reply_to=reply_to,
        fail_silently=fail_silently,
    )
