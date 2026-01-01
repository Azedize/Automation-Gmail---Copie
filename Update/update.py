import os
import sys
import shutil
import zipfile
import tempfile
import requests
import traceback
import subprocess
from typing import Optional
import json


# ==========================================================
# 📁 ROOT DIR
# ==========================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import Settings
from ui_utils import UIManager

class UpdateManager:
    # ==========================================================
    # 🔹 UTILITAIRES
    # ==========================================================
    @staticmethod
    def _read_local_version(path: str):
        """Lire une version depuis un fichier texte"""
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None

    @staticmethod
    def _download_and_extract( zip_url: str, target_dir: str, clean_target: bool = False, extract_subdir:  Optional[str] = None):
        """Télécharge un ZIP et l’extrait proprement"""
        try:
            print(f"\n⬇️ Téléchargement : {zip_url}")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()

                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)

                print("📦 ZIP téléchargé")

                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)

                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )

                extracted_dir = (
                    os.path.join(extracted_root, extract_subdir)
                    if extract_subdir
                    and os.path.exists(os.path.join(extracted_root, extract_subdir))
                    else extracted_root
                )

                os.makedirs(target_dir, exist_ok=True)

                for item in os.listdir(extracted_dir):
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(target_dir, item)

                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.move(src, dst)
                    else:
                        shutil.move(src, dst)

                print(f"✅ Extraction terminée → {target_dir}")

        except Exception:
            print("❌ Erreur download/extract")
            traceback.print_exc()
            raise

    # ==========================================================
    # 🔥 LOGIQUE PRINCIPALE
    # ==========================================================
    @staticmethod
    def check_and_update( Window) -> None:
        """
        🔴 PROGRAMME changé :
            - Lance nouvelle instance
            - Quitte immédiatement
            - ❌ Ne touche PAS aux tools

        🟡 TOOLS changés :
            - Met à jour tools
            - Continue

        🟢 Rien changé :
            - Continue
        """
        try:
            from api.base_client import APIManager

            print("\n" + "=" * 80)
            print("🔍 CHECK UPDATE")
            print("=" * 80)

            response = APIManager.make_request(
                "__CHECK_URL_PROGRAMM__", method="GET", timeout=10
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                print("⚠️ Serveur indisponible → Continuer")
                return

            data = response.get("data", {})
            server_program = data.get("version_Programme")
            server_tools = data.get("version_extension")

            local_program = UpdateManager._read_local_version(
                Settings.VERSION_LOCAL_PROGRAMM
            )
            local_tools = UpdateManager._read_local_version(
                Settings.VERSION_LOCAL_EXT
            )

            print(f"Programme serveur : {server_program}")
            print(f"Programme local   : {local_program}")
            print(f"Tools serveur     : {server_tools}")
            print(f"Tools local       : {local_tools}")

            # ==================================================
            # 🔴 UPDATE PROGRAMME (STRICT)
            # ==================================================
            if not local_program or local_program != server_program:
                print("\n🔴 UPDATE PROGRAMME")
                # close window 
                if Window:
                    print(f"[DEBUG] Fermeture de la fenêtre : {Window}")
                    Window.close()
                    print("[DEBUG] Fenêtre fermée avec succès")
                else:
                    print("[DEBUG] Aucune fenêtre ouverte")



                # ⚠️ AUCUN code tools ici
                UpdateManager.launch_new_window()

                print("⛔ Quitter instance actuelle")
                sys.exit(0)

            # ==================================================
            # 🟡 UPDATE TOOLS
            # ==================================================
            if not local_tools or local_tools != server_tools:
                print("\n🟡 UPDATE TOOLS")

                os.makedirs(Settings.TOOLS_DIR, exist_ok=True)

                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    Settings.TOOLS_DIR,
                    clean_target=True,
                    extract_subdir="tools",
                )

                print("✅ Tools mis à jour")

            print("\n🟢 Application à jour")

        except Exception:
            print("🔥 ERREUR CRITIQUE → Continuer")
            traceback.print_exc()

    # ==========================================================
    # 🚀 LANCEMENT NOUVELLE INSTANCE
    # ==========================================================
    @staticmethod
    def launch_new_window() -> bool:
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.py")
        print(f"[DEBUG] Chemin du script à lancer : {script_path}")

        if not os.path.isfile(script_path):
            print(f"[LAUNCH] Script introuvable : {script_path}")
            return False

        try:
            # Utiliser pythonw.exe si possible (Windows)
            python_exe = sys.executable
            if sys.platform == "win32":
                pythonw_candidate = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                if os.path.isfile(pythonw_candidate):
                    python_exe = pythonw_candidate

            # Lancer le subprocess en arrière-plan
            subprocess.Popen(
                [python_exe, script_path],
                cwd=Settings.BASE_DIR,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            print("[DEBUG] Nouvelle instance lancée avec succès")
            return True

        except Exception as e:
            print("[LAUNCH] Échec du lancement")
            print(f"[DEBUG] Exception: {str(e)}")
            traceback.print_exc()
            return False




    
    @staticmethod
    def Check_Version_Extention(window):
        """
        Checks and updates the Chrome extension if necessary.
        Returns:
            str  -> returns the remote version if an update is required
            True -> extension exists and is up to date
            False -> failure (download issue, fetch remote error, manifest mismatch, or missing local extension files)
        """
        try:
            #print("\n🔎 Checking local and remote extension versions...")

            # Fetch remote version
            try:
                response = requests.get(Settings.CHECK_URL_EX3, verify=False, timeout=10)
                response.raise_for_status()
                data = response.json()
                remote_version = data.get("version_Extention")
                remote_manifest_version = data.get("manifest_version")

                print("\n=== JSON Response ===")
                print(json.dumps(data, indent=4, ensure_ascii=False))
                print("\n=== Retrieved Versions ===")
                print(f"➤ version_Extention     : {remote_version}")
                print(f"➤ manifest_version      : {remote_manifest_version}")

            except Exception as e:
                #print(f"❌ Unable to fetch remote version: {e}")
                UIManager.Show_Critical_Message(
                    window,
                    "Network / Remote Version Error",
                    f"Unable to fetch the remote version. Check your connection or contact support.\n\nTechnical details: {str(e).capitalize()}",
                    message_type="critical"
                )
                return False

            # Check local files
            if not os.path.exists(Settings.MANIFEST_PATH_EX3) or not os.path.exists(Settings.VERSION_LOCAL_EX3):
                #print("⚠️ Local files missing for version check.")
                UIManager.Show_Critical_Message(
                    window,
                    "Missing Local Files",
                    "The local extension files could not be found. Please reinstall the extension.",
                    message_type="critical"
                )
                return False

            # Read local manifest
            with open(Settings.MANIFEST_PATH_EX3, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            local_manifest_version = manifest_data.get("version", None)

            # Read local version
            with open(Settings.VERSION_LOCAL_EX3, "r", encoding="utf-8") as f:
                local_version = f.read().strip()

            #print(f"📄 Local version : {local_version}, Local manifest : {local_manifest_version}")
            #print(f"🌍 Remote version : {remote_version}, Remote manifest : {remote_manifest_version}")

            # Check manifest compatibility
            if str(local_manifest_version) != str(remote_manifest_version):
                UIManager.Show_Critical_Message(
                    window,
                    "Manifest Incompatibility",
                    "The local manifest version does not match the remote one.\nPlease contact support.",
                    message_type="critical"
                )
                #print("⚠️ Manifest incompatible, automatic update not possible.")
                return False

            # Check version difference
            if local_version != remote_version:
                #print(f"🔄 Update required (new version: {remote_version})")
                return remote_version  # update required
            else:
                #print("✅ Local extension is up to date.")
                return True  # already up to date

        except Exception as e:
            #print(f"❌ Unexpected error in Check_Version_Extention: {e}")
            UIManager.Show_Critical_Message(
                window,
                "Internal Error",
                "An unexpected error occurred during extension verification. Please contact support.",
                message_type="critical"
            )
            return False


# ==========================================================
# ▶️ POINT D’ENTRÉE
# ==========================================================
UpdateManager = UpdateManager()
