from core.scraper.models import Product
from core.tryon.models import TryOnJob
from core.tryon.services.garment_mapping import garment_type_for_category
from core.tryon.task import generate_try_on_task


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
        product = self._validate_product(data)
        self._validate_photo()

        job = TryOnJob.objects.create(
            user=self.user,
            product=product,
            garment_image_url=product.image_urls[0],
            garment_type=garment_type_for_category(product.category),
        )
        generate_try_on_task.delay(str(job.id))
        return job

    def get_job(self, job_id):
        return TryOnJob.objects.filter(id=job_id, user=self.user).first()

    def _validate_product(self, data):
        product_ids = data.get("product_ids")
        if not isinstance(product_ids, list) or len(product_ids) != 1:
            raise TryOnValidationError(
                "INVALID_PRODUCTS", "Debes enviar exactamente un producto."
            )
        product = Product.objects.filter(id=product_ids[0]).first()
        if not product:
            raise TryOnValidationError("INVALID_PRODUCTS", "Producto no encontrado.")
        if not product.image_urls:
            raise TryOnValidationError(
                "PRODUCT_IMAGE_REQUIRED", "El producto no tiene imagen disponible."
            )
        return product

    def _validate_photo(self):
        mobile_profile = getattr(self.user, "mobile_profile", None)
        if not mobile_profile or not mobile_profile.try_on_photo:
            raise TryOnValidationError(
                "TRY_ON_PHOTO_REQUIRED", "Debes subir tu foto antes de probar prendas."
            )
