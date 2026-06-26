from rest_framework import serializers

from core.auth.models import User
from core.profiles.models import MobileProfile


class AuthTokenSerializerInput(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "password"]


class MobileProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    preferred_size = serializers.CharField(required=False, allow_blank=True)
    style_preferences = serializers.JSONField(required=False)
    language = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        user = instance

        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.save(update_fields=["first_name", "last_name"])

        mobile_profile, _ = MobileProfile.objects.get_or_create(user=user)

        mobile_profile.gender = validated_data.get(
            "gender",
            mobile_profile.gender,
        )
        mobile_profile.country = validated_data.get(
            "country",
            mobile_profile.country,
        )
        mobile_profile.preferred_size = validated_data.get(
            "preferred_size",
            mobile_profile.preferred_size,
        )
        mobile_profile.language = validated_data.get(
            "language",
            mobile_profile.language,
        )

        if "style_preferences" in validated_data:
            mobile_profile.style_preferences = validated_data["style_preferences"]

        mobile_profile.save()

        return user
