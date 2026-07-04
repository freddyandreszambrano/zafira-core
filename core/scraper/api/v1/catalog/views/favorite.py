from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.scraper.api.v1.catalog.outputs import ProductListOutput, ProductOutput
from core.scraper.models import Favorite, Product


class FavoriteListApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(favorited_by__user=request.user).order_by(
            "-favorited_by__created_at"
        )
        output = ProductListOutput(products, request=request)
        return Response(output.data)

    def post(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        Favorite.objects.get_or_create(user=request.user, product=product)
        output = ProductOutput(product, request=request)
        return Response(
            {"message": "Agregado a favoritos", "product": output.data},
            status=status.HTTP_201_CREATED,
        )


class FavoriteDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id, *args, **kwargs):
        Favorite.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(
            {"message": "Eliminado de favoritos"},
            status=status.HTTP_200_OK,
        )
