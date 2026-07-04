import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from core.auth.utils.email import send_password_reset_code_email

User = get_user_model()

CODE_TTL_MINUTES = 15


class PasswordResetApi:
    invalid_code_message = "El codigo es invalido o ha expirado."

    def request_reset(self, email):
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return None

        code = self._generate_code()
        user.email_reset_token = make_password(code)
        user.email_reset_expires_at = timezone.now() + timedelta(minutes=CODE_TTL_MINUTES)
        user.password_reset_pending = True
        user.save(
            update_fields=[
                "email_reset_token",
                "email_reset_expires_at",
                "password_reset_pending",
            ]
        )
        send_password_reset_code_email(user.email, user.get_full_name(), code)
        return user

    def confirm_reset(self, email, code, password):
        user = User.objects.filter(email__iexact=email).first()
        if not self.is_valid_code(user, code):
            return False

        user.set_password(password)
        user.email_reset_token = None
        user.email_reset_expires_at = None
        user.password_reset_pending = False
        user.password_reset_count = (user.password_reset_count or 0) + 1
        user.last_password_reset_at = timezone.now()
        user.save(
            update_fields=[
                "password",
                "email_reset_token",
                "email_reset_expires_at",
                "password_reset_pending",
                "password_reset_count",
                "last_password_reset_at",
                "last_password_change_at",
            ]
        )
        return True

    def is_valid_code(self, user, code):
        if user is None or not user.password_reset_pending or not user.email_reset_token:
            return False
        if not user.email_reset_expires_at or user.email_reset_expires_at < timezone.now():
            return False
        return check_password(code, user.email_reset_token)

    def _generate_code(self):
        return f"{secrets.randbelow(1000000):06d}"
