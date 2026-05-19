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
    from api.base_client import APIManager
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)  # quitte immédiatement le script avec un code d'erreur


class SessionManager:

    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.key = settings.KEY
        self.timezone = pytz.timezone("Africa/Casablanca")

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
        session_info = {"valid": False, "username": None , "password": None, "date": None, "p_entity_Origine": None, "p_entity_Nouveau": None, "error": None}

        print(f"[INFO] Chemin du fichier session : {self.session_path}")

        if not ValidationUtils.path_exists(self.session_path):
            print("[WARNING] ❌ Le fichier session.txt n'existe pas")
            settings.WRITE_LOG_DEV_FILE("Le fichier session n'existe pas", "WARNING")
            session_info["error"] = "FileNotFound"
            return session_info

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            if not encrypted:
                print("[WARNING] ❌ Fichier session.txt vide")
                settings.WRITE_LOG_DEV_FILE("Le fichier session est vide", "WARNING")
                session_info["error"] = "EmptyFile"
                return session_info

            decrypted = EncryptionService.decrypt_message(encrypted, self.key)
            print("decrypted" , decrypted)

            is_valid, data = ValidationUtils.validate_session_format(decrypted)
            print("data session :" , data)
            if not is_valid:
                settings.WRITE_LOG_DEV_FILE("Format de session invalide", "WARNING")
                print("[ERROR] Format session invalide")
                session_info["error"] = "InvalidFormat"
                return session_info

            username,password, date_str, p_p_entity_Origine , p_entity_Nouveau , Id_User = data["username"],data["password"], data["date"], data["p_entity_Origine"], data["p_entity_Nouveau"] , data["Id_User"]

            print("🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​🎊​🎊​🎾​🏉​username:", username,"password : ", password , "date_str:", date_str, "p_p_entity_Origine:", p_p_entity_Origine, "p_entity_Nouveau", p_entity_Nouveau, "Id_User", Id_User ) 

            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            last_session = self.timezone.localize(last_session)
            now = datetime.datetime.now(self.timezone)

            if (now - last_session) < datetime.timedelta(days=2):
                session_info.update({"valid": True, "username": username , "password": password, "date": last_session, "p_entity_Origine": p_p_entity_Origine, "p_entity_Nouveau": p_entity_Nouveau, "Id_User": Id_User})
            else:
                settings.WRITE_LOG_DEV_FILE("Session expirée", "WARNING")
                print("[INFO] Session expirée")
                session_info["error"] = "Expired"

        except Exception as e:
            print(f"[ERROR] Lecture fichier session : {e}")
            session_info["error"] = f"FileReadError: {e}"
            settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la lecture du fichier session : {e}\n{traceback.format_exc()}", "ERROR")

        return session_info

    
    
    
    # ================== Création de session ==================
    def create_session(self, username: str,password: str, p_p_entity_Origine: str  , p_entity_New: str , Id_USER) -> bool:
        try:
            now = datetime.datetime.now(self.timezone)
            session_data = f"{username}::{password}::{now.strftime('%Y-%m-%d %H:%M:%S')}::{p_p_entity_Origine}::{p_entity_New}::{Id_USER}"

            encrypted = EncryptionService.encrypt_message(session_data, self.key)

            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)

            print(f"[INFO] Session créée pour '{username}'")
            settings.WRITE_LOG_DEV_FILE(f"Session crée pour '{username}'", "INFO")
            return True
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la création de la session : {e}\n{traceback.format_exc()}", "ERROR")
            print(f"[ERROR] Création session échouée : {e}")
            return False

    # ================== Suppression de session ==================
    def clear_session(self):
        if ValidationUtils.path_exists(self.session_path):
            try:
                os.remove(self.session_path)
                settings.WRITE_LOG_DEV_FILE("Session supprimée", "INFO")
                print("[INFO] Session supprimée")
                
            except Exception as e:
                settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la suppression de la session : {e}\n{traceback.format_exc()}", "ERROR")
                print(f"[ERROR] Suppression session échouée : {e}")
                settings.WRITE_LOG_DEV_FILE(f"[ERROR] Suppression session échouée : {e}", "ERROR")
        else:
            print("[INFO] Aucun fichier de session à supprimer")
            settings.WRITE_LOG_DEV_FILE("Aucun fichier de session à supprimer", "INFO")

    # ================== Validation via API ==================


    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        try:
            params = {
                "k": "mP5QXYrK9E67Y",
                "rID": "4",
                "u": username,
                "entity": p_entity,
                "rv4": "1"
            }

            result = APIManager.make_request('_MAIN_API', method="GET", params=params, timeout=10)
            print(f"🤖🤖 Résultat brut de l'API : {result}")

            if result.get("status") != "success":
                print(f"❌ API returned non-success status: {result.get('status')}")
                return {"valid": False, "error": result.get("error", "ApiRequestFailed")}

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
                print(f"🔐 Tentative de décryptage (length={len(data)})...")
                decrypted = EncryptionService.decrypt_message(data, self.key)
                print(f"✅ Décrypté : {decrypted}")

                if ";" not in decrypted:
                    print("⚠️ Décryptage invalide : format inattendu")
                    return {"valid": False, "error": "InvalidDecryptedFormat"}

                id_user_str, entity = decrypted.split(";", 1)

                try:
                    id_user = int(id_user_str)
                except ValueError:
                    print("⚠️ idUser non numérique après décryptage")
                    return {"valid": False, "error": "InvalidUserId"}

                if id_user < 0 or not entity:
                    return {"valid": False, "error": "InvalidUserData"}

                print(f"🎯 Validation réussie : idUser={id_user}, entity={entity}")
                return {"valid": True}

            except Exception as e_decrypt:
                print(f"💥 Exception lors du décryptage : {e_decrypt}")
                settings.WRITE_LOG_DEV_FILE(f"Exception lors du décryptage: {e_decrypt}\n{traceback.format_exc()}", "ERROR")
                traceback.print_exc()
                return {"valid": False, "error": "DecryptionFailed"}

        except Exception as e_api:
            print(f"⚠️ Validation API échouée : {e_api}")
            settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la validation de la session via l'API : {e_api}\n{traceback.format_exc()}", "ERROR")
            traceback.print_exc()
            return {"valid": False, "error": str(e_api)}


    # ================== Vérification complète ==================
    def check_session_full(self) -> Dict:
        session_info = self.check_session()
        if not session_info["valid"]:
            print("[SESSION] ❌ Session locale invalide")
            settings.WRITE_LOG_DEV_FILE(f"Session locale invalide: {session_info['error']}", "WARNING")
            return session_info

        print("[SESSION] ✅ Session locale valide, vérification API...")
        settings.WRITE_LOG_DEV_FILE("Session locale valide, étape API", "INFO")
        api_result = self.validate_session_with_api(session_info["username"], session_info["p_entity_Origine"])
        #  affiche api result
        print(f"[SESSION] Résultat validation API : {api_result}")

        if not api_result.get("valid"):
            print("[SESSION] ❌ Session refusée par l’API")
            settings.WRITE_LOG_DEV_FILE(f"Session refusée par l'API: {api_result['error']}", "WARNING")
            session_info["valid"] = False
            session_info["error"] = api_result.get("error", "ApiValidationFailed")
            return session_info

        print("[SESSION] ✅ Session validée (LOCAL + API)")
        settings.WRITE_LOG_DEV_FILE("Session validée (LOCAL + API)", "INFO")
        return session_info

    # ================== Vérification credentials API ==================
    def check_api_credentials(self, username: str, password: str) -> Union[tuple, int]:

        try:
            print(f"[DEBUG] Début de check_api_credentials")
            # settings.WRITE_LOG_DEV_FILE(f"Début check_api_credentials: username='{username}', password='{'*' * len(password)}'", "DEBUG")

            # Validation username
            valid_user, msg_user = ValidationUtils.validate_qlineedit_text(username, validator_type="text", min_length=5)
            if not valid_user:
                settings.WRITE_LOG_DEV_FILE(f"\u274c Username invalide: {msg_user}", "ERROR")
                return -1

            # Validation password
            valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(password, min_length=6)
            if not valid_pass:
                settings.WRITE_LOG_DEV_FILE(f"\u274c Password invalide: {msg_pass}", "ERROR")
                return -1

            settings.WRITE_LOG_DEV_FILE("Validation des inputs réussie", "DEBUG")
            print("[DEBUG] Validation inputs réussie")

            # Préparation payload API
            payload = {
                "rID": "1",
                "u": username,
                "p": password,
                "k": "mP5QXYrK9E67Y",
                "l": "1"
            }
            print(f"[DEBUG] Payload API préparé: {payload}")

            resp = None
            for attempt in range(1, 6):
                print(f"[DEBUG] Tentative API {attempt}/5...")
                settings.WRITE_LOG_DEV_FILE(f"Tentative {attempt}/5", "DEBUG")
                try:
                    result = APIManager.make_request("_APIACCESS_API", method="POST", data=payload, timeout=10)
                    print(f"➡️​➡️​➡️​➡️​➡️​➡️​➡️​➡️​➡️​ [DEBUG] Réponse brute API: {result}")
                    resp = APIManager._handle_response(result, failure_default=None)
                    print(f"[DEBUG] Réponse traitée API: {resp}")

                    if resp is not None:
                        settings.WRITE_LOG_DEV_FILE("Réponse API reçue", "DEBUG")
                        print("[DEBUG] Réponse API reçue")
                        break
                except Exception as e:
                    print(f"[ERROR] Exception lors de la requête API: {e}")
                    traceback.print_exc()
                    settings.WRITE_LOG_DEV_FILE(f"Exception lors de la requête API: {e}\n{traceback.format_exc()}", "ERROR")
                time.sleep(2)
            else:
                print("[ERROR] Connexion échouée après 5 tentatives")
                settings.WRITE_LOG_DEV_FILE("Connexion échouée après 5 tentatives", "ERROR")
                return -3

            # Vérification des codes d'erreur API
            if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
                print(f"[DEBUG] Code d'erreur API reçu: {resp}")
                return int(resp)

            # Décryptage et séparation idUser / entity
            try:
                print(f"[DEBUG] Tentative de décryptage de la réponse API (length={len(resp) if resp else 0})...")
                decrypted = EncryptionService.decrypt_message(resp, self.key)
                print(f"[DEBUG] Décrypté: {decrypted}")

                if not decrypted or ";" not in decrypted:
                    print("[ERROR] Décryptage invalide ou format inattendu")
                    return -4

                id_user, entity = decrypted.split(";", 1)  # split une seule fois
                print(f"[DEBUG] Décryptage réussi: idUser={id_user}, entity={entity}")
                return (id_user, entity)

            except Exception as e:
                print(f"[CRITICAL] Exception lors du décryptage: {e}")
                settings.WRITE_LOG_DEV_FILE(f"Exception lors du décryptage: {e}\n{traceback.format_exc()}", "ERROR")
                traceback.print_exc()
                return -5

        except Exception as e:
            print(f"[CRITICAL] Exception inattendue dans check_api_credentials: {e}")
            settings.WRITE_LOG_DEV_FILE(f"Exception inattendue dans check_api_credentials: {e}\n{traceback.format_exc()}", "ERROR")
            traceback.print_exc()
            return -5



# ==========================================================
# Instance globale
# ==========================================================
SessionManager = SessionManager()


# le programme is runing dans une interface logique et capable de renitailiser l'interface
# si on est dans un script il faut utiliser la function suivante :
