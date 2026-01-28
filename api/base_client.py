# ==========================================================
# api/base_client.py
# APIManager sécurisé avec DevLogger
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
        self.session.verify = False  # Désactive vérif SSL (warning mais volontaire)

        retries = Retry( total=3 , backoff_factor=0.5 , status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        self.session.headers.update(Settings.HEADER)

    # --------------------- Requêtes HTTP ---------------------

    def make_request( self, endpoint: str, method: str = "POST" ,data: Optional[Dict] = None,   json_data: Optional[Dict] = None, params: Optional[Dict] = None,   timeout: int = 30):
        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith('_') else endpoint
        last_exception = None

        print(f"\n🔗 [INIT] Endpoint: {endpoint}")
        print(f"🔗 [INIT] URL Résolue: {url}")
        print(f"🔗 [INIT] Méthode: {method}")
        print(f"🔗 [INIT] Data: {data}")
        print(f"🔗 [INIT] JSON: {json_data}")
        print(f"🔗 [INIT] Params: {params}")
        print(f"⏱️ [INIT] Timeout: {timeout}s\n")

        Settings.WRITE_LOG_DEV_FILE(
            f"[INIT] {method} {url} | data={data} json={json_data} params={params} timeout={timeout}",
            level="DEBUG"
        )

        for attempt in range(1, 4):
            try:
                print(f"🌐 [TRY {attempt}] {method.upper()} {url}")
                Settings.WRITE_LOG_DEV_FILE(f"[TRY {attempt}] {method.upper()} {url}", level="INFO")

                response = self.session.request(  method=method.upper(), url=url,   data=data,  json=json_data,  params=params,    timeout=timeout  )

                print("➡️​➡️​➡️​➡️​", response)
                print(f"📥 [RESP] HTTP {response.status_code}")
                print(f"📄 [RESP] Headers: {dict(response.headers)}")
                print(f"📄 [RESP] Text (100 chars): {response.text[:100]}")

                Settings.WRITE_LOG_DEV_FILE(f"[RESP] HTTP {response.status_code} | Headers={dict(response.headers)} | Body(100)={response.text[:100]}",   level="DEBUG")

                if response.status_code == 200:
                    try:
                        parsed = response.json()
                        print(f"✅ [SUCCESS] JSON parsed: {parsed}")
                        Settings.WRITE_LOG_DEV_FILE(f"[SUCCESS] JSON parsed: {parsed}", level="INFO")
                        return {"status": "success", "data": parsed, "status_code": 200}
                    except json.JSONDecodeError:
                        print(f"⚠️ [WARN] JSON decode failed, returning raw text")
                        Settings.WRITE_LOG_DEV_FILE("[WARN] JSON decode failed, returning raw text", level="WARNING")
                        return {"status": "success", "data": response.text, "status_code": 200}

                elif response.status_code in (401, 403):
                    msg = f"HTTP {response.status_code}: Access denied / session expired"
                    print(f"⛔ [AUTH] {msg}")
                    Settings.WRITE_LOG_DEV_FILE(f"[AUTH] {msg}", level="ERROR")
                    return {"status": "error", "error": msg, "status_code": response.status_code}

                else:
                    last_exception = f"HTTP {response.status_code}"
                    print(f"⚠️ [FAIL] HTTP {response.status_code} - Body(100): {response.text[:100]}")
                    Settings.WRITE_LOG_DEV_FILE(
                        f"[FAIL] HTTP {response.status_code} | Body(100)={response.text[:100]}",
                        level="ERROR"
                    )

            except requests.RequestException as e:
                last_exception = str(e)
                print(f"🔥 [EXCEPTION] Try {attempt}: {last_exception}")
                Settings.WRITE_LOG_DEV_FILE(f"[EXCEPTION] Try {attempt}: {last_exception}", level="CRITICAL")

            if attempt < 3:
                print("⏳ [RETRY] Waiting 2 seconds before next attempt...\n")
                time.sleep(2)

        print(f"❌ [FINAL] Failed after 3 attempts: {last_exception}")
        Settings.WRITE_LOG_DEV_FILE(f"[FINAL] Failed after 3 attempts: {last_exception}", level="CRITICAL")

        return {
            "status": "error",
            "error": f"Failed after 3 attempts: {last_exception}",
            "status_code": None
        }


    # --------------------- Gestion de réponse ---------------------
    def _handle_response(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None):
        try:
            # 🔍 Log complet du résultat brut
            Settings.WRITE_LOG_DEV_FILE(f"[DEBUG] Raw API result: {result}", level="DEBUG")
            print(f"🟦 [DEBUG] Raw API result => {result}")

            status = result.get("status")
            print(f"🟨 [DEBUG] Status = {status}")

            if status == "success":
                data = result.get("data", success_default)

                # ✅ Succès – log détaillé
                Settings.WRITE_LOG_DEV_FILE(f"[SUCCESS] API returned data: {data}", level="INFO")
                print(f"🟩 [SUCCESS] Data => {data}")

                return data

            else:
                error_msg = result.get("error", "Unknown error")

                # ❌ Erreur – log détaillé
                Settings.WRITE_LOG_DEV_FILE(f"[ERROR] API Error: {error_msg}", level="ERROR")
                print(f"🟥 [ERROR] API Error => {error_msg}")

                return failure_default

        except Exception as e:
            # 💥 Exception inattendue
            Settings.WRITE_LOG_DEV_FILE(f"[EXCEPTION] _handle_response crashed: {str(e)}", level="CRITICAL")
            print(f"🔥 [EXCEPTION] _handle_response crashed => {e}")

            return failure_default

    # --------------------- Méthodes API ---------------------
    def save_email(self, params: Dict[str, Any]) -> str:
        result = self.make_request("_SAVE_EMAIL_API", "POST", data=params)
        return str(self._handle_response(result, ""))

    def send_status(self, params: Dict[str, Any]) -> str:
        result = self.make_request("_SEND_STATUS_API", "POST", data=params)
        return str(self._handle_response(result, ""))

    def save_process(self, params: Dict[str, Any]) -> int:
        result = self.make_request("_SAVE_PROCESS_API", "POST", data=params)
        data = self._handle_response(result, {})
        if isinstance(data, dict) and data.get("status") is True:
            return data.get("inserted_id", -1)
        return -1

    def load_scenarios(self, Url_Api) -> Dict[str, Any]:
        # print("🔹 Starting load_scenarios")

        # 1️⃣ Show API URL
        # print(f"🌐 API URL: {Url_Api}")

        # 2️⃣ Send GET request
        try:
            # print("📡 Sending GET request to API...")
            result = self.make_request(Url_Api, "GET")
            # print(f"📥 Raw API response: {result}")
        except Exception as e:
            # print(f"❌ Exception during API request: {e}")
            return {"session": False, "scenarios": []}

        # 3️⃣ Handle response
        try:
            # print("🔄 Handling API response...")
            response = self._handle_response( result,  {"session": False, "scenarios": []}, {"session": False, "scenarios": []} )
            # print(f"🔍 Final handled response: {response}")
            return response
        except Exception as e:
            # print(f"❌ Exception while handling response: {e}")
            return {"session": False, "scenarios": []}


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


