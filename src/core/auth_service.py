import os
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional
from .global_db import GlobalDatabaseManager

class AuthService:
    """
    Servicio de Autenticación y Gestión de Identidad.
    Coordina el acceso de usuarios, la validación de tokens 
    y la resolución de la base de datos del tenant.
    """
    
    def __init__(self, global_db: GlobalDatabaseManager):
        self.global_db = global_db
        self.logger = logging.getLogger("AuthService")
        # Almacenamiento simple de sesiones en memoria {token: user_data}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def list_all_users_admin(self) -> Dict[str, Any]:
        """
        Devuelve una lista detallada de TODOS los usuarios del sistema, 
        incluyendo la información de suscripción de sus tenants.
        Acceso exclusivo para administradores globales.
        """
        try:
            query = '''
                SELECT 
                    u.id as user_id, 
                    u.username, 
                    u.role, 
                    u.tenant_id, 
                    t.business_name, 
                    t.plan, 
                    t.credits 
                FROM users u 
                JOIN tenants t ON u.tenant_id = t.id
                ORDER BY t.business_name ASC, u.username ASC
            '''
            results = self.global_db.fetch_all(query)
            return {
                "status": "success", 
                "data": [dict(row) for row in results],
                "total": len(results)
            }
        except Exception as e:
            self.logger.error(f"Error listing all users: {e}")
            return {"status": "error", "message": str(e)}

    def _hash_password(self, password: str) -> str:
        """Hashea la contraseña para almacenamiento seguro."""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password) -> Dict[str, Any]:
        """
        Autentica al usuario y crea una sesión.
        Retorna el token y la información básica del usuario, incluyendo el plan del negocio.
        """
        pwd_hash = self._hash_password(password)
        # Join con la tabla tenants para obtener el plan y los créditos
        user = self.global_db.fetch_one(
            '''
            SELECT u.*, t.plan, t.credits 
            FROM users u 
            JOIN tenants t ON u.tenant_id = t.id 
            WHERE u.username = ? AND u.password_hash = ?
            ''', 
            (username, pwd_hash)
        )

        if not user:
            self.logger.warning(f"Intento de login fallido para usuario: {username}")
            return {"status": "error", "message": "Credenciales incorrectas."}

        # Crear token de sesión único
        token = str(uuid.uuid4())
        user_data = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "tenant_id": user["tenant_id"],
            "plan": user["plan"],
            "credits": user["credits"]
        }
        self._sessions[token] = user_data
        
        self.logger.info(f"Usuario {username} logueado correctamente. Plan: {user['plan']}. Token generado.")
        return {
            "status": "success", 
            "token": token, 
            "user": user_data
        }

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida si un token es activo y retorna la información del usuario."""
        return self._sessions.get(token)

    def logout(self, token: str):
        """Elimina la sesión del usuario."""
        if token in self._sessions:
            del self._sessions[token]
            return {"status": "success"}
        return {"status": "error", "message": "Sesión no encontrada."}

    def resolve_tenant_db(self, tenant_id: str) -> Optional[str]:
        """Busca la ruta del archivo de base de datos para un tenant específico."""
        if not tenant_id:
            return None
        
        tenant = self.global_db.fetch_one(
            "SELECT db_path FROM tenants WHERE id = ?", 
            (tenant_id,)
        )
        return tenant["db_path"] if tenant else None

    def get_user_permissions(self, user_id: str, tenant_id: str) -> set:
        """
        Retorna el conjunto de permisos otorgados para un usuario en un tenant.
        Retorna un set de strings (ej: {'perm_stock_read', 'perm_sales_process'}).
        """
        query = "SELECT permission_key FROM permissions WHERE user_id = ? AND tenant_id = ? AND granted = 1"
        results = self.global_db.fetch_all(query, (user_id, tenant_id))
        return {row["permission_key"] for row in results}

    def set_user_permission(self, tenant_id: str, user_id: str, permission_key: str, granted: bool) -> Dict[str, Any]:
        """Asigna o revoca un permiso específico para un usuario en un tenant."""
        try:
            query = '''
                INSERT INTO permissions (tenant_id, user_id, permission_key, granted, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tenant_id, user_id, permission_key) DO UPDATE SET
                    granted=excluded.granted,
                    updated_at=excluded.updated_at
            '''
            self.global_db.execute(query, (tenant_id, user_id, permission_key, 1 if granted else 0))
            return {"status": "success", "message": f"Permiso {permission_key} {'otorgado' if granted else 'revocado'}."}
        except Exception as e:
            self.logger.error(f"Error setting permission: {e}")
            return {"status": "error", "message": str(e)}

    def revoke_user_access(self, user_id: str) -> Dict[str, Any]:
        """Elimina completamente a un usuario del sistema (y sus permisos)."""
        try:
            # Eliminar permisos primero por integridad
            self.global_db.execute("DELETE FROM permissions WHERE user_id = ?", (user_id,))
            # Eliminar usuario
            self.global_db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return {"status": "success", "message": "Acceso del usuario revocado exitosamente."}
        except Exception as e:
            self.logger.error(f"Error revoking access: {e}")
            return {"status": "error", "message": str(e)}

    def create_owner_account(self, username, password, business_name) -> Dict[str, Any]:
        """
        Crea un nuevo dueño y su respectiva instancia de negocio (Tenant).
        Esta función es la base para el registro de nuevos negocios.
        """
        try:
            # 1. Crear IDs únicos
            user_id = str(uuid.uuid4())[:8]
            tenant_id = f"tenant_{user_id}"
            
            # 2. Definir ruta de la base de datos del tenant
            # Usamos la ruta absoluta al directorio de datos central
            db_filename = f"{tenant_id}.db"
            # Resolver ruta relativa a la carpeta /data del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "data", db_filename) 

            # 3. Insertar Tenant
            self.global_db.execute(
                "INSERT INTO tenants (id, owner_id, db_path, business_name, plan, credits) VALUES (?, ?, ?, ?, ?, ?)",
                (tenant_id, user_id, db_path, business_name, "FREE", 10)
            )

            # 4. Insertar Usuario como OWNER
            self.global_db.execute(
                "INSERT INTO users (id, username, password_hash, role, tenant_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, self._hash_password(password), "OWNER", tenant_id)
            )

            self.logger.info(f"Nuevo dueño creado: {username} para negocio {business_name} ({tenant_id})")
            return {
                "status": "success", 
                "user_id": user_id, 
                "tenant_id": tenant_id, 
                "db_path": db_path
            }
        except Exception as e:
            self.logger.error(f"Error creando cuenta de dueño: {e}")
            return {"status": "error", "message": str(e)}

    def create_employee_account(self, username, password, tenant_id) -> Dict[str, Any]:
        """Crea un usuario con rol EMPLOYEE vinculado a un negocio existente."""
        try:
            user_id = str(uuid.uuid4())[:8]
            self.global_db.execute(
                "INSERT INTO users (id, username, password_hash, role, tenant_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, self._hash_password(password), "EMPLOYEE", tenant_id)
            )
            return {"status": "success", "user_id": user_id}
        except Exception as e:
            self.logger.error(f"Error creando cuenta de empleado: {e}")
            return {"status": "error", "message": str(e)}

    def update_subscription(self, tenant_id: str, new_plan: str, additional_credits: int = 0) -> Dict[str, Any]:
        """Actualiza el plan de suscripción y añade créditos a un tenant."""
        try:
            # Actualizar plan y sumar créditos
            self.global_db.execute(
                "UPDATE tenants SET plan = ?, credits = credits + ? WHERE id = ?",
                (new_plan, additional_credits, tenant_id)
            )
            self.logger.info(f"Suscripción actualizada para {tenant_id}: {new_plan}, +{additional_credits} créditos.")
            return {"status": "success", "message": f"Plan actualizado a {new_plan} exitosamente."}
        except Exception as e:
            self.logger.error(f"Error updating subscription: {e}")
            return {"status": "error", "message": str(e)}
