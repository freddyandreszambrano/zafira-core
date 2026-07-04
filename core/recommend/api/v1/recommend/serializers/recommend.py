from rest_framework import serializers


class RecommendRequestSerializer(serializers.Serializer):
    occasion = serializers.CharField(
        max_length=200,
        help_text="Ocasión para la recomendación (ej: fiesta, trabajo, boda)",
    )
    store = serializers.ChoiceField(
        choices=["all", "modarm", "etafashion"],
        default="all",
        required=False,
    )
    gender = serializers.ChoiceField(
        choices=["hombre", "mujer"],
        default="hombre",
        required=False,
    )
    exclude_ids = serializers.ListField(
        child=serializers.IntegerField(),
        default=list,
        required=False,
        help_text="IDs de productos ya mostrados (para re-roll)",
    )
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        default=list,
        required=False,
        help_text="Si viene, genera outfits SOLO con estos productos (modo favoritos)",
    )
