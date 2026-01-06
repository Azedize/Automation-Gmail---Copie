# ==========================================================
# main.py
# Version complète avec DevLogger et sécurité
# ==========================================================

import os
import sys
import shutil
import zipfile
import importlib
import subprocess
import time
from pathlib import Path
import tempfile
import io

# ==========================================================
# 🔹 FIX UTF-8 POUR WINDOWS CONSOLE
# ==========================================================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==========================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ==========================================================
# 🔹 IMPORTS INTERNES
# ==========================================================
from config import Settings
from core import EncryptionService
# from Log import DevLogger

SCRIPT_DIR = Path(__file__).resolve().parent

# ==========================================================
# 🔹 CLASSE GESTION DES DÉPENDANCES
# ==========================================================
class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():
        python_exe = sys.executable
        spec = importlib.util.find_spec("win32api")
        if spec:
            print("pywin32 déjà installé")
            return True

        print("Installation de pywin32...")
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]

        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    print(f"Suppression de {folder}")
                except PermissionError:
                    print(f"Impossible de supprimer {folder} (fermez IDE/console)")

        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("pywin32 installé avec succès")
        except subprocess.CalledProcessError:
            print("Échec installation pywin32")
            return False

        postinstall_script = Path(python_exe).parent / "Scripts" / "pywin32_postinstall.py"
        if postinstall_script.exists():
            try:
                subprocess.run(
                    [python_exe, str(postinstall_script), "-install"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("Post-installation terminée")
            except subprocess.CalledProcessError:
                print("Échec post-installation pywin32")
                return False

        print("Redémarrage script dans 10s...")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True

    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
        module_to_import = module_name or package
        install_spec = f"{package}=={version}" if version else package

        try:
            module = importlib.import_module(module_to_import)
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")
            return module
        except (ModuleNotFoundError, ImportError):
            Settings.ALL_PACKAGES_INSTALLED = False
            print(f"Installation de {package}...")

            if not Settings.UPDATED_PIP_23_3:
                try:
                    print("Mise à jour pip...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
                    Settings.UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    print("Erreur mise à jour pip")
                    sys.exit()

            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
                print(f"{package} installé")
            except subprocess.CalledProcessError:
                print(f"Erreur installation {package}")
                sys.exit()

            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                print(f"Erreur import {module_to_import}")
                sys.exit()


# ==========================================================
# 🔹 CLASSE GESTION DES UPDATES
# ==========================================================
class UpdateManager:

    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            print("Version locale introuvable")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            print("Erreur lecture version locale")
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            print("Téléchargement mise à jour depuis serveur")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests
                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                print("ZIP téléchargé avec succès")

                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    print("Ancien dossier cible supprimé")

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                print("Extraction ZIP temporaire terminée")

                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )

                extracted_dir = extracted_root
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                        print(f"Sous-dossier extrait : {extract_subdir}")

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                for item in os.listdir(extracted_dir):
                    s = os.path.join(extracted_dir, item)
                    d = os.path.join(target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.move(s, d)
                    else:
                        shutil.move(s, d)

                print(f"Extraction terminée dans : {target_dir}")

        except Exception:
            print("Erreur téléchargement/extraction update")
            raise

    @staticmethod
    def check_and_update() -> bool:
        print("Vérification mise à jour")
        try:
            from api.base_client import APIManager
            response = APIManager.make_request("__CHECK_URL_PROGRAMM__", method="GET", timeout=10)

            if not isinstance(response, dict) or response.get("status_code") != 200:
                return True

            data = response.get("data", {})
            server_program = data.get("version_Programme")
            server_ext = data.get("version_extension")

            local_program = UpdateManager._read_local_version(Settings.VERSION_LOCAL_PROGRAMM)
            local_ext = UpdateManager._read_local_version(Settings.VERSION_LOCAL_EXT)

            if not local_program or local_program != server_program:
                print("MISE À JOUR PROGRAMME REQUISE")
                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    ROOT_DIR,
                    clean_target=False,
                    extract_subdir=None
                )
                return True

            if not local_ext or local_ext != server_ext:
                print("MISE À JOUR EXTENSIONS REQUISE")
                tools_dir = Settings.TOOLS_DIR
                if not os.path.exists(tools_dir):
                    os.makedirs(tools_dir)
                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    tools_dir,
                    clean_target=True,
                    extract_subdir="tools"
                )
                return True

            print("APPLICATION À JOUR – AUCUNE ACTION")
            return False

        except Exception:
            print("Erreur critique update")
            return True


# ==========================================================
# 🔹 INITIALISATION DÉPENDANCES
# ==========================================================
def initialize_dependencies():
    print("Initialisation des dépendances")
    DependencyManager.install_and_verify_pywin32()

    global requests, urllib3, PyQt6, cryptography_module, psutil, pytz, tqdm, platformdirs, selenium
    requests = DependencyManager.install_and_import("requests")
    urllib3 = DependencyManager.install_and_import("urllib3", version="2.2.3")
    if urllib3:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    PyQt6 = DependencyManager.install_and_import("PyQt6", version="6.7.0", required_import="QtCore")
    cryptography_module = DependencyManager.install_and_import("cryptography", version="3.3.2")
    psutil = DependencyManager.install_and_import("psutil")
    pytz = DependencyManager.install_and_import("pytz")
    tqdm = DependencyManager.install_and_import("tqdm")
    platformdirs = DependencyManager.install_and_import("platformdirs")
    selenium = DependencyManager.install_and_import("selenium", required_import="webdriver", version="4.27.1")


# ==========================================================
# 🔹 MAIN
# ==========================================================
def main():
    try:
        # DevLogger.init_logger(log_file="Log/LogDev/my_project.log")
        print("Démarrage application principale")

        initialize_dependencies()

        pythonw_path = Settings.find_pythonw()
        if not pythonw_path:
            # DevLogger.critical("pythonw.exe introuvable")
            sys.exit(1)

        updated = UpdateManager.check_and_update()
        if updated:
            print("UPDATE EFFECTUÉ")
        else:
            print("APPLICATION À JOUR")

        if len(sys.argv) == 1:
            print("Lancement de l'application principale")
            encrypted_key, secret_key = EncryptionService.generate_encrypted_key()
            # ❌ Ne jamais logger ces clés

            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])
            else:
                print("Script principal introuvable")
                sys.exit(1)

    except Exception:
        print("Erreur fatale application")
        sys.exit(1)


if __name__ == "__main__":
    main()
