import re

_PRICE_RE = re.compile(r"\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?")

_CURRENCY_SIGNS = (
    ("€", "EUR"),
    ("£", "GBP"),
    ("s/", "PEN"),
    ("$", "USD"),
)
_CURRENCY_CODES = ("USD", "EUR", "GBP", "PEN", "COP", "MXN", "ARS", "CLP")


def parse_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace("\xa0", " ").strip()
    if not text:
        return None

    match = _PRICE_RE.search(text)
    if not match:
        return None

    raw = match.group(0).replace(" ", "")
    last_dot, last_comma = raw.rfind("."), raw.rfind(",")
    separator = max(last_dot, last_comma)

    try:
        if separator == -1:
            return float(raw)
        # El último . o , solo es decimal si deja 1-2 dígitos a su derecha;
        # de lo contrario es separador de miles ("12.999" -> 12999).
        decimals = raw[separator + 1 :]
        integer = re.sub(r"[.,]", "", raw[:separator])
        if len(decimals) <= 2:
            return float(f"{integer}.{decimals}")
        return float(integer + decimals)
    except ValueError:
        return None


def detect_currency(value, default=""):
    text = str(value or "")
    upper = text.upper()
    for code in _CURRENCY_CODES:
        if code in upper:
            return code
    lower = text.lower()
    for sign, code in _CURRENCY_SIGNS:
        if sign in lower:
            return code
    return default
