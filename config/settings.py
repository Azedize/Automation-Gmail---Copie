import os
from pathlib import Path
import sys
import json

class Settings:
    # =========================================
    #  DATA AUTH
    # =========================================
    KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
    KEY     = bytes.fromhex(KEY_HEX)

    # =========================================
    #  Supported Browsers
    # =========================================
    SUPPORTED_BROWSERS = {
        "chrome": {"exe_name": "chrome.exe", "display_name": "Google Chrome"},
        "firefox": {"exe_name": "firefox.exe", "display_name": "Mozilla Firefox"},
        "edge": {"exe_name": "msedge.exe", "display_name": "Microsoft Edge"},
        "icedragon": {"exe_name": "dragon.exe", "display_name": "Ice Dragon"},
        "comodo": {"exe_name": "chrome.exe", "display_name": "Comodo Dragon"}
    }

    # =========================================
    # Environment Settings
    # =========================================
    PYTHON_PATH = None
    UPDATED_PIP_23_3 = False
    ALL_PACKAGES_INSTALLED = True

    # =========================================
    # API Settings
    # =========================================
    API_BASE_URL = "https://reporting.nrb-apps.com"
    API_TIMEOUT = 15
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 5

    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    }

    API_ENDPOINTS = {
        '_APIACCESS_API': 'https://reporting.nrb-apps.com/pub/chk_usr1.php?rv4=1',
        '_SAVE_EMAIL_API': 'https://reporting.nrb-apps.com/pub/h_new.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1',
        '_SEND_STATUS_API': 'http://reporting.nrb-apps.com:8585/rep/pub/email_status.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1',
        '_SAVE_PROCESS_API': 'https://reporting.nrb-apps.com/pub/SaveProcess.php?k=mP5QXYrK9E67Y&rID=1&rv4=1',
        '_MAIN_API': "https://apps1.nrb-apps.com/pub/chk_usr1.php",
        '_DOWNLOAD_EXTRACTT_API': "https://github.com/Azedize/Programme/archive/refs/heads/main.zip",
        '_CHECK_VERSION_API': "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1"
    }

    # =========================================
    # Encryption Settings
    # =========================================
    ENCRYPTION_KEY_HEX = 'f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2'
    AES_BLOCK_SIZE = 128    
    AES_KEY_LENGTH = 32         
    AES_IV_LENGTH = 16         
    AES_SALT_LENGTH = 16        
    PBKDF2_ITERATIONS = 100_000
    AES_IV_LENGTH_CBC = 16        
    AES_IV_LENGTH_GCM = 12        

    # =========================================
    # Paths
    # =========================================
    BASE_DIR = Path(__file__).resolve().parent.parent
    RESOURCES_DIR = BASE_DIR / 'resources'
    UI_DIR = RESOURCES_DIR / 'ui'
    TEMPLATES_DIR = RESOURCES_DIR / 'templates'

    DATA_DIR = Path(os.getenv('APPDATA')) / 'AutoMailPro'
    SESSION_FILE = DATA_DIR / 'session.txt'

    TOOLS_DIR = BASE_DIR / 'Tools'
    EXTENSIONS_DIR = TOOLS_DIR / 'Extensions'

    PROFILES_DIR = TOOLS_DIR / 'Profiles'
    CHROME_PROFILES = PROFILES_DIR / 'chrome'
    FIREFOX_PROFILES = PROFILES_DIR / 'firefox'
    FAMILY_CHROME_DIR_PROFILES = PROFILES_DIR / 'Family_Chrome'

    EXTENTIONS_DIR_FIREFOX = TOOLS_DIR / 'extensions' / 'FIREFOX_EXTENTIONS'
    EXTENSIONS_DIR_FAMILY_CHROME = TOOLS_DIR / 'extensions' / 'FAMILY_CHROME_EXTENTIONS'

    ICONS_DIR = RESOURCES_DIR / 'icons'
    APP_ICON = ICONS_DIR / "logo.jpg"  # إضافة متغير APP_ICON لتفادي الخطأ

    LOGS_DIRECTORY = TOOLS_DIR / 'logs'
    RESULT_FILE_PATH = TOOLS_DIR / "result.txt"

    SESSION_PATH = DATA_DIR / "session.txt"

    # =========================================
    # Application Settings
    # =========================================
    WINDOW_WIDTH = 1710
    WINDOW_HEIGHT = 1005
    PRIMARY_COLOR = '#669bbc'
    SECONDARY_COLOR = '#b2cddd'
    ACCENT_COLOR = '#d90429'
    SUCCESS_COLOR = '#2e7d32'
    WARNING_COLOR = '#ed6c02'
    ERROR_COLOR = '#d32f2f'
    INFO_COLOR = '#0288d1'

    FONT_FAMILY = 'Times, Times New Roman, serif'
    FONT_SIZE_SMALL = 12
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_LARGE = 16

    MAX_CONCURRENT_BROWSERS = 10
    THREAD_POOL_SIZE = 4

    # =========================================
    # Utility Methods
    # =========================================
    @classmethod
    def ensure_directories(cls):
        """Créer tous les dossiers nécessaires de manière sûre"""
        directories = [
            cls.DATA_DIR,
            cls.TOOLS_DIR,
            cls.LOGS_DIRECTORY,
            cls.PROFILES_DIR,
            cls.CHROME_PROFILES,
            cls.FIREFOX_PROFILES,
            cls.FAMILY_CHROME_DIR_PROFILES,
            cls.EXTENSIONS_DIR,
            cls.EXTENTIONS_DIR_FIREFOX,
            cls.EXTENSIONS_DIR_FAMILY_CHROME,
        ]

        for path in directories:
            path = Path(path)
            if path.exists():
                if not path.is_dir():
                    raise RuntimeError(f"❌ Path exists but is not a directory: {path}")
                else:
                    print(f"ℹ️ Directory exists: {path}")
            else:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Directory created: {path}")

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

# Instance unique globale
settings = Settings()

# Vérification et création des dossiers
settings.ensure_directories()

