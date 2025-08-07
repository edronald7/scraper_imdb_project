-- Procedimientos almacenados o funciones para carga incremental en PostgreSQL

-- Función para insertar o actualizar una película y devolver su ID
CREATE OR REPLACE FUNCTION upsert_pelicula(
    p_titulo VARCHAR,
    p_anio INTEGER,
    p_calificacion NUMERIC(3,1),
    p_duracion INTEGER,
    p_metascore INTEGER
) RETURNS INTEGER AS $$
DECLARE
    existing_id INTEGER;
BEGIN
    SELECT id INTO existing_id FROM peliculas
    WHERE titulo = p_titulo AND anio = p_anio;
    IF existing_id IS NULL THEN
        INSERT INTO peliculas(titulo, anio, calificacion, duracion, metascore)
        VALUES (p_titulo, p_anio, p_calificacion, p_duracion, p_metascore)
        RETURNING id INTO existing_id;
    ELSE
        UPDATE peliculas
        SET calificacion = p_calificacion,
            duracion    = p_duracion,
            metascore   = p_metascore
        WHERE id = existing_id;
    END IF;
    RETURN existing_id;
END;
$$ LANGUAGE plpgsql;

-- Función para insertar un actor vinculado a una película por título y año
CREATE OR REPLACE FUNCTION insert_actor(
    p_movie_title VARCHAR,
    p_movie_year INTEGER,
    p_actor_name VARCHAR,
    p_position_order INTEGER
) RETURNS VOID AS $$
DECLARE
    movie_id INTEGER;
BEGIN
    SELECT id INTO movie_id FROM peliculas
    WHERE titulo = p_movie_title AND anio = p_movie_year;
    IF movie_id IS NOT NULL THEN
        INSERT INTO actores(pelicula_id, nombre, posicion_orden)
        VALUES (movie_id, p_actor_name, p_position_order);
    END IF;
END;
$$ LANGUAGE plpgsql;