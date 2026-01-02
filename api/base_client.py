import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

# ==========================================================
# ROOT DIR
# ==========================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from core import EncryptionService
    from Log import DevLogger
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")


class APIManager:
    """
    Gestionnaire central des appels API
    Logging développeur avancé pour diagnostic et performance
    """

    def __init__(self):
        start = time.time()
        DevLogger.debug("▶️ START APIManager.__init__")

        try:
            self.session = requests.Session()
            self.session.verify = False

            retries = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )

            self.session.mount("https://", HTTPAdapter(max_retries=retries))
            self.session.mount("http://", HTTPAdapter(max_retries=retries))
            self.session.headers.update(Settings.HEADER)

            DevLogger.info("✅ Session HTTP initialisée avec succès")

        except Exception as e:
            DevLogger.exception("❌ Erreur lors de l'initialisation APIManager", e)
            raise
        finally:
            DevLogger.log_time("⏱ END APIManager.__init__", start)

    # ==================================================
    # Requête HTTP générique
    # ==================================================
    def make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:

        start = time.time()
        DevLogger.debug(
            "▶️ START make_request | endpoint=%s | method=%s",
            endpoint, method
        )

        url = (
            Settings.API_ENDPOINTS.get(endpoint, endpoint)
            if endpoint.startswith("_")
            else endpoint
        )

        last_exception = None

        try:
            for attempt in range(1, 4):
                try:
                    DevLogger.debug("🌐 Tentative %s -> %s", attempt, url)

                    response = self.session.request(
                        method=method.upper(),
                        url=url,
                        data=data,
                        json=json_data,
                        params=params,
                        timeout=timeout
                    )

                    DevLogger.debug("📥 HTTP %s", response.status_code)

                    if response.status_code == 200:
                        try:
                            payload = response.json()
                            DevLogger.debug(
                                "📦 JSON reçu (%s clés)",
                                len(payload) if isinstance(payload, dict) else "N/A"
                            )
                            return {
                                "status": "success",
                                "data": payload,
                                "status_code": 200
                            }
                        except json.JSONDecodeError:
                            DevLogger.warning("⚠️ Réponse non JSON")
                            return {
                                "status": "success",
                                "data": response.text,
                                "status_code": 200
                            }

                    elif response.status_code in (401, 403):
                        DevLogger.error("⛔ Accès refusé (%s)", response.status_code)
                        return {
                            "status": "error",
                            "error": "Accès refusé",
                            "status_code": response.status_code
                        }

                    else:
                        last_exception = f"HTTP {response.status_code}"
                        DevLogger.error(
                            "⚠️ HTTP %s | %s",
                            response.status_code,
                            response.text[:200]
                        )

                except requests.RequestException as e:
                    last_exception = str(e)
                    DevLogger.warning(
                        "⚠️ Erreur réseau tentative %s: %s",
                        attempt, last_exception
                    )

                time.sleep(2)

            DevLogger.error("❌ Échec après 3 tentatives")
            return {
                "status": "error",
                "error": last_exception,
                "status_code": None
            }

        except Exception as e:
            DevLogger.exception("❌ Exception fatale make_request", e)
            raise
        finally:
            DevLogger.log_time("⏱ END make_request", start)

    # ==================================================
    # Gestion standard de réponse
    # ==================================================
    def _handle_response(
        self,
        result: Dict[str, Any],
        success_default: Any = None,
        failure_default: Any = None
    ) -> Any:

        if result.get("status") == "success":
            return result.get("data", success_default)

        DevLogger.error("❌ API Error: %s", result.get("error"))
        return failure_default

    # ==================================================
    # Méthodes API métier
    # ==================================================
    def save_email(self, params: Dict[str, Any]) -> str:
        DevLogger.debug("▶️ START save_email")
        return str(
            self._handle_response(
                self.make_request("_SAVE_EMAIL_API", "POST", data=params),
                ""
            )
        )

    def send_status(self, params: Dict[str, Any]) -> str:
        DevLogger.debug("▶️ START send_status")
        return str(
            self._handle_response(
                self.make_request("_SEND_STATUS_API", "POST", data=params),
                ""
            )
        )

    def save_process(self, params: Dict[str, Any]) -> int:
        DevLogger.debug("▶️ START save_process")

        result = self.make_request("_SAVE_PROCESS_API", "POST", data=params)
        data = self._handle_response(result, {})

        try:
            if isinstance(data, dict) and data.get("status") is True:
                return data.get("inserted_id", -1)
        except Exception as e:
            DevLogger.exception("❌ Erreur save_process", e)

        return -1

    def load_scenarios(self, encrypted_key: str) -> Dict[str, Any]:
        DevLogger.debug("▶️ START load_scenarios")

        payload = {"encrypted": encrypted_key}
        return self._handle_response(
            self.make_request("_LOAD_SCENARIOS_API", "POST", json_data=payload),
            {"session": False, "scenarios": []},
            {"session": False, "scenarios": []}
        )

    def handle_save_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        DevLogger.debug("▶️ START handle_save_scenario")

        return self._handle_response(
            self.make_request("_HANDLE_SAVE_API", "POST", json_data=payload),
            {"success": True},
            {"success": False, "error": "Format de réponse invalide"}
        )

    def on_scenario_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        DevLogger.debug("▶️ START on_scenario_changed")

        return self._handle_response(
            self.make_request("_ON_SCENARIO_CHANGED_API", "POST", json_data=payload),
            {"success": True},
            {"success": False, "error": "Format de réponse invalide"}
        )

    def check_extension_update(self) -> Dict[str, Any]:
        DevLogger.debug("▶️ START check_extension_update")

        data = {"login": "rep.test", "password": "zsGEnntKD5q2Brp68yxT"}
        encrypted = EncryptionService.encrypt_message(
            json.dumps(data),
            Settings.KEY
        )

        url = (
            "http://reporting.nrb-apps.com/APP_R/redirect.php"
            f"?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted}"
        )

        return self._handle_response(
            self.make_request(url, "GET"),
            {}
        )


# ==========================================================
# Instance globale
# ==========================================================
APIManager = APIManager()
