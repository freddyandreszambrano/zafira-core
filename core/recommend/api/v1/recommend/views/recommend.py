import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.recommend.api.v1.recommend.features import RecommendApi
from core.recommend.api.v1.recommend.outputs import ErrorOutput, RecommendOutput
from core.recommend.api.v1.recommend.serializers.recommend import RecommendRequestSerializer
from core.recommend.services.gemini import InsufficientFavoritesError

logger = logging.getLogger(__name__)


class RecommendApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RecommendRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            outfit_list = RecommendApi(data).build_outfits()
        except InsufficientFavoritesError as e:
            return Response(ErrorOutput(str(e)).data, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response(ErrorOutput(str(e)).data, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ValueError as e:
            logger.exception("Recommend: configuracion invalida")
            return Response(ErrorOutput(str(e)).data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Recommend: error inesperado generando outfits")
            return Response(
                ErrorOutput("Error al conectar con el servicio de recomendacion").data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not outfit_list:
            logger.warning(
                "Recommend: sin outfits (occasion=%s, gender=%s, excludes=%s)",
                data["occasion"],
                data.get("gender", "hombre"),
                len(data.get("exclude_ids", [])),
            )
            return Response(
                ErrorOutput("No se encontraron prendas para esta ocasion").data,
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(RecommendOutput(data, outfit_list, request=request).data_response)
