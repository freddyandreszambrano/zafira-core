# Scraper genérico adaptable + flujo previsualizar→guardar

**Fecha:** 2026-07-05
**Repo:** `ZAFIRA-CORE` (Django)

## Problema
1. El scan solo soportaba modarm/etafashion (dominios hardcodeados); cualquier otra URL fallaba.
2. Las 2 fuentes guardadas (`ScraperSource`) son homepages y el flujo buscaba links `/p/` directamente
   en esa página → 0 productos.
3. Los errores del adapter se tragaban con `print` a stderr → la UI decía "éxito" con 0 productos
   (caso Playwright sin browsers instalados).
4. El scan persistía directo a `Product`; se quería: escanear → previsualizar → botón "Guardar" →
   BD → la app consume de la BD.

## Solución
### Motor de extracción multi-estrategia — `core/scraper/extract/`
- `jsonld.py` (schema.org Product/ItemList), `microdata.py`, `opengraph.py`, `embedded.py`
  (`__NEXT_DATA__`, `__INITIAL_STATE__`…), `heuristic.py` (detección de cards repetidas con precio),
  `links.py` (descubrimiento de links de producto y de listados), `prices.py` (parser robusto
  US/EU: `$1,299.00`, `1.299,00`, `$71,92`), `engine.py` (orquesta estrategias, merge, normaliza
  al contrato de adapter, `slug_id`).

### `GenericAdapter` — `core/scraper/adapters/generic.py`
- Acepta cualquier URL http(s). Pipeline: atajo Shopify (`/products.json`) → fetch estático +
  estrategias → si la página es SPA (pocos links) render con Chromium headless (`browser.py`,
  hilo dedicado) → si es página de producto único la detecta → último recurso: cruza hasta 4
  listados internos. Productos completos quedan prefetched (no re-fetch por producto).
- Registrado como `generic` al FINAL de `ADAPTER_MAP`; `infer_store_from_url` cae ahí si ningún
  adapter específico matchea. `Product.store` = dominio (ej. `allbirds.com`).

### services.py
- `scan_url(..., persist=False)` para la vista (preview) — el comando `manage.py scrape` sigue
  persistiendo. `save_products(store, products)` valida y persiste el payload del preview
  (retorna created/updated/skipped).
- URL raíz con adapter conocido → `_scan_root`: recorre categorías del adapter con corte temprano
  (fix de "los homepages no traen nada").
- Errores ya NO se tragan: suben al array `errors` con hint amigable para Playwright faltante.
- Género: keywords ampliados (hombre/caballero/men…, mujer/dama/women…) mirando categoría + URL.

### Vista /scraper/ (scan.html + scan.js)
- `action=scan` → preview sin guardar (muestra tienda + estrategias usadas).
- Si hay ≥1 producto aparece botón **"Guardar N productos"** → `action=save_products` →
  botón verde "Guardados: X nuevos · Y actualizados". Panel de avisos muestra `errors`.

### Infra
- `playwright install chromium` + `playwright install-deps chromium` en WSL (faltaba
  `libasound.so.2`, el Chromium crasheaba al lanzar).
- `_get_browser` endurecido (modarm + BrowserFetcher): si el launch falla se detiene Playwright;
  antes quedaba a medio iniciar y las siguientes llamadas fallaban con "Sync API inside asyncio loop".

## Verificación
- 90 tests del scraper verdes (baseline: 43/46, con 3 fallas pre-existentes corregidas + 11
  tests de regresión nuevos).
- Sonda real: allbirds.com (tienda desconocida) → 3 productos completos vía estrategia `shopify`
  con precio/imágenes/tallas; modarm/etafashion vía categorías con Playwright.

## Ronda de fixes (revisión adversarial multi-agente, 14 hallazgos confirmados)
- **parse_price**: truncaba precios sin separador ≥1000 (`1299.00`→`129`). Regex corregido.
- **heurística**: tomaba el número más chico de la card como precio (`3 colores`→precio 3).
  Ahora exige signo de moneda o 2 decimales.
- **género**: `women`/`female` se clasificaban como `man` (substring + orden). Ahora `woman`
  primero + límite de palabra `\b`.
- **colisión cross-store**: `update_or_create` solo por `id_external` (global unique) sobrescribía
  productos de otra tienda. Ahora `UniqueConstraint(store, id_external)` + key compuesta + `slug_id`
  usa el path completo (migración 0005).
- **save_products**: precio Decimal fuera de rango (1e20) rompía toda lectura de la tabla → se
  clampa a rango válido; loop `@transaction.atomic`; gateado con `PermissionMixin('add_product')`;
  error genérico (sin filtrar excepción cruda).
- **XSS**: URL con esquema `javascript:`/`data:` renderizada en `href` → `Zafira.safeUrl` + guard
  server-side (`finalize` y `_safe_http_url` solo http/https).
- **SSRF**: `GenericAdapter` bloquea hosts internos (localhost, 169.254.x, rangos privados).
- **scan_store** con adapter sin categorías (generic) → `ValueError` claro en vez de ZeroDivision.
- **scan_saved_sources / _scan_product**: capturan excepción por fuente (una URL rota ya no aborta
  todo el run).
- **services_live**: sin fallback a ModarmAdapter para tiendas genéricas (evitaba precios/stock
  falsos parseando con selectores ajenos).
- **generic**: conserva links de ItemList sin `offers`; `parse_product` cae al prefetched si el GET
  de detalle falla; `_get_browser` endurecido.
- **scan.js**: guard de identidad para que un guardado tardío no marque como guardado un escaneo nuevo.
