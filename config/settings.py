import os
from pathlib import Path
import sys
import datetime
import traceback
import subprocess
import shutil


class Settings:

    API_KEY_PROXY = "Gmf15dfVD61G8gZQg"

    AUTHORISED_PORTS = ["5836", "0000", "8080", "3128", "1111", "16666"]

    # ═══════════════════════════════════════════════════════════
    #  DATA AUTH
    # ═══════════════════════════════════════════════════════════

    KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
    KEY = bytes.fromhex(KEY_HEX)

    # ═══════════════════════════════════════════════════════════
    #  Sopport des navigateurs
    # ═══════════════════════════════════════════════════════════

    SUPPORTED_BROWSERS = {
        "chrome": {"exe_name": "chrome.exe"},
        "firefox": {"exe_name": "firefox.exe"},
        "edge": {"exe_name": "msedge.exe"},
        "icedragon": {"exe_name": "dragon.exe"},
        "comodo": {"exe_name": "chrome.exe"},
    }

    # ═══════════════════════════════════════════════════════════
    # 🌐 Header
    # ═══════════════════════════════════════════════════════════
    HEADER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    API_ENDPOINTS = {
        "_APIACCESS_API": "https://reporting.nrb-apps.com/pub/chk_usr1.php?rv4=1",
        "_SAVE_EMAIL_API": "https://reporting.nrb-apps.com/pub/h_new.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1",
        "_SEND_STATUS_API": "http://reporting.nrb-apps.com:8585/rep/pub/email_status.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1",
        "_SAVE_PROCESS_API": "https://reporting.nrb-apps.com/pub/SaveProcess.php?k=mP5QXYrK9E67Y&rID=1&rv4=1",
        "_MAIN_API": "https://apps1.nrb-apps.com/pub/chk_usr1.php",
        "__CHECK_URL_PROGRAMM__": "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1",
        "__SERVER_ZIP_URL_PROGRAM__": "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/master.zip",
        "__GET_PROXY_INFO__": "https://reporting.nrb-apps.com/pub/getInfoProxy.php",
    }

    # ═══════════════════════════════════════════════════════════
    # 🔐 Paramètres de chiffrement
    # ═══════════════════════════════════════════════════════════

    ENCRYPTION_KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"

    AES_BLOCK_SIZE = 128
    AES_KEY_LENGTH = 32
    AES_IV_LENGTH = 16
    AES_SALT_LENGTH = 16
    PBKDF2_ITERATIONS = 100_000
    AES_IV_LENGTH_CBC = 16
    AES_IV_LENGTH_GCM = 12

    # ═══════════════════════════════════════════════════════════
    # 📁 Paramètres des chemins
    # ═══════════════════════════════════════════════════════════

    BASE_DIR = Path(__file__).resolve().parent.parent
    RESOURCES_DIR = BASE_DIR / "resources"

    DATA_DIR = Path(os.getenv("APPDATA")) / "AutoMailPro"
    SESSION_FILE = DATA_DIR / "session.txt"

    TOOLS_DIR = BASE_DIR / "Tools"
    EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"

    PROFILES_DIR = TOOLS_DIR / "Profiles"
    CHROME_PROFILES = PROFILES_DIR / "chrome"
    FIREFOX_PROFILES = PROFILES_DIR / "firefox"
    EDGE_PROFILES = PROFILES_DIR / "edge"
    ICEDRAGON_PROFILES = PROFILES_DIR / "icedragon"
    COMODO_PROFILES = PROFILES_DIR / "comodo"

  

    VERSION_LOCAL_EXT = os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt")
    VERSION_LOCAL_PROGRAMM = os.path.join(BASE_DIR, "config", "version.txt")

    EXTENTIONS_DIR_FIREFOX_TEMPLETE = EXTENSIONS_DIR_TEMPLETE / "ExtensionTemplateFirefox"
    EXTENSIONS_DIR_CHROMIUM_TEMPLETE = EXTENSIONS_DIR_TEMPLETE / "Extention_Family_Chrome"

    FOLDER_EXTENSIONS_DIR = TOOLS_DIR / "extensions"
    FOLDER_EXTENTIONS_FIREFOX = FOLDER_EXTENSIONS_DIR / "firefox"
    FOLDER_EXTENTIONS_CHROME = FOLDER_EXTENSIONS_DIR / "chrome"
    FOLDER_EXTENTIONS_EDGE = FOLDER_EXTENSIONS_DIR / "edge"
    FOLDER_EXTENTIONS_ICEDRAGON = FOLDER_EXTENSIONS_DIR / "icedragon"
    FOLDER_EXTENTIONS_COMODO = FOLDER_EXTENSIONS_DIR / "comodo"

    CHROMIUM_BROWSER_PATHS = {
        "edge": {
            "profiles": EDGE_PROFILES,
            "extensions": FOLDER_EXTENTIONS_EDGE,
        },
        "icedragon": {
            "profiles": ICEDRAGON_PROFILES,
            "extensions": FOLDER_EXTENTIONS_ICEDRAGON,
        },
        "comodo": {
            "profiles": COMODO_PROFILES,
            "extensions": FOLDER_EXTENTIONS_COMODO,
        },
    }

    CHROME_FAMILY_BROWSERS = {"chrome", "edge", "icedragon", "comodo"}

    BROWSER_PROFILE_PATHS = {
        "chrome": CHROME_PROFILES,
        "firefox": FIREFOX_PROFILES,
        "edge": EDGE_PROFILES,
        "icedragon": ICEDRAGON_PROFILES,
        "comodo": COMODO_PROFILES,
    }

    ICONS_DIR = BASE_DIR / "resources" / "icons"
    FILE_ISP = os.path.join(BASE_DIR, "config", "Isp.txt")

    # ═══════════════════════════════════════════════════════════
    # Chemin Extentions
    # ═══════════════════════════════════════════════════════════

    CONFIG_PROFILE = r"C:\RepProxy\template_Profile"
    SECURE_PREFERENCES_TEMPLATE = r"C:\RepProxy\template_Profile\default\Secure Preferences"
    FICHIER_LOCAL_STATE = r"C:\RepProxy\template_Profile\Local State"
    FICHIER_VARIATIONS = r"C:\RepProxy\template_Profile\Variations"


    EXTENTION_EX3_FIREFOX = r"C:\RepProxy\Ext3_Firefox"
    VERSION_LOCAL_EX3_FIREFOX = os.path.join(EXTENTION_EX3_FIREFOX, "version.txt")

    
    EXTENTION_EX3_CHROMIUM = r"C:\RepProxy\Ext3"
    MANIFEST_PATH_EX3 = os.path.join(EXTENTION_EX3_CHROMIUM, "manifest.json")
    VERSION_LOCAL_EX3 = os.path.join(EXTENTION_EX3_CHROMIUM, "version.txt")

    TEMPLATE_DIRECTORY_FIREFOX = os.path.join( TOOLS_DIR, "extensions Templete", "ExtensionTemplateFirefox" )
    TEMPLATE_DIRECTORY_CHROMIUM = os.path.join(  TOOLS_DIR, "extensions Templete", "Extention_Family_Chrome" )

    LOGS_DIRECTORY = os.path.join(TOOLS_DIR, "logs")
    RESULT_FILE_PATH = os.path.join(TOOLS_DIR, "result.txt")

    APPDATA = os.getenv("APPDATA")
    APP_NAME = "SecureDesk"
    APPDATA_DIR = os.path.join(APPDATA, APP_NAME)

    SESSION_PATH = os.path.join(APPDATA_DIR, "session.txt")

    # ═══════════════════════════════════════════════════════════
    # 🔑 Recherche clés spécifiques
    # ═══════════════════════════════════════════════════════════
    RESULTATS = []
    CLES_RECHERCHE = [
        "cglaeklndjbecchejgkdpblljkmgkacg",
        "dkbionknflglndapchlcfnelgchogjnl",
        "developer_mode",
    ]
    RESULTATS_EX = []

    ARROW_DOWN_PATH = os.path.join(ICONS_DIR, "arrow_Down.png").replace("\\", "/")
    ARROW_UP_PATH = os.path.join(ICONS_DIR, "arrow_up.png").replace("\\", "/")
    ARROW_DOWN_W_PATH = os.path.join(ICONS_DIR, "arrow_Down_w.png")
    ARROW_UP_W_PATH = os.path.join(ICONS_DIR, "arrow_up_w.png")

    DOWN_EXISTS = os.path.exists(ARROW_DOWN_PATH)
    UP_EXISTS = os.path.exists(ARROW_UP_PATH)
    DOWN_EXISTS_W = os.path.exists(ARROW_DOWN_W_PATH)
    UP_EXISTS_W = os.path.exists(ARROW_UP_W_PATH)

    # ═══════════════════════════════════════════════════════════
    # 🖥️ Paramètres de l’interface
    # ═══════════════════════════════════════════════════════════

    WINDOW_WIDTH = 1710
    WINDOW_HEIGHT = 1005

    PRIMARY_COLOR = "#669bbc"
    SECONDARY_COLOR = "#b2cddd"
    ACCENT_COLOR = "#d90429"
    SUCCESS_COLOR = "#2e7d32"
    WARNING_COLOR = "#ed6c02"
    ERROR_COLOR = "#d32f2f"
    INFO_COLOR = "#0288d1"

    FONT_FAMILY = "Times, Times New Roman, serif"
    FONT_SIZE_SMALL = 12
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_LARGE = 16

    # ═══════════════════════════════════════════════════════════
    # ⚙️ Paramètres de l’application
    # ═══════════════════════════════════════════════════════════

    SERVICES = {
        "Gmail": "Gmail.png",
        # "Hotmail": "Hotmail.png",
        # "Yahoo": "Yahoo.png"
    }

    MAX_CONCURRENT_BROWSERS = 10
    THREAD_POOL_SIZE = 4

    # ═══════════════════════════════════════════════════════════
    # 📂 Déclaration des chemins UI globaux Interface
    # ═══════════════════════════════════════════════════════════

    INTERFACE_UI = os.path.abspath(os.path.join(BASE_DIR, "resources", "ui", "interface.ui"))
    AUTH_UI = os.path.abspath(os.path.join(BASE_DIR, "resources", "ui", "Auth.ui"))
    FILE_ACTIONS_JSON = os.path.join(BASE_DIR, "config", "action.json")
    AUTH_BACKGROUND = os.path.join(BASE_DIR, "resources", "icons", "baghround.jpg")
    APP_ICON = os.path.join(BASE_DIR, "resources", "icons", "logo.jpg")

    STATUS_LIST = [
        "all",
        "bad_proxy",
        "completed",
        "account_closed",
        "password_changed",
        "code_de_validation",
        "recoverychanged",
        "Activite_suspecte",
        "validation_capcha",
        "restore_account",
        "others",
    ]

    LOG_DEV_FILE = os.path.abspath(os.path.join(BASE_DIR, "Log/LogDev/my_project.log"))

    @classmethod
    def WRITE_LOG_DEV_FILE(cls, message: str, level: str = "INFO"):
        try:
            # Génération de la date et heure actuelle pour le timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] [{level}] {message}\n"

            # Vérifie que le dossier contenant le fichier de log existe, sinon le crée
            log_path = Path(cls.LOG_DEV_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Ouvre le fichier en mode "append" pour ajouter la ligne de log à la fin
            with open(cls.LOG_DEV_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)

        except Exception as e:

            print(f"❌ [LOG] Erreur lors de l'écriture du log: {e}")
            pass

    @classmethod
    def clear_log(cls):
        try:
            log_path = Path(cls.LOG_DEV_FILE)
            if log_path.exists():
                # Ouvre le fichier en mode "write" pour effacer tout son contenu
                open(log_path, "w", encoding="utf-8").close()
                # print(f"✅ [LOG] Fichier log vidé: {cls.LOG_DEV_FILE}")
            else:
                #print(f"⚠️ [LOG] Fichier log inexistant: {cls.LOG_DEV_FILE}")
                settings.WRITE_LOG_DEV_FILE("Fichier log inexistant", "WARNING")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(   f"Exception while clearing log: {traceback.format_exc()}", "ERROR"  )
            # print(f"❌ [LOG] Erreur lors de la suppression du fichier log: {e}")
            pass

    @classmethod
    def ensure_directories(cls):
        """Créer les dossiers nécessaires s’ils n’existent pas"""
        directories = [
            cls.DATA_DIR,
            cls.PROFILES_DIR,
            cls.LOGS_DIRECTORY,
            cls.CHROME_PROFILES,
            cls.FIREFOX_PROFILES,
            cls.EDGE_PROFILES,
            cls.ICEDRAGON_PROFILES,
            cls.COMODO_PROFILES,
            cls.FOLDER_EXTENSIONS_DIR,
            cls.FOLDER_EXTENTIONS_FIREFOX,
            cls.FOLDER_EXTENTIONS_CHROME,
            cls.FOLDER_EXTENTIONS_EDGE,
            cls.FOLDER_EXTENTIONS_ICEDRAGON,
            cls.FOLDER_EXTENTIONS_COMODO,
        ]
        for directory in directories:
            path = Path(directory)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    # print(f"✅ Dossier créé: {path}")
                except Exception as e:
                    Settings.WRITE_LOG_DEV_FILE(  f"Exception while creating directory {path}: {traceback.format_exc()}",   "ERROR" )
                    # print(f"💥 Erreur lors de la création du dossier {path}: {e}")
            # else:
            #     print(f"ℹ️ Dossier déjà existant: {path}")

    @classmethod
    def get_encryption_key_bytes(cls) -> bytes:
        return bytes.fromhex(cls.ENCRYPTION_KEY_HEX)

    @classmethod
    def find_pythonw(cls):
        base_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(base_dir, "pythonw.exe")
        if os.path.isfile(candidate):
            return candidate
        for path in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(path.strip('"'), "pythonw.exe")
            if os.path.isfile(candidate):
                return candidate
        return None

    @classmethod
    def ensure_node_installed(cls):
        if shutil.which("node") is not None:
            cls.WRITE_LOG_DEV_FILE("Node.js already installed", "INFO")
            return True

        cls.WRITE_LOG_DEV_FILE("Node.js not installed. Trying to install via Chocolatey...", "INFO")

        if shutil.which("choco") is None:
            cls.WRITE_LOG_DEV_FILE("Chocolatey not found. Installing...", "INFO")
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
                        "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                cls.WRITE_LOG_DEV_FILE(f"Error installing Chocolatey{traceback.format_exc()}", "ERROR")
                return False

        try:
            subprocess.run(["choco", "install", "nodejs-lts", "-y"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            cls.WRITE_LOG_DEV_FILE(f"Error installing Node.js via Chocolatey: {e}\n{traceback.format_exc()}", "ERROR")
            return False

    @classmethod
    def get_web_ext_path(cls):
        path = shutil.which("web-ext")
        if path:
            return path
        return None

    @classmethod
    def ensure_web_ext_installed(cls):
        if not cls.ensure_node_installed():
            cls.WRITE_LOG_DEV_FILE("Unable to continue without Node.js.", "WARNING")
            return
        if shutil.which("npm") is None:
            cls.WRITE_LOG_DEV_FILE("npm is not installed.", "ERROR")
            return
        if shutil.which("web-ext") is not None:
            cls.WRITE_LOG_DEV_FILE("web-ext already installed", "INFO")
            return
        try:
            subprocess.run("npm install --global web-ext", check=True, shell=True)
        except subprocess.CalledProcessError as e:
            cls.WRITE_LOG_DEV_FILE(f"Error installing web-ext via npm: {e}\n{traceback.format_exc()}", "ERROR")


# Création d’une instance unique utilisée dans tout le projet
settings = Settings()

# Vérification et création des dossiers de base
settings.ensure_directories()
