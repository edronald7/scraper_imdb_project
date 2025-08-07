-- SQL DDL
-- Esquema de base de datos para el proyecto IMDb
-- Se usa PostgreSQL como motor de base de datos

CREATE TABLE IF NOT EXISTS peliculas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    anio INTEGER,
    calificacion NUMERIC(3, 1),
    duracion INTEGER,
    metascore INTEGER,
    CONSTRAINT uq_pelicula UNIQUE (titulo, anio)
);

CREATE TABLE IF NOT EXISTS actores (
    id SERIAL PRIMARY KEY,
    pelicula_id INTEGER NOT NULL REFERENCES peliculas(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    posicion_orden INTEGER
);

-- Índices para optimizar consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_peliculas_anio ON peliculas(anio);
CREATE INDEX IF NOT EXISTS idx_actores_pelicula ON actores(pelicula_id);