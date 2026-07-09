from django.test import SimpleTestCase

from core.tryon.services.garment_mapping import (
    garment_type_for_category,
    garment_type_for_product,
)


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


# Categoría real de la tienda que mezcla faldas y vestidos.
_MIXED = "MUJERES/MODA MUJER/FALDAS Y VESTIDOS/FALDAS Y VESTIDOS"


class GarmentTypeForProductTests(SimpleTestCase):
    def test_mixed_category_dresses_by_name(self):
        for name in ("Vestido Largo Floreado", "Vestido Camisero", "Enterizo Short"):
            self.assertEqual(garment_type_for_product(name, _MIXED), "dress")

    def test_mixed_category_skirts_and_shorts_are_lower(self):
        for name in ("Falda Short - Taxi", "Minifalda Denim", "Bermuda Tipo Sastre", "Falda Lápiz"):
            self.assertEqual(garment_type_for_product(name, _MIXED), "lower_body")

    def test_mixed_category_without_hint_defaults_to_dress(self):
        self.assertEqual(garment_type_for_product("Prenda X", _MIXED), "dress")

    def test_non_mixed_categories_follow_category(self):
        # Fuera de la categoría mixta, el nombre no altera nada: se respeta la
        # categoría igual que antes (sin regresión en lo que ya funcionaba).
        self.assertEqual(
            garment_type_for_product("Blusa Floreada", "MUJERES/.../BLUSAS"), "upper_body"
        )
        self.assertEqual(
            garment_type_for_product("Jean Skinny", "MUJERES/.../JEANS Y PANTALONES"), "lower_body"
        )
        self.assertEqual(
            garment_type_for_product("Chaqueta Bomber", "MUJERES/.../CHAQUETAS Y ABRIGOS"),
            "upper_body",
        )
