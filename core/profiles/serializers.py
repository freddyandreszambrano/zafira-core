from rest_framework import serializers

from core.auth.models import User

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    department_display = serializers.CharField(source="get_department_display", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "address",
            "city",
            "country",
            "department",
            "department_display",
            "job_title",
            "manager",
            "manager_name",
            "employee_id",
            "hire_date",
            "bio",
            "social_media",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "is_verified"]

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None


class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    image = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "dni",
            "first_name",
            "last_name",
            "full_name",
            "image",
            "is_active",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_image(self, obj):
        return obj.get_image_url()

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "address",
            "city",
            "country",
            "department",
            "job_title",
            "manager",
            "employee_id",
            "hire_date",
            "bio",
            "social_media",
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserProfileListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()
    department_display = serializers.CharField(source="get_department_display", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user_username",
            "user_email",
            "full_name",
            "phone",
            "department",
            "department_display",
            "job_title",
            "employee_id",
            "is_verified",
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
