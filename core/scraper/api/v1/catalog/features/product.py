from core.scraper.models import Product
from core.scraper.services_live import refresh_product_from_live

# Techo defensivo por respuesta; la app pagina con limit/offset
MAX_PAGE_SIZE = 100


def _to_int(value, default=None, maximum=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    if result < 0:
        return default
    return min(result, maximum) if maximum else result


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

        # Paginación opcional (sin params responde completo: retrocompatible
        # con recomendación y clientes viejos)
        offset = _to_int(self.request.query_params.get("offset"), default=0)
        limit = _to_int(self.request.query_params.get("limit"), maximum=MAX_PAGE_SIZE)
        if limit:
            queryset = queryset[offset : offset + limit]
        return queryset

    def get_product(self, pk):
        return Product.objects.filter(pk=pk).first()

    def refresh_live(self, product):
        return refresh_product_from_live(product)
