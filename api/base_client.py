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
    from core import EncryptionService
    from Log import DevLogger
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")


class APIManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # Désactive vérif SSL (warning mais volontaire)

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        self.session.headers.update(Settings.HEADER)

    # --------------------- Requêtes HTTP ---------------------
    def make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30
    ):

        print("\n================= 🌐 MAKE REQUEST =================")

        # URL sécurisée
        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith('_') else endpoint
        last_exception = None

        print(f"🔗 Endpoint : {endpoint}")
        print(f"🌍 URL finale : {url}")
        print(f"🧭 Méthode : {method}")
        print(f"⏱️ Timeout : {timeout}s")

        if params:
            print(f"📎 Params : {params}")
        if data:
            print(f"📦 Data : {data}")
        if json_data:
            print(f"📦 JSON : {json_data}")

        DevLogger.debug(f"URL={url} | METHOD={method} | PARAMS={params} | DATA={data} | JSON={json_data}")

        # ================= Retry =================
        for attempt in range(1, 4):
            print(f"\n🔁 Tentative {attempt}/3")
            DevLogger.debug(f"🌐 Tentative {attempt} - {method} {url}")

            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    data=data,
                    json=json_data,
                    params=params,
                    timeout=timeout
                )

                print(f"📥 Status HTTP : {response.status_code}")
                DevLogger.debug(f"📥 HTTP {response.status_code}")

                # ================= SUCCESS =================
                if response.status_code == 200:
                    print("✅ Réponse HTTP 200 reçue")

                    try:
                        json_resp = response.json()
                        print("📄 Réponse JSON :")
                        print(json_resp)
                        return {
                            "status": "success",
                            "data": json_resp,
                            "status_code": 200
                        }

                    except json.JSONDecodeError:
                        print("⚠️ Réponse non JSON (texte brut)")
                        print(response.text[:300])
                        return {
                            "status": "success",
                            "data": response.text,
                            "status_code": 200
                        }

                # ================= AUTH ERROR =================
                elif response.status_code in (401, 403):
                    print("❌ Accès refusé (401/403)")
                    DevLogger.error(f"Accès refusé HTTP {response.status_code}")

                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: accès refusé",
                        "status_code": response.status_code
                    }

                # ================= OTHER ERRORS =================
                else:
                    last_exception = f"HTTP {response.status_code}"
                    print(f"⚠️ Erreur HTTP {response.status_code}")
                    print(f"📄 Réponse (tronquée) : {response.text[:200]}")
                    DevLogger.warning(
                        f"⚠️ HTTP {response.status_code} - réponse tronquée: {response.text[:100]}"
                    )

            except requests.RequestException as e:
                last_exception = str(e)
                print("🔥 Exception RequestException")
                print(f"❌ Détail : {last_exception}")
                DevLogger.warning(f"⚠️ Erreur tentative {attempt}: {last_exception}")

            # ================= WAIT RETRY =================
            if attempt < 3:
                print("⏳ Attente avant nouvelle tentative (2s)...")
                time.sleep(2)

        # ================= FAILED AFTER RETRIES =================
        print("❌ Échec après 3 tentatives")
        print(f"🧨 Dernière erreur : {last_exception}")
        DevLogger.error(f"Échec après 3 tentatives: {last_exception}")

        print("================= ❌ FIN MAKE REQUEST =================\n")

        return {
            "status": "error",
            "error": f"Échec après 3 tentatives: {last_exception}",
            "status_code": None
        }

   
   
    # --------------------- Gestion de réponse ---------------------
    def _handle_response(
        self,
        result: Dict[str, Any],
        success_default: Any = None,
        failure_default: Any = None
    ) -> Any:
        if result.get("status") == "success":
            return result.get("data", success_default)
        else:
            DevLogger.error(f"❌ API Error: {result.get('error')}")
            return failure_default

    # --------------------- Méthodes API ---------------------
    def save_email(self, params: Dict[str, Any]) -> str:
        # ❌ Ne jamais logger params contenant emails
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

    def load_scenarios(self, encrypted_key: str) -> Dict[str, Any]:
        payload = {"encrypted": encrypted_key}
        result = self.make_request("_LOAD_SCENARIOS_API", "POST", json_data=payload)
        return self._handle_response(result, {"session": False, "scenarios": []},
                                     {"session": False, "scenarios": []})

    def handle_save_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        print("\n================= 💾 HANDLE SAVE SCENARIO =================")
        DevLogger.info("💾 Début sauvegarde scénario")

        # 1️⃣ Affichage des données envoyées
        print("📤 Payload envoyé à l'API :")
        print(payload)
        DevLogger.debug(f"Payload envoyé : {payload}")

        # 2️⃣ Appel API
        print("🌐 Appel API : _HANDLE_SAVE_API (POST)")
        result = self.make_request("_HANDLE_SAVE_API", "POST", json_data=payload)

        # 3️⃣ Affichage réponse brute
        print("📥 Réponse brute de l'API :")
        print(result)
        DevLogger.debug(f"Réponse brute API : {result}")

        # 4️⃣ Traitement de la réponse
        response = self._handle_response(
            result,
            {"success": True},
            {"success": False, "error": "Format de réponse invalide"}
        )

        # 5️⃣ Résultat final
        print("✅ Résultat final après traitement :")
        print(response)

        if response.get("success"):
            DevLogger.info("✅ Scénario sauvegardé avec succès")
        else:
            DevLogger.error(f"❌ Échec sauvegarde scénario : {response}")

        print("================= ✅ FIN HANDLE SAVE =================\n")
        return response


    def on_scenario_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.make_request("_ON_SCENARIO_CHANGED_API", "POST", json_data=payload)
        return self._handle_response(result, {"success": True},
                                     {"success": False, "error": "Format de réponse invalide"})

    def check_extension_update(self) -> Dict[str, Any]:
        # ❌ Ne jamais logger login/password
        DATA = {"login": "rep.test", "password": "zsGEnntKD5q2Brp68yxT"}
        encrypted = EncryptionService.encrypt_message(json.dumps(DATA), Settings.KEY)
        url = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted}"
        result = self.make_request(url, "GET")
        return self._handle_response(result, {})


# ==========================================================
# Instance globale
# ==========================================================
APIManager = APIManager()
