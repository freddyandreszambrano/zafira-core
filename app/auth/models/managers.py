"""Custom managers for User model."""

from django.contrib.auth.models import UserManager
from rest_framework.authtoken.models import Token


class CustomUserManager(UserManager):
    """Custom manager for User model."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular user."""
        if not username:
            raise ValueError('The Username field must be set')

        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Create auth token
        Token.objects.get_or_create(user=user)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(username, email, password, **extra_fields)
