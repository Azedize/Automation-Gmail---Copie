import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional, Union, List
from requests.adapters import HTTPAdapter, Retry


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from core import EncryptionService
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")


class APIManager:
    """Gestionnaire centralisé pour toutes les requêtes API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False

        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

        self.session.headers.update(Settings.HEADER)

    # --------------------- Requêtes HTTP ---------------------
    def make_request(self, endpoint: str, method: str = "POST", data: Optional[Dict] = None,
                     json_data: Optional[Dict] = None, params: Optional[Dict] = None,
                     timeout: int = 30) -> Dict[str, Any]:

        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith('_') else endpoint
        last_exception = None

        for attempt in range(1, 4):
            try:
                print(f"🌐 Tentative {attempt} - {method} {url}")
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    data=data,
                    json=json_data,
                    params=params,
                    timeout=timeout
                )
                print(f"📥 HTTP {response.status_code}")

                if response.status_code == 200:
                    try:
                        return {"status": "success", "data": response.json(), "status_code": 200}
                    except json.JSONDecodeError:
                        return {"status": "success", "data": response.text, "status_code": 200}
                elif response.status_code in [401, 403]:
                    return {"status": "error", "error": f"HTTP {response.status_code}: accès refusé", "status_code": response.status_code}
                else:
                    last_exception = f"HTTP {response.status_code}"
                    print(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")

            except requests.RequestException as e:
                last_exception = str(e)
                print(f"⚠️ Erreur tentative {attempt}: {last_exception}")

            if attempt < 3:
                time.sleep(2)  # Attente avant retry

        return {"status": "error", "error": f"Échec après 3 tentatives: {last_exception}", "status_code": None}

    # --------------------- Gestion de réponse ---------------------
    def _handle_response(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None) -> Any:
        if result["status"] == "success":
            return result["data"] if result["data"] is not None else success_default
        else:
            self.logger.error(f"❌ API Error: {result['error']}")
            return failure_default

    # --------------------- Méthodes API ---------------------
    def save_email(self, params: Dict[str, Any]) -> str:
        return str(self._handle_response(self.make_request('_SAVE_EMAIL_API', "POST", data=params), ""))

    def send_status(self, params: Dict[str, Any]) -> str:
        return str(self._handle_response(self.make_request('_SEND_STATUS_API', "POST", data=params), ""))

    def save_process(self, params: Dict[str, Any]) -> int:
        result = self.make_request('_SAVE_PROCESS_API', "POST", data=params)
        data = self._handle_response(result, {})
        try:
            if isinstance(data, dict) and data.get('status') is True:
                return data.get('inserted_id', -1)
        except Exception:
            pass
        return -1

    def check_versions(self) -> Union[Dict[str, Any], str]:
        result = self.make_request('_ON_SCENARIO_CHANGED_API', "GET", timeout=15)
        data = self._handle_response(result, {})
        if all(k in data for k in ["version_python", "version_interface", "version_extensions"]):
            return data
        return "_1"

    def load_scenarios(self, encrypted_key: str) -> Dict[str, Any]:
        payload = {"encrypted": encrypted_key}
        return self._handle_response(self.make_request('_LOAD_SCENARIOS_API', "POST", json_data=payload),
                                     {"session": False, "scenarios": []},
                                     {"session": False, "scenarios": []})

    def handle_save_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_response(self.make_request('_HANDLE_SAVE_API', "POST", json_data=payload),
                                     {"success": True},
                                     {"success": False, "error": "Format de réponse invalide"})

    def on_scenario_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_response(self.make_request('_ON_SCENARIO_CHANGED_API', "POST", json_data=payload),
                                     {"success": True},
                                     {"success": False, "error": "Format de réponse invalide"})

    def check_extension_update(self) -> Dict[str, Any]:
        DATA = {"login": "rep.test", "password": "zsGEnntKD5q2Brp68yxT"}
        encrypted = EncryptionService.encrypt_message(json.dumps(DATA), Settings.KEY)
        url = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted}"
        return self._handle_response(self.make_request(url, "GET"), {})

    def download_extension(self, download_url: str, dest_path: str) -> bool:
        try:
            with self.session.get(download_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            self.logger.error(f"❌ Download failed: {e}")
            return False

    def check_api_credentials(self, username: str, password: str) -> Union[Dict[str, Any], int]:
        data = {"rID": "1", "u": username, "p": password, "k": "mP5QXYrK9E67Y", "l": "1"}
        result = self.make_request('_APIACCESS_API', "POST", data=data)
        resp = self._handle_response(result, "")
        if resp in ["-1", "-2"]:
            return int(resp)
        try:
            entity = EncryptionService.decrypt_message(resp, Settings.KEY)
            return {"entity": entity, "encrypted_response": resp}
        except Exception:
            return -5

    def validate_session(self, username: str, entity: str) -> bool:
        params = {"k": "mP5QXYrK9E67Y", "rID": "4", "u": username, "entity": entity}
        result = self.make_request('_MAIN_API', "GET", params=params)
        data = self._handle_response(result, {})
        try:
            return data.get("data", [{}])[0].get("n") == "1"
        except Exception:
            return False


# Instance globale
APIManager = APIManager()
