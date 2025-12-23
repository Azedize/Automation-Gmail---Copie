# core/session_manager.py
import os
import sys
import json
import datetime
import pytz
from typing import Dict, Union
import traceback

# 🔹 Ajout du chemin racine
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from core.encryption import EncryptionService
    from config import settings
    from utils.validation_utils import ValidationUtils
    from api.base_client import APIManager
except ImportError as e:
    print(f"[ERROR] Import modules failed: {e}")


class SessionManager:
    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.encryption_service = EncryptionService
        self.key = settings.KEY

    # ================== Check session locale ==================
    def check_session(self) -> Dict:
        session_info = {"valid": False, "username": None, "date": None, "p_entity": None, "error": None}

        if not os.path.exists(self.session_path):
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                session_info["error"] = "EmptyFile"
                return session_info

            # Déchiffrement
            try:
                decrypted = self.encryption_service.decrypt_message(encrypted, self.key)
            except Exception as e:
                session_info["error"] = f"DecryptError: {e}"
                return session_info

            # Validation du format
            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            if not is_valid:
                session_info["error"] = "InvalidFormat"
                return session_info

            username = data["username"]
            date_str = data["date"]
            p_entity = data["entity"]

            tz = pytz.timezone("Africa/Casablanca")
            last_session = tz.localize(datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
            now = datetime.datetime.now(tz)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update({"valid": True, "username": username, "date": last_session, "p_entity": p_entity})
            else:
                session_info["error"] = "Expired"

        except Exception as e:
            session_info["error"] = f"FileReadError: {e}"

        return session_info

    # ================== Création de session ==================
    def create_session(self, username: str, p_entity: str) -> bool:
        try:
            casablanca_time = datetime.datetime.now(pytz.timezone("Africa/Casablanca"))
            session_data = f"{username}::{casablanca_time.strftime('%Y-%m-%d %H:%M:%S')}::{p_entity}"
            encrypted = self.encryption_service.encrypt_message(session_data, self.key)
            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)
            return True
        except Exception:
            return False

    # ================== Suppression de session ==================
    def clear_session(self):
        if os.path.exists(self.session_path):
            try:
                os.remove(self.session_path)
            except Exception:
                pass

    # ================== Vérification credentials API ==================
    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:
        try:
            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(username, validator_type="email", min_length=5)
            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(password, min_length=6)
            if not valid_user or not valid_pass:
                return -1

            data = {"rID": "1", "u": username, "p": password, "k": "mP5QXYrK9E67Y", "l": "1"}
            result = APIManager.make_request('_APIACCESS_API', "POST", data=data)
            resp = APIManager._handle_response(result, "")

            if resp in ["-1", "-2"]:
                return int(resp)

            try:
                entity = self.encryption_service.decrypt_message(resp, self.key)
                return (entity, resp)
            except Exception:
                return -5

        except Exception:
            return -5

    # ================== Validation complète ==================
    def validate_session_full(self, username: str, password: str) -> Dict:
        result = {"valid": False, "username": username, "p_entity": None, "error": None}

        check = self.check_api_credentials(username, password)
        if isinstance(check, int):
            result["error"] = f"APIErrorCode: {check}"
            return result

        entity, encrypted_response = check
        if not self.create_session(username, entity):
            result["error"] = "SessionCreationFailed"
            return result

        result.update({"valid": True, "p_entity": entity})
        return result

    # ================== Résumé de session ==================
    def get_session_summary(self) -> str:
        session_info = self.check_session()
        if session_info["valid"]:
            return f"Session active - Utilisateur: {session_info['username']}, Date: {session_info['date'].strftime('%Y-%m-%d %H:%M:%S')}, Entité: {session_info['p_entity']}"
        elif session_info["error"]:
            return f"Session invalide - Erreur: {session_info['error']}"
        else:
            return "Aucune session active"


# 🔹 Instance globale
SessionManager = SessionManager()
