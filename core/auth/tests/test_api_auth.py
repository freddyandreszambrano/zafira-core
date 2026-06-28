from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.auth.models import User


class AuthTokenApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="mobile",
            email="mobile@zafira.local",
            dni="1234567890",
            password="secret12345",
        )

    def test_versioned_endpoint_returns_token(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "mobile", "password": "secret12345"},
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
                "dni": self.user.dni,
                "full_name": self.user.get_full_name(),
                "user_type": self.user.user_type,
                "token": Token.objects.get(user=self.user).key,
            },
        )

    def test_invalid_app_source_return_bad_request(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "mobile", "password": "secret12345"},
            format="json",
            HTTP_APP_SOURCE="unknown-app",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"message": "Invalid app source"})

    def test_invalid_credentials_return_bad_request(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "mobile", "password": "bad-password"},
            format="json",
            HTTP_APP_SOURCE="zafira-app",
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("token", response.json())
