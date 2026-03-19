# ==========================================================
# api/safe_api_manager.py
# APIManager آمن مع logs مفصلة و emojis
# ==========================================================

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")


class APIManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # ⚠️ SSL désactivé volontairement

        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        # 🔹 Header global
        self.session.headers.update(Settings.HEADER)
        print(f"🟢 [INIT] Headers globaux appliqués : {self.session.headers}")

    # --------------------- Requête HTTP ---------------------
    def make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:

        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith('_') else endpoint

        # 🔹 Fusionner headers globaux مع headers spécifiques
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        print(f"\n🔗 [INIT] Endpoint: {endpoint}")
        print(f"🔗 [INIT] URL Résolue: {url}")
        print(f"🔗 [INIT] Méthode: {method}")
        print(f"📥 Data: {data}")
        print(f"📥 JSON: {json_data}")
        print(f"📥 Params: {params}")
        print(f"📝 Headers: {req_headers}")
        print(f"⏱️ Timeout: {timeout}s\n")

        last_exception = None

        for attempt in range(1, 4):
            try:
                print(f"🌐 [TRY {attempt}] {method.upper()} {url}")
                response = self.session.request(  method=method.upper(),  url=url,   data=data,   json=json_data,   params=params, headers=req_headers,   timeout=timeout   )
                print(f"🌍 [FULL URL] {response.url}")  
                print(f"➡️ Response: HTTP {response.status_code}")
                print(f"📄 Headers: {dict(response.headers)}")
                print(f"📄 Body preview: {response.text[:200]}")

                # ✅ Succès
                if response.status_code == 200:
                    try:
                        parsed = response.json()
                        print(f"✅ [SUCCESS] JSON parsed: {parsed}")
                        return {"status": "success", "data": parsed, "status_code": 200}
                    except json.JSONDecodeError:
                        print(f"⚠️ [WARN] JSON decode failed, returning raw text")
                        return {"status": "success", "data": response.text, "status_code": 200}

                # 🔒 Auth / Accès refusé
                elif response.status_code in (401, 403):
                    msg = f"HTTP {response.status_code}: Access denied / session expired"
                    print(f"⛔ [AUTH] {msg}")
                    return {"status": "error", "error": msg, "status_code": response.status_code}

                # ❌ Autres erreurs HTTP
                else:
                    last_exception = f"HTTP {response.status_code}"
                    print(f"⚠️ [FAIL] HTTP {response.status_code} - Body preview: {response.text[:200]}")

            except requests.RequestException as e:
                last_exception = str(e)
                print(f"🔥 [EXCEPTION] Try {attempt}: {last_exception}")

            # ⏳ Retry
            if attempt < 3:
                print("⏳ [RETRY] Waiting 2s before next attempt...\n")
                time.sleep(2)

        # ❌ Échec final
        print(f"❌ [FINAL] Failed after 3 attempts: {last_exception}")
        return {"status": "error", "error": f"Failed after 3 attempts: {last_exception}", "status_code": None}

    # --------------------- Gestion de réponse ---------------------
    def _handle_response(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None):
        try:
            status = result.get("status")
            if status == "success":
                data = result.get("data", success_default)
                print(f"🟩 [HANDLE SUCCESS] Data => {data}")
                return data
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"🟥 [HANDLE ERROR] {error_msg}")
                return failure_default
        except Exception as e:
            print(f"🔥 [HANDLE EXCEPTION] _handle_response crashed: {str(e)}")
            return failure_default


    def load_scenarios(self, Url_Api) -> Dict[str, Any]:
        print("🔹 Starting load_scenarios")

        # 1️⃣ Show API URL
        print(f"🌐 API URL: {Url_Api}")

        # 2️⃣ Send GET request
        try:
            print("📡 Sending GET request to API...")
            result = self.make_request(Url_Api, "GET")
            print(f"📥 Raw API response: {result}")
        except Exception as e:
            print(f"❌ Exception during API request: {e}")
            return {"session": False, "scenarios": []}

        try:
            print("🔄 Handling API response...")
            response = self._handle_response( result,  {"session": False, "scenarios": []}, {"session": False, "scenarios": []} )
            print(f"🔍 Final handled response: {response}")
            return response
        except Exception as e:
            print(f"❌ Exception while handling response: {e}")
            return {"session": False, "scenarios": []}
    # --------------------- Méthodes API ---------------------
    def save_process(self, params: Dict[str, Any]) -> int:
        result = self.make_request("_SAVE_PROCESS_API", "POST", json_data=params)
        print(f"🔍 [DEBUG] Raw result: {result}")
        data = self._handle_response(result, {})
        if isinstance(data, dict) and data.get("status") is True:
            print(f"✅ [PROCESS SAVED] ID: {data.get('inserted_id')}")
            return data.get("inserted_id", -1)
        return -1

    def save_email(self, params: Dict[str, Any]) -> str:
        result = self.make_request("_SAVE_EMAIL_API", "POST", json_data=params)
        return str(self._handle_response(result, ""))

    def send_status(self, params: Dict[str, Any]) -> str:
        result = self.make_request("_SEND_STATUS_API", "POST", json_data=params)
        return str(self._handle_response(result, ""))


    def handle_save_scenario(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
        result = self.make_request(Url_Api, "POST", data=payload)
        return self._handle_response(result, {"success": True} , {"success": False, "error": "Format de réponse invalide"})

    def on_scenario_changed(self,  payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
        result = self.make_request(Url_Api, "POST", data=payload)
        return self._handle_response(result, {"success": True},{"success": False, "error": "Format de réponse invalide"})

# ==========================================================
# Instance globale
# ==========================================================
APIManager = APIManager()
