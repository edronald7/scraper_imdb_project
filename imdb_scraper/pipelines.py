"""
Pipelines de Scrapy para manejar la persistencia de los datos.

Este módulo contiene dos pipelines:

* ``CsvExportPipeline``: exporta la información de películas y actores a
  ficheros CSV (`peliculas.csv` y `actores.csv`) en la carpeta `data/`.
* ``PostgresPipeline``: guarda los registros en una base de datos
  PostgreSQL utilizando SQLAlchemy.  Crea las tablas si no existen y
  realiza inserciones con idempotencia básica para evitar duplicados.

Ambos pipelines son configurables los valores en ``settings.py``.
"""

from __future__ import annotations

import csv
import logging
import os
from typing import Dict, Iterable

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert


from .items import MovieItem, ActorItem

logger = logging.getLogger(__name__)


class CsvExportPipeline:
    """Exporta los items a archivos CSV separados para películas y actores."""

    def __init__(self, base_path: str = "data") -> None:
        self.base_path = base_path
        self.movie_file = None
        self.actor_file = None
        self.movie_writer = None
        self.actor_writer = None

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore[override]
        base_path = crawler.settings.get("CSV_EXPORT_DIR", "data")
        return cls(base_path)

    def open_spider(self, spider):  # type: ignore[no-untyped-def]
        os.makedirs(self.base_path, exist_ok=True)
        movie_path = os.path.join(self.base_path, "peliculas.csv")
        actor_path = os.path.join(self.base_path, "actores.csv")
        self.movie_file = open(movie_path, "w", newline="", encoding="utf-8")
        self.actor_file = open(actor_path, "w", newline="", encoding="utf-8")
        self.movie_writer = csv.DictWriter(
            self.movie_file,
            fieldnames=["title", "year", "rating", "duration", "metascore"],
        )
        self.actor_writer = csv.DictWriter(
            self.actor_file,
            fieldnames=["movie_title", "actor_name", "position_order"],
        )
        self.movie_writer.writeheader()
        self.actor_writer.writeheader()

    def close_spider(self, spider):
        if self.movie_file:
            self.movie_file.close()
        if self.actor_file:
            self.actor_file.close()

    def process_item(self, item, spider):
        if isinstance(item, MovieItem) and self.movie_writer:
            self.movie_writer.writerow({
                "title": item.get("title"),
                "year": item.get("year"),
                "rating": item.get("rating"),
                "duration": item.get("duration"),
                "metascore": item.get("metascore"),
            })
        elif isinstance(item, ActorItem) and self.actor_writer:
            self.actor_writer.writerow({
                "movie_title": item.get("movie_title"),
                "actor_name": item.get("actor_name"),
                "position_order": item.get("position_order"),
            })
        return item


class PostgresPipeline:
    """Inserta los items en una base de datos PostgreSQL usando SQLAlchemy."""

    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self.engine: sa.engine.Engine = sa.create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._setup_tables()

    @classmethod
    def from_crawler(cls, crawler): 
        db_url = crawler.settings.get("POSTGRES_CONNECTION_STRING")
        if not db_url:
            raise ValueError(
                "Debe definir POSTGRES_CONNECTION_STRING en settings.py para usar PostgresPipeline"
            )
        return cls(db_url)

    def _setup_tables(self) -> None:
        """Crea las tablas si no existen."""
        metadata = sa.MetaData()
        self.movies_table = sa.Table(
            "peliculas",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("titulo", sa.String(255), nullable=False),
            sa.Column("anio", sa.Integer),
            sa.Column("calificacion", sa.Numeric(3, 1)),
            sa.Column("duracion", sa.Integer),
            sa.Column("metascore", sa.Integer),
            sa.UniqueConstraint("titulo", "anio", name="uq_pelicula_unique"),
            extend_existing=True,
        )
        self.actors_table = sa.Table(
            "actores",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("pelicula_id", sa.Integer, sa.ForeignKey("peliculas.id", ondelete="CASCADE")),
            sa.Column("nombre", sa.String(255), nullable=False),
            sa.Column("posicion_orden", sa.Integer),
            extend_existing=True,
        )
        metadata.create_all(self.engine)

    def open_spider(self, spider):
        self.session: Session = self.SessionLocal()

    def close_spider(self, spider):
        self.session.commit()
        self.session.close()

    def process_item(self, item, spider):
        if isinstance(item, MovieItem):
            self._insert_movie(item)
        elif isinstance(item, ActorItem):
            self._insert_actor(item)
        return item

    def _insert_movie(self, item: MovieItem) -> None:
        # Inserta o actualiza la película. Se usa upsert manual por
        # compatibilidad con PostgreSQL.
        """stmt = sa.insert(self.movies_table).values(
            titulo=item.get("title"),
            anio=item.get("year"),
            calificacion=item.get("rating"),
            duracion=item.get("duration"),
            metascore=item.get("metascore"),
        ).on_conflict_do_nothing(index_elements=["titulo", "anio"])
        """
        stmt = (
            pg_insert(self.movies_table)
            .values(
                titulo=item.get("title"),
                anio=item.get("year"),
                calificacion=item.get("rating"),
                duracion=item.get("duration"),
                metascore=item.get("metascore"),
            )
            .on_conflict_do_nothing(index_elements=["titulo", "anio"])
        )
        try:
            result = self.session.execute(stmt)
            if result.rowcount == 0:
                # La película ya existe; opcionalmente se podría actualizar
                pass
            self.session.flush()
        except Exception as exc:
            logger.exception("Error al insertar película: %s", exc)
            self.session.rollback()

    def _insert_actor(self, item: ActorItem) -> None:
        # Obtiene el ID de la película correspondiente
        movie_title = item.get("movie_title")
        movie = self.session.execute(
            sa.select(self.movies_table.c.id).where(
                self.movies_table.c.titulo == movie_title
            )
        ).first()
        if not movie:
            logger.warning(
                "No se encontró la película '%s' en la base de datos al insertar actor.",
                movie_title,
            )
            return
        pelicula_id = movie[0]
        try:
            self.session.execute(
                sa.insert(self.actors_table).values(
                    pelicula_id=pelicula_id,
                    nombre=item.get("actor_name"),
                    posicion_orden=item.get("position_order"),
                )
            )
            self.session.flush()
        except Exception as exc:
            logger.exception("Error al insertar actor: %s", exc)
            self.session.rollback()