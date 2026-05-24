from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

from .models import User


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user details with groups and permissions."""

    groups = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'dni', 'first_name', 'last_name',
            'image', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'groups', 'permissions'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'is_superuser', 'groups', 'permissions'
        ]

    def get_groups(self, obj):
        """Get user groups."""
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]

    def get_permissions(self, obj):
        """Get user permissions."""
        return [
            {'id': p.id, 'codename': p.codename, 'name': p.name}
            for p in obj.user_permissions.all()
        ]

    def get_image(self, obj):
        """Get full image URL."""
        return obj.get_image_url()


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view."""

    image = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'dni', 'first_name', 'last_name',
            'full_name', 'image', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_image(self, obj):
        """Get full image URL."""
        return obj.get_image_url()

    def get_full_name(self, obj):
        """Get full name."""
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration/creation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'dni', 'first_name', 'last_name',
            'password', 'password2'
        ]
        extra_kwargs = {
            'dni': {'validators': [UniqueValidator(queryset=User.objects.all())]},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError(
                {'password': 'Las contraseñas no coinciden.'}
            )
        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'image']

    def update(self, instance, validated_data):
        """Update user instance."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password (requires old password)."""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'La contraseña antigua es incorrecta.'
            )
        return value

    def validate(self, data):
        """Validate password confirmation."""
        if data['new_password'] != data.pop('new_password2'):
            raise serializers.ValidationError(
                {'new_password': 'Las nuevas contraseñas no coinciden.'}
            )
        return data

    def save(self):
        """Save new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'No existe un usuario con este correo electrónico.'
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token."""

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Validate password confirmation."""
        if data['new_password'] != data.pop('new_password2'):
            raise serializers.ValidationError(
                {'new_password': 'Las contraseñas no coinciden.'}
            )
        return data


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Validate credentials."""
        from django.contrib.auth import authenticate

        user = authenticate(
            username=data['username'],
            password=data['password']
        )

        if not user:
            raise serializers.ValidationError(
                'Usuario o contraseña incorrectos.'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'Esta cuenta está desactivada.'
            )

        data['user'] = user
        return data


class TokenSerializer(serializers.Serializer):
    """Serializer for token response."""

    token = serializers.CharField()
    user = UserDetailSerializer()


class JWTTokenSerializer(serializers.Serializer):
    """Serializer for JWT token response."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserDetailSerializer()
