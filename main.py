import logging
import sys
import os
from src.core.database import DatabaseManager
from src.core.stock_service import StockService
from src.core.sales_service import SalesService
from src.core.system_service import SystemService
from src.commands.dispatcher import CommandDispatcher
from src.ui.web_server import WebServer

def setup_logging():
    """Configura el sistema de logging profesional."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "system.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Logging system initialized.")

def main():
    """
    Punto de entrada principal del Sistema de Stock y Escaneo.
    Orquestra la carga de todos los componentes en orden.
    """
    setup_logging()
    logger = logging.getLogger("Main")
    logger.info("🚀 Iniciando Sistema de Stock y Escaneo...")

    try:
        # 1. Inicializar Base de Datos
        # El DatabaseManager resuelve la ruta automáticamente (PC/Android)
        db = DatabaseManager()
        logger.info("✅ Base de datos conectada.")

        # 2. Inicializar Servicios de Negocio (Core)
        stock_service = StockService(db)
        sales_service = SalesService(db, stock_service)
        system_service = SystemService(db)
        logger.info("✅ Servicios del núcleo cargados.")

        # 3. Inicializar Orquestador de Comandos (Dispatcher)
        dispatcher = CommandDispatcher(
            db=db, 
            stock_service=stock_service, 
            sales_service=sales_service, 
            system_service=system_service
        )
        logger.info("✅ Command Dispatcher operativo.")

        # 4. Inicializar Interfaz de Usuario (Web Server)
        # El servidor API expone el Dispatcher al Frontend HTML
        web_server = WebServer(dispatcher=dispatcher, port=8888)
        web_server.start()
        logger.info("✅ Servidor Web iniciado en http://localhost:8888")

        logger.info("🌟 SISTEMA COMPLETAMENTE OPERATIVO")
        logger.info("Presione Ctrl+C para detener el servidor.")
        
        # Mantener el proceso vivo mientras el servidor corre en el hilo secundario
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo el sistema...")
        if 'web_server' in locals():
            web_server.stop()
        sys.exit(0)
    except Exception as e:
        logger.critical(f"❌ Error fatal durante el arranque: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
