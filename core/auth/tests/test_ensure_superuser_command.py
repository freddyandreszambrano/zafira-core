import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from core.auth.management.commands.ensure_superuser import REQUIRED_ENVIRONMENT_VARIABLES
from core.auth.models import User
from core.utils.enums import UserTypeChoices


class EnsureSuperuserCommandTests(TestCase):
    credentials = {
        "DJANGO_SUPERUSER_USERNAME": "production-admin",
        "DJANGO_SUPERUSER_EMAIL": "admin@zafira.local",
        "DJANGO_SUPERUSER_DNI": "0102030405",
        "DJANGO_SUPERUSER_PASSWORD": "CorrectHorseBatteryStaple!2026",
    }

    def environment(self, **values):
        environment = {name: values.get(name, "") for name in REQUIRED_ENVIRONMENT_VARIABLES}
        return patch.dict(os.environ, environment, clear=False)

    def test_skips_when_superuser_environment_is_not_configured(self):
        output = StringIO()

        with self.environment():
            call_command("ensure_superuser", stdout=output)

        self.assertFalse(User.objects.exists())
        self.assertIn("no configurado", output.getvalue())

    def test_creates_superuser_from_environment(self):
        with self.environment(**self.credentials):
            call_command("ensure_superuser")

        user = User.objects.get(username=self.credentials["DJANGO_SUPERUSER_USERNAME"])
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.user_type, UserTypeChoices.ADMIN)
        self.assertTrue(user.check_password(self.credentials["DJANGO_SUPERUSER_PASSWORD"]))

    def test_existing_superuser_is_not_modified_or_reset(self):
        with self.environment(**self.credentials):
            call_command("ensure_superuser")

        updated_credentials = {
            **self.credentials,
            "DJANGO_SUPERUSER_PASSWORD": "AnotherCorrectPassword!2026",
        }
        with self.environment(**updated_credentials):
            call_command("ensure_superuser")

        user = User.objects.get(username=self.credentials["DJANGO_SUPERUSER_USERNAME"])
        self.assertTrue(user.check_password(self.credentials["DJANGO_SUPERUSER_PASSWORD"]))
        self.assertFalse(user.check_password(updated_credentials["DJANGO_SUPERUSER_PASSWORD"]))

    def test_rejects_partial_environment_configuration(self):
        with self.environment(DJANGO_SUPERUSER_USERNAME="production-admin"):
            with self.assertRaises(CommandError):
                call_command("ensure_superuser")
