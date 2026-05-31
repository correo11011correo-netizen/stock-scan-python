from typing import Dict, Any, Callable
import logging
from ..core.database import DatabaseManager
from ..core.stock_service import StockService
from ..core.sales_service import SalesService
from ..core.system_service import SystemService

class CommandDispatcher:
    """
    Orquestador central del sistema.
    Traduce comandos de texto en acciones de servicio, validando permisos y licencias.
    """
    
    def __init__(self, db: DatabaseManager, stock_service: StockService, sales_service: SalesService, system_service: SystemService):
        self.db = db
        self.stock_service = stock_service
        self.sales_service = sales_service
        self.system_service = system_service
        self.logger = logging.getLogger("CommandDispatcher")
        
        # Mapa de comandos: "comando" -> (función, nivel_acceso, es_pro)
        # Niveles de acceso: 'gratis', 'empleado', 'admin'
        self.commands_map: Dict[str, tuple] = {
            # --- STOCK ---
            "stock.list": (self._handle_stock_list, "gratis", False),
            "stock.get": (self._handle_stock_get, "gratis", False),
            "stock.add": (self._handle_stock_add, "admin", False),
            "stock.edit": (self._handle_stock_edit, "admin", False),
            "stock.delete": (self._handle_stock_delete, "admin", False),
            "stock.update_qty": (self._handle_stock_update_qty, "empleado", False),
            
            # --- VENTAS ---
            "venta.nueva": (self._handle_venta_nueva, "empleado", False),
            "venta.add": (self._handle_venta_add, "empleado", False),
            "venta.cobrar": (self._handle_venta_cobrar, "empleado", False),
            "venta.cancelar": (self._handle_venta_cancelar, "empleado", False),
            
            # --- CAJA ---
            "caja.abrir": (self._handle_caja_abrir, "admin", False),
            "caja.cerrar": (self._handle_caja_cerrar, "admin", False),
            "caja.status": (self._handle_caja_status, "empleado", False),
            
            # --- REPORTES (PRO) ---
            "reporte.resumen": (self._handle_reporte_resumen, "admin", True),
            "reporte.top": (self._handle_reporte_top, "admin", True),
            "reporte.alertas": (self._handle_reporte_alertas, "admin", True),
            
            # --- SISTEMA ---
            "sys.theme.set": (self._handle_sys_theme_set, "gratis", False),
            "sys.lang.set": (self._handle_sys_lang_set, "gratis", False),
            "sys.export_csv": (self._handle_sys_export_csv, "admin", True),
            "sys.info": (self._handle_sys_info, "gratis", False),
            "logs.view": (self._handle_logs_view, "admin", False),
        }

    def execute(self, command_str: str, params: Dict[str, Any] = None, current_user_role: str = "empleado", is_pro: bool = False) -> Dict[str, Any]:
        """
        Ejecuta un comando validando permisos y licencia.
        """
        if params is None:
            params = {}

        # 1. Buscar comando
        if command_str not in self.commands_map:
            return {"status": "error", "message": f"Comando '{command_str}' no reconocido."}

        handler, required_role, is_pro_feature = self.commands_map[command_str]

        # 2. Validar Licencia PRO
        if is_pro_feature and not is_pro:
            return {"status": "error", "message": "Esta función es exclusiva de la versión PRO. Por favor, actualiza tu licencia."}

        # 3. Validar Rol de Usuario
        if not self._check_role_permission(current_user_role, required_role):
            return {"status": "error", "message": f"Permisos insuficientes. Se requiere rol: {required_role}."}

        # 4. Ejecutar Handler
        try:
            self.logger.info(f"Executing command: {command_str} | User: {current_user_role}")
            return handler(params)
        except Exception as e:
            self.logger.error(f"Exception executing {command_str}: {e}")
            return {"status": "error", "message": f"Error interno ejecutando comando: {str(e)}"}

    def _check_role_permission(self, user_role: str, required_role: str) -> bool:
        """
        Verifica la jerarquía de roles.
        admin > empleado > gratis
        """
        hierarchy = {"admin": 3, "empleado": 2, "gratis": 1}
        return hierarchy.get(user_role, 0) >= hierarchy.get(required_role, 0)

    # --- HANDLERS DE STOCK ---

    def _handle_stock_get(self, params):
        codigo = params.get("codigo")
        if not codigo:
            return {"status": "error", "message": "Falta el código del producto"}
        
        res = self.stock_service.get_product(codigo)
        return res

    def _handle_stock_list(self, params):
        return self.stock_service.list_products(
            filter_text=params.get("filter"), 
            category=params.get("category")
        )

    def _handle_stock_add(self, params):
        return self.stock_service.add_product(
            codigo=params.get("codigo"),
            nombre=params.get("nombre"),
            precio=params.get("precio"),
            cantidad=params.get("cantidad"),
            categoria=params.get("categoria"),
            es_peso=params.get("es_peso", False)
        )

    def _handle_stock_edit(self, params):
        # Lógica simplificada: el add_product ya hace Upsert
        return self.stock_service.add_product(
            codigo=params.get("codigo"),
            nombre=params.get("nombre"),
            precio=params.get("precio"),
            cantidad=params.get("cantidad"),
            categoria=params.get("categoria"),
            es_peso=params.get("es_peso", False)
        )

    def _handle_stock_delete(self, params):
        return self.stock_service.delete_product(params.get("codigo"))

    def _handle_stock_update_qty(self, params):
        return self.stock_service.update_stock(
            codigo=params.get("codigo"), 
            amount=params.get("amount")
        )

    # --- HANDLERS DE VENTAS ---

    def _handle_venta_nueva(self, params):
        # En una TUI, el carrito suele ser un estado en memoria de la UI
        # Aquí simplemente confirmamos que la venta puede iniciar.
        return {"status": "success", "message": "Carrito de ventas inicializado."}

    def _handle_venta_add(self, params):
        # Valida si el producto existe antes de permitir agregarlo al carrito
        res = self.stock_service.get_product(params.get("codigo"))
        if res["status"] == "success":
            return {"status": "success", "data": res["data"], "message": "Producto agregado al carrito."}
        return res

    def _handle_venta_cobrar (self, params):
        # params: {cliente, items: [{codigo, cantidad}], metodo_pago, paga_con, alias}
        return self.sales_service.process_sale(
            cliente=params.get("cliente"),
            items=params.get("items"),
            metodo_pago=params.get("metodo_pago"),
            paga_con=params.get("paga_con"),
            alias=params.get("alias")
        )

    def _handle_venta_cancelar(self, params):
        return {"status": "success", "message": "Carrito vaciado."}

    # --- HANDLERS DE CAJA ---

    def _handle_caja_abrir(self, params):
        return self.sales_service.open_cash_box(params.get("monto_inicial"))

    def _handle_caja_cerrar(self, params):
        return self.sales_service.close_cash_box(params.get("monto_real"))

    def _handle_caja_status(self, params):
        return self.sales_service.get_cash_box_status()

    # --- HANDLERS DE REPORTES (PRO) ---

    def _handle_reporte_resumen(self, params):
        # Lógica de reporte: Facturación total y Ganancia
        sales = self.db.fetch_all("SELECT SUM(total) as total FROM sales")
        total_facturado = sales[0]['total'] or 0
        ganancia_est = total_facturado * 0.3 # Basado en el 30% del original
        return {
            "status": "success", 
            "data": {
                "total_facturado": total_facturado,
                "ganancia_estimada": ganancia_est
            }
        }

    def _handle_reporte_top(self, params):
        # Top productos más vendidos
        limit = params.get("limit", 3)
        query = '''
            SELECT p.nombre, SUM(si.cantidad) as total_vendido
            FROM sale_items si
            JOIN products p ON si.product_codigo = p.codigo
            WHERE 1=1
            GROUP BY p.codigo
            ORDER BY total_vendido DESC
            LIMIT ?
        '''
        top = self.db.fetch_all(query, (limit,))
        return {"status": "success", "data": [dict(t) for t in top]}

    def _handle_reporte_alertas(self, params):
        return self.stock_service.get_low_stock()

    # --- HANDLERS DE SISTEMA ---

    def _handle_sys_theme_set(self, params):
        return self.system_service.set_setting("theme", params.get("value"))

    def _handle_sys_lang_set(self, params):
        return self.system_service.set_setting("lang", params.get("value"))

    def _handle_sys_export_csv(self, params):
        return self.system_service.export_inventory_to_csv()

    def _handle_sys_info(self, params):
        return self.system_service.get_system_info()

    def _handle_logs_view(self, params):
        limit = params.get("limit", 100)
        logs = self.db.fetch_all("SELECT * FROM audit WHERE id > 0 ORDER BY id DESC LIMIT ?", (limit,))
        return {"status": "success", "data": [dict(l) for l in logs]}
