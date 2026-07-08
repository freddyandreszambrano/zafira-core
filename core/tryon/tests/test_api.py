import base64
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from rest_framework.test import APITestCase

from core.profiles.models import MobileProfile
from core.tryon.models import TryOnJob
from core.tryon.tests.test_models import create_product

TINY_GIF = base64.b64decode(b"R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")


class InlineThread:
    """Sustituye a threading.Thread en tests: ejecuta el target al instante
    para que el resultado del hilo sea observable dentro del mismo request."""

    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        self._target()


class TryOnApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="freddy", email="freddy@test.com", password="secret123"
        )
        self.profile, _ = MobileProfile.objects.get_or_create(user=self.user)
        self.profile.try_on_photo = SimpleUploadedFile("me.gif", TINY_GIF, content_type="image/gif")
        self.profile.save(update_fields=["try_on_photo"])
        self.user = get_user_model().objects.get(pk=self.user.pk)
        self.product = create_product()
        self.client.force_authenticate(self.user)
        # Los tests no deben depender de la red: la verificación real de URLs
        # alcanzables se simula devolviendo la primera imagen del producto.
        patcher = mock.patch(
            "core.tryon.api.v1.tryon.features.tryon._first_reachable_image",
            side_effect=lambda product: (product.image_urls[0] if product.image_urls else None),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("core.tryon.api.v1.tryon.features.tryon.dispatch_generate_try_on")
    def test_create_job(self, mock_dispatch):
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )

        self.assertEqual(response.status_code, 201)
        job_data = response.json()["job"]
        self.assertEqual(job_data["status"], "pending")
        self.assertEqual(job_data["product_id"], self.product.id)

        job = TryOnJob.objects.get(id=job_data["id"])
        self.assertEqual(job.garment_type, "upper_body")
        self.assertEqual(job.garment_image_url, self.product.image_urls[0])
        mock_dispatch.assert_called_once_with(str(job.id))

    @override_settings(TRYON_USE_CELERY=False)
    @mock.patch("core.tryon.task.dispatch.threading.Thread", new=InlineThread)
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_create_job_direct_mode_completes_inline(self, mock_client_cls):
        mock_client_cls.return_value.try_on.return_value = {
            "external_ref": "x",
            "result_image_b64": base64.b64encode(b"generated-image").decode(),
        }

        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )

        self.assertEqual(response.status_code, 201)
        job_data = response.json()["job"]
        self.assertEqual(job_data["status"], "completed")
        self.assertIsNotNone(job_data["result_url"])
        mock_client_cls.return_value.try_on.assert_called_once()

    def test_create_without_photo_returns_code(self):
        self.profile.try_on_photo.delete(save=True)
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "TRY_ON_PHOTO_REQUIRED")

    def test_create_without_product_image_returns_code(self):
        bare = create_product(id_external="ext-2", image_urls=[])
        response = self.client.post("/api/v1/tryon/", {"product_ids": [bare.id]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "PRODUCT_IMAGE_REQUIRED")

    def test_create_with_invalid_products_returns_code(self):
        for payload in ({}, {"product_ids": []}, {"product_ids": [1, 2]}, {"product_ids": [99999]}):
            response = self.client.post("/api/v1/tryon/", payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["code"], "INVALID_PRODUCTS")

    @mock.patch("core.tryon.api.v1.tryon.features.tryon.dispatch_generate_try_on")
    def test_get_job_only_for_owner(self, mock_dispatch):
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )
        job_id = response.json()["job"]["id"]

        detail = self.client.get(f"/api/v1/tryon/{job_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["job"]["id"], job_id)

        other = get_user_model().objects.create_user(
            username="otro", email="otro@test.com", password="secret123", dni="0999999999"
        )
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(f"/api/v1/tryon/{job_id}/").status_code, 404)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post("/api/v1/tryon/", {"product_ids": [1]}, format="json").status_code,
            401,
        )
