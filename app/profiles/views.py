from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import UserProfile
from .serializers import (
    UserProfileListSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserWithProfileSerializer,
)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user', 'manager')
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['user__username', 'user__email', 'job_title', 'employee_id']
    ordering_fields = ['created_at', 'user__first_name', 'department']
    ordering = ['-created_at']

    serializer_action_classes = {
        'list': UserProfileListSerializer,
        'update': UserProfileUpdateSerializer,
        'partial_update': UserProfileUpdateSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, UserProfileSerializer)

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserProfile.objects.select_related('user', 'manager')
        return UserProfile.objects.filter(user=self.request.user).select_related('user', 'manager')

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if not request.user.is_staff and request.user.pk != profile.user.pk:
            return Response(
                {'detail': 'No tienes permiso para actualizar este perfil.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(UserProfileSerializer(profile).data)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {'detail': 'No tienes permiso para eliminar este perfil.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = self.get_object()
        user = profile.user
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def me(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserProfileSerializer(profile).data)

    @action(detail=False, methods=['PUT'])
    def me_update(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(UserProfileSerializer(profile).data)

    @action(detail=True, methods=['GET'])
    def full_info(self, request, pk=None):
        profile = self.get_object()
        return Response(UserWithProfileSerializer(profile.user).data)
