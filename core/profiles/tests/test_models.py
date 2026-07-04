from django.test import TestCase

from core.auth.models import User
from core.utils.enums import GenderChoices


class MobileProfileOnboardingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mobile",
            email="mobile@zafira.local",
            dni="1234567890",
            password="secret12345",
        )
        self.profile = self.user.mobile_profile

    def test_new_profile_has_both_steps_pending(self):
        status = self.profile.onboarding_status()

        self.assertEqual(self.profile.onboarding_pending_steps(), ["gender", "preferred_size"])
        self.assertFalse(status["completed"])
        self.assertEqual(status["pending_steps"], ["gender", "preferred_size"])

    def test_completed_when_data_present(self):
        self.profile.gender = GenderChoices.FEMALE
        self.profile.preferred_size = "M"

        self.assertEqual(self.profile.onboarding_pending_steps(), [])
        self.assertTrue(self.profile.onboarding_status()["completed"])

    def test_undisclosed_gender_keeps_step_pending(self):
        self.profile.gender = GenderChoices.UNDISCLOSED
        self.profile.preferred_size = "M"

        self.assertIn("gender", self.profile.onboarding_pending_steps())
        self.assertFalse(self.profile.onboarding_status()["completed"])

    def test_explicit_flag_completes_even_with_missing_data(self):
        self.profile.onboarding_completed = True

        status = self.profile.onboarding_status()

        self.assertTrue(status["completed"])
        self.assertEqual(status["pending_steps"], ["gender", "preferred_size"])

    def test_force_show_reopens_even_when_completed(self):
        self.profile.gender = GenderChoices.FEMALE
        self.profile.preferred_size = "M"
        self.profile.onboarding_completed = True
        self.profile.onboarding_force_show = True

        status = self.profile.onboarding_status()

        self.assertFalse(status["completed"])
        self.assertTrue(status["force_show"])
