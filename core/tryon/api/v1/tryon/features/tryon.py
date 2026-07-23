import requests

from core.scraper.models import Product
from core.tryon.models import TryOnJob
from core.tryon.services.garment_mapping import garment_type_for_product
from core.tryon.task import dispatch_generate_try_on


def _first_reachable_image(product):
    """Primera URL de imagen que realmente responde (las tiendas rotan URLs
    y algunas quedan en 404, lo que hacia fallar el try-on de esa prenda)."""
    for url in product.image_urls[:3]:
        try:
            resp = requests.get(url, stream=True, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            ok = resp.status_code == 200
            resp.close()
            if ok:
                return url
        except requests.RequestException:
            continue
    return None


class TryOnValidationError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


class TryOnApi:
    def __init__(self, request):
        self.request = request
        self.user = request.user

    def create_job(self, data):
        products = self._validate_products(data)
        self._validate_photo()

        primary = products[0]
        primary_image = _first_reachable_image(primary)
        if not primary_image:
            raise TryOnValidationError(
                "PRODUCT_IMAGE_REQUIRED",
                "La imagen de la prenda no está disponible en la tienda.",
            )
        job_kwargs = {
            "user": self.user,
            "product": primary,
            "garment_image_url": primary_image,
            "garment_type": garment_type_for_product(primary.name, primary.category),
        }
        # Outfit completo: la segunda prenda se aplica sobre el resultado
        if len(products) == 2:
            extra = products[1]
            extra_image = _first_reachable_image(extra)
            if not extra_image:
                raise TryOnValidationError(
                    "PRODUCT_IMAGE_REQUIRED",
                    "La imagen de una de las prendas no está disponible en la tienda.",
                )
            job_kwargs["extra_garment_image_url"] = extra_image
            job_kwargs["extra_garment_type"] = garment_type_for_product(extra.name, extra.category)
            # El nombre de la 2a prenda va a la IA (extra_garment_des) para que
            # la aplique bien y el inspector confirme que si se puso.
            job_kwargs["extra_garment_name"] = extra.name

        job = TryOnJob.objects.create(**job_kwargs)
        dispatch_generate_try_on(str(job.id))
        job.refresh_from_db()
        return job

    def get_job(self, job_id):
        return TryOnJob.objects.filter(id=job_id, user=self.user).first()

    def _validate_products(self, data):
        product_ids = data.get("product_ids")
        # 1 producto = prenda individual · 2 productos = outfit (torso + piernas)
        if not isinstance(product_ids, list) or len(product_ids) not in (1, 2):
            raise TryOnValidationError("INVALID_PRODUCTS", "Debes enviar uno o dos productos.")

        products = []
        for pid in product_ids:
            product = Product.objects.filter(id=pid).first()
            if not product:
                raise TryOnValidationError("INVALID_PRODUCTS", "Producto no encontrado.")
            if not product.image_urls:
                raise TryOnValidationError(
                    "PRODUCT_IMAGE_REQUIRED", "El producto no tiene imagen disponible."
                )
            products.append(product)
        return products

    def _validate_photo(self):
        mobile_profile = getattr(self.user, "mobile_profile", None)
        if not mobile_profile or not mobile_profile.try_on_photo:
            raise TryOnValidationError(
                "TRY_ON_PHOTO_REQUIRED", "Debes subir tu foto antes de probar prendas."
            )
