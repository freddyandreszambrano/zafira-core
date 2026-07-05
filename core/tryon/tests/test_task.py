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


def make_job():
    user = get_user_model().objects.create_user(
        username="freddy", email="freddy@test.com", password="secret123"
    )
    mobile_profile, _ = MobileProfile.objects.get_or_create(user=user)
    mobile_profile.try_on_photo = SimpleUploadedFile(
        "me.gif", TINY_GIF, content_type="image/gif"
    )
    mobile_profile.save(update_fields=["try_on_photo"])
    product = create_product()
    return TryOnJob.objects.create(
        user=user,
        product=product,
        garment_image_url=product.image_urls[0],
        garment_type="upper_body",
    )


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
    def test_missing_job_is_noop(self, mock_client_cls):
        generate_try_on_task.apply(args=["00000000-0000-0000-0000-000000000000"])
        mock_client_cls.assert_not_called()
