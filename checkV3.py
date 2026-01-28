# ==========================================================
# main.py
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
import datetime


from pathlib import Path
import traceback
TOOLS_DIR = Path("Tools")
EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"




# 
LOG_DEV_FILE = os.path.abspath(os.path.join( "Log/LogDev/my_project.log"))

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

SCRIPT_DIR = Path(__file__).resolve().parent


def generate_encrypted_key():
    from cryptography.fernet import Fernet
    
    secret_key = Fernet.generate_key()
    fernet = Fernet(secret_key)
    encrypted_message = fernet.encrypt(b"authorized")
    
    return encrypted_message.decode(), secret_key.decode()





def WRITE_LOG_DEV_FILE( message: str, level: str = "INFO"):
    try:
        # Génération de la date et heure actuelle pour le timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"

        # Vérifie que le dossier contenant le fichier de log existe, sinon le crée
        log_path = Path(LOG_DEV_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Ouvre le fichier en mode "append" pour ajouter la ligne de log à la fin
        with open(LOG_DEV_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)

    except Exception as e:
        # print(f"❌ [LOG] Erreur lors de l'écriture du log: {e}")
        pass


def clear_log():
    try:
        log_path = Path(LOG_DEV_FILE)
        if log_path.exists():
            # Ouvre le fichier en mode "write" pour effacer tout son contenu
            open(log_path, "w", encoding="utf-8").close()
            # print(f"✅ [LOG] Fichier log vidé: {LOG_DEV_FILE}")
        # else:
        #     print(f"⚠️ [LOG] Fichier log inexistant: {LOG_DEV_FILE}")

    except Exception as e:
        # print(f"❌ [LOG] Erreur lors de la suppression du fichier log: {e}")
        pass



def find_pythonw():
    base_dir = os.path.dirname(sys.executable)
    candidate = os.path.join(base_dir, "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate

    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path.strip('"'), "pythonw.exe")
        if os.path.isfile(candidate):
            return candidate

    return None


# ==========================================================
# 🔹 CLASSE GESTION DES DÉPENDANCES
# ==========================================================
class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():
        python_exe = sys.executable
        spec = importlib.util.find_spec("win32api")
        if spec:
            # print("pywin32 déjà installé")
            WRITE_LOG_DEV_FILE("pywin32 already installed", "INFO")
            return True

        # print("Installation de pywin32...")
        WRITE_LOG_DEV_FILE("Installing pywin32...", "INFO")
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]

        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    # print(f"Suppression de {folder}")
                    WRITE_LOG_DEV_FILE(f"Removed {folder}", "INFO")
                except PermissionError:
                    # print(f"Impossible de supprimer {folder} (fermez IDE/console)")
                    WRITE_LOG_DEV_FILE(f"Impossible de supprimer {folder} (fermez IDE/console)", "ERROR")


        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # print("pywin32 installé avec succès")
            WRITE_LOG_DEV_FILE("pywin32 installed successfully", "INFO")
        except subprocess.CalledProcessError:
            # print("Échec installation pywin32")
            WRITE_LOG_DEV_FILE("Failed to install pywin32", "ERROR")
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
                # print("Post-installation terminée")
                WRITE_LOG_DEV_FILE("Post-installation completed", "INFO")
            except subprocess.CalledProcessError:
                # print("Échec post-installation pywin32")
                WRITE_LOG_DEV_FILE("Failed post-installation pywin32", "ERROR")
                return False

        # print("Redémarrage script dans 10s...")
        WRITE_LOG_DEV_FILE("Restarting script in 10s...", "INFO")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True

    
    
    
    
    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
        module_to_import = module_name or package
        install_spec = f"{package}=={version}" if version else package
        UPDATED_PIP_23_3 = False
        try:
            module = importlib.import_module(module_to_import)
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")
            return module
        except (ModuleNotFoundError, ImportError):
            ALL_PACKAGES_INSTALLED = False
            # print(f"Installation de {package}...")
            WRITE_LOG_DEV_FILE(f"Installing {package}...", "INFO")

            if not UPDATED_PIP_23_3:
                try:
                    # print("Mise à jour pip...")
                    WRITE_LOG_DEV_FILE("Updating pip...", "INFO")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
                    UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    # print("Erreur mise à jour pip")
                    WRITE_LOG_DEV_FILE("Error updating pip", "ERROR")
                    sys.exit()

            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
                # print(f"{package} installé")
                WRITE_LOG_DEV_FILE(f"{package} installed", "INFO")
            except subprocess.CalledProcessError:
                # print(f"Erreur installation {package}")
                WRITE_LOG_DEV_FILE(f"Error installing {package}", "ERROR")
                sys.exit()

            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                # print(f"Erreur import {module_to_import}")
                WRITE_LOG_DEV_FILE(f"Error importing {module_to_import}", "ERROR")
                sys.exit()


# ==========================================================
# 🔹 CLASSE GESTION DES UPDATES
# ==========================================================
class UpdateManager:

    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            # print("Version locale introuvable")
            WRITE_LOG_DEV_FILE("Local version not found", "ERROR")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            WRITE_LOG_DEV_FILE("Error reading local version", "ERROR")
            # print("Erreur lecture version locale")
            return None
        



    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            # print("Téléchargement mise à jour depuis serveur")
            WRITE_LOG_DEV_FILE("Downloading update from server", "INFO")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests
                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                # print("ZIP téléchargé avec succès")
                WRITE_LOG_DEV_FILE("ZIP downloaded successfully", "INFO")

                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    # print("Ancien dossier cible supprimé")
                    WRITE_LOG_DEV_FILE("Old target directory removed", "INFO")

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                # print("Extraction ZIP temporaire terminée")
                WRITE_LOG_DEV_FILE("Temporary ZIP extraction completed", "INFO")

                extracted_root = next( os.path.join(tmpdir, d)  for d in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, d)) )

                extracted_dir = extracted_root
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                        # print(f"Sous-dossier extrait : {extract_subdir}")
                        WRITE_LOG_DEV_FILE(f"Subdirectory extracted: {extract_subdir}", "INFO")

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

                # print(f"Extraction terminée dans : {target_dir}")
                WRITE_LOG_DEV_FILE(f"Extraction completed in: {target_dir}", "INFO")
                return True

        except Exception:
            # print("Erreur téléchargement/extraction update")
            WRITE_LOG_DEV_FILE("Error downloading/extracting update", "ERROR")
            raise

    
    
    
    @staticmethod
    def check_and_update():
        WRITE_LOG_DEV_FILE("Checking for updates", "INFO")
        import requests

        url = "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1"

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Failed to fetch version.json (status {response.status_code})", "ERROR")
                    if attempt < max_attempts:
                        time.sleep(2)  
                        continue
                    return True

                data = response.json()
                server_program = data.get("version_Programme")
                server_ext = data.get("version_extension")

                local_program = UpdateManager._read_local_version(os.path.join("config", "version.txt"))
                local_ext = UpdateManager._read_local_version(os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt"))

                if not local_program or local_program != server_program:
                    WRITE_LOG_DEV_FILE("Required program update", "INFO")
                    UpdateManager._download_and_extract("https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/master.zip", ROOT_DIR, clean_target=False , extract_subdir=None)
                    return True

                if not local_ext or local_ext != server_ext:
                    WRITE_LOG_DEV_FILE("Required extensions update", "INFO")
                    tools_dir = TOOLS_DIR
                    if not os.path.exists(tools_dir):
                        os.makedirs(tools_dir)
                    UpdateManager._download_and_extract( "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/master.zip", tools_dir, clean_target=True,  extract_subdir="tools" )
                    return True

                WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")
                return False

            except Exception as e:
                WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Critical update error: {e}", "ERROR")
                if attempt < max_attempts:
                    time.sleep(2)  #    المحاولة
                    continue
                return True



# ==========================================================
# 🔹 INITIALISATION DÉPENDANCES
# ==========================================================
def initialize_dependencies():
    # print("Initialisation des dépendances")

    WRITE_LOG_DEV_FILE("Initialisation des dépendances" , level="INFO")

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
        WRITE_LOG_DEV_FILE("Démarrage application principale", level="INFO")

        initialize_dependencies()
    

        pythonw_path = find_pythonw()
        if not pythonw_path:
            # DevLogger.critical("pythonw.exe introuvable")
            WRITE_LOG_DEV_FILE("pythonw.exe not found", "ERROR")
            sys.exit(1)

        updated = UpdateManager.check_and_update()
        # if updated:
        #     print("UPDATE EFFECTUÉ")
        #     WRITE_LOG_DEV_FILE("Update completed", "INFO")
        # else:
        #     print("APPLICATION À JOUR")
        #     WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")

        if len(sys.argv) == 1:
            # print("Lancement de l'application principale")
            WRITE_LOG_DEV_FILE("Launching main application", "INFO")
            encrypted_key, secret_key = generate_encrypted_key()
            # ❌ Ne jamais logger ces clés

            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])
            else:
                # print("Script principal introuvable")
                WRITE_LOG_DEV_FILE("Main script not found", "ERROR")
                sys.exit(1)

    
    except Exception as e:
        print(f"Erreur fatale application: {e}")
        
        # Pour afficher plus de détails sur l'erreur
        print("Détails de l'erreur:")
        traceback.print_exc()  # Affiche la stack trace complète
        
        # Écriture dans le log
        WRITE_LOG_DEV_FILE(f"Fatal application error: {e}", "ERROR")
        
        # Pour conserver aussi la trace dans les logs
        error_details = traceback.format_exc()
        WRITE_LOG_DEV_FILE(f"Error details:\n{error_details}", "ERROR")
        
        sys.exit(1)  # Quitte l'application avec code d'erreur

if __name__ == "__main__":
    main()



