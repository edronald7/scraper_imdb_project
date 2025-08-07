-- ============== consultas SQL avanzadas ===================

-- 1. Obtener las 5 películas con mayor promedio de duración por década:
WITH decade_avg AS (
    SELECT
        (pel.anio / 10) * 10 AS decade,
        pel.titulo,
        AVG(pel.duracion) AS avg_duration,
        ROW_NUMBER() OVER (PARTITION BY (pel.anio / 10) * 10 ORDER BY AVG(pel.duracion) DESC) AS rn
    FROM peliculas pel
    GROUP BY decade, pel.titulo
)
SELECT decade, titulo, avg_duration
FROM decade_avg
WHERE rn <= 5
ORDER BY decade, avg_duration DESC;

-- 2. Calcular la desviación estándar de las calificaciones por año:
SELECT
    anio,
    STDDEV_POP(calificacion) AS std_calificacion
FROM peliculas
GROUP BY anio
HAVING COUNT(*) > 1
ORDER BY anio;

-- 3. Detectar películas con más de un 20% de diferencia entre calificación IMDb y Metascore normalizado
-- El Metascore va de 0 a 100, se normaliza dividiéndolo por 10
SELECT
    titulo,
    anio,
    calificacion AS imdb_rating,
    metascore,
    ABS(calificacion - metascore / 10.0) / ((calificacion + metascore / 10.0) / 2.0) AS diff_ratio
FROM peliculas
WHERE metascore IS NOT NULL
  AND ABS(calificacion - metascore / 10.0) / ((calificacion + metascore / 10.0) / 2.0) > 0.20
ORDER BY diff_ratio DESC;

-- 4. Crear una vista que relacione películas y actores, permitiendo filtrar por actor principal:
CREATE OR REPLACE VIEW vw_peliculas_actores AS
SELECT
    p.id AS pelicula_id,
    p.titulo,
    p.anio,
    a.nombre AS actor_nombre,
    a.posicion_orden
FROM peliculas p
JOIN actores a ON p.id = a.pelicula_id;

-- Consulta para filtrar por actor principal
SELECT * FROM vw_peliculas_actores 
WHERE actor_nombre ILIKE '%Morgan Freeman%' 
    AND posicion_orden = 1;

-- 5. Ejemplo de índice adicional si se realizan búsquedas frecuentes por calificación:
CREATE INDEX IF NOT EXISTS idx_peliculas_calificacion ON peliculas(calificacion);