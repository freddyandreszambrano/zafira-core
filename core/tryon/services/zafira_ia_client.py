import requests
from django.conf import settings


class ZafiraIaError(Exception):
    def __init__(self, message, code=""):
        self.code = code
        super().__init__(message)


class ZafiraIaUnavailable(ZafiraIaError):
    """Error de red o 5xx: la tarea puede reintentar."""


class ZafiraIaRejected(ZafiraIaError):
    """4xx o configuración inválida: no reintentar."""


class ZafiraIaClient:
    def __init__(self, base_url=None, timeout=None):
        self.base_url = (base_url or settings.ZAFIRA_IA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.ZAFIRA_IA_TIMEOUT_SECONDS

    def try_on(self, *, external_ref, person_image_url, garment_image_url, garment_type):
        payload = {
            "external_ref": external_ref,
            "person_image_url": person_image_url,
            "garment_image_url": garment_image_url,
            "garment_type": garment_type,
            "params": {},
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/tryon",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ZafiraIaUnavailable(f"ZAFIRA-IA no disponible: {exc}") from exc

        code, detail = self._error_fields(response)

        if response.status_code >= 500:
            raise ZafiraIaUnavailable(
                f"ZAFIRA-IA respondió {response.status_code}: {detail}",
                code=code or "IA_UNAVAILABLE",
            )
        if response.status_code != 200:
            raise ZafiraIaRejected(
                f"ZAFIRA-IA rechazó la solicitud ({response.status_code}): {detail}",
                code=code or "IA_REJECTED",
            )
        return response.json()

    @staticmethod
    def _error_fields(response):
        try:
            body = response.json()
        except ValueError:
            return "", ""
        return body.get("code", ""), body.get("detail", "")
