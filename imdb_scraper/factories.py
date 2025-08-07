"""
Esta parte es para instanciar spiders y componentes bajo demanda.

El uso de un patrón Factory permite centralizar la lógica de creación de
objetos complejos, como spiders o pipelines, y facilita la extensión a
futuras fuentes de datos sin modificar el código cliente.
"""

from __future__ import annotations

from typing import Any, Type


class SpiderFactory:
    """Crea instancias de spiders según un nombre registrado."""

    _registry = {
        "imdb_top_bs": "imdb_scraper.spiders.imdb_top_bs.ImdbTopBsSpider",
    }

    @classmethod
    def create(cls, name: str, **kwargs: Any):
        """Devuelve una instancia del spider indicado.

        Args:
            name: nombre del spider registrado.
            kwargs: argumentos opcionales que se pasan al constructor.

        Raises:
            ValueError: si el nombre no está registrado.
        """
        if name not in cls._registry:
            raise ValueError(f"Spider '{name}' no está registrado en la fábrica")
        module_path, class_name = cls._registry[name].rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        spider_cls: Type = getattr(module, class_name)
        return spider_cls(**kwargs)