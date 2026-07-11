from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from core.scraper.models import FavoriteOutfit, Product


def _create_product(**overrides):
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


class FavoriteOutfitApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="freddy", email="freddy@test.com", password="secret123"
        )
        self.top = _create_product(id_external="ext-top", name="Camisa Azul")
        self.bottom = _create_product(
            id_external="ext-bottom", name="Jean Clásico", category="jeans"
        )
        self.client.force_authenticate(self.user)

    def test_save_outfit(self):
        response = self.client.post(
            "/api/v1/catalog/favorites/outfits/",
            {
                "top_id": self.top.id,
                "bottom_id": self.bottom.id,
                "result_image_url": "http://core.test/media/result.png",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        outfit = response.json()["outfit"]
        self.assertEqual(outfit["top"]["id"], self.top.id)
        self.assertEqual(outfit["bottom"]["id"], self.bottom.id)
        self.assertEqual(outfit["result_image_url"], "http://core.test/media/result.png")

    def test_save_same_pair_twice_updates_image_without_duplicating(self):
        for image in ("http://core.test/a.png", "http://core.test/b.png"):
            self.client.post(
                "/api/v1/catalog/favorites/outfits/",
                {
                    "top_id": self.top.id,
                    "bottom_id": self.bottom.id,
                    "result_image_url": image,
                },
                format="json",
            )
        self.assertEqual(FavoriteOutfit.objects.count(), 1)
        self.assertEqual(FavoriteOutfit.objects.get().result_image_url, "http://core.test/b.png")

    def test_save_with_unknown_product_returns_404(self):
        response = self.client.post(
            "/api/v1/catalog/favorites/outfits/",
            {"top_id": self.top.id, "bottom_id": 99999},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_list_only_own_outfits(self):
        FavoriteOutfit.objects.create(user=self.user, top=self.top, bottom=self.bottom)
        other = get_user_model().objects.create_user(
            username="otro", email="otro@test.com", password="secret123", dni="0999999999"
        )
        FavoriteOutfit.objects.create(user=other, top=self.top, bottom=self.bottom)

        response = self.client.get("/api/v1/catalog/favorites/outfits/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_delete_own_outfit_only(self):
        mine = FavoriteOutfit.objects.create(user=self.user, top=self.top, bottom=self.bottom)
        other = get_user_model().objects.create_user(
            username="otro", email="otro@test.com", password="secret123", dni="0999999999"
        )
        theirs = FavoriteOutfit.objects.create(user=other, top=self.top, bottom=self.bottom)

        self.client.delete(f"/api/v1/catalog/favorites/outfits/{mine.id}/")
        self.client.delete(f"/api/v1/catalog/favorites/outfits/{theirs.id}/")

        self.assertFalse(FavoriteOutfit.objects.filter(id=mine.id).exists())
        self.assertTrue(FavoriteOutfit.objects.filter(id=theirs.id).exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/v1/catalog/favorites/outfits/")
        self.assertEqual(response.status_code, 401)
