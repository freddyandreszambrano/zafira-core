from datetime import datetime, timezone
from typing import List, Optional


def normalize_price(price_str: str) -> Optional[float]:
    """
    Normalize price string to float.

    Accepts formats like: '$12.999', '12,99', '$ 45.50', etc.
    Returns None if conversion fails.
    """
    if not isinstance(price_str, str):
        return None

    try:
        price_str = price_str.strip()

        cleaned = "".join(char for char in price_str if char.isdigit() or char in ".,")

        if not cleaned:
            return None

        cleaned = cleaned.replace(",", ".")

        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def extract_category_path(breadcrumb: List[str]) -> str:
    """
    Convert breadcrumb list to category path string.

    Example: ['Hombres', 'Moda Hombre', 'Camisas'] -> 'Hombres/Moda Hombre/Camisas'
    """
    if not breadcrumb:
        return ""

    return "/".join(str(item).strip() for item in breadcrumb if item)


def extract_images(container) -> List[str]:
    """
    Extract image URLs from BeautifulSoup container.

    Finds all img tags with src or data-src attributes.
    Skips data:* URIs and removes duplicates while maintaining order.
    """
    images = []
    seen = set()

    if container is None:
        return images

    img_tags = container.find_all("img")

    for img in img_tags:
        url = img.get("src") or img.get("data-src")

        if url and not url.startswith("data:") and url not in seen:
            images.append(url)
            seen.add(url)

    return images


def now_iso() -> str:
    """
    Return current UTC timestamp in ISO 8601 format.

    Example: '2026-05-26T12:30:45.123456+00:00'
    """
    return datetime.now(timezone.utc).isoformat()
