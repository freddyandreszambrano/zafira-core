from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.profiles'

    def ready(self):
        import app.profiles.signals  # noqa
