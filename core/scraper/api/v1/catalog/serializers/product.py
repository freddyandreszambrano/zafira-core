from rest_framework import serializers

from core.scraper.models import Favorite, Product


class ProductSerializer(serializers.ModelSerializer):
    color_options = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "id_external",
            "name",
            "category",
            "gender",
            "url",
            "price",
            "price_old",
            "currency",
            "sizes",
            "colors",
            "description",
            "image_urls",
            "availability",
            "store",
            "extracted_at",
            "color_options",
            "is_favorite",
        ]

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, product=obj).exists()

    def get_color_options(self, obj):
        if not obj.base_name:
            return []

        siblings = (
            Product.objects.filter(
                base_name=obj.base_name,
                category=obj.category,
                gender=obj.gender,
            )
            .exclude(pk=obj.pk)
            .order_by("name")
        )

        return [
            {
                "id": sibling.id,
                "color": sibling.colors[0] if sibling.colors else None,
                "image_url": sibling.image_urls[0] if sibling.image_urls else None,
            }
            for sibling in siblings
        ]
