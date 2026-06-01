from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from .models import User
from .utils import create_default_groups


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)


@receiver(post_migrate)
def create_groups_on_migrate(sender, **kwargs):
    if sender.label != 'users':
        return
    try:
        create_default_groups()
    except Exception as exc:
        print(f'Error creando grupos por defecto: {exc}')
