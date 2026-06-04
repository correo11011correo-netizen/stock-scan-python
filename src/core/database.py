import sqlite3
import os
import logging
from datetime import datetime

class DatabaseManager:
    """
    Gestor de persistencia de datos para el Sistema de Stock y Escaneo.
    Sustituye el sistema de AsyncStorage por SQLite para mayor rendimiento y seguridad.
    """
    
    def __init__(self, db_name="stock_pro.db", db_path=None):
        self.db_name = db_name
        # Si se proporciona una ruta directa (vía AuthService), la usamos. 
        # Si no, resolvemos la ruta por defecto.
        self.db_path = db_path if db_path else self._resolve_db_path()
        self.logger = logging.getLogger("DatabaseManager")
        self._init_db()

    def _resolve_db_path(self):
        """Resuelve la ruta de la base de datos apuntando a la carpeta central de datos."""
        # Buscamos la carpeta 'data' relativa a la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, "data", self.db_name)

    def _get_connection(self):
        """Crea y retorna una conexión a la base de datos con row_factory para acceso por nombre."""
        # Asegurar que el directorio de datos existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True) if os.path.dirname(self.db_path) else None
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Crea todas las tablas necesarias si no existen."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Tabla de Productos (Migración de Storage.js)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        codigo TEXT PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        precio REAL NOT NULL,
                        cantidad REAL DEFAULT 0,
                        categoria TEXT,
                        es_peso BOOLEAN DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 2. Tabla de Ventas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total REAL NOT NULL,
                        cliente TEXT,
                        metodo_pago TEXT,
                        paga_con REAL,
                        vuelto REAL,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 3. Detalle de Ventas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sale_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sale_id INTEGER,
                        product_codigo TEXT,
                        cantidad REAL,
                        subtotal REAL,
                        FOREIGN KEY(sale_id) REFERENCES sales(id)
                    )
                ''')
                
                # 4. Auditoría (Migración de registrarAuditoria)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usuario TEXT,
                        accion TEXT,
                        detalle TEXT
                    )
                ''')
                
                # 5. Caja y Turnos (Migración de getCajaEstado)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cash_box (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        abierta BOOLEAN DEFAULT 0,
                        efectivo_inicial REAL DEFAULT 0,
                        ventas_efectivo REAL DEFAULT 0,
                        ventas_digital REAL DEFAULT 0,
                        hora_apertura TIMESTAMP,
                        hora_cierre TIMESTAMP,
                        monto_cierre_real REAL
                    )
                ''')
                # Asegurar que exista la fila de la caja
                cursor.execute("INSERT OR IGNORE INTO cash_box (id, abierta) VALUES (1, 0)")
                
                # 6. Alias de Clientes / QR (Migración de getAliases)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aliases (
                        id TEXT PRIMARY KEY,
                        nombre TEXT UNIQUE NOT NULL,
                        limite REAL DEFAULT 0,
                        acumulado REAL DEFAULT 0
                    )
                ''')
                
                # 7. Configuraciones del Sistema (Temas, Idioma, etc)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Critical Error initializing DB: {e}")
            raise e

    # --- MÉTODOS DE UTILIDAD ---

    def execute(self, query, params=()):
        """Ejecuta una consulta (INSERT, UPDATE, DELETE)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Query Error: {query} | Params: {params} | Error: {e}")
            return None

    def execute_many(self, query, params_list):
        """Ejecuta una consulta múltiples veces con una lista de parámetros en una sola transacción."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"ExecuteMany Error: {query} | Error: {e}")
            return None

    def fetch_one(self, query, params=()):

        """Retorna una sola fila."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"FetchOne Error: {query} | Error: {e}")
            return None

    def fetch_all(self, query, params=()):
        """Retorna todas las filas coincidentes."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"FetchAll Error: {query} | Error: {e}")
            return []
