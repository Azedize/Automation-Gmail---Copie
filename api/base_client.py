# ==========================================================
# api/safe_api_manager.py
# ApiClient sécurisé avec des journaux détaillés
# ==========================================================

import os
import sys
import json
import time
import traceback
import requests
import re
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from core.encryption import EncryptionService
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__}: {e}")
    sys.exit(1)  


class ApiClient:
    MAX_REQUEST_ATTEMPTS = 3

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = Settings.VERIFY_SSL
        retries = Retry(total=0)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.headers.update(Settings.HEADER)
        Settings.write_log_event(  "api_client_initialized",  "INFO", verify_ssl=self.session.verify, retry_attempts=self.MAX_REQUEST_ATTEMPTS)

    # --------------------- Requête HTTP ---------------------

    def makeRequest( self,  endpoint: str, method: str = "POST",  data: Optional[Dict] = None,  json_data: Optional[Dict] = None, params: Optional[Dict] = None,  headers: Optional[Dict] = None, timeout: int = 30 ) -> Dict[str, Any]:
        url = ( Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith("_")   else endpoint  )
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        Settings.write_log_event("http_request_prepared", "INFO", endpoint=endpoint,  method=method.upper(),  has_data=bool(data),  has_json=bool(json_data),   has_params=bool(params), timeout_seconds=timeout )
        last_exception = None
        for attempt in range(1, self.MAX_REQUEST_ATTEMPTS + 1):
            try:
                Settings.write_log_event(  "http_request_started",  "INFO",  endpoint=endpoint,   method=method.upper(),   attempt=attempt,  max_attempts=self.MAX_REQUEST_ATTEMPTS )
                response = self.session.request(  method=method.upper(),   url=url,  data=data, json=json_data,  params=params,   headers=req_headers,timeout=timeout, )
                Settings.write_log_event( "http_response_received", "INFO",  method=method.upper(),   status_code=response.status_code, response_size=len(response.content),  content_type=response.headers.get("Content-Type", "unknown"),)

                if response.status_code == 200:
                    try:
                        parsed = response.json()
                        Settings.write_log_event(  "http_json_parsed", "INFO",  response_type=type(parsed).__name__, item_count=len(parsed) if hasattr(parsed, "__len__") else None )
                        return {"status": "success", "data": parsed, "status_code": 200}
                    except json.JSONDecodeError:
                        Settings.write_log_event( "http_json_decode_failed", "WARNING"  )
                        return {"status": "success", "data": response.text, "status_code": 200}
                elif response.status_code in (401, 403):
                    Settings.write_log_event( "http_authentication_failed", "WARNING", endpoint=endpoint, status_code=response.status_code,  action="verify credentials or session" )
                    return {"status": "error", "error": f"HTTP {response.status_code}: Access denied / session expired", "status_code": response.status_code}

                else:
                    last_exception = f"HTTP {response.status_code}"
                    Settings.write_log_event(  "http_request_failed", "WARNING",  status_code=response.status_code,  response_size=len(response.content) )
            except requests.RequestException as e:
                Settings.write_log_event(  "http_request_exception", "ERROR",  endpoint=endpoint, attempt=attempt,  exception_type=type(e).__name__ ,   error=str(e))
                last_exception = str(e)

            if attempt < self.MAX_REQUEST_ATTEMPTS:
                Settings.write_log_event( "http_request_retry_scheduled", "WARNING",  endpoint=endpoint,  next_attempt=attempt + 1,  delay_seconds=2 )
                time.sleep(2)

        Settings.write_log_event( "http_request_failed_final", "ERROR", endpoint=endpoint, attempts=self.MAX_REQUEST_ATTEMPTS, error=last_exception )
        return {"status": "error", "error": f"Failed after {self.MAX_REQUEST_ATTEMPTS} attempts: {last_exception}", "status_code": None}





    def handleResponse(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None):
        try:
            if not isinstance(result, dict):
                Settings.write_log_event(
                    "api_response_handler_failed",
                    "ERROR",
                    reason="invalid_response_type",
                    response_type=type(result).__name__,
                )
                return failure_default

            status = result.get("status")
            if status == "success":
                data = result.get("data", success_default)
                Settings.write_log_event( "api_response_handled",  "INFO",  status="success", data_type=type(data).__name__)
                return data
            else:
                Settings.write_log_event( "api_response_handled", "ERROR", status="error", status_code=result.get("status_code"),  error=result.get("error", "Unknown error"), )
                return failure_default
        except Exception as e:
            Settings.write_log_event("api_response_handler_failed", "ERROR",  exception_type=type(e).__name__,  error=str(e) )

            return failure_default

    

    def fetchScenarios(self, Url_Api) -> Dict[str, Any]:
        Settings.write_log_event( "scenarios_fetch_started",  "INFO", method="GET",  endpoint=Url_Api )
        try:
            result = self.makeRequest(Url_Api, "GET")
        except Exception as e:
            Settings.write_log_event( "scenarios_fetch_failed",  "ERROR", exception_type=type(e).__name__, error=str(e))
            return {"session": False, "scenarios": []}

        try:
            response = self.handleResponse(result, {"session": False, "scenarios": []}, {"session": False, "scenarios": []})
            Settings.write_log_event( "scenarios_fetch_completed",  "INFO", response_type=type(response).__name__,
                scenario_count=(
                    len(response.get("scenarios", []))
                    if isinstance(response, dict)  and isinstance(response.get("scenarios"), list)  else None
                ),
            )
            return response
        except Exception as e:
            Settings.write_log_event( "scenarios_response_processing_failed",  "ERROR",   exception_type=type(e).__name__, error=str(e) )
            return {"session": False, "scenarios": []}


    def saveProcess(self, params: Dict[str, Any]) -> int:
        result = self.makeRequest("_SAVE_PROCESS_API", "POST", json_data=params)
        data = self.handleResponse(result, {})
        if isinstance(data, dict) and data.get("status") is True:
            Settings.write_log_event( "process_saved", "INFO", has_inserted_id=bool(data.get("inserted_id")) )
            return data.get("inserted_id", -1)
        Settings.write_log_event("process_save_rejected", "WARNING")
        return -1

    def saveEmail(self, params: Dict[str, Any]) -> str:
        result = self.makeRequest("_SAVE_EMAIL_API", "POST", json_data=params)
        return str(self.handleResponse(result, ""))

    def sendStatus(self, params: Dict[str, Any]) -> str:
        Settings.write_log_event( "status_request_prepared", "INFO",  parameter_count=len(params) )
        result = self.makeRequest("_SEND_STATUS_API", "POST", json_data=params)
        Settings.write_log_event( "status_response_received", "INFO", response_type=type(result).__name__ )
        return str(self.handleResponse(result, ""))

    def handleSaveScenario(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
        Settings.write_log_event( "scenario_save_started", "INFO",  endpoint=Url_Api,  payload_type=type(payload).__name__, payload_field_count=len(payload) )
        result = self.makeRequest(Url_Api, "POST", data=payload)
        Settings.write_log_event( "save_scenario_response_received", "INFO",  status_code=result.get("status_code"),  status=result.get("status"),  response_type=type(result).__name__  )
        response = self.handleResponse(  result, {"success": True}, {"success": False, "error": "Format de réponse invalide"}, )
        Settings.write_log_event(  "save_scenario_response_processed",  "INFO", success=response.get("success") if isinstance(response, dict) else None, )
        return response



    def fetchProxyConfiguration(self, unique_ips: set, entity_New: str) -> Dict[str, Any]:
        try:
            Settings.write_log_event("proxy_configuration_fetch_started", "INFO",  entity=entity_New,  ip_count=len(unique_ips) )

            if not unique_ips:
                Settings.write_log_event( "proxy_configuration_input_invalid",  "ERROR", reason="no_ips_provided" )
                return {"valid": False, "data": None, "error": "No IPs provided"}
            k_proxy = ",".join(unique_ips) + "---" + entity_New
            params = {"m": "5454542z15szsdz4jklhjhdfz", "k": k_proxy}
            Settings.write_log_event("proxy_request_prepared", "INFO", parameter_count=len(params), ip_count=len(unique_ips) )
            headers = {"User-Agent": "Mozilla/5.0"}
            result = self.makeRequest(Settings.API_ENDPOINTS["__GET_PROXY_INFO__"],  method="POST",  data=params,  headers=headers,  timeout=30 )
            Settings.write_log_event(  "proxy_response_received", "INFO", status=result.get("status"),  status_code=result.get("status_code"),  response_type=type(result.get("data")).__name__ )
            if result.get("status") != "success":
                error_detail = ( result.get("error") or "Invalid response status from proxy service")
                Settings.write_log_event( "proxy_configuration_fetch_failed",  "ERROR",  stage="http_response",  status=result.get("status"),  status_code=result.get("status_code"),  error=error_detail )
                return {"valid": False, "data": None, "error": f"Données API non valides : {error_detail}"}

            response_text = result.get("data", "")
            response_size = len(response_text) if isinstance(response_text, str) else 0
            Settings.write_log_event("proxy_response_ready_for_decryption",  "INFO",  response_size_bytes=response_size )
            try:
                decrypted = EncryptionService.decrypt_message( response_text, Settings.API_KEY_PROXY  )
                Settings.write_log_event( "proxy_response_decrypted", "INFO", decrypted_size_bytes=len(decrypted) )
            except Exception as decrypt_error:
                Settings.write_log_event( "proxy_configuration_fetch_failed",  "ERROR", stage="decryption",  exception_type=type(decrypt_error).__name__ ,  error=str(decrypt_error))
                return {"valid": False, "data": None, "error": f"Decryption error: {str(decrypt_error)}"}
            decrypted = re.sub(r"[^\x20-\x7E]", "", decrypted)
            try:
                data = json.loads(decrypted)
                Settings.write_log_event(  "proxy_json_parsed",  "INFO", data_type=type(data).__name__,  key_count=len(data) if isinstance(data, dict) else None )
            except json.JSONDecodeError as json_error:
                Settings.write_log_event( "proxy_configuration_fetch_failed",  "ERROR",  stage="json_parse",  exception_type=type(json_error).__name__ ,  error=str(json_error) )
                return {"valid": False, "data": None, "error": f"JSON parsing error: {str(json_error)}"}

            if not isinstance(data, dict):
                Settings.write_log_event( "proxy_configuration_fetch_failed",  "ERROR",  stage="validation",   reason="response_data_not_object",  response_type=type(data).__name__,)
                return {"valid": False, "data": None, "error": "Invalid proxy response format"}

            api_ips = set(k.split("#")[0] for k in data.keys())
            missing = unique_ips - api_ips
            extra = api_ips - unique_ips
            Settings.write_log_event( "proxy_configuration_compared", "INFO",   expected_ip_count=len(unique_ips),  returned_ip_count=len(api_ips),  missing_ip_count=len(missing),  extra_ip_count=len(extra) )
            if missing:
                Settings.write_log_event(  "proxy_configuration_fetch_failed", "ERROR", stage="validation",  reason="missing_expected_ips", missing_ip_count=len(missing), response_key_count=len(data) if isinstance(data, dict) else None)
                return { "valid": False,  "data": data, "error": "Données du service non valides : certaines adresses IP attendues sont absentes de la réponse. Veuillez réessayer ou contacter le support si le problème persiste."}

            Settings.write_log_event( "proxy_configuration_fetch_completed", "INFO", ip_count=len(api_ips))
            return {"valid": True, "data": data, "error": None}

        except Exception as e:
            Settings.write_log_event( "proxy_configuration_fetch_failed",  "ERROR",  stage="unexpected", exception_type=type(e).__name__ ,  error=str(e), )
            return {"valid": False, "data": None, "error": str(e)}


# ==========================================================
# Instance globale
# ==========================================================
API_MANAGER = ApiClient()
