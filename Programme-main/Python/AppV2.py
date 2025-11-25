import os
import json
from base64 import b64encode, b64decode
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import *
from cryptography.fernet import Fernet
from PyQt6.QtGui import QIcon , QCursor 
from PyQt6.QtCore import Qt , QTimer , QThread, pyqtSignal , QSize
import winreg as reg
from PyQt6 import  uic ,  QtWidgets, QtGui, QtCore
import shutil
import signal
import time
import subprocess
import uuid
import random
import string                           
import re
import datetime
import requests
import sys
import zipfile
import traceback
import urllib3
import psutil
import PyQt6
from typing import Optional, Dict
import configparser
from platformdirs import user_downloads_dir
import win32gui       
import win32process
import win32con
from datetime import  timedelta
from PyQt6.QtGui import QColor, QPixmap
from PyQt6 import uic
from PyQt6.QtGui import QGuiApplication
import pytz
import copy
import warnings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile
import stat
import base64
from collections import defaultdict

warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()



SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# =========================================
# 📁 Constantes de chemins et fichiers
# =========================================
CONFIG_PROFILE              = r"C:\RepProxy\template Profile"
SECURE_PREFERENCES_TEMPLATE = r"C:\RepProxy\template Profile\default\Secure Preferences"
EXTENTION_EX3               = r"C:\RepProxy\Ext3"
MANIFEST_PATH_EX3           = os.path.join(EXTENTION_EX3, "manifest.json")
VERSION_LOCAL_EX3           = os.path.join(EXTENTION_EX3, "version.txt")




# Recherche clés spécifiques
RESULTATS=[]
CLES_RECHERCHE = ["cglaeklndjbecchejgkdpblljkmgkacg","dkbionknflglndapchlcfnelgchogjnl", "developer_mode"]
RESULTATS_EX = []
# CLES_RECHERCHE_EX2 = ["nephppeagmlfdjfpneeedifeflnijakl", "developer_mode"]

# CLES_RECHERCHE_EX2 = ["eoblcnapnenpmgdcmecapipdojplafpm", "nephppeagmlfdjfpneeedifeflnijakl" , "developer_mode"]


# =========================================
# 🔑 Paramètres cryptographie
# =========================================
PBKDF2_ITERATIONS = 100_000
SALT_LEN = 16
IV_LEN = 12
KEY_LEN = 32





# =========================================
# 
# =========================================


FIREFOX_LAUNCH = []
LOGS= []
PROCESS_PIDS = []
NOTIFICATION_BADGES = {}
EXTRACTION_THREAD = None 
CLOSE_BROWSER_THREAD = None 
NEW_VERSION = None
LOGS_RUNNING = True  
SELECTED_BROWSER_GLOBAL=None

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIRECTORY = os.path.join(SCRIPT_DIR, '..', 'tools', 'ExtensionEmail')
TEMPLATE_DIRECTORY_FIREFOX  = os.path.join(SCRIPT_DIR, '..', 'tools', 'ExtensionTemplateFirefox')
TEMPLATE_DIRECTORY_FAMILY_CHROME = os.path.join(SCRIPT_DIR, '..', 'tools', 'Extention_Family_Chrome')

# =========================================
# 
# =========================================
LOGS_DIRECTORY = os.path.join(SCRIPT_DIR, '..', 'Tools', 'logs')
RESULT_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "result.txt")


# =========================================
# icons
# =========================================
DEFAULT_ICON_PATH    = os.path.join(SCRIPT_DIR, '..', "Tools", "icons")
ICONS_DIR_INTERFACE  = os.path.join(SCRIPT_DIR, '..', "interface", "icons")
ARROW_DOWN_PATH      = os.path.join(ICONS_DIR_INTERFACE, "arrow_Down.png").replace("\\", "/")
ARROW_UP_PATH        = os.path.join(ICONS_DIR_INTERFACE, "arrow_up.png").replace("\\", "/")
ARROW_DOWN_W_PATH    = os.path.join(ICONS_DIR_INTERFACE, "arrow_Down_w.png")
ARROW_UP_W_PATH      = os.path.join(ICONS_DIR_INTERFACE, "arrow_up_w.png")

DOWN_EXISTS    = os.path.exists(ARROW_DOWN_PATH)
UP_EXISTS      = os.path.exists(ARROW_UP_PATH)
DOWN_EXISTS_W  = os.path.exists(ARROW_DOWN_W_PATH)
UP_EXISTS_W    = os.path.exists(ARROW_UP_W_PATH)




# =========================================
# 🌐 API
# =========================================
_APIACCESS_API              =  "https://reporting.nrb-apps.com/pub/chk_usr1.php?rv4=1"
_SAVE_EMAIL_API             =  "https://reporting.nrb-apps.com/pub/h_new.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1"
_SEND_STATUS_API            =  "http://reporting.nrb-apps.com:8585/rep/pub/email_status.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1"
_SAVE_PROCESS_API           =  "https://reporting.nrb-apps.com/pub/SaveProcess.php?k=mP5QXYrK9E67Y&rID=1&rv4=1"
_MAIN_API                   =  "https://apps1.nrb-apps.com/pub/chk_usr1.php"

# =========================================
# 🌐 URL UPDATE PROGRAMM
# =========================================
_DOWNLOAD_EXTRACTT_API      =  "https://github.com/Azedize/Programme/archive/refs/heads/main.zip"
_CHECK_VERSION_API          =  "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1"



# =========================================
# 🌐 API Local
# =========================================
_HANDLE_SAVE_API            =  "http://localhost/auth-api/add_scenario.php"
_LOAD_SCENARIOS_API         =  "http://localhost/auth-api/get_scenarios.php"
_ON_SCENARIO_CHANGED_API    =  "http://localhost/auth-api/get_scenario_by_name.php"


# =========================================
# GLOBAL
# =========================================
APPDATA       = os.getenv("APPDATA")
APP_NAME      = "SecureDesk"
APPDATA_DIR   = os.path.join(APPDATA, APP_NAME)

os.makedirs(APPDATA_DIR, exist_ok=True)

SESSION_PATH  = os.path.join(APPDATA_DIR, "session.txt")
FILE_ISP      = os.path.join(SCRIPT_DIR, "Isp.txt")




# =========================================
# HEADER
# =========================================
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:48.0) Gecko/20100101 Firefox/48.0'}

# les clés pour générer la clé finale
CLE1 = "pr"
CLE2 = "rep"
COMBINED_KEYS = f"&{CLE1}&{CLE2}"


# =========================================
# 📂 Déclaration des chemins UI globaux Interface
# =========================================

INTERFACE_UI      = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "interface", "interface.ui"))
AUTH_UI           = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "interface", "login_ui", "Auth.ui"))
FILE_ACTIONS_JSON = os.path.join(SCRIPT_DIR, '..', "Tools", "action.json")




STATUS_LIST = ["all", "bad_proxy", "completed", "account_closed", "password_changed", "code_de_validation",
                "recoverychanged", "Activite_suspecte", "validation_capcha", "restore_account", "others"]



def encrypt_message(plaintext: str, key_bytes: bytes):
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()

    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return b64encode(iv + ciphertext).decode()






# =========================================
# 🌐 URLs externes
# =========================================

KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
KEY     = bytes.fromhex(KEY_HEX)

DATA = {
    "login": "rep.test",
    "password": "zsGEnntKD5q2Brp68yxT"
}




encrypted = encrypt_message(json.dumps(DATA), KEY)



DROPBOX_URL    = "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=ormvslid&dl=1"
GITHUB_ZIP_URL = "https://github.com/Azedize/Extention-Repo/archive/refs/heads/main.zip"

CHECK_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted}"
SERVEUR_ZIP_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Ext3&k={encrypted}"







def decrypt_message(base64_data: str, key_bytes: bytes) -> str:
    raw = base64.b64decode(base64_data)

    iv = raw[:16]
    ciphertext = raw[16:]

    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext.decode("utf-8")







# 📦 Fonction pour s'assurer que Node.js est installé.
# Si ce n'est pas le cas, il tente de l'installer via Chocolatey (et installe aussi npm).
def ensure_node_installed():
    if shutil.which("node") is not None:
        print("✅ Node.js est déjà installé.")
        return True

    print("❌ Node.js n'est pas installé. Tentative d'installation via Chocolatey...")

    if shutil.which("choco") is None:
        print("🔍 Chocolatey non trouvé. Installation...")
        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                    "[System.Net.ServicePointManager]::SecurityProtocol = "
                    "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                    "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
                ],
                check=True
            )
            print("✅ Chocolatey installé.")
        except subprocess.CalledProcessError:
            print("❌ Échec de l'installation de Chocolatey.")
            return False

    try:
        subprocess.run(["choco", "install", "nodejs-lts", "-y"], check=True)
        print("✅ Node.js installé avec succès.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Échec de l'installation de Node.js.")
        return False






# Cette fonction retourne le chemin de l'exécutable web-ext s'il est trouvé
def get_web_ext_path():
    path = shutil.which("web-ext")
    if path:
        return path
    else:
        return None







# 🔍📦 Vérifie si 'web-ext' est installé, sinon l'installe globalement via npm
def ensure_web_ext_installed():
    if not ensure_node_installed():
        print("⚠️ Impossible de continuer sans Node.js.")
        return

    if shutil.which('npm') is None:
        print("❌ npm n'est pas installé. Vérifiez l'installation de Node.js.")
        return

    if shutil.which('web-ext') is not None:
        print("✅ 'web-ext' est déjà installé.")
        return

    print("🔍 'web-ext' n'est pas installé. Installation via npm...")
    try:
        subprocess.run('npm install --global web-ext', check=True, shell=True)
        print("✅ 'web-ext' a été installé avec succès.")
    except subprocess.CalledProcessError:
        print("❌ Échec de l'installation de 'web-ext' via npm.")






# 🔍  Analyse le fichier profiles.ini de Firefox et retourne un dictionnaire des profils existants avec leurs chemins complets
def parse_firefox_profiles_ini() -> Dict[str, str]:
    ini_path = os.path.join(APPDATA, 'Mozilla', 'Firefox', 'profiles.ini')
    config = configparser.ConfigParser()
    config.read(ini_path, encoding='utf-8')

    profiles = {}
    base_dir = os.path.dirname(ini_path)
    for section in config.sections():
        if section.startswith('Profile'):
            name = config.get(section, 'Name', fallback=None)
            path = config.get(section, 'Path', fallback=None)
            is_rel = config.getint(section, 'IsRelative', fallback=1)
            if name and path:
                full_path = os.path.join(base_dir, path) if is_rel else path
                profiles[name] = os.path.normpath(full_path)
    return profiles






# 🛠️ Crée un profil Firefox avec un nom donné s'il n'existe pas déjà, et affiche les profils avant/après la création
def create_firefox_profile(profile_name: str) -> Optional[str]:
    # Vérifier la présence de firefox.exe
    path_firefox = Get_Browser_Path("firefox.exe")
    if not path_firefox:
        print("❌ Firefox introuvable dans le registre.")
        return None
    print(f"🧭 Firefox détecté : {path_firefox}\n")

    # Afficher les profils existants avant la création
    print("=== Profils existants AVANT la création ===")
    existing_profiles = parse_firefox_profiles_ini()
    for name, path in existing_profiles.items():
        print(f" - {name}: {path}")
    print()

    # Définir le chemin de base pour les profils: SCRIPT_DIR/firefox
    path_profile = os.path.join(SCRIPT_DIR,'..','Tools', 'Profiles', 'firefox')
    print(f"📁 Répertoire de base des profils : {path_profile}")

    # Vérifier et créer le répertoire racine des profils si nécessaire
    if not os.path.exists(path_profile):
        print(f"🔧 Création du dossier racine des profils : {path_profile}")
        os.makedirs(path_profile, exist_ok=True)

    # Chemin complet du profil spécifique
    custom_dir = os.path.join(path_profile, profile_name)
    print("=== VÉRIFICATION DANS path_profile ===")
    if os.path.isdir(custom_dir):
        print(f"✅ Profil '{profile_name}' déjà existant : {custom_dir}")
        return custom_dir

    # Créer le profil via subprocess
    print(f"🔧 Création du profil '{profile_name}' dans {custom_dir}\n")
    cmd = f"{profile_name} {custom_dir}"
    result = subprocess.run(
        [path_firefox, '--CreateProfile', cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Afficher résultats
    print("🪵 stdout :", result.stdout.strip() or "<vide>")
    print("🪵 stderr :", result.stderr.strip() or "<vide>", "\n")

    if result.returncode != 0:
        print(f"❌ Échec de la création (code {result.returncode})")
        return None

    # Vérifier l'existence après création
    if os.path.isdir(custom_dir):
        print(f"✅ Profil créé avec succès : {custom_dir}")
    else:
        print("❌ Le dossier du profil n'a pas été trouvé après création.")
        return None

    # Afficher les profils existants après la création
    print("=== Profils existants APRÈS la création ===")
    updated_profiles = parse_firefox_profiles_ini()
    for name, path in updated_profiles.items():
        print(f" - {name}: {path}")
    print()

    return custom_dir






# ✅ Vérifie si une clé chiffrée est valide en la déchiffrant avec une clé secrète
def verify_key(encrypted_key: str, secret_key: str) -> bool:
    try:
        fernet = Fernet(secret_key.encode())
        decrypted = fernet.decrypt(encrypted_key.encode())
        if decrypted == b"authorized":
            return True
        else:
            return False
    except Exception as e:
        return False







# 🚀 Lance discrètement un nouveau script Python (checkV3.pyc) dans une nouvelle fenêtre sans console
def launch_new_window():
    target_dir = os.path.dirname(PARENT_DIR)
    script_path = os.path.join(target_dir, "checkV3.pyc")
    time.sleep(1)

    if not os.path.exists(script_path):
        return None  

    time.sleep(1)

    try:
        python_executable = sys.executable
        command = [python_executable, script_path]
        process = subprocess.Popen(
            command,
            creationflags=subprocess.CREATE_NO_WINDOW ,
            close_fds=True
        )
        stdout, stderr = process.communicate()  
        if process.returncode != 0:
            try:
                print(f"   📝 [ERROR] Standard Error: {stderr.decode(encoding='utf-8', errors='replace')}") 
            except Exception as decode_err:
                print(f"   ⚠️ [ERROR] Failed to decode stderr: {decode_err}")
                print(f"   📝 [ERROR] Raw stderr: {stderr}") 
            try:
                print(f"   📤 [INFO] Standard Output: {stdout.decode(encoding='utf-8', errors='replace')}") 
            except Exception as decode_err:
                print(f"   ⚠️ [ERROR] Failed to decode stdout: {decode_err}")
                print(f"   📤 [INFO] Raw stdout: {stdout}") 
            return None

        time.sleep(1)

    except Exception as e:
        print(f"💥 [CRITICAL ERROR] Failed to launch: {str(e)}")
        print("💡 [TIP] Check execution permissions or file integrity.")
        print(f"   📌 [ERROR] Details: {traceback.format_exc()}")  
        return None

    return target_dir





# 📝 Ajoute un message au journal global 'LOGS'
def log_message(text):
    global LOGS
    LOGS.append(text)








def Download_Extract(new_versions):
    """
    Download a single ZIP from GitHub, extract it safely,
    and replace the Tools/extensions folder if needed.
    Includes backup and detailed error handling.
    """
    try:
        if not isinstance(new_versions, dict):
            print("❌ [ERROR] Invalid new_versions (not a dict).")
            return -1

        if "version_extensions" not in new_versions:
            print("✅ [INFO] No extension updates required.")
            return 0

        with tempfile.TemporaryDirectory() as tmpdir:
            local_zip = os.path.join(tmpdir, "Programme-main.zip")

            # Download ZIP
            print("⬇️ Downloading update ZIP from GitHub...")
            resp = requests.get(_DOWNLOAD_EXTRACTT_API, stream=True, headers=HEADERS, verify=False, timeout=60)
            if resp.status_code != 200:
                print(f"❌ [ERROR] Failed to download ZIP: HTTP {resp.status_code}")
                return -1

            with open(local_zip, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"✅ Download completed: {local_zip}")

            # Extract safely
            print("📂 Extracting ZIP file...")
            with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                if not zip_ref.namelist():
                    print("❌ [ERROR] ZIP is empty.")
                    return -1
                topdir = zip_ref.namelist()[0].split('/')[0]
                extracted_dir = os.path.join(tmpdir, topdir)
                safe_extract(zip_ref, tmpdir)
            print(f"✅ Extraction completed: {extracted_dir}")

            # Tools update
            tools_target = os.path.join(PARENT_DIR, "tools")
            new_tools_root = os.path.join(extracted_dir, "tools")

            if not os.path.exists(new_tools_root):
                print("❌ [ERROR] 'tools' folder not found in archive.")
                return -1

            # Backup before replacing
            backup_dir = tools_target + "_backup"
            if os.path.exists(tools_target):
                print(f"📦 Creating backup of current tools: {backup_dir}")
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                shutil.move(tools_target, backup_dir)

            try:
                print(f"🚚 Moving new tools to {tools_target}")
                shutil.move(new_tools_root, tools_target)
                print("✅ Extensions updated successfully")

                # Cleanup backup after success
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)

            except Exception as move_err:
                print(f"❌ [ERROR] Failed to replace tools: {move_err}")
                if os.path.exists(backup_dir):
                    print("↩️ Restoring backup...")
                    shutil.move(backup_dir, tools_target)
                return -1

        print("🎉 [SUCCESS] Download and update process completed.")
        return 0

    except Exception as e:
        traceback.print_exc()
        print(f"❌ [EXCEPTION] Unexpected error in Download_Extract: {e}")
        return -1





def safe_extract(zip_ref, path):
    for member in zip_ref.namelist():
        member_path = os.path.abspath(os.path.join(path, member))
        if not member_path.startswith(os.path.abspath(path)):
            raise Exception("⚠️ [SECURITY] Unsafe path detected in ZIP archive.")
    zip_ref.extractall(path)




# 🔍 Vérifie les versions distantes et locales des composants, puis signale les mises à jour nécessaires
def Check_Version():
    """
    Check remote and local versions of Python, interface, and extensions.
    Returns a dict with updates if available, "_1" on error, or None if up to date.
    """
    try:
        print("🌐 Checking latest versions from server...")
        response = requests.get(_CHECK_VERSION_API, timeout=15)
        if response.status_code != 200:
            print(f"❌ [ERROR] Failed to fetch versions: HTTP {response.status_code}")
            return "_1"

        data = response.json()
        version_updates = {}

        # server versions
        server_version_python = data.get("version_python")
        server_version_interface = data.get("version_interface")
        server_version_extensions = data.get("version_extensions")

        if not all([server_version_python, server_version_interface, server_version_extensions]):
            print("❌ [ERROR] Missing version information on server.")
            return "_1"

        # local versions
        client_files = {
            "version_python": os.path.join(SCRIPT_DIR, "version.txt"),
            "version_interface": os.path.join(PARENT_DIR, "interface", "version.txt"),
            "version_extensions": os.path.join(PARENT_DIR, "tools", "version.txt")
        }

        client_versions = {}
        for key, path in client_files.items():
            if os.path.exists(path):
                with open(path, "r") as f:
                    client_versions[key] = f.read().strip()
                print(f"📄 {key}: Local = {client_versions[key]}")
            else:
                client_versions[key] = None
                print(f"⚠️ {key}: Local version file not found.")
                return "_1"

        # compare
        if server_version_python != client_versions["version_python"]:
            version_updates["version_python"] = server_version_python
            print(f"⬆️ Python update available: {server_version_python}")

        if server_version_interface != client_versions["version_interface"]:
            version_updates["version_interface"] = server_version_interface
            print(f"⬆️ Interface update available: {server_version_interface}")

        if server_version_extensions != client_versions["version_extensions"]:
            version_updates["version_extensions"] = server_version_extensions
            print(f"⬆️ Extensions update available: {server_version_extensions}")

        if version_updates:
            print(f"✅ Updates detected: {version_updates}")
            return version_updates
        else:
            print("✅ All software versions are up to date.")
            return None

    except Exception as e:
        traceback.print_exc()
        print(f"❌ [EXCEPTION] Error checking versions: {e}")
        return "_1"






# -----------------------------
# Personnalisation d'un onglet pour afficher le nombre d'emails complétés et non complétés
# -----------------------------
def Set_Custom_Colored_Tab(tab_widget, index, completed_count, not_completed_count):
    html_text = (
        f'<div style="text-align:center;margin:0;padding:0;">'
        f'<span style="font-family:\'Segoe UI\', sans-serif; font-size:14px;">Result ('
        f'<span style="color:#008000;">{completed_count} completed</span> / '
        f'<span style="color:#d90429;">{not_completed_count} not completed</span>)</span>'
        f'</div>'
    )

    # إزالة النص الافتراضي
    tab_widget.setTabText(index, "")

    # إنشاء QLabel
    label = QLabel()
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setText(html_text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # لف QLabel داخل QWidget لتوسيطه
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(label)

    # إزالة أي أزرار جانبية موجودة
    tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
    tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)

    # إضافة الـ wrapper كزر التبويب (محاذاة مركزية)
    tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, wrapper)









# -----------------------------
# Read email results and update the UI
# -----------------------------
def Read_Result_Update_List(window):
    # Vérifier si le fichier existe
    if not os.path.exists(RESULT_FILE_PATH):
        Show_Critical_Message(
            window,
            "Information",
            "No emails have been processed yet.\nPlease check the filters or new data.",
            message_type="info"
        )
        return

    errors_dict = defaultdict(list)
    all_emails = []

    try:
        # Lire toutes les lignes non vides
        with open(RESULT_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Vérification si le fichier est vide
        if not lines:
            Show_Critical_Message(window, "Warning", "No results available.", message_type="warning")
            return

        completed_count = 0
        no_completed_count = 0

        # Parcourir chaque ligne et classer les emails par statut
        for line in lines:
            parts = line.split(":")
            if len(parts) != 4:
                continue
            _, _, email, status = [p.strip() for p in parts]
            all_emails.append(email)
            errors_dict[status].append(email)
            if status == "completed":
                completed_count += 1
            else:
                no_completed_count += 1

        errors_dict["all"] = all_emails

        # Mise à jour du tab principal
        interface_tab_widget = window.findChild(QTabWidget, "interface_2")
        if interface_tab_widget:
            for i in range(interface_tab_widget.count()):
                if interface_tab_widget.tabText(i).startswith("Result"):
                    Set_Custom_Colored_Tab(interface_tab_widget, i, completed_count, no_completed_count)
                    break

        # Mise à jour des tabs secondaires
        result_tab_widget = window.findChild(QTabWidget, "tabWidgetResult")
        if not result_tab_widget:
            return

        for status in STATUS_LIST:
            tab_widget = result_tab_widget.findChild(QWidget, status)
            if not tab_widget:
                continue

            list_widgets = tab_widget.findChildren(QListWidget)
            if not list_widgets:
                continue

            list_widget = list_widgets[0]
            list_widget.clear()
            emails = errors_dict.get(status, [])
            if emails:
                list_widget.addItems(emails)
                list_widget.scrollToBottom()
                # Ajouter un badge de notification
                Add_Notification_Badge(result_tab_widget, result_tab_widget.indexOf(tab_widget), len(emails))
                # Supprimer le message "no data" si présent
                message_label = tab_widget.findChild(QLabel, "no_data_message")
                if message_label:
                    message_label.deleteLater()
            else:
                list_widget.addItem("⚠ No email data available for this category currently.")
                list_widget.show()

    except Exception as e:
        Show_Critical_Message(window, "Error", f"An error occurred while displaying results: {e}")







# -----------------------------
# Gestion des badges de notification sur les onglets
# -----------------------------
def Remove_Notification(index):
    badge = NOTIFICATION_BADGES.pop(index, None)
    if badge:
        badge.deleteLater()


def Add_Notification_Badge(tab_widget, tab_index, count):
    old_badge = NOTIFICATION_BADGES.get(tab_index)
    if old_badge:
        old_badge.deleteLater()

    tab_bar = tab_widget.tabBar()
    tab_rect = tab_bar.tabRect(tab_index)

    badge_x = tab_rect.right() - 14
    badge_y = tab_rect.top() + 2

    badge_label = QLabel(f"{count}", tab_widget)
    badge_label.setStyleSheet("""
        background-color: #d90429;
        color: white;
        font-size: 14px;
        padding: 3px;
        border-radius: 10px;
        min-width: 15px;
        text-align: center;
    """)
    badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    try:
        badge_label.setParent(tab_widget)
        badge_label.move(badge_x, badge_y)
        badge_label.show()
        NOTIFICATION_BADGES[tab_index] = badge_label
        tab_widget.update()
        tab_bar.update()
    except Exception as e:
        Show_Critical_Message(tab_widget, "Error", f"Error adding notification badge: {e}")






# 🆔 Génère un ID de session aléatoire basé sur UUID (tronqué à la longueur désirée)
def Generate_Session_Id(length=5):
    if length <= 0:
        raise ValueError("The length must be a positive integer.")
    return str(uuid.uuid4()).replace("-", "")[:length]






# 🧪 Exemple de génération d'un ID de session
SESSION_ID = Generate_Session_Id()









# -----------------------------
# Génération de messages critiques stylés avec PyQt6
# -----------------------------
def Show_Critical_Message(window, title, message, message_type="critical"):
    """Affiche un QMessageBox stylé selon le type (critical, warning, info, success)."""
    dialog = QMessageBox(window)

    # Définition des styles pour chaque type
    colors = {
        "critical": {"accent": "#d32f2f", "start": "#d32f2f", "end": "#b71c1c", "bg": "#ffebee", "icon": QMessageBox.Icon.Critical},
        "warning": {"accent": "#ed6c02", "start": "#ed6c02", "end": "#e65100", "bg": "#fff3e0", "icon": QMessageBox.Icon.Warning},
        "info": {"accent": "#0288d1", "start": "#0288d1", "end": "#01579b", "bg": "#e1f5fe", "icon": QMessageBox.Icon.Information},
        "success": {"accent": "#2e7d32", "start": "#2e7d32", "end": "#1b5e20", "bg": "#e8f5e9", "icon": QMessageBox.Icon.Information}
    }

    c = colors.get(message_type, colors["info"])
    dialog.setIcon(c["icon"])
    dialog.setWindowTitle(title)
    dialog.setText(f"<h2 style='margin:0; font-weight:700; color:{c['accent']};'>{title}</h2>"
                   f"<p style='margin:0px; color:#37474f; line-height:1.5;'>{message}</p>")

    # Ombre
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(50)
    shadow.setColor(QColor(0, 0, 0, 160))
    shadow.setOffset(0, 12)
    dialog.setGraphicsEffect(shadow)

    # Style global (fusionné et optimisé)
    dialog.setStyleSheet(f"""
        QMessageBox {{
            background-color: {c['bg']};
            color: #263238;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-size: 14px;
            padding: 20px;
            min-width: 480px;
            border-radius: 12px;
        }}
        QMessageBox QLabel#qt_msgbox_label {{
            padding: 15px;
            border-radius: 10px;
            background: {c['bg']};
        }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['start']}, stop:1 {c['end']});
            color: #fff;
            font-weight: 600;
            border-radius: 8px;
            padding: 10px 25px;
            min-width: 100px;
        }}
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Lighten_Color(c['start'], 12)}, stop:1 {Lighten_Color(c['end'], 12)});
        }}
        QMessageBox QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {Darken_Color(c['start'], 12)}, stop:1 {Darken_Color(c['end'], 12)});
            padding: 11px 26px 9px 26px;
        }}
    """)

    if window:
        dialog.move(window.frameGeometry().center() - dialog.rect().center())

    return dialog.exec()


# -----------------------------
# Ajustement de la couleur HEX (assombrir / éclaircir)
# -----------------------------
def Darken_Color(hex_color, percent):
    r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    factor = 1 - percent / 100
    r, g, b = [max(0, min(255, int(c * factor))) for c in (r, g, b)]
    return f"#{r:02x}{g:02x}{b:02x}"


def Lighten_Color(hex_color, percent):
    r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    r = min(255, int(r + (255 - r) * percent / 100))
    g = min(255, int(g + (255 - g) * percent / 100))
    b = min(255, int(b + (255 - b) * percent / 100))
    return f"#{r:02x}{g:02x}{b:02x}"








# 🔐 Génère un mot de passe sécurisé aléatoire pour Gmail avec au moins 12 caractères
def Generate_Gmail_Password(length=12):
    if length < 12:
        raise ValueError("The recommended minimum length for a secure password is 12 characters.")
    
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()-_+=<>?/|"

    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars),
    ]
    remaining_length = length - len(password)
    all_chars = lowercase + uppercase + digits + special_chars
    password += random.choices(all_chars, k=remaining_length)
    random.shuffle(password)
    return ''.join(password)





# 🔍 Récupère le chemin absolu d'un exécutable de navigateur en consultant le registre Windows.

def Get_Browser_Path(exe_name: str) -> Optional[str]:
    key_app_paths = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
    hives = [
        (reg.HKEY_LOCAL_MACHINE, reg.KEY_READ | reg.KEY_WOW64_32KEY),
        (reg.HKEY_LOCAL_MACHINE, reg.KEY_READ | reg.KEY_WOW64_64KEY),
        (reg.HKEY_CURRENT_USER,  reg.KEY_READ)
    ]
    for hive, access in hives:
        try:
            with reg.OpenKey(hive, key_app_paths, 0, access) as key_obj:
                path, _ = reg.QueryValueEx(key_obj, None)
                return path
        except FileNotFoundError:
            continue
    return None








# -----------------------------
# Fonction pour extraire un bloc complet d'un JS selon le process
# -----------------------------
def Extraire_Bloc_Complet(contenu, process_key):
    start = contenu.find(f'"{process_key}": [')
    if start == -1:
        return None

    pos = start + len(f'"{process_key}": [')
    depth = 1
    while pos < len(contenu):
        char = contenu[pos]
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                return contenu[start:pos+1]
        pos += 1
    return None




# -----------------------------
# Fonction pour remplacer __reply_message__ dans ispProcess
# -----------------------------
def Remplacer_ReplyMessage_Value(contenu_json, ispProcess):
    def parcourir_blocs(blocs):
        valeurs = []
        for bloc in blocs:
            if "sub_process" in bloc:
                valeurs.extend(parcourir_blocs(bloc["sub_process"]))
            elif bloc.get("process") == "reply_message":
                valeurs.append(bloc.get("value", ""))
        return valeurs

    try:
        data = json.loads(contenu_json) if isinstance(contenu_json, str) else contenu_json
        valeurs_reply = parcourir_blocs(data)
        for valeur in valeurs_reply:
            ispProcess = ispProcess.replace("__reply_message__", valeur, 1)
        return ispProcess
    except Exception as e:
        print(f"[ERREUR] Remplacer_ReplyMessage_Value : {e}")
        return ispProcess




# -----------------------------
# Modifier gmail_process.js selon traitement.json
# -----------------------------
def Modifier_Extension_Par_Traitement(email_folder):
    traitement_path = os.path.join(email_folder, 'traitement.json')
    gmail_process_path = os.path.join(email_folder, 'gmail_process.js')

    if not os.path.exists(traitement_path) or not os.path.exists(gmail_process_path):
        print("❌ Fichier traitement.json ou gmail_process.js introuvable.")
        return

    with open(traitement_path, 'r', encoding='utf-8') as f:
        traitement_data = json.load(f)

    remplacement_dict = {}
    for obj in traitement_data:
        process_name = obj.get("process", "")
        if process_name.startswith("google") and "search" in obj:
            remplacement_dict[process_name] = obj["search"]

    if not remplacement_dict:
        return

    with open(gmail_process_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    for process_key, search_value in remplacement_dict.items():
        bloc_complet = Extraire_Bloc_Complet(content, process_key)
        if bloc_complet is None or '__search_value__' not in bloc_complet:
            continue
        bloc_modifie = bloc_complet.replace('"__search_value__"', f'"{search_value}"')
        content = content.replace(bloc_complet, bloc_modifie)

    # Remplacer également __reply_message__ si présent dans gmail_process.js
    content = Remplacer_ReplyMessage_Value(traitement_data, content)

    with open(gmail_process_path, 'w', encoding='utf-8') as f:
        f.write(content)




# -----------------------------
# Génération complète de l'extension Chrome/Firefox
# -----------------------------
# Crée une extension personnalisée pour l'utilisateur
# Copie template, remplace placeholders JS et applique JSON modifié
def Create_Extension_For_Email(email, password, host, port, user, passwordP, recovry, new_password, new_recovry, IDL, selected_Browser):
    template_directory = TEMPLATE_DIRECTORY_FIREFOX if selected_Browser.lower() == "firefox" else TEMPLATE_DIRECTORY_FAMILY_CHROME

    if not os.path.exists(BASE_DIRECTORY):
        os.makedirs(BASE_DIRECTORY)
        
    email_folder = os.path.join(BASE_DIRECTORY, email)
    if os.path.exists(email_folder):
        shutil.rmtree(email_folder)
    os.makedirs(email_folder)

    # Lecture session si existante
    session = ""
    if os.path.exists(SESSION_PATH):
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            session = f.read().strip()

    # Copier les fichiers du template
    for item in os.listdir(template_directory):
        src = os.path.join(template_directory, item)
        dst = os.path.join(email_folder, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # Modification des fichiers JS principaux
    js_files = {
        "actions.js": {
            "__IDL__": IDL, "__email__": email, "___session_user__": session
        },
        "background.js": {
            "__host__": host, "__port__": port, "__user__": user,
            "__pass__": passwordP, "__IDL__": IDL, "__email__": email
        },
        "gmail_process.js": {
            "__email__": email, "__password__": password,
            "__recovry__": recovry, "__newPassword__": new_password,
            "__newRecovry__": new_recovry
        },
        "ReportingActions.js": {
            "__IDL__": IDL, "__email__": email
        }
    }

    for js_file, replacements in js_files.items():
        path = os.path.join(email_folder, js_file)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, str(value))
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    # Appliquer le traitement avancé sur gmail_process.js
    Modifier_Extension_Par_Traitement(email_folder)








# 📝 Enregistre de façon unique le PID, l'email et l'ID de session dans un fichier texte lié à l'email.
def Add_Pid_To_Text_File(pid, email , inserted_id):
    print(f"🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴 Function add_pid_to_text_file called with PID: {pid}, Email: {email}")
    text_file_path = os.path.join(BASE_DIRECTORY, email , "data.txt")

    os.makedirs(os.path.dirname(text_file_path), exist_ok=True)

    if os.path.exists(text_file_path):
        with open(text_file_path, 'r', encoding='utf-8') as file:
            existing_entries = set(file.read().splitlines())
    else:
        existing_entries = set()

    print(f"PID: {pid}, Email: {email}")
    entry = f"{pid}:{email}:{SESSION_ID}:{inserted_id}" 

    if entry not in existing_entries:
        with open(text_file_path, 'w', encoding='utf-8') as file:
            file.write(f"{entry}\n")








def Get_Firefox_Profiles_In_Use():
    """Retourne les profils Firefox actuellement utilisés (lockés)"""
    base_path = os.path.join(SCRIPT_DIR, ".." ,"tools", "Profiles", "firefox")

    profiles = []
    if not os.path.exists(base_path):
        return profiles

    for folder in os.listdir(base_path):
        profile_path = os.path.join(base_path, folder)
        lock_file = os.path.join(profile_path, 'parent.lock')
        if os.path.isdir(profile_path) and os.path.exists(lock_file):
            profiles.append({'name': folder, 'path': profile_path})
    return profiles








def Get_Profile_By_Pid(pid, active_profiles):
    """Associe un PID Firefox à un profil actif"""
    try:
        proc = psutil.Process(pid)
        for f in proc.open_files():
            for profile in active_profiles:
                if os.path.commonpath([f.path, profile['path']]) == profile['path']:
                    return profile
                if profile['name'] in f.path:
                    return profile
    except Exception:
        pass
    return None








def Get_Firefox_Windows():
    active_profiles = Get_Firefox_Profiles_In_Use()
    windows = []

    def window_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetClassName(hwnd) == 'MozillaWindowClass':
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                profile = Get_Profile_By_Pid(pid, active_profiles)
                if profile:
                    windows.append({
                        'hwnd': hwnd,
                        'title': win32gui.GetWindowText(hwnd),
                        'pid': pid,
                        'profile': profile['name']
                    })
            except Exception:
                pass
        return True

    win32gui.EnumWindows(window_callback, None)
    return windows








def Close_Windows_By_Profiles(profiles_list):
    noms_profils = [p["profile"] for p in profiles_list]  
    
    print(f"\n🔎 Recherche des fenêtres pour les profils : {', '.join(noms_profils)}")
    all_windows = Get_Firefox_Windows()
    

    target_windows = [w for w in all_windows if w["profile"] in noms_profils]

    if not target_windows:
        print("❌ Aucune fenêtre trouvée pour ces profils")
        return


    for window in target_windows:
        try:
            win32gui.PostMessage(window["hwnd"], win32con.WM_CLOSE, 0, 0)
            print(f"✅ Fermeture : {window['profile']} - {window['title']}")
        except Exception as e:
            print(f"❌ Erreur avec {window['profile']} : {str(e)}")








def Stop_All_Processes(window):
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD, PROCESS_PIDS, LOGS_RUNNING, SELECTED_BROWSER_GLOBAL

    print("Stopping all processes...")
    LOGS_RUNNING = False

    if EXTRACTION_THREAD:
        print("Stopping extraction thread...")
        EXTRACTION_THREAD.stop_flag = True
        EXTRACTION_THREAD.wait()
        EXTRACTION_THREAD = None
        print("Extraction thread stopped.")


    if CLOSE_BROWSER_THREAD:
        print("Stopping close Chrome thread...")
        CLOSE_BROWSER_THREAD.stop_flag = True
        CLOSE_BROWSER_THREAD.wait()
        CLOSE_BROWSER_THREAD = None
        print("Close Chrome thread stopped.")

    if EXTRACTION_THREAD and EXTRACTION_THREAD.isRunning():
        print("Waiting for extraction thread to finish before updating UI...")
        EXTRACTION_THREAD.finished.connect(
            lambda: QTimer.singleShot(100, 
            lambda: Read_Result_Update_List(window))
        )

    if SELECTED_BROWSER_GLOBAL != "firefox":
        for pid in PROCESS_PIDS[:]:
            try:
                print(f"Attempting to terminate process with PID {pid}...")
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                print(f"Process {pid} terminated successfully.")
            except psutil.NoSuchProcess:
                print(f"The process with PID {pid} no longer exists.")
            except psutil.AccessDenied:
                print(f"Permission denied to terminate the process with PID {pid}.")
            except Exception as e:
                print(f"An error occurred while terminating PID {pid}: {e}")
            finally:
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")
    else:
            try:
                Close_Windows_By_Profiles(FIREFOX_LAUNCH)
            except Exception as e:
                print(f"⚠️ Erreur lors de la fermeture des profils Firefox: {e}")
 
            finally:
                for pid in PROCESS_PIDS[:]:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")








# 🚀 Lance un thread pour fermer automatiquement les processus Chrome actifs.
def Launch_Close_Chrome(selected_Browser , username):
    global CLOSE_BROWSER_THREAD
    CLOSE_BROWSER_THREAD = CloseBrowserThread( selected_Browser ,username)
    CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
    CLOSE_BROWSER_THREAD.start()







# -----------------------------
# Génération complète de l'extension Chrome/Firefox
# -----------------------------

def Generate_User_Input_Data(window):
    # Récupération du texte des QTextEdit
    input_data = window.textEdit_3.toPlainText().strip()
    entered_number = window.textEdit_4.toPlainText().strip()

    # Vérification que l'entrée n'est pas vide
    if not input_data:
        Show_Critical_Message(
            window,
            "Error - Missing Data",
            "Please enter the required information before proceeding.",
            message_type="critical"
        )
        return

    # Vérification que le nombre saisi est bien un entier
    if not entered_number.isdigit():
        Show_Critical_Message(
            window,
            "Error - Invalid Input",
            "Please enter a valid numerical value in the number field.",
            message_type="critical"
        )
        return

    entered_number = int(entered_number)

    try:
        # Séparer le texte en lignes et supprimer les espaces superflus
        lines = [line.strip() for line in input_data.split("\n") if line.strip()]
        if not lines:
            Show_Critical_Message(window, "Error", "Input is empty after stripping spaces.", message_type="critical")
            return

        # Extraire les clés depuis la première ligne
        keys = [key.strip() for key in lines[0].split(";")]

        # Définir les clés obligatoires et optionnelles
        mandatory_patterns = [
            ["email", "passwordEmail", "ipAddress", "port"],
            ["Email", "password_email", "ip_address", "port"]
        ]
        optional_patterns = [
            ["login", "password", "recoveryEmail", "newrecoveryEmail"],
            ["login", "password", "recovery_email", "New_recovery_email"]
        ]

        # Créer un set de toutes les clés valides
        all_valid_keys = set()
        for pat in mandatory_patterns + optional_patterns:
            all_valid_keys.update(pat)

        # Vérifier que toutes les clés obligatoires sont présentes
        if not any(set(pat).issubset(keys) for pat in mandatory_patterns):
            missing_keys = [k for pat in mandatory_patterns for k in pat if k not in keys]
            pattern_message = (
                "<b>The required keys are missing in your input.</b><br><br>"
                "Please include the required keys in one of the following formats:<br>"
                "1. <i>email; passwordEmail; ipAddress; port</i><br>"
                "2. <i>Email; password_email; ip_address; port</i><br><br>"
                f"<b>Missing keys detected:</b> {', '.join(missing_keys)}"
            )
            Show_Critical_Message(window, "Error - Required Keys Missing", pattern_message, message_type="critical")
            return

        # Vérifier qu'il n'y a pas de clés invalides
        invalid_keys = [k for k in keys if k not in all_valid_keys]
        if invalid_keys:
            pattern_message = f"<b>Invalid keys detected:</b> {', '.join(invalid_keys)}"
            Show_Critical_Message(window, "Error - Invalid Keys", pattern_message, message_type="critical")
            return

        # Transformer les lignes suivantes en liste de dictionnaires
        data_list = []
        for line in lines[1:]:
            values = [v.strip() for v in line.split(";")]
            if len(values) != len(keys):
                Show_Critical_Message(window, "Error - Key/Value Mismatch", 
                                      "The number of keys and values does not match for a line.", 
                                      message_type="critical")
                return
            data_list.append(dict(zip(keys, values)))

        # Vérifier que le nombre saisi ne dépasse pas le nombre d'entrées disponibles
        if entered_number > len(data_list):
            Show_Critical_Message(
                window,
                "Error - Invalid Range",
                f"Please enter a value between 1 and {len(data_list)}.<br>"
                f"Selected entries cannot exceed available items.",
                message_type="critical"
            )
            return

        return data_list, entered_number

    except Exception as e:
        Show_Critical_Message(
            window,
            "Operation Failed - System Error",
            f"Critical failure during data processing:<br>"
            f"(Technical details: {str(e).capitalize()})",
            message_type="critical"
        )
        return




print("📤 Envoi du statut de l'email à l'API...")





# 🔍 Recherche la première clé disponible dans email_data parmi une liste de clés possibles et_
def Get_Key_Value( email_data, possible_keys):
    for key in possible_keys:
        if key in email_data:
            if not email_data[key]:  
                return key
            return email_data[key]
    return possible_keys[0]















# 🛠️ Démarre le processus d'extraction en lançant le thread principal avec les paramètres utilisateur, après validation des entrées et préparation de l'environnement.
def Start_Extraction(window, data_list, entered_number , selected_Browser , Isp , unique_id , output_json_final , username):
    global EXTRACTION_THREAD 

    
    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)
    
    try:
        entered_number = int(entered_number)
    except ValueError:
        Show_Critical_Message(
            window,
            "Input Error - Invalid Format",
            "Numeric value required. Please check your input and try again.",
            message_type="critical"
        )

        return

    email_count = len(data_list)
    if entered_number > email_count:
        Show_Critical_Message(
            window,
            "Range Error - Exceeded Limit",
            f"Maximum allowed entries: {email_count}\n"
            f"Please enter a value between 1 and {email_count}.",
            message_type="critical"
        )
        return
    
    # submit_button = window.findChild(QPushButton, "submitButton")  
    # if submit_button:
    #     submit_button.setEnabled(False)
    #     submit_button.setStyleSheet("""
    #         QPushButton {
    #             background-color: #a0a0a0; /* Greyed-out background */
    #             color: #c0c0c0;          /* Greyed-out text */
    #             border: 1px solid #808080; /* Grey border */
    #             border-radius: 5px;
    #         }
    #     """)


    Launch_Close_Chrome(selected_Browser , username)
    # find_chrome_for_testing() 
    browser_path = (
        Get_Browser_Path("chrome.exe") if selected_Browser == "chrome"
        else Get_Browser_Path("firefox.exe") if selected_Browser == "firefox"
        else Get_Browser_Path("msedge.exe") if selected_Browser == "edge"
        else Get_Browser_Path("dragon.exe")  
    )

    if selected_Browser == "firefox":
        ensure_web_ext_installed()

    print("browser path   :",   browser_path    or "Non trouvé")

    # return browser_path;
    EXTRACTION_THREAD = ExtractionThread(
        data_list, SESSION_ID, entered_number, browser_path, BASE_DIRECTORY, window ,selected_Browser , Isp , unique_id , output_json_final
    )
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.finished.connect(lambda: QMessageBox.information(window, "Terminé", "L'extraction est terminée."))
    EXTRACTION_THREAD.stopped.connect(lambda msg: QMessageBox.warning(window, "Arrêté", msg))
    EXTRACTION_THREAD.start()









# 🔍 Trouve la fenêtre principale d'un processus donné en utilisant son PID.
def Find_Main_Window_Handle( target_pid):
    """Trouve le handle de la fenêtre principale de Firefox et affiche ses informations détaillées."""
    def enum_windows_callback(hwnd, hwnds):
        # Vérifier si la fenêtre est visible et a un titre
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != '':
            # Obtenir IDs de thread et de processus
            thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == target_pid:
                # Récupérer les informations de la fenêtre
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

                # Afficher toutes les informations collectées
                # print(f"[INFO] HWND           : {hwnd}")
                # print(f"       Titre          : {title}")
                # print(f"       Classe         : {class_name}")
                # print(f"       PID            : {pid}")
                # print(f"       Thread ID      : {thread_id}")
                # print(f"       Position/Size  : (left={rect[0]}, top={rect[1]}, right={rect[2]}, bottom={rect[3]})")
                # print(f"       Style          : 0x{style:08X}")
                # print(f"       Ex-Style       : 0x{ex_style:08X}")

                hwnds.append(hwnd)
        return True

    hwnds = []
    # Enumérer les fenêtres pour trouver la fenêtre principale
    win32gui.EnumWindows(enum_windows_callback, hwnds)
    return hwnds[0] if hwnds else None








def Parse_Random_Range(text):
    try:
        if ',' in text:
            min_val, max_val = map(int, text.split(','))
            return random.randint(min_val, max_val)
        return int(text)
    except:
        return 0








def Save_Email(params):
    
    response_text = ''
    
    while response_text == '':
        try:
            print(f"🌐 [API] Envoi de la requête ➜ {_SAVE_EMAIL_API}")
            print(f"📤 [DATA] Paramètres envoyés: {params}")

            response = requests.post(_SAVE_EMAIL_API, headers=HEADERS, verify=False, data=params)
            
            print(f"📥 [HTTP] Code de réponse: {response.status_code}")
            print(f"📄 [HTTP] Réponse brute:\n{response.text}")

            # Vérification d'erreur HTTP
            response.raise_for_status()

            response_text = response.text
            break

        except requests.exceptions.RequestException as req_err:
            print(f"💥 [ERREUR DE REQUÊTE] : {req_err}")
            print("⏳ Nouvelle tentative dans 5 secondes...")
            time.sleep(5)
        except Exception as e:
            print(f"💥 [EXCEPTION] Erreur inconnue : {e}")
            print("⏳ Nouvelle tentative dans 5 secondes...")
            time.sleep(5)

    return response_text









def Send_Status(params):
    print( "\n📤 Préparation de l'envoi du statut à l'API...")
    print("🧾 Paramètres envoyés :")

    response = ''
    cpt = 0

    print("\n📤 Envoi du statut de l'email à l'API...")

    while response == '':
        try:
            res = requests.post(_SEND_STATUS_API, headers=HEADERS, verify=False, data=params)
            response = res.text

            print("✅ Statut envoyé avec succès !")
            print("🔽 Détails de la réponse de l'API :")
            print(response)

            break
        except Exception as e:
            print(f"\n❌ Erreur [API:h CG] : Connexion refusée par le serveur... ({e})")
            print("🕒 Nouvelle tentative dans 5 secondes...")

            cpt += 1
            if cpt == 5:
                print("❌ Échec après 5 tentatives.")
                break
            time.sleep(5)
            continue

    return response








# Thread pour afficher les LOGS en temps réel depuis une liste partagée.
# Émet un signal log_signal à chaque nouvelle entrée de log.
class LogsDisplayThread(QThread):
    log_signal = pyqtSignal(str)
    def __init__(self, LOGS, parent=None):
        super().__init__(parent)
        self.LOGS = LOGS
        self.stop_flag = False


    def run(self):
        global LOGS_RUNNING 
        while LOGS_RUNNING: 
            if self.LOGS:
                log_entry = self.LOGS.pop(0)
                self.log_signal.emit(log_entry)
            else:
                time.sleep(1)  


    def stop(self):
        self.stop_flag = True
        self.wait()










def Derive_Key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))








def Encrypt_Aes_Gcm(password: str, plaintext: str) -> str:
    salt = os.urandom(SALT_LEN)
    key = Derive_Key(password, salt)
    iv = os.urandom(IV_LEN)

    aesgcm = AESGCM(key)
    ct_and_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

    payload = salt + iv + ct_and_tag
    return payload.hex()







def Updated_Secure_Preferences(profile_name, RESULTATS_EX):
    try:
        secure_preferences_path = os.path.abspath(os.path.join(
            SCRIPT_DIR, "..", "tools", "Profiles", "chrome", profile_name, profile_name, "Secure Preferences"
        ))

        # 🖨️ Affichage du chemin complet
        print("🔍 Étape 1 : Vérification du chemin du fichier Secure Preferences...")
        print(f"📂 Chemin complet du fichier 'Secure Preferences' : {secure_preferences_path}")

        # Vérification existence fichier
        if not os.path.exists(secure_preferences_path):
            print(f"❌ Le fichier 'Secure Preferences' est introuvable pour le profil '{profile_name}'.")
            print("👉 Veuillez contacter le support technique pour assistance.")
            return None

        print("✅ Étape 2 : Fichier trouvé. Lecture du contenu JSON...")
        with open(secure_preferences_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérification structure
        if "extensions" not in data:
            print("⚠️ Aucune clé 'extensions' trouvée. Initialisation forcée...")
            data["extensions"] = {}

        data["extensions"].setdefault("ui", {})
        # data["extensions"].setdefault("settings", {})
        # data.setdefault("protection", {}).setdefault("macs", {}).setdefault("extensions", {}).setdefault("settings", {})
        # data["protection"]["macs"]["extensions"].setdefault("ui", {})

        print("✅ Étape 3 : Structure JSON vérifiée et préparée.")

        # 🔄 Ajouter les résultats sans supprimer les anciennes valeurs
        print("🔄 Étape 4 : Mise à jour des paramètres avec RESULTATS_EX...")
        for idx, item in enumerate(RESULTATS_EX, start=1):
            print(f"➡️ Traitement de l'élément {idx} : {item}")

            if not isinstance(item, dict):
                print("⚠️ Ignoré (élément non dict).")
                continue

            for k, v in item.items():
                if isinstance(v, dict) and "account_extension_type" in v:
                    data["extensions"]["settings"][k] = v
                    print(f"   📝 Ajout/maj dans extensions.settings[{k}] = {v}")

                elif isinstance(v, str) and len(v) > 30 and k != "developer_mode":
                    data["protection"]["macs"]["extensions"]["settings"][k] = v
                    print(f"   🔐 Ajout/maj MAC dans protection.macs.extensions.settings[{k}]")

                elif isinstance(v, bool) and k == "developer_mode":
                    data["extensions"]["ui"]["developer_mode"] = v
                    print(f"   ⚙️ developer_mode activé/désactivé (extensions.ui) : {v}")

                elif isinstance(v, str) and k == "developer_mode":
                    data["protection"]["macs"]["extensions"]["ui"]["developer_mode"] = v
                    print(f"   🔐 MAC pour developer_mode ajouté dans protection.macs.extensions.ui")

        # Sauvegarde
        print("💾 Étape 5 : Écriture du fichier JSON mis à jour...")
        with open(secure_preferences_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

        print("✅ Étape 6 : Mise à jour terminée avec succès !")
        return data

    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du fichier Secure Preferences : {e}")
        return None







def Search_Keys(data, CLES_RECHERCHE, RESULTATS):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in CLES_RECHERCHE:
                print(f"🔑 Clé trouvée : {key} ➜ Valeur : {value}") 
                RESULTATS.append({key: value})
            Search_Keys(value, CLES_RECHERCHE, RESULTATS)
    elif isinstance(data, list):
        for item in data:
            Search_Keys(item, CLES_RECHERCHE, RESULTATS)









def Upload_EXTENTION_PROXY(profile_name, CLES_RECHERCHE, RESULTATS):
    print("====================================================")
    print(f"📂 Début du traitement pour le profil : {profile_name}")
    print("====================================================")

    # Construction du chemin complet du fichier "Secure Preferences"
    profile_path_file_secure_preferences = os.path.join(
        CONFIG_PROFILE, profile_name, "Secure Preferences"
    )
    print(f"🔍 Chemin du fichier Secure Preferences : {profile_path_file_secure_preferences}")

    # Vérification si le fichier existe
    if not os.path.exists(profile_path_file_secure_preferences):
        print("❌ Erreur : le fichier 'Secure Preferences' est introuvable !")
        print("👉 Vérifiez que le profil Chrome existe correctement ou contactez le support.")
        return None

    try:
        # Lecture du fichier JSON
        print("📖 Lecture du fichier JSON en cours ...")
        with open(profile_path_file_secure_preferences, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Lecture réussie du fichier Secure Preferences.")

        # Nettoyage de la liste des résultats
        RESULTATS.clear()
        print("🧹 Initialisation de la liste des résultats (RESULTATS) ...")

        # Recherche des clés
        print(f"🔎 Début de la recherche des clés : {CLES_RECHERCHE}")
        Search_Keys(data, CLES_RECHERCHE, RESULTATS)

        # Affichage des résultats trouvés
        print("📌 Résultats trouvés :")
        if RESULTATS:
            for idx, item in enumerate(RESULTATS, start=1):
                print(f"   {idx}. {item}")
        else:
            print("⚠️ Aucun résultat trouvé pour les clés spécifiées.")

        print("====================================================")
        print(f"✅ Fin du traitement pour le profil : {profile_name}")
        print("====================================================")

        return RESULTATS

    except Exception as e:
        print("❌ Une erreur inattendue est survenue lors du traitement du fichier Secure Preferences.")
        print(f"➡️ Détail de l'erreur : {e}")
        return None







def Run_Browser_Create_Profile(profile_name):
    print("=============================================")
    print("🔧 Initialisation de la création du profil...")
    print("=============================================")

    # 📂 Définir le chemin du profil (remontée de 2 niveaux pour Desktop\Tools)
    profile_path = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'chrome', profile_name))
    print(f"📂 Chemin complet du profil : {profile_path}")

    # Créer le dossier si non existant
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        print(f"✅ Dossier de profil créé : {profile_path}")
    else:
        print(f"✅ Profil déjà existant : {profile_path}")

    # ⚙️ Configuration des options Chrome
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument(f"--profile-directory={profile_name}")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-sync")

    print("⚙️ Options appliquées à Chrome :")
    for arg in chrome_options.arguments:
        print(f"   ➜ {arg}")

    # 🚀 Lancement du navigateur
    print("🌐 Lancement de Chrome avec ce profil...")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Navigateur lancé avec succès !")
        print("⏳ Attente de 2 secondes pour stabilisation...")
        time.sleep(2)

    except Exception as e:
        print(f"❌ Erreur lors du lancement du navigateur : {e}")

    finally:
        if driver:
            print("🛑 Fermeture du navigateur...")
            driver.quit()
            print("✅ Navigateur fermé proprement.")

        print("=============================================")
        print("🎉 Profil créé et testé avec succès.")
        print("=============================================")






# Thread responsable du traitement de l'extraction des emails.
# Gère l'exécution des navigateurs avec les extensions, l'enregistrement des LOGS,
# et la gestion des processus.
class ExtractionThread(QThread):

    progress = pyqtSignal(str)  
    finished = pyqtSignal()  
    stopped = pyqtSignal(str)

    def __init__(self, data_list, SESSION_ID, entered_number, Browser_path, BASE_DIRECTORY, main_window ,selected_Browser,Isp , unique_id , output_json_final):  
        super().__init__()
        self.data_list = data_list  
        self.session_id = SESSION_ID  
        self.entered_number = entered_number  
        self.Browser_path = Browser_path 
        self.BASE_DIRECTORY = BASE_DIRECTORY  
        self.stop_flag = False
        self.emails_processed = 0 
        self.selected_Browser = selected_Browser
        self.main_window = main_window 
        self.Isp=Isp
        self.unique_id=unique_id
        self.output_json_final = output_json_final

    def run(self):
        # Exécute la boucle principale de traitement des emails :
        # - Création des profils/extensions
        # - Lancement des navigateurs
        # - Gestion des processus

        global PROCESS_PIDS, LOGS_RUNNING  ,SELECTED_BROWSER_GLOBAL  ,RESULTATS_EX 
        SELECTED_BROWSER_GLOBAL=self.selected_Browser
        remaining_emails = self.data_list[:]  
        log_message("[INFO] Processing started")
        total_emails = len(self.data_list) 

        # session = ""
        # if os.path.exists(SESSION_PATH):
        #     with open(SESSION_PATH, "r") as f:
        #         encrypted = f.read().strip()
        #         if encrypted:
        #             print("🔐 [SESSION] Déchiffrement des données de session...")
        #             decrypted = decrypt_message(encrypted, KEY)

        #             if "::" in decrypted:
        #                 parts = decrypted.split("::", 2)
        #                 if len(parts) == 3:
        #                     username = parts[0].strip()
        #                     date_str = parts[1].strip()
        #                     p_entity = parts[2].strip()
        # else:
        #     print("[❌] session.txt introuvable")


        session_info = check_session(SESSION_PATH, KEY)

        if not session_info["valid"]:
            print("[SESSION] ❌ Session invalide. Impossible de continuer l’extraction.")
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            return
        

        if self.selected_Browser == "chrome":
            print(f"✅ Navigateur sélectionné : {self.selected_Browser}")


            RESULTATS_EX = Upload_EXTENTION_PROXY("default", CLES_RECHERCHE, RESULTATS)
            print("↕️​↕️​↕️​↕️​↕️​ Résultats EX2 :")
            for item in RESULTATS_EX:
                print(json.dumps(item, indent=4, ensure_ascii=False))


        while remaining_emails or PROCESS_PIDS:

            if self.stop_flag:  
                LOGS_RUNNING=False 
                log_message("[INFO] Processing interrupted by user.")
                break


            if len(PROCESS_PIDS) < self.entered_number and remaining_emails:
                next_email = remaining_emails.pop(0)  
                email_value = Get_Key_Value(next_email, ["email", "Email"])
                log_message(f"[INFO] Processing the email:  {email_value}")

        

                try:
                    profile_email = Get_Key_Value(next_email, ["email", "Email"])
                    profile_password = Get_Key_Value(next_email, ["password_email", "passwordEmail"])
                    ip_address =Get_Key_Value(next_email, ["ip_address", "ipAddress"])
                    port = Get_Key_Value(next_email, ["port"])
                    login = Get_Key_Value(next_email, ["login"])
                    password = Get_Key_Value(next_email, ["password"])
                    recovery_email = Get_Key_Value(next_email, ["recovery_email", "recoveryEmail"])
                    new_recovery_email = Get_Key_Value(next_email, ["new_recovery_email", "neWrecoveryEmail"])


                    params = {
                        'l': encrypt_message(session_info["username"],KEY),
                        'login': session_info["username"],
                        'entity': session_info["entity"],
                        'isp': self.Isp,
                        'action': json.dumps(self.output_json_final),
                        'email': email_value,
                        'password': '',
                        'proxy_ip': ip_address+":"+port,
                        'proxy_login': f"{login};{password}" if login != session_info["username"] else "",
                        'email_recovery': '',
                        'line': '',
                        'app': "V4",
                        'e_pid':self.unique_id
                    }

                    inserted_id=Save_Email(params)
                    new_password = Generate_Gmail_Password(16)

                    session_directory = os.path.join(LOGS_DIRECTORY, f"{CURRENT_DATE}_{CURRENT_HOUR}")
                    os.makedirs(session_directory, exist_ok=True)

                    logs_subdirs = [os.path.join(LOGS_DIRECTORY, d) for d in os.listdir(LOGS_DIRECTORY) if os.path.isdir(os.path.join(LOGS_DIRECTORY, d))]
                    logs_subdirs.sort(key=os.path.getctime)

                    if len(logs_subdirs) > 4:
                        to_delete = logs_subdirs[:4]
                        for dir_to_delete in to_delete:
                            try:
                                shutil.rmtree(dir_to_delete)
                            except Exception as e:
                                log_message(f"[INFO]  Erreur lors de la suppression de {dir_to_delete} : {e}")

                  
                    if self.selected_Browser == "firefox":
                        Create_Extension_For_Email(
                            profile_email, profile_password,
                            f'"{ip_address}"', f'"{port}"',
                            f'"{login}"', f'"{password}"', f'{recovery_email}',
                            new_password, new_recovery_email, f'"{self.session_id}"' , self.selected_Browser 
                        )
                        create_firefox_profile(profile_email)
                        print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)

                        eb_ext_path = get_web_ext_path()
                        print("eb_ext_path : ", eb_ext_path)

                        command = [
                            eb_ext_path,
                            "run",
                            "--source-dir", os.path.join(self.BASE_DIRECTORY, profile_email),
                            "--firefox-profile", os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'firefox', profile_email),
                            "--keep-profile-changes",  
                            "--no-reload"
                        ]
                        process = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 
                        
                        ts   = time.time()
                        FIREFOX_LAUNCH.append({
                            'profile': profile_email,
                            'create_time': ts,
                            'proc': process,
                            'hwnd': None
                        })
                        print("Firefox launched with PID: ", process.pid)
                        Add_Pid_To_Text_File(process.pid, profile_email , inserted_id)

                    elif self.selected_Browser in ["edge", "icedragon", "Comodo"]:
                        print(f"✅ Navigateur sélectionné : {self.selected_Browser}")
                        command = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'chrome', profile_email)}",
                            f"--disable-extensions-except={os.path.join(self.BASE_DIRECTORY, profile_email)}",
                            f"--load-extension={os.path.join(self.BASE_DIRECTORY, profile_email)}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync"
                        ]
                        process = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 
                        print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)
                        Add_Pid_To_Text_File(process.pid, profile_email , inserted_id)
                    
                    else:

                        

                        profiles_dir = os.path.join(SCRIPT_DIR,'..','Tools', 'Profiles','chrome')
                        if not os.path.exists(profiles_dir):
                            os.makedirs(profiles_dir)

                        profile_path = os.path.join(profiles_dir,profile_email)
                        if not os.path.exists(profile_path):
                            print(f"🆕 Création du profil pour {profile_email}")
                            Run_Browser_Create_Profile(profile_email)
                            time.sleep(3)
                        else:
                            print(f"✅ Profil déjà existant pour {profile_email}")   


                        if not  RESULTATS_EX:
                            error_msg = (
                                "❌ An issue occurred while copying the JSON file to the template profile.\n"
                                "➡ Please contact support."
                            )
                            log_message(error_msg)   
                            self.stopped.emit(error_msg)  
                            self.stop_flag = True   
                            return                   
                        else:
                            print(f"✅ Profil prêt pour {profile_email} avec les paramètres proxy.")
                            Updated_Secure_Preferences(profile_email, RESULTATS_EX)
                            time.sleep(2)



                        # cmd = [
                        #     self.Browser_path,
                        #     f"--user-data-dir={os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'chrome', profile_email)}",
                        #     f'--profile-directory={profile_email}',
                        #     '--lang=En-US',
                        #     '--no-first-run',
                        # ]

                        # process = subprocess.Popen(cmd)

                        time.sleep(2)
                        

                        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email}"

                        b64 = Encrypt_Aes_Gcm("A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined)
                        url =f"https://example.com/?rep={combined}"

                        command = [
                            Get_Browser_Path("chrome.exe"),
                            f"--user-data-dir={os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'chrome', profile_email)}",
                            f'--profile-directory={profile_email}',
                            f'{url}',
                            '--lang=En-US',
                            '--no-first-run',
                        ]


                        process1 = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 
                        print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)
                        # add_pid_to_text_file(process.pid, profile_email , inserted_id)
             
                    self.emails_processed += 1  

                except Exception as e:
                    log_message(f"[INFO] Erreur : {e}")
            self.msleep(1000) 

        log_message("[INFO] Processing finished for all emails.") 
        time.sleep(3)
        LOGS_RUNNING=False
        self.finished.emit()















# Thread qui surveille la fin des processus Chrome/Firefox lancés
# et qui traite les fichiers de session et LOGS générés dans le dossier Downloads.
class CloseBrowserThread(QThread):


    progress = pyqtSignal(str)  



    def __init__(self , selected_Browser, username):
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username =username
        self.session_id = SESSION_ID  
        self.stop_flag = False 
        self.downloads_folder = user_downloads_dir() 




    def run(self):
        # Boucle de surveillance continue tant que tous les processus ne sont pas terminés.
        # Traite les fichiers de session et de log détectés.

        # print("Dossier Téléchargements :", self.downloads_folder)
        # print("[DEBUG] Run CloseBrowserThread")
        # print("[Thread] Dossier Téléchargements :", self.downloads_folder)
        # print("[Thread] Démarrage du thread de fermeture des navigateurs...")
        time.sleep(10)
        session = ""
        if os.path.exists(SESSION_PATH):
            with open(SESSION_PATH, "r", encoding="utf-8") as f:
                session = f.read().strip()
        else:
            print("[❌] session.txt introuvable")

        while not self.stop_flag:  
            # print("🫀🫀🫀🫀🫀🫀🫀🫀🫀 PROCESS_PIDS : ", PROCESS_PIDS)
            # print("[Thread] Vérification des processus restants...")

            if not PROCESS_PIDS:
                # print("🧠🧠🧠🧠🧠🧠🧠🧠🧠 PROCESS_PIDS : ", PROCESS_PIDS)

                # print("[Thread] Tous les processus ont été arrêtés. Fin du thread.")
                # ici fais active de button
                break

            files = [f for f in os.listdir(self.downloads_folder) if f.startswith(self.session_id) and f.endswith(".txt")]
            log_files = [f for f in os.listdir(self.downloads_folder) if f.startswith("log_") and f.endswith(".txt")]
            # affiche les files de log et de session détectés
      
            # if files:
            #     print("Fichiers de session détectés :")
            #     for file in files:
            #         print(f" - {file}")
            # else:
            #     print("Aucun files de session détecté.")

            # # Affichage des fichiers de log
            # if log_files:
            #     print("Fichiers de log détectés :")
            #     for file in log_files:
            #         print(f" - {file}")
            # else:
            #     print("Aucun fichier de log détecté.")




            # la probleme cet partie de code affiche mais les autre print dans cet classe ne s'affiche pas
            # print("Dossier Téléchargements :", self.downloads_folder)
            # print(f"[Thread] Fichiers de session détectés: {files}")
            # print(f"[Thread] Fichiers de log détectés: {log_files}")
            # print(f"[Thread] session_id: {self.session_id}")

            for file_name in files:
                file_path = os.path.join(self.downloads_folder, file_name)
                if os.path.exists(file_path):
                    print(f"[Thread] Fichier de session détecté: {file_name}")


            with ThreadPoolExecutor() as executor:
                futures = []
                for log_file in log_files:
                    futures.append(executor.submit(self.process_log_file, log_file, self.downloads_folder))

                for future in as_completed(futures):
                    result = future.result() 

                # print("[Thread][Log] Résultat:", result)

            with ThreadPoolExecutor() as executor:
                futures = []
                for file_name in files:
                    futures.append(executor.submit(self.process_session_file, file_name, self.downloads_folder , self.selected_Browser, session))

                for future in as_completed(futures):
                    result = future.result() 

                # print("[Thread][Session] Résultat:", result)

            time.sleep(1)


    

    def process_log_file(self, log_file, downloads_folder):
        #  Traite un fichier de log :
        # - Lit le contenu
        # - Déplace les données vers le fichier de log global
        # - Supprime le fichier de log
        print(f"[Traitement Log] Début du traitement de {log_file}")

        log_file_path = os.path.join(downloads_folder, log_file)

        try:
            global CURRENT_HOUR, CURRENT_DATE

            email = self.get_email_from_log_file(log_file_path)  
            if not email:
                return f"⚠️ Erreur dans le fichier {log_file}: Email non trouvé."

            session_folder = f"{CURRENT_DATE}_{CURRENT_HOUR}"
            target_folder = os.path.join(LOGS_DIRECTORY, session_folder)
            target_file_path = os.path.join(target_folder, f"{email}_{CURRENT_HOUR}.txt")

            try:
                with open(log_file_path, 'r', encoding='utf-8') as log_file_reader:
                    log_content = log_file_reader.read()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {log_file}: {e}"

            try:
                with open(target_file_path, 'a', encoding='utf-8') as target_file_writer:
                    target_file_writer.write(log_content + "\n")
            except Exception as e:
                return f"⚠️ Erreur lors de l'écriture dans {target_file_path}: {e}"
            print(f"Fichier log supprimé et contenu déplacé: {log_file_path}")

            # Suppression du fichier log après traitement
            try:
                os.remove(log_file_path)
                return f"🗑️ Fichier log supprimé : {log_file_path}"
            except Exception as e:
                return f"⚠️ Erreur lors de la suppression du fichier {log_file_path}: {e}"

        except Exception as e:
            return f"⚠️ Erreur dans le fichier {log_file} : {e}"





    def process_session_file(self, file_name, downloads_folder , selected_Browser, session):
        # Traite un fichier de session :
        # - Récupère les infos de session (pid, email, état)
        # - Écrit dans le fichier result.txt
        # - Termine le processus si actif
        # - Supprime le fichier
        print(f"[Traitement Session] Début du traitement de {file_name}")
        file_path = os.path.join(downloads_folder, file_name)  

        try:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read().strip()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {file_name}: {e}"

            match = re.search(r"session_id:(\w+)_PID:(\d+)_Email:([\w.@]+)_Status:(\w+)", file_content)
            if not match:
                os.remove(file_path)
                return f"⚠️ Format incorrect dans {file_name}: {file_content}"

            session_id, pid, email, etat  = match.groups()
            print(f"[Session Info] PID: {pid}, Email: {email}, État: {etat}")

            log_message(f"[INFO] Email {email} has completed  processing with status {etat}.")

            # text_file_path = os.path.join(BASE_DIRECTORY, email , "data.txt")

            text_file_path = os.path.join(BASE_DIRECTORY, email , "data.txt")

            try:
                with open(text_file_path, 'r', encoding='utf-8') as file:
                    first_line = file.readline().strip()  # lire juste la première ligne

                    parts = first_line.split(":")
                    if len(parts) >= 4:
                        inserted_id = parts[3]
                        print(f"😶‍🌫️😶‍🌫️ ID extrait : {inserted_id}")
                    else:
                        return f"⚠️ Format de ligne invalide dans le fichier : {first_line}"

            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {file_path}: {e}"

            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read().strip()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {file_name}: {e}"
            
            try:
                with open(RESULT_FILE_PATH, 'a', encoding='utf-8') as result_file:
                    result_file.write(f"{session_id}:{pid}:{email}:{etat}\n")
                    params = {
                        'id': inserted_id,
                        'login': self.username,
                        'status': 'OK' if etat == "completed" else 'NotOK',
                        'error':  '' if etat == "completed" else etat
                    }

                    Send_Status(params)

            except Exception as e:
                return f"⚠️ Erreur lors de l'écriture dans le fichier {file_name}: {e}"

         
            pid = int(pid)
            if pid in PROCESS_PIDS: 
                print(f"[Session] Tentative de fermeture du processus PID {pid} ({email})")
                log_message(f"[INFO] Attempting to terminate process:  {email}.")
                if selected_Browser == "firefox":
                    try:
                        print("browser : ", selected_Browser)
                        print('✅✅✅✅✅✅✅✅PID : ', pid)
                        self.find_firefox_window(email)
                        self.wait_then_close(email)
                        PROCESS_PIDS.remove(pid)   
                        print(f"Processus {pid} ({email}) terminé.")
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la fermeture du processus {pid} ({email}): {e}")
                    
                else:
                    try:
                        print('✅✅✅✅✅✅✅✅✅✅ PID : ', pid)
                        os.kill(pid, signal.SIGTERM) 
                        PROCESS_PIDS.remove(pid)   
                        print(f"Processus {pid} ({email}) terminé.")
    
                    except Exception as e:
                        return f"⚠️ Erreur lors de la fermeture du processus {file_name}: {e}"
            try:
                os.remove(file_path)
                print(f"Fichier session supprimé: {file_path}")
                return f"🗑️ Fichier session supprimé : {file_path}"
            except Exception as e:
                return f"⚠️ Erreur lors de la suppression du fichier {file_name}: {e}"


        except Exception as e:
            return f"⚠️ Erreur dans le fichier {file_name} : {e}"



    

    def find_firefox_window(self, profile_email, timeout=30):
        print(f"\n{'='*50}\n🔍 DÉBUT RECHERCHE FENÊTRE POUR {profile_email.upper()}\n{'='*50}")
        entry = next((e for e in FIREFOX_LAUNCH if e['profile'] == profile_email), None)
        if not entry:
            raise ValueError(f"❌ ERREUR: Profil '{profile_email}' non trouvé.")

        target_title = f"EXT:{profile_email}"
        print(f"• Titre recherché : {target_title}")
        print(f"• Timeout : {timeout}s\n")

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1
            elapsed = time.time() - start_time
            print(f"\n🔎 Tentative #{attempt} (écoulé: {elapsed:.1f}s)")

            found = [False]

            def window_processor(hwnd, _):
                if found[0]:
                    return False

                if not win32gui.IsWindowVisible(hwnd):
                    return True

                try:
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name != 'MozillaWindowClass':
                        return True

                    window_title = win32gui.GetWindowText(hwnd)
                    print(f"🔸 Fenêtre détectée - HWND: {hwnd} | Title: {window_title}")

                    if target_title in window_title:
                        entry['hwnd'] = hwnd
                        found[0] = True
                        print(f"\n✅ FENÊTRE MATCHÉE PAR TITRE:")
                        print(f"  • HWND  : {hwnd}")
                        print(f"  • Title : {window_title}")
                        return False
                except Exception as e:
                    print(f"⚠️ Erreur lors du traitement de la fenêtre HWND={hwnd} : {e}")
                return True
            try:
                win32gui.EnumWindows(window_processor, None)
            except Exception as e:
                print(f"⚠️ Exception EnumWindows : {e}")
            if entry['hwnd']:
                print(f"\n🎯 Fenêtre correspondante trouvée (HWND={entry['hwnd']})")
                return entry['hwnd']
            print("⏳ Nouvelle tentative dans 2 secondes...")
            time.sleep(2)

        print("❌ Timeout. Aucune fenêtre Firefox avec le titre spécifié.")
        raise TimeoutError(f"Impossible de trouver la fenêtre pour {profile_email}")




    def wait_then_close(self, profile_email):
        entry = next((e for e in FIREFOX_LAUNCH if e['profile'] == profile_email), None)
        if not entry or not entry.get('hwnd'):
            print(f"❌ Aucune fenêtre trouvée pour {profile_email}.")
            return
        
        print(f"⏰ Fermeture de la fenêtre (HWND={entry['hwnd']})")
        self.close_window_by_hwnd(entry['hwnd'], entry['proc'])




    def close_confirmation_dialogs(self, pid):
        def _enum(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, p = win32process.GetWindowThreadProcessId(hwnd)
                if p == pid and win32gui.GetClassName(hwnd) == '#32770':
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True

        win32gui.EnumWindows(_enum, None)





    def close_window_by_hwnd(self, hwnd, proc, wait_grace=2, wait_force=3):
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        time.sleep(wait_grace)

        if not win32gui.IsWindow(hwnd):
            return

        self.close_confirmation_dialogs(proc.pid)
        time.sleep(0.5)

        if not win32gui.IsWindow(hwnd):
            return

        try:
            proc.terminate()
            proc.wait(timeout=wait_force)
        except Exception:
            pass




    def get_email_from_log_file(self, file_name):
        # Extrait l'adresse email depuis un nom de fichier log formaté.
        print(f"🔎 Extraction de l'adresse email depuis le fichier {file_name}...")
        file_name = os.path.basename(file_name)
        match = re.search(r"log_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z_([\w.+-]+@[\w.-]+\.[a-zA-Z]{2,6})\.txt", file_name)
        if match:
            print(f"   - Email extrait : {match.group(1)}")
            email = match.group(1)
            return email
        else:
            print(f"[Email Extraction] Aucun email trouvé dans {file_name}")
            return None










# QTabBar personnalisé pour un affichage vertical avec des styles adaptés.
# Affiche les onglets avec icônes, couleurs personnalisées et texte formaté.
class VerticalTabBar(QtWidgets.QTabBar):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShape(QtWidgets.QTabBar.Shape.RoundedWest)

        self.tab_margin = 0
        self.left_margin = 0
        self.right_margin = 0


    def tabSizeHint(self, index):
        # Retourne la taille personnalisée d'un onglet vertical.
        size_hint = super().tabSizeHint(index)
        size_hint.transpose()
        size_hint.setWidth(180)
        size_hint.setHeight(60)
        return size_hint


    def tabRect(self, index):
        rect = super().tabRect(index)
        rect.adjust(self.left_margin, self.tab_margin, -self.right_margin, -self.tab_margin)
        return rect


    def paintEvent(self, event):
        # Redessine les onglets avec le style défini (couleurs, bordures, icônes, texte).
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        for i in range(self.count()):
            rect = self.tabRect(i)
            text = self.tabText(i)
            icon = self.tabIcon(i)

            painter.save()
            if self.currentIndex() == i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor("#669bbc")))
            else:
                painter.setBrush(QtGui.QBrush(QtGui.QColor("#F5F5F5")))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawRect(rect)  
            border_pen = QtGui.QPen(QtGui.QColor("#669bbc"))
            border_pen.setWidth(1)
            painter.setPen(border_pen)
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.drawLine(rect.topRight(), rect.bottomRight())
            painter.restore()
            painter.save()

            if not icon.isNull():
                pixmap = icon.pixmap(24, 24)
                icon_pos = QtCore.QPoint(rect.left() + 8, rect.top() + 15)
                painter.drawPixmap(icon_pos, pixmap)

            painter.setPen(QtGui.QPen(QtGui.QColor("#333")))
            font = painter.font()
            font.setPointSize(10)
            font.setFamily("Times New Roman")
            painter.setFont(font)

            text_rect = QtCore.QRect(
                rect.left() + 44,
                rect.top(),
                rect.width() - 45,
                rect.height() - 8
            )
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft, text)
            painter.restore()











# QTabWidget personnalisé pour utiliser VerticalTabBar comme barre d'onglets.
# Position des onglets sur le côté gauche (Ouest).
class VerticalTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(VerticalTabBar())
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)








# 📥 Télécharger fichier depuis URL
def Download_File(url, dest_path):
    try:
        print(f"⬇️ Téléchargement depuis : {url}")
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"   → Progression : {percent:.2f}%", end="\r")
        print(f"\n✅ Téléchargement terminé : {dest_path}")
        return True
    except Exception as e:
        print("❌ Erreur lors du téléchargement :", e)
        return False







# 🔧 Forcer suppression même si fichier en lecture seule
def Remove_Readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)







# 📦 Télécharger et extraire le projet GitHub
def Update_From_Serveur(remote_version=None):
    try:
        print("📥 Téléchargement de la dernière version depuis GitHub ...")
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "Ext3.zip")

            if not Download_File(SERVEUR_ZIP_URL_EX3, zip_path):
                print("❌ Impossible de télécharger le fichier ZIP depuis GitHub.")
                return False

            if os.path.exists(EXTENTION_EX3):
                print(f"🗑️ Suppression de l'ancien dossier {EXTENTION_EX3} ...")
                shutil.rmtree(EXTENTION_EX3, onerror=Remove_Readonly)

            print("📂 Extraction du fichier ZIP ...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            extracted_dir = None
            for item in os.listdir(tmpdir):
                item_path = os.path.join(tmpdir, item)
                if os.path.isdir(item_path):
                    extracted_dir = item_path
                    break

            if extracted_dir is None:
                print("❌ Impossible de trouver le dossier extrait dans le ZIP.")
                return False

            shutil.move(extracted_dir, EXTENTION_EX3)
            print(f"✅ Mise à jour réussie : {EXTENTION_EX3}")
            return True
    except Exception as e:
        print("❌ Erreur lors de la mise à jour :", e)
        traceback.print_exc()
        return False






def Check_Version_Extention(window):
    """
    Checks and updates the Chrome extension if necessary.
    Returns:
        str  -> returns the remote version if an update is required
        True -> extension exists and is up to date
        False -> failure (download issue, fetch remote error, manifest mismatch, or missing local extension files)
    """
    try:
        print("\n🔎 Checking local and remote extension versions...")

        # Fetch remote version
        try:
            response = requests.get(CHECK_URL_EX3, verify=False, timeout=10)
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
            print(f"❌ Unable to fetch remote version: {e}")
            Show_Critical_Message(
                window,
                "Network / Remote Version Error",
                f"Unable to fetch the remote version. Check your connection or contact support.\n\nTechnical details: {str(e).capitalize()}",
                message_type="critical"
            )
            return False

        # Check local files
        if not os.path.exists(MANIFEST_PATH_EX3) or not os.path.exists(VERSION_LOCAL_EX3):
            print("⚠️ Local files missing for version check.")
            Show_Critical_Message(
                window,
                "Missing Local Files",
                "The local extension files could not be found. Please reinstall the extension.",
                message_type="critical"
            )
            return False

        # Read local manifest
        with open(MANIFEST_PATH_EX3, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        local_manifest_version = manifest_data.get("version", None)

        # Read local version
        with open(VERSION_LOCAL_EX3, "r", encoding="utf-8") as f:
            local_version = f.read().strip()

        print(f"📄 Local version : {local_version}, Local manifest : {local_manifest_version}")
        print(f"🌍 Remote version : {remote_version}, Remote manifest : {remote_manifest_version}")

        # Check manifest compatibility
        if str(local_manifest_version) != str(remote_manifest_version):
            Show_Critical_Message(
                window,
                "Manifest Incompatibility",
                "The local manifest version does not match the remote one.\nPlease contact support.",
                message_type="critical"
            )
            print("⚠️ Manifest incompatible, automatic update not possible.")
            return False

        # Check version difference
        if local_version != remote_version:
            print(f"🔄 Update required (new version: {remote_version})")
            return remote_version  # update required
        else:
            print("✅ Local extension is up to date.")
            return True  # already up to date

    except Exception as e:
        print(f"❌ Unexpected error in Check_Version_Extention: {e}")
        Show_Critical_Message(
            window,
            "Internal Error",
            "An unexpected error occurred during extension verification. Please contact support.",
            message_type="critical"
        )
        return False












def Process_Browser(window, selected_Browser):
    if selected_Browser != "chrome":
        print(f"⚠️ Navigateur non pris en charge : {selected_Browser}")
        return False  

    print(f"\n🌐 Navigateur sélectionné : {selected_Browser}")

    # Étape 1 : Vérification du dossier de configuration
    print("\n🔍 Étape 1 : Vérification du dossier de configuration ...")
    if not os.path.exists(CONFIG_PROFILE):
        print(f"❌ Le dossier requis '{CONFIG_PROFILE}' est introuvable.")
        return False  
    print(f"📂 Dossier de configuration trouvé : {CONFIG_PROFILE}")

    # Étape 2 : Vérification du fichier secure_preferences
    print("\n🔍 Étape 2 : Vérification du fichier secure_preferences ...")
    if not os.path.exists(SECURE_PREFERENCES_TEMPLATE):
        print(f"❌ Le fichier '{SECURE_PREFERENCES_TEMPLATE}' est introuvable.")
        return False  

    try:
        with open(SECURE_PREFERENCES_TEMPLATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Lecture réussie du fichier Secure Preferences.")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier secure_preferences : {e}")
        return False  

    results_keys=[]
    missing_keys = []  # Liste des clés manquantes

    # Étape 3 : Vérification des clés attendues
    Search_Keys(data, CLES_RECHERCHE , results_keys)



    found_keys = [list(d.keys())[0] for d in results_keys]  
    for key in CLES_RECHERCHE:
        if key in found_keys:
            print(f"✅ Clé trouvée : {key}")
        else:
            print(f"❌ Clé manquante : {key}")
            missing_keys.append(key)

    if missing_keys:
        print("\n⚠️ Vérification échouée : certaines clés sont manquantes.")
        print("Clés manquantes :")
        for idx, k in enumerate(missing_keys, start=1):
            print(f"   {idx}. {k}")
        return False  
    else:
        print("\n✅ Toutes les clés requises ont été trouvées avec succès.")

    # Étape 4 : Vérification et mise à jour de l'extension locale
    print("\n🔍 Étape 4 : Vérification de l'extension locale ...")
    if not os.path.exists(EXTENTION_EX3):
        print(f"📂 Le dossier '{EXTENTION_EX3}' a été créé car il n'existait pas.")
        print("📥 Téléchargement de la dernière version de l'extension...")
        if Update_From_Serveur():
            print("✅ Extension installée avec succès.")
        else:
            print("We could not install the extension. Please contact Support.")
            return False  
    else:
        print(f"📂 Extension trouvée : {EXTENTION_EX3}")
        remote_version = Check_Version_Extention(window)

        if isinstance(remote_version, str):  # Mise à jour nécessaire
            print(f"🔄 Mise à jour nécessaire vers {remote_version}")
            if Update_From_Serveur(remote_version):
                print("✅ Mise à jour réussie : l'extension a été mise à jour avec succès !")
            else:
                print("We could not update the extension from GitHub. Please contact Support.")
                return False  
        elif remote_version is True:
            print("✅ L'extension locale est déjà à jour.")
        else:
            print("Unable to verify extension version. Please contact Support.")
            return False  

    # Si toutes les étapes ont réussi
    print("\n🎉 Traitement terminé avec succès pour le navigateur Chrome.")
    return True






def check_session(SESSION_PATH, KEY):
    """
    Vérifie la validité d'une session stockée dans un fichier session.txt
    et retourne un dictionnaire avec les informations utiles.

    Args:
        SESSION_PATH (str): Chemin vers le fichier session.
        KEY (bytes/str): Clé utilisée pour le déchiffrement.

    Returns:
        dict: {
            "valid": bool,
            "username": str or None,
            "date": datetime or None,
            "p_entity": str or None,
            "error": str or None
        }
    """
    session_info = {
        "valid": False,
        "username": None,
        "date": None,
        "p_entity": None,
        "error": None
    }

    print(f"[INFO] Chemin du fichier session : {SESSION_PATH}")

    if not os.path.exists(SESSION_PATH):
        print("[AVERTISSEMENT SESSION] ❌ Le fichier session.txt n'existe pas")
        session_info["error"] = "FileNotFound"
        return session_info

    print("[INFO] Le fichier session.txt existe ✅")

    try:
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            encrypted = f.read().strip()

        print(f"[INFO] Contenu chiffré lu :\n'{encrypted}'")
        print(f"[INFO] Longueur du contenu chiffré : {len(encrypted)} caractères")

        if not encrypted:
            print("[AVERTISSEMENT SESSION] Le fichier session.txt est vide ❌")
            session_info["error"] = "EmptyFile"
            return session_info

        # Tentative de déchiffrement
        try:
            decrypted = decrypt_message(encrypted, KEY)
            print(f"[INFO] Contenu déchiffré complet :\n'{decrypted}'")
            print(f"[INFO] Longueur du contenu déchiffré : {len(decrypted)} caractères")
        except Exception as e:
            print(f"[ERREUR DECHIFFREMENT] Erreur lors du déchiffrement : {e}")
            session_info["error"] = f"DecryptError: {e}"
            return session_info

        # Analyse du contenu déchiffré
        parts = decrypted.split("::", 2)
        print(f"[INFO] Contenu découpé en {len(parts)} parties : {parts}")

        if len(parts) != 3:
            print("[ERREUR FORMAT SESSION] ❌ Format invalide (attendu : username::date::p_entity)")
            print(f"[DEBUG] Contenu déchiffré complet : '{decrypted}'")
            session_info["error"] = "InvalidFormat"
            return session_info

        username, date_str, p_entity = [p.strip() for p in parts]

        print(f"[INFO] Nom d'utilisateur : '{username}'")
        print(f"[INFO] Date de session (date_str) : '{date_str}'")
        print(f"[INFO] p_entity : '{p_entity}'")

        try:
            tz = pytz.timezone("Africa/Casablanca")
            print(f"[DEBUG] Conversion de la date '{date_str}' en datetime...")
            last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            last_session = tz.localize(last_session)

            now = datetime.datetime.now(tz)
            print(f"[INFO] Date de la session : {last_session}")
            print(f"[INFO] Date actuelle : {now}")

            if (now - last_session) < timedelta(days=2):
                session_info.update({
                    "valid": True,
                    "username": username,
                    "date": last_session,
                    "p_entity": p_entity
                })
                print(f"[SESSION] ✅ Session valide pour l'utilisateur '{username}' (p_entity = {p_entity})")
            else:
                print("[SESSION EXPIRÉE] ⌛ La session a expiré depuis plus de 2 jours")
                session_info["error"] = "Expired"
        except ValueError as e:
            print(f"[ERREUR FORMAT DATE] ❌ Format de date invalide : {e}")
            print(f"[DEBUG] Contenu complet de date_str : '{date_str}'")
            session_info["error"] = f"InvalidDateFormat: {e}"

    except Exception as e:
        print(f"[ERREUR LECTURE SESSION] ❌ Exception lors de la lecture du fichier : {e}")
        session_info["error"] = f"FileReadError: {e}"

    return session_info






class MainWindow(QMainWindow):
    # Initialise l'interface graphique principale de l'application.
    # - Charge le fichier `.ui` et connecte les éléments de l'interface.
    # - Configure les templates, boutons, onglets, styles, icônes, champs, et autres éléments de la GUI.
    # - Initialise les conteneurs de scénarios, options de reset et de LOGS.
    # - Connecte les signaux aux slots pour les boutons cliqués.
    # - Applique le style personnalisé aux QSpinBox, QComboBox et onglets verticaux.
    # - Prépare la zone d'affichage des LOGS et lance le thread associé.

    def __init__(self, json_data):

        super(MainWindow, self).__init__()

        # Charger l'interface utilisateur depuis le fichier .ui
        uic.loadUi(INTERFACE_UI , self)
        
        # Initialiser les données et layouts principaux
        self.states = json_data
        self.STATE_STACK = []

        def get_widget(name, wtype):
            widget = self.findChild(wtype, name)
            if widget is None:
                print(f"⚠️ Widget '{name}' introuvable.")
            return widget


        self.reset_options_container = self.findChild(QWidget, "resetOptionsContainer")
        self.reset_options_layout = QVBoxLayout(self.reset_options_container)
        self.reset_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scenario_container = self.findChild(QWidget, "scenarioContainer")
        self.scenario_layout = QVBoxLayout(self.scenario_container)
        self.scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop )


        # Masquer les templates visuels non utilisés par défaut
        self.template_button = self.findChild(QPushButton, "TemepleteButton")
        self.Temeplete_Button_2 = self.findChild(QPushButton, "TemepleteButton_2")
        self.template_Frame1 = self.findChild(QFrame, "Template1")
        self.template_Frame2 = self.findChild(QFrame, "Template2")
        self.template_Frame3 = self.findChild(QFrame, "Template3")
        self.template_Frame4 = self.findChild(QFrame, "Template4")
        self.template_Frame5 = self.findChild(QFrame, "Template5")
        self.Temeplete_Button_2.hide()
        self.template_button.hide()
        self.template_Frame1.hide()
        self.template_Frame2.hide()
        self.template_Frame4.hide()
        self.template_Frame5.hide()

        # Connexion du bouton d'état initial
        self.Button_Initaile_state = self.findChild(QPushButton, "Button_Initaile_state")
        
        if self.Button_Initaile_state:
            self.Button_Initaile_state.clicked.connect(self.Load_Initial_Options)

        # Connexion du bouton de soumission
        self.submit_button = self.findChild(QPushButton, "submitButton")
        if self.submit_button:
            self.submit_button.clicked.connect(lambda: self.Submit_Button_Clicked(self))

        # Icône et action pour le bouton de nettoyage
        self.ClearButton = self.findChild(QPushButton, "ClearButton")

        if self.ClearButton:
            clear_path = os.path.join(ICONS_DIR_INTERFACE, "clear.png").replace("\\", "/")
            if os.path.exists(clear_path):
                icon = QIcon(clear_path)
                self.ClearButton.setIcon(icon)
                self.ClearButton.setIconSize(QSize(32, 32))

            # جعل الأيقونة في المنتصف وإزالة النص
            self.ClearButton.setText("")
            self.ClearButton.setFixedSize(36, 36)  # حسب حجم الأيقونة

            self.ClearButton.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton::icon {
                    alignment: center;
                }
            """)

            self.ClearButton.clicked.connect(self.Clear_Button_Clicked)



        self.CopyButton = self.findChild(QPushButton, "CopyButton")

        if self.CopyButton:
            clear_path = os.path.join(ICONS_DIR_INTERFACE, "copyLog.png").replace("\\", "/")
            if os.path.exists(clear_path):
                icon = QIcon(clear_path)
                self.CopyButton.setIcon(icon)
                self.CopyButton.setIconSize(QSize(26, 26))

                # إخفاء النص داخل الزر
                self.CopyButton.setText("")

                # إزالة المساحات وتوسيط المحتوى
                self.CopyButton.setStyleSheet("""
                    QPushButton {
                        border: none;
                        padding: 0px;
                        margin: 0px;
                        background-color: transparent;
                    }
                    QPushButton::icon {
                        alignment: center;
                    }
                """)

                # اختياري: جعل الزر مربع الشكل لتناسب الأيقونة
                self.CopyButton.setFixedSize(38, 38)  # حسب الحاجة
                self.CopyButton.clicked.connect(self.Copy_Logs_To_Clipboard)



        self.SaveButton = self.findChild(QPushButton, "saveButton")

        if self.SaveButton:
            icon_path_save = os.path.join(ICONS_DIR_INTERFACE, "save.png").replace("\\", "/")
            if os.path.exists(icon_path_save):
                icon = QIcon(icon_path_save)
                self.SaveButton.setIcon(icon)
                self.SaveButton.setIconSize(QSize(16, 16))
                self.SaveButton.clicked.connect(self.Handle_Save)


        # Champ de recherche (masqué au démarrage)
        self.lineEdit_search = self.findChild(QLineEdit, "lineEdit_search")

        if self.lineEdit_search:
            self.lineEdit_search.hide()
        
        # Configuration des onglets principaux avec icônes personnalisés
        self.tabWidgetResult = self.findChild(QTabWidget, "tabWidgetResult")

        if self.tabWidgetResult:
            self.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
            if os.path.exists(DEFAULT_ICON_PATH):
                icon_size = (40, 40)  
                for i in range(self.tabWidgetResult.count()):
                    tab_text = self.tabWidgetResult.tabText(i)
                    icon_name = tab_text.lower().replace(" ", "_") + ".png"
                    icon_path = os.path.join(DEFAULT_ICON_PATH, icon_name)
                    if os.path.exists(icon_path):
                        icon = QIcon(icon_path)
                        icon_pixmap = icon.pixmap(icon_size[0], icon_size[1])
                        icon = QIcon(icon_pixmap)
                        self.tabWidgetResult.setTabIcon(i, icon)



        # if self.tabWidgetResult:
        #     for i in range(self.tabWidgetResult.count()):
        #         widget = self.tabWidgetResult.widget(i)
        #         text = self.tabWidgetResult.tabText(i)

            # Remplacement du QTabWidget par un VerticalTabWidget personnalisé
            self.vertical_tab_widget = VerticalTabWidget()
            parent_widget = self.tabWidgetResult.parentWidget()
            geometry = self.tabWidgetResult.geometry()

            while self.tabWidgetResult.count() > 0:
                widget = self.tabWidgetResult.widget(0)
                text = self.tabWidgetResult.tabText(0)
                icon = self.tabWidgetResult.tabIcon(0)


                self.vertical_tab_widget.addTab(widget, icon, text)
                style_sheet = widget.styleSheet()
                object_name = widget.objectName()
                self.vertical_tab_widget.widget(self.vertical_tab_widget.count() - 1).setStyleSheet(style_sheet)
                self.vertical_tab_widget.widget(self.vertical_tab_widget.count() - 1).setObjectName(object_name)

            self.tabWidgetResult.setParent(None)
            self.vertical_tab_widget.setParent(parent_widget)
            self.vertical_tab_widget.setObjectName("tabWidgetResult") 
            self.vertical_tab_widget.setGeometry(geometry)  
            self.vertical_tab_widget.show()


            self.tabWidgetResult = self.vertical_tab_widget
            self.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)



        # Mise en forme des onglets secondaires (interface_2)
        self.INTERFACE = self.findChild(QTabWidget, "interface_2")

        if self.INTERFACE:
            self.INTERFACE.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
            for i in range(self.INTERFACE.count()):
                tab_text = self.INTERFACE.tabText(i)
                if tab_text.startswith("Result"):
                    tab_widget = self.INTERFACE.widget(i)
                    frame = QFrame(tab_widget)
                    frame.setStyleSheet("background-color: #F5F5F5; border-right: 1px solid #669bbc;")
                    frame.setGeometry(0, 660, 179, 300)
                    frame.show()
                    break

        # Placeholder dans les champs textEdit
        self.textEdit_3.setPlaceholderText(
            "Please enter the data in the following format : \n"
            "Email* ; passwordEmail* ; ipAddress* ; port* ; login ; password ; recovery_email , new_recovery_email"
        )
        self.textEdit_4.setPlaceholderText(
            "Specify the maximum number of operations to process"
        )
        


        # Étirement automatique des colonnes dans les tableaux
        for table in self.findChildren(QTableWidget):
            for col in range(table.columnCount()):
                table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        # Personnalisation des boutons de QSpinBox avec des flèches    
        spin_boxes = self.findChildren(QSpinBox)
        if DOWN_EXISTS and UP_EXISTS:
            for spin_box in spin_boxes:
                old_style = spin_box.styleSheet()  
                spin_box.setStyleSheet(old_style + f"""
                    QSpinBox::down-button {{
                        image: url("{ARROW_DOWN_PATH}");
                        width: 13px;
                        height: 13px;
                        border-top-left-radius: 5px;
                        border-bottom-left-radius: 5px;
                    }}
                    QSpinBox::up-button {{
                        image: url("{ARROW_UP_PATH}");
                        width: 13px;
                        height: 13px;
                        border-top-left-radius: 5px;
                        border-bottom-left-radius: 5px;
                    }}
                """)

        # Initialisation du thread d'affichage des LOGS
        self.LOGS_THREAD = LogsDisplayThread(LOGS)
        self.LOGS_THREAD.log_signal.connect(self.Update_Logs_Display)

        # Configuration du QComboBox "browsers" avec icônes et style
        self.browser = self.findChild(QComboBox, "browsers")
        if self.browser is not None:
            if os.path.exists(ARROW_DOWN_PATH):
                new_style = f'''
                    QComboBox::down-arrow {{
                        image: url("{ARROW_DOWN_PATH}");
                        width: 16px;
                        height: 16px;
                    }}
                '''
                old_style = self.browser.styleSheet()
                self.browser.setStyleSheet(old_style + new_style)


            self.browser.addItem(QIcon(os.path.join(ICONS_DIR_INTERFACE, "chrome.png")), "Chrome")
            self.browser.addItem(QIcon(os.path.join(ICONS_DIR_INTERFACE, "firefox.png")), "Firefox")
            self.browser.addItem(QIcon(os.path.join(ICONS_DIR_INTERFACE, "edge.png")), "Edge")
            self.browser.addItem(QIcon(os.path.join(ICONS_DIR_INTERFACE, "comodo.png")), "Comodo")
    


        self.Isp = self.findChild(QComboBox, "Isps")
        if self.Isp is not None:
            print("✅ QComboBox 'Isps' trouvé.")

            # 🔽 Style de flèche personnalisée
            if os.path.exists(ARROW_DOWN_PATH):
                print(f"🎨 Fichier flèche trouvé : {ARROW_DOWN_PATH}")
                new_style = f'''
                    QComboBox::down-arrow {{
                        image: url("{ARROW_DOWN_PATH}");
                        width: 16px;
                        height: 16px;
                    }}
                '''
                old_style = self.Isp.styleSheet()
                self.Isp.setStyleSheet(old_style + new_style)
            else:
                print(f"❌ Fichier flèche manquant : {ARROW_DOWN_PATH}")

            # 📁 Icônes
            print(f"📁 Dossier d'icônes : {ICONS_DIR_INTERFACE}")
            self.Isp.clear()

            services = {
                "Gmail": "Gmail.png",
                # "Hotmail": "Hotmail.png",
                # "Yahoo": "Yahoo.png"
            }

            for name, icon_file in services.items():
                icon_path = os.path.join(ICONS_DIR_INTERFACE, icon_file)
                if os.path.exists(icon_path):
                    self.Isp.addItem(QIcon(icon_path), name)
                    print(f"✅ Ajout de l'élément '{name}' avec icône : {icon_path}")
                else:
                    self.Isp.addItem(name)
                    print(f"⚠️ Icône manquante pour '{name}' : {icon_path}, ajouté sans icône.")

            selected_isp = None

            if os.path.exists(FILE_ISP):
                print(f"📄 Lecture de : {FILE_ISP}")
                with open(FILE_ISP, 'r', encoding='utf-8') as f:
                    line = f.readline().strip().lower()
                    print(f"🔍 Valeur lue dans Isp.txt : '{line}'")
                    if "gmail" in line:
                        selected_isp = "Gmail"
                    elif "hotmail" in line:
                        selected_isp = "Hotmail"
                    elif "yahoo" in line:
                        selected_isp = "Yahoo"
                    else:
                        print("⚠️ Aucune correspondance trouvée dans le fichier.")
            else:
                print(f"❌ Fichier Isp.txt non trouvé : {FILE_ISP}")



            # ✅ Définir la valeur sélectionnée par défaut
            if selected_isp:
                index = self.Isp.findText(selected_isp)
                if index >= 0:
                    self.Isp.setCurrentIndex(index)
                    print(f"✅ Élément '{selected_isp}' sélectionné dans la QComboBox.")
                else:
                    print(f"❌ Élément '{selected_isp}' introuvable dans la QComboBox.")
        else:
            print("❌ QComboBox 'Isps' introuvable.")



            
        self.saveSanario = self.findChild(QComboBox, "saveSanario")
        if self.saveSanario is not None:
                    if os.path.exists(ARROW_DOWN_PATH):
                        new_style = f'''
                            QComboBox::down-arrow {{
                                image: url("{ARROW_DOWN_PATH}");
                                width: 16px;
                                height: 16px;
                            }}
                        '''
                        old_style = self.saveSanario.styleSheet()
                        self.saveSanario.setStyleSheet(old_style + new_style)
                        self.saveSanario.currentTextChanged.connect(self.Scenario_Changed)


        # selectinner Qframe avec Object souName "LogOut"
        # fais backgroud image  os.path.join(icons_dir, "LogOut.png")
  

        self.image_path = os.path.join(ICONS_DIR_INTERFACE, "LogOut4.png")
        self.log_out_Button = self.findChild(QPushButton, "LogOut")

        if self.log_out_Button:
            self.log_out_Button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  
            self.log_out_Button.clicked.connect(self.logOut)

            if os.path.exists(self.image_path):
                self.log_out_Button.setIcon(QIcon(self.image_path))
                self.log_out_Button.setIconSize(QSize(18, 18))




        # Initialisation de l'affichage des LOGS
        self.log_container = self.findChild(QWidget, "log")
        self.log_layout = QVBoxLayout(self.log_container)  
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_container.adjustSize() 
        self.log_container.setFixedWidth(1627)

        self.result_tab_widget = self.findChild(QTabWidget, "tabWidgetResult")

        if self.result_tab_widget:
            print("[DEBUG] ✅ tabWidgetResult trouvé dans l'interface.")
        else:
            print("[DEBUG] ❌ tabWidgetResult introuvable. Vérifiez le nom de l'objet dans le fichier .ui.")
        

        self.Set_Icon_For_Existing_Buttons()
        self.Load_Scenarios_Into_Combobox()

        # Chargement initial des options
        self.Load_Initial_Options()



    def Save_Process(self, parameters):
        try:
            response = requests.post(_SAVE_PROCESS_API, data=parameters, headers=HEADERS)
            print(f"🌐 [POST] URL: {_SAVE_PROCESS_API}")
            print(f"📤 [POST] Paramètres envoyés: {parameters}")
            print(f"📥 [HTTP] Code de réponse: {response.status_code}")
            print(f"📄 [HTTP] Réponse brute:\n{response.text}")

            results = response.json()
            status = results.get('status', False)

            if status is True:
                print(f"✅ [API] Insertion réussie ➜ ID inséré: {results.get('inserted_id')}")
                return results.get('inserted_id')
            else:
                print(f"❌ [API] Échec de l'insertion ➜ Détails: {results}")
                return -1

        except ValueError as ve:
            print(f"💥 [JSON ERROR] Impossible de parser la réponse JSON: {ve}")
            return -1
        except Exception as e:
            print(f"💥 [EXCEPTION] Erreur lors de l'appel POST: {e}")
            return -1

        


    def Handle_Save(self):
        """
        Sends the current scenario state to the API and handles responses.
        Displays user-friendly messages for errors and success.
        """
        # 1️⃣ Check if there are any actions to save
        if not self.STATE_STACK:
            msg = "No actions to save. Please add actions before saving."
            print("[❌] " + msg)
            Show_Critical_Message(self, "No Data", msg, message_type="critical")
            return

        # 2️⃣ Check if the session file exists
        if not os.path.exists(SESSION_PATH):
            msg = "Your session file is missing. Please restart the application."
            print("[❌] " + msg)
            Show_Critical_Message(self, "Session Not Found", msg, message_type="critical")
            return

        # 3️⃣ Read the encrypted session key
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            encrypted_key = f.read().strip()

        payload = {
            # ⚠️ Ton PHP attend "encrypted", pas "decrypted_key"
            "encrypted": encrypted_key,
            "state": self.STATE_STACK[-1],
            "state_stack": self.STATE_STACK
        }

        # 4️⃣ Send payload to API
        try:
            response = requests.post(_HANDLE_SAVE_API, json=payload)

            print("\n--- DEBUG API RESPONSE ---")
            print("HTTP Status:", response.status_code)
            print("Raw Response:", response.text)  # 🔍 voir tout ce que renvoie PHP
            try:
                result = response.json()
                print("Parsed JSON:", result)
            except Exception as je:
                print("⚠️ JSON Decode Error:", je)
                result = {}

            # 5️⃣ Process API response
            if response.status_code == 200:
                # 🔐 Session validation
                if result.get("session") is False:
                    msg = "Your session has expired. Please log in again."
                    print("[🔒] " + msg)
                    Show_Critical_Message(self, "Session Expired", msg, message_type="critical")

                    # Open login window and close MainWindow
                    self.login_window = LoginWindow()
                    self.login_window.setFixedSize(1710, 1005)
                    screen = QGuiApplication.primaryScreen()
                    screen_geometry = screen.availableGeometry()
                    x = (screen_geometry.width() - self.login_window.width()) // 2
                    y = (screen_geometry.height() - self.login_window.height()) // 2
                    self.login_window.move(x, y)
                    self.login_window.show()

                    self.close()
                    return

                # ✅ Success
                if result.get("success"):
                    msg = f"Scenario sent successfully. Name: {result.get('name', 'N/A')}"
                    print("[✅] " + msg)
                    self.Load_Scenarios_Into_Combobox()
                    Show_Critical_Message(self, "Success", msg, message_type="success")
                else:
                    msg = result.get("error", "Unable to save the scenario due to a server error.")
                    print(f"[❌] API Error: {msg}")
                    Show_Critical_Message(self, "API Error", msg, message_type="critical")

            else:
                msg = "A network error occurred while saving. Please check your connection."
                print(f"[❌] HTTP Error - Status Code: {response.status_code}")
                Show_Critical_Message(self, "Network Error", msg, message_type="critical")

        except Exception as e:
            msg = "An unexpected error occurred while saving. Please try again."
            print(f"[❌] Exception during API request: {str(e)}")
            Show_Critical_Message(self, "Error", msg, message_type="critical")





    def Load_Scenarios_Into_Combobox(self):
        print("📥 [INFO] Début du chargement des scénarios...")

        print(f"[📂] Chemin du fichier de session: {SESSION_PATH}")

        if not os.path.exists(SESSION_PATH):
            print("[❌] Fichier session.txt introuvable.")
            return

        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            encrypted_key = f.read().strip()
        print(f"[🔐] Clé chiffrée lue: {encrypted_key}")

        payload = {"encrypted": encrypted_key}
        print(f"[📦] Payload préparé pour la requête: {payload}")

        try:
            response = requests.post(_LOAD_SCENARIOS_API, json=payload)
            print(f"[🌐] Requête envoyée. Code HTTP: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                # print(f"[📨] Réponse reçue (JSON): {result}")

                # 🟡 Vérification de session expirée
                if result.get("session") is False:
                    print("[🔒] Session expirée. Redirection vers la page de connexion.")
                    self.login_window = LoginWindow()
                    self.login_window.setFixedSize(1710, 1005)

                    screen = QGuiApplication.primaryScreen()
                    screen_geometry = screen.availableGeometry()
                    x = (screen_geometry.width() - self.login_window.width()) // 2
                    y = (screen_geometry.height() - self.login_window.height()) // 2
                    self.login_window.move(x, y)
                    self.login_window.show()

                    print("[🔁] Fenêtre de connexion affichée. Fermeture de la fenêtre actuelle...")
                    self.close()
                    return

                # ✅ Session valide → remplir la combo
                scenarios = result.get("scenarios", [])
                if scenarios:
                    print(f"✅ [INFO] Nombre de scénarios reçus: {len(scenarios)}")

                    self.saveSanario.clear()
                    self.saveSanario.addItem("None")

                    for index, scenario in enumerate(scenarios, 1):
                        name = scenario.get("name", f"Scénario {index}")
                        self.saveSanario.addItem(name)
                        print(f"   ➕ Scénario {index}: {name}")

                    print("[✅] Scénarios chargés dans la liste déroulante avec succès.")
                else:
                    self.saveSanario.addItem("None")

                    print("")
            else:
                print(f"[❌] Erreur HTTP {response.status_code}")
                print(f"[❗] Contenu de la réponse: {response.text}")

        except Exception as e:
            print(f"[❌] Erreur lors de la récupération des scénarios: {e}")






    def Set_Icon_For_Existing_Buttons(self):
        if not self.result_tab_widget:
            print("[DEBUG] ❌ tabWidgetResult introuvable. Vérifiez le nom.")
            return

        print("[DEBUG] ✅ tabWidgetResult trouvé.")

        for i in range(self.result_tab_widget.count()):
            tab_widget = self.result_tab_widget.widget(i)
            buttons = tab_widget.findChildren(QPushButton)

            for button in buttons:
                object_name = button.objectName()

                if object_name.startswith("copy"):
                    icon_path = os.path.join(ICONS_DIR_INTERFACE, "copy.png")
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(QtCore.QSize(20, 20))
                    # print(f"[DEBUG] 🎯 Icône ajoutée au bouton '{object_name}' dans l'onglet {i}")

                    # ✅ ربط الزر بدالة النسخ (مرة واحدة)
                    try:
                        button.clicked.disconnect()
                    except Exception:
                        pass  # لم يكن هناك ربط سابق

                    button.clicked.connect(lambda _, idx=i: self.Copy_Result_From_Tab(idx))
                else:
                    print(f"[DEBUG] ⏭️ Bouton ignoré: '{object_name}'")





    def Copy_Result_From_Tab(self, tab_index):
        tab_widget = self.result_tab_widget.widget(tab_index)
        list_widgets = tab_widget.findChildren(QListWidget)

        if list_widgets:
            list_widget = list_widgets[0]
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            text_to_copy = "\n".join(items)
            clipboard = QApplication.clipboard()
            clipboard.setText(text_to_copy)
            print(f"[DEBUG] 📋 {len(items)} éléments copiés dans le presse-papiers.")
        else:
            print("[DEBUG] ⚠️ Aucun QListWidget trouvé dans cet onglet.")

            


    def Copy_Logs_To_Clipboard(self):
        log_box = self.findChild(QGroupBox, "log")
        if not log_box:
            print("[DEBUG] ❌ QGroupBox 'log' introuvable.")
            return

        labels = log_box.findChildren(QLabel)

        if not labels:
            print("[DEBUG] ⚠️ Aucun QLabel trouvé dans 'log'.")
            return

        log_lines = [label.text() for label in labels]
        text_to_copy = "\n".join(log_lines)

        QApplication.clipboard().setText(text_to_copy)
        print(f"[DEBUG] 📋 {len(log_lines)} lignes de LOGS copiées dans le presse-papiers.")





    def logOut(self  ):
        global SELECTED_BROWSER_GLOBAL;
        try:
            # Supprimer la session
            if os.path.exists(SESSION_PATH):
                os.remove(SESSION_PATH)
                print("[LOGOUT] Session supprimée.")



            # selected_browser
            if(SELECTED_BROWSER_GLOBAL):
                Stop_All_Processes(self)


            # Revenir à la fenêtre de connexion
            self.login_window = LoginWindow()
            self.login_window.setFixedSize(1710, 1005)

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()

            # Fermer la fenêtre actuelle (MainWindow)
            self.close()

        except Exception as e:
            print(f"[LOGOUT ERROR] {e}")




    #Ajoute une nouvelle ligne de log dans la zone de log (interface utilisateur).
    #Chaque log est stylisé pour rester lisible avec fond transparent.
    def Update_Logs_Display(self, log_entry):
        log_label = QLabel(log_entry)
        log_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                background-color: transparent;
                font-family: "Times", "Times New Roman", serif;
                padding: 2px;
            }
        """)
        self.log_layout.addWidget(log_label)



    # Fonction appelée automatiquement à la fermeture de la fenêtre principale.
    # Permet d'arrêter proprement le thread de LOGS avant la fermeture de l'application.
    # def closeEvent(self, event):
    #     self.LOGS_THREAD.stop()  
    #     super().closeEvent(event)



    # -----------------------------
    # Enregistre les données JSON dans traitement.json selon le navigateur
    # Retourne un statut de succès ou d'erreur
    # -----------------------------

    def Save_Json_To_File(self, json_data, selected_browser):
        if selected_browser.lower() == "firefox":
            template_dir = TEMPLATE_DIRECTORY_FIREFOX
        elif selected_browser.lower() == "chrome":
            template_dir = EXTENTION_EX3
        else:
            template_dir = TEMPLATE_DIRECTORY_FAMILY_CHROME  

        traitement_file = os.path.join(template_dir, 'traitement.json')

        try:
            os.makedirs(template_dir, exist_ok=True)
            with open(traitement_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            return "SUCCESS" if template_dir != EXTENTION_EX3 else "SUCCESS_FAMILY"
        except Exception as e:
            print(f"Error while creating the file {traitement_file}: {e}")
            return "ERROR"



    # -----------------------------
    # Génération complète de l'extension Chrome/Firefox
    # -----------------------------
    # Réorganise et nettoie le JSON pour actions spécifiques
    # Supprime boucles vides et ajuste sub_process selon le contexte
    def Process_Split_Json(self, input_json):
        output_json = []
        current_section = []
        current_start = None

        def finalize_section():
            if current_section:
                output_json.extend(current_section)

        # 🔁 المرور على كل عنصر
        for element in input_json:
            process_type = element.get("process")

            # ⛔ تجاهل الحلقات الفارغة
            if process_type == "loop" and not element.get("sub_process"):
                continue

            # 📨 بداية قسم جديد
            if process_type in {"open_inbox", "open_spam"}:
                finalize_section()
                current_section = [element]
                current_start = process_type
                continue

            # 🔂 معالجة الحلقات الفرعية
            if process_type == "loop":
                sub_process = element.get("sub_process", [])

                # ✅ العمليات المسموح بها حسب نوع القسم
                allowed_items = {
                    "open_inbox": {"report_spam", "delete", "archive"},
                    "open_spam": {"not_spam", "delete", "report_spam"}
                }.get(current_start, set())

                # 🔍 التحقق من وجود عمليات خاصة داخل الحلقة
                has_select_all = any(sp.get("process") == "select_all" for sp in sub_process)
                has_allowed_item = any(sp.get("process") in allowed_items for sp in sub_process)

                # 🧹 تنظيف العمليات الفرعية عند الحاجة فقط
                if has_select_all or has_allowed_item:
                    sub_process = [
                        sp for sp in sub_process
                        if sp.get("process") not in {"return_back", "next"}
                    ]

                element["sub_process"] = sub_process
                current_section.append(element)
                continue

            # ➕ إضافة العناصر العادية
            current_section.append(element)

        finalize_section()
        return output_json


    # -----------------------------
    # Génération complète de l'extension Chrome/Firefox
    # -----------------------------
    # Gère le dernier élément de chaque loop
    # Ajoute open_message si last est next et ajuste OPEN_MESSAGE_ONE_BY_ONE
    def Process_Handle_Last_Element(self, input_json):
        output_json = []

        for element in input_json:
            process_type = element.get("process")
            if process_type in ["google_maps_actions", "save_location", "search_activities"]:
                continue

            if process_type == "loop" and "sub_process" in element:
                sub_process = element["sub_process"]
                if sub_process:
                    last = sub_process[-1].get("process")
                    if last == "next":
                        output_json.append({"process": "open_message", "sleep": random.randint(1, 3)})
                        sub_process = [sp for sp in sub_process if sp.get("process") != "open_message"]
                    elif last not in ["delete", "archive", "not_spam", "report_spam"]:
                        for sp in sub_process:
                            if sp.get("process") == "open_message":
                                sp["process"] = "OPEN_MESSAGE_ONE_BY_ONE"
                element["sub_process"] = sub_process

            output_json.append(element)

        return output_json




    # -----------------------------
    # Génération complète de l'extension Chrome/Firefox
    # -----------------------------
    # Modifie les loops si un open_message a été trouvé avant
    # Supprime la clé 'check' si sub_process contient 'next'
    def Process_Modify_Json(self, input_json):
        output_json = []
        current_section = []
        found_open_message = False

        def finalize_section():
            if current_section:
                output_json.extend(current_section)

        for element in input_json:
            process_type = element.get("process")
            if process_type == "open_message":
                found_open_message = True

            if process_type == "loop":
                if found_open_message:
                    sub_process = element.get("sub_process", [])
                    if any(sp.get("process") == "next" for sp in sub_process):
                        element.pop("check", None)
                current_section.append(element)
                continue

            current_section.append(element)

        finalize_section()
        return output_json


    # Appelée une fois l'extraction des données terminée.
    # - Arrête proprement le thread de LOGS.
    # - Lance la mise à jour de la liste des résultats après un court délai.
    def Extraction_Finished(self, window):
        self.LOGS_THREAD.stop()  
        self.LOGS_THREAD.wait()  
        QTimer.singleShot(100, lambda: Read_Result_Update_List(window))





    # Fonction déclenchée lors du clic sur le bouton "Submit".
    # - Gère l'initialisation de l'extraction, la création du JSON de scénario,
    #     la vérification des champs, et le lancement de l'extraction dans un thread.
    
    def Submit_Button_Clicked(self, window):
        global CURRENT_HOUR, CURRENT_DATE, LOGS_RUNNING , NOTIFICATION_BADGES


        session_valid = False

        print(f"[INFO] Chemin du fichier session : {SESSION_PATH}")

       
        session_info = check_session(SESSION_PATH, KEY)
        session_valid = session_info["valid"]


        # Si la session est invalide, ouvrir la fenêtre de login
        if not session_valid:
            print("[SESSION] ❌ Session invalide => ouverture de la fenêtre LoginWindow...")

            self.login_window = LoginWindow()
            self.login_window.setFixedSize(1710, 1005)

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)

            self.login_window.show()

            print("[SESSION] 🔒 Fermeture de la fenêtre principale MainWindow...")
            self.close()

            # Nettoyage du fichier session
            try:
                with open(SESSION_PATH, "w", encoding="utf-8") as f:
                    f.write("")
                print("[SESSION] 🧼 Fichier session.txt nettoyé.")
            except Exception as e:
                print(f"[ERREUR NETTOYAGE SESSION] ❌ {e}")

            return




        # 🧹 Supprimer tous les badges de notification dans les onglets de résultats
        try:
            if self.result_tab_widget:
                for tab_index, badge in NOTIFICATION_BADGES.items():
                    if badge:
                        badge.deleteLater()
                NOTIFICATION_BADGES.clear()

                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        for lw in list_widgets:
                            lw.clear()  
        except Exception as e:
            print(f"[BADGES ERROR] Erreur lors de la suppression des badges : {e}")



        # For PROGRAMM COMPLETE UPDATE

        # new_versions = Check_Version()

        # if new_versions == "_1":
        #     Show_Critical_Message(
        #         window,
        #         "Connection Error",
        #         "We could not reach the server or retrieve the required version information.\n\n"
        #         "👉 Please check your internet connection and try again.\n"
        #         "If the problem continues, contact Support for further assistance.",
        #         message_type="critical"
        #     )
        #     return

        # if not new_versions:
        #     print("✅ Everything is up to date. No updates are required.")
        # else:
        #     # 🔄 Python or interface update
        #     if 'version_python' in new_versions or 'version_interface' in new_versions:
        #         Show_Critical_Message(
        #             window,
        #             "Update Required",
        #             "A new update is available for the application.\n\n"
        #             "The program will now restart to apply the latest changes.",
        #             message_type="info"
        #         )
        #         print("🔄 Python or interface update detected. Restarting the program...")
        #         window.close()
        #         launch_new_window()
        #         sys.exit(0)

        #     # 🌐 Extensions update
        #     elif 'version_extensions' in new_versions:
        #         print("⬇️ Downloading new Extensions update...")

        #         if Download_Extract(new_versions) == 0:
        #             Show_Critical_Message(
        #                 window,
        #                 "Update Completed",
        #                 "The browser extensions have been successfully updated.\n\n"
        #                 "You can now continue using the application.",
        #                 message_type="success"
        #             )
        #             print("✅ Extensions updated successfully")
        #         else:
        #             Show_Critical_Message(
        #                 window,
        #                 "Update Failed",
        #                 "We were unable to complete the update of one or more browser extensions.\n\n"
        #                 "Possible causes:\n"
        #                 " • Internet connection issues\n"
        #                 " • Server temporarily unavailable\n\n"
        #                 "👉 Please check your connection and try again.\n"
        #                 "If the problem persists, contact Support for assistance.",
        #                 message_type="critical"
        #             )
        #             print("❌ Failed to update one or more extensions")
        #             return





        selected_Browser = self.browser.currentText().lower()
        print('selected_Browser : ', selected_Browser)



        if not Process_Browser(window, selected_Browser):
            print(f"\n⛔ Échec du processus navigateur '{selected_Browser}'. Vérifie les logs ci-dessus.")
            return


        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                tab_text = self.INTERFACE.tabText(i)
                if tab_text.startswith("Result"):
                    self.INTERFACE.setTabText(i, "Result")
                    break
        
        LOGS_RUNNING =True

        output_json = [
            {
                "process": "login",  
                "sleep": 1  
            }
        ]

        if self.scenario_layout.count() == 0:
            Show_Critical_Message(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning"
            )

            return
        
        i = 0
        while i < self.scenario_layout.count():
            widget = self.scenario_layout.itemAt(i).widget()  
            if widget:
                
                full_state = widget.property("full_state")
                hidden_id = full_state.get("id") if full_state else None
                
                print(f"📋 full_state: {full_state}")  # Afficher le contenu de full_state
                print(f"📋 hidden_id: {hidden_id}")    # Afficher la valeur de hidden_id

                checkbox = next((child for child in widget.children() if isinstance(child, QCheckBox)), None)

                if full_state and not full_state.get("showOnInit", False) and not hidden_id.startswith("google") and  hidden_id.startswith("youtube"):
                    print(f"✅ Condition remplie ! Le code à l'intérieur du if sera exécuté ✅ hidden_id : {hidden_id}")
                    qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]

                    if len(qlineedits) > 1:
                        limit_text = qlineedits[0].text()
                        sleep_text = qlineedits[1].text()

                        try:
                            limit_value = Parse_Random_Range(limit_text)
                        except ValueError:
                            limit_value = 0

                        try:
                            sleep_value = Parse_Random_Range(sleep_text)
                        except ValueError:
                            sleep_value = 0

                        # 👇 Ajouter UN SEUL objet avec process, limit et sleep
                        if  hidden_id.startswith("youtube"):
                            output_json.append({
                                "process": "CheckLoginYoutube",
                                "sleep":  random.randint(1, 3)
                            })
                            output_json.append({
                                "process": hidden_id,
                                "limit": limit_value,
                                "sleep": sleep_value
                            })
                        else:
                            output_json.append({
                                "process": hidden_id,
                                "limit": limit_value,
                                "sleep": sleep_value
                            })

                    else:
                        # S'il n'y a qu'un seul QLineEdit → utilisé pour sleep seulement
                        sleep_text = qlineedits[0].text() if qlineedits else "0"
                        print("✅ QLineEdit utilisé comme sleep uniquement:", sleep_text)

                        try:
                            sleep_value = Parse_Random_Range(sleep_text)
                        except ValueError:
                            sleep_value = 0

                        output_json.append({
                            "process": hidden_id,
                            "sleep": sleep_value
                        })

                    i += 1
                    continue

                if full_state and full_state.get("showOnInit", False) and checkbox:
                    sub_process = []  
                    # spinbox = next((child.value() for child in widget.children() if isinstance(child, QSpinBox)), 0)
                    # openInbox
                    output_json.append({
                        "process": hidden_id,
                        "sleep": random.randint(1, 3)
                    })

                    if checkbox.isChecked():
                        search_value = next((child.text() for child in reversed(widget.children()) if isinstance(child, QLineEdit)), None)
                        
                        if output_json and output_json[-1]["process"] == "open_spam":
                            output_json.append({
                                "process": "search",
                                "value": f"in:spam {search_value}"
                            })
                        else:
                            output_json.append({
                                "process": "search",
                                "value": search_value
                            })



                    i += 1
                    while i < self.scenario_layout.count():
                        sub_widget = self.scenario_layout.itemAt(i).widget()
                        if not sub_widget:
                            break

                        sub_full_state = sub_widget.property("full_state")
                        sub_hidden_id = sub_full_state.get("id") if sub_full_state else None
                        # sub_spinbox = next((child.value() for child in sub_widget.children() if isinstance(child, QSpinBox)), 0)
                        wait_process_txt = next((child.text() for child in sub_widget.children() if isinstance(child, QLineEdit)), "0")
                        try:
                            wait_process = Parse_Random_Range(wait_process_txt)
                        except ValueError:
                            wait_process = 0
                        sub_checkbox = next((child for child in sub_widget.children() if isinstance(child, QCheckBox)), None)

                        combobox = next((child for child in widget.children() if isinstance(child, QComboBox)), None)
                        combo_value = combobox.currentText() if combobox else None

                        if sub_full_state and sub_full_state.get("showOnInit", False) or sub_hidden_id.startswith("google") or sub_hidden_id.startswith("youtube"):
                            break

                        if not sub_checkbox:
                            if sub_full_state.get("id") == "reply_message":
                                sub_process.append({
                                    "process": sub_hidden_id,
                                    "sleep": wait_process,
                                    "value":  next((child.toPlainText() for child in sub_widget.children() if isinstance(child, QTextEdit)), "0")
                                })
                                print(f"➡️  Sous-process ajouté avec message vide : {sub_hidden_id} ⏱️ sleep={wait_process}")
                            sub_process.append({
                                "process": sub_hidden_id,
                                "sleep": wait_process
                            })
                        else:
                            break

                        i += 1

                    if len(sub_process) > 0:
                        action = "return_back" if combo_value == "Return back" else "next"
                        sub_process.append({
                            "process": action
                        })
                    qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]

                    limit_loop_text = qlineedits[0].text() if len(qlineedits) > 1 else "0"
                    Start_loop_text =qlineedits[1].text() if len(qlineedits) > 1 else "0"

                    try:
                        limit_loop = Parse_Random_Range(limit_loop_text)
                        Start_loop =  Parse_Random_Range(Start_loop_text)
                    except ValueError:
                        limit_loop = 0

                    output_json.append({
                        "process": "loop",
                        "check": "is_empty_folder",
                        "limit_loop": limit_loop,
                        "start": Start_loop,
                        "sub_process": sub_process
                    })
                    continue

                if full_state and full_state.get("showOnInit", False) and not checkbox:
                    # spinbox = next((child.value() for child in widget.children() if isinstance(child, QSpinBox)), 0)
                    wait_process_txt = next((child.text() for child in widget.children() if isinstance(child, QLineEdit)), "0")
                    try:
                        wait_process = Parse_Random_Range(wait_process_txt)
                    except ValueError:
                        wait_process = 0

                    # 🔎 Affichage avec emojis
                    print("🐍 --- DEBUG INFO --- 🐍")
                    print(f"🆔 Process ID : {hidden_id}")
                    print(f"⌨️  Valeur récupérée (texte) : {wait_process_txt}")
                    print(f"⏱️  Valeur parsée (sleep) : {wait_process}")
                    print("✅ -------------------- ✅")

                    output_json.append({
                        "process": hidden_id,
                        "sleep": wait_process
                    })


                if full_state and not full_state.get("showOnInit", False) and (hidden_id.startswith("google") or hidden_id.startswith("youtube")):
                    print("🔍 ✅ Condition principale remplie (if)")
                    print(f"🔸 Identifiant caché (hidden_id) : {hidden_id}")
                    
                    print(f"📋 État de la case à cocher : {'trouvée' if checkbox else 'non trouvée'}")
                    
                    wait_process_txt = next((child.text() for child in widget.children() if isinstance(child, QLineEdit)), "0")
                    print(f"📥 Valeur du champ de délai (wait_process_txt) : {wait_process_txt}")
                    
                    try:
                        wait_process = Parse_Random_Range(wait_process_txt)
                        print(f"⏳ Délai après conversion (wait_process) : {wait_process}")
                    except ValueError:
                        wait_process = 0
                        print("⚠️ Erreur lors de la conversion du délai. Valeur par défaut utilisée : 0")
                    
                    if checkbox and checkbox.isChecked():
                        print("✅ La case à cocher est activée")

                        qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]
                        print(f"✏️ Nombre total de champs QLineEdit trouvés : {len(qlineedits)}")

                        for idx, line_edit in enumerate(qlineedits, start=1):
                            print(f"   ➤ Champ QLineEdit {idx} : \"{line_edit.text()}\"")

                        if len(qlineedits) > 1:
                            search_value = qlineedits[1].text()
                            print(f"🔎 Valeur de recherche utilisée (deuxième champ) : {search_value}")
                        elif len(qlineedits) == 1:
                            search_value = qlineedits[0].text()
                            print(f"🔎 Un seul champ trouvé, valeur de recherche utilisée : {search_value}")
                        else:
                            search_value = ""
                            print("⚠️ Aucun champ QLineEdit trouvé, valeur de recherche vide.")

                        output_json.append({
                            "process": hidden_id,
                            "search": search_value,
                            "sleep": wait_process
                        })
                        print("📤 Données ajoutées à output_json avec valeur de recherche.")
                    else:
                        output_json.append({
                            "process": hidden_id,
                            "sleep": wait_process
                        })
                        print("🚫 La case à cocher n’est pas activée. Aucune donnée ajoutée.")



            i += 1


        try:
            result = Generate_User_Input_Data(window)

            if not result:  
                return
            data_list, entered_number = result  

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error while parsing the JSON: {e}")
            return
    
        print("📦 JSON test:")

        print(json.dumps(output_json, indent=4, ensure_ascii=False))
        
        current_time = datetime.datetime.now()
        CURRENT_DATE = current_time.strftime("%Y-%m-%d")
        CURRENT_HOUR = current_time.strftime("%H-%M-%S") 
        modified_json = self.Process_Split_Json(output_json)
        print(f"📦 JSON Modifié après Process_Split_Json:{json.dumps(modified_json, indent=4, ensure_ascii=False)}")
        output_json = self.Process_Handle_Last_Element(modified_json)
        print(f"📦 JSON Modifié après Process_Handle_Last_Element:{json.dumps(output_json, indent=4, ensure_ascii=False)}")
        output_json_final=self.Process_Modify_Json(output_json)
        print(f"📦 JSON Final après Process_Modify_Json:{json.dumps(output_json_final, indent=4, ensure_ascii=False)}")
        result_json = self.Save_Json_To_File(output_json_final, selected_Browser)

        if result_json == "ERROR":
            Show_Critical_Message(
                window,
                "Error - Save Configuration",
                "An error occurred while saving the configuration file.\n\n"
                "If the problem persists, contact Support.",
                message_type="critical"
            )
            return
        print("📦 JSON Final:")
        print(json.dumps(output_json_final, indent=4, ensure_ascii=False))

 
        try:
            with open( FILE_ISP, 'w', encoding='utf-8') as f:
                f.write(self.Isp.currentText().strip())
            print(f"📄 Fichier Isp.txt mis à jour avec : '{self.Isp.currentText().strip()}'")
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture dans Isp.txt : {e}")



        json_string = json.dumps(output_json_final)
        print("✈️​✈️​✈️​✈️​✈️​✈️​ : ",json_string)

        parameters = { 
            'p_owner':session_info["username"],
            'p_entity':session_info["p_entity"],
            'p_isp': self.Isp.currentText(),
            'p_action_name': json.dumps(output_json_final), 
            'p_app':'V4',
            'p_python_version': f"{sys.version_info.major}.{sys.version_info.minor}", 
            'p_browser': self.browser.currentText(),
        }

        unique_id=self.Save_Process(parameters)

        if unique_id==-1:
            print("Error getting process ID ")
            os.system("pause")
            exit()
            return


        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(Start_Extraction, window, data_list , entered_number, selected_Browser, self.Isp.currentText() , unique_id , output_json_final, session_info["username"])
            executor.submit(self.LOGS_THREAD.start)
        EXTRACTION_THREAD.finished.connect(lambda: self.Extraction_Finished(window))



    # Charge les options visibles dès le démarrage de l'application.
    # - Supprime les anciens widgets.
    # - Crée un bouton pour chaque option avec `showOnInit = True`.
    def Load_Initial_Options(self):
        # Clear existing widgets from the layout
        while self.reset_options_layout.count() > 0:
            item = self.reset_options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add option buttons for states with showOnInit=True
        for key, state in self.states.items():
            if state.get("showOnInit", False):
                # print(f"Displayed option for: {key}")
                # print(f"state: {state}") 
                self.Create_Option_Button(state)
                # print(f"Displayed option for: {key}") 
        # print("🫁​🫁​🫁​🫀​🫀​🫀​🫀​ self.STATE_STACK : ",  self.STATE_STACK)



    #Crée dynamiquement un bouton d'option basé sur un état donné.
    #Ce bouton est ajouté à un conteneur prédéfini, reprend le style d'un bouton modèle,
    #et est relié à la fonction `Load_State`.
    #:param state: Dictionnaire contenant les informations de l'état à charger.
    def Create_Option_Button(self, state):
        default_icon_path = os.path.join(DEFAULT_ICON_PATH, "icon.png")
        default_icon_path_Templete2 = os.path.join(DEFAULT_ICON_PATH, "next.png")

        # Create and configure the button
        # button = QPushButton(state.get("label", "Unnamed"), self.reset_options_container)
        # button.setStyleSheet(self.template_button.styleSheet())
        # button.setFixedSize(self.template_button.size())
        # button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # # Connect button to state loader
        # button.clicked.connect(lambda _, s=state: self.Load_State(s))

        # # Set icon if it exists
        # if os.path.exists(default_icon_path):
        #     button.setIcon(QIcon(default_icon_path))
        # else:
        #     print(f"[Warning] Icon not found at: {default_icon_path}")

        # # Add button to layout
        # self.reset_options_layout.addWidget(button)

        # Detailed display output
        # print(f"[Info] Option button created:")
        # print(f"       Label     : {state.get('label', 'N/A')}")
        # print(f"       State id : {state.get('id', 'N/A')}")
        # print(f"       ShowOnInit: {state.get('showOnInit', False)}")
        # print(f"       Icon Path : {'Found' if os.path.exists(default_icon_path) else 'Missing'}")
        # Vérifie si c'est un bouton multi-sélection
        is_multi = state.get("isMultiSelect", False)

        # Choisir le modèle et l’icône selon l’état
        if is_multi:
            template_button = self.Temeplete_Button_2
            icon_path = default_icon_path_Templete2
        else:
            template_button = self.template_button
            icon_path = default_icon_path

        # Créer le bouton
        button = QPushButton(state.get("label", "Unnamed"), self.reset_options_container)
        button.setStyleSheet(template_button.styleSheet())
        button.setFixedSize(template_button.size())

        # Définir la forme du curseur seulement si isMultiSelect = True
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # Placer l’icône à gauche
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Relier le bouton à l’état
        button.clicked.connect(lambda _, s=state: self.Load_State(s))

        # Définir l’icône si elle existe
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            print(f"[Warning] Icon not found at: {icon_path}")

        # Ajouter le bouton à l’interface
        self.reset_options_layout.addWidget(button)

        # Detailed display output
        # print(f"[Info] Option button created:")
        # print(f"       Label     : {state.get('label', 'N/A')}")
        # print(f"       State id : {state.get('id', 'N/A')}")
        # print(f"       ShowOnInit: {state.get('showOnInit', False)}")
        # print(f"       Icon Path : {'Found' if os.path.exists(default_icon_path) else 'Missing'}")
        # Vérifie si c'est un bouton multi-sélection




    def Display_State_Stack_As_Table(self):
        if not self.STATE_STACK:
            print("📭 La pile d'états est vide.\n")
            return

        print("\n📦 Pile des états (🧱 du plus ancien au plus récent) :\n")
        for i, state in enumerate(self.STATE_STACK):
            print(f"🧱 État {i+1:02d} :")
            print(json.dumps(state, indent=4, ensure_ascii=False))  # JSON واضح ومنسق
            print("-" * 50)




    #Charge un nouvel état de scénario. Met à jour l'interface avec les nouvelles actions,
    #le template associé, et remet les éléments spécifiques à zéro (copieur, INITAILE...).
    #:param state: Dictionnaire représentant l'état à charger.
    def Load_State(self, state):

        print("\n📥 ===== Début du chargement d’un nouvel état =====")
        print(f"🔹 État reçu : {state}")

        # 🧾 Affichage de la pile avant mise à jour
        print("\n🪜 Pile d'états AVANT mise à jour :")
        self.Display_State_Stack_As_Table()
        is_multi = state.get("isMultiSelect", False)

        if not is_multi:
        # Ajout de l’état à la pile
            self.STATE_STACK.append(state)

        print(f"Pile d’états mise à jour (taille : {len(self.STATE_STACK)}).")

        # print("➡️​➡️​➡️​➡️​➡️​➡️​ Contenu actuel de state_stack :")
        self.Display_State_Stack_As_Table()

        # Mise à jour du scénario
        # template = state.get("Template", "")
        # print(f"Chargement du scénario avec le template : '{template}'")
        # self.Update_Scenario(template, state)

        if not is_multi:
            template = state.get("Template", "")
            self.Update_Scenario(template, state)


        # Mise à jour des options de réinitialisation
        actions = state.get("actions", [])
        print(f"Actions à charger : {actions}")
        self.Update_Reset_Options(actions)

        # Mise à jour des couleurs et gestion du dernier bouton
        print("Mise à jour des couleurs et du dernier bouton...")
        self.Update_Actions_Color_Handle_Last_Button()

        # Suppression des éléments inutiles
        print("Suppression des éléments : copier et INITAILE")
        self.Remove_Copier()
        self.Remove_Initaile()

        # 🧾 Affichage de la pile après mise à jour
        print("\n📦 Pile d'états APRÈS mise à jour :")
        self.Display_State_Stack_As_Table()

        print("✅ ===== Fin du chargement de l’état =====\n")






    def Inject_Border_Into_Style(self, old_style: str, border_line: str = "border: 2px solid #cc4c4c;") -> str:
        print("\n[🔍] Style avant injection :\n", old_style)
        pattern = r"(QLineEdit\s*{[^}]*?)\s*}" 
        match = re.search(pattern, old_style, re.DOTALL)

        if match:
            before_close = match.group(1)
            if "border" not in before_close:
                new_block = before_close + f"\n    {border_line}\n}}"
                result = re.sub(pattern, new_block, old_style, flags=re.DOTALL)
                print("[✅] Nouveau style après injection dans QLineEdit:\n", result)
                return result
            else:
                print("[⚠️] 'border' déjà présent, aucun changement.")
                return old_style
        else:
            appended = old_style + f"""
            QLineEdit {{
                {border_line}
            }}"""
            print("[➕] Bloc QLineEdit ajouté car manquant:\n", appended)
            return appended





    def Remove_Border_From_Style(self, style: str) -> str:
        cleaned_style = re.sub(r'border\s*:\s*[^;]+;', '', style, flags=re.IGNORECASE)
        return cleaned_style.strip()






    def Validate_Qlineedit(self, qlineedit: QLineEdit, default_value="50,50"):
        text = qlineedit.text().strip()
        pattern = r"^\s*(\d+)(?:\s*,\s*(\d+))?\s*$"
        match = re.match(pattern, text)

        if match:
            min_val = int(match.group(1))
            max_val = int(match.group(2)) if match.group(2) else min_val

            if min_val > max_val:
                qlineedit.setText(f"{min_val},{min_val}")
                old_style = qlineedit.styleSheet()
                def apply_style():
                    new_style = self.Inject_Border_Into_Style(old_style)
                    qlineedit.setStyleSheet(new_style)
                    qlineedit.setToolTip("La valeur Min est supérieure à Max. Correction appliquée.")
                QTimer.singleShot(0, apply_style)
            else:
                old_style = qlineedit.styleSheet()
                cleaned = self.Remove_Border_From_Style(old_style)
                qlineedit.setStyleSheet(cleaned)
                qlineedit.setToolTip("")
        else:
            qlineedit.setText(default_value)
            old_style = qlineedit.styleSheet()
            def apply_error():
                new_style = self.Inject_Border_Into_Style(old_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip("Veuillez entrer une valeur sous la forme 'Min,Max' ou un seul nombre.")
            QTimer.singleShot(0, apply_error)






    # Met à jour dynamiquement le style de tous les widgets enfants dans le layout du scénario.
    # Différencie le dernier bloc des autres :
    # - Applique des styles personnalisés pour les QLabels, QSpinBox, QCheckBox, et QComboBox.
    # - Cache le dernier bouton dans chaque bloc sauf le dernier, où il devient visible et fonctionnel.
    # - Applique des styles conditionnels selon les icônes disponibles.
    def Update_Actions_Color_Handle_Last_Button(self):
        for i in range(self.scenario_layout.count()):
            widget = self.scenario_layout.itemAt(i).widget()

            if widget:
                if i != self.scenario_layout.count() - 1:
                    widget.setStyleSheet("background-color: #ffffff; border: 1px solid #b2cddd; border-radius: 8px;")
                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        first_label = label_list[0]

                        # 🖌️ Appliquer style par défaut à la première QLabel
                        first_label.setStyleSheet("""
                            QLabel {
                                color: #669bbc;
                                font-size: 16px;
                                border: none;
                                border-radius: 4px;
                                text-align: center;
                                background-color: transparent;
                                font-family: "Times", "Times New Roman", serif;
                                margin-left: 10px;
                            }
                        """)

                        # 🎯 Si elle commence par "Random", remplacer le style
                        if first_label.text().startswith("Random"):
                            first_label.setStyleSheet("""
                                QLabel {
                                    color: #669bbc;
                                    font-size: 9px;
                                    border: none;
                                    border-radius: 4px;
                                    background-color: transparent;
                                    font-family: "Monaco", monospace;
                                    padding: 0px;
                                    margin: 0px;
                                    border:None;
                                }
                            """)
                            print(f"[🎯] Style appliqué sur QLabel (index 0): '{first_label.text()}'")

                        # 🎨 Appliquer style aux autres QLabels
                        for label in label_list[1:]:
                            label.setStyleSheet("""
                                QLabel {
                                    color: #669bbc;
                                    font-size: 14px;
                                    border: none;
                                    border-radius: 4px;
                                    text-align: center;
                                    background-color: transparent;
                                    font-family: "Times", "Times New Roman", serif;
                                }
                            """)

                            # 🎯 S'il commence par "Random", on remplace
                            if label.text().startswith("Random"):
                                label.setStyleSheet("""
                                    QLabel {
                                        color: #669bbc;
                                        font-size: 9px;
                                        border: none;
                                        border-radius: 4px;
                                        background-color: transparent;
                                        font-family: "Monaco", monospace;
                                        padding: 0px;
                                        margin: 0px;
                                        border:None;
                                    }
                                """)
                                print(f"[🎯] Style appliqué sur QLabel: '{label.text()}'")


                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[-1]
                        last_button.setVisible(False)  


                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and DOWN_EXISTS and UP_EXISTS:
                        new_style = f"""
                            QSpinBox {{
                                padding: 2px; 
                                border: 1px solid #669bbc; 
                                color: black;
                            }}
                            QSpinBox::down-button {{
                                image: url("{ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;  
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                            QSpinBox::up-button {{
                                image: url("{ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                        """
                        spin_boxes[0].setStyleSheet(new_style)  



                    QCheckBox_list = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list:  
                        checkbox = QCheckBox_list[0]                
                        if checkbox.isChecked():
                            additional_style = """
                                QCheckBox::indicator:checked  {
                                    background-color: #669bbc;
                                    border: 2px solid #669bbc;
                                }
                            """
                        else:
                            additional_style = """
                                QCheckBox::indicator {
                                    color: gray;
                                    background-color: #e0e0e0; 
                                    border: 1px solid #cccccc;
                                }
                            """

                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)

                    QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]

                    if QComboBox_list:
                        QComboBox = QComboBox_list[0]
                        if DOWN_EXISTS:
                            old_style = QComboBox.styleSheet()
                            new_style = f"""
                                QComboBox::down-arrow {{
                                    image: url("{ARROW_DOWN_PATH}");
                                    width: 13px;
                                    height: 13px;
                                    border: 1px solid #669bbc; 
                                    background-color: white;
                                }}
                                QComboBox::drop-down {{
                                    border: 1px solid #669bbc; 
                                    width: 20px;
                                    outline: none;
                                }}
                                
                                QComboBox QAbstractItemView {{
                                    min-width: 90px; 
                                    border: 1px solid #669bbc; 
                                    background: white;
                                    selection-background-color: #669bbc;
                                    selection-color: white;
                                    padding: 3px; 
                                    margin: 0px;  
                                    alignment: center; 
                                }}
                                QComboBox {{
                                    padding-left: 10px; 
                                    font-size: 12px;
                                    font-family: "Times", "Times New Roman", serif;
                                    border: 1px solid #669bbc; 
                                }}
                                QComboBox QAbstractItemView::item {{
                                    padding: 5px; 
                                    font-size: 12px;
                                    color: #333;
                                    border: none; 
                                }}
                                QComboBox QAbstractItemView::item:selected {{
                                    background-color: #669bbc;
                                    color: white;
                                    border-radius: 3px;
                                }}
                                QComboBox:focus {{
                                    border: 1px solid #669bbc; 
                                }}
                            """
                            combined_style = old_style + new_style
                            QComboBox.setStyleSheet(combined_style)

                if i == self.scenario_layout.count() - 1:
                    widget.setStyleSheet("background-color: #669bbc; border-radius: 8px;")

                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]

                    if label_list:
                        # 🎯 Première QLabel (souvent le titre)
                        label_list[0].setStyleSheet("""
                            QLabel {
                                color: white;
                                font-size: 16px;
                                border: none;
                                border-radius: 4px;
                                text-align: center;
                                background-color: #669bbc;
                                font-family: "Times", "Times New Roman", serif;
                                margin-left: 8px;
                            }
                        """)

                        # ➕ Vérifier si c’est un "Random"
                        if label_list[0].text().startswith("Random"):
                            label_list[0].setStyleSheet("""
                                QLabel {
                                    color: white;
                                    font-size: 9px;
                                    border: 1px dashed #ffffff;
                                    border-radius: 4px;
                                    background-color: transparent;
                                    font-family: "Monaco", monospace;
                                    padding: 0px;
                                    margin: 0px;
                                    border:None;
                                }
                            """)
                            print(f"[🎯] Dernier widget - QLabel (0) spéciale: '{label_list[0].text()}'")

                        # 🎨 Toutes les autres QLabels
                        for label in label_list[1:]:
                            label.setStyleSheet("""
                                QLabel {
                                    color: white;
                                    font-size: 16px;
                                    border: none;
                                    border-radius: 4px;
                                    text-align: center;
                                    background-color: #669bbc;
                                    font-family: "Times", "Times New Roman", serif;
                                }
                            """)

                            # 🎯 Appliquer style spécial si commence par "Random"
                            if label.text().startswith("Random"):
                                label.setStyleSheet("""
                                    QLabel {
                                        color: white;
                                        font-size: 9px;
                                        border: 1px dashed #ffffff;
                                        border-radius: 4px;
                                        background-color: transparent;
                                        font-family: "Monaco", monospace;
                                        padding: 0px;
                                        margin: 0px;
                                        border:None;
                                    }
                                """)
                                print(f"[🎯] Dernier widget - QLabel Random: '{label.text()}'")



                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[0]
                        last_button.setVisible(True)
                        last_button.setCursor(Qt.CursorShape.PointingHandCursor)

                        try:
                            last_button.clicked.disconnect()
                        except TypeError:
                            pass  
                        last_button.clicked.connect(self.Go_To_Previous_State)
            
                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and DOWN_EXISTS_W and UP_EXISTS_W:
                        new_style = f"""
                            QSpinBox {{
                                padding: 2px; 
                                border: 1px solid white; 
                                color: white;
                            }}
                            QSpinBox::down-button {{
                                image: url("{ARROW_DOWN_W_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;  
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                            QSpinBox::up-button {{
                                image: url("{ARROW_UP_W_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                        """
                        spin_boxes[0].setStyleSheet(new_style)  



                    QCheckBox_list_last = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list_last:  
                        checkbox = QCheckBox_list_last[0]
                        
                        if checkbox.isChecked():
                            additional_style = """
                                QCheckBox::indicator:checked  {
                                    background-color: #669bbc;
                                    border: 2px solid #ffffff;
                                }
                            """
                        else:
                            additional_style = """
                                QCheckBox::indicator {
                                    color: gray;
                                    background-color: #e0e0e0; 
                                    border: 1px solid #cccccc;
                                }
                            """


                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)


                QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]
                if QComboBox_list:
                    QComboBox = QComboBox_list[0]

                    if DOWN_EXISTS:
                        old_style = QComboBox.styleSheet()
                        new_style = f"""
                            QComboBox::down-arrow {{
                                image: url("{ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                border: none;
                                background-color: white;
                            }}
                            QComboBox::drop-down {{
                                border: none;
                                width: 20px;
                                outline: none;
                            }}
                            
                            QComboBox QAbstractItemView {{
                                min-width: 90px; 
                                border: none; 
                                background: white;
                                selection-background-color: #669bbc;
                                selection-color: white;
                                padding: 3px; 
                                margin: 0px;  
                                alignment: center; 
                            }}
                            QComboBox {{
                                padding-left: 10px; 
                                font-size: 12px;
                                font-family: "Times", "Times New Roman", serif;
                                border: 1px solid #669bbc; 
                                outline: none; 
                            }}
                            QComboBox QAbstractItemView::item {{
                                padding: 5px; 
                                font-size: 12px;
                                color: #333;
                                border: none; 
                            }}
                            QComboBox QAbstractItemView::item:selected {{
                                background-color: #669bbc;
                                color: white;
                                border-radius: 3px;
                            }}
                            QComboBox:focus {{
                                border: 1px solid #669bbc; 
                            }}
                        """
                        combined_style = old_style + new_style
                        QComboBox.setStyleSheet(combined_style)

            




                # Récupérer tous les QTextEdit dans le widget
                QTextEdits = [child for child in widget.children() if isinstance(child, QTextEdit)]
                print(f"[🔍] Nombre de QTextEdit détectés : {len(QTextEdits)}")

                for idx, qtextedit in enumerate(QTextEdits):
                    print(f"[➡️] Préparation du QTextEdit numéro {idx}")

                    # ✅ إخفاء الـ scrollbars
                    qtextedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    qtextedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


                    def create_handler(te, index):
                        def handler(event):
                            print(f"[🖱️] Clic détecté sur le QTextEdit numéro {index}")
                            try:
                                dialog = CustomTextDialog(te, texte_initial=te.toPlainText())
                                if dialog.exec():  # Si l’utilisateur clique sur "Enregistrer"
                                    new_text = dialog.get_text()
                                    te.setPlainText(new_text)
                                    print(f"[✅] Nouveau texte saisi pour QTextEdit {index} :\n{new_text}")
                                else:
                                    print(f"[⚠️] Modification annulée (QTextEdit {index})")
                                # ✅ دايمًا ننحي الفوكس سواء سجل أو لغى
                                te.clearFocus()
                            except Exception as e:
                                print(f"[❌] Erreur lors de l’ouverture de la boîte de dialogue : {e}")
                        return handler

                    qtextedit.mousePressEvent = create_handler(qtextedit, idx)
                    print(f"[🔗] Gestionnaire de clic associé au QTextEdit numéro {idx}")




                                                    


                qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]
                checkbox_qlineedit = None  # ⚠️ تخزين QLineEdit المرتبط بـ QCheckBox

                print("[🔍] Total QLineEdits détectés:", len(qlineedits))

                # إذا كان آخر QLineEdit داخل widget يحتوي على QCheckBox، نحذفه من القائمة
                if qlineedits:
                    last_qlineedit = qlineedits[-1]
                    parent_widget = last_qlineedit.parent()
                    if parent_widget:
                        contains_checkbox = any(isinstance(child, QCheckBox) for child in parent_widget.children())
                        print(f"[🧩] Dernier QLineEdit détecté. Contient QCheckBox ? {contains_checkbox}")
                        if contains_checkbox:
                            checkbox_qlineedit = last_qlineedit  # ✅ نحفظه ولكن لا نحذفه
                            qlineedits.pop()  # حذف العنصر الأخير
                            print("[📦] QLineEdit avec QCheckBox stocké séparément.")

                # ربط المحققين للـ QLineEdits العادية
                for idx, qlineedit in enumerate(qlineedits):
                    def create_validator(line_edit, default_val):
                        def validator():
                            print(f"[📝] Validation déclenchée pour QLineEdit[{idx}] avec valeur par défaut: {default_val}")
                            self.Validate_Qlineedit(line_edit, default_val)
                        return validator

                    if len(qlineedits) > 1 and idx == 0:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "50,50"))
                    else:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "1,1"))

                # ربط المحقق الخاص بـ QLineEdit مع QCheckBox
                if checkbox_qlineedit:
                    print("[🔗] Connexion du QLineEdit contenant QCheckBox à une validation personnalisée.")
                    def validate_checkbox_qlineedit():
                        print("[✅] Validation personnalisée déclenchée pour QLineEdit avec QCheckBox.")
                        self.Validate_Checkbox_Linked_Qlineedit(checkbox_qlineedit)

                    checkbox_qlineedit.editingFinished.connect(validate_checkbox_qlineedit)
                else:
                    print("[⚠️] Aucun QLineEdit avec QCheckBox détecté.")






    def Validate_Checkbox_Linked_Qlineedit(self, qlineedit: QLineEdit):
        if qlineedit is None:
            print("[❌ ERREUR] Le QLineEdit est None. Validation ignorée.")
            return

        parent_widget = qlineedit.parent()
        full_state = parent_widget.property("full_state") if parent_widget else None

        text = qlineedit.text().strip()
        print(f"[🔍 INFO] Texte saisi dans QLineEdit associé à QCheckBox : '{text}'")

        old_style = qlineedit.styleSheet()
        cleaned_style = self.Remove_Border_From_Style(old_style)

        # ✅ Vérification conditionnelle selon full_state
        if full_state and isinstance(full_state, dict):
            sub_id = full_state.get("id", "")
            sub_label = full_state.get("label", "Google")

            # Chercher le QCheckBox associé dans le même parent
            checkbox = next((child for child in parent_widget.children() if isinstance(child, QCheckBox)), None)

            if sub_id in ["open_spam", "open_inbox"]:
                if checkbox and checkbox.isChecked():
                    if text :
                        print("[✅ CONDITION VALIDE] Checkbox cochée et texte valide.")
                        def apply_ok():
                            qlineedit.setStyleSheet(cleaned_style)
                            qlineedit.setToolTip("")
                            print("[🔔 INFO] Bordure retirée et tooltip supprimé.")
                        QTimer.singleShot(0, apply_ok)
                        return
                    else:
                        print("[⚠️ TEXTE INVALIDE] Champ vide ou numérique malgré checkbox cochée.")
                        qlineedit.setText(sub_label or "Google")

                        def apply_error():
                            new_style = self.Inject_Border_Into_Style(cleaned_style)
                            qlineedit.setStyleSheet(new_style)
                            qlineedit.setToolTip("Texte invalide. Valeur remplacée par défaut depuis full_state.")
                            print("[🔔 INFO] Erreur appliquée avec bordure rouge.")
                        QTimer.singleShot(0, apply_error)
                        return

        # 🧾 Sinon: validation classique (ancienne logique)
        if text.isdigit() or len(text) < 4:
            print("[⚠️ INVALIDE] Le texte est un nombre ou trop court (<4).")
            qlineedit.setText("Google")

            def apply_error():
                new_style = self.Inject_Border_Into_Style(cleaned_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip("Le texte est un nombre ou trop court, veuillez corriger la saisie.")
                print("[🔔 INFO] Bordure rouge appliquée et tooltip invitant à corriger la saisie.")
            QTimer.singleShot(0, apply_error)
        else:
            print("[✅ VALIDE] Texte non numérique et au moins 4 caractères.")

            def apply_ok():
                qlineedit.setStyleSheet(cleaned_style)
                qlineedit.setToolTip("")
                print("[🔔 INFO] Bordure retirée et tooltip supprimé.")
            QTimer.singleShot(0, apply_ok)





    # Supprime tous les boutons de réinitialisation liés aux blocs ajoutés *après* le dernier bloc contenant une checkbox.
    # Cette fonction :
    # - Identifie l'index du dernier bloc contenant une QCheckBox.
    # - Récupère les labels des blocs ajoutés après celui-ci.
    # - Compare avec les boutons existants dans le layout des options de reset.
    # - Supprime ceux qui sont déjà couverts par les labels détectés.

    def Remove_Copier(self):
        lastactionLoop = None
        scenarioContainertableauAdd = []
        resetOptionsContainertableauALL = []
        found_checkbox = False

        for i in range(self.scenario_layout.count()):
            widget = self.scenario_layout.itemAt(i).widget()
            if widget:
                for child in widget.children():
                    if isinstance(child, QCheckBox):
                        lastactionLoop = i 
                        found_checkbox = True
        
        if not found_checkbox:
            return


        for i in range(lastactionLoop + 1, self.scenario_layout.count()):
            widget = self.scenario_layout.itemAt(i).widget()
            if widget:
                labels = [child.text() for child in widget.children() if isinstance(child, QLabel)]
                if labels:
                    scenarioContainertableauAdd.append(labels[0])

        for i in range(self.reset_options_layout.count()):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())

        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        for i in reversed(range(self.reset_options_layout.count())):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    self.reset_options_layout.removeWidget(widget)



    # Supprime les boutons de réinitialisation associés aux blocs ayant l’attribut `INITAILE`.
    # Cette fonction :
    # - Récupère tous les labels associés à un bloc contenant l'attribut `INITAILE`.
    # - Supprime de l'UI les boutons de réinitialisation qui ne sont pas dans cette liste.

    def Remove_Initaile(self):

        scenarioContainertableauAdd = []  
        resetOptionsContainertableauALL = []  

        for i in range(self.scenario_layout.count()):
            widget = self.scenario_layout.itemAt(i).widget()
            if widget:
                sub_full_state = widget.property("full_state")
                sub_hidden_id = sub_full_state.get("INITAILE")
                if sub_hidden_id:
                    scenarioContainertableauAdd.append(sub_full_state.get("label"))  



        for i in range(self.reset_options_layout.count()):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())


        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        for i in reversed(range(self.reset_options_layout.count())):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    self.reset_options_layout.removeWidget(widget)



    # Met à jour dynamiquement les boutons d'options de réinitialisation à partir d’une liste d’actions.
    # :param actions: Liste des clés d'action à afficher comme options. Si vide, recharge les options initiales.

    def Update_Reset_Options(self, actions):
        print("\n===== Mise à jour des options de réinitialisation =====")

        count = self.reset_options_layout.count()
        print(f"Suppression des {count} widgets existants dans reset_options_layout.")
        for i in reversed(range(count)):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget:
                print(f"Suppression du widget à l'indice {i}.")
                widget.deleteLater()

        if not actions:
            print("Aucune action trouvée. Chargement des options initiales.")
            self.Load_Initial_Options()
            print("Options initiales chargées.")
            return

        # print(f"Création des boutons pour {len(actions)} actions:")
        for action_key in actions:
            state = self.states.get(action_key)
            if state:
                label = state.get('label', action_key)
                print(f"🔘 {label}")
                self.Create_Option_Button(state)
            else:
                print(f"⚠️ Aucune définition trouvée pour l'action : '{action_key}'.")

        print("===== Mise à jour terminée =====\n")





    # Affiche ou cache un champ QLineEdit en fonction de l'état d'une checkbox.
    # :param state: État de la QCheckBox (0: décochée, 2: cochée)
    # :param lineedit: Référence au champ QLineEdit à afficher/cacher

    def Handle_Checkbox_State(self, state, lineedit):
        if lineedit:  
            if state == 2: 
                lineedit.show()
            else:  

                lineedit.hide()



    # Génère un nouveau bloc de scénario basé sur un template existant et le remplit avec les données d'état.
    # :param template_name: Nom du template ("Template1" ou "Template2")
    # :param state: Dictionnaire contenant les valeurs à insérer dans le bloc

    def Update_Scenario(self, template_name, state):
        template_frame = None

        if template_name == "Template1":
            template_frame = self.template_Frame1
        elif template_name == "Template2":
            template_frame = self.template_Frame2
        elif template_name == "Template3":
            template_frame = self.template_Frame3
        elif template_name == "Template4":
            template_frame = self.template_Frame4
        elif template_name == "Template5":
            template_frame = self.template_Frame5
        else:
            return

        if template_frame:
            new_template = QFrame()
            new_template.setStyleSheet(template_frame.styleSheet())
            new_template.setMaximumHeight(51)
            new_template.setMinimumHeight(51)
            new_template.setMaximumWidth(780)  # ← Ajout ici (ajuste selon ton besoin)

            lineedits = []
            checkboxes = []
            first_label_updated = False

            for child in template_frame.children():
                # print(f"[👁️] Found: {type(child).__name__} | Text: {getattr(child, 'text', lambda: '')()}")

                if isinstance(child, QLabel):
                    new_label = QLabel(new_template)
                    if not first_label_updated:
                        new_label.setText(state.get("label", ""))
                        first_label_updated = True
                    else:
                        new_label.setText(child.text())
                    new_label.setStyleSheet(child.styleSheet())
                    new_label.setGeometry(child.geometry())
                elif isinstance(child, QPushButton):
                    new_button = QPushButton(child.text(), new_template)
                    new_button.setStyleSheet(child.styleSheet())
                    new_button.setGeometry(child.geometry())
                    new_button.clicked.connect(child.clicked)
                elif isinstance(child, QSpinBox):
                    new_spinbox = QSpinBox(new_template)
                    new_spinbox.setValue(child.value())
                    new_spinbox.setGeometry(child.geometry())
                    new_spinbox.setStyleSheet(child.styleSheet())
                elif isinstance(child, QLineEdit):
                    # print(f"[📝] Copied QLineEdit → Value: {child.text()}")
                    new_lineedit = QLineEdit(new_template)
                    new_lineedit.setText(child.text())
                    new_lineedit.setGeometry(child.geometry())
                    new_lineedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_lineedit)
                elif isinstance(child, QTextEdit):
                    new_textedit = QTextEdit(new_template)
                    new_textedit.setPlainText(child.toPlainText())
                    new_textedit.setGeometry(child.geometry())
                    new_textedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_textedit)
                elif isinstance(child, QCheckBox):
                    new_checkbox = QCheckBox(child.text(), new_template)
                    new_checkbox.setChecked(child.isChecked())
                    new_checkbox.setGeometry(child.geometry())
                    new_checkbox.setStyleSheet(child.styleSheet())
                    checkboxes.append(new_checkbox)
                elif isinstance(child, QComboBox):
                    new_combobox = QComboBox(new_template)
                    new_combobox.setCurrentIndex(child.currentIndex())
                    new_combobox.addItems([child.itemText(i) for i in range(child.count())])
                    new_combobox.setGeometry(child.geometry())
                    new_combobox.setStyleSheet(child.styleSheet())

            for checkbox in checkboxes:
                if lineedits:
                    linked_lineedit = lineedits[-1]
                    linked_lineedit.hide()
                    checkbox.stateChanged.connect(
                        lambda state, lineedit=linked_lineedit: self.Handle_Checkbox_State(state, lineedit)
                    )


            new_template.setProperty("full_state", state)

            self.scenario_layout.addWidget(new_template)


    # Revient à l'état précédent du scénario :
    # - Supprime le dernier bloc visuel du scénario.
    # - Restaure les actions de l'état précédent.
    # - Si aucun historique n’est disponible, réinitialise complètement.
    # - Met à jour le style et nettoie les boutons redondants.

    def Go_To_Previous_State(self):
        # print("\n===== Retour à l'état précédent =====")
        # print("\n 🫁🫁🫁🫁🫁🫁​​ ===== Contenu de json_data fourni à MainWindow avant  =====")
        self.Display_State_Stack_As_Table()
        print("=====================================================\n")
        if len(self.STATE_STACK) > 1:
            # print(f"Plus d’un état dans la pile ({len(self.STATE_STACK)}). Suppression de l’état actuel...")

            if self.scenario_layout.count() > 0:
                # print("Suppression du dernier widget du scénario affiché.")
                last_item = self.scenario_layout.takeAt(self.scenario_layout.count() - 1)
                if last_item.widget():
                    last_item.widget().deleteLater()
            
            self.STATE_STACK.pop()
            previous_state = self.STATE_STACK[-1]
            # print(f"État précédent restauré : {previous_state.get('label', 'Sans nom')}")

            self.Update_Reset_Options(previous_state.get("actions", []))
        else:
            # print("Un seul état ou aucun. Réinitialisation complète de l’interface.")
            self.STATE_STACK.clear()

            while self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(0)
                if last_item.widget():
                    last_item.widget().deleteLater()

            self.Load_Initial_Options()
            # print("Options initiales rechargées.")

        self.Update_Actions_Color_Handle_Last_Button()
        # print("Couleurs et état du dernier bouton mis à jour.")

        self.Remove_Copier()
        # print("Élément 'copier' supprimé s’il existe.")
        # print("\n 🎁​🎁​🎁​🎁​🎁​​ ===== Contenu de json_data fourni à MainWindow apres =====")
        # self.Display_State_Stack_As_Table()
        # print("=====================================================\n")
        # print("===== Retour terminé =====\n")
        print("\n🪜 Go_To_Previous_State mise à jour apres Go_To_Previous_State:")
        self.Display_State_Stack_As_Table()




    # Nettoie entièrement les LOGS affichés à l'écran et vide la variable globale `LOGS`.

    def Clear_Button_Clicked(self):
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        global LOGS
        LOGS = []





    def Scenario_Changed(self, name_selected):
        print("Scenario_Changed called with name_selected=%r", name_selected)

        # 1) تحقق من ملف الجلسة
        if not os.path.exists(SESSION_PATH):
            print("session.txt introuvable: %s", SESSION_PATH)
            return

        try:
            with open(SESSION_PATH, "r", encoding="utf-8") as f:
                encrypted_key = f.read().strip()
            if not encrypted_key:
                print("Le fichier session est vide.")
                return
            print("Encrypted key length=%d", len(encrypted_key))
        except Exception:
            print("Erreur en lisant le fichier de session")
            return

        payload = {"encrypted": encrypted_key, "name": name_selected}
        print("Payload prepared: %s", {k: ("<hidden>" if k == "encrypted" else v) for k, v in payload.items()})

        try:
            start_time = time.time()
            # timeout pour éviter le blocage infini
            response = requests.post(_ON_SCENARIO_CHANGED_API, json=payload, timeout=10)
            duration = time.time() - start_time
            print("HTTP POST to %s finished in %.2fs; status_code=%s", _ON_SCENARIO_CHANGED_API, duration, response.status_code)
        except requests.exceptions.RequestException as e:
            print("RequestException while calling API: %s", e)
            # enregistrer le contenu d'erreur si disponible
            return

        # تسجيل نص الاستجابة كاملة لو احتجنا لفحصها عند الأخطاء
        if response.status_code != 200:
            try:
                print("HTTP %s: %s", response.status_code, response.text[:1000])
            except Exception:
                print("HTTP %s and failed to read response.text", response.status_code)
            return

        # محاولة تحويل الاستجابة إلى JSON مع حماية
        try:
            result = response.json()
            print("Response JSON keys: %s", list(result.keys()))
        except ValueError:
            # JSON غير صالح — حفظ النص لفحص لاحق
            print("Failed to parse JSON from response. Response text (first 2000 chars):\n%s", response.text[:2000])
            with open("last_bad_response.txt", "w", encoding="utf-8") as fh:
                fh.write(response.text)
            return

        # التحقق من حالة الجلسة
        try:
            session_ok = result.get("session", True)
            if session_ok is False:
                print("Session expirée. Redirection vers login.")
                try:
                    self.login_window = LoginWindow()
                    self.login_window.setFixedSize(1710, 1005)
                    screen = QGuiApplication.primaryScreen()
                    screen_geometry = screen.availableGeometry()
                    x = (screen_geometry.width() - self.login_window.width()) // 2
                    y = (screen_geometry.height() - self.login_window.height()) // 2
                    self.login_window.move(x, y)
                    self.login_window.show()
                    self.close()
                except Exception:
                    print("Erreur pendant l'affichage de la fenêtre de login")
                return
        except Exception:
            print("Erreur en vérifiant la clé 'session' du résultat")
            return

        # إذا العملية ناجحة
        try:
            if result.get("success"):
                scenario = result.get("scenario")
                if scenario is None:
                    print("Le champ 'scenario' est manquant dans la réponse.")
                    return

                # التأكد من وجود state_stack
                state_stack = scenario.get("state_stack")
                if not isinstance(state_stack, list):
                    print("state_stack n'est pas une liste (type=%s). Tentative de conversion...", type(state_stack))
                    # محاولة تصحيح إذا كانت سلسلة JSON
                    if isinstance(state_stack, str):
                        try:
                            state_stack = json.loads(state_stack)
                            print("state_stack loaded from string; length=%d", len(state_stack))
                        except Exception:
                            print("Impossible de parser state_stack string")
                            return
                    else:
                        print("state_stack a un format inattendu: %r", state_stack)
                        return

                self.STATE_STACK = state_stack
                print("Scénario récupéré avec %d états.", len(self.STATE_STACK))

                # نسخة للمعالجة
                state_stack_copy = copy.deepcopy(self.STATE_STACK)

                for index, state in enumerate(state_stack_copy, start=1):
                    print("Processing state #%d", index)
                    # محاولة عرض حالة بشكل آمن (fallback to str)
                    try:
                        pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
                        print("State #%d preview: %s", index, pretty[:2000])  # لا تطبع كل شيء لو كبير
                    except Exception:
                        print("Cannot JSON-dump state #%d; fallback to repr", index)
                        print("State #%d repr: %s", index, repr(state)[:1000])

                    # استدعاء Load_State مع قياس الوقت
                    try:
                        t0 = time.time()
                        self.Load_State(state)
                        t1 = time.time()
                        print("Load_State for #%d succeeded in %.3fs", index, t1 - t0)
                        # بعد كل تحميل حدّث الأزرار
                        try:
                            self.Update_Actions_Color_Handle_Last_Button()
                        except Exception:
                            print("Update_Actions_Color_Handle_Last_Button failed after state #%d", index)
                    except Exception as e:
                        print("Erreur pendant Load_State() pour l'état #%d: %s", index, e)
                        # لا نكسر الحلقة — نستمر في محاولة تحميل باقي الحالات
                        continue

                print("Scénario chargé avec succès.")

                # حذف التكرارات بطريقة آمنة: نستخدم json.dumps(default=str) لتجنب TypeError
                try:
                    unique_states = []
                    seen = set()
                    for state in self.STATE_STACK:
                        try:
                            state_key = json.dumps(state, sort_keys=True, ensure_ascii=False, default=str)
                        except Exception:
                            print("json.dumps failed for a state during dedup; using repr fallback")
                            state_key = repr(state)
                        if state_key not in seen:
                            seen.add(state_key)
                            unique_states.append(state)
                    self.STATE_STACK = unique_states
                    print("self.STATE_STACK dédupliqué, nouveau length=%d", len(self.STATE_STACK))
                except Exception:
                    print("Échec de suppression des doublons")
            else:
                print("API returned success=false; error: %s", result.get("error"))
        except Exception:
            print("Erreur pendant le traitement du résultat JSON")














class CustomTextDialog(QDialog):
    def __init__(self, parent=None, texte_initial=""):
        super().__init__(parent)
        self.setWindowTitle("Update Text")
        self.setMinimumSize(500, 350)


        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Label d’instruction
        label = QLabel("📝 Please enter your text below:")
        layout.addWidget(label)

        # Zone de texte
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(texte_initial)
        layout.addWidget(self.text_edit)

        # Boutons Annuler / Enregistrer
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 🌟 Style QSS compatible Qt
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-family: "Times", "Times New Roman", serif;
                font-size: 14px;
                color: #2d2d2d;
                font-weight: 500;
                margin-bottom: 10px;
            }
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                font-family: "Times", "Times New Roman", serif;
                background-color: #fafafa;
                font-size: 12pt;
                padding: 5px;
            }
            QTextEdit:focus {
                border: 2px solid #0078d7;
                background-color: #ffffff;
            }
            QPushButton {
                font-family: "Times", "Times New Roman", serif;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton#btn_ok {
                background-color: #0078d7;
                border: none;
                color: white;
            }
            QPushButton#btn_ok:hover {
                background-color: #005a9e;
            }
            QPushButton#btn_cancel {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                color: #333333;
            }
            QPushButton#btn_cancel:hover {
                background-color: #e0e0e0;
            }
        """)

        # IDs pour styles séparés
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel.setObjectName("btn_cancel")

    def get_text(self):
        return self.text_edit.toPlainText()






class LoginWindow(QMainWindow):



    def __init__(self):
        super().__init__()

        # Charger le bon fichier .ui
        self.ui_path = self.Select_Ui_File()
        uic.loadUi(self.ui_path, self)

        # Initialiser les widgets si Auth.ui
        if "Auth.ui" in self.ui_path:
            self.Initialize_Login_Ui()

        self.setWindowTitle("AutoMailPro")




    def Select_Ui_File(self) -> str:
        """Retourne le chemin du .ui à charger (interface ou login)"""

        try:
            session_info = check_session(SESSION_PATH, KEY)

            if session_info["valid"]:
                username = session_info.get("username", "Inconnu")
                date_str = session_info.get("date", "")

                print(f"[SESSION INFO] Utilisateur: {username}")
                print(f"[SESSION INFO] Dernière session: {date_str}")

                return INTERFACE_UI
        except Exception as e:
            print(f"[SESSION ERROR] {e}")

        # Par défaut → retour sur Auth.ui
        return AUTH_UI


    def Initialize_Login_Ui(self):
        """Initialise l'interface de connexion"""
        self.login_input = self.findChild(QLineEdit, "loginInput")
        self.password_input = self.findChild(QLineEdit, "passwordInput")
        self.login_button = self.findChild(QPushButton, "loginButton")
        self.title = self.findChild(QPushButton, "title")
        self.erreur_label = self.findChild(QLabel, "erreur")

        if self.erreur_label:
            self.erreur_label.hide()

        if self.title:
            self.title.clicked.connect(self.Handle_Show_Session_Date)
        if self.login_button:
            self.login_button.clicked.connect(self.Handle_Login)

        # Ajout ombre panneau droit
        right_frame = self.findChild(QWidget, "rightFrame")
        if right_frame:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(25)
            shadow.setXOffset(0)
            shadow.setYOffset(8)
            shadow.setColor(QColor(0, 0, 0, 80))
            right_frame.setGraphicsEffect(shadow)

        # Image de fond
        self.background_image_path = os.path.join(SCRIPT_DIR, "icons", "baghround.jpg")
        self.background_frame = self.findChild(QFrame, "background")
        if self.background_frame:
            self.background_label = QLabel(self.background_frame)
            self.background_label.setStyleSheet("""
                border-top-left-radius: 30px;
                border-bottom-left-radius: 30px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                overflow: hidden;
            """)
            self.background_label.setScaledContents(True)
            self.background_label.lower()
            self.Update_Background_Image()


            self.logoFrame = self.findChild(QFrame, "logoFrame")

            if self.logoFrame:
                self.logo_label = QLabel(self.logoFrame)
                self.logo_label.setScaledContents(True)
                logo_path = os.path.join(SCRIPT_DIR, "icons", "logo.jpg")
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setGeometry(0, 0, self.logoFrame.width(), self.logoFrame.height())
                    self.logo_label.show()
 
            self.UseFrame = self.findChild(QFrame, "userFrame")
            if self.UseFrame:
                self.user_label = QLabel(self.UseFrame)
                self.user_label.setScaledContents(True)
                user_path = os.path.join(SCRIPT_DIR, "icons", "user.png")
                user_pixmap = QPixmap(user_path)
                if not user_pixmap.isNull():
                    self.user_label.setPixmap(user_pixmap)
                    self.user_label.setGeometry(0, 0, self.UseFrame.width(), self.UseFrame.height())
                    self.user_label.show()



    def Update_Background_Image(self):
        if hasattr(self, "background_frame") and hasattr(self, "background_label"):
            pixmap = QPixmap(self.background_image_path)
            if not pixmap.isNull():
                self.background_label.resize(self.background_frame.size())
                self.background_label.setPixmap(pixmap)


    def Check_Api_Credentials(self, username, password):
        try:
            print("\u23f3 [DEBUG] D\u00e9but d'authentification via API")

            data = {
                "rID": "1", "u": username, "p": password,
                "k": "mP5QXYrK9E67Y", "l": "1"
            }

            print(f"📤 [DEBUG] Envoi des donn\u00e9es \u00e0 l'API : {data}")
            for i in range(5):
                try:
                    response = requests.post(_APIACCESS_API, headers=HEADERS, data=data, verify=False).text
                    print(f"✅ [DEBUG] R\u00e9ponse re\u00e7ue \u00e0 la tentative {i+1} : {response}")
                    break
                except Exception as e:
                    print(f"⚠️ [DEBUG] \u00c9chec tentative {i+1} : {str(e)}")
                    time.sleep(5)
            else:
                print("❌ [DEBUG] \u00c9chec apr\u00e8s 5 tentatives")
                return -3

            if response == "-1":
                print("❌ [DEBUG] Identifiants incorrects")
                return -1
            elif response == "-2":
                print("❌ [DEBUG] Appareil non autoris\u00e9")
                return -2
            else:
                print(f"🔐 [DEBUG] Donn\u00e9es chiffr\u00e9es re\u00e7ues : {response}")
                entity = decrypt_message(response, KEY)
                print(f"🔓 [DEBUG] Donn\u00e9es d\u00e9chiffr\u00e9es : {entity}")
                return (entity, response) if entity != -1 else -4
        except Exception as e:
            print(f"🔥 [DEBUG] Erreur inattendue dans Check_Api_Credentials : {str(e)}")
            return -5



    def Handle_Login(self):
        username = self.login_input.text().strip() if self.login_input else ""
        password = self.password_input.text().strip() if self.password_input else ""

        print(f"📅 [DEBUG] Nom d'utilisateur : '{username}', Mot de passe : {'*' * len(password)}")

        if not username or not password:
            print("⚠️ [DEBUG] Champs vides détectés")
            self.erreur_label.setText("Veuillez remplir tous les champs obligatoires.")
            self.erreur_label.show()
            return

        auth_result = self.Check_Api_Credentials(username, password)
        print(f"🔁 [DEBUG] Résultat de l'authentification : {auth_result}")

        if isinstance(auth_result, int):
            messages = {
                -1: "Identifiants incorrects. Veuillez réessayer.",
                -2: "Cet appareil n'est pas autorisé. Contactez l'équipe de support.",
                -3: "Impossible de se connecter au serveur. Réessayez plus tard.",
                -4: "Accès refusé à cette application.",
                -5: "Erreur inconnue pendant l'authentification."
            }
            self.erreur_label.setText(messages.get(auth_result, "Erreur inconnue."))
            self.erreur_label.show()
            return

        entity, encrypted_response = auth_result
        self.erreur_label.hide()

        # هنا نفك تشفير الـ encrypted_response قبل إضافته للجلسة
        decrypted_response = decrypt_message(encrypted_response, KEY)
        print(f"🔓 [DEBUG] Réponse déchiffrée pour session : {decrypted_response}")

        casablanca_time = datetime.datetime.now(pytz.timezone("Africa/Casablanca"))
        print(f"🕒 [DEBUG] Heure Casablanca : {casablanca_time}")

        # دمج اسم المستخدم + الوقت + البيانات المفكوكة في نص الجلسة
        session_data = f"{username}::{casablanca_time.strftime('%Y-%m-%d %H:%M:%S')}::{decrypted_response}"
        print(f"🔐 [DEBUG] Session à chiffrer : {session_data}")

        encrypted = encrypt_message(session_data, KEY)

        os.makedirs(APPDATA_DIR, exist_ok=True)
        session_file_path = os.path.join(APPDATA_DIR, "session.txt")
        print(f"📂 [DEBUG] Sauvegarde de la session dans : {session_file_path}")
        with open(session_file_path, "w") as f:
            f.write(encrypted)

        # تحميل ملف التكوين كما في الكود الأصلي
        print(f"📂 [DEBUG] Chargement du fichier de configuration : {FILE_ACTIONS_JSON}")
        try:
            with open(FILE_ACTIONS_JSON, "r", encoding='utf-8') as file:
                json_data = json.load(file)

            if not json_data:
                raise ValueError("Fichier de configuration vide")

        except Exception as e:
            print(f"❌ [DEBUG] Erreur de lecture configuration : {str(e)}")
            self.erreur_label.setText(f"Erreur configuration : {str(e)}")
            self.erreur_label.show()
            return

        print("🚀 [DEBUG] Lancement de la fenêtre principale")
        self.main_window = MainWindow(json_data)
        self.main_window.setFixedSize(1710, 1005)
        self.main_window.setWindowTitle("AutoMailPro")
        self.main_window.stopButton.clicked.connect(lambda: Stop_All_Processes(self.main_window))

        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.main_window.width()) // 2
        y = (screen_geometry.height() - self.main_window.height()) // 2
        self.main_window.move(x, y)
        self.main_window.show()
        self.close()



    def Handle_Show_Session_Date(self):
        if not os.path.exists(SESSION_PATH):
            self.erreur_label.setText("Aucune session enregistrée.")
            self.erreur_label.show()
            return
        try:
            with open(SESSION_PATH, "r") as f:
                encrypted = f.read().strip()
            decrypted = decrypt_message(encrypted, KEY)
            self.erreur_label.setText(f"Date session : {decrypted}")
            self.erreur_label.show()
        except Exception as e:
            self.erreur_label.setText(f"Erreur lecture session : {e}")
            self.erreur_label.show()














def main():

    if len(sys.argv) < 3:
        sys.exit(1)

    encrypted_key = sys.argv[1]
    secret_key = sys.argv[2]
    if not verify_key(encrypted_key, secret_key):
        sys.exit(1)






    # if os.path.exists(SESSION_PATH):
    #     try:
    #         print("📂 [SESSION] Lecture du fichier de session...")
    #         with open(SESSION_PATH, "r") as f:
    #             encrypted = f.read().strip()

    #         if encrypted:
    #             print("🔐 [SESSION] Déchiffrement des données de session...")
    #             decrypted = decrypt_message(encrypted, KEY)

    #             if "::" in decrypted:
    #                 parts = decrypted.split("::", 2)
    #                 if len(parts) == 3:
    #                     username = parts[0].strip()
    #                     date_str = parts[1].strip()
    #                     p_entity = parts[2].strip()
    #                     print(f"🧾 [SESSION] Données extraites ➜ Utilisateur: `{username}`, Date: `{date_str}`, Entité: `{p_entity}`")
    #                 else:
    #                     print("❌ [ERREUR] Format invalide : 3 parties attendues (username::date::entity)")
    #                     session_valid = False
    #                     return

    #                 try:
    #                     last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    #                     now = datetime.datetime.utcnow()

    #                     if (now - last_session) < timedelta(days=2):
    #                         print("⏳ [VALIDATION] Vérification de la session via API...")

    #                         try:
    #                             params = {
    #                                 "k": "mP5QXYrK9E67Y",
    #                                 "rID": "4",
    #                                 "u": username,
    #                                 "entity": p_entity
    #                             }

    #                             print(f"🌐 [API] Envoi de la requête ➜ {_MAIN_API}")
    #                             response = requests.get(_MAIN_API, params=params, headers=HEADERS, verify=False)
    #                             print(f"📥 [API] Code de réponse: {response.status_code}")
    #                             print(f"📄 [API] Contenu brut de la réponse:\n{response.text}")
    #                             if response.status_code == 200:
    #                                 print(f"📥 [API] Réponse HTTP 200 reçue ✅")
    #                                 data = response.json()

    #                                 if data.get("data")[0].get("n") == "1":
    #                                     session_valid = True
    #                                     print(f"✅ [SESSION] Session valide pour l'utilisateur `{username}` 🎉")

    #                             else:
    #                                 session_valid = False
    #                                 print(f"🚫 [API ERROR] Erreur HTTP ➜ Code {response.status_code}")
    #                         except Exception as e:
    #                             session_valid = False
    #                             print(f"💥 [API EXCEPTION] Erreur lors de l'appel API : {str(e)}")
    #                     else:
    #                         session_valid = False
    #                         print(f"⏱️ [SESSION] Session expirée (⏳ date: `{date_str}`)")
    #                 except ValueError as e:
    #                     session_valid = False
    #                     print(f"❌ [DATE ERROR] Format de date invalide : {e}")
    #             else:
    #                 session_valid = False
    #                 print("⚠️ [FORMAT] Format de session invalide (manque `username::date::entity`)")
    #         else:
    #             session_valid = False
    #             print("🕳️ [SESSION] Fichier de session vide.")
    #     except Exception as e:
    #         session_valid = False
    #         print(f"💣 [SESSION ERROR] Erreur inattendue : {str(e)}")



    session_info = check_session(SESSION_PATH, KEY)
    session_valid = session_info["valid"]

    app = QApplication(sys.argv)


    icon_path = os.path.join(SCRIPT_DIR, "icons", "logo.jpg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    if session_valid:
        try:
            with open(FILE_ACTIONS_JSON, "r", encoding='utf-8') as file:
                json_data = json.load(file)

            if json_data:
                window = MainWindow(json_data)
                window.setFixedSize(1710, 1005)
                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - window.width()) // 2
                y = (screen_geometry.height() - window.height()) // 2
                window.move(x, y)
                window.stopButton.clicked.connect(lambda: Stop_All_Processes(window))
                window.setWindowTitle("AutoMailPro")
                window.show()
            else:
                raise ValueError("Fichier de configuration vide")
        except Exception as e:
            print(f"[CONFIG ERROR] {e}")
            window = LoginWindow()
            window.setFixedSize(1710, 1005)
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - window.width()) // 2
            y = (screen_geometry.height() - window.height()) // 2
            window.move(x, y)
            window.show()
    else:
        window = LoginWindow()
        window.setFixedSize(1710, 1005)
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - window.width()) // 2
        y = (screen_geometry.height() - window.height()) // 2
        window.move(x, y)
        window.show()

    sys.exit(app.exec())








if __name__ == "__main__":
    main()
