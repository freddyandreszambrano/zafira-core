from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.scraper.api.v1.catalog.outputs import ProductListOutput, ProductOutput
from core.scraper.models import Favorite, FavoriteOutfit, Product


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


class FavoriteOutfitListApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        outfits = FavoriteOutfit.objects.filter(user=request.user).select_related("top", "bottom")
        return Response([outfit.to_json_api(request=request) for outfit in outfits])

    def post(self, request, *args, **kwargs):
        top = Product.objects.filter(pk=request.data.get("top_id")).first()
        bottom = Product.objects.filter(pk=request.data.get("bottom_id")).first()
        if not top or not bottom:
            return Response(
                {"message": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        outfit, created = FavoriteOutfit.objects.get_or_create(
            user=request.user,
            top=top,
            bottom=bottom,
            defaults={"result_image_url": request.data.get("result_image_url", "")},
        )
        # Mismo par guardado de nuevo: conservar la imagen generada más reciente
        new_image = request.data.get("result_image_url", "")
        if not created and new_image and outfit.result_image_url != new_image:
            outfit.result_image_url = new_image
            outfit.save(update_fields=["result_image_url"])

        return Response(
            {
                "message": "Outfit guardado en favoritos",
                "outfit": outfit.to_json_api(request=request),
            },
            status=status.HTTP_201_CREATED,
        )


class FavoriteOutfitDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, outfit_id, *args, **kwargs):
        FavoriteOutfit.objects.filter(user=request.user, id=outfit_id).delete()
        return Response(
            {"message": "Outfit eliminado de favoritos"},
            status=status.HTTP_200_OK,
        )
