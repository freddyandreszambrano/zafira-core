from django.core.cache import cache

from core.recommend.services.gemini import (
    get_favorites_recommendations,
    get_multiple_recommendations,
)
from core.scraper.models import Product

_PRODUCTS_CACHE_TTL = 300


class RecommendApi:
    def __init__(self, data):
        self.data = data

    def build_outfits(self):
        product_ids = list(self.data.get("product_ids", []))
        occasion = self.data["occasion"]
        gender = self.data.get("gender", "hombre")

        if product_ids:
            favorites = list(Product.objects.filter(id__in=product_ids))
            return get_favorites_recommendations(favorites, occasion, gender=gender)

        return get_multiple_recommendations(
            self.get_products(),
            occasion,
            gender=gender,
            exclude_ids=list(self.data.get("exclude_ids", [])),
        )

    def get_products(self):
        store_filter = self.data.get("store", "all")
        cache_key = f"products_available_{store_filter}"
        products = cache.get(cache_key)
        if products is not None:
            return products

        queryset = Product.objects.filter(availability="available")
        if store_filter != "all":
            queryset = queryset.filter(store=store_filter)
        products = list(queryset)
        cache.set(cache_key, products, _PRODUCTS_CACHE_TTL)
        return products
