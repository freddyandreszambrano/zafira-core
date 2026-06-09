from core.scraper.adapters.modarm import ModarmAdapter
from core.scraper.adapters.test_mock import TestMockAdapter

ADAPTER_MAP = {
    'modarm': ModarmAdapter,
    'test_mock': TestMockAdapter,
}

__all__ = ['ADAPTER_MAP', 'ModarmAdapter', 'TestMockAdapter']
