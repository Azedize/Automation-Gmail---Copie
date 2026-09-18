import os
import sys
import json
import stat
import shutil
import zipfile
import tempfile
import traceback
import subprocess
from typing import Optional
import requests
import datetime
import urllib.parse


from config import settings

# ==========================================================
# 📁 ROOT DIR
# ==========================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


try:
    from config import settings as Settings
    from core import EncryptionService
    from core import SessionManager
    from api.base_client import API_MANAGER
    from ui_utils import UIManager

except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__} : {e}")
    sys.exit(1)  # quitte immédiatement le script avec un code d'erreur


class UpdateManager:
    # ==========================================================
    # 🔹 UTILITAIRES
    # ==========================================================
    @staticmethod
    def readLocalVersion(path: str) -> Optional[str]:
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            Settings.write_log_dev_file(
                f"Error reading local version from {path}\n{traceback.format_exc()}",
                "ERROR",
            )
            return None

    @staticmethod
    def downloadFile(url: str, dest_path: str) -> bool:
        try:
            Settings.write_log_dev_file(
                f"⬇️ [DOWNLOAD] Demarrage du téléchargement\n   URL: {url}\n   Destination: {dest_path}",
                "INFO",
            )
            response = requests.get(
                url, stream=True, headers=Settings.HEADER, verify=False, timeout=60
            )
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            Settings.write_log_dev_file(
                                f"   🔄 [DOWNLOAD] Progression: {percent:.2f}% ({downloaded}/{total_size} bytes)",
                                "DEBUG",
                            )
            Settings.write_log_dev_file(
                f"✅ [DOWNLOAD] Téléchargement réussi : {dest_path}", "INFO"
            )
            return True
        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ [DOWNLOAD] Erreur lors du téléchargement\n   URL: {url}\n   Destination: {dest_path}\n   Erreur: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return False

    @staticmethod
    def handleReadonlyRemoval(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    @staticmethod
    def downloadAndExtract(
        zip_url: str,
        target_dir: str,
        clean_target: bool = False,
        extract_subdir: Optional[str] = None,
    ) -> bool:
        try:
            # print(f"\n⬇️ Téléchargement : {zip_url}")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                # Téléchargement
                if not UpdateManager.downloadFile(zip_url, zip_path):
                    Settings.write_log_dev_file(
                        "Échec du téléchargement pour mise à jour", "ERROR"
                    )
                    return False

                # print("📦 ZIP téléchargé")

                # Nettoyage du répertoire cible si demandé
                if clean_target and os.path.exists(target_dir):
                    Settings.write_log_dev_file(
                        f"Nettoyage du répertoire cible avant extraction ", "INFO"
                    )
                    shutil.rmtree(
                        target_dir, onerror=UpdateManager.handleReadonlyRemoval
                    )

                # Extraction
                with zipfile.ZipFile(zip_path, "r") as z:
                    Settings.write_log_dev_file("Extraction du ZIP téléchargé", "INFO")
                    z.extractall(tmpdir)

                # Recherche du répertoire extrait
                extracted_root = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path):
                        extracted_root = item_path
                        break

                if extracted_root is None:
                    # print("❌ Aucun dossier trouvé dans l'archive")
                    Settings.write_log_dev_file(
                        "Aucun dossier trouvé dans l'archive", "ERROR"
                    )
                    return False

                # Gestion du sous-répertoire
                extracted_dir = (
                    os.path.join(extracted_root, extract_subdir)
                    if extract_subdir
                    and os.path.exists(os.path.join(extracted_root, extract_subdir))
                    else extracted_root
                )

                os.makedirs(target_dir, exist_ok=True)

                # Déplacement des fichiers
                for item in os.listdir(extracted_dir):
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(target_dir, item)

                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(
                                dst, onerror=UpdateManager.handleReadonlyRemoval
                            )
                        shutil.move(src, dst)
                    else:
                        if os.path.exists(dst):
                            os.remove(dst)
                        shutil.move(src, dst)

                Settings.write_log_dev_file(
                    f"Mise à jour extraite avec succès vers ", "INFO"
                )

                # print(f"✅ Extraction terminée → {target_dir}")
                return True

        except Exception as e:
            Settings.write_log_dev_file(
                f"Échec de l'extraction de mise à jour - {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            # print("❌ Erreur lors de l'extraction")
            traceback.print_exc()
            return False

    # ==========================================================
    # FONCTION PRINCIPALE DE CHECK ET UPDATE
    #
    # Description :
    # Cette fonction vérifie la validité de la session utilisateur
    # puis contrôle la disponibilité des mises à jour du programme
    # principal ainsi que des outils externes.
    #
    # Étapes principales :
    #
    # 1) Vérification de la session :
    #    - Appelle SessionManager.check_session()
    #    - Si la session est invalide → log erreur + arrêt du programme.
    #
    # 2) Validation et formatage de la date :
    #    - Récupère la date depuis SESSION_INFO.
    #    - Vérifie que le type est datetime.datetime.
    #    - Convertit la date au format 'YYYY-MM-DD'.
    #
    # 3) Sécurisation :
    #    - Chiffre la date avec EncryptionService.
    #    - Encode le résultat pour utilisation dans une URL.
    #    - En cas d’erreur → log + arrêt du processus.
    #
    # 4) Vérification serveur :
    #    - Envoie une requête GET vers l’API distante.
    #    - Récupère les versions serveur :
    #         • version programme
    #         • version outils
    #
    # 5) Comparaison des versions :
    #    - Compare versions locales et serveur.
    #
    # 6) Mise à jour programme (obligatoire) :
    #    - Si version différente :
    #         • Ferme la fenêtre active si fournie
    #         • Lance la fenêtre de mise à jour
    #         • Stoppe l’application
    #
    # 7) Mise à jour outils (non bloquante) :
    #    - Télécharge l’archive ZIP
    #    - Nettoie le dossier cible
    #    - Extrait les nouveaux fichiers
    #
    # Gestion des erreurs :
    #    - Journalisation des erreurs critiques
    #    - Continuité si serveur indisponible
    #
    # Paramètre :
    #    window (optionnel) → fenêtre active à fermer en cas d’update
    #
    # ==========================================================

    @staticmethod
    def checkAndUpdate(window=None) -> bool:
        """
        🔹 Vérifie les mises à jour du programme et des extensions
        🔹 Retourne True si tout est à jour ou update réussi
        🔹 Retourne False si échec ou erreur
        """

        # ================================================
        # 1️⃣ Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer.", "ERROR"
            )
            return False

        # ================================================
        # 2️⃣ Date de session
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file(
                f"SESSION date type incorrect: {type(session_dt)}", "ERROR"
            )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file(
            f"Date de session formatée pour update: {session_date_plain}", "INFO"
        )
        settings.write_log_dev_file("Session date is valid datetime", "INFO")

        # ================================================
        # 3️⃣ Chiffrement de la date
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            if not date_encrypted:
                raise Exception("Encryption failed")

            encrypted_safe = urllib.parse.quote(date_encrypted)
            settings.write_log_dev_file(f"Date encryptée: {encrypted_safe}", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(
                f"Échec du chiffrement : {e}\n{traceback.format_exc()}", "ERROR"
            )
            traceback.print_exc()
            return False

        # ================================================
        # 4️⃣ URL API
        # ================================================
        CHECK_URL_PROGRAMM = (
            f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
            f"nv=1&rv4=1&event=check&type=V4&ext=Script&k={encrypted_safe}"
        )

        # SERVER_ZIP_URL_PROGRAM = (
        #     f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
        #     f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={encrypted_safe}"
        # )
        SERVER_ZIP_URL_PROGRAM = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"

        settings.write_log_dev_file(
            f"URL finale pour API: {CHECK_URL_PROGRAMM}", "INFO"
        )

        # ================================================
        # 5️⃣ Requête GET
        # ================================================
        try:
            settings.write_log_dev_file(
                "Vérification de mise à jour en cours...", "INFO"
            )
            response = API_MANAGER.makeRequest(
                CHECK_URL_PROGRAMM, method="GET", timeout=10
            )

            settings.write_log_dev_file(f"Réponse brute de l'API: {response}", "DEBUG")
            settings.write_log_dev_file(
                f"Type de la réponse: {type(response)}", "DEBUG"
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                settings.write_log_dev_file(
                    "Serveur indisponible → Continuer sans update", "WARNING"
                )
                return False

            data = response.get("data")

            # ================================================
            # 🚨 INVALID TOKEN DETECTION
            # ================================================

            if isinstance(data, str) and "Invalid token" in data:
                Settings.write_log_dev_file(
                    "Invalid token detected - clearing session", "ERROR"
                )

                try:
                    SessionManager.clear_session()
                    settings.write_log_dev_file(
                        "Session cleared due to invalid token detection", "INFO"
                    )
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"Error clearing session after invalid token detection\n{traceback.format_exc()}",
                        "ERROR",
                    )

                os._exit(1)

            # ================================================
            # Vérification structure JSON
            # ================================================
            if not isinstance(data, dict):
                # print("❌ Réponse serveur invalide :", data)
                Settings.write_log_dev_file(
                    f"Réponse serveur invalide: {data}", "ERROR"
                )
                return False

            server_program = data.get("version")
            server_tools = data.get("version_Extention")

            # print("\n=== Versions serveur ===")
            # print("server_program :", server_program)
            # print("server_tools   :", server_tools)
            settings.write_log_dev_file(
                f"Versions serveur - Programme: {server_program}, Outils: {server_tools}",
                "INFO",
            )

            local_program = UpdateManager.readLocalVersion(
                Settings.VERSION_LOCAL_PROGRAMM
            )
            # local_tools = UpdateManager._read_local_version( Settings.VERSION_LOCAL_EXT )

            # print("\n=== Versions locales ===")
            # print("local_program :", local_program)
            # print("local_tools   :", local_tools)
            settings.write_log_dev_file(
                f"Versions locales - Programme: {local_program}", "INFO"
            )

            # 🔴 Update Programme
            if not local_program or local_program != server_program:
                # print("🔴 UPDATE PROGRAMME NECESSAIRE")
                Settings.write_log_dev_file(
                    "Mise à jour du programme nécessaire", "INFO"
                )

                if window and hasattr(window, "close"):
                    # print("[DEBUG] Fermeture fenêtre")
                    settings.write_log_dev_file("Fermeture fenêtre", "DEBUG")
                    window.close()

                UpdateManager.launchNewWindow()
                return True

            # 🟡 Update Tools
            # if not local_tools or local_tools != server_tools:
            #     # print("🟡 UPDATE TOOLS NECESSAIRE")
            #     Settings.write_log_dev_file("Mise à jour des outils nécessaires", "INFO")

            #     os.makedirs(Settings.TOOLS_DIR, exist_ok=True)

            #     success = UpdateManager._download_and_extract(  SERVER_ZIP_URL_PROGRAM, Settings.TOOLS_DIR,  clean_target=True, extract_subdir="tools" )

            #     if success:
            #         Settings.write_log_dev_file("Outils mis à jour avec succès", "INFO")
            #     else:
            #         Settings.write_log_dev_file("Échec de la mise à jour des outils", "ERROR")
            #         return False

            Settings.write_log_dev_file("Application à jour", "INFO")
            return True

        except ImportError:
            Settings.write_log_dev_file("API_MANAGER non disponible", "INFO")
            return False

        except Exception as e:
            Settings.write_log_dev_file(
                f"Erreur critique lors de la vérification de mise à jour: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return False

    # ==========================================================
    # 🚀 LANCEMENT NOUVELLE INSTANCE
    # ==========================================================
    @staticmethod
    def launchNewWindow() -> bool:
        """Lance une nouvelle instance de l'application"""
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.pyc")
        # print(f"[DEBUG] Chemin du script à lancer : {script_path}")

        if not os.path.isfile(script_path):
            # print(f"[LAUNCH] Script introuvable : {script_path}")
            return False

        try:
            # Utiliser pythonw.exe si possible (Windows)
            python_exe = sys.executable
            if sys.platform == "win32":
                pythonw_candidate = os.path.join(
                    os.path.dirname(python_exe), "pythonw.exe"
                )
                if os.path.isfile(pythonw_candidate):
                    python_exe = pythonw_candidate

            # Lancer le subprocess
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [python_exe, script_path],
                cwd=Settings.BASE_DIR,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )

            # print("[DEBUG] Nouvelle instance lancée avec succès")
            return True

        except Exception as e:
            # print(f"[LAUNCH] Échec du lancement : {e}")
            Settings.write_log_dev_file(
                f"Échec du lancement de la nouvelle instance: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return False

    # =============================================================================
    # Fonction : check_version_extension
    # -----------------------------------------------------------------------------
    # Description générale :
    # Cette fonction vérifie de manière sécurisée si une extension locale est
    # à jour ou si une nouvelle version est disponible sur le serveur distant.
    #
    # Scénario complet d’exécution :
    # 1. Vérifie la validité de la session utilisateur (sécurité et autorisation).
    #    - Si la session est invalide, le programme est arrêté immédiatement.
    #
    # 2. Récupère la date de la session et s’assure qu’elle est bien de type
    #    datetime.datetime afin d’éviter toute incohérence ou erreur de traitement.
    #
    # 3. Formate la date selon le standard (YYYY-MM-DD) puis la chiffre à l’aide
    #    d’une clé secrète pour sécuriser la requête vers le serveur.
    #
    # 4. Génère une URL sécurisée et envoie une requête HTTP GET vers l’API distante
    #    afin de récupérer :
    #       - la version distante de l’extension
    #       - la version distante du manifest
    #
    # 5. Analyse la réponse du serveur (JSON) et gère les erreurs réseau,
    #    de parsing ou de réponse invalide.
    #
    # 6. Vérifie l’existence des fichiers locaux nécessaires (version locale et
    #    manifest) et lit leurs valeurs.
    #
    # 7. Compare la version du manifest local avec celle du serveur afin de garantir
    #    la compatibilité de l’extension.
    #    - En cas d’incompatibilité, l’exécution est stoppée pour éviter tout risque.
    #
    # 8. Compare la version locale de l’extension avec la version distante :
    #    - Si une nouvelle version est disponible, retourne le numéro de version
    #      distante (string).
    #    - Si l’extension est déjà à jour, retourne True.
    #    - En cas d’erreur ou d’impossibilité de vérification, retourne False.
    #
    # Valeurs de retour :
    #    - str   : Nouvelle version disponible (mise à jour requise).
    #    - True  : Extension déjà à jour.
    #    - False : Erreur critique ou impossibilité de poursuivre.
    #
    # Remarque :
    # Cette fonction agit comme un point de contrôle critique (gatekeeper).
    # Toute erreur entraîne l’arrêt du processus de mise à jour afin de garantir
    # la stabilité, la sécurité et l’intégrité de l’application.
    # =============================================================================

    @staticmethod
    def checkExtensionVersion(window=None):

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer l’extraction.", "ERROR"
            )
            sys.exit()
            return False

        # ================================================
        # 🔹 Gestion sécurisée du champ date (datetime uniquement)
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            settings.write_log_dev_file(
                f"SESSION date type incorrect: {type(session_dt)}", "ERROR"
            )
            return

        settings.write_log_dev_file("Session date is valid datetime", "INFO")

        session_date_plain = session_dt.strftime("%Y-%m-%d")

        settings.write_log_dev_file(
            f"Session date (format YYYY-MM-DD): {session_date_plain}", "INFO"
        )

        # ================================================
        # 🔹 Chiffrement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            settings.write_log_dev_file(f"Encrypted date: {date_encrypted}", "INFO")
        except Exception as e:
            settings.write_log_dev_file(
                f"Encryption failed: {e}\n{traceback.format_exc()}", level="ERROR"
            )
            traceback.print_exc()
            return False

        if not date_encrypted:
            Settings.write_log_dev_file("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")

        encrypted_safe = urllib.parse.quote(date_encrypted)
        CHECK_URL_EX3 = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted_safe}"

        # ================================================
        # 🔹 Requête GET
        # ================================================
        try:
            response = requests.get(
                CHECK_URL_EX3, headers=Settings.HEADER, verify=False, timeout=10
            )
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    settings.write_log_dev_file(
                        "Content-Type incorrect, but JSON parsed successfully",
                        "WARNING",
                    )
                except Exception as e:
                    settings.write_log_dev_file(
                        f"Failed to parse JSON response: {e}\n{traceback.format_exc()}",
                        level="ERROR",
                    )
                    return False

            remote_version = data.get("version_Extention")
            remote_manifest_version = data.get("manifest_version")

        except Exception as e:
            settings.write_log_dev_file(
                f"Failed to get remote version: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            traceback.print_exc()
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Network Error",
                    "Unable to check for updates. Please check your internet connection.",
                    message_type="critical",
                )
            return False

        # ================================================
        # 🔹 Vérification fichiers locaux
        # ================================================
        if not os.path.exists(Settings.MANIFEST_PATH_EX3):
            settings.write_log_dev_file(
                "Fichier manifest.json local introuvable", "ERROR"
            )
            return False
        if not os.path.exists(Settings.VERSION_LOCAL_EX3):
            settings.write_log_dev_file("Fichier version locale introuvable", "ERROR")
            return False

        with open(Settings.MANIFEST_PATH_EX3, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        local_manifest_version = manifest_data.get("version")
        local_version = UpdateManager.readLocalVersion(Settings.VERSION_LOCAL_EX3)

        settings.write_log_dev_file(
            f"Version locale: {local_version}, Manifest local version: {local_manifest_version}",
            "INFO",
        )

        # ================================================
        # 🔹 Compatibilité manifest
        # ================================================
        if str(local_manifest_version) != str(remote_manifest_version):
            settings.write_log_dev_file(
                "Manifest incompatible, mise à jour automatique impossible", "WARNING"
            )
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Manifest Incompatibility",
                    "The local manifest version does not match the remote version.",
                    message_type="critical",
                )
            return False

        # ================================================
        # 🔹 Différence de version
        # ================================================
        if local_version != remote_version:
            settings.write_log_dev_file(
                f"Extension update required - new version: {remote_version}", "INFO"
            )
            return remote_version
        else:
            settings.write_log_dev_file(f"Extension up-to-date", "INFO")
            return True

    @staticmethod
    def checkFirefoxExtensionVersion(window=None):

        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer l’extraction.", "ERROR"
            )
            sys.exit()
            return False

        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            settings.write_log_dev_file(
                f"SESSION date type incorrect: {type(session_dt)}", "ERROR"
            )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file(
            f"Session date (format YYYY-MM-DD): {session_date_plain}", "INFO"
        )

        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            settings.write_log_dev_file(f"Encrypted date: {date_encrypted}", "INFO")
        except Exception as e:
            settings.write_log_dev_file(
                f"Encryption failed: {e}\n{traceback.format_exc()}", level="ERROR"
            )
            traceback.print_exc()
            return False

        if not date_encrypted:
            Settings.write_log_dev_file("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")

        encrypted_safe = urllib.parse.quote(date_encrypted)

        CHECK_URL_EX3 = f"https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=ek8lwoh2&dl=1"

        settings.write_log_dev_file(f"URL finale pour API: {CHECK_URL_EX3}", "INFO")

        try:
            response = requests.get(
                CHECK_URL_EX3, headers=Settings.HEADER, verify=False, timeout=10
            )
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    settings.write_log_dev_file(
                        "Content-Type incorrect, but JSON parsed successfully",
                        "WARNING",
                    )
                except Exception as e:
                    settings.write_log_dev_file(
                        f"Failed to parse JSON response: {e}\n{traceback.format_exc()}",
                        level="ERROR",
                    )
                    return False

            remote_version = data.get("version_Extention")
            remote_manifest_version = data.get("manifest_version")
        except Exception as e:
            settings.write_log_dev_file(
                f"Failed to get remote version: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            traceback.print_exc()
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Network Error",
                    "Unable to check for updates. Please check your internet connection.",
                    message_type="critical",
                )
            return False

        if remote_version is None:
            settings.write_log_dev_file(
                "Remote extension version is missing from update server response",
                "ERROR",
            )
            return False

        if not os.path.exists(Settings.MANIFEST_PATH_EX3_FIREFOX):
            settings.write_log_dev_file(
                "Fichier manifest.json Firefox local introuvable", "ERROR"
            )
            return False

        try:
            with open(Settings.MANIFEST_PATH_EX3_FIREFOX, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            local_manifest_version = manifest_data.get("version")
        except Exception as e:
            settings.write_log_dev_file(
                f"Erreur lecture du manifest Firefox local: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return False

        local_version = None
        if os.path.exists(Settings.VERSION_LOCAL_EX3_FIREFOX):
            local_version = UpdateManager.readLocalVersion(
                Settings.VERSION_LOCAL_EX3_FIREFOX
            )

        settings.write_log_dev_file(
            f"Firefox local manifest version: {local_manifest_version}, local version file: {local_version}, remote version: {remote_version}",
            "INFO",
        )

        compare_value = (
            local_version if local_version is not None else local_manifest_version
        )

        if compare_value is None:
            settings.write_log_dev_file(
                "Aucune version locale de l’extension Firefox disponible pour comparaison",
                "ERROR",
            )
            return False

        if str(compare_value) != str(remote_version):
            settings.write_log_dev_file(
                f"Firefox extension update required - new version: {remote_version}",
                "INFO",
            )
            return remote_version
        else:
            settings.write_log_dev_file("Firefox extension up-to-date", "INFO")
            return True

    @staticmethod
    def updateFirefoxExtensionFromServer(remote_version=None) -> bool:
        """Download and install the Firefox extension to EXTENTION_EX3_FIREFOX."""
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer la mise à jour Firefox.",
                "ERROR",
            )
            sys.exit()
            return False

        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file(
                f" type incorrect date session: {type(session_dt)}", "ERROR"
            )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")

        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            encrypted_safe = urllib.parse.quote(date_encrypted)
        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ Encryption failed: {e}\n{traceback.format_exc()}", "ERROR"
            )
            traceback.print_exc()
            return False

        SERVEUR_ZIP_URL_EX3_FIREFOX = (
            "https://github.com/Azedize/Ext3Lastversion/archive/refs/heads/main.zip"
        )
        Settings.write_log_dev_file(
            "🚀 [EXTENSION FIREFOX] Lancement de la séquence de mise à jour Firefox",
            "INFO",
        )
        Settings.write_log_dev_file(
            f"🔗 URL de mise à jour Firefox : {SERVEUR_ZIP_URL_EX3_FIREFOX}", "INFO"
        )

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "Ext3_Firefox.zip")

                settings.write_log_dev_file(
                    "⬇️ [EXTENSION FIREFOX] Téléchargement de l'archive Firefox", "INFO"
                )
                if not UpdateManager.downloadFile(
                    SERVEUR_ZIP_URL_EX3_FIREFOX, zip_path
                ):
                    Settings.write_log_dev_file(
                        "🛑 [EXTENSION FIREFOX] Échec du téléchargement de l'extension Firefox",
                        "ERROR",
                    )
                    return False

                if os.path.exists(Settings.EXTENTION_EX3_FIREFOX):
                    Settings.write_log_dev_file(
                        f"Suppression de l'ancienne extension Firefox: {Settings.EXTENTION_EX3_FIREFOX}",
                        "INFO",
                    )
                    shutil.rmtree(
                        Settings.EXTENTION_EX3_FIREFOX,
                        onerror=UpdateManager.handleReadonlyRemoval,
                    )

                Settings.write_log_dev_file("Extraction du ZIP Firefox...", "INFO")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)

                extracted_dir = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path) and item != "__MACOSX":
                        extracted_dir = item_path
                        break

                if extracted_dir is None:
                    Settings.write_log_dev_file(
                        "Dossier extrait introuvable pour l'extension Firefox", "ERROR"
                    )
                    return False

                shutil.move(extracted_dir, Settings.EXTENTION_EX3_FIREFOX)
                Settings.write_log_dev_file(
                    f"Extension Firefox mise à jour vers la version {remote_version}",
                    "INFO",
                )
                return True

        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ Erreur lors de la mise à jour Firefox : {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return False

    @staticmethod
    def updateExtensionFromServer(remote_version=None) -> bool:

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer la mise à jour.", "ERROR"
            )
            sys.exit()
            return False

        # ================================================
        # 🔹 Gestion sécurisée du champ date
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file(
                f" type incorrect date session: {type(session_dt)}", "ERROR"
            )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")

        # ================================================
        # 🔹 Chiffrement du token pour téléchargement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            encrypted_safe = urllib.parse.quote(date_encrypted)
        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ Encryption failed: {e}\n{traceback.format_exc()}", "ERROR"
            )
            traceback.print_exc()
            return False

        # ================================================
        # 🔹 URL de téléchargement de l'extension
        # ================================================
        SERVEUR_ZIP_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Ext3&k={encrypted_safe}"
        Settings.write_log_dev_file(
            "🚀 [EXTENSION CHROMIUM] Lancement de la séquence de mise à jour Chromium",
            "INFO",
        )
        Settings.write_log_dev_file(
            f"🔗 URL de mise à jour Chromium : {SERVEUR_ZIP_URL_EX3}", "INFO"
        )

        # ================================================
        # 🔹 Téléchargement et extraction
        # ================================================
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "Ext3.zip")

                settings.write_log_dev_file(
                    "⬇️ [EXTENSION CHROMIUM] Téléchargement de l'archive Chromium",
                    "INFO",
                )
                if not UpdateManager.downloadFile(SERVEUR_ZIP_URL_EX3, zip_path):
                    Settings.write_log_dev_file(
                        "🛑 [EXTENSION CHROMIUM] Échec du téléchargement de l'extension Chromium",
                        "ERROR",
                    )
                    return False

                # Suppression ancienne version
                if os.path.exists(Settings.EXTENTION_EX3_CHROMIUM):
                    Settings.write_log_dev_file(
                        f"Suppression de l'ancienne extension avant mise à jour", "INFO"
                    )
                    shutil.rmtree(
                        Settings.EXTENTION_EX3_CHROMIUM,
                        onerror=UpdateManager.handleReadonlyRemoval,
                    )

                # Extraction
                # print("📂 Extraction du fichier ZIP...")
                settings.write_log_dev_file("Extracting ZIP file...", "INFO")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)

                # Recherche dossier extrait
                extracted_dir = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path) and item != "__MACOSX":
                        extracted_dir = item_path
                        break

                if extracted_dir is None:
                    # print("❌ Dossier extrait introuvable")
                    Settings.write_log_dev_file("Dossier extrait introuvable", "ERROR")
                    return False

                # Déplacement vers destination finale
                shutil.move(extracted_dir, Settings.EXTENTION_EX3_CHROMIUM)
                # print(f"✅ Mise à jour réussie : {Settings.EXTENTION_EX3_CHROMIUM}")
                Settings.write_log_dev_file(
                    f"Extension mise à jour vers la version {remote_version}", "INFO"
                )

                return True

        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ Erreur lors de la mise à jour : {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            # print(f"❌ Erreur lors de la mise à jour : {e}")
            traceback.print_exc()
            return False


# ==========================================================
# ▶️ POINT D’ENTRÉE
# ==========================================================
UpdateManager = UpdateManager()
