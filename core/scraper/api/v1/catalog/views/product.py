from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.scraper.api.v1.catalog.features import ProductCatalogApi
from core.scraper.api.v1.catalog.outputs import ProductListOutput, ProductLiveOutput, ProductOutput


class ProductListApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        feature = ProductCatalogApi(request)
        output = ProductListOutput(feature.get_queryset(), request=request)
        return Response(output.data)


class ProductDetailApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        feature = ProductCatalogApi(request)
        product = feature.get_product(pk)
        if not product:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        output = ProductOutput(product, request=request)
        return Response(output.data)


class ProductLiveApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        feature = ProductCatalogApi(request)
        product = feature.get_product(pk)
        if not product:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        fresh = feature.refresh_live(product)
        output = ProductLiveOutput(product, fresh, request=request)
        return Response(output.data)
