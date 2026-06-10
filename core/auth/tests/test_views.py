from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.auth.models import User


class UserCrudAnonymousPostTests(TestCase):
    def test_search_redirects_to_login_without_data(self):
        response = self.client.post(
            reverse("user_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(settings.LOGIN_URL))

    def test_add_redirects_and_does_not_create(self):
        response = self.client.post(
            reverse("user_create"),
            {
                "action": "add",
                "username": "intruso",
                "email": "intruso@zafira.local",
                "dni": "0999999999",
                "password1": "ClaveSegura123",
                "password2": "ClaveSegura123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="intruso").exists())

    def test_change_state_redirects_and_does_not_toggle(self):
        user = User.objects.create_user(
            username="operador",
            email="operador@zafira.local",
            password="secret123",
            dni="0911111111",
        )
        response = self.client.post(
            reverse("user_list"),
            {"action": "change_state", "id": user.pk},
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
