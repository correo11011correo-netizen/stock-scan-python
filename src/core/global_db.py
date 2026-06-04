import sqlite3
import os
import logging

class GlobalDatabaseManager:
    """
    Gestor de la Base de Datos Global del Sistema.
    Maneja la identidad de usuarios, la definición de tenants (negocios) 
    y la matriz de permisos global.
    """
    
    def __init__(self, db_name="global_system.db"):
        self.db_name = db_name
        self.logger = logging.getLogger("GlobalDatabaseManager")
        self.db_path = self._resolve_global_path()
        self._init_global_db()

    def _resolve_global_path(self):
        """Resuelve la ruta de la base de datos global apuntando a la carpeta central de datos."""
        # Buscamos la carpeta 'data' relativa a la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, "data", self.db_name)
        self.logger.info(f"Global DB path resolved to central data directory: {path}")
        return path

    def _get_connection(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True) if os.path.dirname(self.db_path) else None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_global_db(self):
        """Inicializa las tablas globales de identidad y permisos."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Tabla de Tenants (Negocios)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        db_path TEXT NOT NULL,
                        business_name TEXT NOT NULL,
                        plan TEXT DEFAULT 'FREE', -- 'FREE', 'PRO', 'ENTERPRISE'
                        credits INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 2. Tabla de Usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL, -- 'OWNER', 'EMPLOYEE'
                        tenant_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(tenant_id) REFERENCES tenants(id)
                    )
                ''')
                
                # 3. Tabla de Permisos Dinámicos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS permissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tenant_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        permission_key TEXT NOT NULL, -- ej: 'perm_stock_write'
                        granted BOOLEAN DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tenant_id, user_id, permission_key),
                        FOREIGN KEY(tenant_id) REFERENCES tenants(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"Global Database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Critical Error initializing Global DB: {e}")
            raise e

    # --- MÉTODOS DE ACCESO ---

    def execute(self, query, params=()):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Global Query Error: {query} | Error: {e}")
            return None

    def fetch_one(self, query, params=()):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Global FetchOne Error: {query} | Error: {e}")
            return None

    def fetch_all(self, query, params=()):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Global FetchAll Error: {query} | Error: {e}")
            return []
