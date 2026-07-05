from django.test import SimpleTestCase

from core.tryon.services.garment_mapping import garment_type_for_category


class GarmentMappingTests(SimpleTestCase):
    def test_lower_body_categories(self):
        for category in ("pantalones", "Jeans", "faldas", "SHORTS", "joggers"):
            self.assertEqual(garment_type_for_category(category), "lower_body")

    def test_dress_categories(self):
        for category in ("vestidos", "Vestido midi", "enterizos"):
            self.assertEqual(garment_type_for_category(category), "dress")

    def test_upper_body_default(self):
        for category in ("camisetas", "chaquetas", "", None, "accesorios"):
            self.assertEqual(garment_type_for_category(category), "upper_body")
