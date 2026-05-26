from app.scraper.adapters.modarm import ModarmAdapter
from app.scraper.adapters.test_mock import TestMockAdapter

# Registry de adaptadores por tienda
ADAPTER_MAP = {
    'modarm': ModarmAdapter,
    'test_mock': TestMockAdapter,
    # v2: agregar más tiendas (zara, shein, etc.)
}

__all__ = ['ADAPTER_MAP', 'ModarmAdapter', 'TestMockAdapter']
