import base64
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from core.profiles.models import MobileProfile
from core.tryon.models import TryOnJob
from core.tryon.services.zafira_ia_client import ZafiraIaRejected, ZafiraIaUnavailable
from core.tryon.task.tryon import generate_try_on_task
from core.tryon.tests.test_models import create_product

TINY_GIF = base64.b64decode(b"R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")


def make_job(**extra):
    user = get_user_model().objects.create_user(
        username="freddy", email="freddy@test.com", password="secret123"
    )
    mobile_profile, _ = MobileProfile.objects.get_or_create(user=user)
    mobile_profile.try_on_photo = SimpleUploadedFile("me.gif", TINY_GIF, content_type="image/gif")
    mobile_profile.save(update_fields=["try_on_photo"])
    product = create_product()
    return TryOnJob.objects.create(
        user=user,
        product=product,
        garment_image_url=product.image_urls[0],
        garment_type="upper_body",
        **extra,
    )


def make_outfit_job():
    return make_job(
        extra_garment_image_url="https://store.example.com/img/pants.jpg",
        extra_garment_type="lower_body",
    )


def _b64_result(payload):
    return {"result_image_b64": base64.b64encode(payload).decode()}


@override_settings(SITE_URL="http://core.test")
class GenerateTryOnTaskTests(TestCase):
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_success_saves_result_and_completes(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.return_value = {
            "external_ref": str(job.id),
            "result_image_b64": base64.b64encode(b"generated-image").decode(),
        }

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.COMPLETED)
        self.assertTrue(job.result_image)
        self.assertEqual(job.result_image.read(), b"generated-image")

        kwargs = mock_client_cls.return_value.try_on.call_args.kwargs
        self.assertTrue(kwargs["person_image_url"].startswith("http://core.test/"))
        self.assertEqual(kwargs["garment_image_url"], job.garment_image_url)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_rejected_marks_failed_without_retry(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaRejected("blocked")

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertNotEqual(job.error_message, "")
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 1)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_unavailable_retries_then_fails(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaUnavailable("down")

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 3)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_rate_limited_uses_quota_message(self, mock_client_cls):
        from core.tryon.task.tryon import QUOTA_ERROR

        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaUnavailable(
            "quota", code="RATE_LIMITED"
        )

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertEqual(job.error_message, QUOTA_ERROR)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 3)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_content_rejected_uses_content_message(self, mock_client_cls):
        from core.tryon.task.tryon import CONTENT_ERROR

        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaRejected(
            "blocked", code="GENERATION_REJECTED"
        )

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertEqual(job.error_message, CONTENT_ERROR)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 1)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_missing_job_is_noop(self, mock_client_cls):
        generate_try_on_task.apply(args=["00000000-0000-0000-0000-000000000000"])
        mock_client_cls.assert_not_called()

    @mock.patch("core.tryon.task.tryon._mean_diff", return_value=50.0)
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_outfit_applies_legs_on_first_attempt(self, mock_client_cls, _diff):
        job = make_outfit_job()
        mock_client_cls.return_value.try_on.side_effect = [
            _b64_result(b"torso"),
            _b64_result(b"torso+legs"),
        ]

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.COMPLETED)
        self.assertEqual(job.result_image.read(), b"torso+legs")
        # 1 paso torso + 1 paso piernas (se aplicó al primer intento, sin reintento)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 2)

    @mock.patch("core.tryon.task.tryon._mean_diff", side_effect=[1.0, 50.0])
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_outfit_retries_legs_when_first_is_noop(self, mock_client_cls, _diff):
        job = make_outfit_job()
        mock_client_cls.return_value.try_on.side_effect = [
            _b64_result(b"torso"),
            _b64_result(b"noop"),  # paso 2 intento 1: no aplicó (diff bajo)
            _b64_result(b"torso+legs"),  # paso 2 intento 2: aplicó (diff alto)
        ]

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.COMPLETED)
        self.assertEqual(job.result_image.read(), b"torso+legs")
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 3)

    @mock.patch("core.tryon.task.tryon._mean_diff", return_value=1.0)
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_outfit_keeps_torso_when_legs_never_apply(self, mock_client_cls, _diff):
        job = make_outfit_job()
        mock_client_cls.return_value.try_on.side_effect = [
            _b64_result(b"torso"),
            _b64_result(b"noop-1"),
            _b64_result(b"noop-2"),
        ]

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.COMPLETED)
        # Ningún intento aplicó las piernas -> conserva el paso 1 (torso)
        self.assertEqual(job.result_image.read(), b"torso")
        # 1 torso + 2 intentos de piernas (máximo)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 3)
