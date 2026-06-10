from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_email(email, user_name, reset_link):
    subject = "Resetea tu contraseña - ZAFIRA"
    message = (
        f"Hola {user_name},\n\n"
        f"Hemos recibido una solicitud para resetear tu contraseña.\n"
        f"Haz clic en el siguiente enlace para continuar:\n\n"
        f"{reset_link}\n\n"
        f"Si no realizaste esta solicitud, puedes ignorar este mensaje.\n\n"
        f"Saludos,\nEl equipo de ZAFIRA"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)


def send_welcome_email(email, user_name, temporary_password=None):
    subject = "Bienvenido a ZAFIRA"
    password_line = f"Contraseña temporal: {temporary_password}\n" if temporary_password else ""
    message = (
        f"Hola {user_name},\n\n"
        f"Tu cuenta en ZAFIRA ha sido creada exitosamente.\n\n"
        f"Usuario: {email}\n"
        f"{password_line}\n"
        f"Para acceder, visita: {settings.FRONTEND_URL}\n\n"
        f"Saludos,\nEl equipo de ZAFIRA"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
