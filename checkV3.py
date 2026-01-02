import os
import sys
import shutil
import zipfile
import traceback
import importlib
import subprocess
import time
from pathlib import Path
import tempfile
import requests
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

from config import Settings
from core import EncryptionService
from Log import DevLogger


# Configuration des chemins
SCRIPT_DIR = Path(__file__).resolve().parent


# ==========================================================
# 🔹 CLASSE GESTION DES DÉPENDANCES
# ==========================================================
class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():
        """Vérifie et installe pywin32 si nécessaire"""
        python_exe = sys.executable
        
        # Vérifier si pywin32 est déjà installé
        spec = importlib.util.find_spec("win32api")
        if spec:
            DevLogger.info("[INFO] pywin32 est déjà installé")
            return True

        DevLogger.info("[INFO] Installation de pywin32...")
        
        # Supprimer les anciens dossiers
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]
        
        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    DevLogger.info(f"[INFO] Suppression de : {folder}")
                except PermissionError:
                    DevLogger.error(f"[WARN] Impossible de supprimer {folder}. Veuillez fermer Python/IDE.")

        # Installation de pywin32
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            DevLogger.info("[INFO] pywin32 installé avec succès")
        except subprocess.CalledProcessError:
            DevLogger.error("[ERROR] Échec de l'installation de pywin32")
            return False

        # Exécution du post-install
        postinstall_script = Path(python_exe).parent / "Scripts" / "pywin32_postinstall.py"
        if postinstall_script.exists():
            try:
                subprocess.run(
                    [python_exe, str(postinstall_script), "-install"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                DevLogger.info("[INFO] Post-installation terminée")
            except subprocess.CalledProcessError:
                DevLogger.error("[ERROR] Échec du post-install")
                return False

        # Redémarrage du script
        DevLogger.info("[INFO] Redémarrage dans 10 secondes...")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True

    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
        
        if package.lower() == "pywin32":
            module_name = "win32api"

        module_to_import = module_name or package
        install_spec = f"{package}=={version}" if version else package

        try:
            module = importlib.import_module(module_to_import)
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")
            return module
        except (ModuleNotFoundError, ImportError):
            Settings.ALL_PACKAGES_INSTALLED = False
            DevLogger.info(f"[INFO] Installation de {package}...")

            # Mise à jour de pip si nécessaire
            if not Settings.UPDATED_PIP_23_3:
                try:
                    DevLogger.info("[INFO] Mise à jour de pip...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
                    Settings.UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    DevLogger.error("[WARN] Erreur lors de la mise à jour de pip")
                    sys.exit()

            # Installation du package
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
                DevLogger.info(f"[INFO] {package} installé")
            except subprocess.CalledProcessError:
                DevLogger.error(f"[ERROR] Erreur d'installation de {package}")
                sys.exit()

            # Import après installation
            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                DevLogger.error(f"[ERROR] Erreur lors de l'import de {module_to_import} : {e}")
                sys.exit()

# ==========================================================
# 🔹 CLASSE GESTION DES UPDATES
# ==========================================================
class UpdateManager:

    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            DevLogger.error("[ERROR] Erreur lors de la lecture de la version locale")
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            DevLogger.info(f"[INFO] Téléchargement depuis : {zip_url}")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                # téléchargement
                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()

                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)

                DevLogger.info("[INFO] ZIP téléchargé avec succès")

                # إزالة المجلد القديم إذا clean_target = True
                if clean_target and os.path.exists(target_dir):
                    DevLogger.info(f"[INFO] Suppression du dossier cible : {target_dir}")
                    shutil.rmtree(target_dir)

                # استخراج ZIP مؤقتاً
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                    DevLogger.info(f"[INFO] ZIP extrait temporairement dans {tmpdir}")

                # العثور على المجلد الرئيسي
                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )
                DevLogger.info(f"[INFO] Dossier principal extrait : {extracted_root}")

                # التعامل مع extract_subdir إذا موجود
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                        DevLogger.info(f"[INFO] Sous-dossier extrait : {extracted_dir}")
                    else:
                        DevLogger.warning(f"[WARN] Subfolder '{extract_subdir}' non trouvé, utilisation du dossier racine")
                        extracted_dir = extracted_root
                else:
                    extracted_dir = extracted_root

                # التأكد أن المجلد الهدف موجود
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    DevLogger.info(f"[INFO] Création du dossier cible : {target_dir}")

                # نقل الملفات من extracted_dir إلى target_dir
                for item in os.listdir(extracted_dir):
                    s = os.path.join(extracted_dir, item)
                    d = os.path.join(target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                            DevLogger.info(f"[INFO] Suppression du dossier existant : {d}")
                        shutil.move(s, d)
                        DevLogger.info(f"[INFO] Dossier extrait et transféré : {s}")
                    else:
                        shutil.move(s, d)
                        DevLogger.info(f"[INFO] Fichier extrait et transféré : {s}")

                DevLogger.info(f"[INFO] Extraction terminée dans : {target_dir}")

        except Exception as e:
            DevLogger.error("[ERROR] Erreur dans _download_and_extract :", e)
            traceback.print_exc()
            raise e

    @staticmethod
    def check_and_update() -> bool:
        DevLogger.info("[INFO] Run FuncTion : check_and_update()")
        try:
            from api.base_client import APIManager

            # -------------------------------
            # 🌐 APPEL SERVEUR pour récupérer versions
            # -------------------------------
            response = APIManager.make_request(
                "__CHECK_URL_PROGRAMM__", method="GET", timeout=10
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                return True

            data = response.get("data", {})
            server_program = data.get("version_Programme")
            server_ext = data.get("version_extension")

            local_program = UpdateManager._read_local_version(Settings.VERSION_LOCAL_PROGRAMM)
            local_ext = UpdateManager._read_local_version(Settings.VERSION_LOCAL_EXT)

            DevLogger.info(f"[INFO] Version programme locale : {local_program}")
            DevLogger.info(f"[INFO] Version extensions locale : {local_ext}")

            if not local_program or local_program != server_program:
                print("[INFO] MISE À JOUR PROGRAMME REQUISE")
                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    ROOT_DIR,
                    clean_target=False,
                    extract_subdir=None
                )
                DevLogger.info("[INFO] Arrêt après mise à jour programme")
                return True

            if not local_ext or local_ext != server_ext:
                DevLogger.info("[INFO] MISE À JOUR EXTENSIONS REQUISE")
                tools_dir = Settings.TOOLS_DIR
                if not os.path.exists(tools_dir):
                    os.makedirs(tools_dir)

                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    tools_dir,
                    clean_target=True,
                    extract_subdir="tools"
                )
                DevLogger.info("[INFO] Extensions mises à jour, poursuite normale")
                return True

            DevLogger.info("[INFO] APPLICATION À JOUR – AUCUNE ACTION")
            return False

        except Exception as e:
            DevLogger.error("[ERROR] ERREUR CRITIQUE → UPDATE PAR SÉCURITÉ")
            traceback.print_exc()
            return True

# ==========================================================
# 🔹 INITIALISATION DES DÉPENDANCES
# ==========================================================
def initialize_dependencies():
    DependencyManager.install_and_verify_pywin32()
    
    global requests, urllib3, PyQt6, cryptography_module, psutil, pytz, tqdm, platformdirs, selenium, dotenv
    
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
    selenium = DependencyManager.install_and_import("selenium", module_name="selenium", required_import="webdriver", version="4.27.1")
    jsonschema = DependencyManager.install_and_import("jsonschema")
    

    
    from tqdm import tqdm
    from platformdirs import user_downloads_dir
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    import ctypes





# ==========================================================
# 🔹 MAIN
# ==========================================================

def main():
    try:
        DevLogger.init_logger(log_file="Log/LogDev/my_project.log")

        # if sys.platform == "win32":
        #         ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


        initialize_dependencies()
        pythonw_path = Settings.find_pythonw()
        if not pythonw_path:
            DevLogger.error("[ERROR] pythonw.exe introuvable")
            sys.exit(1)

        try:
            updated = UpdateManager.check_and_update()
            if updated:
                DevLogger.info("[INFO] UPDATE EFFECTUÉ")
            else:
                DevLogger.info("[INFO] APPLICATION À JOUR")
        except Exception as e:
            DevLogger.error("[WARN] ERREUR CRITIQUE LORS DU CHECK/UPDATE")
            DevLogger.error(f"[WARN] Détails : {e}")
            traceback.print_exc()
        

        
        # sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')
        # sys.stdin = open(os.devnull, 'r')
        
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        if len(sys.argv) == 1:

            encrypted_key, secret_key = EncryptionService.generate_encrypted_key()
            script_path = SCRIPT_DIR / 'src' / 'AppV2.py'
            if script_path.is_file():
                subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])
            else:
                DevLogger.error(f"[ERROR] Fichier introuvable : {script_path}")
                sys.exit(1)

    except Exception as e:
        DevLogger.error(f"[FATAL] Erreur fatale : {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
