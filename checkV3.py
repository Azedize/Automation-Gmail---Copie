import os
import sys
import shutil
import zipfile
import traceback
import importlib
import subprocess
import time
from pathlib import Path
from utils import ValidationUtils

import os
import sys
import shutil
import zipfile
import tempfile
import requests
import traceback

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import Settings
from api.base_client import APIManager



# Configuration des chemins
SCRIPT_DIR = Path(__file__).resolve().parent
DIRECTORY_VERSIONS = SCRIPT_DIR / "Programme-main"

# URLs de configuration
CHECK_URL_PROGRAM = "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1"
SERVER_ZIP_URL_PROGRAM = "https://github.com/Azedize/Programme/archive/refs/heads/main.zip"


# Flags d'état
UPDATED_PIP_23_3 = False
ALL_PACKAGES_INSTALLED = True


class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():
        """Vérifie et installe pywin32 si nécessaire"""
        python_exe = sys.executable
        
        # Vérifier si pywin32 est déjà installé
        spec = importlib.util.find_spec("win32api")
        if spec:
            print("✅ pywin32 est déjà installé")
            return True

        print("🔧 Installation de pywin32...")
        
        # Supprimer les anciens dossiers
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]
        
        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    print(f"🗑️ Suppression de : {folder}")
                except PermissionError:
                    print(f"⚠️ Impossible de supprimer {folder}. Veuillez fermer Python/IDE.")

        # Installation de pywin32
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ pywin32 installé avec succès")
        except subprocess.CalledProcessError:
            print("❌ Échec de l'installation de pywin32")
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
                print("✅ Post-installation terminée")
            except subprocess.CalledProcessError:
                print("❌ Échec du post-install")
                return False

        # Redémarrage du script
        print("⏳ Redémarrage dans 10 secondes...")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True



    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
        """Installe et importe un package"""
        global UPDATED_PIP_23_3, ALL_PACKAGES_INSTALLED
        
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
            ALL_PACKAGES_INSTALLED = False
            print(f"📦 Installation de {package}...")

            # Mise à jour de pip si nécessaire
            if not UPDATED_PIP_23_3:
                try:
                    print("🔄 Mise à jour de pip...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
                    UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    sys.exit(f"❌ Erreur lors de la mise à jour de pip")

            # Installation du package
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
                print(f"✅ {package} installé")
            except subprocess.CalledProcessError:
                sys.exit(f"❌ Erreur d'installation de {package}")

            # Import après installation
            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                sys.exit(f"❌ Import impossible : {e}")





class UpdateManager:
    # ==========================================================
    # 🔹 UTILITAIRES
    # ==========================================================
    @staticmethod
    def _read_local_version(path):
        """Lire la version locale depuis un fichier"""
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            print(f"\n⬇️ Téléchargement depuis : {zip_url}")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")

                # téléchargement
                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()

                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)

                print("📦 ZIP téléchargé avec succès")

                # إزالة المجلد القديم إذا clean_target = True
                if clean_target and os.path.exists(target_dir):
                    print(f"🗑️ Suppression du dossier cible : {target_dir}")
                    shutil.rmtree(target_dir)

                # استخراج ZIP مؤقتاً
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                print(f"✅ ZIP extrait temporairement dans {tmpdir}")

                # العثور على المجلد الرئيسي
                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )
                print(f"📁 Dossier principal extrait : {extracted_root}")

                # التعامل مع extract_subdir إذا موجود
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                    else:
                        print(f"⚠️ Subfolder '{extract_subdir}' non trouvé, utilisation du dossier racine")
                        extracted_dir = extracted_root
                else:
                    extracted_dir = extracted_root

                # التأكد أن المجلد الهدف موجود
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    print(f"📂 Création du dossier cible : {target_dir}")

                # نقل الملفات من extracted_dir إلى target_dir
                for item in os.listdir(extracted_dir):
                    s = os.path.join(extracted_dir, item)
                    d = os.path.join(target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.move(s, d)
                    else:
                        shutil.move(s, d)

                print(f"✅ Extraction terminée dans : {target_dir}")

        except Exception as e:
            print("❌ Erreur dans _download_and_extract :", e)
            traceback.print_exc()
            raise e

    # ==========================================================
    # 🔥 LOGIQUE PRINCIPALE
    # ==========================================================
    @staticmethod
    def check_and_update() -> bool:
        """Vérifier et mettre à jour le programme et/ou extensions"""
        try:
            print("\n" + "=" * 80)
            print("🔍 DÉMARRAGE DU SYSTÈME DE MISE À JOUR")
            print("=" * 80)

            # -------------------------------
            # 🌐 APPEL SERVEUR pour récupérer versions
            # -------------------------------
            response = APIManager.make_request(
                "__CHECK_URL_PROGRAMM__", method="GET", timeout=10
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                print("❌ Réponse serveur invalide → Update forcé")
                return True

            data = response.get("data", {})
            server_program = data.get("version_Programme")
            server_ext = data.get("version_extension")

            print(f"🌐 Version programme serveur : {server_program}")
            print(f"🌐 Version extensions serveur : {server_ext}")

            # -------------------------------
            # 📁 VERSIONS LOCALES
            # -------------------------------
            local_program = UpdateManager._read_local_version(Settings.VERSION_LOCAL_PROGRAMM)
            local_ext = UpdateManager._read_local_version(Settings.VERSION_LOCAL_EXT)

            print(f"📄 Version programme locale : {local_program}")
            print(f"📄 Version extensions locale : {local_ext}")

            # ======================================================
            # 🟥 MISE À JOUR PROGRAMME
            # ======================================================
            if not local_program or local_program != server_program:
                print("\n🟥 MISE À JOUR PROGRAMME REQUISE")
                UpdateManager._download_and_extract(
                    "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip",
                    ROOT_DIR,
                    clean_target=False,
                    extract_subdir=None  # كل الملفات في الجذر
                )
                print("⛔ Arrêt après mise à jour programme")
                return True

            # ======================================================
            # 🟨 MISE À JOUR EXTENSIONS (TOOLS)
            # ======================================================
            if not local_ext or local_ext != server_ext:
                print("\n🟨 MISE À JOUR EXTENSIONS REQUISE")
                tools_dir = Settings.TOOLS_DIR
                if not os.path.exists(tools_dir):
                    print(f"⚠️ Dossier Tools introuvable, création automatique : {tools_dir}")
                    os.makedirs(tools_dir)

                UpdateManager._download_and_extract(
                    "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip",
                    tools_dir,
                    clean_target=True,
                    extract_subdir="tools"
                )
                print("▶️ Extensions mises à jour, poursuite normale")
                return True

            # ======================================================
            # 🟩 AUCUNE MISE À JOUR
            # ======================================================
            print("\n🟩 APPLICATION À JOUR – AUCUNE ACTION")
            return False

        except Exception as e:
            print("🔥 ERREUR CRITIQUE → UPDATE PAR SÉCURITÉ")
            traceback.print_exc()
            return True



class SecurityManager:
    """Gestionnaire de sécurité et chiffrement"""
    
    @staticmethod
    def generate_encrypted_key():
        """Génère une clé chiffrée pour l'authentification"""
        from cryptography.fernet import Fernet
        
        secret_key = Fernet.generate_key()
        fernet = Fernet(secret_key)
        encrypted_message = fernet.encrypt(b"authorized")
        
        return encrypted_message.decode(), secret_key.decode()





def initialize_dependencies():
    """Initialise toutes les dépendances nécessaires"""
    # Installation de pywin32 en premier
    DependencyManager.install_and_verify_pywin32()
    
    # Installation des autres dépendances
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
    selenium = DependencyManager.install_and_import("selenium", module_name="selenium", 
                                                   required_import="webdriver", version="4.27.1")
    jsonschema = DependencyManager.install_and_import("jsonschema")
    
    # Installation de python-dotenv
    try:
        import dotenv
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        import dotenv
    
    from dotenv import load_dotenv
    
    # Imports après installation
    from tqdm import tqdm
    from platformdirs import user_downloads_dir
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def main():
    """Fonction principale"""
    try:
   

         # 🪟 إخفاء نافذة الكونسول في الويندوز (اختياري)
        # if sys.platform == "win32":
        #     ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        # 🔍 البحث عن pythonw.exe لتشغيل البرنامج بدون نافذة كونسول
        # pythonw_path = None
        # for path in os.environ["PATH"].split(os.pathsep):
        #     pythonw_exe = os.path.join(path, "pythonw.exe")
        #     if ValidationUtils.path_exists(pythonw_exe):
        #         pythonw_path = pythonw_exe
        #         break

        # if not pythonw_path:
        #     pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        #     if ValidationUtils.path_exists(pythonw_exe):
        #         pythonw_path = pythonw_exe
        # Initialisation des dépendances
        initialize_dependencies()
        
        # Import de la configuration
        from config import settings
        
        # Vérification de pythonw.exe
        pythonw_path = settings.find_pythonw()
        if not pythonw_path:
            print("❌ pythonw.exe introuvable")
            sys.exit(1)


        # sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')
        # sys.stdin = open(os.devnull, 'r')
        
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE
        # Code en commentaire pour la mise à jour automatique
        # Vous pouvez le décommenter si nécessaire :
        print("\n" + "=" * 80)
        print("📌 DÉBUT DU SCRIPT")
        print("=" * 80)

        try:
            updated = UpdateManager.check_and_update()

            print("\n" + "=" * 80)
            print("📌 RÉSULTAT FINAL")
            print("=" * 80)

            if updated:
                print("🔄 UPDATE EFFECTUÉ")
            else:
                print("✅ APPLICATION À JOUR")

        except Exception as e:
            print("\n🔥 ERREUR CRITIQUE LORS DU CHECK/UPDATE")
            print(f"❌ Détails : {e}")
            import traceback
            traceback.print_exc()
            print("⚠️ L'application continue malgré l'erreur")
            

        # Génération des clés de sécurité
        encrypted_key, secret_key = SecurityManager.generate_encrypted_key()
        
        # Lancement de l'application principale
        script_path = SCRIPT_DIR / 'src' / 'AppV2.py'
        if script_path.is_file():
            subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])
        else:
            print(f"❌ Fichier introuvable : {script_path}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()