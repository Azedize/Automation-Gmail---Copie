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

# Détermine la racine du projet à partir de l'emplacement de ce fichier.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    # Service responsable du chiffrement et du déchiffrement des données sensibles.
    from core.encryption import EncryptionService

    # Configuration globale de l'application.
    from config import settings

    # Utilitaires centralisés pour la validation des données et des chemins.
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    # Une dépendance essentielle manque : l'application ne peut pas continuer.
    print(f"Import error in file {__file__}: {e}")
    sys.exit(1)


class SessionManager:

    def __init__(self):
        # Chemin du fichier contenant la session chiffrée.
        self.session_path = settings.SESSION_PATH

        # Clé utilisée pour chiffrer et déchiffrer les données de session.
        self.key = settings.KEY

        # Toutes les opérations de date de session utilisent le fuseau horaire du Maroc.
        self.timezone = pytz.timezone("Africa/Casablanca")

    # ----------------------------------------------------------
    # Méthodes de compatibilité avec les anciennes conventions.
    # Elles redirigent vers les méthodes utilisant snake_case.
    # ----------------------------------------------------------

    def checkSession(self) -> Dict:
        # Conserve la compatibilité avec l'ancien nom de méthode.
        return self.check_session()

    def createSession(self, username: str, password: str, p_p_entity_Origine: str, p_entity_New: str, Id_USER) -> bool:
        # Conserve la compatibilité avec l'ancien nom de méthode.
        return self.create_session(username, password, p_p_entity_Origine, p_entity_New, Id_USER)

    def clearSession(self):
        # Redirige vers la méthode de suppression de session.
        self.clear_session()

    def validateSessionWithApi(self, username: str, p_entity: str) -> Dict:
        # Redirige vers la validation distante de la session.
        return self.validate_session_with_api(username, p_entity)

    def checkSessionFull(self) -> Dict:
        # Effectue la validation locale puis la validation API.
        return self.check_session_full()

    def checkApiCredentials(self, username: str, password: str) -> Union[tuple, int]:
        # Redirige vers la validation des identifiants auprès de l'API.
        return self.check_api_credentials(username, password)

    # ==========================================================
    # VALIDATION DE LA SESSION LOCALE
    # ==========================================================

    def check_session(self) -> Dict:
        # Structure par défaut retournée lorsque la session n'est pas valide.
        session_info = {"valid": False, "username": None, "password": None, "date": None, "p_entity_Origine": None, "p_entity_Nouveau": None, "error": None}

        # Vérifie d'abord si le fichier de session existe.
        session_file_present = ValidationUtils.pathExists(self.session_path)
        settings.write_log_event("session_validation_started", "INFO", session_file_present=session_file_present)

        # Une session inexistante signifie qu'aucune session locale n'est disponible.
        if not session_file_present:
            settings.write_log_event("session_validation_failed", "WARNING", reason="file_not_found")
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            # Lit le contenu chiffré du fichier de session.
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            # Un fichier vide ne peut pas représenter une session valide.
            if not encrypted:
                settings.write_log_event("session_validation_failed", "WARNING", reason="empty_file")
                session_info["error"] = "EmptyFile"
                return session_info

            # Déchiffre les données avec la clé configurée.
            decrypted = EncryptionService.decrypt_message(encrypted, self.key)

            # Vérifie que les données déchiffrées respectent le format attendu.
            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            if not is_valid:
                settings.write_log_event("session_validation_failed", "WARNING", reason="invalid_format")
                session_info["error"] = "InvalidFormat"
                return session_info

            # Ces champs sont obligatoires pour considérer la session comme exploitable.
            required_fields = ("username", "password", "p_entity_Origine", "p_entity_Nouveau", "Id_User")

            # Vérifie que tous les champs obligatoires possèdent une valeur.
            if not all(data.get(field) for field in required_fields):
                settings.write_log_event("session_validation_failed", "WARNING", reason="empty_required_field")
                session_info["error"] = "EmptyRequiredField"
                return session_info

            # Extrait les informations validées de la structure de session.
            (username, password, date_str, p_p_entity_Origine, p_entity_Nouveau, Id_User) = (
                data["username"],
                data["password"],
                data["date"],
                data["p_entity_Origine"],
                data["p_entity_Nouveau"],
                data["Id_User"],
            )

            # Convertit la date texte en objet datetime.
            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            # Associe explicitement la date au fuseau horaire du Maroc.
            last_session = self.timezone.localize(last_session)

            # Récupère la date et l'heure actuelles dans le même fuseau horaire.
            now = datetime.datetime.now(self.timezone)

            # Calcule l'âge exact de la session.
            session_age = now - last_session

            # Une session est valide si elle n'est pas dans le futur et a moins de deux jours.
            if datetime.timedelta(0) <= session_age < datetime.timedelta(days=2):
                session_info.update(
                    {"valid": True, "username": username, "password": password, "date": last_session, "p_entity_Origine": p_p_entity_Origine, "p_entity_Nouveau": p_entity_Nouveau, "Id_User": Id_User}
                )

                # Journalise uniquement des informations non sensibles.
                settings.write_log_event("session_validation_succeeded", "INFO", has_username=bool(username), has_entity=bool(p_entity_Nouveau))

            # Une date future indique une session incohérente.
            elif session_age < datetime.timedelta(0):
                settings.write_log_event("session_validation_failed", "WARNING", reason="future_date")
                session_info["error"] = "FutureDate"

            # Toute session âgée de deux jours ou plus est considérée comme expirée.
            else:
                settings.write_log_event("session_validation_failed", "WARNING", reason="expired")
                session_info["error"] = "Expired"

        except Exception as e:
            # Capture le type et le message de l'erreur sans enregistrer les données sensibles.
            session_info["error"] = f"FileReadError: {e}"
            settings.write_log_event("session_validation_failed", "ERROR", reason="read_or_decrypt_error", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

        return session_info

    # ==========================================================
    # CRÉATION DE LA SESSION LOCALE
    # ==========================================================

    def create_session(self, username: str, password: str, p_p_entity_Origine: str, p_entity_New: str, Id_USER) -> bool:
        try:
            # Génère l'heure de création de la session dans le fuseau du Maroc.
            now = datetime.datetime.now(self.timezone)

            # Construit la structure interne de la session avant chiffrement.
            session_data = f"{username}::{password}::{now.strftime('%Y-%m-%d %H:%M:%S')}" f"::{p_p_entity_Origine}::{p_entity_New}::{Id_USER}"

            # Chiffre la totalité des données avant de les écrire sur le disque.
            encrypted = EncryptionService.encrypt_message(session_data, self.key)

            # Une réponse vide signifie que le chiffrement n'a pas produit de session.
            if not encrypted:
                settings.write_log_event("session_creation_failed", "ERROR", reason="encryption_empty")
                return False

            # Crée le dossier de session s'il n'existe pas encore.
            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)

            # Écrit uniquement la version chiffrée dans le fichier local.
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)

            # Journalise uniquement les métadonnées non sensibles de l'opération.
            settings.write_log_event(
                "session_created", "INFO", has_username=bool(username), has_entity=bool(p_entity_New), session_age_seconds=int((datetime.datetime.now(self.timezone) - now).total_seconds())
            )
            return True

        except Exception as e:
            # Enregistre l'erreur complète pour faciliter le diagnostic développeur.
            settings.write_log_event("session_creation_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())
            return False

    # ==========================================================
    # SUPPRESSION DE LA SESSION LOCALE
    # ==========================================================

    def clear_session(self):
        # Vérifie que le fichier de session existe avant de tenter sa suppression.
        if ValidationUtils.pathExists(self.session_path):
            try:
                # Supprime définitivement le fichier de session locale.
                os.remove(self.session_path)

                settings.write_log_event("session_cleared", "INFO")

            except Exception as e:
                # Enregistre le détail complet de l'exception.
                settings.write_log_event("session_clear_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())
        else:
            # Aucun fichier n'existe : aucune suppression n'est nécessaire.
            settings.write_log_event("session_clear_skipped", "INFO", reason="file_not_found")

    # ==========================================================
    # VALIDATION DE LA SESSION AVEC L'API
    # ==========================================================

    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        try:
            # Import différé pour éviter de charger le gestionnaire API inutilement.
            from api.base_client import API_MANAGER

            # Prépare les paramètres nécessaires à la validation distante.
            params = {"k": settings.SESSION_API_KEY, "rID": settings.SESSION_VALIDATION_REQUEST_ID, "u": username, "entity": p_entity, "rv4": settings.SESSION_APP_VERSION}

            # Envoie une requête GET vers l'API principale de validation.
            result = API_MANAGER.makeRequest("_MAIN_API", method="GET", params=params, timeout=10)

            # Une réponse non dictionnaire ne respecte pas le contrat attendu.
            if not isinstance(result, dict):
                settings.write_log_event("session_api_validation_failed", "ERROR", reason="invalid_response_type", response_type=type(result).__name__)
                return {"valid": False, "error": "ApiRequestFailed"}

            # Vérifie le statut global retourné par l'API.
            if result.get("status") != "success":
                settings.write_log_event("session_api_validation_failed", "ERROR", reason="api_request_failed", status=result.get("status"), status_code=result.get("status_code"))
                return {"valid": False, "error": result.get("error", "ApiRequestFailed")}

            # Récupère les données renvoyées par l'API.
            raw_data = result.get("data")

            # Certaines réponses contiennent un niveau supplémentaire "data".
            if isinstance(raw_data, dict):
                data = raw_data.get("data")
            else:
                data = raw_data

            # Les données doivent être une chaîne ou des bytes chiffrés.
            if not data or not isinstance(data, (str, bytes)):
                return {"valid": False, "error": "ApiRejected"}

            try:
                # Convertit les bytes en texte avant le déchiffrement.
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                # Le format attendu après déchiffrement est : ID_USER;ENTITY.
                if ";" not in data:
                    settings.write_log_event("session_api_validation_failed", "WARNING", reason="invalid_decrypted_format")
                    return {"valid": False, "error": "InvalidDecryptedFormat"}

                # Sépare l'identifiant utilisateur et l'entity.
                id_user_str, entity = data.split(";", 1)

                try:
                    # Convertit l'identifiant texte en entier.
                    id_user = int(id_user_str)
                except ValueError:
                    settings.write_log_event("session_api_validation_failed", "WARNING", reason="invalid_user_id")
                    return {"valid": False, "error": "InvalidUserId"}

                # Refuse un identifiant négatif ou une entity vide.
                if id_user < 0 or not entity:
                    return {"valid": False, "error": "InvalidUserData"}

                settings.write_log_event("session_api_validation_succeeded", "INFO", has_entity=bool(entity))
                return {"valid": True}

            except Exception as e_decrypt:
                # Capture le détail complet des erreurs de déchiffrement ou de parsing.
                settings.write_log_event(
                    "session_api_validation_failed", "ERROR", reason="decryption_error", exception_type=type(e_decrypt).__name__, error=str(e_decrypt), traceback=traceback.format_exc()
                )
                return {"valid": False, "error": "DecryptionFailed"}

        except Exception as e_api:
            # Capture toute erreur inattendue provenant de l'appel API.
            settings.write_log_event("session_api_validation_failed", "ERROR", reason="unexpected_error", exception_type=type(e_api).__name__, error=str(e_api), traceback=traceback.format_exc())
            return {"valid": False, "error": str(e_api)}

    # ==========================================================
    # VALIDATION COMPLÈTE : SESSION LOCALE + API
    # ==========================================================

    def check_session_full(self) -> Dict:
        # Première étape : validation de la session enregistrée localement.
        session_info = self.check_session()

        # Si la validation locale échoue, aucune requête API supplémentaire n'est nécessaire.
        if not session_info["valid"]:
            settings.write_log_event("full_session_validation_failed", "WARNING", stage="local", error_code=session_info.get("error"))
            return session_info

        # La session locale est valide : passage à la validation distante.
        settings.write_log_event("full_session_api_validation_started", "INFO")

        api_result = self.validate_session_with_api(session_info["username"], session_info["p_entity_Origine"])

        # L'API peut refuser une session encore valide localement.
        if not api_result.get("valid"):
            settings.write_log_event("full_session_validation_failed", "WARNING", stage="api", error_code=api_result.get("error"))
            session_info["valid"] = False
            session_info["error"] = api_result.get("error", "ApiValidationFailed")
            return session_info

        # Les deux validations ont réussi.
        settings.write_log_event("full_session_validation_succeeded", "INFO")
        return session_info

    # ==========================================================
    # VALIDATION DES IDENTIFIANTS AVEC L'API
    # ==========================================================

    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:
        try:
            # Import différé du gestionnaire API.
            from api.base_client import API_MANAGER

            # Vérifie la longueur minimale du nom utilisateur.
            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(username, validator_type="text", min_length=5)

            if not valid_user:
                settings.write_log_event("credentials_validation_failed", "ERROR", field="username", reason=str(msg_user))
                return -1

            # Vérifie la longueur minimale du mot de passe.
            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(password, min_length=6)

            if not valid_pass:
                settings.write_log_event("credentials_validation_failed", "ERROR", field="password", reason=str(msg_pass))
                return -1

            settings.write_log_event("credentials_validation_succeeded", "DEBUG")

            # Prépare les paramètres d'authentification sans les écrire dans les logs.
            payload = {"rID": settings.SESSION_AUTHENTICATION_REQUEST_ID, "u": username, "p": password, "k": settings.SESSION_API_KEY, "l": settings.SESSION_AUTHENTICATION_LOGIN}

            # Journalise uniquement le nombre de paramètres et jamais leur contenu.
            settings.write_log_event("authentication_request_prepared", "DEBUG", parameter_count=len(payload))

            resp = None

            # Effectue jusqu'à cinq tentatives en cas d'échec réseau ou API.
            for attempt in range(1, 6):
                settings.write_log_dev_file(f"Attempt {attempt}/5", "DEBUG")

                try:
                    # Envoie les credentials vers l'API d'authentification.
                    result = API_MANAGER.makeRequest("_APIACCESS_API", method="POST", data=payload, timeout=10)

                    # Normalise la réponse API selon la logique centrale du client.
                    resp = API_MANAGER.handleResponse(result, failure_default=None)

                    # Une réponse non nulle permet d'arrêter les tentatives.
                    if resp is not None:
                        settings.write_log_event("credentials_api_response_received", "DEBUG", attempt=attempt, response_size=len(str(resp)))
                        break

                except Exception as e:
                    # Enregistre l'erreur et sa stack trace complète pour le diagnostic.
                    settings.write_log_event("credentials_api_request_failed", "ERROR", attempt=attempt, exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

                # Attend deux secondes avant une nouvelle tentative.
                if attempt < 5:
                    time.sleep(2)

            else:
                # Le bloc else du for est exécuté uniquement si aucun break n'a eu lieu.
                settings.write_log_event("credentials_api_request_failed", "ERROR", reason="max_attempts_exceeded", attempts=5)
                return -3

            # Vérifie si l'API a retourné directement un code d'erreur.
            if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                settings.write_log_event("credentials_api_error_code_received", "DEBUG", code=resp)
                return int(resp)

            try:
                # Déchiffre la réponse positive retournée par l'API.
                decrypted = EncryptionService.decrypt_message(resp, self.key)

                # Vérifie que la réponse déchiffrée respecte le format attendu.
                if not decrypted or ";" not in decrypted:
                    settings.write_log_event("credentials_response_invalid", "ERROR", reason="invalid_or_unexpected_format")
                    return -4

                # Extrait l'identifiant utilisateur et l'entity.
                id_user, entity = decrypted.split(";", 1)

                # Journalise uniquement la présence des valeurs, jamais leur contenu.
                settings.write_log_event("credentials_response_decrypted", "DEBUG", has_user_id=bool(id_user), has_entity=bool(entity))

                return id_user, entity

            except Exception as e:
                # Capture les erreurs de déchiffrement avec leur stack trace complète.
                settings.write_log_event("credentials_response_decryption_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())
                return -5

        except Exception as e:
            # Capture toute erreur inattendue de la validation des credentials.
            settings.write_log_event("credentials_validation_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())
            return -5


# Instance globale utilisée par le reste de l'application.
# Cela permet d'appeler directement SessionManager.check_session(), etc.
SessionManager = SessionManager()
