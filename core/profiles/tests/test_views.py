from django.test import TestCase
from django.urls import reverse

from core.auth.models import User
from core.profiles.models import MobileProfile


class UserProfileViewSetTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)


class MobileProfileViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@zafira.local",
            dni="0102030405",
            password="admin12345",
        )
        self.user = User.objects.create_user(
            username="mobile",
            email="mobile@zafira.local",
            dni="0912345678",
            password="secret12345",
        )
        self.profile = MobileProfile.objects.get(user=self.user)
        self.profile.preferred_size = "M"
        self.profile.country = "Ecuador"
        self.profile.save()
        self.client.force_login(self.admin)

    def test_list_returns_mobile_profiles(self):
        response = self.client.post(
            reverse("mobile_profile_list"),
            {"action": "search", "page": 1, "page_size": 10},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["recordsTotal"], 1)
        self.assertEqual(payload["data"][0]["username"], "mobile")

    def test_detail_view_is_available(self):
        response = self.client.get(reverse("mobile_profile_detail", args=[self.profile.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mobile@zafira.local")
