import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from core.auth.models import User
from core.security.forms import ExternalProviderForm
from core.security.models import ExternalProvider


class ExternalProviderModelTests(TestCase):
    def test_create_autogenerates_client_id(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        uuid.UUID(str(provider.client_id))
        self.assertTrue(provider.is_active)
        self.assertEqual(str(provider), "ZAFIRA-IA")

    def test_client_id_unique(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExternalProvider.objects.create(
                    name="Otro servicio",
                    client_id=provider.client_id,
                    client_secret="secret2",
                )

    def test_name_unique(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret2")

    def test_to_json_excludes_client_secret(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        payload = provider.to_json()
        self.assertEqual(payload["name"], "ZAFIRA-IA")
        self.assertEqual(payload["client_id"], str(provider.client_id))
        self.assertTrue(payload["is_active"])
        self.assertNotIn("client_secret", payload)


class ExternalProviderFormTests(TestCase):
    def test_autogenerates_secret_when_empty(self):
        form = ExternalProviderForm(
            data={"name": "ZAFIRA-IA", "client_secret": "", "is_active": True}
        )
        self.assertTrue(form.is_valid(), form.errors)
        provider = form.save()
        self.assertGreaterEqual(len(provider.client_secret), 32)

    def test_keeps_given_secret(self):
        form = ExternalProviderForm(
            data={"name": "ZAFIRA-IA", "client_secret": "mi-secreto", "is_active": True}
        )
        self.assertTrue(form.is_valid(), form.errors)
        provider = form.save()
        self.assertEqual(provider.client_secret, "mi-secreto")

    def test_rejects_duplicated_name(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        form = ExternalProviderForm(
            data={"name": "ZAFIRA-IA", "client_secret": "", "is_active": True}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class ExternalProviderViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@zafira.local",
            password="admin",
            dni="0102030405",
        )
        self.client.force_login(self.user)

    def test_list_search_returns_providers_without_secret(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["recordsTotal"], 1)
        self.assertEqual(payload["data"][0]["name"], "ZAFIRA-IA")
        self.assertNotIn("client_secret", payload["data"][0])

    def test_list_search_filters_by_client_id(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        ExternalProvider.objects.create(name="Otro servicio", client_secret="secret2")
        response = self.client.post(
            reverse("external_provider_list"),
            {
                "action": "search",
                "page": 1,
                "page_size": 10,
                "search[value]": str(provider.client_id),
            },
        )
        payload = response.json()
        self.assertEqual(payload["recordsTotal"], 1)
        self.assertEqual(payload["data"][0]["client_id"], str(provider.client_id))

    def test_create_validate_data_detects_duplicated_name(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(
            reverse("external_provider_create"),
            {"action": "validate_data", "pattern": "name", "name": "zafira-ia"},
        )
        self.assertFalse(response.json()["valid"])
