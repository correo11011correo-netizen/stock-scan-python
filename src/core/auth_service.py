import logging
from datetime import datetime, timedelta
from .database import DatabaseManager
import bcrypt # Import bcrypt for password hashing

class AuthService:
    """
    Servicio de gestión de usuarios, suscripciones y control de acceso (Feature Gating).
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.logger = logging.getLogger("AuthService")

    def register_user(self, username, email, password):
        """Registra un nuevo usuario con una contraseña hasheada y asigna un rol por defecto.
        Asigna 7 días de prueba (trial).
        """
        try:
            # Hashear la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insertar usuario
            user_id = self.db.execute(
                "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?)",
                (username, email, hashed_password, 'free', 'active')
            )

            # Crear suscripción de prueba
            end_date = datetime.now() + timedelta(days=7)
            self.db.execute(
                "INSERT INTO subscriptions (user_id, plan_name, end_date, status) VALUES (?, ?, ?, ?)",
                (user_id, 'trial', end_date.isoformat(), 'active')
            )

            return {"status": "success", "user_id": user_id, "message": "Usuario registrado y prueba iniciada."}
        except Exception as e:
            self.logger.error(f"Error registering user {username}: {e}")
            return {"status": "error", "message": str(e)}

    def login_user(self, username, password):
        """Autentica un usuario y retorna sus datos si las credenciales son correctas."""
        try:
            user = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
            if user:
                # Verificar la contraseña hasheada
                if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return {"status": "success", "user_id": user['id'], "username": user['username'], "role": user['role']}
                else:
                    return {"status": "error", "message": "Contraseña incorrecta."}
            else:
                return {"status": "error", "message": "Usuario no encontrado."}
        except Exception as e:
            self.logger.error(f"Error logging in user {username}: {e}")
            return {"status": "error", "message": str(e)}

    def get_user_status(self, user_id):
        """Retorna el estado de suscripción y acceso del usuario."""
        query = '''
            SELECT u.status as user_status, u.role, s.plan_name, s.end_date, s.status as sub_status
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
            WHERE u.id = ?
        '''
        data = self.db.fetch_one(query, (user_id,))
        if data:
            return dict(data)
        return None

    def is_pro_access(self, user_id):
        """Valida si el usuario tiene acceso a funcionalidades PRO."""
        status = self.get_user_status(user_id)
        if not status:
            return False

        # Verificar si la suscripción está activa y no ha expirado
        if status.get('sub_status') == 'active':
            end_date_str = status.get('end_date')
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str)
                if end_date > datetime.now() or status['plan_name'] == 'lifetime':
                    return True
            elif status['plan_name'] == 'lifetime': # Si no hay end_date pero es lifetime
                return True
        return False
