from celery import shared_task

from core.auth.utils.email import send_password_reset_code_email


@shared_task
def send_password_reset_email_task(email, user_name, code):
    send_password_reset_code_email(email, user_name, code)
