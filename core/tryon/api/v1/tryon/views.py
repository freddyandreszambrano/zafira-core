from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.tryon.api.v1.tryon.features import TryOnApi, TryOnValidationError
from core.tryon.api.v1.tryon.outputs import TryOnJobOutput


class TryOnCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            job = TryOnApi(request).create_job(request.data)
        except TryOnValidationError as e:
            return Response(
                {"message": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            TryOnJobOutput(job, request=request).data,
            status=status.HTTP_201_CREATED,
        )


class TryOnJobDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id, *args, **kwargs):
        job = TryOnApi(request).get_job(job_id)
        if not job:
            return Response(
                {"message": "Prueba no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TryOnJobOutput(job, request=request).data)
