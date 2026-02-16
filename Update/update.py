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
    from api.base_client import APIManager

except ImportError as e:
    # print(f"[ERROR] Import modules failed: {e}")
    pass










class UpdateManager:

    
    # ==========================================================
    # 🔹 UTILITAIRES
    # ==========================================================
    @staticmethod
    def _read_local_version(path: str) -> Optional[str]:
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None

    @staticmethod
    def _download_file(url: str, dest_path: str) -> bool:
        try:
            # print(f"⬇️ Téléchargement depuis : {url}")
            response = requests.get(url, stream=True, verify=False, timeout=60)
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
                            # print(f"   → Progression : {percent:.2f}%", end="\r")
            # print(f"\n✅ Téléchargement terminé : {dest_path}")
            Settings.WRITE_LOG_DEV_FILE("Téléchargement réussi : ", "INFO")
            return True
        except Exception as e:
            # print(f"❌ Erreur lors du téléchargement : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lors du téléchargement : - {e}", "ERROR")
            return False

    @staticmethod
    def _remove_readonly(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    
    
    
    @staticmethod
    def _download_and_extract(zip_url: str, target_dir: str, clean_target: bool = False, extract_subdir: Optional[str] = None) -> bool:
        try:
            # print(f"\n⬇️ Téléchargement : {zip_url}")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                # Téléchargement
                if not UpdateManager._download_file(zip_url, zip_path):
                    Settings.WRITE_LOG_DEV_FILE("Échec du téléchargement pour mise à jour", "ERROR")
                    return False

                # print("📦 ZIP téléchargé")

                # Nettoyage du répertoire cible si demandé
                if clean_target and os.path.exists(target_dir):
                    Settings.WRITE_LOG_DEV_FILE(f"Nettoyage du répertoire cible avant extraction ", "INFO")
                    shutil.rmtree(target_dir, onerror=UpdateManager._remove_readonly)

                # Extraction
                with zipfile.ZipFile(zip_path, "r") as z:
                    Settings.WRITE_LOG_DEV_FILE("Extraction du ZIP téléchargé", "INFO")
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
                    Settings.WRITE_LOG_DEV_FILE("Aucun dossier trouvé dans l'archive", "ERROR")
                    return False

                # Gestion du sous-répertoire
                extracted_dir = (
                    os.path.join(extracted_root, extract_subdir)
                    if extract_subdir and os.path.exists(os.path.join(extracted_root, extract_subdir))
                    else extracted_root
                )

                os.makedirs(target_dir, exist_ok=True)

                # Déplacement des fichiers
                for item in os.listdir(extracted_dir):
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(target_dir, item)

                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst, onerror=UpdateManager._remove_readonly)
                        shutil.move(src, dst)
                    else:
                        if os.path.exists(dst):
                            os.remove(dst)
                        shutil.move(src, dst)

                # print(f"✅ Extraction terminée → {target_dir}")
                return True

        except Exception as e:
            # print("❌ Erreur lors de l'extraction")
            traceback.print_exc()
            return False

    # ==========================================================
    # 🔥 LOGIQUE PRINCIPALE DE MISE À JOUR
    # ==========================================================
    @staticmethod
    def check_and_update(window=None) -> None:

        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            # print("[SESSION] ❌ Session invalide. Impossible de continuer.")
            sys.exit()
            return False



        # ================================================
        # 🔹 Utilisation directe de la date de session
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            # print(f"❌ SESSION_INFO['date'] type incorrect: {type(session_dt)}")
            return False
        # print("🟢 SESSION_INFO['date'] est déjà datetime.datetime")

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        # print("➤ Date session (format YYYY-MM-DD) :", session_date_plain)

        # ================================================
        # 🔹 Chiffrement de la date
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(session_date_plain, Settings.KEY)
            if not date_encrypted:
                raise Exception("Encryption failed")
            encrypted_safe = urllib.parse.quote(date_encrypted)
            # print("🔐 Date encryptée :", encrypted_safe)
        except Exception as e:
            # print(f"❌ Échec du chiffrement : {e}")
            traceback.print_exc()
            return False

        # ================================================
        # 🔹 URL finale pour check
        # ================================================
        CHECK_URL_PROGRAMM = (
            "https://reporting.nrb-apps.com/APP_R/redirect.php"
            f"?nv=1&rv4=1&event=check&type=V4&ext=Script&k={encrypted_safe}"
        )
        # SERVER_ZIP_URL_PROGRAM = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"
        SERVER_ZIP_URL_PROGRAM = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={encrypted_safe}"

        # print("\n🌍 URL finale pour API :", CHECK_URL_PROGRAMM)

        # ================================================
        # 🔹 Requête GET et traitement
        # ================================================
        try:
            # print("\n🔍 CHECK UPDATE")
            response = APIManager.make_request(CHECK_URL_PROGRAMM, method="GET", timeout=10)

            # print("\n=== RAW RESPONSE ===")
            # print(response)

            if not isinstance(response, dict) or response.get("status_code") != 200:
                print("⚠️ Serveur indisponible → Continuer")
                return

            data = response
            inner_data = data.get("data", {})
            server_program = inner_data.get("version")
            server_tools = inner_data.get("version_Extention")

            # print("\n=== Versions serveur ===")
            # print("server_program :", server_program)
            # print("server_tools   :", server_tools)

            local_program = UpdateManager._read_local_version(Settings.VERSION_LOCAL_PROGRAMM)
            local_tools = UpdateManager._read_local_version(Settings.VERSION_LOCAL_EXT)

            # print("\n=== Versions locales ===")
            # print("local_program :", local_program)
            # print("local_tools   :", local_tools)

            # 🔴 Update Programme
            if not local_program or local_program != server_program:
                print("\n🔴 UPDATE PROGRAMME NECESSAIRE")
                if window and hasattr(window, "close"):
                    print("[DEBUG] Fermeture fenêtre")
                    window.close()
                UpdateManager.launch_new_window()
                sys.exit(0)

            # 🟡 Update Tools
            if not local_tools or local_tools != server_tools:
                print("\n🟡 UPDATE TOOLS NECESSAIRE")
                os.makedirs(Settings.TOOLS_DIR, exist_ok=True)
                success = UpdateManager._download_and_extract(
                    SERVER_ZIP_URL_PROGRAM,
                    Settings.TOOLS_DIR,
                    clean_target=True,
                    extract_subdir="tools"
                )
                # if success:
                #     print("✅ Tools mis à jour")
                # else:
                #     print("❌ Échec mise à jour tools")

            # print("\n🟢 Application à jour")

        except ImportError:
            # print("⚠️ APIManager non disponible → Continuer")
            Settings.WRITE_LOG_DEV_FILE("APIManager non disponible", "INFO")

        except Exception:
            # print("🔥 ERREUR CRITIQUE")
            traceback.print_exc()


    # ==========================================================
    # 🚀 LANCEMENT NOUVELLE INSTANCE
    # ==========================================================
    @staticmethod
    def launch_new_window() -> bool:
        """Lance une nouvelle instance de l'application"""
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.py")
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
                creationflags=creation_flags
            )

            # print("[DEBUG] Nouvelle instance lancée avec succès")
            return True

        except Exception as e:
            # print(f"[LAUNCH] Échec du lancement : {e}")
            traceback.print_exc()
            return False



    # ==========================================================
    # 🔌 GESTION DES EXTENSIONS
    # ==========================================================
    @staticmethod
    def check_version_extension(window=None):

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            print("[SESSION] ❌ Session invalide. Impossible de continuer l’extraction.")
            sys.exit()
            return False

   

        # ================================================
        # 🔹 Gestion sécurisée du champ date (datetime uniquement)
        # ================================================
        session_dt = SESSION_INFO.get('date')
        if not isinstance(session_dt, datetime.datetime):
            # print(f"❌ SESSION_INFO['date'] type incorrect: {type(session_dt)}")
            return False
        # print("🟢 SESSION_INFO['date'] est déjà datetime.datetime")

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        # print("➤ Date session (format YYYY-MM-DD) :", session_date_plain)

        # ================================================
        # 🔹 Chiffrement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(session_date_plain, Settings.KEY)
            # print(f"🔐 Date encryptée : {date_encrypted}")
        except Exception as e:
            # print(f"❌ Encryption failed: {e}")
            traceback.print_exc()
            return False

        if not date_encrypted:
            Settings.WRITE_LOG_DEV_FILE("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")

        encrypted_safe = urllib.parse.quote(date_encrypted)
        CHECK_URL_EX3 = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted_safe}"
        # print("\n🌍 URL finale pour API :", CHECK_URL_EX3)

        # ================================================
        # 🔹 Requête GET
        # ================================================
        try:
            response = requests.get(CHECK_URL_EX3, verify=False, timeout=10)
            response.raise_for_status()

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    # print("⚠️ Content-Type incorrect, mais JSON parsé avec succès")
                except Exception as e:
                    # print("❌ Impossible de parser la réponse JSON :", e)
                    # print("Raw response:", response.text)
                    return False

            remote_version = data.get("version_Extention")
            remote_manifest_version = data.get("manifest_version")

            # print("\n=== JSON Response ===")
            # print(json.dumps(data, indent=4, ensure_ascii=False))
            # print(f"➤ version_Extention : {remote_version}")
            # print(f"➤ manifest_version  : {remote_manifest_version}")

        except Exception as e:
            # print(f"❌ Impossible de récupérer la version distante: {e}")
            traceback.print_exc()
            if window:
                from ui_utils import UIManager
                UIManager.Show_Critical_Message(
                    window,
                    "Erreur réseau",
                    "Impossible de vérifier la mise à jour.\nVérifiez votre connexion.",
                    message_type="critical"
                )
            return False

        # ================================================
        # 🔹 Vérification fichiers locaux
        # ================================================
        if not os.path.exists(Settings.MANIFEST_PATH_EX3):
            # print("❌ Fichier manifest.json local introuvable")
            return False
        if not os.path.exists(Settings.VERSION_LOCAL_EX3):
            # print("❌ Fichier version locale introuvable")
            return False

        with open(Settings.MANIFEST_PATH_EX3, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        local_manifest_version = manifest_data.get("version")
        local_version = UpdateManager._read_local_version(Settings.VERSION_LOCAL_EX3)

        # print(f"📄 Version locale : {local_version}")
        # print(f"📄 Manifest local : {local_manifest_version}")

        # ================================================
        # 🔹 Compatibilité manifest
        # ================================================
        if str(local_manifest_version) != str(remote_manifest_version):
            # print("⚠️ Manifest incompatible, mise à jour automatique impossible")
            if window:
                from ui_utils import UIManager
                UIManager.Show_Critical_Message(
                    window,
                    "Incompatibilité manifest",
                    "La version du manifest local ne correspond pas à la distante.",
                    message_type="critical"
                )
            return False

        # ================================================
        # 🔹 Différence de version
        # ================================================
        if local_version != remote_version:
            # print(f"🔄 Mise à jour requise (nouvelle version: {remote_version})")
            return remote_version
        else:
            # print("✅ Extension locale à jour")
            return True




    @staticmethod
    def update_extension_from_server(remote_version=None) -> bool:

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            # print("[SESSION] ❌ Session invalide. Impossible de continuer la mise à jour.")
            Settings.WRITE_LOG_DEV_FILE("Session invalide. Impossible de continuer la mise à jour.", "ERROR")
            sys.exit()
            return False

   

        # ================================================
        # 🔹 Gestion sécurisée du champ date
        # ================================================
        session_dt = SESSION_INFO.get('date')
        if not isinstance(session_dt, datetime.datetime):
            # print(f"❌ SESSION_INFO['date'] type incorrect: {type(session_dt)}")
            Settings.WRITE_LOG_DEV_FILE(f" type incorrect date session: {type(session_dt)}", "ERROR")
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        # print("➤ Date session (format YYYY-MM-DD) :", session_date_plain)

        # ================================================
        # 🔹 Chiffrement du token pour téléchargement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(session_date_plain, Settings.KEY)
            encrypted_safe = urllib.parse.quote(date_encrypted)
            # print(f"🔐 Date encryptée pour API : {encrypted_safe}")
        except Exception as e:
            # print(f"❌ Encryption failed: {e}")
            Settings.WRITE_LOG_DEV_FILE(f"❌ Encryption failed: {e}", "ERROR")
            traceback.print_exc()
            return False

        # ================================================
        # 🔹 URL de téléchargement de l'extension
        # ================================================
        SERVEUR_ZIP_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Ext3&k={encrypted_safe}"
        # print(f"🌍 URL téléchargement : {SERVEUR_ZIP_URL_EX3}")

        # ================================================
        # 🔹 Téléchargement et extraction
        # ================================================
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "Ext3.zip")

                # Téléchargement
                # print("📥 Téléchargement de la dernière version...")
                if not UpdateManager._download_file(SERVEUR_ZIP_URL_EX3, zip_path):
                    # print("❌ Échec du téléchargement")
                    Settings.WRITE_LOG_DEV_FILE("Échec du téléchargement", "ERROR")
                    return False

                # Suppression ancienne version
                if os.path.exists(Settings.EXTENTION_EX3):
                    # print(f"🗑️ Suppression ancien dossier {Settings.EXTENTION_EX3}")
                    Settings.WRITE_LOG_DEV_FILE(f"Suppression de l'ancienne extension avant mise à jour", "INFO")
                    shutil.rmtree(Settings.EXTENTION_EX3, onerror=UpdateManager._remove_readonly)

                # Extraction
                # print("📂 Extraction du fichier ZIP...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
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
                    Settings.WRITE_LOG_DEV_FILE("Dossier extrait introuvable", "ERROR")
                    return False

                # Déplacement vers destination finale
                shutil.move(extracted_dir, Settings.EXTENTION_EX3)
                # print(f"✅ Mise à jour réussie : {Settings.EXTENTION_EX3}")
                Settings.WRITE_LOG_DEV_FILE(f"Extension mise à jour vers la version {remote_version}", "INFO")

                return True

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"❌ Erreur lors de la mise à jour : {e}", "ERROR")
            # print(f"❌ Erreur lors de la mise à jour : {e}")
            traceback.print_exc()
            return False






# ==========================================================
# ▶️ POINT D’ENTRÉE
# ==========================================================
UpdateManager = UpdateManager()
