from core.scraper.adapters.etafashion import EtafashionAdapter
from core.scraper.adapters.modarm import ModarmAdapter
from core.scraper.adapters.test_mock import TestMockAdapter

ADAPTER_MAP = {
    "modarm": ModarmAdapter,
    "etafashion": EtafashionAdapter,
    "test_mock": TestMockAdapter,
}

__all__ = ["ADAPTER_MAP", "EtafashionAdapter", "ModarmAdapter", "TestMockAdapter"]
