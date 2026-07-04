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
        self.user.refresh_from_db()
        expected_user = self.user.to_json_api()
        expected_token = expected_user.pop("token")
        self.assertEqual(response.json(), {"token": expected_token, "user": expected_user})
        self.assertEqual(expected_token, Token.objects.get(user=self.user).key)

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
