import psycopg2
from psycopg2 import extras
import os
import logging

class GlobalDatabaseManager:
    """
    Gestor de la base de datos maestra.
    Contiene la tabla de usuarios, tenants y permisos globales.
    Usa el esquema 'public' por defecto.
    """
    def __init__(self):
        self.logger = logging.getLogger("GlobalDatabaseManager")
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            self.logger.critical("DATABASE_URL no encontrada.")
            raise Exception("Error: Railway DATABASE_URL no configurada.")
        
        self._init_global_db()

    def _get_connection(self):
        return psycopg2.connect(self.db_url)

    def _init_global_db(self):
        """Crea las tablas maestras en el esquema public."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # 1. Tabla de Tenants (Negocios)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tenants (
                        id TEXT PRIMARY KEY,
                        owner_id TEXT,
                        schema_name TEXT UNIQUE NOT NULL,
                        business_name TEXT,
                        plan TEXT DEFAULT 'FREE',
                        credits INTEGER DEFAULT 10,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 2. Tabla de Usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        tenant_id TEXT REFERENCES tenants(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 3. Tabla de Permisos Granulares
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS permissions (
                        tenant_id TEXT REFERENCES tenants(id),
                        user_id TEXT REFERENCES users(id),
                        permission_key TEXT,
                        granted BOOLEAN DEFAULT FALSE,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (tenant_id, user_id, permission_key)
                    )
                ''')
                conn.commit()
                self.logger.info("Global Database initialized successfully in schema 'public'.")
            conn.close()
        except Exception as e:
            self.logger.error(f"Error initializing global DB: {e}")
            raise e

    def execute(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Global execute error: {e}")
            return None

    def fetch_one(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                res = cursor.fetchone()
            conn.close()
            return res
        except Exception as e:
            self.logger.error(f"Global fetch_one error: {e}")
            return None

    def fetch_all(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                res = cursor.fetchall()
            conn.close()
            return res
        except Exception as e:
            self.logger.error(f"Global fetch_all error: {e}")
            return []
