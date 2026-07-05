# Probador Virtual IA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El usuario móvil pulsa "Probar con IA" en un producto y recibe una imagen generada de sí mismo usando la prenda (mobile → ZAFIRA-CORE → ZAFIRA-IA → Gemini).

**Architecture:** Django crea un `TryOnJob` y una tarea Celery llama a ZAFIRA-IA firmando HMAC con credenciales de `ExternalProvider`; ZAFIRA-IA (backend nuevo `gemini`) genera el composite con Gemini 2.5 Flash Image y devuelve la imagen en base64; Django la guarda en `/media/try_on_results/` y la app Flutter hace polling cada 2.5s hasta `completed`.

**Tech Stack:** Django 5 + DRF + Celery/Redis · FastAPI + httpx + pydantic · Flutter (Riverpod StateNotifier, Dio, go_router) · Gemini 2.5 Flash Image (REST).

**Spec:** `docs/superpowers/specs/2026-07-05-probador-ia-tryon-design.md`

**Rutas de los repos:**

| Repo | Ruta |
|---|---|
| ZAFIRA-CORE | `\\wsl.localhost\ubuntu\home\freddyandres\Project_development\Django\ZAFIRA-CORE` |
| ZAFIRA-IA | `\\wsl.localhost\ubuntu\home\freddyandres\Project_development\Django\ZAFIRA-IA` |
| zafira (Flutter) | `C:\FAZQ\DEV\MOBILE\MULTIPLATFORM\zafira` |

**Comandos de test:**

- ZAFIRA-IA: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run pytest <archivo> -v`
- ZAFIRA-CORE: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py test core.tryon -v 2`
- Flutter: `flutter test test/feature/try_on` (desde el repo zafira, PowerShell)

**Convenciones del proyecto (obligatorias):** sin comentarios obvios en el código; paquetes con `__init__.py` en vez de archivos monolíticos; API móvil con service classes en `features/` + `to_json_api()` + `outputs`; commits frecuentes.

---

## Parte A — ZAFIRA-IA

### Task A1: Contrato de respuesta con `result_image_b64` y storage opcional

**Files:**
- Modify: `src/app/application/dto/tryon.py`
- Modify: `src/app/application/dto/avatar.py`
- Modify: `src/app/application/use_cases/tryon/generate.py`
- Modify: `src/app/application/use_cases/avatar/generate.py`
- Modify: `src/app/interfaces/dependencies.py`
- Test: `tests/test_tryon.py`, `tests/test_avatar.py`

- [ ] **Step 1: Ampliar los tests existentes (fallarán)**

En `tests/test_tryon.py`, agregar imports y asserts al happy path, y un test nuevo sin storage:

```python
import base64
```

Dentro de `test_generate_tryon_happy_path`, después de los asserts existentes:

```python
    assert base64.b64decode(data["result_image_b64"]) == b"person-bytes"
```

Al final del archivo:

```python
def test_tryon_without_storage_returns_b64_and_null_key() -> None:
    fetcher = FakeImageFetcher(payload=b"person-bytes")

    app.dependency_overrides[verify_hmac_request] = lambda: None
    app.dependency_overrides[get_image_fetcher] = lambda: fetcher
    app.dependency_overrides[get_storage_client] = lambda: None

    try:
        response = client.post(
            "/api/v1/tryon",
            json={
                "external_ref": "tryon-9",
                "person_image_url": _PERSON_URL,
                "garment_image_url": _GARMENT_URL,
                "garment_type": "upper_body",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["result_image_key"] is None
    assert base64.b64decode(data["result_image_b64"]) == b"person-bytes"
```

En `tests/test_avatar.py` hacer el cambio equivalente (assert de `avatar_image_b64` en el happy path; el test sin storage es opcional ahí).

- [ ] **Step 2: Correr tests y verificar que fallan**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run pytest tests/test_tryon.py tests/test_avatar.py -v`
Expected: FAIL con `KeyError: 'result_image_b64'` (o assert de campo faltante).

- [ ] **Step 3: Actualizar DTOs**

`src/app/application/dto/tryon.py` — reemplazar `TryOnResponse`:

```python
class TryOnResponse(BaseModel):
    external_ref: str
    result_image_b64: str = Field(description="Base64-encoded bytes of the try-on result image")
    result_image_key: str | None = Field(
        default=None, description="Object storage key (only when storage is configured)"
    )
    meta: dict[str, Any] = Field(default_factory=dict)
```

`src/app/application/dto/avatar.py` — reemplazar `AvatarResponse`:

```python
class AvatarResponse(BaseModel):
    external_ref: str
    avatar_image_b64: str = Field(description="Base64-encoded bytes of the generated avatar")
    avatar_image_key: str | None = Field(
        default=None, description="Object storage key (only when storage is configured)"
    )
    meta: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Actualizar use cases (storage opcional)**

`src/app/application/use_cases/tryon/generate.py` completo:

```python
"""Try-on use case — fetch person + garment images, run the model, return the result.

Storage upload is optional: when no storage backend is configured the caller
receives only the base64 payload.
"""

from __future__ import annotations

import base64

from app.application.dto.tryon import TryOnRequest, TryOnResponse
from app.infrastructure.ai.base import TryOnModel
from app.infrastructure.http.image_fetcher import ImageFetcher
from app.infrastructure.storage.base import StorageClient


class GenerateTryOnUseCase:
    def __init__(
        self, *, fetcher: ImageFetcher, model: TryOnModel, storage: StorageClient | None
    ) -> None:
        self._fetcher = fetcher
        self._model = model
        self._storage = storage

    async def execute(self, request: TryOnRequest) -> TryOnResponse:
        person_image = await self._fetcher.fetch(str(request.person_image_url))
        garment_image = await self._fetcher.fetch(str(request.garment_image_url))
        generated = await self._model.generate(
            person_image=person_image,
            garment_image=garment_image,
            garment_type=request.garment_type,
            params=request.params,
        )

        key: str | None = None
        if self._storage is not None:
            key = f"tryons/{request.external_ref}.png"
            await self._storage.upload(key=key, data=generated, content_type="image/png")

        return TryOnResponse(
            external_ref=request.external_ref,
            result_image_b64=base64.b64encode(generated).decode(),
            result_image_key=key,
            meta={"model": type(self._model).__name__, "size_bytes": len(generated)},
        )
```

`src/app/application/use_cases/avatar/generate.py` completo (mismo patrón):

```python
"""Avatar generation use case — fetch the source photo, run the model, return the result."""

from __future__ import annotations

import base64

from app.application.dto.avatar import AvatarRequest, AvatarResponse
from app.infrastructure.ai.base import AvatarModel
from app.infrastructure.http.image_fetcher import ImageFetcher
from app.infrastructure.storage.base import StorageClient


class GenerateAvatarUseCase:
    def __init__(
        self, *, fetcher: ImageFetcher, model: AvatarModel, storage: StorageClient | None
    ) -> None:
        self._fetcher = fetcher
        self._model = model
        self._storage = storage

    async def execute(self, request: AvatarRequest) -> AvatarResponse:
        source_image = await self._fetcher.fetch(str(request.source_image_url))
        generated = await self._model.generate(source_image=source_image, params=request.params)

        key: str | None = None
        if self._storage is not None:
            key = f"avatars/{request.external_ref}.png"
            await self._storage.upload(key=key, data=generated, content_type="image/png")

        return AvatarResponse(
            external_ref=request.external_ref,
            avatar_image_b64=base64.b64encode(generated).decode(),
            avatar_image_key=key,
            meta={"model": type(self._model).__name__, "size_bytes": len(generated)},
        )
```

- [ ] **Step 5: `get_storage_client` devuelve `None` sin config**

En `src/app/interfaces/dependencies.py` reemplazar `get_storage_client` y las firmas de los factories de use cases:

```python
@lru_cache
def get_storage_client() -> S3StorageClient | None:
    settings = get_settings()
    if not settings.storage_endpoint_url:
        return None
    return S3StorageClient(
        bucket=settings.storage_bucket,
        endpoint_url=settings.storage_endpoint_url,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        region=settings.storage_region,
    )
```

```python
def get_generate_avatar_use_case(
    fetcher: ImageFetcher = Depends(get_image_fetcher),
    model: AvatarModel = Depends(get_avatar_model),
    storage: StorageClient | None = Depends(get_storage_client),
) -> GenerateAvatarUseCase:
    return GenerateAvatarUseCase(fetcher=fetcher, model=model, storage=storage)


def get_generate_tryon_use_case(
    fetcher: ImageFetcher = Depends(get_image_fetcher),
    model: TryOnModel = Depends(get_tryon_model),
    storage: StorageClient | None = Depends(get_storage_client),
) -> GenerateTryOnUseCase:
    return GenerateTryOnUseCase(fetcher=fetcher, model=model, storage=storage)
```

- [ ] **Step 6: Correr toda la suite**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run pytest -v`
Expected: PASS (todos).

- [ ] **Step 7: Commit (repo ZAFIRA-IA)**

```bash
git add src/app/application src/app/interfaces/dependencies.py tests/
git commit -m "feat: return base64 image in tryon/avatar responses, make storage optional"
```

### Task A2: Backend `gemini` (Gemini 2.5 Flash Image)

**Files:**
- Create: `src/app/infrastructure/ai/gemini.py`
- Modify: `src/app/config.py`
- Modify: `src/app/interfaces/dependencies.py`
- Test: `tests/test_gemini.py` (nuevo)

- [ ] **Step 1: Escribir tests del adaptador**

`tests/test_gemini.py`:

```python
"""Gemini backend tests — no network (httpx.MockTransport / fake client)."""

import base64
import json

import httpx
import pytest

from app.domain.exceptions import DomainError
from app.infrastructure.ai.gemini import (
    GeminiImageClient,
    GeminiTryOnModel,
    _detect_mime,
)

_PNG = b"\x89PNG\r\n\x1a\nrest"
_JPEG = b"\xff\xd8\xffrest"


def test_detect_mime() -> None:
    assert _detect_mime(_PNG) == "image/png"
    assert _detect_mime(_JPEG) == "image/jpeg"
    assert _detect_mime(b"unknown-bytes") == "image/jpeg"


def _gemini_response(image: bytes | None) -> dict:
    parts = [{"text": "done"}]
    if image is not None:
        parts.append(
            {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(image).decode()}}
        )
    return {"candidates": [{"content": {"parts": parts}}]}


def _client_with_transport(handler) -> GeminiImageClient:
    return GeminiImageClient(
        api_key="test-key",
        model="gemini-2.5-flash-image",
        transport=httpx.MockTransport(handler),
    )


async def test_generate_extracts_inline_image() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers.get("x-goog-api-key")
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json=_gemini_response(b"generated-image"))

    client = _client_with_transport(handler)
    result = await client.generate(prompt="try on", images=[_PNG, _JPEG])

    assert result == b"generated-image"
    assert captured["api_key"] == "test-key"
    assert "gemini-2.5-flash-image:generateContent" in captured["url"]
    parts = captured["payload"]["contents"][0]["parts"]
    assert parts[0] == {"text": "try on"}
    assert parts[1]["inline_data"]["mime_type"] == "image/png"
    assert parts[2]["inline_data"]["mime_type"] == "image/jpeg"


async def test_generate_without_image_raises_generation_rejected() -> None:
    client = _client_with_transport(
        lambda request: httpx.Response(200, json=_gemini_response(None))
    )

    with pytest.raises(DomainError) as exc_info:
        await client.generate(prompt="try on", images=[_PNG])

    assert exc_info.value.code == "GENERATION_REJECTED"


async def test_generate_http_error_raises_provider_error() -> None:
    client = _client_with_transport(
        lambda request: httpx.Response(429, json={"error": {"message": "quota"}})
    )

    with pytest.raises(DomainError) as exc_info:
        await client.generate(prompt="try on", images=[_PNG])

    assert exc_info.value.code == "PROVIDER_ERROR"


class FakeGeminiClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def generate(self, *, prompt: str, images: list[bytes]) -> bytes:
        self.calls.append({"prompt": prompt, "images": images})
        return b"composited"


async def test_tryon_model_builds_prompt_by_garment_type() -> None:
    fake = FakeGeminiClient()
    model = GeminiTryOnModel(client=fake)

    result = await model.generate(
        person_image=b"person",
        garment_image=b"garment",
        garment_type="lower_body",
        params={},
    )

    assert result == b"composited"
    assert fake.calls[0]["images"] == [b"person", b"garment"]
    assert "lower-body" in fake.calls[0]["prompt"]


async def test_tryon_model_honors_prompt_override() -> None:
    fake = FakeGeminiClient()
    model = GeminiTryOnModel(client=fake)

    await model.generate(
        person_image=b"person",
        garment_image=b"garment",
        garment_type="dress",
        params={"prompt": "custom prompt"},
    )

    assert fake.calls[0]["prompt"] == "custom prompt"
```

Nota: `DomainError` en este repo se construye como `DomainError(message, code)` y expone `.code` (verificar en `src/app/domain/exceptions.py`; ajustar el acceso si el atributo tiene otro nombre).

- [ ] **Step 2: Correr tests y verificar que fallan**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run pytest tests/test_gemini.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.infrastructure.ai.gemini'`.

- [ ] **Step 3: Implementar `gemini.py`**

`src/app/infrastructure/ai/gemini.py`:

```python
"""Gemini image backend — try-on/avatar composites via Gemini 2.5 Flash Image.

Plain REST over httpx (models/{model}:generateContent with inline images);
no extra SDK dependency. Wire it up with AI_BACKEND=gemini + GEMINI_API_KEY.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from app.domain.exceptions import DomainError

TRYON_PROMPT_TEMPLATE = (
    "Virtual try-on task. The first image is a person; the second image is a "
    "{garment_label} garment product photo. Generate a photorealistic image of "
    "the same person wearing that garment. Preserve the person's face, identity, "
    "body pose and the background of the first image. Replace only the "
    "{garment_label} clothing. Return only the final image."
)

AVATAR_PROMPT = (
    "Generate a clean, semi-realistic avatar portrait of the person in the image. "
    "Preserve identity and facial features. Neutral studio background. "
    "Return only the final image."
)

_GARMENT_LABELS = {
    "upper_body": "upper-body",
    "lower_body": "lower-body",
    "dress": "full-body dress",
}


def _detect_mime(image: bytes) -> str:
    if image.startswith(b"\x89PNG"):
        return "image/png"
    if image.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if image[:16].find(b"WEBP") != -1:
        return "image/webp"
    return "image/jpeg"


class GeminiImageClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout_seconds: int = 120,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport

    async def generate(self, *, prompt: str, images: list[bytes]) -> bytes:
        parts: list[dict[str, Any]] = [{"text": prompt}]
        for image in images:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": _detect_mime(image),
                        "data": base64.b64encode(image).decode(),
                    }
                }
            )

        url = f"{self._base_url}/v1beta/models/{self._model}:generateContent"
        async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
            response = await client.post(
                url,
                json={"contents": [{"parts": parts}]},
                headers={"x-goog-api-key": self._api_key},
            )

        if response.status_code != 200:
            raise DomainError(
                f"Gemini rejected the request (HTTP {response.status_code})", "PROVIDER_ERROR"
            )
        return self._extract_image(response.json())

    @staticmethod
    def _extract_image(data: dict[str, Any]) -> bytes:
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                inline = part.get("inline_data") or part.get("inlineData") or {}
                if inline.get("data"):
                    return base64.b64decode(inline["data"])
        raise DomainError(
            "Gemini returned no image (safety block or text-only reply)", "GENERATION_REJECTED"
        )


class GeminiTryOnModel:
    def __init__(self, *, client: GeminiImageClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        person_image: bytes,
        garment_image: bytes,
        garment_type: str,
        params: dict[str, Any],
    ) -> bytes:
        label = _GARMENT_LABELS.get(garment_type, "upper-body")
        prompt = params.get("prompt") or TRYON_PROMPT_TEMPLATE.format(garment_label=label)
        return await self._client.generate(prompt=prompt, images=[person_image, garment_image])


class GeminiAvatarModel:
    def __init__(self, *, client: GeminiImageClient) -> None:
        self._client = client

    async def generate(self, *, source_image: bytes, params: dict[str, Any]) -> bytes:
        prompt = params.get("prompt") or AVATAR_PROMPT
        return await self._client.generate(prompt=prompt, images=[source_image])
```

Nota de tipos: `GeminiTryOnModel` recibe `client:` con el mismo duck-typing que los Protocols del repo — el fake del test cumple la interfaz. Si ruff/mypy exige, tipar `client` como `GeminiImageClient` está bien igualmente porque los tests usan duck typing en runtime; no agregar Protocol nuevo (YAGNI).

- [ ] **Step 4: Settings + wiring**

En `src/app/config.py`, cambiar la línea de `ai_backend` y agregar debajo del bloque hosted:

```python
    ai_backend: Literal["stub", "hosted", "gemini"] = Field(
        default="stub", validation_alias="AI_BACKEND"
    )
```

```python
    # Gemini (only required when ai_backend == 'gemini')
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash-image", validation_alias="GEMINI_MODEL")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com",
        validation_alias="GEMINI_BASE_URL",
    )
    gemini_timeout_seconds: int = Field(
        default=120, ge=10, le=900, validation_alias="GEMINI_TIMEOUT_SECONDS"
    )
```

En `src/app/interfaces/dependencies.py` agregar import y helper, y ramas en los dos factories:

```python
from app.infrastructure.ai.gemini import GeminiAvatarModel, GeminiImageClient, GeminiTryOnModel
```

```python
def _gemini_client(settings: Settings) -> GeminiImageClient:
    if not settings.gemini_api_key:
        raise RuntimeError("AI_BACKEND=gemini requires GEMINI_API_KEY")
    return GeminiImageClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
        timeout_seconds=settings.gemini_timeout_seconds,
    )
```

```python
@lru_cache
def get_avatar_model() -> AvatarModel:
    settings = get_settings()
    if settings.ai_backend == "hosted":
        return HostedAvatarModel(
            client=_hosted_client(settings, settings.avatar_model_ref, "AVATAR_MODEL_REF")
        )
    if settings.ai_backend == "gemini":
        return GeminiAvatarModel(client=_gemini_client(settings))
    return StubAvatarModel()


@lru_cache
def get_tryon_model() -> TryOnModel:
    settings = get_settings()
    if settings.ai_backend == "hosted":
        return HostedTryOnModel(
            client=_hosted_client(settings, settings.tryon_model_ref, "TRYON_MODEL_REF")
        )
    if settings.ai_backend == "gemini":
        return GeminiTryOnModel(client=_gemini_client(settings))
    return StubTryOnModel()
```

- [ ] **Step 5: Correr toda la suite + lint**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run pytest -v`
Expected: PASS.
Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run ruff check src tests`
Expected: sin errores.

- [ ] **Step 6: Actualizar `.env.example`**

Agregar al final de `.env.example`:

```bash
GEMINI_API_KEY=
GEMINI_MODEL=
GEMINI_BASE_URL=
GEMINI_TIMEOUT_SECONDS=
```

- [ ] **Step 7: Commit (repo ZAFIRA-IA)**

```bash
git add src/app tests/test_gemini.py .env.example
git commit -m "feat: add gemini image backend for tryon/avatar generation"
```

---

## Parte B — ZAFIRA-CORE

### Task B1: App `core/tryon` + modelo `TryOnJob`

**Files:**
- Create: `core/tryon/__init__.py`, `core/tryon/apps.py`, `core/tryon/admin.py`
- Create: `core/tryon/models/__init__.py`, `core/tryon/models/job.py`
- Create: `core/tryon/migrations/__init__.py`
- Create: `core/tryon/tests/__init__.py`, `core/tryon/tests/test_models.py`
- Modify: `config/settings.py` (INSTALLED_APPS + bloque ZAFIRA-IA)

- [ ] **Step 1: Test del modelo**

`core/tryon/tests/test_models.py`:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.scraper.models import Product
from core.tryon.models import TryOnJob


def create_product(**overrides):
    defaults = {
        "id_external": "ext-1",
        "name": "Camiseta básica",
        "category": "camisetas",
        "gender": "M",
        "url": "https://store.example.com/p/1",
        "price": "19.99",
        "image_urls": ["https://store.example.com/img/1.jpg"],
        "extracted_at": timezone.now(),
    }
    defaults.update(overrides)
    return Product.objects.create(**defaults)


class TryOnJobModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="freddy", password="secret123"
        )
        self.product = create_product()

    def test_defaults_and_str(self):
        job = TryOnJob.objects.create(
            user=self.user,
            product=self.product,
            garment_image_url=self.product.image_urls[0],
            garment_type="upper_body",
        )
        self.assertEqual(job.status, TryOnJob.Status.PENDING)
        self.assertIn("pending", str(job))

    def test_to_json_api_without_result(self):
        job = TryOnJob.objects.create(
            user=self.user,
            product=self.product,
            garment_image_url=self.product.image_urls[0],
            garment_type="upper_body",
        )
        data = job.to_json_api()
        self.assertEqual(data["id"], str(job.id))
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["product_id"], self.product.id)
        self.assertIsNone(data["result_url"])
        self.assertEqual(data["error_message"], "")
```

- [ ] **Step 2: Crear el esqueleto de la app**

`core/tryon/__init__.py`: vacío.

`core/tryon/apps.py`:

```python
from django.apps import AppConfig


class TryonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.tryon"
```

`core/tryon/models/job.py`:

```python
import uuid

from django.conf import settings
from django.db import models


class TryOnJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="try_on_jobs",
        verbose_name="Usuario",
    )
    product = models.ForeignKey(
        "scraper.Product",
        on_delete=models.CASCADE,
        related_name="try_on_jobs",
        verbose_name="Producto",
    )
    garment_image_url = models.TextField(verbose_name="Imagen de la prenda")
    garment_type = models.TextField(default="upper_body", verbose_name="Tipo de prenda")
    status = models.TextField(
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Estado",
    )
    result_image = models.ImageField(
        upload_to="try_on_results/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name="Resultado",
    )
    error_message = models.TextField(blank=True, verbose_name="Error")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Prueba virtual"
        verbose_name_plural = "Pruebas virtuales"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"TryOn {self.id} ({self.status})"

    def to_json_api(self, request=None):
        result_url = None
        if self.result_image:
            result_url = (
                request.build_absolute_uri(self.result_image.url)
                if request
                else self.result_image.url
            )
        return {
            "id": str(self.id),
            "status": self.status,
            "product_id": self.product_id,
            "result_url": result_url,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
```

`core/tryon/models/__init__.py`:

```python
from core.tryon.models.job import TryOnJob

__all__ = ["TryOnJob"]
```

`core/tryon/admin.py`:

```python
from django.contrib import admin

from core.tryon.models import TryOnJob


@admin.register(TryOnJob)
class TryOnJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "product__name")
    readonly_fields = ("created_at", "updated_at")
```

`core/tryon/migrations/__init__.py` y `core/tryon/tests/__init__.py`: vacíos.

- [ ] **Step 3: Registrar app + settings**

En `config/settings.py`, en `INSTALLED_APPS` después de `"core.scraper.apps.ScraperConfig",`:

```python
    "core.tryon.apps.TryonConfig",
```

Al final del archivo (junto a `FRONTEND_URL`):

```python
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")

ZAFIRA_IA_BASE_URL = os.getenv("ZAFIRA_IA_BASE_URL", "http://localhost:8001")
ZAFIRA_IA_PROVIDER_NAME = os.getenv("ZAFIRA_IA_PROVIDER_NAME", "zafira-ia")
ZAFIRA_IA_TIMEOUT_SECONDS = int(os.getenv("ZAFIRA_IA_TIMEOUT_SECONDS", 180))
```

Si existe `.env.example` en el repo, agregar las 4 variables.

- [ ] **Step 4: Generar migración**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py makemigrations tryon`
Expected: crea `core/tryon/migrations/0001_initial.py`.

- [ ] **Step 5: Correr tests**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py test core.tryon -v 2`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit (repo ZAFIRA-CORE)**

```bash
git add core/tryon config/settings.py
git commit -m "feat: add tryon app with TryOnJob model"
```

### Task B2: Mapeo categoría → `garment_type`

**Files:**
- Create: `core/tryon/services/__init__.py`, `core/tryon/services/garment_mapping.py`
- Test: `core/tryon/tests/test_garment_mapping.py`

- [ ] **Step 1: Test**

`core/tryon/tests/test_garment_mapping.py`:

```python
from django.test import SimpleTestCase

from core.tryon.services.garment_mapping import garment_type_for_category


class GarmentMappingTests(SimpleTestCase):
    def test_lower_body_categories(self):
        for category in ("pantalones", "Jeans", "faldas", "SHORTS", "joggers"):
            self.assertEqual(garment_type_for_category(category), "lower_body")

    def test_dress_categories(self):
        for category in ("vestidos", "Vestido midi", "enterizos"):
            self.assertEqual(garment_type_for_category(category), "dress")

    def test_upper_body_default(self):
        for category in ("camisetas", "chaquetas", "", None, "accesorios"):
            self.assertEqual(garment_type_for_category(category), "upper_body")
```

- [ ] **Step 2: Correr y ver fallar**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py test core.tryon.tests.test_garment_mapping -v 2`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: Implementar**

`core/tryon/services/__init__.py`: vacío.

`core/tryon/services/garment_mapping.py`:

```python
UPPER_BODY = "upper_body"
LOWER_BODY = "lower_body"
DRESS = "dress"

_CATEGORY_KEYWORDS = (
    (DRESS, ("vestido", "dress", "enterizo", "jumpsuit", "overol")),
    (
        LOWER_BODY,
        (
            "pantalon",
            "pantalón",
            "jean",
            "short",
            "falda",
            "legging",
            "jogger",
            "bermuda",
            "trouser",
            "skirt",
        ),
    ),
)


def garment_type_for_category(category):
    normalized = (category or "").strip().lower()
    for garment_type, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return garment_type
    return UPPER_BODY
```

- [ ] **Step 4: Correr tests → PASS, commit**

```bash
git add core/tryon/services core/tryon/tests/test_garment_mapping.py
git commit -m "feat: map product category to garment type for try-on"
```

### Task B3: Cliente HMAC hacia ZAFIRA-IA

**Files:**
- Create: `core/tryon/services/zafira_ia_client.py`
- Test: `core/tryon/tests/test_client.py`

- [ ] **Step 1: Tests (verifican la firma con el mismo algoritmo de ZAFIRA-IA)**

`core/tryon/tests/test_client.py`:

```python
import hashlib
import hmac
import json
from unittest import mock

import requests
from django.test import TestCase

from core.security.models import ExternalProvider
from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaRejected,
    ZafiraIaUnavailable,
)


class ZafiraIaClientTests(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            name="zafira-ia",
            client_id="core-client",
            client_secret="core-secret",
        )

    def test_signed_headers_match_zafira_ia_verifier(self):
        client = ZafiraIaClient(base_url="http://ia.test")
        body = json.dumps({"external_ref": "abc"}).encode("utf-8")

        headers = client.signed_headers(body)

        message = body.decode("utf-8") + headers["X-TIMESTAMP"]
        expected = hmac.new(
            b"core-secret", message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        self.assertEqual(headers["X-CLIENT-ID"], "core-client")
        self.assertEqual(headers["X-SIGNATURE"], expected)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_missing_provider_raises_rejected(self):
        self.provider.delete()
        with self.assertRaises(ZafiraIaRejected):
            ZafiraIaClient(base_url="http://ia.test")

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_success(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"external_ref": "abc", "result_image_b64": "aW1n"},
        )
        client = ZafiraIaClient(base_url="http://ia.test")

        data = client.try_on(
            external_ref="abc",
            person_image_url="http://core.test/media/p.jpg",
            garment_image_url="http://store.test/g.jpg",
            garment_type="upper_body",
        )

        self.assertEqual(data["result_image_b64"], "aW1n")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://ia.test/api/v1/tryon")
        sent = json.loads(kwargs["data"])
        self.assertEqual(sent["garment_type"], "upper_body")
        self.assertIn("X-SIGNATURE", kwargs["headers"])

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_5xx_raises_unavailable(self, mock_post):
        mock_post.return_value = mock.Mock(status_code=503, json=lambda: {})
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaUnavailable):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_network_error_raises_unavailable(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaUnavailable):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_4xx_raises_rejected(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=422, json=lambda: {"detail": "bad payload"}
        )
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaRejected):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )
```

- [ ] **Step 2: Correr y ver fallar** (`ModuleNotFoundError`)

- [ ] **Step 3: Implementar**

`core/tryon/services/zafira_ia_client.py`:

```python
import hashlib
import hmac
import json
import time

import requests
from django.conf import settings

from core.security.models import ExternalProvider


class ZafiraIaError(Exception):
    def __init__(self, message, code=""):
        self.code = code
        super().__init__(message)


class ZafiraIaUnavailable(ZafiraIaError):
    """Error de red o 5xx: la tarea puede reintentar."""


class ZafiraIaRejected(ZafiraIaError):
    """4xx o configuración inválida: no reintentar."""


class ZafiraIaClient:
    def __init__(self, base_url=None, provider=None, timeout=None):
        self.base_url = (base_url or settings.ZAFIRA_IA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.ZAFIRA_IA_TIMEOUT_SECONDS
        self.provider = provider or self._get_provider()

    @staticmethod
    def _get_provider():
        provider = ExternalProvider.objects.filter(
            name=settings.ZAFIRA_IA_PROVIDER_NAME, is_active=True
        ).first()
        if not provider:
            raise ZafiraIaRejected(
                f"No existe ExternalProvider activo '{settings.ZAFIRA_IA_PROVIDER_NAME}'",
                code="PROVIDER_NOT_CONFIGURED",
            )
        return provider

    def signed_headers(self, body):
        timestamp = str(int(time.time()))
        message = body.decode("utf-8") + timestamp
        signature = hmac.new(
            self.provider.client_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Content-Type": "application/json",
            "X-CLIENT-ID": str(self.provider.client_id),
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
        }

    def try_on(self, *, external_ref, person_image_url, garment_image_url, garment_type):
        body = json.dumps(
            {
                "external_ref": external_ref,
                "person_image_url": person_image_url,
                "garment_image_url": garment_image_url,
                "garment_type": garment_type,
                "params": {},
            }
        ).encode("utf-8")

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/tryon",
                data=body,
                headers=self.signed_headers(body),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ZafiraIaUnavailable(f"ZAFIRA-IA no disponible: {exc}") from exc

        if response.status_code >= 500:
            raise ZafiraIaUnavailable(f"ZAFIRA-IA respondió {response.status_code}")
        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "")
            except ValueError:
                detail = ""
            raise ZafiraIaRejected(
                f"ZAFIRA-IA rechazó la solicitud ({response.status_code}): {detail}",
                code="IA_REJECTED",
            )
        return response.json()
```

- [ ] **Step 4: Correr tests → PASS, commit**

```bash
git add core/tryon/services/zafira_ia_client.py core/tryon/tests/test_client.py
git commit -m "feat: add HMAC-signed client for ZAFIRA-IA"
```

### Task B4: Tarea Celery `generate_try_on_task`

**Files:**
- Create: `core/tryon/task/__init__.py`, `core/tryon/task/tryon.py`
- Test: `core/tryon/tests/test_task.py`

- [ ] **Step 1: Tests (cliente mockeado, tarea ejecutada en modo eager llamándola directo)**

`core/tryon/tests/test_task.py`:

```python
import base64
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from core.profiles.models import MobileProfile
from core.tryon.models import TryOnJob
from core.tryon.services.zafira_ia_client import ZafiraIaRejected, ZafiraIaUnavailable
from core.tryon.task.tryon import generate_try_on_task
from core.tryon.tests.test_models import create_product

TINY_GIF = base64.b64decode(b"R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")


def make_job():
    user = get_user_model().objects.create_user(username="freddy", password="secret123")
    MobileProfile.objects.create(
        user=user,
        try_on_photo=SimpleUploadedFile("me.gif", TINY_GIF, content_type="image/gif"),
    )
    product = create_product()
    return TryOnJob.objects.create(
        user=user,
        product=product,
        garment_image_url=product.image_urls[0],
        garment_type="upper_body",
    )


@override_settings(SITE_URL="http://core.test")
class GenerateTryOnTaskTests(TestCase):
    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_success_saves_result_and_completes(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.return_value = {
            "external_ref": str(job.id),
            "result_image_b64": base64.b64encode(b"generated-image").decode(),
        }

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.COMPLETED)
        self.assertTrue(job.result_image)
        self.assertEqual(job.result_image.read(), b"generated-image")

        kwargs = mock_client_cls.return_value.try_on.call_args.kwargs
        self.assertTrue(kwargs["person_image_url"].startswith("http://core.test/"))
        self.assertEqual(kwargs["garment_image_url"], job.garment_image_url)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_rejected_marks_failed_without_retry(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaRejected("blocked")

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertNotEqual(job.error_message, "")
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 1)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_unavailable_retries_then_fails(self, mock_client_cls):
        job = make_job()
        mock_client_cls.return_value.try_on.side_effect = ZafiraIaUnavailable("down")

        generate_try_on_task.apply(args=[str(job.id)])

        job.refresh_from_db()
        self.assertEqual(job.status, TryOnJob.Status.FAILED)
        self.assertEqual(mock_client_cls.return_value.try_on.call_count, 3)

    @mock.patch("core.tryon.task.tryon.ZafiraIaClient")
    def test_missing_job_is_noop(self, mock_client_cls):
        generate_try_on_task.apply(args=["00000000-0000-0000-0000-000000000000"])
        mock_client_cls.assert_not_called()
```

Nota: `task.apply(args=...)` ejecuta la tarea eager (incluidos retries) sin broker.

- [ ] **Step 2: Correr y ver fallar** (`ModuleNotFoundError: core.tryon.task`)

- [ ] **Step 3: Implementar**

`core/tryon/task/__init__.py`:

```python
from core.tryon.task.tryon import generate_try_on_task

__all__ = ["generate_try_on_task"]
```

`core/tryon/task/tryon.py`:

```python
import base64

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

from core.tryon.models import TryOnJob
from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaError,
    ZafiraIaUnavailable,
)

USER_FRIENDLY_ERROR = "No pudimos generar tu prueba virtual. Intenta nuevamente."


@shared_task(bind=True, max_retries=2)
def generate_try_on_task(self, job_id):
    job = (
        TryOnJob.objects.select_related("user", "product")
        .filter(id=job_id)
        .exclude(status=TryOnJob.Status.COMPLETED)
        .first()
    )
    if not job:
        return

    job.status = TryOnJob.Status.PROCESSING
    job.save(update_fields=["status", "updated_at"])

    try:
        mobile_profile = job.user.mobile_profile
        data = ZafiraIaClient().try_on(
            external_ref=str(job.id),
            person_image_url=settings.SITE_URL + mobile_profile.try_on_photo.url,
            garment_image_url=job.garment_image_url,
            garment_type=job.garment_type,
        )
        image_bytes = base64.b64decode(data["result_image_b64"])
        job.result_image.save(f"{job.id}.png", ContentFile(image_bytes), save=False)
        job.status = TryOnJob.Status.COMPLETED
        job.error_message = ""
        job.save()
    except ZafiraIaUnavailable as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))
        _mark_failed(job, USER_FRIENDLY_ERROR)
    except (ZafiraIaError, KeyError, ValueError):
        _mark_failed(job, USER_FRIENDLY_ERROR)


def _mark_failed(job, message):
    job.status = TryOnJob.Status.FAILED
    job.error_message = message
    job.save(update_fields=["status", "error_message", "updated_at"])
```

- [ ] **Step 4: Correr tests → PASS, commit**

```bash
git add core/tryon/task core/tryon/tests/test_task.py
git commit -m "feat: add celery task that generates try-on via ZAFIRA-IA"
```

### Task B5: API `POST /api/v1/tryon/` y `GET /api/v1/tryon/<uuid>/`

**Files:**
- Create: `core/tryon/api/__init__.py`, `core/tryon/api/v1/__init__.py`, `core/tryon/api/v1/urls.py`
- Create: `core/tryon/api/v1/tryon/__init__.py`, `core/tryon/api/v1/tryon/urls.py`, `core/tryon/api/v1/tryon/views.py`, `core/tryon/api/v1/tryon/outputs.py`
- Create: `core/tryon/api/v1/tryon/features/__init__.py`, `core/tryon/api/v1/tryon/features/tryon.py`
- Modify: `config/urls.py`
- Test: `core/tryon/tests/test_api.py`

- [ ] **Step 1: Tests**

`core/tryon/tests/test_api.py`:

```python
import base64
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.profiles.models import MobileProfile
from core.tryon.models import TryOnJob
from core.tryon.tests.test_models import create_product

TINY_GIF = base64.b64decode(b"R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==")


class TryOnApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="freddy", password="secret123"
        )
        self.profile = MobileProfile.objects.create(
            user=self.user,
            try_on_photo=SimpleUploadedFile("me.gif", TINY_GIF, content_type="image/gif"),
        )
        self.product = create_product()
        self.client.force_authenticate(self.user)

    @mock.patch("core.tryon.api.v1.tryon.features.tryon.generate_try_on_task")
    def test_create_job(self, mock_task):
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )

        self.assertEqual(response.status_code, 201)
        job_data = response.json()["job"]
        self.assertEqual(job_data["status"], "pending")
        self.assertEqual(job_data["product_id"], self.product.id)

        job = TryOnJob.objects.get(id=job_data["id"])
        self.assertEqual(job.garment_type, "upper_body")
        self.assertEqual(job.garment_image_url, self.product.image_urls[0])
        mock_task.delay.assert_called_once_with(str(job.id))

    def test_create_without_photo_returns_code(self):
        self.profile.try_on_photo.delete(save=True)
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "TRY_ON_PHOTO_REQUIRED")

    def test_create_without_product_image_returns_code(self):
        bare = create_product(id_external="ext-2", image_urls=[])
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [bare.id]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "PRODUCT_IMAGE_REQUIRED")

    def test_create_with_invalid_products_returns_code(self):
        for payload in ({}, {"product_ids": []}, {"product_ids": [1, 2]}, {"product_ids": [99999]}):
            response = self.client.post("/api/v1/tryon/", payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["code"], "INVALID_PRODUCTS")

    @mock.patch("core.tryon.api.v1.tryon.features.tryon.generate_try_on_task")
    def test_get_job_only_for_owner(self, mock_task):
        response = self.client.post(
            "/api/v1/tryon/", {"product_ids": [self.product.id]}, format="json"
        )
        job_id = response.json()["job"]["id"]

        detail = self.client.get(f"/api/v1/tryon/{job_id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["job"]["id"], job_id)

        other = get_user_model().objects.create_user(username="otro", password="secret123")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(f"/api/v1/tryon/{job_id}/").status_code, 404)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post("/api/v1/tryon/", {"product_ids": [1]}, format="json").status_code,
            401,
        )
```

- [ ] **Step 2: Correr y ver fallar** (404 en las rutas / import errors)

- [ ] **Step 3: Implementar feature service**

`core/tryon/api/v1/tryon/features/tryon.py`:

```python
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
```

Nota: el test parchea `core.tryon.api.v1.tryon.features.tryon.generate_try_on_task`, por eso el import es del paquete `core.tryon.task` re-exportado.

`core/tryon/api/v1/tryon/features/__init__.py`:

```python
from core.tryon.api.v1.tryon.features.tryon import TryOnApi, TryOnValidationError

__all__ = ["TryOnApi", "TryOnValidationError"]
```

- [ ] **Step 4: Outputs, views y urls**

`core/tryon/api/v1/tryon/outputs.py`:

```python
class TryOnJobOutput:
    def __init__(self, job, request=None):
        self.job = job
        self.request = request

    @property
    def data(self):
        return {"job": self.job.to_json_api(request=self.request)}
```

`core/tryon/api/v1/tryon/views.py`:

```python
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.tryon.api.v1.tryon.features import TryOnApi, TryOnValidationError
from core.tryon.api.v1.tryon.outputs import TryOnJobOutput


class TryOnCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            job = TryOnApi(request).create_job(request.data)
        except TryOnValidationError as e:
            return Response(
                {"message": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            TryOnJobOutput(job, request=request).data,
            status=status.HTTP_201_CREATED,
        )


class TryOnJobDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id, *args, **kwargs):
        job = TryOnApi(request).get_job(job_id)
        if not job:
            return Response(
                {"message": "Prueba no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TryOnJobOutput(job, request=request).data)
```

`core/tryon/api/v1/tryon/urls.py`:

```python
from django.urls import path

from core.tryon.api.v1.tryon.views import TryOnCreateApiView, TryOnJobDetailApiView

urlpatterns = [
    path("", TryOnCreateApiView.as_view(), name="api_v1_tryon_create"),
    path("<uuid:job_id>/", TryOnJobDetailApiView.as_view(), name="api_v1_tryon_detail"),
]
```

`core/tryon/api/v1/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("tryon/", include("core.tryon.api.v1.tryon.urls")),
]
```

`core/tryon/api/__init__.py` y `core/tryon/api/v1/__init__.py` y `core/tryon/api/v1/tryon/__init__.py`: vacíos.

En `config/urls.py`, después de la línea de `core.scraper.api.v1.urls`:

```python
    path("api/v1/", include("core.tryon.api.v1.urls")),
```

- [ ] **Step 5: Correr toda la app + suite completa**

Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py test core.tryon -v 2`
Expected: PASS.
Run: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py test`
Expected: PASS (sin romper lo existente).

- [ ] **Step 6: Commit (repo ZAFIRA-CORE)**

```bash
git add core/tryon config/urls.py
git commit -m "feat: add try-on API endpoints (create job + poll status)"
```

---

## Parte C — Flutter (repo zafira)

### Task C1: Modelo + service + repository + usecase

**Files:**
- Create: `lib/feature/try_on/domain/try_on_job_model.dart`
- Create: `lib/feature/try_on/data/services/try_on_service.dart`
- Create: `lib/feature/try_on/data/interfaces/try_on_interface.dart`
- Create: `lib/feature/try_on/data/repositories/try_on_repository.dart`
- Create: `lib/feature/try_on/application/try_on_usecase.dart`
- Test: `test/feature/try_on/try_on_job_model_test.dart`

- [ ] **Step 1: Test del modelo**

`test/feature/try_on/try_on_job_model_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:zafira/feature/try_on/domain/try_on_job_model.dart';

void main() {
  test('fromJson parses job payload', () {
    final job = TryOnJobModel.fromJson({
      'id': 'abc-123',
      'status': 'completed',
      'product_id': 7,
      'result_url': 'http://core.test/media/try_on_results/x.png',
      'error_message': '',
      'created_at': '2026-07-05T10:00:00',
    });

    expect(job.id, 'abc-123');
    expect(job.isCompleted, isTrue);
    expect(job.isFailed, isFalse);
    expect(job.resultUrl, 'http://core.test/media/try_on_results/x.png');
  });

  test('fromJson tolerates missing fields', () {
    final job = TryOnJobModel.fromJson({'id': 'abc'});

    expect(job.status, 'pending');
    expect(job.resultUrl, isNull);
    expect(job.errorMessage, '');
  });
}
```

Nota: verificar el nombre del package en `pubspec.yaml` (`name:`); si no es `zafira`, ajustar los imports `package:zafira/...` de los tests.

- [ ] **Step 2: Correr y ver fallar**

Run (PowerShell, desde `C:\FAZQ\DEV\MOBILE\MULTIPLATFORM\zafira`): `flutter test test/feature/try_on`
Expected: FAIL (archivo no existe).

- [ ] **Step 3: Implementar modelo**

`lib/feature/try_on/domain/try_on_job_model.dart`:

```dart
class TryOnJobModel {
  const TryOnJobModel({
    required this.id,
    required this.status,
    this.resultUrl,
    this.errorMessage = '',
  });

  final String id;
  final String status;
  final String? resultUrl;
  final String errorMessage;

  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';

  factory TryOnJobModel.fromJson(Map<String, dynamic> json) {
    final result = json['result_url'];
    return TryOnJobModel(
      id: json['id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'pending',
      resultUrl: result == null ? null : result.toString(),
      errorMessage: json['error_message']?.toString() ?? '',
    );
  }
}
```

- [ ] **Step 4: Service, interface, repository, usecase (patrón catalog)**

`lib/feature/try_on/data/services/try_on_service.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/utils/logger.dart';
import '../../../../modules/common/drivers/http/dio_http_client.dart';
import '../../domain/try_on_job_model.dart';

final tryOnServiceProvider = Provider<TryOnService>((ref) {
  final remoteDataSource = ref.watch(dioHttpClientProvider);
  return TryOnService(remoteDataSource: remoteDataSource);
});

class TryOnService {
  TryOnService({required this.remoteDataSource});

  final DioHttpClient remoteDataSource;

  Future<TryOnJobModel> createJob(int productId) async {
    const url = '/api/v1/tryon/';

    DebugLogger(runtimeType).request(url, {'product_ids': productId});

    final response = await remoteDataSource().post(
      url,
      data: {
        'product_ids': [productId],
      },
    );

    DebugLogger(runtimeType).response(url, [response.statusCode]);

    final data = response.data as Map<String, dynamic>;
    return TryOnJobModel.fromJson(data['job'] as Map<String, dynamic>);
  }

  Future<TryOnJobModel> getJob(String jobId) async {
    final url = '/api/v1/tryon/$jobId/';

    DebugLogger(runtimeType).request(url);

    final response = await remoteDataSource().get(url);

    DebugLogger(runtimeType).response(url, [response.statusCode]);

    final data = response.data as Map<String, dynamic>;
    return TryOnJobModel.fromJson(data['job'] as Map<String, dynamic>);
  }
}
```

`lib/feature/try_on/data/interfaces/try_on_interface.dart`:

```dart
import '../../domain/try_on_job_model.dart';

abstract class ITryOn {
  Future<TryOnJobModel> createJob(int productId);

  Future<TryOnJobModel> getJob(String jobId);
}
```

`lib/feature/try_on/data/repositories/try_on_repository.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/try_on_job_model.dart';
import '../interfaces/try_on_interface.dart';
import '../services/try_on_service.dart';

final tryOnRepositoryProvider = Provider<ITryOn>((ref) {
  final remoteDataSource = ref.watch(tryOnServiceProvider);
  return TryOnRepository(remoteDataSource: remoteDataSource);
});

class TryOnRepository implements ITryOn {
  TryOnRepository({required this.remoteDataSource});

  final TryOnService remoteDataSource;

  @override
  Future<TryOnJobModel> createJob(int productId) async =>
      await remoteDataSource.createJob(productId);

  @override
  Future<TryOnJobModel> getJob(String jobId) async =>
      await remoteDataSource.getJob(jobId);
}
```

`lib/feature/try_on/application/try_on_usecase.dart`:

```dart
import 'package:either_dart/either.dart';

import '../../../core/utils/logger.dart';
import '../../../modules/common/error/mixin_error_controller.dart';
import '../data/interfaces/try_on_interface.dart';
import '../domain/try_on_job_model.dart';

class TryOnUseCase with ErrorExceptionHandler {
  TryOnUseCase(this.interface);

  final ITryOn interface;

  Future<Either<Exception, TryOnJobModel>> createJob(int productId) async {
    const String methodName = "CREATE_TRY_ON_JOB";
    DebugLogger(runtimeType).methodInit(methodName);

    return await handlerApiExceptions(
      () async => await interface.createJob(productId),
      methodName,
      runtimeType,
    );
  }

  Future<Either<Exception, TryOnJobModel>> getJob(String jobId) async {
    const String methodName = "GET_TRY_ON_JOB";
    DebugLogger(runtimeType).methodInit(methodName);

    return await handlerApiExceptions(
      () async => await interface.getJob(jobId),
      methodName,
      runtimeType,
    );
  }
}
```

- [ ] **Step 5: Correr tests → PASS, commit (repo zafira)**

```bash
git add lib/feature/try_on test/feature/try_on
git commit -m "feat: add try-on job model, service and usecase"
```

### Task C2: State + controller con polling

**Files:**
- Create: `lib/feature/try_on/view/state/try_on_state.dart`
- Create: `lib/feature/try_on/view/controller/try_on_controller.dart`
- Test: `test/feature/try_on/try_on_controller_test.dart`

- [ ] **Step 1: Test del controller (interface fake, polling con `Duration.zero`)**

`test/feature/try_on/try_on_controller_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:zafira/feature/try_on/application/try_on_usecase.dart';
import 'package:zafira/feature/try_on/data/interfaces/try_on_interface.dart';
import 'package:zafira/feature/try_on/domain/try_on_job_model.dart';
import 'package:zafira/feature/try_on/view/controller/try_on_controller.dart';
import 'package:zafira/feature/try_on/view/state/try_on_state.dart';

class FakeTryOn implements ITryOn {
  FakeTryOn({required this.statuses, this.failCreate = false});

  final List<String> statuses;
  final bool failCreate;
  int polls = 0;

  @override
  Future<TryOnJobModel> createJob(int productId) async {
    if (failCreate) throw Exception('create failed');
    return const TryOnJobModel(id: 'job-1', status: 'pending');
  }

  @override
  Future<TryOnJobModel> getJob(String jobId) async {
    final status = statuses[polls < statuses.length ? polls : statuses.length - 1];
    polls++;
    return TryOnJobModel(
      id: jobId,
      status: status,
      resultUrl: status == 'completed' ? 'http://core.test/r.png' : null,
      errorMessage: status == 'failed' ? 'No pudimos generar tu prueba.' : '',
    );
  }
}

TryOnController buildController(FakeTryOn fake) => TryOnController(
      TryOnUseCase(fake),
      pollInterval: Duration.zero,
    );

void main() {
  test('reaches success when job completes', () async {
    final fake = FakeTryOn(statuses: ['processing', 'processing', 'completed']);
    final controller = buildController(fake);

    await controller.startTryOn(7);

    expect(controller.state.status, TryOnStatus.success);
    expect(controller.state.job?.resultUrl, 'http://core.test/r.png');
  });

  test('reaches failure when job fails', () async {
    final fake = FakeTryOn(statuses: ['processing', 'failed']);
    final controller = buildController(fake);

    await controller.startTryOn(7);

    expect(controller.state.status, TryOnStatus.failure);
    expect(controller.state.errorMessage, isNotEmpty);
  });

  test('create error sets failure', () async {
    final controller = buildController(FakeTryOn(statuses: [], failCreate: true));

    await controller.startTryOn(7);

    expect(controller.state.status, TryOnStatus.failure);
  });
}
```

- [ ] **Step 2: Correr y ver fallar**

Run: `flutter test test/feature/try_on/try_on_controller_test.dart`
Expected: FAIL (archivos no existen).

- [ ] **Step 3: Implementar state y controller**

`lib/feature/try_on/view/state/try_on_state.dart`:

```dart
import '../../domain/try_on_job_model.dart';

enum TryOnStatus { initial, creating, generating, success, failure }

class TryOnState {
  TryOnState({required this.status, this.job, this.errorMessage});

  factory TryOnState.initial() => TryOnState(status: TryOnStatus.initial);

  final TryOnStatus status;
  final TryOnJobModel? job;
  final String? errorMessage;

  TryOnState copyWith({
    TryOnStatus? status,
    TryOnJobModel? job,
    String? errorMessage,
  }) => TryOnState(
    status: status ?? this.status,
    job: job ?? this.job,
    errorMessage: errorMessage ?? this.errorMessage,
  );
}
```

`lib/feature/try_on/view/controller/try_on_controller.dart`:

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/try_on_usecase.dart';
import '../../data/repositories/try_on_repository.dart';
import '../state/try_on_state.dart';

final tryOnControllerProvider =
    StateNotifierProvider.autoDispose<TryOnController, TryOnState>((ref) {
      final tryOnRepository = ref.watch(tryOnRepositoryProvider);

      return TryOnController(TryOnUseCase(tryOnRepository));
    });

class TryOnController extends StateNotifier<TryOnState> {
  TryOnController(
    this._tryOnUseCase, {
    this.pollInterval = const Duration(milliseconds: 2500),
    this.maxAttempts = 48,
  }) : super(TryOnState.initial());

  final TryOnUseCase _tryOnUseCase;
  final Duration pollInterval;
  final int maxAttempts;

  Future<void> startTryOn(int productId) async {
    state = TryOnState.initial().copyWith(status: TryOnStatus.creating);

    final created = await _tryOnUseCase.createJob(productId);

    await created.fold(
      (err) async {
        state = state.copyWith(
          status: TryOnStatus.failure,
          errorMessage:
              'No se pudo iniciar la prueba virtual. Verifica tu foto e intenta de nuevo.',
        );
      },
      (job) async {
        state = state.copyWith(status: TryOnStatus.generating, job: job);
        await _pollUntilDone(job.id);
      },
    );
  }

  Future<void> _pollUntilDone(String jobId) async {
    for (var attempt = 0; attempt < maxAttempts; attempt++) {
      await Future<void>.delayed(pollInterval);
      if (!mounted) return;

      final response = await _tryOnUseCase.getJob(jobId);
      final job = response.fold((err) => null, (job) => job);
      if (job == null) continue;
      if (!mounted) return;

      if (job.isCompleted) {
        state = state.copyWith(status: TryOnStatus.success, job: job);
        return;
      }
      if (job.isFailed) {
        state = state.copyWith(
          status: TryOnStatus.failure,
          job: job,
          errorMessage: job.errorMessage.isEmpty
              ? 'No pudimos generar tu prueba virtual.'
              : job.errorMessage,
        );
        return;
      }
      state = state.copyWith(job: job);
    }

    if (!mounted) return;
    state = state.copyWith(
      status: TryOnStatus.failure,
      errorMessage: 'La generación tardó demasiado. Intenta de nuevo.',
    );
  }
}
```

- [ ] **Step 4: Correr tests → PASS, commit (repo zafira)**

```bash
git add lib/feature/try_on/view test/feature/try_on/try_on_controller_test.dart
git commit -m "feat: add try-on controller with polling state"
```

### Task C3: Pantalla de resultado + conectar botón "Probar con IA"

**Files:**
- Create: `lib/feature/try_on/view/main/try_on_result_screen.dart`
- Modify: `lib/modules/common/routes/app_router.dart` (registrar ruta)
- Modify: `lib/feature/catalog/view/main/product_detail_screen.dart:454-457` (placeholder actual)

- [ ] **Step 1: Pantalla de resultado**

`lib/feature/try_on/view/main/try_on_result_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gap/gap.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_numbers.dart';
import '../../../../core/helpers/context_helper.dart';
import '../controller/try_on_controller.dart';
import '../state/try_on_state.dart';

class TryOnResultScreen extends ConsumerStatefulWidget {
  const TryOnResultScreen({super.key, required this.productId});

  static const routeName = '/try-on/result';

  final int productId;

  @override
  ConsumerState<TryOnResultScreen> createState() => _TryOnResultScreenState();
}

class _TryOnResultScreenState extends ConsumerState<TryOnResultScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(tryOnControllerProvider.notifier).startTryOn(widget.productId),
    );
  }

  void _retry() {
    ref.read(tryOnControllerProvider.notifier).startTryOn(widget.productId);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.appColors;
    final state = ref.watch(tryOnControllerProvider);

    return Scaffold(
      backgroundColor: colors.nightDeep,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(gradient: colors.authBackground),
        child: SafeArea(
          child: Padding(
            padding: kSpaceDeviceHLg,
            child: Column(
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: () => context.pop(),
                      icon: Icon(Icons.arrow_back, color: colors.white),
                    ),
                    Expanded(
                      child: Text(
                        'Probador virtual',
                        textAlign: TextAlign.center,
                        style: context.typography.titleMedium?.copyWith(
                          color: colors.white,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 48),
                  ],
                ),
                const Gap(separatorLg),
                Expanded(child: _buildBody(state, colors)),
                const Gap(separatorMd),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody(TryOnState state, dynamic colors) {
    switch (state.status) {
      case TryOnStatus.initial:
      case TryOnStatus.creating:
      case TryOnStatus.generating:
        return Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: colors.primaryLight),
            const Gap(separatorLg),
            Text(
              'Probando tu prenda…',
              style: context.typography.titleMedium?.copyWith(
                color: colors.white,
                fontWeight: FontWeight.w800,
              ),
            ),
            const Gap(separatorXSm),
            Text(
              'La IA está generando tu imagen. Esto puede tardar unos segundos.',
              textAlign: TextAlign.center,
              style: context.typography.bodySmall?.copyWith(color: colors.slate),
            ),
          ],
        );
      case TryOnStatus.success:
        return Column(
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: kBorderRadiusAllXLarge,
                child: Image.network(
                  state.job?.resultUrl ?? '',
                  fit: BoxFit.contain,
                  width: double.infinity,
                  loadingBuilder: (context, child, progress) => progress == null
                      ? child
                      : Center(
                          child: CircularProgressIndicator(color: colors.primaryLight),
                        ),
                  errorBuilder: (context, error, stackTrace) => Center(
                    child: Icon(
                      Icons.broken_image_outlined,
                      color: colors.slate,
                      size: 54,
                    ),
                  ),
                ),
              ),
            ),
            const Gap(separatorLg),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                onPressed: () => context.pop(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  side: BorderSide(color: colors.white.withValues(alpha: 0.7)),
                  shape: const RoundedRectangleBorder(
                    borderRadius: kBorderRadiusAllLarge,
                  ),
                ),
                icon: Icon(Icons.checkroom_rounded, color: colors.white),
                label: Text(
                  'Probar otra prenda',
                  style: context.typography.labelLarge?.copyWith(
                    color: colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
          ],
        );
      case TryOnStatus.failure:
        return Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline_rounded, color: colors.error, size: 54),
            const Gap(separatorMd),
            Text(
              state.errorMessage ?? 'No pudimos generar tu prueba virtual.',
              textAlign: TextAlign.center,
              style: context.typography.bodyMedium?.copyWith(
                color: colors.white,
                height: 1.4,
              ),
            ),
            const Gap(separatorLg),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: colors.gradientPrimary,
                  borderRadius: kBorderRadiusAllLarge,
                ),
                child: ElevatedButton.icon(
                  onPressed: _retry,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    shape: const RoundedRectangleBorder(
                      borderRadius: kBorderRadiusAllLarge,
                    ),
                  ),
                  icon: Icon(Icons.refresh_rounded, color: colors.nightDeep),
                  label: Text(
                    'Reintentar',
                    style: context.typography.labelLarge?.copyWith(
                      color: colors.nightDeep,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
    }
  }
}
```

Nota: revisar los nombres reales en `context.appColors` (`error`, `slate`, `primaryLight`, `gradientPrimary`, `authBackground`, `nightDeep`) — todos aparecen usados en `upload_photo_screen.dart`, así que deberían existir. Si `_buildBody` con `dynamic colors` molesta al linter, tipar con la clase real de colores del tema.

- [ ] **Step 2: Registrar ruta en `app_router.dart`**

Agregar import y `GoRoute` junto a los de try_on existentes (después del bloque de `PhotoPreviewScreen`):

```dart
        GoRoute(
          path: TryOnResultScreen.routeName,
          pageBuilder: (context, state) => _fadePage(
            TryOnResultScreen(productId: state.extra as int? ?? 0),
            state,
          ),
        ),
```

- [ ] **Step 3: Conectar el botón placeholder en `product_detail_screen.dart`**

El botón ya existe (líneas ~440-471) con `onTap` placeholder. Reemplazar:

```dart
                        onTap: () => AppNotification.info(
                          context,
                          'Try-On con IA disponible próximamente',
                        ),
```

por:

```dart
                        onTap: () {
                          final user = ref.read(authControllerProvider).user;
                          final hasPhoto =
                              (user?.tryOnPhoto ?? '').trim().isNotEmpty;
                          if (!hasPhoto) {
                            AppNotification.info(
                              context,
                              'Primero sube tu foto para el probador virtual',
                            );
                            context.push(UploadPhotoScreen.routeName);
                            return;
                          }
                          context.push(
                            TryOnResultScreen.routeName,
                            extra: product.id,
                          );
                        },
```

Agregar los imports que falten en `product_detail_screen.dart`:

```dart
import '../../../auth/view/controller/auth_controller.dart';
import '../../../try_on/view/main/try_on_result_screen.dart';
import '../../../try_on/view/main/upload_photo_screen.dart';
```

(Verificar cuáles ya existen; `go_router` y `AppNotification` ya están importados en ese archivo.)

- [ ] **Step 4: Analizar y correr tests**

Run: `flutter analyze lib/feature/try_on lib/feature/catalog/view/main/product_detail_screen.dart`
Expected: sin errores.
Run: `flutter test test/feature/try_on`
Expected: PASS.

- [ ] **Step 5: Commit (repo zafira)**

```bash
git add lib/feature/try_on lib/feature/catalog/view/main/product_detail_screen.dart lib/modules/common/routes/app_router.dart
git commit -m "feat: wire try-on AI flow with result screen and polling"
```

---

## Parte D — Configuración y verificación end-to-end

### Task D1: Configurar credenciales y levantar los servicios

- [ ] **Step 1: Crear el `ExternalProvider` en ZAFIRA-CORE**

Run:

```bash
wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py shell -c "
from core.security.models import ExternalProvider
import secrets
p, created = ExternalProvider.objects.get_or_create(name='zafira-ia', defaults={'client_secret': secrets.token_urlsafe(32)})
print('client_id:', p.client_id)
print('client_secret:', p.client_secret)
"
```

- [ ] **Step 2: Configurar `.env` de ZAFIRA-IA**

Con los valores impresos en el paso anterior:

```bash
HMAC_ALLOWED_CLIENTS={"<client_id>": "<client_secret>"}
AI_BACKEND=gemini
GEMINI_API_KEY=<la key existente de Google Gemini>
```

- [ ] **Step 3: Configurar `.env` de ZAFIRA-CORE**

```bash
ZAFIRA_IA_BASE_URL=http://localhost:8001
SITE_URL=http://localhost:8000
```

- [ ] **Step 4: Levantar servicios y probar el flujo (smoke test manual)**

1. Redis: `wsl -d ubuntu -- docker compose -f /home/freddyandres/Project_development/Django/ZAFIRA-CORE/deploy/docker-service-zafira/docker-compose.yml up -d redis` (o el redis local que use).
2. ZAFIRA-IA: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-IA -- poetry run uvicorn app.main:app --port 8001`
3. Django: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/python manage.py runserver`
4. Celery: `wsl -d ubuntu --cd /home/freddyandres/Project_development/Django/ZAFIRA-CORE -- ~/.pyenv/versions/zafira-core/bin/celery -A config worker -l info`
5. Con un usuario que tenga `try_on_photo`, hacer `POST /api/v1/tryon/` con `{"product_ids": [<id>]}` (token en header) y polling a `GET /api/v1/tryon/<job_id>/` hasta `completed`; abrir `result_url`.
6. En la app Flutter (flavor dev apuntando al backend local), abrir un producto → "Probar con IA" → ver animación → ver resultado.

- [ ] **Step 5: Commit final de docs si hubo ajustes**

---

## Notas de fase 2 (NO implementar ahora)

- Multi-prenda: `product_ids` ya es lista; encadenar top+bottom en la tarea Celery.
- Push FCM al completar (implementar `lib/core/services/push_notification_service.dart`).
- Historial `GET /api/v1/tryon/` (list).
- MinIO compartido (ZAFIRA-IA ya sube a S3 si `STORAGE_ENDPOINT_URL` está configurado).
