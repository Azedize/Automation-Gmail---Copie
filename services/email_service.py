# services/api_service.py
import requests
import json
from typing import Dict, Optional, Any
from core.encryption import EncryptionService
from config import settings

class ApiService:
    def __init__(self):
        self.headers = settings.HEADER
        self.verify_ssl = False
        
    def authenticate(self, username: str, password: str) -> Dict:
        """
        Authentification via l'API
        """
        data = {
            "rID": "1",
            "u": username,
            "p": password,
            "k": "mP5QXYrK9E67Y",
            "l": "1"
        }
        
        for i in range(5):
            try:
                response = requests.post(
                    settings.API_ENDPOINTS['_APIACCESS_API'],
                    headers=self.headers,
                    data=data,
                    verify=self.verify_ssl,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.text
                    if result == "-1":
                        return {"success": False, "error": "Invalid credentials"}
                    elif result == "-2":
                        return {"success": False, "error": "Device not authorized"}
                    else:
                        # Décrypter la réponse
                        decrypted = EncryptionService.decrypt_message(result, settings.KEY)
                        return {"success": True, "entity": decrypted, "encrypted": result}
                        
            except Exception as e:
                print(f"Tentative {i+1} échouée: {e}")
                
        return {"success": False, "error": "Connection failed"}

    def save_email(self, data: Dict) -> Optional[str]:
        """
        Enregistre un email via l'API
        """
        try:
            response = requests.post(
                settings.API_ENDPOINTS['_SAVE_EMAIL_API'],
                headers=self.headers,
                data=data,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Erreur save_email: {e}")
        
        return None

    def send_status(self, data: Dict) -> Optional[str]:
        """
        Envoie un statut via l'API
        """
        try:
            response = requests.post(
                settings.API_ENDPOINTS['_SEND_STATUS_API'],
                headers=self.headers,
                data=data,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Erreur send_status: {e}")
        
        return None