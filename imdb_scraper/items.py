"""
Definición de Items para el proyecto IMDb.
"""

import scrapy


class MovieItem(scrapy.Item):
    """Representa los datos de una película extraída de IMDb."""

    title: str = scrapy.Field()
    year: int = scrapy.Field()
    rating: float = scrapy.Field()
    duration: int = scrapy.Field()
    metascore: int = scrapy.Field()


class ActorItem(scrapy.Item):
    """Representa un actor asociado a una película."""

    movie_title: str = scrapy.Field()
    actor_name: str = scrapy.Field()
    position_order: int = scrapy.Field()