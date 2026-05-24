from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from app.auth.models import User
from app.common.constants import MSG_PASSWORDS_MISMATCH


class UserDetailSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'dni', 'first_name', 'last_name',
            'image', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'groups', 'permissions',
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'is_superuser', 'groups', 'permissions',
        ]

    def get_groups(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]

    def get_permissions(self, obj):
        return [
            {'id': p.id, 'codename': p.codename, 'name': p.name}
            for p in obj.user_permissions.all()
        ]

    def get_image(self, obj):
        return obj.get_image_url()


class UserListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'dni', 'first_name', 'last_name',
            'full_name', 'image', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_image(self, obj):
        return obj.get_image_url()

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.CharField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())],
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'dni', 'first_name', 'last_name',
            'password', 'password2',
        ]
        extra_kwargs = {
            'dni': {'validators': [UniqueValidator(queryset=User.objects.all())]},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({'password': MSG_PASSWORDS_MISMATCH})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'image']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
