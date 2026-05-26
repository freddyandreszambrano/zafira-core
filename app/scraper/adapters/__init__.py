from app.scraper.adapters.modarm import ModarmAdapter

# Registry de adaptadores por tienda
ADAPTER_MAP = {
    'modarm': ModarmAdapter,
    # v2: agregar más tiendas (zara, shein, etc.)
}

__all__ = ['ADAPTER_MAP', 'ModarmAdapter']
