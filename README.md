# Scraper IMDB con Python y PostgreSQL

Este proyecto es una solución escrita en python, usando scrapy y postgresql,  
que permite extraer datos de las 50 primeras películas del Top 250 de IMDB,
persistirlos en una base de datos **PostgreSQL**, exportarlos a CSV y
describir el enfoque basado en Scrapy con herramientas como Selenium o
Playwright.

## Estructura del repositorio

```
scraper_imdb_project/
├── imdb_scraper/              # Código fuente del scraper
│   ├── items.py               # Definición de Items de Scrapy
│   ├── middlewares.py         # Middlewares: rotación de User‑Agents y proxies
│   ├── pipelines.py           # Pipelines: exportación a CSV y PostgreSQL
│   ├── settings.py            # Configuración global de Scrapy
│   ├── factories.py           # Patrón Factory para instanciar spiders
│   └── spiders/
│       └── imdb_top_bs.py     # Spider principal que recorre Top 50 y detalles
├── sql/
│   ├── 1_schema.sql           # DDL para crear tablas e índices en PostgreSQL
│   ├── 2_procedures.sql       # Procedimientos almacenados opcionales
│   └── 3_analysis_queries.sql # Consultas analíticas solicitadas
├── data/                      # Datos generados
│   ├── actores.csv            # Archivo CSV generado por el scraper para actores
│   └── peliculas.csv          # Archivo CSV generado por el scraper para peliculas
├── requirements.txt           # Dependencias de Python
├── scrapy.cfg                 # Archivo de configuracion de scrapy
└── README.md                  # Este documento
```

## Requisitos previos

1. **Python 3.9+**
2. **PostgreSQL** en ejecución. Crea una base de datos llamada
   `imdb_db` o la de tu preferencia.
3. **Instalar las dependencias**:

```bash
pip install -r requirements.txt
```

> **Nota:** Si `fake_useragent` falla al inicializar (por ejemplo, sin
> conexión a internet), el middleware usa una lista corta de User‑Agents
> comunes.

## Configuración de la base de datos

1. Ejecuta el script de esquema para crear las tablas e índices:

```bash
psql -U postgres -d imdb_db -f sql/1_schema.sql
```

2. (Opcional) Crea las funciones almacenadas para cargas incrementales:

```bash
psql -U postgres -d imdb_db -f sql/2_procedures.sql
```

3. Ajusta la cadena de conexión a PostgreSQL en `imdb_scraper/settings.py`:

```python
# Solo para pruebas locales, la base de datos y usuario es postgres y sin contraseña
# Se recomienda manejar credenciales a nivel variables de entorno como por ejemplo `DATABASE_URL`.
POSTGRES_CONNECTION_STRING = "postgresql://postgres:@localhost:5432/postgres"
```


## Configuración de proxies

El scraper incluye un middleware que rota proxies para minimizar
bloqueos. Pero para fines de esta prueba se desactiva/comenta dado que no se cuenta con un proxy de pago.

**IMPORTANTE:** los proxies gratuitos pueden dejar de funcionar en
cualquier momento, por esta razon se desactiva para esta prueba.  
Para añadir debe agregar a la lista PROXIES = [] que se encuentra en el archivo `settings.py` con proxies propios o terceros de pago.  El middleware registrará en los logs la IP pública utilizada en cada cambio de proxy.

## Ejecución del scraper

Para ejecutar el spider que recorre las primeras 50 películas del Top 250:

```bash
cd scraper_imdb_project
scrapy crawl imdb_top_bs -s LOG_LEVEL=INFO

```

El spider hará lo siguiente:

1. Visitará `https://www.imdb.com/chart/top/` y extraerá las primeras 50 entradas.
2. Para cada película, accederá a la página de detalle para obtener
   duración, año, metascore y 3 actores principales.
3. Por cada película generará un `MovieItem` y tres `ActorItem` para
   los actores principales.
4. El pipeline `CsvExportPipeline` guardará los datos en
   `data/peliculas.csv` y `data/actores.csv`.
5. El pipeline `PostgresPipeline` insertará los registros en las tablas
   `peliculas` y `actores` de PostgreSQL utilizando idempotencia.

### Variables de entorno útiles

- `DATABASE_URL`: URI de conexión a PostgreSQL.  Si está definida,
  `settings.py` la usará automáticamente.

## Consultas analíticas

Las consultas solicitadas se encuentran en `sql/3_analysis_queries.sql`.  Por
ejemplo, para obtener las 5 películas con mayor duración promedio por
década se emplea una función de ventana `ROW_NUMBER()` y la consulta:

```sql
WITH decade_avg AS (
    SELECT (anio / 10) * 10 AS decade,
           titulo,
           AVG(duracion) AS avg_duration,
           ROW_NUMBER() OVER (PARTITION BY (anio / 10) * 10 ORDER BY AVG(duracion) DESC) AS rn
    FROM peliculas
    GROUP BY decade, titulo
)
SELECT decade, titulo, avg_duration
FROM decade_avg
WHERE rn <= 5
ORDER BY decade, avg_duration DESC;
```

En el fichero se puede ver otras consultas como la desviación estándar
de calificaciones, detección de discrepancias entre IMDb y Metascore y
la vista `vw_peliculas_actores`.

## Comparación con Selenium/Playwright

El spider de este proyecto utiliza **Scrapy** y **Requests/BeautifulSoup**
porque la web de imdb.com es mayormente HTML estático; esto permite concurrencia
alta y bajo consumo de recursos.  Si el sitio tuviera contenido cargado
dinámicamente por JavaScript o necesitara interacción compleja, se podría
optar por **Selenium** o **Playwright**.  con algunas de las siguientes consideraciones:

- **Configuración del navegador**: Con Selenium/Playwright se puede
  ejecutar en modo headless, modificar headers, desactivar la detección
  de `webdriver` e inyectar scripts para evitar bloqueos.
- **Selectores dinámicos**: Se utilizan esperas explícitas y selectores
  robustos (`locator.wait_for()` en Playwright) para esperar la carga
  de elementos dinámicos.
- **Captchas y rendering de JS**: Estas herramientas permiten resolver
  captchas manualmente o mediante servicios externos.  Para páginas
  renderizadas totalmente por JS son casi imprescindibles.
  Otras opciones para romper captchas clasicos se puede usar modelos CNN y OCR.
- **Concurrencia**: Playwright soporta múltiples contextos/navegadores
  simultáneos; sin embargo, consume más memoria y CPU que Scrapy.  Para
  scraping masivo sin necesidad de JS, Scrapy sigue siendo más eficiente.


## Licencia

Este proyecto se proporciona con fines demostrativos o educativos y de evaluación.  Su uso
en producción debe respetar los términos de servicio de IMDb y las leyes
vigentes sobre scraping y propiedad intelectual.