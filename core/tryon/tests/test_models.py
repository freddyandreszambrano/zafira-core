from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.scraper.models import Product
from core.tryon.models import TryOnJob


def create_product(**overrides):
    defaults = {
        "id_external": "ext-1",
        "name": "Camiseta básica",
        "category": "camisetas",
        "gender": "M",
        "url": "https://store.example.com/p/1",
        "price": "19.99",
        "image_urls": ["https://store.example.com/img/1.jpg"],
        "extracted_at": timezone.now(),
    }
    defaults.update(overrides)
    return Product.objects.create(**defaults)


class TryOnJobModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="freddy", email="freddy@test.com", password="secret123"
        )
        self.product = create_product()

    def test_defaults_and_str(self):
        job = TryOnJob.objects.create(
            user=self.user,
            product=self.product,
            garment_image_url=self.product.image_urls[0],
            garment_type="upper_body",
        )
        self.assertEqual(job.status, TryOnJob.Status.PENDING)
        self.assertIn("pending", str(job))

    def test_to_json_api_without_result(self):
        job = TryOnJob.objects.create(
            user=self.user,
            product=self.product,
            garment_image_url=self.product.image_urls[0],
            garment_type="upper_body",
        )
        data = job.to_json_api()
        self.assertEqual(data["id"], str(job.id))
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["product_id"], self.product.id)
        self.assertIsNone(data["result_url"])
        self.assertEqual(data["error_message"], "")
