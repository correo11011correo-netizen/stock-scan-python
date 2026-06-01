import json
import logging
import os
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
        # Permitir CORS de forma más permisiva para facilitar el acceso vía túnel
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        """Soporte para pre-flight requests de CORS."""
        logging.info(f"OPTIONS request: {self.path} from {self.address_string()}")
        self._set_headers()

    def do_GET(self):
        """
        Soporta peticiones GET. Sirve el index.html en la raíz, configuraciones en /api/config, 
        y archivos estáticos desde la carpeta UI.
        """
        logging.info(f"GET {self.path}")
        ui_dir = os.path.dirname(__file__)
        
        # Mapeo de ruta a archivo
        if self.path == '/':
            file_path = os.path.join(ui_dir, "index.html")
        else:
            # Eliminar el leading slash
            rel_path = self.path.lstrip('/')
            
            # Si la ruta comienza con 'src/ui/', quitarlo para que apunte a la raíz de la UI
            if rel_path.startswith('src/ui/'):
                rel_path = rel_path.replace('src/ui/', '', 1)
                
            file_path = os.path.join(ui_dir, rel_path)

        # Verificar si el archivo existe
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                from pathlib import Path
                logging.info(f"Intentando abrir archivo: {file_path}")
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                
                content = Path(file_path).read_bytes()
                
                self.send_response(200)
                self.send_header('Content-type', mime_type or 'application/octet-stream')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                logging.error(f"Error sirviendo archivo {file_path}: {e}")
                self.send_error(500, f"Error interno: {e}")
                return

        # Endpoints de API
        if self.path == '/api/config':
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
    def __init__(self, dispatcher: CommandDispatcher, port=8889):
        self.dispatcher = dispatcher
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Inicia el servidor en 0.0.0.0 para compatibilidad con túneles."""
        # Configurar el handler directamente
        WebAPIHandler.dispatcher = self.dispatcher
        
        # Iniciar en 0.0.0.0 para asegurar visibilidad al túnel
        self.server = HTTPServer(("0.0.0.0", self.port), WebAPIHandler)
        self.server.allow_reuse_address = True
        
        def run():
            logging.info(f"🚀 API Server iniciado en puerto {self.port}")
            self.server.serve_forever()
            
        self.thread = Thread(target=run, daemon=True)
        self.thread.start()
        logging.info(f"🌐 Servidor API ejecutándose en puerto {self.port}.")

    def stop(self):
        """Detiene el servidor."""
        if self.server:
            self.server.shutdown()
            logging.info("Servidor API detenido.")
