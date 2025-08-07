import json
import re
from typing import List, Optional

import scrapy
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ..items import MovieItem, ActorItem


class ImdbTopBsSpider(scrapy.Spider):
    name = "imdb_top_bs"
    allowed_domains = ["imdb.com"]
    start_urls = ["https://www.imdb.com/chart/top/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,   # para no provocar 429
        "AUTOTHROTTLE_ENABLED": True,
    }

    # Parse lista de peliculas 
    def parse(self, response: scrapy.http.Response):
        soup = BeautifulSoup(response.text, "lxml")

        script_tag = soup.find(
            "script",
            type="application/ld+json",
            string=lambda t: t and "ItemList" in t,
        )
        if not script_tag:
            self.logger.error("No se encontró el bloque ItemList JSON-LD")
            return

        try:
            items = json.loads(script_tag.string)["itemListElement"][:50] # solo top 50
        except json.JSONDecodeError as exc:
            self.logger.error("JSON-LD inválido: %s", exc)
            return

        for elem in items:
            movie = elem["item"]
            meta = {
                "title": movie["name"],
                "rating": float(movie["aggregateRating"]["ratingValue"])
                if "aggregateRating" in movie
                else None,
                "duration_iso": movie.get("duration"),
            }
            # Petición al detalle de la película
            yield response.follow(
                movie["url"],
                callback=self.parse_movie,
                meta=meta,
                headers={"User-Agent": UserAgent().random},
            )

    # Parse detalle de película y actores
    def parse_movie(self, response: scrapy.http.Response):
        meta = response.meta
        soup = BeautifulSoup(response.text, "lxml")

        # funcion estática para extraer año
        year = self._extract_year(soup)

        # metascore (si existe)
        metascore_tag = soup.find("span", class_="metacritic-score-box")
        metascore = int(metascore_tag.text.strip()) if metascore_tag else None

        # función estática para extraer max 3 actores
        actors = self._extract_actors(soup, meta["title"])

        # función estática para convertir ISO 8601 a minutos
        duration_min = self._iso_to_minutes(meta["duration_iso"])

        # generamos MovieItem
        yield MovieItem(
            title=meta["title"],
            year=year,
            rating=meta["rating"],
            duration=duration_min,
            metascore=metascore,
        )

        # generamos los 3 ActorItem
        for actor in actors:
            yield ActorItem(**actor)

    
    @staticmethod
    def _iso_to_minutes(iso_val: Optional[str]) -> Optional[int]:
        """
        Convierte 'PT2H22M' a minutos. Si no hay ISO, devuelve None.
        """
        if not iso_val:
            return None
        hrs = re.search(r"(\d+)H", iso_val)
        mins = re.search(r"(\d+)M", iso_val)
        total = 0
        if hrs:
            total += int(hrs.group(1)) * 60
        if mins:
            total += int(mins.group(1))
        return total or None

    @staticmethod
    def _extract_year(soup: BeautifulSoup) -> Optional[int]:
        """
        Año desde el <li data-testid="title-details-releasedate">.
        """
        li = soup.find("li", attrs={"data-testid": "title-details-releasedate"})
        if not li:
            return None
        text = li.get_text(strip=True)
        m = re.search(r"\d{4}", text)
        return int(m.group(0)) if m else None

    @staticmethod
    def _extract_actors(soup: BeautifulSoup, movie_title: str) -> List[dict]:
        """
        Devuelve lista de dicts con los 3 primeros actores.
        """
        actors = []
        cast_sec = soup.find("section", attrs={"data-testid": "title-cast"})
        if cast_sec:
            for pos, div in enumerate(
                cast_sec.find_all(
                    "div", attrs={"data-testid": "title-cast-item"}
                )[:3],  # solo primeros 3 actores
                start=1,
            ):
                a = div.find(
                    "a", attrs={"data-testid": "title-cast-item__actor"}
                )
                if a:
                    actors.append(
                        {
                            "movie_title": movie_title,
                            "actor_name": a.text.strip(),
                            "position_order": pos,
                        }
                    )
        return actors
