import logging
import os
import random
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types as genai_types
from groq import Groq

logger = logging.getLogger(__name__)


class InsufficientFavoritesError(Exception):
    """Los favoritos no tienen al menos 1 prenda de torso y 1 de piernas."""


# ── Singletons ────────────────────────────────────────────────────────────────

_groq_client: Groq | None = None
_gemini_client: genai.Client | None = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY no configurada en .env")
        _groq_client = Groq(api_key=key)
    return _groq_client


def _get_gemini() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY no configurada en .env")
        _gemini_client = genai.Client(
            api_key=key,
            # Si Gemini se cuelga, cortamos a los 25s y usamos el fallback
            http_options=genai_types.HttpOptions(timeout=25_000),
        )
    return _gemini_client


# ── Constantes ────────────────────────────────────────────────────────────────

EXCLUDED_CATEGORIES = [
    "perfume",
    "fragancia",
    "maquillaje",
    "cosmetico",
    "belleza",
    "zapato",
    "zapatilla",
    "bota",
    "sandalia",
    "accesorio",
    "bolso",
    "cartera",
    "gorra",
    "sombrero",
    "joya",
    "reloj",
]

COMPLETE_KEYWORDS = [
    "vestido",
    "enterizo",
    "mono",
    "jumpsuit",
    "maxi",
    "minivestido",
]

TORSO_KEYWORDS = [
    "camisa",
    "camiseta",
    "blusa",
    "polo",
    "suéter",
    "sueter",
    "sweater",
    "chaqueta",
    "jacket",
    "abrigo",
    "buzo",
    "hoodie",
    "top",
    "chaleco",
    "chompa",
    "pullover",
    "cardigan",
    "tshirt",
    "t-shirt",
    "buso",
]

PIERNA_KEYWORDS = [
    "pantalón",
    "pantalon",
    "jean",
    "jeans",
    "short",
    "shorts",
    "falda",
    "leggin",
    "legging",
    "bermuda",
    "jogger",
    "cargo",
]

OCCASION_TYPES = {
    "romantic": [
        "cita",
        "romántica",
        "romantica",
        "aniversario",
        "enamorado",
        "cena romántica",
        "san valentín",
        "pareja",
        "novia",
        "novio",
    ],
    "formal": [
        "trabajo",
        "oficina",
        "reunión",
        "reunion",
        "negocios",
        "entrevista",
        "conferencia",
        "presentación",
        "presentacion",
        "corporativo",
        "ejecutivo",
    ],
    "gala": [
        "boda",
        "graduación",
        "graduacion",
        "gala",
        "ceremonia",
        "evento formal",
        "coctel",
        "cóctel",
    ],
    "party": [
        "fiesta",
        "discoteca",
        "club",
        "celebración",
        "celebracion",
        "cumpleaños",
        "after",
        "noche de fiesta",
    ],
    "sport": [
        "gym",
        "gimnasio",
        "deporte",
        "ejercicio",
        "entrenamiento",
        "correr",
        "fútbol",
        "futbol",
        "running",
    ],
    "beach": [
        "playa",
        "piscina",
        "verano",
        "vacaciones",
        "resort",
    ],
}

OCCASION_EXCLUSIONS = {
    "romantic": [
        "hoodie",
        "buzo",
        "buso",
        "chompa",
        "deportivo",
        "sport",
        "athletic",
        "sudadera",
        "cargo",
        "bermuda",
    ],
    "formal": [
        "hoodie",
        "buzo",
        "buso",
        "chompa",
        "deportivo",
        "sport",
        "athletic",
        "sudadera",
        "estampado",
        "cargo",
        "bermuda",
        "short",
    ],
    "gala": [
        "hoodie",
        "buzo",
        "buso",
        "chompa",
        "deportivo",
        "sport",
        "athletic",
        "sudadera",
        "cargo",
        "bermuda",
        "short",
    ],
    "party": ["deportivo", "sport", "athletic", "cargo", "bermuda"],
    "sport": [],
    "beach": ["formal", "vestir", "traje", "blazer"],
    "casual": [],
}

# Cuántos candidatos por grupo se envían a Gemini para evaluación visual
# (8 torso + 8 pierna alcanza de sobra para 3 outfits y reduce mucho el tiempo)
MAX_VISION_CANDIDATES = 8
MAX_OUTFITS = 3


# ── Helpers ───────────────────────────────────────────────────────────────────

_OCCASION_TYPE_CACHE: dict[str, str] = {}


def _detect_occasion_type(occasion: str) -> str:
    """Detecta tipo de ocasión con keyword matching (rápido, sin API call)."""
    key = occasion.strip().lower()
    if key in _OCCASION_TYPE_CACHE:
        return _OCCASION_TYPE_CACHE[key]

    text = key
    for otype, keywords in OCCASION_TYPES.items():
        if any(k in text for k in keywords):
            _OCCASION_TYPE_CACHE[key] = otype
            return otype

    _OCCASION_TYPE_CACHE[key] = "casual"
    return "casual"


def _is_clothing(product) -> bool:
    text = (product.category + " " + product.name).lower()
    return not any(ex in text for ex in EXCLUDED_CATEGORIES)


def _matches_gender(product, gender: str) -> bool:
    cat = product.category.upper()
    return cat.startswith("MUJERES") if gender == "mujer" else cat.startswith("HOMBRES")


def _is_complete(product) -> bool:
    # Solo miramos el NOMBRE — la categoría "FALDAS Y VESTIDOS" también tiene faldas
    return any(k in product.name.lower() for k in COMPLETE_KEYWORDS)


def _is_torso(product) -> bool:
    text = (product.category + " " + product.name).lower()
    return any(k in text for k in TORSO_KEYWORDS)


def _is_pierna(product) -> bool:
    text = (product.category + " " + product.name).lower()
    return any(k in text for k in PIERNA_KEYWORDS)


def _is_appropriate(product, occasion_type: str) -> bool:
    exclusions = OCCASION_EXCLUSIONS.get(occasion_type, [])
    if not exclusions:
        return True
    text = (product.category + " " + product.name).lower()
    return not any(ex in text for ex in exclusions)


def _build_pool(
    products: list, gender: str, occasion_type: str, exclude_ids: set
) -> tuple[list, list, list]:
    gendered = [p for p in products if _matches_gender(p, gender)]
    clothing = [p for p in gendered if _is_clothing(p)]
    appropriate = [p for p in clothing if _is_appropriate(p, occasion_type)]

    if len(appropriate) < 6:
        appropriate = clothing

    available = [p for p in appropriate if p.id not in exclude_ids]
    if len(available) < 4:
        available = appropriate

    complete = [p for p in available if _is_complete(p)]
    torso = [p for p in available if _is_torso(p) and not _is_complete(p)]
    pierna = [p for p in available if _is_pierna(p) and not _is_complete(p)]

    if not torso:
        torso = available
    if not pierna:
        pierna = available

    return torso, pierna, complete


def _fetch_image_bytes(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read()
    except Exception:
        return None


# Caché en memoria: product.id → bytes. Evita re-descargar en regeneraciones.
_IMAGE_CACHE: dict[int, bytes] = {}
_IMAGE_CACHE_MAX = 300


def _fetch_best_image(product) -> bytes | None:
    """Intenta cada URL del producto hasta obtener una imagen válida (con caché)."""
    cached = _IMAGE_CACHE.get(product.id)
    if cached:
        return cached

    urls = product.image_urls if isinstance(product.image_urls, list) else []
    for url in urls[:3]:  # máximo 3 intentos por producto
        data = _fetch_image_bytes(url)
        if data:
            if len(_IMAGE_CACHE) >= _IMAGE_CACHE_MAX:
                _IMAGE_CACHE.clear()
            _IMAGE_CACHE[product.id] = data
            return data
    return None


def _groq_call_with_retry(client: Groq, **kwargs) -> any:
    """Llama a Groq con retry corto en caso de rate limit (429).
    Esperas cortas para no exceder el timeout HTTP del cliente móvil."""
    for attempt in range(2):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            err = str(e).lower()
            if ("429" in err or "rate" in err or "limit" in err) and attempt == 0:
                time.sleep(2)
            else:
                raise
    raise RuntimeError("Groq rate limit")


# ── Paso 1: Groq elige candidatos por texto ───────────────────────────────────


def _groq_select_candidates(
    torso_pool: list,
    pierna_pool: list,
    complete_pool: list,
    occasion: str,
    gender: str,
    occasion_type: str,
    count: int,
) -> tuple[list, list, list]:
    """
    Groq elige los mejores candidatos por nombre/categoría.
    Retorna (torso_cands, pierna_cands, complete_cands).
    """
    n = MAX_VISION_CANDIDATES
    torso_sample = random.sample(torso_pool, min(n * 2, len(torso_pool)))
    pierna_sample = random.sample(pierna_pool, min(n * 2, len(pierna_pool)))
    complete_sample = (
        random.sample(complete_pool, min(count, len(complete_pool))) if complete_pool else []
    )

    gender_label = "mujer" if gender == "mujer" else "hombre"

    lines = [
        f"Eres experto en moda para {gender_label}.",
        f'El usuario escribió: "{occasion}"',
        "Primero identifica el tipo de ocasión (puede tener typos o ser una frase):",
        "romantic=cita/pareja, formal=trabajo/oficina, gala=boda/graduación,",
        "party=fiesta/noche, sport=gym/deporte, beach=playa, casual=otro.",
        f"Luego selecciona los {n} mejores candidatos de TORSO y {n} de PIERNAS",
        "según la ocasión detectada.",
        "",
        "TORSO disponibles:",
    ]
    for i, p in enumerate(torso_sample):
        cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
        lines.append(f"  [T{i}] {p.name} | {cat}")

    lines.append("\nPIERNAS disponibles:")
    for i, p in enumerate(pierna_sample):
        cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
        lines.append(f"  [P{i}] {p.name} | {cat}")

    if complete_sample:
        lines.append("\nCOMPLETO (vestidos/enterizos — outfit completo solo):")
        for i, p in enumerate(complete_sample):
            cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
            lines.append(f"  [C{i}] {p.name} | {cat}")

    json_example = '{"occasion_type": "<tipo>", "tops": [índices T], "bottoms": [índices P]'
    if complete_sample:
        json_example += ', "completes": [índices C]'
    json_example += "}"
    lines += ["", f"Responde SOLO con JSON: {json_example}"]

    try:
        client = _get_groq()
        resp = _groq_call_with_retry(
            client,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "\n".join(lines)}],
            max_tokens=160,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()

        # Extraer occasion_type detectado por Groq (entiende typos)
        ot_m = re.search(r'"occasion_type"\s*:\s*"(\w+)"', raw)
        if ot_m:
            detected = ot_m.group(1).lower()
            valid = {"romantic", "formal", "gala", "party", "sport", "beach", "casual"}
            if detected in valid:
                occasion_type = detected
                _OCCASION_TYPE_CACHE[occasion.strip().lower()] = occasion_type

        def _parse_indices(pattern, pool):
            m = re.search(pattern, raw)
            if not m:
                return pool[:n]
            # Acepta 1, "1" y "T1" (varía según el modelo)
            indices = [int(d) for d in re.findall(r"\d+", m.group(1))]
            result = [pool[i] for i in indices if i < len(pool)]
            return result[:n] if result else pool[:n]

        tops = _parse_indices(r'"tops"\s*:\s*\[([^\]]+)\]', torso_sample)
        bottoms = _parse_indices(r'"bottoms"\s*:\s*\[([^\]]+)\]', pierna_sample)
        completes = (
            _parse_indices(r'"completes"\s*:\s*\[([^\]]+)\]', complete_sample)
            if complete_sample
            else []
        )

        # Para gala/romántica garantizamos al menos `count` vestidos como candidatos
        if complete_sample and occasion_type in ("gala", "romantic"):
            if len(completes) < count:
                extra = [p for p in complete_sample if p not in completes]
                completes = completes + extra[: count - len(completes)]

        return tops, bottoms, completes

    except Exception:
        logger.exception("Groq fallo seleccionando candidatos, usando muestra aleatoria")
        return torso_sample[:n], pierna_sample[:n], complete_sample[:n] if complete_sample else []


# ── Paso 2: Gemini evalúa visualmente y arma los outfits ─────────────────────


def _gemini_visual_outfits(
    torso_cands: list,
    pierna_cands: list,
    complete_cands: list,
    occasion: str,
    gender: str,
    occasion_type: str,
    count: int,
    allow_repeat: bool = False,
) -> list[dict]:
    """
    Gemini Flash lee las imágenes reales de cada prenda y elige las
    combinaciones que mejor combinan visualmente para la ocasión.
    """
    # Fail-fast si falta GEMINI_API_KEY, antes de descargar imágenes
    _get_gemini()
    gender_label = "mujer" if gender == "mujer" else "hombre"

    # Descargar imágenes
    all_products = torso_cands + pierna_cands + complete_cands

    with ThreadPoolExecutor(max_workers=max(len(all_products), 1)) as ex:
        futures = {ex.submit(_fetch_best_image, p): i for i, p in enumerate(all_products)}
        all_imgs = [None] * len(all_products)
        for future, i in futures.items():
            all_imgs[i] = future.result()

    n_torso = len(torso_cands)
    n_pierna = len(pierna_cands)
    torso_imgs = all_imgs[:n_torso]
    pierna_imgs = all_imgs[n_torso : n_torso + n_pierna]
    complete_imgs = all_imgs[n_torso + n_pierna :]

    # Construir prompt con imágenes intercaladas
    parts = [
        f"Eres un experto en moda para {gender_label}.\n"
        f'El usuario necesita {count} outfits DISTINTOS para: "{occasion}" '
        f"(tipo: {occasion_type}).\n\n"
        "Evalúa colores, patrones y estilo visual para elegir las mejores combinaciones.\n\n"
        "PRENDAS DE TORSO:\n"
    ]

    for i, (p, img) in enumerate(zip(torso_cands, torso_imgs)):
        cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
        parts.append(f"[T{i}] {p.name} | {cat}\n")
        if img:
            parts.append(genai_types.Part.from_bytes(data=img, mime_type="image/jpeg"))
            parts.append("\n")

    parts.append("\nPRENDAS DE PIERNAS:\n")
    for i, (p, img) in enumerate(zip(pierna_cands, pierna_imgs)):
        cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
        parts.append(f"[P{i}] {p.name} | {cat}\n")
        if img:
            parts.append(genai_types.Part.from_bytes(data=img, mime_type="image/jpeg"))
            parts.append("\n")

    if complete_cands:
        parts.append(
            "\nPRENDAS COMPLETAS (vestidos/enterizos — outfit completo solo, "
            "sin necesidad de combinar):\n"
        )
        for i, (p, img) in enumerate(zip(complete_cands, complete_imgs)):
            cat = p.category.split("/")[2] if p.category.count("/") >= 2 else p.category
            parts.append(f"[C{i}] {p.name} | {cat}\n")
            if img:
                parts.append(genai_types.Part.from_bytes(data=img, mime_type="image/jpeg"))
                parts.append("\n")

    # Para gala/romántica pedimos 1 vestido forzado y el AI elige el resto
    forced_dress = None
    ai_count = count
    if occasion_type in ("gala", "romantic") and complete_cands:
        forced_dress = random.choice(complete_cands)
        ai_count = count - 1  # el AI genera los restantes como combinaciones

    repeat_rule = (
        "Puedes repetir una prenda en varios outfits si hay pocas opciones, "
        "pero NUNCA la misma combinación completa."
        if allow_repeat
        else "No repitas prendas entre outfits."
    )
    parts.append(
        f"\nCrea {ai_count} outfits DISTINTOS (combinaciones top+piernas) "
        f"apropiados para la ocasión.\n"
        f"{repeat_rule}\n"
        f'Responde SOLO con JSON: {{"outfits": [{{"top": <n>, "bottom": <n>}}, ...]}}\n'
        f"Exactamente {ai_count} elementos."
    )

    try:
        client = _get_gemini()
        resp = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=parts,
        )
        raw = resp.text.strip()
        logger.debug("Gemini raw response: %s", raw)

        outfits_block = re.search(r'"outfits"\s*:\s*(\[.*?\])', raw, re.DOTALL)
        block = outfits_block.group(1) if outfits_block else raw
        outfit_objects = re.findall(r"\{[^{}]+\}", block)

        outfits = []
        used_ids: set = set()
        used_pairs: set = set()

        # Insertar vestido forzado primero
        if forced_dress:
            used_ids.add(forced_dress.id)
            outfits.append({"top": forced_dress, "bottom": None})

        for obj in outfit_objects[:ai_count]:
            # Acepta "top": 2, "top": "2" y "top": "T2" (varía según el modelo)
            top_m = re.search(r'"top"\s*:\s*"?[A-Za-z]*(\d+)', obj)
            bottom_m = re.search(r'"bottom"\s*:\s*"?[A-Za-z]*(\d+)', obj)
            if top_m and bottom_m:
                ti = int(top_m.group(1))
                bi = int(bottom_m.group(1))
                top = torso_cands[ti if ti < len(torso_cands) else 0]
                bottom = pierna_cands[bi if bi < len(pierna_cands) else 0]

                if allow_repeat:
                    # Solo se bloquea el mismo par completo
                    valid = (top.id, bottom.id) not in used_pairs
                else:
                    valid = top.id not in used_ids and bottom.id not in used_ids

                if valid:
                    used_ids.update([top.id, bottom.id])
                    used_pairs.add((top.id, bottom.id))
                    outfits.append({"top": top, "bottom": bottom})

        if not outfits:
            raise ValueError("No se pudieron parsear outfits")

        return outfits

    except Exception:
        logger.exception("Gemini fallo evaluando outfits, usando fallback")
        outfits = []
        used_ids: set = set()
        used_pairs: set = set()
        if forced_dress:
            used_ids.add(forced_dress.id)
            outfits.append({"top": forced_dress, "bottom": None})

        if allow_repeat:
            # Combinaciones cruzadas sin repetir el mismo par
            for top in torso_cands:
                for bottom in pierna_cands:
                    if len(outfits) >= count:
                        break
                    if (top.id, bottom.id) not in used_pairs:
                        used_pairs.add((top.id, bottom.id))
                        outfits.append({"top": top, "bottom": bottom})
                if len(outfits) >= count:
                    break
        else:
            for i in range(min(ai_count, len(torso_cands), len(pierna_cands))):
                top = torso_cands[i]
                bottom = pierna_cands[i]
                if top.id not in used_ids and bottom.id not in used_ids:
                    used_ids.update([top.id, bottom.id])
                    outfits.append({"top": top, "bottom": bottom})
        return outfits


# ── API pública ───────────────────────────────────────────────────────────────


def get_multiple_recommendations(
    products: list,
    occasion: str,
    gender: str = "hombre",
    exclude_ids: list = None,
    count: int = MAX_OUTFITS,
) -> list[dict]:
    """
    Enfoque híbrido:
      1. Groq (texto) → elige los mejores candidatos por nombre/categoría/ocasión
      2. Gemini Flash (visión) → evalúa imágenes reales y arma los outfits que mejor combinan
    """
    occasion_type = _detect_occasion_type(occasion)
    exclude_set = set(exclude_ids or [])

    torso_pool, pierna_pool, complete_pool = _build_pool(
        products, gender, occasion_type, exclude_set
    )
    if not torso_pool or not pierna_pool:
        return []

    # Paso 1: Groq filtra candidatos por texto
    torso_cands, pierna_cands, complete_cands = _groq_select_candidates(
        torso_pool, pierna_pool, complete_pool, occasion, gender, occasion_type, count
    )

    # Paso 2: Gemini evalúa visualmente y arma los outfits
    return _gemini_visual_outfits(
        torso_cands, pierna_cands, complete_cands, occasion, gender, occasion_type, count
    )


def get_favorites_recommendations(
    products: list,
    occasion: str,
    gender: str = "hombre",
) -> list[dict]:
    """
    Genera outfits usando SOLO las prendas favoritas del usuario.

    Reglas:
      - Requiere al menos 1 prenda de torso y 1 de piernas (si no,
        lanza InsufficientFavoritesError).
      - Los vestidos/enterizos se ignoran (no combinan con nada).
      - Se permite repetir prendas entre outfits (pools pequeños),
        pero nunca la misma combinación completa.
      - Cantidad de outfits = min(3, combinaciones posibles).
    """
    torso = [p for p in products if _is_torso(p) and not _is_complete(p)]
    pierna = [p for p in products if _is_pierna(p) and not _is_complete(p)]

    if not torso or not pierna:
        raise InsufficientFavoritesError(
            "Necesitas al menos una prenda de torso y una de piernas "
            "en tus favoritos para generar outfits"
        )

    count = min(MAX_OUTFITS, len(torso) * len(pierna))
    occasion_type = _detect_occasion_type(occasion)

    # Los favoritos son pocos: van todos directo a Gemini (sin filtro de Groq)
    return _gemini_visual_outfits(
        torso[:MAX_VISION_CANDIDATES],
        pierna[:MAX_VISION_CANDIDATES],
        [],  # sin vestidos en modo favoritos
        occasion,
        gender,
        occasion_type,
        count,
        allow_repeat=True,
    )


def get_recommendations(
    products: list,
    occasion: str,
    gender: str = "hombre",
    exclude_ids: list = None,
) -> dict:
    results = get_multiple_recommendations(products, occasion, gender, exclude_ids, count=1)
    return results[0] if results else {}
