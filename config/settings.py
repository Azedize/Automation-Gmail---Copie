import os
from pathlib import Path
import sys
import json





class Settings:
    # ═══════════════════════════════════════════════════════════
    #  DATA AUTH
    # ═══════════════════════════════════════════════════════════
    DATA_AUTH = {
            "login": "rep.test",
            "password": "zsGEnntKD5q2Brp68yxT"
    }

    KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
    KEY     = bytes.fromhex(KEY_HEX)




    # ═══════════════════════════════════════════════════════════
    #  Sopport des navigateurs
    # ═══════════════════════════════════════════════════════════


    SUPPORTED_BROWSERS = {
        "chrome": {
            "exe_name": "chrome.exe",
            "display_name": "Google Chrome"
        },
        "firefox": {
            "exe_name": "firefox.exe",
            "display_name": "Mozilla Firefox"
        },
        "edge": {
            "exe_name": "msedge.exe",
            "display_name": "Microsoft Edge"
        },
        "icedragon": {
            "exe_name": "dragon.exe",
            "display_name": "Ice Dragon"
     
        },
        "comodo": {
            "exe_name": "chrome.exe",  
            "display_name": "Comodo Dragon"
        }
    }
    # ═══════════════════════════════════════════════════════════
    # 🌐 Paramètres de l’environnement
    # ═══════════════════════════════════════════════════════════

    # Chemin de l’executable de Python
    PYTHON_PATH = None
    UPDATED_PIP_23_3 = False
    ALL_PACKAGES_INSTALLED = True

    # ═══════════════════════════════════════════════════════════
    # 🌐 Paramètres de l’API
    # ═══════════════════════════════════════════════════════════

    API_BASE_URL = "https://reporting.nrb-apps.com"
    API_TIMEOUT = 15  # en secondes
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 5  # en secondes
    
    # ═══════════════════════════════════════════════════════════
    # 🌐 Header
    # ═══════════════════════════════════════════════════════════
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
        '_DOWNLOAD_EXTRACTT_API'    :  "https://github.com/Azedize/Programme/archive/refs/heads/main.zip",
        '_CHECK_VERSION_API'        :  "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1",
        '_HANDLE_SAVE_API'          :  "http://localhost/auth-api/add_scenario.php",
        '_LOAD_SCENARIOS_API'       :  "http://localhost/auth-api/get_scenarios.php",
        '_ON_SCENARIO_CHANGED_API'  :  "http://localhost/auth-api/get_scenario_by_name.php",
        '__CHECK_URL_PROGRAMM__': "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1",
        '__SERVER_ZIP_URL_PROGRAM__': "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/master.zip"
    }




    # =========================================
    # 🌐 URL UPDATE PROGRAMM
    # =========================================


    # les clés pour générer la clé finale
    CLE1 = "pr"
    CLE2 = "rep"
    COMBINED_KEYS = f"&{CLE1}&{CLE2}"



    
    # ═══════════════════════════════════════════════════════════
    # 🔐 Paramètres de chiffrement
    # ═══════════════════════════════════════════════════════════
    
    ENCRYPTION_KEY_HEX = 'f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2'
    
    
    
    
    
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
    RESOURCES_DIR = BASE_DIR / 'resources'
    UI_DIR = RESOURCES_DIR / 'ui'
    # ICONS_DIR = RESOURCES_DIR / 'icons'
    TEMPLATES_DIR = RESOURCES_DIR / 'templates'
    
    DATA_DIR = Path(os.getenv('APPDATA')) / 'AutoMailPro'
    SESSION_FILE = DATA_DIR / 'session.txt'
    LOGS_DIR = BASE_DIR / 'Tools'  / 'logs'
    
    PROFILES_DIR = BASE_DIR / 'Tools' / 'Profiles'
    CHROME_PROFILES = PROFILES_DIR / 'chrome'
    FIREFOX_PROFILES = PROFILES_DIR / 'firefox'
    
    TOOLS_DIR = BASE_DIR / 'Tools'
    EXTENSIONS_DIR = BASE_DIR / 'Tools' / 'Extensions'
    VERSION_LOCAL_EXT = os.path.join(EXTENSIONS_DIR, "version.txt")
    VERSION_LOCAL_PROGRAMM = os.path.join(BASE_DIR , "config", "version.txt")

    ICONS_DIR = BASE_DIR / 'resources' / 'icons'
    FILE_ISP = os.path.join(BASE_DIR, "config", "Isp.txt")


    # ═══════════════════════════════════════════════════════════
    # Chemin Extentions
    # ═══════════════════════════════════════════════════════════

    CONFIG_PROFILE              = r"C:\RepProxy\template Profile"
    SECURE_PREFERENCES_TEMPLATE = r"C:\RepProxy\template Profile\default\Secure Preferences"
    EXTENTION_EX3               = r"C:\RepProxy\Ext3"
    MANIFEST_PATH_EX3           = os.path.join(EXTENTION_EX3, "manifest.json")
    VERSION_LOCAL_EX3           = os.path.join(EXTENTION_EX3, "version.txt")



    BASE_DIRECTORY = os.path.join(BASE_DIR, 'tools', 'ExtensionEmail')
    TEMPLATE_DIRECTORY_FIREFOX  = os.path.join(BASE_DIR, 'tools', 'ExtensionTemplateFirefox')
    TEMPLATE_DIRECTORY_FAMILY_CHROME = os.path.join(BASE_DIR, 'tools', 'Extention_Family_Chrome')


    LOGS_DIRECTORY = os.path.join(BASE_DIR, 'tools', 'logs')
    RESULT_FILE_PATH = os.path.join(BASE_DIR,  "tools", "result.txt")

    APPDATA       = os.getenv("APPDATA")
    APP_NAME      = "SecureDesk"
    APPDATA_DIR   = os.path.join(APPDATA, APP_NAME)

    SESSION_PATH  = os.path.join(APPDATA_DIR, "session.txt")

    # ═══════════════════════════════════════════════════════════
    # 🔑 Recherche clés spécifiques
    # ═══════════════════════════════════════════════════════════
    RESULTATS=[]
    CLES_RECHERCHE = ["cglaeklndjbecchejgkdpblljkmgkacg","dkbionknflglndapchlcfnelgchogjnl", "developer_mode"]
    RESULTATS_EX = []



    ARROW_DOWN_PATH      = os.path.join(ICONS_DIR, "arrow_Down.png").replace("\\", "/")
    ARROW_UP_PATH        = os.path.join(ICONS_DIR, "arrow_up.png").replace("\\", "/")
    ARROW_DOWN_W_PATH    = os.path.join(ICONS_DIR, "arrow_Down_w.png")
    ARROW_UP_W_PATH      = os.path.join(ICONS_DIR, "arrow_up_w.png")

    DOWN_EXISTS    = os.path.exists(ARROW_DOWN_PATH)
    UP_EXISTS      = os.path.exists(ARROW_UP_PATH)
    DOWN_EXISTS_W  = os.path.exists(ARROW_DOWN_W_PATH)
    UP_EXISTS_W    = os.path.exists(ARROW_UP_W_PATH)

    # ═══════════════════════════════════════════════════════════
    # 🖥️ Paramètres de l’interface
    # ═══════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════
    # ⚙️ Paramètres de l’application
    # ═══════════════════════════════════════════════════════════
    

    
    SESSION_VALIDITY_DAYS = 2
    SESSION_TIMEZONE = 'Africa/Casablanca'
    
    SERVICES = {
                "Gmail": "Gmail.png",
                # "Hotmail": "Hotmail.png",
                # "Yahoo": "Yahoo.png"
            }
 
    MAX_CONCURRENT_BROWSERS = 10
    THREAD_POOL_SIZE = 4
    
    # ═══════════════════════════════════════════════════════════
    # 🔍 Paramètres de mise à jour
    # ═══════════════════════════════════════════════════════════
    
    UPDATE_CHECK_URL = (
        "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/"
        "version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1"
    )
    UPDATE_DOWNLOAD_URL = (
        "https://github.com/Azedize/Programme/archive/refs/heads/main.zip"
    )
    

    

    
    # ═══════════════════════════════════════════════════════════
    # 📂 Déclaration des chemins UI globaux Interface
    # ═══════════════════════════════════════════════════════════


    INTERFACE_UI      = os.path.abspath(os.path.join(BASE_DIR,  "resources", 'ui', "interface.ui"))
    AUTH_UI           = os.path.abspath(os.path.join(BASE_DIR, "resources", 'ui', "Auth.ui"))
    FILE_ACTIONS_JSON = os.path.join(BASE_DIR, "config", "action.json")
    AUTH_BACKGROUND   = os.path.join(BASE_DIR,"resources" , "icons", "baghround.jpg")
    APP_ICON          = os.path.join(BASE_DIR,"resources" , "icons", "logo.jpg")
    # ═══════════════════════════════════════════════════════════
    # Méthodes utilitaires
    # ═══════════════════════════════════════════════════════════
    

    
    STATUS_LIST = ["all", "bad_proxy", "completed", "account_closed", "password_changed", "code_de_validation",
                    "recoverychanged", "Activite_suspecte", "validation_capcha", "restore_account", "others"]
    


    
    @classmethod
    def ensure_directories(cls):
        """Créer les dossiers nécessaires s’ils n’existent pas"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.PROFILES_DIR,
            cls.CHROME_PROFILES,
            cls.FIREFOX_PROFILES,
            cls.EXTENSIONS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_encryption_key_bytes(cls) -> bytes:
        """Obtenir la clé de chiffrement au format bytes"""
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



# Création d’une instance unique utilisée dans tout le projet
settings = Settings()

# Vérification et création des dossiers de base
# settings.ensure_directories()
