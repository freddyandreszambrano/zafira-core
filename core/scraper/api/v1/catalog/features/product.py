from core.scraper.models import Product
from core.scraper.services_live import refresh_product_from_live


class ProductCatalogApi:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        queryset = Product.objects.all()

        gender = self.request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__icontains=category)

        return queryset

    def get_product(self, pk):
        return Product.objects.filter(pk=pk).first()

    def refresh_live(self, product):
        return refresh_product_from_live(product)
