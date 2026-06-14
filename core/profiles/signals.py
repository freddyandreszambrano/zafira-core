from django.db.models.signals import post_save
from django.dispatch import receiver

from core.auth.models import User

from core.utils.enums import UserTypeChoices

from .models import MobileProfile, UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if instance.user_type == UserTypeChoices.MOBILE:
        MobileProfile.objects.get_or_create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)
