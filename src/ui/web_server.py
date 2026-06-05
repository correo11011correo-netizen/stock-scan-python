import json
import logging
import os
import mimetypes
import email
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from datetime import datetime
from ..commands.dispatcher import CommandDispatcher

class WebAPIHandler(BaseHTTPRequestHandler):
    """
    Handler de API y Servidor de Archivos Estáticos.
    Conecta el Frontend HTML con el Command Dispatcher y sirve la UI.
    Soporta multi-tenancy mediante la resolución dinámica de bases de datos.
    """
    
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def log_message(self, format, *args):
        """Override to prevent OSError [Errno 5] when running in background."""
        logging.info(format % args)

    def _json_response(self, data, status=200):
        """Estandariza todas las respuestas JSON de la API."""
        response = {
            "timestamp": datetime.now().isoformat(),
            "payload": data
        }
        self._set_headers(status)
        self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        logging.info(f"GET {self.path}")
        ui_dir = os.path.dirname(__file__)
        
        if self.path == '/':
            file_path = os.path.join(ui_dir, "index.html")
        else:
            # Soporte para descarga de archivos CSV
            if self.path.startswith('/download/') and self.path.endswith('.csv'):
                # El path viene como /download/home/adrian/...
                abs_path = self.path.replace('/download/', '', 1)
                if os.path.exists(abs_path) and os.path.isfile(abs_path):
                    try:
                        content = Path(abs_path).read_bytes()
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/csv')
                        self.send_header('Content-Disposition', f'attachment; filename={os.path.basename(abs_path)}')
                        self.send_header('Content-Length', len(content))
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        logging.error(f"Error sirviendo CSV {abs_path}: {e}")
                        self.send_error(500, f"Error interno: {e}")
                        return
            
            rel_path = self.path.lstrip('/')
            if rel_path.startswith('src/ui/'):
                rel_path = rel_path.replace('src/ui/', '', 1)
            file_path = os.path.join(ui_dir, rel_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
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

        if self.path == '/api/config':
            res = self.dispatcher.execute("sys.info")
            return self._json_response(res)
        
        if self.path == '/api/health':
            return self._json_response({"status": "healthy", "server": "StockScan-API", "version": "2.0"})
        
        self.send_error(404, "Endpoint o archivo no encontrado")

    def do_POST(self):
        # Manejar la carga de archivos (Upload)
        if self.path == '/api/upload':
            try:
                content_type = self.headers.get('Content-Type')
                if not content_type or 'multipart/form-data' not in content_type:
                    return self._json_response({"status": "error", "message": "Content-Type debe ser multipart/form-data"}, 400)

                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                
                # Simular un mensaje de correo para que el parser de email pueda procesarlo
                msg = email.message_from_bytes(
                    f"Content-Type: {content_type}\r\n\r\n".encode() + body,
                    strict=False
                )
                
                file_item = None
                for part in msg.get_payload():
                    if part.get_filename():
                        file_item = part
                        break
                
                if not file_item:
                    return self._json_response({"status": "error", "message": "No se recibió ningún archivo válido."}, 400)
                
                filename_orig = file_item.get_filename()
                content = file_item.get_payload(decode=True)
                
                # Crear carpeta de uploads relativa a la raíz del proyecto
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                upload_dir = os.path.join(base_dir, "data", "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                
                # Guardar el archivo con un nombre único para evitar colisiones
                filename = f"upload_{int(datetime.now().timestamp())}_{filename_orig}"
                full_path = os.path.join(upload_dir, filename)
                
                with open(full_path, 'wb') as f:
                    f.write(content)
                
                logging.info(f"Archivo subido exitosamente: {full_path}")
                return self._json_response({"status": "success", "path": full_path})
            except Exception as e:
                logging.exception(f"Error en upload: {e}")
                return self._json_response({"status": "error", "message": str(e)}, 500)

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            command = data.get("command")
            params = data.get("params", {})
            
            # --- FLUJO DE AUTENTICACIÓN Y MULTI-TENANCY ---
            
            # 1. Manejar endpoints especiales (Login / Registro)
            if command == "auth.login":
                # Extraer credenciales ya sea de la raíz o de params
                username = data.get("username") or params.get("username")
                password = data.get("password") or params.get("password")
                res = self.dispatcher.execute("auth.login", {"username": username, "password": password})
                return self._json_response(res)
            
            if command == "auth.register_owner":
                # Extraer datos ya sea de la raíz o de params
                username = data.get("username") or params.get("username")
                password = data.get("password") or params.get("password")
                biz_name = data.get("business_name") or params.get("business_name")
                res = self.dispatcher.execute("auth.register_owner", {
                    "username": username, 
                    "password": password, 
                    "business_name": biz_name
                })
                return self._json_response(res)

            # 2. Validar Token de Sesión para todos los demás comandos
            token = self.headers.get('Authorization')
            user_session = self.auth_service.validate_session(token)
            
            if not user_session:
                return self._json_response({"status": "error", "message": "Sesión no válida o expirada. Por favor, inicie sesión."}, 401)

            # --- EXCEPCIÓN PARA COMANDOS GLOBALES DE ADMINISTRACIÓN ---
            if command.startswith('sys.admin.'):
                # Los comandos de administración global usan el dispatcher maestro del servidor
                # ya que no dependen de una base de datos de tenant específica.
                result = self.dispatcher.execute(
                    command, 
                    params, 
                    current_user_role=user_session["role"], 
                    is_pro=True, # El Master Admin siempre tiene acceso PRO
                    user_id=user_session["id"] # Crucial para el God Mode
                )
                return self._json_response(result)

            # 3. Resolución Dinámica de la Base de Datos del Tenant
            tenant_id = user_session["tenant_id"]
            schema_name = self.auth_service.resolve_tenant_db(tenant_id)
            
            if not schema_name:
                return self._json_response({"status": "error", "message": "No se pudo localizar la base de datos del negocio."}, 500)

            # Determinar estado PRO basándose en la sesión/tenant, NO en el cliente
            # El plan se almacena en la sesión al hacer login
            is_pro_user = (user_session.get("plan") == "PRO" or user_session.get("plan") == "ENTERPRISE")

            # 4. Inyección de Dependencias por Petición (Aislamiento Total)
            from ..core.database import DatabaseManager
            from ..core.stock_service import StockService
            from ..core.sales_service import SalesService
            from ..core.system_service import SystemService
            from ..commands.dispatcher import CommandDispatcher

            tenant_db = DatabaseManager(schema_name=schema_name)
            tenant_stock = StockService(tenant_db)
            tenant_sales = SalesService(tenant_db, tenant_stock)
            tenant_sys = SystemService(tenant_db)
            
            tenant_dispatcher = CommandDispatcher(
                db=tenant_db, 
                stock_service=tenant_stock, 
                sales_service=tenant_sales, 
                system_service=tenant_sys,
                auth_service=self.auth_service
            )

            # 5. Ejecución del Comando con contexto de usuario
            result = tenant_dispatcher.execute(
                command, 
                params, 
                current_user_role=user_session["role"], 
                is_pro=is_pro_user,
                user_permissions=self.auth_service.get_user_permissions(user_session["id"], tenant_id),
                user_id=user_session["id"]
            )
            
            return self._json_response(result)
            
        except Exception as e:
            logging.exception(f"Error processing POST request: {e}")
            return self._json_response({"status": "error", "message": str(e)}, 500)

class WebServer:
    def __init__(self, dispatcher: CommandDispatcher, auth_service, port=8888):
        self.dispatcher = dispatcher
        self.auth_service = auth_service
        self.port = port
        self.server = None

    def _create_handler(self):
        class HandlerWithContext(WebAPIHandler):
            dispatcher = self.dispatcher
            auth_service = self.auth_service
        return HandlerWithContext

    def start(self):
        handler_class = self._create_handler()
        self.server = HTTPServer(("0.0.0.0", self.port), handler_class)
        logging.info(f"🌐 Servidor API iniciado en puerto {self.port}")
        self.server.serve_forever()
        logging.info(f"🌐 Servidor API iniciado en puerto {self.port}")

    def stop(self):
        if self.server: self.server.shutdown()

