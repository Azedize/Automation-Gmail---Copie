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
    from api.base_client import API_MANAGER
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__}: {e}")
    sys.exit(1)  # quitte immédiatement le script avec un code d'erreur


class SessionManager:
    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.key = settings.KEY
        self.timezone = pytz.timezone("Africa/Casablanca")

    def checkSession(self) -> Dict:
        return self.check_session()

    def createSession(
        self,
        username: str,
        password: str,
        p_p_entity_Origine: str,
        p_entity_New: str,
        Id_USER,
    ) -> bool:
        return self.create_session(
            username, password, p_p_entity_Origine, p_entity_New, Id_USER
        )

    def clearSession(self):
        self.clear_session()

    def validateSessionWithApi(self, username: str, p_entity: str) -> Dict:
        return self.validate_session_with_api(username, p_entity)

    def checkSessionFull(self) -> Dict:
        return self.check_session_full()

    def checkApiCredentials(self, username: str, password: str) -> Union[tuple, int]:
        return self.check_api_credentials(username, password)

        # ================== Vérification session locale ==================
        #
        # Description :
        # Cette fonction vérifie la validité d’une session locale stockée
        # dans un fichier chiffré (session.txt).
        #
        # Objectif :
        # - Lire le fichier de session
        # - Déchiffrer son contenu
        # - Valider son format
        # - Vérifier que la session n’est pas expirée (moins de 2 jours)
        #
        # Étapes principales :
        #
        # 1) Initialisation :
        #    - Création d’un dictionnaire session_info avec :
        #         • valid (False par défaut)
        #         • username
        #         • password
        #         • date
        #         • p_entity
        #         • Id_User
        #         • error
        #
        # 2) Vérification existence fichier :
        #    - Vérifie si le fichier session existe.
        #    - Si inexistant → log WARNING + retour erreur "FileNotFound".
        #
        # 3) Lecture fichier :
        #    - Ouvre le fichier en mode lecture UTF-8.
        #    - Vérifie qu’il n’est pas vide.
        #    - Si vide → log WARNING + retour erreur "EmptyFile".
        #
        # 4) Déchiffrement :
        #    - Déchiffre le contenu avec EncryptionService.
        #
        # 5) Validation format :
        #    - Vérifie que les données respectent le format attendu
        #      via ValidationUtils.validate_session_format().
        #    - Si format invalide → log WARNING + erreur "InvalidFormat".
        #
        # 6) Extraction données :
        #    - Récupère :
        #         • username
        #         • password
        #         • date (string)
        #         • entity
        #         • Id_User
        #
        # 7) Vérification expiration :
        #    - Convertit la date string en datetime.
        #    - Applique le timezone configuré.
        #    - Compare avec la date actuelle.
        #    - Si différence < 2 jours → session valide.
        #    - Sinon → log WARNING + erreur "Expired".
        #
        # 8) Gestion erreurs :
        #    - Capture toute exception lors de la lecture/déchiffrement.
        #    - Log l’erreur et retourne "FileReadError".
        #
        # Retour :
        #    - Dictionnaire session_info contenant :
        #         • valid = True/False
        #         • informations utilisateur si valide
        #         • code erreur si invalide
        #
        # ================================================================

    def check_session(self) -> Dict:
        session_info = {
            "valid": False,
            "username": None,
            "password": None,
            "date": None,
            "p_entity_Origine": None,
            "p_entity_Nouveau": None,
            "error": None,
        }

        settings.write_log_event(
            "session_validation_started",
            "INFO",
            session_file_present=ValidationUtils.pathExists(self.session_path),
        )

        if not ValidationUtils.pathExists(self.session_path):
            settings.write_log_event(
                "session_validation_failed",
                "WARNING",
                reason="file_not_found",
            )
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                settings.write_log_event(
                    "session_validation_failed",
                    "WARNING",
                    reason="empty_file",
                )
                session_info["error"] = "EmptyFile"
                return session_info

            decrypted = EncryptionService.decrypt_message(encrypted, self.key)
            # print("decrypted" , decrypted)

            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            # print("data session :" , data)
            if not is_valid:
                settings.write_log_event(
                    "session_validation_failed",
                    "WARNING",
                    reason="invalid_format",
                )
                session_info["error"] = "InvalidFormat"
                return session_info

            (
                username,
                password,
                date_str,
                p_p_entity_Origine,
                p_entity_Nouveau,
                Id_User,
            ) = (
                data["username"],
                data["password"],
                data["date"],
                data["p_entity_Origine"],
                data["p_entity_Nouveau"],
                data["Id_User"],
            )

            # print("🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​username:", username,"password : ", password , "date_str:", date_str, "p_p_entity_Origine:", p_p_entity_Origine, "p_entity_Nouveau", p_entity_Nouveau, "Id_User", Id_User )

            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            last_session = self.timezone.localize(last_session)
            now = datetime.datetime.now(self.timezone)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update(
                    {
                        "valid": True,
                        "username": username,
                        "password": password,
                        "date": last_session,
                        "p_entity_Origine": p_p_entity_Origine,
                        "p_entity_Nouveau": p_entity_Nouveau,
                        "Id_User": Id_User,
                    }
                )
                settings.write_log_event(
                    "session_validation_succeeded",
                    "INFO",
                    has_username=bool(username),
                    has_entity=bool(p_entity_Nouveau),
                )
            else:
                settings.write_log_event(
                    "session_validation_failed",
                    "WARNING",
                    reason="expired",
                )
                session_info["error"] = "Expired"

        except Exception as e:
            # print(f"[ERROR] Lecture fichier session : {e}")
            session_info["error"] = f"FileReadError: {e}"
            settings.write_log_event(
                "session_validation_failed",
                "ERROR",
                reason="read_or_decrypt_error",
                exception_type=type(e).__name__,
                error=str(e),
            )

        return session_info

    # ================== Création de session ==================
    def create_session(  self,  username: str, password: str,  p_p_entity_Origine: str, p_entity_New: str,  Id_USER, ) -> bool:
        try:
            now = datetime.datetime.now(self.timezone)
            session_data = f"{username}::{password}::{now.strftime('%Y-%m-%d %H:%M:%S')}::{p_p_entity_Origine}::{p_entity_New}::{Id_USER}"

            encrypted = EncryptionService.encrypt_message(session_data, self.key)

            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)

            settings.write_log_event(
                "session_created",
                "INFO",
                has_username=bool(username),
                has_entity=bool(p_entity_New),
                session_age_seconds=int((datetime.datetime.now(self.timezone) - now).total_seconds()),
            )
            return True
        except Exception as e:
            settings.write_log_event(
                "session_creation_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
            )
            return False

    # ================== Suppression de session ==================
    def clear_session(self):
        if ValidationUtils.pathExists(self.session_path):
            try:
                os.remove(self.session_path)
                settings.write_log_event("session_cleared", "INFO")

            except Exception as e:
                settings.write_log_event(
                    "session_clear_failed",
                    "ERROR",
                    exception_type=type(e).__name__,
                    error=str(e),
                )
        else:
            settings.write_log_event("session_clear_skipped", "INFO", reason="file_not_found")

    # ================== Validation via API ==================
    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        try:
            params = {
                "k": "mP5QXYrK9E67Y",
                "rID": "4",
                "u": username,
                "entity": p_entity,
                "rv4": "1",
            }

            result = API_MANAGER.makeRequest(
                "_MAIN_API", method="GET", params=params, timeout=10
            )
            # print(f"🤖🤖 Résultat brut de l'API : {result}")

            if result.get("status") != "success":
                settings.write_log_event(
                    "session_api_validation_failed",
                    "ERROR",
                    reason="api_request_failed",
                    status=result.get("status"),
                    status_code=result.get("status_code"),
                )
                return {
                    "valid": False,
                    "error": result.get("error", "ApiRequestFailed"),
                }

            # --- Correction : vérifier le type de 'data' ---
            raw_data = result.get("data")
            if isinstance(raw_data, dict):
                data = raw_data.get("data")
            else:
                data = raw_data  # si c'est déjà une string (comme ton exemple)

            if not data or not isinstance(data, (str, bytes)):
                return {"valid": False, "error": "ApiRejected"}

            # --- Décryptage ---
            try:
                # print(f"🔐 Tentative de décryptage (length={len(data)})...")
                decrypted = EncryptionService.decrypt_message(data, self.key)
                # print(f"✅ Décrypté : {decrypted}")

                if ";" not in decrypted:
                    settings.write_log_event(
                        "session_api_validation_failed",
                        "WARNING",
                        reason="invalid_decrypted_format",
                    )
                    return {"valid": False, "error": "InvalidDecryptedFormat"}

                id_user_str, entity = decrypted.split(";", 1)

                try:
                    id_user = int(id_user_str)
                except ValueError:
                    settings.write_log_event(
                        "session_api_validation_failed",
                        "WARNING",
                        reason="invalid_user_id",
                    )
                    return {"valid": False, "error": "InvalidUserId"}

                if id_user < 0 or not entity:
                    return {"valid": False, "error": "InvalidUserData"}

                settings.write_log_event(
                    "session_api_validation_succeeded",
                    "INFO",
                    has_entity=bool(entity),
                )
                return {"valid": True}

            except Exception as e_decrypt:
                settings.write_log_event(
                    "session_api_validation_failed",
                    "ERROR",
                    reason="decryption_error",
                    exception_type=type(e_decrypt).__name__,
                    error=str(e_decrypt),
                )
                return {"valid": False, "error": "DecryptionFailed"}

        except Exception as e_api:
            settings.write_log_event(
                "session_api_validation_failed",
                "ERROR",
                reason="unexpected_error",
                exception_type=type(e_api).__name__,
                error=str(e_api),
            )
            return {"valid": False, "error": str(e_api)}

    # ================== Vérification complète ==================
    def check_session_full(self) -> Dict:
        session_info = self.check_session()
        if not session_info["valid"]:
            # print("[SESSION] ❌ Session locale invalide")
            settings.write_log_event(
                "full_session_validation_failed",
                "WARNING",
                stage="local",
                error_code=session_info.get("error"),
            )
            return session_info

        # print("[SESSION] ✅ Session locale valide, vérification API...")
        settings.write_log_event("full_session_api_validation_started", "INFO")
        api_result = self.validate_session_with_api(
            session_info["username"], session_info["p_entity_Origine"]
        )
        #  affiche api result
        # print(f"[SESSION] Résultat validation API : {api_result}")

        if not api_result.get("valid"):
            # print("[SESSION] ❌ Session refusée par l’API")
            settings.write_log_event(
                "full_session_validation_failed",
                "WARNING",
                stage="api",
                error_code=api_result.get("error"),
            )
            session_info["valid"] = False
            session_info["error"] = api_result.get("error", "ApiValidationFailed")
            return session_info

        # print("[SESSION] ✅ Session validée (LOCAL + API)")
        settings.write_log_event("full_session_validation_succeeded", "INFO")
        return session_info

    # ================== Vérification credentials API ==================
    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:

        try:
            # print(f"[DEBUG] Début de check_api_credentials")
            # settings.write_log_dev_file(f"Début check_api_credentials: username='{username}', password='{'*' * len(password)}'", "DEBUG")

            # Validation username
            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(
                username, validator_type="text", min_length=5
            )
            if not valid_user:
                settings.write_log_event(
                    "credentials_validation_failed",
                    "ERROR",
                    field="username",
                    reason=str(msg_user),
                )
                return -1

            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(
                password, min_length=6
            )
            if not valid_pass:
                settings.write_log_event(
                    "credentials_validation_failed",
                    "ERROR",
                    field="password",
                    reason=str(msg_pass),
                )
                return -1

            settings.write_log_event("credentials_validation_succeeded", "DEBUG")

            # Préparation payload API
            payload = {
                "rID": "1",
                "u": username,
                "p": password,
                "k": "mP5QXYrK9E67Y",
                "l": "1",
            }
            # print(f"[DEBUG] Payload API préparé: {payload}")
            settings.write_log_event( "authentication_request_prepared", "DEBUG", parameter_count=len(payload) )

            resp = None
            for attempt in range(1, 6):
                # print(f"[DEBUG] Tentative API {attempt}/5...")
                settings.write_log_dev_file(f"Tentative {attempt}/5", "DEBUG")
                try:
                    result = API_MANAGER.makeRequest("_APIACCESS_API", method="POST", data=payload, timeout=10)
                    # print(f"➡️​➡️​➡️​➡️​➡️​➡️​➡️​➡️​➡️​ [DEBUG] Réponse brute API: {result}")
                    resp = API_MANAGER.handleResponse(result, failure_default=None)
                    # print(f"[DEBUG] Réponse traitée API: {resp}")

                    if resp is not None:
                        settings.write_log_event(
                            "credentials_api_response_received",
                            "DEBUG",
                            attempt=attempt,
                            response_size=len(str(resp)) if resp is not None else 0,
                        )
                        break
                except Exception as e:
                    settings.write_log_event(
                        "credentials_api_request_failed",
                        "ERROR",
                        attempt=attempt,
                        exception_type=type(e).__name__,
                        error=str(e),
                    )
                time.sleep(2)
            else:
                settings.write_log_event(
                    "credentials_api_request_failed",
                    "ERROR",
                    reason="max_attempts_exceeded",
                    attempts=5,
                )
                return -3

            if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                settings.write_log_event(
                    "credentials_api_error_code_received",
                    "DEBUG",
                    code=resp,
                )
                return int(resp)

            # Décryptage et séparation idUser / entity
            try:
                # print(f"[DEBUG] Tentative de décryptage de la réponse API (length={len(resp) if resp else 0})...")
                decrypted = EncryptionService.decrypt_message(resp, self.key)
                # print(f"[DEBUG] Décrypté: {decrypted}")

                if not decrypted or ";" not in decrypted:
                    settings.write_log_event(
                        "credentials_response_invalid",
                        "ERROR",
                        reason="invalid_or_unexpected_format",
                    )
                    return -4

                id_user, entity = decrypted.split(";", 1)  # split une seule fois
                settings.write_log_event(
                    "credentials_response_decrypted",
                    "DEBUG",
                    has_user_id=bool(id_user),
                    has_entity=bool(entity),
                )
                return (id_user, entity)

            except Exception as e:
                settings.write_log_event(
                    "credentials_response_decryption_failed",
                    "ERROR",
                    exception_type=type(e).__name__,
                    error=str(e),
                )
                return -5

        except Exception as e:
            settings.write_log_event(
                "credentials_validation_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
            )
            return -5


# ==========================================================
# Instance globale
# ==========================================================
SessionManager = SessionManager()


# le programme is runing dans une interface logique et capable de renitailiser l'interface
# si on est dans un script il faut utiliser la function suivante :
