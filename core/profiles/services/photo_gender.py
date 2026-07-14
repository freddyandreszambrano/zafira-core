"""Detección del género de la persona en la foto del probador.

Una llamada barata a Gemini Flash-Lite al subir la foto. El resultado manda
sobre el género del perfil: así el sistema entiende a QUIÉN se está vistiendo
aunque el usuario haya registrado otro género en su cuenta.
"""

import os

from google import genai
from google.genai import types as genai_types

_PROMPT = (
    "Look at the person in this photo. Answer with EXACTLY one word: "
    "'woman' if the person appears to be a woman, or 'man' if the person "
    "appears to be a man. No other words."
)


def _detect_mime(data):
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if b"WEBP" in data[:16]:
        return "image/webp"
    return "image/jpeg"


def detect_photo_gender(image_bytes):
    """'woman' | 'man' | '' si no se pudo detectar. NUNCA lanza: la subida de
    la foto no debe fallar porque la detección falle (queda el perfil como
    respaldo)."""
    try:
        key = os.getenv("GEMINI_API_KEY")
        if not key or not image_bytes:
            return ""
        client = genai.Client(
            api_key=key,
            http_options=genai_types.HttpOptions(timeout=15_000),
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                genai_types.Part.from_bytes(data=image_bytes, mime_type=_detect_mime(image_bytes)),
                _PROMPT,
            ],
        )
        text = (getattr(response, "text", "") or "").strip().lower()
        # OJO: 'woman' contiene 'man' — comprobar mujer primero
        if "woman" in text or "female" in text:
            return "woman"
        if "man" in text or "male" in text:
            return "man"
    except Exception:
        pass
    return ""
