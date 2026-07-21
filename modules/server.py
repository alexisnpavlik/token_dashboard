"""Servidor HTTP local ligero para servir la API JSON y los archivos del Dashboard en tiempo real."""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from modules.aggregator import get_aggregated_data

logger = logging.getLogger(__name__)

PORT = 48123
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")


class TokenBarHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs HTTP ruidosos en la terminal
        pass

    def do_GET(self):
        if self.path == "/api/data":
            try:
                data = get_aggregated_data(max_days=90)
                
                payload = json.dumps(
                    data,
                    default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o)
                ).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                logger.error("Error sirviendo API JSON: %s", e)
                self.send_error(500, str(e))
            return


        # Servir archivos estáticos del dashboard (HTML, CSS, JS)
        rel_path = self.path.lstrip("/")
        if not rel_path or rel_path == "/":
            rel_path = "index.html"

        file_path = os.path.join(WEB_DIR, rel_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type = "text/html"
            if file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".js"):
                content_type = "application/javascript"
            elif file_path.endswith(".svg"):
                content_type = "image/svg+xml"
            elif file_path.endswith(".png"):
                content_type = "image/png"

            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File Not Found")


_server_thread = None


def start_server_in_background(port: int = PORT):
    global _server_thread
    if _server_thread and _server_thread.is_alive():
        return

    def run():
        try:
            server = HTTPServer(("127.0.0.1", port), TokenBarHandler)
            logger.info("Servidor de TokenBar corriendo en http://127.0.0.1:%d", port)
            server.serve_forever()
        except OSError as oe:
            if oe.errno == 98 or "Address already in use" in str(oe):
                logger.info("Servidor TokenBar ya activo en puerto %d", port)
            else:
                logger.error("Error iniciando servidor TokenBar: %s", oe)
        except Exception as e:
            logger.error("Error iniciando servidor TokenBar: %s", e)


    _server_thread = Thread(target=run, daemon=True)
    _server_thread.start()
