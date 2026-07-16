"""Normaliza la orientación EXIF de la foto de try-on al subirla.

Las cámaras de los teléfonos suelen guardar la imagen "acostada" junto con
una etiqueta EXIF que indica cómo rotarla al mostrarla. Los visores obedecen
la etiqueta, pero la IA trabaja con los píxeles crudos (y la etiqueta se
pierde al reencodar), así que el try-on salía rotado con fotos tomadas con
la cámara. Aquí se aplica la rotación físicamente a los píxeles; si algo
falla, se devuelve el archivo original (nunca se bloquea la subida).
"""

from io import BytesIO

from django.core.files.base import ContentFile

_EXIF_ORIENTATION_TAG = 274  # 0x0112


def normalize_photo_orientation(uploaded_file):
    try:
        from PIL import Image, ImageOps

        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        orientation = image.getexif().get(_EXIF_ORIENTATION_TAG, 1)
        if orientation in (None, 0, 1):
            uploaded_file.seek(0)
            return uploaded_file

        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        name = (getattr(uploaded_file, "name", "") or "foto").rsplit(".", 1)[0] + ".jpg"
        return ContentFile(buffer.getvalue(), name=name)
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return uploaded_file
