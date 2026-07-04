import logging

from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.recommend.api.v1.recommend.serializers.recommend import RecommendRequestSerializer
from core.recommend.services.gemini import (
    InsufficientFavoritesError,
    get_favorites_recommendations,
    get_multiple_recommendations,
)
from core.scraper.api.v1.catalog.serializers.product import ProductSerializer
from core.scraper.models import Product

logger = logging.getLogger(__name__)

_PRODUCTS_CACHE_TTL = 300  # 5 minutos


def _get_products(store_filter: str) -> list:
    cache_key = f"products_available_{store_filter}"
    products = cache.get(cache_key)
    if products is None:
        queryset = Product.objects.filter(availability="available")
        if store_filter != "all":
            queryset = queryset.filter(store=store_filter)
        products = list(queryset)
        cache.set(cache_key, products, _PRODUCTS_CACHE_TTL)
    return products


class RecommendApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RecommendRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        occasion = serializer.validated_data["occasion"]
        store_filter = serializer.validated_data.get("store", "all")
        gender = serializer.validated_data.get("gender", "hombre")
        exclude_ids = list(serializer.validated_data.get("exclude_ids", []))
        product_ids = list(serializer.validated_data.get("product_ids", []))

        try:
            if product_ids:
                # Modo favoritos: combina solo las prendas indicadas
                favorites = list(Product.objects.filter(id__in=product_ids))
                outfit_list = get_favorites_recommendations(
                    favorites, occasion, gender=gender
                )
            else:
                products = _get_products(store_filter)
                outfit_list = get_multiple_recommendations(
                    products, occasion, gender=gender, exclude_ids=exclude_ids
                )
        except InsufficientFavoritesError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ValueError as e:
            logger.exception("Recommend: configuracion invalida")
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Recommend: error inesperado generando outfits")
            return Response(
                {"error": "Error al conectar con el servicio de recomendación"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not outfit_list:
            logger.warning(
                "Recommend: sin outfits (occasion=%s, gender=%s, excludes=%s)",
                occasion, gender, len(exclude_ids),
            )
            return Response(
                {"error": "No se encontraron prendas para esta ocasión"},
                status=status.HTTP_404_NOT_FOUND,
            )

        outfits = [
            {
                "top": ProductSerializer(o["top"], context={"request": request}).data,
                "bottom": ProductSerializer(o["bottom"], context={"request": request}).data
                          if o["bottom"] else None,
            }
            for o in outfit_list
        ]

        return Response({
            "occasion": occasion,
            "gender": gender,
            "store": store_filter,
            "outfits": outfits,
        })
