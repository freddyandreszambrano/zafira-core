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
