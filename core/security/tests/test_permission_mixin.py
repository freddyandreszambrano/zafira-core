from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from core.auth.models import User
from core.security.models import ExternalProvider, Group, GroupPermission, Module


class AnonymousPostTests(TestCase):
    def test_search_redirects_to_login_without_data(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_add_redirects_and_does_not_create(self):
        response = self.client.post(
            reverse("external_provider_create"),
            {"action": "add", "name": "Intruso", "client_secret": "hack", "is_active": True},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ExternalProvider.objects.exists())

    def test_edit_redirects_and_does_not_change(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(
            reverse("external_provider_update", args=[provider.pk]),
            {"action": "edit", "name": "Hackeado", "client_secret": "hack", "is_active": True},
        )
        self.assertEqual(response.status_code, 302)
        provider.refresh_from_db()
        self.assertEqual(provider.name, "ZAFIRA-IA")

    def test_delete_redirects_and_does_not_delete(self):
        provider = ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(reverse("external_provider_delete", args=[provider.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ExternalProvider.objects.filter(pk=provider.pk).exists())

    def test_change_state_redirects_in_every_list_view(self):
        for url_name in ("module_list", "module_type_list", "group_list"):
            response = self.client.post(reverse(url_name), {"action": "change_state", "id": 1})
            self.assertEqual(response.status_code, 302, url_name)
            self.assertTrue(response.url.startswith(settings.LOGIN_URL), url_name)


class AuthenticatedPostPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="operador",
            email="operador@zafira.local",
            password="secret123",
            dni="0911111111",
        )
        self.client.force_login(self.user)
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")

    def _set_group_session(self, group):
        session = self.client.session
        session["group"] = group.to_json()
        session.save()

    def test_post_without_group_in_session_returns_403(self):
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 403)

    def test_post_with_group_lacking_permission_returns_403(self):
        self._set_group_session(Group.objects.create(name="Consulta"))
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 403)

    def test_post_with_group_having_permission_succeeds(self):
        group = Group.objects.create(name="Gestores")
        module = Module.objects.create(
            name="Proveedores externos", url="/security/external_provider/"
        )
        permission = Permission.objects.get(codename="view_externalprovider")
        GroupPermission.objects.create(group=group, module=module, permission=permission)
        self._set_group_session(group)
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recordsTotal"], 1)


class SuperuserPostTests(TestCase):
    def setUp(self):
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@zafira.local",
            password="admin",
            dni="0102030405",
        )
        self.client.force_login(superuser)

    def test_post_bypasses_group_check(self):
        ExternalProvider.objects.create(name="ZAFIRA-IA", client_secret="secret")
        response = self.client.post(
            reverse("external_provider_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recordsTotal"], 1)
