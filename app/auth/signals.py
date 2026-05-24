"""Django signals for authentication module."""

from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from .models import User
from .utils import create_default_groups


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create auth token when a new user is created."""
    if created:
        Token.objects.get_or_create(user=instance)


@receiver(post_migrate)
def create_groups_on_migrate(sender, **kwargs):
    """Create default groups after migrations."""
    # Only run for auth app (label is 'users')
    if sender.label == 'users':
        try:
            create_default_groups()
        except Exception as e:
            print(f'Error creating default groups: {e}')
