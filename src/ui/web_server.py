import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from ..commands.dispatcher import CommandDispatcher

class WebAPIHandler(BaseHTTPRequestHandler):
    """
    Handler de API minimalista que conecta el Frontend HTML con el Command Dispatcher.
    Usa JSON para la comunicación bidireccional.
    """
    
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Permitir CORS para desarrollo
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """Soporte para pre-flight requests de CORS."""
        logging.debug(f"OPTIONS {self.path}")
        self._set_headers()

    def do_GET(self):
        """
        Soporta peticiones GET. Sirve el index.html en la raíz y configuraciones en /api/config.
        """
        logging.info(f"GET {self.path}")
        if self.path == '/':
            try:
                # Intentamos servir el index.html desde la carpeta ui
                # Ajustamos la ruta para que sea relativa al servidor
                import os
                # Buscamos el archivo index.html en el mismo directorio que este script
                ui_dir = os.path.dirname(__file__)
                index_path = os.path.join(ui_dir, "index.html")
                
                with open(index_path, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                logging.error(f"Error sirviendo index.html: {e}")
                self.send_error(500, f"Error sirviendo index.html: {e}")
        elif self.path == '/api/config':
            # Obtenemos la config desde el system_service vía dispatcher
            res = self.dispatcher.execute("sys.info")
            self._set_headers()
            self.wfile.write(json.dumps(res).encode())
            logging.debug(f"Response /api/config: {res}")
        else:
            logging.warning(f"404 Not Found: {self.path}")
            self.send_error(404, "Endpoint no encontrado")

    def do_POST(self):
        """
        El corazón de la interacción. Recibe un comando y parámetros,
        lo pasa al Dispatcher y retorna el resultado.
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            command = data.get("command")
            params = data.get("params", {})
            user_role = data.get("role", "empleado")
            is_pro = data.get("is_pro", False)

            logging.info(f"POST /api/execute | Command: {command} | Role: {user_role} | Params: {params}")

            if not command:
                logging.warning("POST /api/execute | Missing command in request body")
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "error", "message": "Falta el comando"}).encode())
                return

            # Ejecutar el comando a través del Dispatcher
            result = self.dispatcher.execute(
                command_str=command, 
                params=params, 
                current_user_role=user_role, 
                is_pro=is_pro
            )

            logging.info(f"Result {command}: {result}")
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            logging.exception(f"Error processing POST request: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

class WebServer:
    """
    Servidor web ligero que corre en un hilo separado.
    """
    def __init__(self, dispatcher: CommandDispatcher, port=8888):
        self.dispatcher = dispatcher
        self.port = port
        self.server = None
        self.thread = None

    def _create_handler(self):
        # Creamos un wrapper para inyectar el dispatcher en el handler
        class HandlerWithDispatcher(WebAPIHandler):
            dispatcher = self.dispatcher
        return HandlerWithDispatcher

    def start(self):
        """Inicia el servidor en segundo plano."""
        handler_class = self._create_handler()
        self.server = HTTPServer(("0.0.0.0", self.port), handler_class)
        
        def run():
            logging.info(f"🚀 API Server iniciado en puerto {self.port}")
            self.server.serve_forever()
            
        self.thread = Thread(target=run, daemon=True)
        self.thread.start()
        logging.info("🌐 Servidor API ejecutándose en hilo secundario.")

    def stop(self):
        """Detiene el servidor."""
        if self.server:
            self.server.shutdown()
            self.logger.info("Servidor API detenido.")
