from django.test import TestCase

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.auth.models import User
from core.profiles.models import MobileProfile


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

        onboarding = response.json()["user"]["onboarding"]
        self.assertFalse(onboarding["completed"])
        self.assertFalse(onboarding["force_show"])
        self.assertEqual(onboarding["pending_steps"], ["gender", "preferred_size"])

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


class MobileProfileUpdateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="mobile",
            email="mobile@zafira.local",
            dni="1234567890",
            password="secret12345",
        )
        self.client.force_authenticate(user=self.user)

    def test_update_marks_onboarding_completed(self):
        response = self.client.patch(
            "/api/v1/auth/profile/update/",
            {"gender": "femenino", "preferred_size": "M", "onboarding_completed": True},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        onboarding = response.json()["user"]["onboarding"]
        self.assertTrue(onboarding["completed"])
        self.assertEqual(onboarding["pending_steps"], [])

        profile = MobileProfile.objects.get(user=self.user)
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.gender, "femenino")
        self.assertEqual(profile.preferred_size, "M")

    def test_completing_onboarding_clears_force_show(self):
        MobileProfile.objects.filter(user=self.user).update(onboarding_force_show=True)

        response = self.client.patch(
            "/api/v1/auth/profile/update/",
            {
                "gender": "masculino",
                "preferred_size": "L",
                "onboarding_completed": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        onboarding = response.json()["user"]["onboarding"]
        self.assertTrue(onboarding["completed"])
        self.assertFalse(onboarding["force_show"])

        profile = MobileProfile.objects.get(user=self.user)
        self.assertFalse(profile.onboarding_force_show)
        self.assertTrue(profile.onboarding_completed)
