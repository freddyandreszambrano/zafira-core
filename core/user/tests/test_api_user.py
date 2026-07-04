from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from core.auth.models import User
from core.profiles.models import MobileProfile
from core.utils.enums import GenderChoices, UserTypeChoices


class UserCreateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api_v1_user_create")
        self.payload = {
            "username": "mobile",
            "email": "mobile@zafira.local",
            "dni": "0912345678",
            "password": "ZafiraPass123!",
            "first_name": "Ana",
            "last_name": "Mora",
            "gender": "femenino",
            "preferred_size": "M",
            "style_preferences": {"colors": ["negro", "azul"]},
            "language": "es",
            "country": "Ecuador",
            "push_token": "push-token-123",
        }

    def test_create_mobile_user(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username="mobile")
        self.assertEqual(user.user_type, UserTypeChoices.MOBILE)
        self.assertEqual(user.email, "mobile@zafira.local")

        profile = MobileProfile.objects.get(user=user)
        self.assertEqual(profile.push_token, "push-token-123")
        self.assertEqual(profile.style_preferences, {"colors": ["negro", "azul"]})

    def test_registration_ignores_gender_and_size(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 201)

        profile = MobileProfile.objects.get(user__username="mobile")
        self.assertEqual(profile.gender, GenderChoices.UNDISCLOSED)
        self.assertEqual(profile.preferred_size, "")

    def test_create_rejects_invalid_app_source(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_APP_SOURCE="unknown-app",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "Invalid app source"})
        self.assertFalse(User.objects.filter(username="mobile").exists())

    def test_create_rejects_duplicate_identity_fields(self):
        User.objects.create_user(
            username="mobile",
            email="mobile@zafira.local",
            dni="0912345678",
            password="ZafiraPass123!",
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("username", body)
        self.assertIn("email", body)
        self.assertIn("dni", body)

    def test_create_requires_minimum_payload(self):
        response = self.client.post(
            self.url,
            {"username": "mobile"},
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("email", body)
        self.assertIn("dni", body)
        self.assertIn("password", body)
