import os

"""
Configuración del proyecto Scrapy para IMDb.

Se han activado los middlewares y pipelines personalizados para rotar
User‑Agents, rotar proxies (comentado) y almacenar la información en CSV y en
PostgreSQL. 
"""

BOT_NAME = "imdb_scraper"

SPIDER_MODULES = ["imdb_scraper.spiders"]
NEWSPIDER_MODULE = "imdb_scraper.spiders"

ROBOTSTXT_OBEY = False

# Retraso entre peticiones para no saturar el servidor
DOWNLOAD_DELAY = 1.0

# Ajustes de concurrencia
CONCURRENT_REQUESTS = 8

# Directorio de datos para exportar CSV
CSV_EXPORT_DIR = "data"

# Cadena de conexión a PostgreSQL (ajústala en el README)
POSTGRES_CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql://edwin:@localhost:5432/edwin", # Mi base de datos local para pruebas
)

# Configuración de Middlewares
DOWNLOADER_MIDDLEWARES = {
    "imdb_scraper.middlewares.RandomUserAgentMiddleware": 400,
    "imdb_scraper.middlewares.ProxyRotationMiddleware": 410,
    # Mantenemos el RetryMiddleware base de Scrapy para manejar reintentos
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

# Configuración de Pipelines
ITEM_PIPELINES = {
    "imdb_scraper.pipelines.CsvExportPipeline": 300,
    "imdb_scraper.pipelines.PostgresPipeline": 400,
}

# Permitir ciertos códigos de error para reintentar
HTTPERROR_ALLOWED_CODES = [403, 429]

# Ajustes de cabeceras por defecto
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

# Desactivar cookies (puede activarse si es necesario)
COOKIES_ENABLED = False

# Configuración de proxies
PROXIES = []
"""
PROXIES = [
    "http://45.79.178.208:3128",
    "http://178.128.113.118:8080",
    "http://103.147.118.13:8080",
    "socks5://47.251.43.115:1080",
    "socks5://185.199.110.133:1080",
    "socks4://162.240.75.37:1080",
]
"""

DOWNLOADER_MIDDLEWARES = {
    "imdb_scraper.middlewares.RandomUserAgentMiddleware": 400,
    #"imdb_scraper.middlewares.MixedProxyMiddleware": 410,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 420,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 430,
}

RETRY_TIMES = 5
DOWNLOAD_TIMEOUT = 90

# Configuración de Autothrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
