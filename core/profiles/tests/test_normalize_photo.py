from io import BytesIO

from django.test import SimpleTestCase

from PIL import Image

from core.profiles.services import normalize_photo_orientation


def _jpeg(width, height, orientation=None):
    """Genera un JPEG en memoria, opcionalmente con etiqueta EXIF de rotación."""
    image = Image.new("RGB", (width, height), color=(200, 30, 90))
    buffer = BytesIO()
    if orientation:
        exif = image.getexif()
        exif[274] = orientation  # 0x0112 Orientation
        image.save(buffer, format="JPEG", exif=exif.tobytes())
    else:
        image.save(buffer, format="JPEG")
    buffer.seek(0)
    buffer.name = "foto.jpg"
    return buffer


class NormalizePhotoOrientationTests(SimpleTestCase):
    def test_foto_rotada_se_endereza(self):
        # Orientación 6 = el visor debe rotar 90° horario: una foto de cámara
        # "acostada" (ancha) que debería verse vertical (alta).
        result = normalize_photo_orientation(_jpeg(400, 300, orientation=6))
        normalized = Image.open(BytesIO(result.read()))
        self.assertEqual((normalized.width, normalized.height), (300, 400))
        # La etiqueta EXIF de rotación ya no debe existir (píxeles enderezados)
        self.assertEqual(normalized.getexif().get(274, 1), 1)

    def test_foto_normal_se_devuelve_intacta(self):
        original = _jpeg(400, 300)
        result = normalize_photo_orientation(original)
        self.assertIs(result, original)

    def test_archivo_corrupto_no_bloquea_la_subida(self):
        broken = BytesIO(b"esto no es una imagen")
        broken.name = "roto.jpg"
        result = normalize_photo_orientation(broken)
        self.assertIs(result, broken)
