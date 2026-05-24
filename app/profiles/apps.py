from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.profiles'

    def ready(self):
        """Import signals when app is ready."""
        import app.profiles.signals  # noqa
