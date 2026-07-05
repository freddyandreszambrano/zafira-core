# Probador Virtual IA — Diseño end-to-end (mobile → ZAFIRA-CORE → ZAFIRA-IA)

**Fecha:** 2026-07-05
**Estado:** Aprobado por Freddy
**Repos involucrados:**
- `ZAFIRA-CORE` (Django) — este repo
- `ZAFIRA-IA` (FastAPI) — `~/Project_development/Django/ZAFIRA-IA`
- `zafira` (Flutter) — `C:\FAZQ\DEV\MOBILE\MULTIPLATFORM\zafira`

## Objetivo

El usuario logueado en la app móvil, que ya tiene su foto de try-on subida
(`MobileProfile.try_on_photo`), pulsa "Probar con IA" en el detalle de un
producto y recibe una imagen generada de sí mismo usando esa prenda.

## Decisiones tomadas

| Decisión | Elección |
|---|---|
| Motor de IA | Gemini 2.5 Flash Image (nano banana) vía REST desde ZAFIRA-IA. OpenCV/MediaPipe descartados (calidad de overlay insuficiente). |
| UX de espera | Asíncrono: Celery en CORE + polling desde mobile cada 2.5s. Push FCM queda para fase 2. |
| Alcance MVP | 1 prenda por job. El API acepta `product_ids` (lista) para habilitar multi-prenda en fase 2 sin romper contrato. |
| Storage del resultado | ZAFIRA-IA devuelve la imagen en base64; Django la guarda en `/media/try_on_results/`. MinIO/S3 opcional a futuro. |

## Flujo

```
Flutter                    ZAFIRA-CORE (Django)              ZAFIRA-IA (FastAPI)
  │ POST /api/v1/tryon/        │                                  │
  │ {product_ids: [id]}        │                                  │
  ├───────────────────────────>│ crea TryOnJob (pending)          │
  │<── {job_id, status} ───────┤ encola tarea Celery              │
  │  (polling cada 2.5s)       │ [Celery] firma HMAC y llama:     │
  │ GET /api/v1/tryon/{id}/    ├─── POST /api/v1/tryon ──────────>│ descarga persona + prenda
  │<── {status: processing} ───┤                                  │ Gemini image → composite
  │                            │<── {result_image_b64} ───────────┤
  │                            │ guarda /media/try_on_results/    │
  │ GET /api/v1/tryon/{id}/    │ TryOnJob → completed             │
  │<── {status, result_url} ───┤                                  │
```

## 1. ZAFIRA-CORE — app nueva `core/tryon`

App Django nueva con paquetes (`models/`, `api/v1/`, `services/`, `task/`,
`tests/`), siguiendo el patrón modular del proyecto.

### Modelo `TryOnJob` (`core/tryon/models/job.py`)

- `id`: UUIDField pk (se usa como `external_ref` hacia ZAFIRA-IA)
- `user`: FK a AUTH_USER_MODEL
- `product`: FK a `scraper.Product`
- `garment_image_url`: TextField (snapshot de `product.image_urls[0]`)
- `garment_type`: TextField (`upper_body` / `lower_body` / `dress`)
- `status`: TextField con choices `pending / processing / completed / failed`
- `result_image`: ImageField `upload_to='try_on_results/%Y/%m/%d/'`, null/blank
- `error_message`: TextField blank
- `created_at` / `updated_at`
- `to_json_api(request)`: `{id, status, product_id, result_url, error_message, created_at}`

### API v1 (`core/tryon/api/v1/tryon/`)

- `POST /api/v1/tryon/` (autenticado):
  - Body: `{"product_ids": [<int>]}` — MVP valida exactamente 1 elemento.
  - Validaciones → 400 con `code`:
    - `TRY_ON_PHOTO_REQUIRED`: usuario sin `MobileProfile.try_on_photo`
    - `PRODUCT_IMAGE_REQUIRED`: producto sin `image_urls`
    - `INVALID_PRODUCTS`: lista vacía, >1 (MVP) o ids inexistentes
  - Crea `TryOnJob` + encola tarea Celery → 201 `{job: {...}}`
- `GET /api/v1/tryon/<uuid:job_id>/` (autenticado, solo dueño): estado del job.
- Lógica en service class `TryOnApi` (`features/tryon.py`), views delgadas,
  patrón `to_json_api` — igual que `MobileProfileApi`.

### Cliente ZAFIRA-IA (`core/tryon/services/zafira_ia_client.py`)

- Credenciales desde `ExternalProvider` con `name="zafira-ia"` (BD).
- Firma: `HMAC-SHA256(raw_body + timestamp, client_secret)` → headers
  `X-CLIENT-ID`, `X-TIMESTAMP` (epoch segundos), `X-SIGNATURE` (hex).
  Compatible con `HmacRequestVerifier` de ZAFIRA-IA.
- Base URL por env: `ZAFIRA_IA_BASE_URL` (default `http://localhost:8001`).
- Timeout de request: 180s (Gemini tarda 10-30s típicamente).
- Excepciones tipadas: `ZafiraIaUnavailable` (red/5xx, reintentables) y
  `ZafiraIaRejected` (4xx, no reintentables).

### Tarea Celery (`core/tryon/task/tryon.py`)

1. Marca job `processing`.
2. `person_image_url` = `SITE_URL` + URL de `try_on_photo` (env `SITE_URL`,
   default `http://localhost:8000`; en dev ambos servicios corren en la misma
   máquina así que localhost es alcanzable).
3. `garment_type` desde mapa `category → garment_type` (módulo
   `core/tryon/services/garment_mapping.py`; ej. camisetas/camisas/chaquetas →
   `upper_body`; pantalones/jeans/faldas → `lower_body`; vestidos → `dress`;
   default `upper_body`).
4. Llama `POST {ZAFIRA_IA_BASE_URL}/api/v1/tryon` con
   `{external_ref, person_image_url, garment_image_url, garment_type}`.
5. Decodifica `result_image_b64`, guarda en `result_image`, marca `completed`.
6. Errores: `ZafiraIaUnavailable` → retry ×2 (backoff 5s/15s), luego `failed`;
   `ZafiraIaRejected` → `failed` inmediato con mensaje amigable.

## 2. ZAFIRA-IA — backend `gemini` + contrato de respuesta

### Adaptador Gemini (`src/app/infrastructure/ai/gemini.py`)

- `GeminiTryOnModel` implementa el Protocol `TryOnModel`:
  recibe bytes de persona + prenda + `garment_type`, llama al endpoint REST
  `generateContent` de Gemini (`httpx`, sin SDK nuevo) con las dos imágenes
  inline (base64) y un prompt de virtual try-on que instruye preservar
  identidad/pose de la persona y reemplazar la prenda del tipo indicado.
- Extrae la imagen de la respuesta (`inline_data`); si Gemini no devuelve
  imagen (bloqueo de seguridad, respuesta solo-texto) → `DomainError` con
  código `GENERATION_REJECTED`.
- Settings nuevos: `GEMINI_API_KEY`, `GEMINI_MODEL`
  (default `gemini-2.5-flash-image`), `ai_backend` acepta literal `"gemini"`.
- Wiring en `interfaces/dependencies.py` junto a `stub`/`hosted`.

### Cambio de contrato `POST /api/v1/tryon` (y `/avatar` igual)

- Response agrega `result_image_b64: str` (siempre presente).
- La subida a S3 pasa a ser **opcional**: solo si `STORAGE_ENDPOINT_URL` está
  configurado; en ese caso también devuelve `result_image_key`, si no,
  `result_image_key: null`.
- Use cases ajustados; tests existentes actualizados al nuevo contrato.

## 3. Flutter — completar feature `try_on`

- `lib/feature/try_on/domain/try_on_job_model.dart` (freezed):
  `id, status, resultUrl, errorMessage`.
- `lib/feature/try_on/data/services/try_on_service.dart` (Dio):
  `createJob(productId)` → POST `/api/v1/tryon/`;
  `getJob(jobId)` → GET `/api/v1/tryon/{id}/`.
- Provider Riverpod de polling: tras crear el job consulta cada 2.5s hasta
  `completed`/`failed`; timeout de seguridad 120s → estado de error con
  opción de reintentar.
- `product_detail_screen`: botón "Probar con IA".
  - Si `user.try_on_photo == null` → navega a `upload_photo_screen` (existente).
  - Si tiene foto → crea job y navega a pantalla de resultado.
- `lib/feature/try_on/view/main/try_on_result_screen.dart`: animación de
  espera ("Probando tu prenda…"), resultado con imagen generada y acciones
  reintentar / guardar / compartir.
- Manejo del 400 `TRY_ON_PHOTO_REQUIRED` como fallback server-side → redirige
  a subir foto.

## 4. Errores y casos borde

| Caso | Comportamiento |
|---|---|
| Usuario sin foto try-on | 400 `TRY_ON_PHOTO_REQUIRED`; mobile redirige a subir foto |
| Producto sin imágenes | 400 `PRODUCT_IMAGE_REQUIRED` |
| Gemini bloquea/rechaza | Job `failed` + mensaje amigable |
| ZAFIRA-IA caído / 5xx | Retry Celery ×2 → `failed` |
| Polling supera 120s | Mobile muestra error con reintentar (el job puede completarse igual; al reintentar consulta primero el estado) |
| Job de otro usuario | 404 |

## 5. Configuración

| Repo | Variable | Valor dev |
|---|---|---|
| CORE | `ZAFIRA_IA_BASE_URL` | `http://localhost:8001` |
| CORE | `SITE_URL` | `http://localhost:8000` |
| CORE | BD: `ExternalProvider(name="zafira-ia")` | client_id/secret compartidos con IA |
| IA | `HMAC_ALLOWED_CLIENTS` | `{"<client_id>": "<client_secret>"}` |
| IA | `AI_BACKEND` | `gemini` |
| IA | `GEMINI_API_KEY` | key existente |
| IA | `GEMINI_MODEL` | `gemini-2.5-flash-image` |

## 6. Testing

- **CORE** (`core/tryon/tests/`): API create/get (validaciones, ownership,
  formatos), tarea Celery con cliente mockeado (éxito, retry, rechazo),
  firma HMAC del cliente (headers y firma verificables con el mismo algoritmo
  de ZAFIRA-IA), mapeo de `garment_type`.
- **IA**: tests del backend gemini con `httpx` mockeado / fake model
  (happy path, respuesta sin imagen, error de API), contrato nuevo de
  respuesta (`result_image_b64`, storage opcional) en tests existentes.
- **Flutter**: unit tests de `TryOnService` y del provider de polling con
  Dio mockeado (completed, failed, timeout).

## Fase 2 (fuera de alcance MVP)

- Multi-prenda (outfit top+bottom encadenado: el resultado del top es la
  persona para el bottom) — el contrato `product_ids` ya lo permite.
- Push FCM al completar el job (implementar `push_notification_service.dart`).
- Historial de try-ons en la app (`GET /api/v1/tryon/` list).
- MinIO/S3 compartido para resultados.
