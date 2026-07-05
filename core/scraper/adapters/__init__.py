from core.scraper.adapters.etafashion import EtafashionAdapter
from core.scraper.adapters.generic import GenericAdapter
from core.scraper.adapters.modarm import ModarmAdapter
from core.scraper.adapters.test_mock import TestMockAdapter

GENERIC_STORE = "generic"

# El genérico va al final: infer_store_from_url recorre en orden y los
# adaptadores con selectores propios deben ganar sobre el multi-estrategia.
ADAPTER_MAP = {
    "modarm": ModarmAdapter,
    "etafashion": EtafashionAdapter,
    "test_mock": TestMockAdapter,
    GENERIC_STORE: GenericAdapter,
}

__all__ = [
    "ADAPTER_MAP",
    "GENERIC_STORE",
    "EtafashionAdapter",
    "GenericAdapter",
    "ModarmAdapter",
    "TestMockAdapter",
]
