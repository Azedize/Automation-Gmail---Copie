import os
import sys
import datetime
import pytz
import time
import traceback
from typing import Dict, Union

# 🔹 Ajout du chemin racine
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
    raise ImportError(f"❌ Import modules failed: {e}")


class SessionManager:

    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.key = settings.KEY
        DevLogger.debug("🧩 SessionManager initialized")

    # ================== Check session locale ==================
    def check_session(self) -> Dict:
        start = time.perf_counter()
        DevLogger.debug("🔍 check_session() started")

        session_info = {
            "valid": False,
            "username": None,
            "date": None,
            "p_entity": None,
            "error": None
        }

        try:
            DevLogger.info(f"📄 Session file path: {self.session_path}")

            if not ValidationUtils.path_exists(self.session_path):
                DevLogger.warning("❌ session.txt not found")
                session_info["error"] = "FileNotFound"
                return session_info

            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                DevLogger.warning("❌ session.txt is empty")
                session_info["error"] = "EmptyFile"
                return session_info

            # 🔓 Decrypt
            decrypted = EncryptionService.decrypt_message(encrypted, self.key)
            DevLogger.debug("🔓 Session decrypted successfully")

            # 🧪 Validate format
            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            if not is_valid:
                DevLogger.error("❌ Invalid session format")
                session_info["error"] = "InvalidFormat"
                return session_info

            username = data["username"]
            date_str = data["date"]
            p_entity = data["entity"]

            # ⏱ Expiration check
            tz = pytz.timezone("Africa/Casablanca")
            last_session = tz.localize(
                datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            )
            now = datetime.datetime.now(tz)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update({
                    "valid": True,
                    "username": username,
                    "date": last_session,
                    "p_entity": p_entity
                })
                DevLogger.info("✅ Local session valid")
            else:
                DevLogger.info("⌛ Session expired")
                session_info["error"] = "Expired"

        except Exception as e:
            DevLogger.error(
                f"❌ check_session error: {e}\n{traceback.format_exc()}"
            )
            session_info["error"] = f"SessionError: {e}"

        finally:
            DevLogger.debug(
                f"⏱️ check_session execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

        return session_info

    # ================== Create session ==================
    def create_session(self, username: str, p_entity: str) -> bool:
        start = time.perf_counter()
        DevLogger.debug("📝 create_session() started")

        try:
            casablanca_time = datetime.datetime.now(
                pytz.timezone("Africa/Casablanca")
            )

            session_data = (
                f"{username}::"
                f"{casablanca_time.strftime('%Y-%m-%d %H:%M:%S')}::"
                f"{p_entity}"
            )

            encrypted = EncryptionService.encrypt_message(
                session_data, self.key
            )

            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)

            DevLogger.info(f"✅ Session created for user '{username}'")
            return True

        except Exception as e:
            DevLogger.error(
                f"❌ create_session failed: {e}\n{traceback.format_exc()}"
            )
            return False

        finally:
            DevLogger.debug(
                f"⏱️ create_session execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # ================== Clear session ==================
    def clear_session(self):
        start = time.perf_counter()
        DevLogger.debug("🧹 clear_session() started")

        try:
            if ValidationUtils.path_exists(self.session_path):
                os.remove(self.session_path)
                DevLogger.info("🗑 Session file deleted")
            else:
                DevLogger.info("ℹ️ No session file to delete")

        except Exception as e:
            DevLogger.error(
                f"❌ clear_session failed: {e}\n{traceback.format_exc()}"
            )

        finally:
            DevLogger.debug(
                f"⏱️ clear_session execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # ================== Validate session via API ==================
    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        start = time.perf_counter()
        DevLogger.debug("🌐 validate_session_with_api() started")

        try:
            params = {
                "k": "mP5QXYrK9E67Y",
                "rID": "4",
                "u": username,
                "entity": p_entity
            }

            result = APIManager.make_request(
                "_MAIN_API",
                method="GET",
                params=params,
                timeout=10
            )

            if result["status"] != "success":
                DevLogger.error("❌ API validation failed")
                return {"valid": False, "error": result.get("error")}

            data = result["data"]
            if data.get("data") and data["data"][0].get("n") == "1":
                DevLogger.info("✅ API session validation OK")
                return {"valid": True}

            DevLogger.info("❌ API rejected session")
            return {"valid": False, "error": "ApiRejected"}

        except Exception as e:
            DevLogger.error(
                f"❌ validate_session_with_api error: {e}\n{traceback.format_exc()}"
            )
            return {"valid": False, "error": str(e)}

        finally:
            DevLogger.debug(
                f"⏱️ validate_session_with_api execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # ================== Full validation ==================
    def check_session_full(self) -> Dict:
        start = time.perf_counter()
        DevLogger.debug("🔐 check_session_full() started")

        session_info = self.check_session()

        if not session_info["valid"]:
            DevLogger.warning("❌ Local session invalid")
            return session_info

        api_result = self.validate_session_with_api(
            session_info["username"],
            session_info["p_entity"]
        )

        if not api_result.get("valid"):
            DevLogger.warning("❌ Session rejected by API")
            session_info["valid"] = False
            session_info["error"] = api_result.get("error")
            return session_info

        DevLogger.info("✅ Session validated (LOCAL + API)")
        return session_info

        


    # ================== Check API credentials ==================
    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:
        start = time.perf_counter()
        DevLogger.debug("🔑 check_api_credentials() started")

        try:
            DevLogger.debug(
                f"Input username='{username}', password='{'*' * len(password)}'"
            )

            # 🔹 Validation
            valid_user, _ = ValidationUtils.validate_qlineedit_text(
                username, validator_type="text", min_length=5
            )
            valid_pass, _ = ValidationUtils.validate_qlineedit_text(
                password, min_length=6
            )

            if not valid_user or not valid_pass:
                DevLogger.warning("❌ Invalid credentials input")
                return -1

            payload = {
                "rID": "1",
                "u": username,
                "p": password,
                "k": "mP5QXYrK9E67Y",
                "l": "1"
            }

            resp = None
            for attempt in range(1, 6):
                DevLogger.debug(f"🔁 API attempt {attempt}/5")

                result = APIManager.make_request(
                    "_APIACCESS_API",
                    method="POST",
                    data=payload,
                    timeout=10
                )

                resp = APIManager._handle_response(result, failure_default=None)
                if resp is not None:
                    break

                time.sleep(2)

            if resp is None:
                DevLogger.error("❌ API unreachable after retries")
                return -3

            if str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                DevLogger.warning(f"❌ API error code: {resp}")
                return int(resp)

            # 🔓 Decrypt entity
            entity = EncryptionService.decrypt_message(resp, self.key)
            DevLogger.info(f"✅ Credentials valid, entity={entity}")
            return (entity, resp)

        except Exception as e:
            DevLogger.error(
                f"❌ check_api_credentials failed: {e}\n{traceback.format_exc()}"
            )
            return -5

        finally:
            DevLogger.debug(
                f"⏱️ check_api_credentials execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )


# 🌍 Global instance
SessionManager = SessionManager()
