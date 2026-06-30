from core.scraper.adapters.modarm import ModarmAdapter


class EtafashionAdapter(ModarmAdapter):
    """Adapter para Etafashion (etafashion.com).

    Etafashion corre sobre la misma plantilla VTEX que Modarm (mismas
    clases CSS para precio, tallas, colores, stock y descripcion), por lo
    que reutiliza toda la logica de parseo de ModarmAdapter y solo cambia
    el dominio y el listado de categorias.
    """

    BASE_URL = "https://www.etafashion.com"

    CATEGORIES = [
        {"name": "Mujer - Vestidos", "path": "/MUJERES/MODA-MUJER/FALDAS-Y-VESTIDOS/c/10105230799"},
        {"name": "Mujer - Blusas", "path": "/MUJERES/MODA-MUJER/BLUSAS/c/10105230599"},
        {
            "name": "Mujer - Pantalones",
            "path": "/MUJERES/MODA-MUJER/JEANS-Y-PANTALONES/JEANS-Y-PANTALONES/c/12736002",
        },
        {"name": "Mujer - Chaquetas", "path": "/MUJERES/MODA-MUJER/BLAZERS-Y-CONJUNTOS/c/10105230499"},
        {"name": "Hombre - Camisas", "path": "/HOMBRES/MODA-ADULTO/CAMISAS/c/10202816399"},
        {"name": "Hombre - Camisetas", "path": "/HOMBRES/MODA-ADULTO/CAMISETAS-Y-POLOS/c/10202816499"},
        {"name": "Hombre - Pantalones", "path": "/HOMBRES/MODA-ADULTO/JEANS-Y-PANTALONES/c/10202816799"},
        {"name": "Hombre - Shorts", "path": "/HOMBRES/MODA-ADULTO/SHORTS-Y-BERMUDAS/c/10202816899"},
        {"name": "Hombre - Chaquetas", "path": "/HOMBRES/MODA-ADULTO/CHAQUETAS-Y-ABRIGOS/c/10202816599"},
    ]
