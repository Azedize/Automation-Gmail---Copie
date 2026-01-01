# core/session_manager.py

import os
import sys
import datetime
import pytz
from typing import Dict
from typing import Union
import traceback
import time

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
        self.key = settings.KEY

    # ================== Check session locale ==================
    def check_session(self) -> Dict:
        session_info = {
            "valid": False,
            "username": None,
            "date": None,
            "p_entity": None,
            "error": None
        }

        print(f"[INFO] Chemin du fichier session : {self.session_path}")

        if not ValidationUtils.path_exists(self.session_path):
            print("[WARNING] ❌ Le fichier session.txt n'existe pas")
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                print("[WARNING] ❌ Fichier session.txt vide")
                session_info["error"] = "EmptyFile"
                return session_info

            # Déchiffrement
            try:
                decrypted = EncryptionService.decrypt_message(encrypted, self.key)
            except Exception as e:
                print(f"[ERROR] Déchiffrement échoué : {e}")
                session_info["error"] = f"DecryptError: {e}"
                return session_info

            # Validation du format
            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            if not is_valid:
                print("[ERROR] Format session invalide")
                session_info["error"] = "InvalidFormat"
                return session_info

            username = data["username"]
            date_str = data["date"]
            p_entity = data["entity"]

            # Vérification expiration
            tz = pytz.timezone("Africa/Casablanca")
            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            last_session = tz.localize(last_session)
            now = datetime.datetime.now(tz)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update({
                    "valid": True,
                    "username": username,
                    "date": last_session,
                    "p_entity": p_entity
                })
            else:
                print("[INFO] Session expirée")
                session_info["error"] = "Expired"

        except Exception as e:
            print(f"[ERROR] Lecture fichier session : {e}")
            session_info["error"] = f"FileReadError: {e}"

        return session_info

    # ================== Création de session ==================
    def create_session(self, username: str, p_entity: str) -> bool:
        try:
            casablanca_time = datetime.datetime.now(pytz.timezone("Africa/Casablanca"))
            session_data = f"{username}::{casablanca_time.strftime('%Y-%m-%d %H:%M:%S')}::{p_entity}"
            
            encrypted = EncryptionService.encrypt_message(session_data, self.key)
            
            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)
            
            print(f"[INFO] Session créée pour '{username}'")
            return True
        except Exception as e:
            print(f"[ERROR] Création session échouée : {e}")
            return False

    # ================== Suppression de session ==================
    def clear_session(self):
        if ValidationUtils.path_exists(self.session_path):
            try:
                os.remove(self.session_path)
                print("[INFO] Session supprimée")
            except Exception as e:
                print(f"[ERROR] Suppression session échouée : {e}")
        else:
            print("[INFO] Aucun fichier de session à supprimer")

    # ================== Validation via API ==================
    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        try:
            params = {
                "k": "mP5QXYrK9E67Y",
                "rID": "4",
                "u": username,
                "entity": p_entity
            }

            # 🔹 Appel via APIManager
            result = APIManager.make_request('_MAIN_API', method="GET", params=params, timeout=10)

            if result["status"] != "success":
                return {"valid": False, "error": result.get("error", "ApiRequestFailed")}

            data = result["data"]
            if data.get("data") and data["data"][0].get("n") == "1":
                return {"valid": True}

            return {"valid": False, "error": "ApiRejected"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    # ================== Validation complète ==================
    def check_session_full(self) -> Dict:
        session_info = self.check_session()

        if not session_info["valid"]:
            print("[SESSION] ❌ Session locale invalide")
            return session_info

        print("[SESSION] ✅ Session locale valide, vérification API...")
        api_result = self.validate_session_with_api(
            session_info["username"],
            session_info["p_entity"]
        )

        if not api_result.get("valid"):
            print("[SESSION] ❌ Session refusée par l’API")
            session_info["valid"] = False
            session_info["error"] = api_result.get("error", "ApiValidationFailed")
            return session_info

        print("[SESSION] ✅ Session validée (LOCAL + API)")
        return session_info



    # ================== Vérification credentials API ==================

    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:
        """
        Checks user credentials via the API and returns
        either a tuple (entity, encrypted response) or an error code.
        """
        try:
            print(f"🔹 [DEBUG] Input validation: username='{username}', password='{'*' * len(password)}'")

            # ----------------- Input validation -----------------
            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(
                username, validator_type="text", min_length=5
            )
            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(
                password, min_length=6
            )

            if not valid_user:
                print(f"❌ [DEBUG] Invalid username: {msg_user}")
                return -1

            if not valid_pass:
                print(f"❌ [DEBUG] Invalid password: {msg_pass}")
                return -1

            print("✅ [DEBUG] Input validation successful")

            # ----------------- Prepare API payload -----------------
            payload = {
                "rID": "1",
                "u": username,
                "p": password,
                "k": "mP5QXYrK9E67Y",
                "l": "1"
            }
            print(f"🔹 [DEBUG] API payload prepared: {payload}")

            # ----------------- API call with retry -----------------
            resp = None
            for attempt in range(1, 6):
                print(f"🔁 [DEBUG] API attempt {attempt}/5")

                result = APIManager.make_request(
                    "_APIACCESS_API",
                    method="POST",
                    data=payload,
                    timeout=10
                )

                resp = APIManager._handle_response(result, failure_default=None)

                if resp is not None:
                    print(f"✅ [DEBUG] API response received: {resp}")
                    break
                else:
                    print("⚠️ [DEBUG] No response received, waiting before retry...")
                    time.sleep(2)
            else:
                print("❌ [DEBUG] Connection failed after 5 attempts")
                return -3  # Unable to connect to server

            # ----------------- Handle known error codes BEFORE decryption -----------------
            if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                error_codes = {
                    "-1": -1,
                    "-2": -2,
                    "-3": -3,
                    "-4": -4,
                    "-5": -5,
                }
                print(f"❌ [DEBUG] Error code received from API: {resp}")
                return error_codes.get(str(resp), -5)

            # ----------------- Decrypt response -----------------
            try:
                print("🔓 [DEBUG] Attempting to decrypt API response...")
                entity = EncryptionService.decrypt_message(resp, self.key)

                if not entity:
                    print("❌ [DEBUG] Decryption failed: empty entity")
                    return -4

                print(f"✅ [DEBUG] Decryption successful, entity: {entity}")
                return (entity, resp)

            except Exception as e:
                print(f"❌ [DEBUG] Exception during decryption: {e}")
                traceback.print_exc()
                return -5

        except Exception as e:
            print(f"❌ [DEBUG] Unexpected exception in check_api_credentials: {e}")
            traceback.print_exc()
            return -5




    
# 🔹 Instance unique pour usage global
SessionManager= SessionManager()