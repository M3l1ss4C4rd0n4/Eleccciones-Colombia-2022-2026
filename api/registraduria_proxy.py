"""
api/registraduria_proxy.py
===========================
Serverless Function de Vercel (Python) que actúa como proxy hacia la API
de la Registraduría, eliminando el bloqueo CORS para el navegador.

Endpoint público:   /api/registraduria_proxy?path=ACT/CA/00
Fuente real:        https://resultados.registraduria.gov.co/json/{path}.json

Variables de entorno opcionales:
  REGISTRADURIA_BASE_URL  — sobreescribe la URL base (default: ver abajo)
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urljoin
import json
import urllib.request
import urllib.error

# URL base de la Registraduría — sin barra final
REGISTRADURIA_BASE = "https://resultados.registraduria.gov.co/json"

# Rutas permitidas (whitelist para prevenir SSRF)
ALLOWED_PATH_PATTERNS = ("ACT/", "INF/", "PRE/", "CA/", "SE/", "00")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Cache-Control": "no-cache, max-age=30",
}


def _is_safe_path(path: str) -> bool:
    """Valida que el path solo incluya segmentos alfanuméricos seguros."""
    import re
    # Solo letras, números, /, guiones y guiones bajos
    return bool(re.match(r'^[A-Za-z0-9/_\-]{1,100}$', path))


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Responde a preflight CORS."""
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Parámetro 'path' define qué endpoint de la Registraduría consultar
        # Ejemplo: /api/registraduria_proxy?path=ACT/CA/00
        raw_path = params.get("path", ["ACT/CA/00"])[0]

        # ── Validación de seguridad (prevención de SSRF) ──────────────────────
        if not _is_safe_path(raw_path):
            self._error(400, "Ruta no permitida")
            return

        target_url = f"{REGISTRADURIA_BASE}/{raw_path}.json"

        try:
            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
                    "Referer": "https://resultados.registraduria.gov.co/",
                    "Origin": "https://resultados.registraduria.gov.co",
                },
            )
            import ssl
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = resp.read()
                content_type = resp.headers.get("Content-Type", "application/json")

        except urllib.error.HTTPError as e:
            self._error(e.code, f"Error Registraduría: {e.reason}")
            return
        except urllib.error.URLError as e:
            self._error(502, f"No se pudo conectar a la Registraduría: {e.reason}")
            return
        except Exception as e:
            self._error(500, f"Error interno del proxy: {str(e)}")
            return

        # ── Respuesta exitosa ─────────────────────────────────────────────────
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _error(self, code: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Silencia el log por defecto de BaseHTTPRequestHandler en producción
        pass
