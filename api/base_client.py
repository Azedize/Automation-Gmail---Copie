# ==========================================================
# api/safe_api_manager.py
# APIManager آمن مع logs مفصلة و emojis
# ==========================================================

import os
import sys
import json
import time
import traceback
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)  # quitte immédiatement le script avec un code d'erreur
    
    


class APIManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # ⚠️ SSL désactivé volontairement

        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        # 🔹 Header global
        self.session.headers.update(Settings.HEADER)
        # print(f"🟢 [INIT] Headers globaux appliqués : {self.session.headers}")
        settings.WRITE_LOG_DEV_FILE(f"Headers globaux appliqués : {self.session.headers}", "INFO")

    # --------------------- Requête HTTP ---------------------
    def make_request( self, endpoint: str, method: str = "POST",  data: Optional[Dict] = None, json_data: Optional[Dict] = None,  params: Optional[Dict] = None,  headers: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith('_') else endpoint
        # 🔹 Fusionner headers globaux مع headers spécifiques
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        # print(f"\n🔗 [INIT] Endpoint: {endpoint}")
        # print(f"🔗 [INIT] URL Résolue: {url}")
        # print(f"🔗 [INIT] Méthode: {method}")
        # print(f"📥 Data: {data}")
        # print(f"📥 JSON: {json_data}")
        # print(f"📥 Params: {params}")
        # print(f"📝 Headers: {req_headers}")
        # print(f"⏱️ Timeout: {timeout}s\n")       

        settings.WRITE_LOG_DEV_FILE(f"Endpoint: {endpoint}, URL: {url}, Method: {method}, Data: {data}, JSON: {json_data}, Params: {params}, Headers: {req_headers}, Timeout: {timeout}s", "INFO")

        last_exception = None

        for attempt in range(1, 6):
            try:
                settings.WRITE_LOG_DEV_FILE(f"🌐 [TRY {attempt}] {method.upper()} {url}", "INFO")
                response = self.session.request(  method=method.upper(),  url=url,   data=data,   json=json_data,   params=params, headers=req_headers,   timeout=timeout   )
                # print(f"🌍 [FULL URL] {response.url}")  
                # print(f"➡️ Response: HTTP {response.status_code}")
                # print(f"📄 Headers: {dict(response.headers)}")
                # print(f"📄 Body preview: {response.text[:200]}")

                settings.WRITE_LOG_DEV_FILE(f"🌍 [FULL URL] {response.url}", "INFO")
                settings.WRITE_LOG_DEV_FILE(f"➡️ Response: HTTP {response.status_code}", "INFO")
                settings.WRITE_LOG_DEV_FILE(f"📄 Headers: {dict(response.headers)}", "INFO")
                settings.WRITE_LOG_DEV_FILE(f"📄 Body preview: {response.text[:200]}", "INFO")


                # ✅ Succès
                if response.status_code == 200:
                    try:
                        parsed = response.json()
                        # print(f"✅ [SUCCESS] JSON parsed: {parsed}")
                        settings.WRITE_LOG_DEV_FILE(f"✅ JSON parsed successfully: {parsed}", "INFO")
                        return {"status": "success", "data": parsed, "status_code": 200}
                    except json.JSONDecodeError:
                        # print(f"⚠️ [WARN] JSON decode failed, returning raw text")
                        settings.WRITE_LOG_DEV_FILE(f"⚠️ JSON decode failed, returning raw text", "WARN")
                        return {"status": "success", "data": response.text, "status_code": 200}

                # 🔒 Auth / Accès refusé
                elif response.status_code in (401, 403):
                    msg = f"HTTP {response.status_code}: Access denied / session expired"
                    # print(f"⛔ [AUTH] {msg}")
                    settings.WRITE_LOG_DEV_FILE(f"⛔ {msg}", "WARNING")
                    return {"status": "error", "error": msg, "status_code": response.status_code}

                # ❌ Autres erreurs HTTP
                else:
                    last_exception = f"HTTP {response.status_code}"
                    # print(f"⚠️ [FAIL] HTTP {response.status_code} - Body preview: {response.text[:200]}")
                    settings.WRITE_LOG_DEV_FILE(f"⚠️ HTTP {response.status_code} - Body preview: {response.text[:200]}", "WARNING")

            except requests.RequestException as e:
                Settings.WRITE_LOG_DEV_FILE(f"RequestException on attempt {attempt}: {traceback.format_exc()}", "ERROR")
                last_exception = str(e)
                # print(f"🔥 [EXCEPTION] Try {attempt}: {last_exception}")
                settings.WRITE_LOG_DEV_FILE(f"🔥 [EXCEPTION] Try {attempt}: {last_exception}", "ERROR")

            # ⏳ Retry
            if attempt < 3:
                # print("⏳ [RETRY] Waiting 2s before next attempt...\n")
                settings.WRITE_LOG_DEV_FILE("⏳ [RETRY] Waiting 2s before next attempt...\n", "INFO")
                time.sleep(2)

        # ❌ Échec final
        # print(f"❌ [FINAL] Failed after 5 attempts: {last_exception}")
        settings.WRITE_LOG_DEV_FILE(f"❌ Failed after 5 attempts: {last_exception}", "ERROR")
        return {"status": "error", "error": f"Failed after 5 attempts: {last_exception}", "status_code": None}


    # --------------------- Gestion de réponse ---------------------
    def _handle_response(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None):
        try:
            status = result.get("status")
            if status == "success":
                data = result.get("data", success_default)
                # print(f"🟩 [HANDLE SUCCESS] Data => {data}")
                settings.WRITE_LOG_DEV_FILE(f"🟩 [HANDLE SUCCESS] Data => {data}", "INFO")
                return data
            else:
                # print(f"🟥 [HANDLE ERROR] {result.get('error', 'Unknown error')}")
                settings.WRITE_LOG_DEV_FILE(f"🟥 [HANDLE ERROR] {result.get('error', 'Unknown error')}", "ERROR")
                return failure_default
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Exception in _handle_response: {traceback.format_exc()}", "ERROR")

            # print(f"🔥 [HANDLE EXCEPTION] _handle_response crashed: {str(e)}")
            return failure_default


    def load_scenarios(self, Url_Api) -> Dict[str, Any]:
        # print("🔹 Starting load_scenarios")
        settings.WRITE_LOG_DEV_FILE("🔹 Starting load_scenarios", "INFO")

        # 1️⃣ Show API URL
        # print(f"🌐 API URL: {Url_Api}")
        settings.WRITE_LOG_DEV_FILE(f"🌐 API URL: {Url_Api}", "INFO")

        # 2️⃣ Send GET request
        try:
            # print("📡 Sending GET request to API...")
            settings.WRITE_LOG_DEV_FILE("📡 Sending GET request to API...", "INFO")
            result = self.make_request(Url_Api, "GET")
            # print(f"📥 Raw API response: {result}")
            settings.WRITE_LOG_DEV_FILE(f"📥 Raw API response: {result}", "INFO")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Exception during API request: {traceback.format_exc()}", "ERROR")
            # print(f"❌ Exception during API request: {e}")
            settings.WRITE_LOG_DEV_FILE(f"❌ Exception during API request: {e}", "ERROR")
            return {"session": False, "scenarios": []}

        try:
            # print("🔄 Handling API response...")
            settings.WRITE_LOG_DEV_FILE("🔄 Handling API response...", "INFO")
            response = self._handle_response( result,  {"session": False, "scenarios": []}, {"session": False, "scenarios": []} )
            # print(f"🔍 Final handled response: {response}")
            settings.WRITE_LOG_DEV_FILE(f"🔍 Final handled response: {response}", "INFO")
            return response
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Exception while handling response: {traceback.format_exc()}", "ERROR")
            # print(f"❌ Exception while handling response: {e}")
            settings.WRITE_LOG_DEV_FILE(f"❌ Exception while handling response: {e}", "ERROR")
            return {"session": False, "scenarios": []}
    # --------------------- Méthodes API ---------------------
    def save_process(self, params: Dict[str, Any]) -> int:
        result = self.make_request("_SAVE_PROCESS_API", "POST", json_data=params)
        # print(f"🔍 [DEBUG] Raw result: {result}")
        settings.WRITE_LOG_DEV_FILE(f"🔍 [DEBUG] Raw result: {result}", "INFO")
        data = self._handle_response(result, {})
        if isinstance(data, dict) and data.get("status") is True:
            # print(f"✅ [PROCESS SAVED] ID: {data.get('inserted_id')}")
            settings.WRITE_LOG_DEV_FILE(f"✅ [PROCESS SAVED] ID: {data.get('inserted_id')}", "INFO")
            return data.get("inserted_id", -1)
        return -1

    def save_email(self, params: Dict[str, Any]) -> str:
        result = self.make_request("_SAVE_EMAIL_API", "POST", json_data=params)
        return str(self._handle_response(result, ""))

    def send_status(self, params: Dict[str, Any]) -> str:
        # print("📤 Params envoyés:", params)
        settings.WRITE_LOG_DEV_FILE(f"📤 Params envoyés: {params}", "INFO")

        result = self.make_request("_SEND_STATUS_API", "POST", json_data=params)

        # print("📥 Réponse brute:", result)
        settings.WRITE_LOG_DEV_file(f"📥 Réponse brute: {result}", "INFO")

        return str(self._handle_response(result, ""))


    def handle_save_scenario(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
        # print("🚀 [HANDLE_SAVE_SCENARIO] Starting handle_save_scenario function")
        # print(f"📋 [HANDLE_SAVE_SCENARIO] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        # print(f"🔗 [HANDLE_SAVE_SCENARIO] API URL: {Url_Api}")
        settings.WRITE_LOG_DEV_FILE(f"🚀 Starting handle_save_scenario with payload: {json.dumps(payload, indent=2, ensure_ascii=False)} and API URL: {Url_Api}", "INFO")

        # print("📡 [HANDLE_SAVE_SCENARIO] Calling make_request...")
        settings.WRITE_LOG_DEV_FILE("📡 Calling make_request...", "INFO")
        result = self.make_request(Url_Api, "POST", data=payload)
        # print(f"📥 [HANDLE_SAVE_SCENARIO] make_request result: {result}")
        settings.WRITE_LOG_DEV_FILE(f"📥 make_request result: {result}", "INFO")

        # print("🔄 [HANDLE_SAVE_SCENARIO] Calling _handle_response...")
        settings.WRITE_LOG_DEV_FILE("🔄 Calling _handle_response...", "INFO")
        response = self._handle_response(result, {"success": True} , {"success": False, "error": "Format de réponse invalide"})
        # print(f"✅ [HANDLE_SAVE_SCENARIO] _handle_response result: {response}")
        settings.WRITE_LOG_DEV_FILE(f"✅ _handle_response result: {response}", "INFO")

        # print("🏁 [HANDLE_SAVE_SCENARIO] handle_save_scenario completed")
        settings.WRITE_LOG_DEV_FILE("🏁 handle_save_scenario completed", "INFO")
        return response



# ==========================================================
# Instance globale
# ==========================================================
APIManager = APIManager()

