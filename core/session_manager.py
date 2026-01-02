# ==========================================================
# core/session_manager.py
# Gestion des sessions locales et validation API
# ==========================================================

import os
import sys
import datetime
import pytz
import traceback
import time
from typing import Dict, Union

# 🔹 Ajouter chemin racine pour imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from core.encryption import EncryptionService
    from config import settings
    from utils.validation_utils import ValidationUtils
    from api.base_client import APIManager
    from Log import DevLogger
except ImportError as e:
    print(f"[ERROR] Import modules failed: {e}")


class SessionManager:

    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.key = settings.KEY
        self.timezone = pytz.timezone("Africa/Casablanca")

    # ================== Vérification session locale ==================
    def check_session(self) -> Dict:
        session_info = {"valid": False, "username": None , "password": None, "date": None, "p_entity": None, "error": None}

        DevLogger.info(f"[INFO] Chemin du fichier session : {self.session_path}")

        if not ValidationUtils.path_exists(self.session_path):
            DevLogger.info("[WARNING] ❌ Le fichier session.txt n'existe pas")
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                DevLogger.info("[WARNING] ❌ Fichier session.txt vide")
                session_info["error"] = "EmptyFile"
                return session_info

            decrypted = EncryptionService.decrypt_message(encrypted, self.key)

            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            if not is_valid:
                DevLogger.info("[ERROR] Format session invalide")
                session_info["error"] = "InvalidFormat"
                return session_info

            username,password, date_str, p_entity = data["username"],data["password"], data["date"], data["entity"]

            print("🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​username:", username,"password : ", password , "date_str:", date_str, "p_entity:", p_entity)

            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            last_session = self.timezone.localize(last_session)
            now = datetime.datetime.now(self.timezone)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update({"valid": True, "username": username , "password": password, "date": last_session, "p_entity": p_entity})
            else:
                DevLogger.info("[INFO] Session expirée")
                session_info["error"] = "Expired"

        except Exception as e:
            DevLogger.error(f"[ERROR] Lecture fichier session : {e}")
            session_info["error"] = f"FileReadError: {e}"

        return session_info

    # ================== Création de session ==================
    def create_session(self, username: str,password: str, p_entity: str) -> bool:
        try:
            now = datetime.datetime.now(self.timezone)
            session_data = f"{username}::{password}::{now.strftime('%Y-%m-%d %H:%M:%S')}::{p_entity}"

            encrypted = EncryptionService.encrypt_message(session_data, self.key)

            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)

            DevLogger.info(f"[INFO] Session créée pour '{username}'")
            return True
        except Exception as e:
            DevLogger.error(f"[ERROR] Création session échouée : {e}")
            return False

    # ================== Suppression de session ==================
    def clear_session(self):
        if ValidationUtils.path_exists(self.session_path):
            try:
                os.remove(self.session_path)
                DevLogger.info("[INFO] Session supprimée")
            except Exception as e:
                DevLogger.error(f"[ERROR] Suppression session échouée : {e}")
        else:
            DevLogger.info("[INFO] Aucun fichier de session à supprimer")

    # ================== Validation via API ==================
    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        try:
            params = {"k": "mP5QXYrK9E67Y", "rID": "4", "u": username, "entity": p_entity}
            result = APIManager.make_request('_MAIN_API', method="GET", params=params, timeout=10)

            if result["status"] != "success":
                return {"valid": False, "error": result.get("error", "ApiRequestFailed")}

            data = result.get("data", {})
            if data.get("data") and data["data"][0].get("n") == "1":
                return {"valid": True}
            return {"valid": False, "error": "ApiRejected"}

        except Exception as e:
            DevLogger.error(f"[ERROR] Validation API échouée : {e}")
            return {"valid": False, "error": str(e)}

    # ================== Vérification complète ==================
    def check_session_full(self) -> Dict:
        session_info = self.check_session()
        if not session_info["valid"]:
            DevLogger.info("[SESSION] ❌ Session locale invalide")
            return session_info

        DevLogger.info("[SESSION] ✅ Session locale valide, vérification API...")
        api_result = self.validate_session_with_api(session_info["username"], session_info["p_entity"])

        if not api_result.get("valid"):
            DevLogger.info("[SESSION] ❌ Session refusée par l’API")
            session_info["valid"] = False
            session_info["error"] = api_result.get("error", "ApiValidationFailed")
            return session_info

        DevLogger.info("[SESSION] ✅ Session validée (LOCAL + API)")
        return session_info

    # ================== Vérification credentials API ==================
    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:
        try:
            DevLogger.info(f"🔹 [DEBUG] Validation inputs: username='{username}', password='{'*' * len(password)}'")

            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(username, validator_type="text", min_length=5)
            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(password, min_length=6)

            if not valid_user:
                DevLogger.info(f"❌ Invalid username: {msg_user}")
                return -1
            if not valid_pass:
                DevLogger.info(f"❌ Invalid password: {msg_pass}")
                return -1

            DevLogger.info("✅ Input validation successful")
            payload = {"rID": "1", "u": username, "p": password, "k": "mP5QXYrK9E67Y", "l": "1"}

            resp = None
            for attempt in range(1, 6):
                DevLogger.info(f"🔁 API attempt {attempt}/5")
                result = APIManager.make_request("_APIACCESS_API", method="POST", data=payload, timeout=10)
                resp = APIManager._handle_response(result, failure_default=None)
                if resp is not None:
                    DevLogger.info(f"✅ API response received")
                    break
                time.sleep(2)
            else:
                DevLogger.info("❌ Connection failed after 5 attempts")
                return -3

            if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                return int(resp)

            try:
                entity = EncryptionService.decrypt_message(resp, self.key)
                if not entity:
                    return -4
                return (entity, resp)
            except Exception as e:
                DevLogger.error(f"❌ Exception during decryption: {e}")
                traceback.print_exc()
                return -5

        except Exception as e:
            DevLogger.error(f"❌ Unexpected exception in check_api_credentials: {e}")
            traceback.print_exc()
            return -5


# ==========================================================
# Instance globale
# ==========================================================
SessionManager = SessionManager()
