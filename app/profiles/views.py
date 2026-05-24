"""Views for user profiles."""

from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from app.auth.models import User
from .models import UserProfile
from .serializers import (
    UserProfileSerializer, UserWithProfileSerializer,
    UserProfileUpdateSerializer, UserProfileListSerializer
)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles."""

    queryset = UserProfile.objects.select_related('user', 'manager')
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['user__username', 'user__email', 'job_title', 'employee_id']
    ordering_fields = ['created_at', 'user__first_name', 'department']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserProfileListSerializer
        elif self.action in ['partial_update', 'update']:
            return UserProfileUpdateSerializer
        elif self.action == 'retrieve':
            return UserProfileSerializer
        return UserProfileSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        # Staff users can see all profiles
        if self.request.user.is_staff:
            return UserProfile.objects.select_related('user', 'manager')
        # Regular users can see their own profile
        return UserProfile.objects.filter(
            user=self.request.user
        ).select_related('user', 'manager')

    def update(self, request, *args, **kwargs):
        """Update user profile."""
        profile = self.get_object()

        # Non-staff users can only update their own profile
        if not request.user.is_staff and request.user.pk != profile.user.pk:
            return Response(
                {'detail': 'No tienes permiso para actualizar este perfil.'},
                status=status.HTTP_403_FORBIDDEN
            )

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(UserProfileSerializer(profile).data)

    def destroy(self, request, *args, **kwargs):
        """Delete user profile (cascade delete user)."""
        profile = self.get_object()

        # Non-staff users cannot delete
        if not request.user.is_staff:
            return Response(
                {'detail': 'No tienes permiso para eliminar este perfil.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = profile.user
        user.is_active = False
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'Perfil no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['PUT'], permission_classes=[permissions.IsAuthenticated])
    def me_update(self, request):
        """Update current user's profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileUpdateSerializer(
                profile,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            profile = serializer.save()
            return Response(UserProfileSerializer(profile).data)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'Perfil no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def full_info(self, request, pk=None):
        """Get profile with full user information."""
        profile = self.get_object()
        user_serializer = UserWithProfileSerializer(profile.user)
        return Response(user_serializer.data)


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """API view for user profile details."""

    queryset = UserProfile.objects.select_related('user', 'manager')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get user's own profile."""
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            raise generics.NotFound('Perfil no encontrado.')

    def retrieve(self, request, *args, **kwargs):
        """Get user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update user's profile."""
        profile = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(UserProfileSerializer(profile).data)
