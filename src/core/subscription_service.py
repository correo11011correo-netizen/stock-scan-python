import logging
import requests
from .database import DatabaseManager

class SubscriptionService:
    """
    Servicio de suscripción y pagos usando MercadoPago.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.logger = logging.getLogger("SubscriptionService")
        # Obtener token de la DB o configurar por defecto
        self.access_token = self._get_mp_token()

    def _get_mp_token(self):
        token = self.db.fetch_one("SELECT value FROM settings WHERE key = 'mp_token'")
        return token['value'] if token else None

    def create_subscription_link(self, user_id, plan_name, amount):
        """Genera un link de pago para una suscripción."""
        if not self.access_token:
            return {"status": "error", "message": "MercadoPago no configurado."}

        url = "https://api.mercadopago.com/checkout/preferences"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        body = {
            "items": [
                {
                    "title": f"Plan {plan_name}",
                    "quantity": 1,
                    "unit_price": amount,
                    "currency_id": "ARS"
                }
            ],
            "external_reference": str(user_id)
        }

        try:
            resp = requests.post(url, headers=headers, json=body)
            data = resp.json()
            link = data.get("init_point")
            
            if link:
                return {"status": "success", "link": link}
            return {"status": "error", "message": "No se pudo generar el link."}
        except Exception as e:
            self.logger.error(f"Error generating payment link: {e}")
            return {"status": "error", "message": str(e)}
