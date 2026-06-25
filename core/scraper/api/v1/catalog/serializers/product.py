from rest_framework import serializers

from core.scraper.models import Product


class ProductSerializer(serializers.ModelSerializer):
    color_options = serializers.SerializerMethodField()

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
        ]

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
