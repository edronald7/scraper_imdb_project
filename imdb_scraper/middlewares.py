"""
Middlewares personalizados para Scrapy
--------------------------------------

* RandomUserAgentMiddleware: asigna un User-Agent aleatorio por petición.
* MixedProxyMiddleware: rota proxies HTTP/SOCKS (4 y 5) tomados de settings.PROXIES
  y reintenta si una IP es bloqueada.  Registra la IP pública cada vez que cambia
  de proxy para dejar evidencia de la rotación.
  Para usar un proxy se recomienda usar un servicio de proxies pago. 
  OJO: Para esta prueba se implementa pero no se habilita por defecto.
"""

from __future__ import annotations

import logging
import random
from typing import List, Optional

import requests
from fake_useragent import UserAgent
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from twisted.internet.error import TCPTimedOutError, TimeoutError, ConnectionRefusedError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User-Agent aleatorio
# ---------------------------------------------------------------------------

class RandomUserAgentMiddleware:
    """Asigna un User-Agent aleatorio a cada petición."""

    def __init__(self) -> None:
        try:
            self.ua = UserAgent()
        except Exception as exc:
            logger.warning("fake_useragent falló (%s); usando lista básica", exc)
            self.ua = None
            self.fallback_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            ]

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        ua = self.ua.random if self.ua else random.choice(self.fallback_agents)
        request.headers.setdefault("User-Agent", ua)
        return None


# -------------------------------------------------------------------
# Rotación de proxies (HTTP / SOCKS4 / SOCKS5)
# -------------------------------------------------------------------

class MixedProxyMiddleware(RetryMiddleware):
    """
    Rota proxies tomados de settings.PROXIES y reintenta cuando se recibe
    429/403 o se produce un timeout.  Registra la IP pública al cambiar de IP.
    """

    def __init__(self, settings): 
        super().__init__(settings)
        self.proxies: List[str] = settings.getlist("PROXIES")
        if not self.proxies:
            logger.warning("PROXIES está vacío: el scraper se ejecutará sin proxy.")
        self.current_proxy: Optional[str] = None

    @classmethod
    def from_crawler(cls, crawler): 
        return cls(crawler.settings)

    def _choose_proxy(self) -> Optional[str]:
        return random.choice(self.proxies) if self.proxies else None

    def _set_proxy(self, request) -> None:
        proxy = self._choose_proxy()
        if proxy:
            print("Asignando proxy:", proxy)
            request.meta["proxy"] = proxy
            if proxy != self.current_proxy:
                self.current_proxy = proxy
                # obtener IP pública (opcional)
                try:
                    ip = requests.get("https://api.ipify.org", timeout=5).text
                    logger.info("Nueva IP pública %s usando proxy %s", ip, proxy)
                except Exception:
                    logger.info("Proxy cambiado a %s", proxy)

    def process_request(self, request, spider):
        if "proxy" not in request.meta:
            self._set_proxy(request)
        return None

    def process_exception(self, request, exception, spider): 
        if isinstance(exception, (TimeoutError, TCPTimedOutError, ConnectionRefusedError)):
            proxy = request.meta.get("proxy")
            logger.warning("El proxy %s falló (%s); intentando con otro", proxy, exception)
            # intentamos con otro proxy (no marcamos el actual, pero podría añadirse una lista negra)
            self._set_proxy(request)
            return request
        return None

    def process_response(self, request, response, spider): 
        if response.status in (403, 429):
            reason = f"bloqueado con código {response.status}"
            return self._retry(request, reason, spider) or response
        return response
