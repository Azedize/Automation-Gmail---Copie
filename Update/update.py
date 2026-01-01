import os
import sys
import shutil
import zipfile
import tempfile
import requests
import traceback
import subprocess
from typing import Optional

# ==========================================================
# 📁 ROOT DIR
# ==========================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import Settings


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
    def _download_and_extract(
        zip_url: str,
        target_dir: str,
        clean_target: bool = False,
        extract_subdir:  Optional[str] = None,
    ):
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
    def check_and_update() -> None:
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
        """Lance une nouvelle instance silencieuse"""
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.py")

        if not os.path.isfile(script_path):
            print(f"[LAUNCH] Script introuvable : {script_path}")
            return False

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.Popen(
                [sys.executable, script_path],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return True

        except Exception:
            print("[LAUNCH] Échec lancement")
            return False


# ==========================================================
# ▶️ POINT D’ENTRÉE
# ==========================================================
UpdateManager.check_and_update()
