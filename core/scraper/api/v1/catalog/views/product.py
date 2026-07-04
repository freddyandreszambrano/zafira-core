from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.scraper.api.v1.catalog.serializers.product import ProductSerializer
from core.scraper.models import Product
from core.scraper.services_live import refresh_product_from_live


class ProductListApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = Product.objects.all()

        gender = request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__icontains=category)

        serializer = ProductSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class ProductDetailApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)


class ProductLiveApiView(APIView):
    """Consulta la página oficial de la tienda en este momento y devuelve
    el producto con precio y tallas reales (actualizando también la BD)."""

    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        fresh = refresh_product_from_live(product)

        serializer = ProductSerializer(product, context={"request": request})
        return Response(
            {
                "live": fresh,  # False = la tienda no respondió; datos de la BD
                "product": serializer.data,
            }
        )
