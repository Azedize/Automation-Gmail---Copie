import os
import sys
import json
import stat
import shutil
import zipfile
import tempfile
import traceback
import subprocess
from typing import Any, Optional
import requests
import datetime
import urllib.parse


from config import settings as Settings
settings = Settings



BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


try:
    from core import EncryptionService
    from core import SessionManager
    from api.base_client import API_MANAGER
    from ui_utils import UIManager

except ImportError as e:
    Settings.write_log_dev_file(f"❌ Erreur d'importation dans file {__file__}: {e}\n{traceback.format_exc()}", level="ERROR")
    sys.exit(1)

SessionManager: Any




class UpdateManager:

    @staticmethod
    def readLocalVersion(path: str) -> Optional[str]:
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            Settings.write_log_dev_file( f"Error reading local version from {path}\n{traceback.format_exc()}", "ERROR")
            return None

    @staticmethod
    def downloadFile(url: str, dest_path: str) -> bool:
        try:
            Settings.write_log_dev_file( f"⬇️ [DOWNLOAD] Demarrage du téléchargement\n   URL: {url}\n   Destination: {dest_path}", "INFO" )
            response = requests.get(  url, stream=True, headers=Settings.HEADER, verify=False, timeout=60)
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
                            Settings.write_log_dev_file( f"   🔄 [DOWNLOAD] Progression: {percent:.2f}% ({downloaded}/{total_size} bytes)", "DEBUG" )
            Settings.write_log_dev_file(f"✅ [DOWNLOAD] Téléchargement réussi : {dest_path}", "INFO")
            return True
        except Exception as e:
            Settings.write_log_dev_file(  f"❌ [DOWNLOAD] Erreur lors du téléchargement\n   URL: {url}\n   Destination: {dest_path}\n   Erreur: {e}\n{traceback.format_exc()}",  "ERROR" )
            return False

    @staticmethod
    def handleReadonlyRemoval(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    @staticmethod
    def downloadAndExtract(zip_url: str, target_dir: str, clean_target: bool = False, extract_subdir: Optional[str] = None) -> bool:
        try:

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                if not UpdateManager.downloadFile(zip_url, zip_path):
                    Settings.write_log_dev_file("Échec du téléchargement pour mise à jour", "ERROR")
                    return False


                if clean_target and os.path.exists(target_dir):
                    Settings.write_log_dev_file("Nettoyage du répertoire cible avant extraction", "INFO")
                    shutil.rmtree(target_dir, onerror=UpdateManager.handleReadonlyRemoval)

                with zipfile.ZipFile(zip_path, "r") as z:
                    Settings.write_log_dev_file("Extraction du ZIP téléchargé", "INFO")
                    z.extractall(tmpdir)

                extracted_root = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path):
                        extracted_root = item_path
                        break

                if extracted_root is None:
                    Settings.write_log_dev_file("Aucun dossier trouvé dans l'archive", "ERROR")
                    return False
                
                extracted_dir = (   os.path.join(extracted_root, extract_subdir) if extract_subdir  and os.path.exists(os.path.join(extracted_root, extract_subdir)) else extracted_root  )
                os.makedirs(target_dir, exist_ok=True)

                for item in os.listdir(extracted_dir):
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(target_dir, item)

                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst, onerror=UpdateManager.handleReadonlyRemoval)
                        shutil.move(src, dst)
                    else:
                        if os.path.exists(dst):
                            os.remove(dst)
                        shutil.move(src, dst)

                Settings.write_log_dev_file("Mise à jour extraite avec succès", "INFO")
                return True

        except Exception as e:
            Settings.write_log_dev_file( f"Échec de l'extraction de mise à jour - {e}\n{traceback.format_exc()}", "ERROR" )
            traceback.print_exc()
            return False


    @staticmethod
    def checkAndUpdate(window=None) -> bool:

        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file("Session invalide. Impossible de continuer.", "ERROR")
            return False

 
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file(f"SESSION date type incorrect: {type(session_dt)}", "ERROR")
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file(f"Date de session formatée pour update: {session_date_plain}", "INFO")
        settings.write_log_dev_file("Session date is valid datetime", "INFO")


        try:
            date_encrypted = EncryptionService.encrypt_message(session_date_plain, Settings.KEY)
            if not date_encrypted:
                raise Exception("Encryption failed")

            encrypted_safe = urllib.parse.quote(date_encrypted)
            settings.write_log_dev_file(f"Date encryptée: {encrypted_safe}", "INFO")

        except Exception as e:
            Settings.write_log_dev_file( f"Échec du chiffrement : {e}\n{traceback.format_exc()}", "ERROR" )
            traceback.print_exc()
            return False

      
        CHECK_URL_PROGRAMM =  f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k={encrypted_safe}" 

        # SERVER_ZIP_URL_PROGRAM = (
        #     f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
        #     f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={encrypted_safe}"
        # )
        SERVER_ZIP_URL_PROGRAM = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"

        settings.write_log_dev_file(f"URL finale pour API: {CHECK_URL_PROGRAMM}", "INFO")

  
        try:
            settings.write_log_dev_file("Vérification de mise à jour en cours...", "INFO")
            response = API_MANAGER.makeRequest(CHECK_URL_PROGRAMM, method="GET", timeout=10)

            settings.write_log_dev_file(f"Réponse brute de l'API: {response}", "DEBUG")
            settings.write_log_dev_file(f"Type de la réponse: {type(response)}", "DEBUG")

            if not isinstance(response, dict) or response.get("status_code") != 200:
                settings.write_log_dev_file("Serveur indisponible → Continuer sans update", "WARNING")
                return False

            data = response.get("data")



            if isinstance(data, str) and "Invalid token" in data:
                Settings.write_log_dev_file("Invalid token detected - clearing session", "ERROR")

                try:
                    SessionManager.clear_session()
                    settings.write_log_dev_file("Session cleared due to invalid token detection", "INFO")
                except Exception as e:
                    Settings.write_log_dev_file( f"Error clearing session after invalid token detection\n{traceback.format_exc()}",  "ERROR" )

                os._exit(1)

            if not isinstance(data, dict):
                Settings.write_log_dev_file(f"Réponse serveur invalide: {data}", "ERROR")
                return False

            server_program = data.get("version")
            server_tools = data.get("version_Extention")


            settings.write_log_dev_file( f"Versions serveur - Programme: {server_program}, Outils: {server_tools}", "INFO")

            local_program = UpdateManager.readLocalVersion( Settings.VERSION_LOCAL_PROGRAMM)

            settings.write_log_dev_file(f"Versions locales - Programme: {local_program}", "INFO"  )

            if not local_program or local_program != server_program:
                Settings.write_log_dev_file("Mise à jour du programme nécessaire", "INFO")

                if window and hasattr(window, "close"):
                    settings.write_log_dev_file("Fermeture fenêtre", "DEBUG")
                    window.close()

                UpdateManager.launchNewWindow()
                return True

            Settings.write_log_dev_file("Application à jour", "INFO")
            return True

        except ImportError:
            Settings.write_log_dev_file("API_MANAGER non disponible", "INFO")
            return False

        except Exception as e:
            Settings.write_log_dev_file( f"Erreur critique lors de la vérification de mise à jour: {e}\n{traceback.format_exc()}",  "ERROR" )
            traceback.print_exc()
            return False

    @staticmethod
    def launchNewWindow() -> bool:
        """Lance une nouvelle instance de l'application"""
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.pyc")
        if not os.path.isfile(script_path):
            return False

        try:
            python_exe = sys.executable
            if sys.platform == "win32":
                pythonw_candidate = os.path.join( os.path.dirname(python_exe), "pythonw.exe"  )
                if os.path.isfile(pythonw_candidate):
                    python_exe = pythonw_candidate

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen( [python_exe, script_path],   cwd=Settings.BASE_DIR, close_fds=True, stdout=subprocess.DEVNULL ,  stderr=subprocess.DEVNULL, creationflags=creation_flags )
            return True

        except Exception as e:
            Settings.write_log_dev_file( f"Échec du lancement de la nouvelle instance: {e}\n{traceback.format_exc()}", "ERROR")
            traceback.print_exc()
            return False

    @staticmethod
    def checkExtensionVersion(window=None):

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file("Session invalide. Impossible de continuer l’extraction.", "ERROR")
            sys.exit()
            return False

        # ================================================
        # 🔹 Gestion sécurisée du champ date (datetime uniquement)
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            settings.write_log_dev_file(f"SESSION date type incorrect: {type(session_dt)}", "ERROR")
            return

        settings.write_log_dev_file("Session date is valid datetime", "INFO")

        session_date_plain = session_dt.strftime("%Y-%m-%d")

        settings.write_log_dev_file(f"Session date (format YYYY-MM-DD): {session_date_plain}", "INFO")

        # ================================================
        # 🔹 Chiffrement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(session_date_plain, Settings.KEY)
            settings.write_log_dev_file(f"Encrypted date: {date_encrypted}", "INFO")
        except Exception as e:
            settings.write_log_dev_file(f"Encryption failed: {e}\n{traceback.format_exc()}", level="ERROR")
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
            response = requests.get( CHECK_URL_EX3, headers=Settings.HEADER, verify=False, timeout=10 )
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    settings.write_log_dev_file( "Content-Type incorrect, but JSON parsed successfully", "WARNING" )
                except Exception as e:
                    settings.write_log_dev_file(  f"Failed to parse JSON response: {e}\n{traceback.format_exc()}", level="ERROR")
                    return False

            remote_version = data.get("version_Extention")
            remote_manifest_version = data.get("manifest_version")

        except Exception as e:
            settings.write_log_dev_file(  f"Failed to get remote version: {e}\n{traceback.format_exc()}",level="ERROR"  )
            traceback.print_exc()
            if window:
                UIManager.showCriticalMessage(  window,  "Network Error", "Unable to check for updates. Please check your internet connection.",  message_type="critical" )
            return False

        # ================================================
        # 🔹 Vérification fichiers locaux
        # ================================================
        if not os.path.exists(Settings.MANIFEST_PATH_EX3):
            settings.write_log_dev_file("Fichier manifest.json local introuvable", "ERROR")
            return False
        if not os.path.exists(Settings.VERSION_LOCAL_EX3):
            settings.write_log_dev_file("Fichier version locale introuvable", "ERROR")
            return False

        with open(Settings.MANIFEST_PATH_EX3, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        local_manifest_version = manifest_data.get("version")
        local_version = UpdateManager.readLocalVersion(Settings.VERSION_LOCAL_EX3)

        settings.write_log_dev_file(  f"Version locale: {local_version}, Manifest local version: {local_manifest_version}", "INFO")

        # ================================================
        # 🔹 Compatibilité manifest
        # ================================================
        if str(local_manifest_version) != str(remote_manifest_version):
            settings.write_log_dev_file( "Manifest incompatible, mise à jour automatique impossible", "WARNING" )
            if window:
                UIManager.showCriticalMessage( window, "Manifest Incompatibility",  "The local manifest version does not match the remote version.",  message_type="critical"  )
            return False

        # ================================================
        # 🔹 Différence de version
        # ================================================
        if local_version != remote_version:
            settings.write_log_dev_file( f"Extension update required - new version: {remote_version}", "INFO" )
            return remote_version
        else:
            settings.write_log_dev_file(f"Extension up-to-date", "INFO")
            return True

    @staticmethod
    def checkFirefoxExtensionVersion(window=None):

        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file( "Session invalide. Impossible de continuer l’extraction.", "ERROR")
            sys.exit()
            return False

        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            settings.write_log_dev_file( f"SESSION date type incorrect: {type(session_dt)}", "ERROR" )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file( f"Session date (format YYYY-MM-DD): {session_date_plain}", "INFO" )

        try:
            date_encrypted = EncryptionService.encrypt_message(  session_date_plain, Settings.KEY )
            settings.write_log_dev_file(f"Encrypted date: {date_encrypted}", "INFO")
        except Exception as e:
            settings.write_log_dev_file( f"Encryption failed: {e}\n{traceback.format_exc()}", level="ERROR"  )
            traceback.print_exc()
            return False

        if not date_encrypted:
            Settings.write_log_dev_file("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")

        encrypted_safe = urllib.parse.quote(date_encrypted)

        CHECK_URL_EX3 = f"https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=ek8lwoh2&dl=1"

        settings.write_log_dev_file(f"URL finale pour API: {CHECK_URL_EX3}", "INFO")

        try:
            response = requests.get( CHECK_URL_EX3, headers=Settings.HEADER, verify=False, timeout=10 )
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    settings.write_log_dev_file( "Content-Type incorrect, but JSON parsed successfully",  "WARNING")
                except Exception as e:
                    settings.write_log_dev_file( f"Failed to parse JSON response: {e}\n{traceback.format_exc()}", level="ERROR"  )
                    return False

            remote_version = data.get("version_Extention")
            remote_manifest_version = data.get("manifest_version")
        except Exception as e:
            settings.write_log_dev_file(f"Failed to get remote version: {e}\n{traceback.format_exc()}", level="ERROR" )
            traceback.print_exc()
            if window:
                UIManager.showCriticalMessage(  window,  "Network Error",  "Unable to check for updates. Please check your internet connection.",  message_type="critical"  )
            return False

        if remote_version is None:
            settings.write_log_dev_file( "Remote extension version is missing from update server response",  "ERROR" )
            return False

        if not os.path.exists(Settings.MANIFEST_PATH_EX3_FIREFOX):
            settings.write_log_dev_file(  "Fichier manifest.json Firefox local introuvable", "ERROR" )
            return False

        try:
            with open(Settings.MANIFEST_PATH_EX3_FIREFOX, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            local_manifest_version = manifest_data.get("version")
        except Exception as e:
            settings.write_log_dev_file( f"Erreur lecture du manifest Firefox local: {e}\n{traceback.format_exc()}", "ERROR"  )
            return False

        local_version = None
        if os.path.exists(Settings.VERSION_LOCAL_EX3_FIREFOX):
            local_version = UpdateManager.readLocalVersion(  Settings.VERSION_LOCAL_EX3_FIREFOX )

        settings.write_log_dev_file( f"Firefox local manifest version: {local_manifest_version}, local version file: {local_version}, remote version: {remote_version}", "INFO"  )

        compare_value = (  local_version if local_version is not None else local_manifest_version )

        if compare_value is None:
            settings.write_log_dev_file(  "Aucune version locale de l’extension Firefox disponible pour comparaison",  "ERROR"  )
            return False

        if str(compare_value) != str(remote_version):
            settings.write_log_dev_file( f"Firefox extension update required - new version: {remote_version}", "INFO" )
            return remote_version
        else:
            settings.write_log_dev_file("Firefox extension up-to-date", "INFO")
            return True

    @staticmethod
    def updateFirefoxExtensionFromServer(remote_version=None) -> bool:
        """Download and install the Firefox extension to EXTENTION_EX3_FIREFOX."""
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(  "Session invalide. Impossible de continuer la mise à jour Firefox.", "ERROR" )
            sys.exit()
            return False

        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file( f" type incorrect date session: {type(session_dt)}", "ERROR" )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")

        try:
            date_encrypted = EncryptionService.encrypt_message(  session_date_plain, Settings.KEY )
            encrypted_safe = urllib.parse.quote(date_encrypted)
        except Exception as e:
            Settings.write_log_dev_file(  f"❌ Encryption failed: {e}\n{traceback.format_exc()}", "ERROR" )
            traceback.print_exc()
            return False

        SERVEUR_ZIP_URL_EX3_FIREFOX = ( "https://github.com/Azedize/Ext3Lastversion/archive/refs/heads/main.zip")
        Settings.write_log_dev_file( "🚀 [EXTENSION FIREFOX] Lancement de la séquence de mise à jour Firefox", "INFO", )
        Settings.write_log_dev_file( f"🔗 URL de mise à jour Firefox : {SERVEUR_ZIP_URL_EX3_FIREFOX}", "INFO")

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "Ext3_Firefox.zip")

                settings.write_log_dev_file(  "⬇️ [EXTENSION FIREFOX] Téléchargement de l'archive Firefox", "INFO" )
                if not UpdateManager.downloadFile(  SERVEUR_ZIP_URL_EX3_FIREFOX, zip_path ):
                    Settings.write_log_dev_file( "🛑 [EXTENSION FIREFOX] Échec du téléchargement de l'extension Firefox", "ERROR"  )
                    return False

                if os.path.exists(Settings.EXTENTION_EX3_FIREFOX):
                    Settings.write_log_dev_file(  f"Suppression de l'ancienne extension Firefox: {Settings.EXTENTION_EX3_FIREFOX}" ,  "INFO"  )
                    shutil.rmtree( Settings.EXTENTION_EX3_FIREFOX, onerror=UpdateManager.handleReadonlyRemoval )

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
                    Settings.write_log_dev_file(  "Dossier extrait introuvable pour l'extension Firefox", "ERROR" )
                    return False

                shutil.move(extracted_dir, Settings.EXTENTION_EX3_FIREFOX)
                Settings.write_log_dev_file( f"Extension Firefox mise à jour vers la version {remote_version}", "INFO" )
                return True

        except Exception as e:
            Settings.write_log_dev_file(  f"❌ Erreur lors de la mise à jour Firefox : {e}\n{traceback.format_exc()}", "ERROR"  )
            traceback.print_exc()
            return False

    @staticmethod
    def updateExtensionFromServer(remote_version=None) -> bool:

        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file( "Session invalide. Impossible de continuer la mise à jour.", "ERROR" )
            sys.exit()
            return False
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file( f" type incorrect date session: {type(session_dt)}", "ERROR"  )
            return False
        session_date_plain = session_dt.strftime("%Y-%m-%d")


        try:
            date_encrypted = EncryptionService.encrypt_message( session_date_plain, Settings.KEY )
            encrypted_safe = urllib.parse.quote(date_encrypted)
        except Exception as e:
            Settings.write_log_dev_file(  f"❌ Encryption failed: {e}\n{traceback.format_exc()}", "ERROR"  )
            traceback.print_exc()
            return False

        SERVEUR_ZIP_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Ext3&k={encrypted_safe}"
        Settings.write_log_dev_file("🚀 [EXTENSION CHROMIUM] Lancement de la séquence de mise à jour Chromium", "INFO" )
        Settings.write_log_dev_file( f"🔗 URL de mise à jour Chromium : {SERVEUR_ZIP_URL_EX3}", "INFO" )
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "Ext3.zip")
                settings.write_log_dev_file( "⬇️ [EXTENSION CHROMIUM] Téléchargement de l'archive Chromium", "INFO")
                if not UpdateManager.downloadFile(SERVEUR_ZIP_URL_EX3, zip_path):
                    Settings.write_log_dev_file("🛑 [EXTENSION CHROMIUM] Échec du téléchargement de l'extension Chromium",  "ERROR" )
                    return False
                if os.path.exists(Settings.EXTENTION_EX3_CHROMIUM):
                    Settings.write_log_dev_file(  f"Suppression de l'ancienne extension avant mise à jour", "INFO")
                    shutil.rmtree( Settings.EXTENTION_EX3_CHROMIUM,   onerror=UpdateManager.handleReadonlyRemoval, )
                settings.write_log_dev_file("Extracting ZIP file...", "INFO")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)
                extracted_dir = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path) and item != "__MACOSX":
                        extracted_dir = item_path
                        break
                if extracted_dir is None:
                    Settings.write_log_dev_file("Dossier extrait introuvable", "ERROR")
                    return False
                shutil.move(extracted_dir, Settings.EXTENTION_EX3_CHROMIUM)
                Settings.write_log_dev_file(  f"Extension mise à jour vers la version {remote_version}", "INFO" )
                return True
        except Exception as e:
            Settings.write_log_dev_file( f"❌ Erreur lors de la mise à jour : {e}\n{traceback.format_exc()}","ERROR" )
            traceback.print_exc()
            return False




