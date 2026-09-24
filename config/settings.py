import os
from pathlib import Path
import sys
import datetime
import traceback
import subprocess
import shutil
import hashlib
import json
import logging
import re
import threading
import uuid
from logging.handlers import RotatingFileHandler


class Settings:


    SECURITY_CONFIG = {
        "API_KEY_PROXY": "Gmf15dfVD61G8gZQg",
        "AUTHORISED_PORTS": ["5836", "0000", "8080", "3128", "1111", "16666"],
        "PROXY_VALIDATION_PORTS": ["0000", "1111"],
        "KEY_HEX": "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2",
        "VERIFY_SSL": True,
        "HEADER": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        },
    }

    BROWSER_CONFIG = {
        "SUPPORTED_BROWSERS": {
            "chrome": {"exe_name": "chrome.exe"},
            "firefox": {"exe_name": "firefox.exe"},
            "edge": {"exe_name": "msedge.exe"},
            "icedragon": {"exe_name": "dragon.exe"},
            "comodo": {"exe_name": "chrome.exe"},
        },
        "CHROME_FAMILY_BROWSERS": {"chrome", "edge", "msedge", "icedragon", "comodo"},
        "BROWSER_OPTIONS": (
            ("Chrome", "chrome.png"),
            ("Firefox", "firefox.png"),
            ("Edge", "edge.png"),
            ("Comodo", "comodo.png"),
        ),
        "PROCESS_PATTERNS": {
            "chrome": ("chrome", "chromium"),
            "edge": ("edge", "msedge"),
            "icedragon": ("dragon", "icedragon", "chromium"),
            "comodo": ("comodo", "chrome"),
        },
        "EXECUTABLES": {
            "chrome": "chrome.exe",
            "firefox": "firefox",
            "edge": "msedge.exe",
            "icedragon": "dragon.exe",
            "comodo": "dragon.exe",
        },
    }

    EXTENSION_CONFIG = {
        "TARGET_NAME": "EX3",
        "FIREFOX_ID": "gmail.automation.proxy@azedine.dev",
    }

    UPDATE_CONFIG = {
        "PROGRAM_CHECK_ENDPOINT": "https://reporting.nrb-apps.com/APP_R/redirect.php",
        "PROGRAM_CHECK_EXTENSION": "Script",
        "EXTENSION_CHECK_EXTENSION": "Ext3",
        "PROGRAM_DOWNLOAD_URL": "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip",
    }

    BROWSER_EXTENSION_PATHS = {
        "chrome": (
            ("AppData", "Local", "Google", "Chrome", "User Data", "Default", "Extensions"),
            ("AppData", "Local", "Google", "Chrome", "User Data", "Profile 1", "Extensions"),
        ),
        "edge": (
            ("AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Extensions"),
            ("AppData", "Local", "Microsoft", "Edge", "User Data", "Profile 1", "Extensions"),
        ),
        "comodo": (
            ("AppData", "Local", "Comodo", "Browser", "User Data", "Default", "Extensions"),
            ("AppData", "Local", "Comodo", "Dragon", "User Data", "Default", "Extensions"),
            ("AppData", "Local", "Comodo", "Dragon", "User Data", "Profile 1", "Extensions"),
            ("AppData", "Local", "Comodo", "Comodo Dragon", "User Data", "Default", "Extensions"),
            ("AppData", "Roaming", "Comodo", "Dragon", "User Data", "Default", "Extensions"),
        ),
        "icedragon": (
            ("AppData", "Local", "Icedragon", "User Data", "Default", "Extensions"),
        ),
        "firefox": (
            ("AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        ),
    }

    PROCESS_CONFIG = {
        "GOOGLE_PREFIX": "google",
        "YOUTUBE_PREFIX": "youtube",
        "EXCLUDED_PROCESSES": frozenset(
            {"google_maps_actions", "save_location", "search_activities"}
        ),
        "ALLOWED_ITEMS": {
            "open_inbox": ("report_spam", "delete", "archive"),
            "open_spam": ("not_spam", "delete", "report_spam"),
        },
    }

    ISP_MAPPING = {"gmail": "Gmail", "hotmail": "Hotmail", "yahoo": "Yahoo"}

    VALIDATION_CONFIG = {
        "EMAIL": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "NUMERIC_RANGE": r"^\s*(\d+)(?:\s*,\s*(\d+))?\s*$",
        "IP_ADDRESS": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    }

    UI_CONFIG = {
        "WINDOW_WIDTH": 1710,
        "WINDOW_HEIGHT": 1005,
        "PRIMARY_COLOR": "#669bbc",
        "SECONDARY_COLOR": "#b2cddd",
        "ACCENT_COLOR": "#d90429",
        "SUCCESS_COLOR": "#2e7d32",
        "WARNING_COLOR": "#ed6c02",
        "ERROR_COLOR": "#d32f2f",
        "INFO_COLOR": "#0288d1",
        "FONT_FAMILY": "Times, Times New Roman, serif",
        "FONT_SIZE_SMALL": 12,
        "FONT_SIZE_MEDIUM": 14,
        "FONT_SIZE_LARGE": 16,
    }

    API_KEY_PROXY = SECURITY_CONFIG["API_KEY_PROXY"]
    AUTHORISED_PORTS = SECURITY_CONFIG["AUTHORISED_PORTS"]
    PROXY_VALIDATION_PORTS = SECURITY_CONFIG["PROXY_VALIDATION_PORTS"]
    KEY_HEX = SECURITY_CONFIG["KEY_HEX"]
    KEY = bytes.fromhex(KEY_HEX)
    VERIFY_SSL = SECURITY_CONFIG["VERIFY_SSL"]
    HEADER = SECURITY_CONFIG["HEADER"]
    SUPPORTED_BROWSERS = BROWSER_CONFIG["SUPPORTED_BROWSERS"]
    CHROME_FAMILY_BROWSERS = BROWSER_CONFIG["CHROME_FAMILY_BROWSERS"]
    BROWSER_OPTIONS = BROWSER_CONFIG["BROWSER_OPTIONS"]
    BROWSER_PROCESS_PATTERNS = BROWSER_CONFIG["PROCESS_PATTERNS"]
    BROWSER_EXECUTABLES = BROWSER_CONFIG["EXECUTABLES"]

    GOOGLE_PREFIX = PROCESS_CONFIG["GOOGLE_PREFIX"]
    YOUTUBE_PREFIX = PROCESS_CONFIG["YOUTUBE_PREFIX"]
    EXCLUDED_PROCESSES = PROCESS_CONFIG["EXCLUDED_PROCESSES"]
    ALLOWED_ITEMS = PROCESS_CONFIG["ALLOWED_ITEMS"]

    WINDOW_WIDTH = UI_CONFIG["WINDOW_WIDTH"]
    WINDOW_HEIGHT = UI_CONFIG["WINDOW_HEIGHT"]
    PRIMARY_COLOR = UI_CONFIG["PRIMARY_COLOR"]
    SECONDARY_COLOR = UI_CONFIG["SECONDARY_COLOR"]
    ACCENT_COLOR = UI_CONFIG["ACCENT_COLOR"]
    SUCCESS_COLOR = UI_CONFIG["SUCCESS_COLOR"]
    WARNING_COLOR = UI_CONFIG["WARNING_COLOR"]
    ERROR_COLOR = UI_CONFIG["ERROR_COLOR"]
    INFO_COLOR = UI_CONFIG["INFO_COLOR"]
    FONT_FAMILY = UI_CONFIG["FONT_FAMILY"]
    FONT_SIZE_SMALL = UI_CONFIG["FONT_SIZE_SMALL"]
    FONT_SIZE_MEDIUM = UI_CONFIG["FONT_SIZE_MEDIUM"]
    FONT_SIZE_LARGE = UI_CONFIG["FONT_SIZE_LARGE"]

    EXTENSION_TARGET_NAME = EXTENSION_CONFIG["TARGET_NAME"]
    FIREFOX_EXTENSION_ID = EXTENSION_CONFIG["FIREFOX_ID"]
    PROGRAM_CHECK_ENDPOINT = UPDATE_CONFIG["PROGRAM_CHECK_ENDPOINT"]
    PROGRAM_CHECK_EXTENSION = UPDATE_CONFIG["PROGRAM_CHECK_EXTENSION"]
    EXTENSION_CHECK_EXTENSION = UPDATE_CONFIG["EXTENSION_CHECK_EXTENSION"]
    PROGRAM_DOWNLOAD_URL = UPDATE_CONFIG["PROGRAM_DOWNLOAD_URL"]
    BROWSER_EXTENSION_CANDIDATES = BROWSER_EXTENSION_PATHS

    API_ENDPOINTS = {
        "_APIACCESS_API": "https://reporting.nrb-apps.com/pub/chk_usr1.php?rv4=1",
        "_SAVE_EMAIL_API": "https://reporting.nrb-apps.com/pub/h_new.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1",
        "_SEND_STATUS_API": "http://reporting.nrb-apps.com:8585/rep/pub/email_status.php?k=mP5Q2XYrK9E67Y1&rID=1&rv4=1",
        "_SAVE_PROCESS_API": "https://reporting.nrb-apps.com/pub/SaveProcess.php?k=mP5QXYrK9E67Y&rID=1&rv4=1",
        "_MAIN_API": "https://apps1.nrb-apps.com/pub/chk_usr1.php",
        "__CHECK_URL_PROGRAMM__": "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=z6vzw0ox&dl=1",
        "__SERVER_ZIP_URL_PROGRAM__": "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/master.zip",
        "__GET_PROXY_INFO__": "https://reporting.nrb-apps.com/pub/getInfoProxy.php",
        "SCENARIO_API": "https://reporting.nrb-apps.com/pub/ReportingV4/senario.php",
        "ENCRYPTED_PROXY_API": "https://example.com/",
    }

    SESSION_API_CONFIG = {
        "KEY": "mP5QXYrK9E67Y",
        "VALIDATION_REQUEST_ID": "4",
        "AUTHENTICATION_REQUEST_ID": "1",
        "APP_VERSION": "1",
        "AUTHENTICATION_LOGIN": "1",
    }

    SCENARIO_API = API_ENDPOINTS["SCENARIO_API"]
    ENCRYPTED_PROXY_API = API_ENDPOINTS["ENCRYPTED_PROXY_API"]
    SESSION_API_KEY = SESSION_API_CONFIG["KEY"]
    SESSION_VALIDATION_REQUEST_ID = SESSION_API_CONFIG["VALIDATION_REQUEST_ID"]
    SESSION_AUTHENTICATION_REQUEST_ID = SESSION_API_CONFIG["AUTHENTICATION_REQUEST_ID"]
    SESSION_APP_VERSION = SESSION_API_CONFIG["APP_VERSION"]
    SESSION_AUTHENTICATION_LOGIN = SESSION_API_CONFIG["AUTHENTICATION_LOGIN"]

    # ═══════════════════════════════════════════════════════════
    # 🔐 Paramètres de chiffrement
    # ═══════════════════════════════════════════════════════════

    ENCRYPTION_KEY_HEX = (
        "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
    )

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

    APPDATA = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    DATA_DIR = Path(APPDATA) / "AutoMailPro"
    SESSION_FILE = DATA_DIR / "session.txt"

    TOOLS_DIR = BASE_DIR / "Tools"
    # EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"

    PROFILES_DIR = TOOLS_DIR / "Profiles"
    CHROME_PROFILES = PROFILES_DIR / "chrome"
    FIREFOX_PROFILES = PROFILES_DIR / "firefox"
    EDGE_PROFILES = PROFILES_DIR / "edge"
    ICEDRAGON_PROFILES = PROFILES_DIR / "icedragon"
    COMODO_PROFILES = PROFILES_DIR / "comodo"

    # VERSION_LOCAL_EXT = os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt")
    VERSION_LOCAL_PROGRAMM = os.path.join(BASE_DIR, "config", "version.txt")

    CHROMIUM_BROWSER_PATHS = {
        "edge": {"profiles": EDGE_PROFILES},
        "icedragon": {"profiles": ICEDRAGON_PROFILES},
        "comodo": {"profiles": COMODO_PROFILES},
    }

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
    SECURE_PREFERENCES_TEMPLATE = ( r"C:\RepProxy\template_Profile\default\Secure Preferences" )
    FICHIER_LOCAL_STATE = r"C:\RepProxy\template_Profile\Local State"
    FICHIER_VARIATIONS = r"C:\RepProxy\template_Profile\Variations"

    EXTENTION_EX3_FIREFOX = r"C:\RepProxy\Ext3_Firefoxtest"
    VERSION_LOCAL_EX3_FIREFOX = os.path.join(EXTENTION_EX3_FIREFOX, "version.txt")
    MANIFEST_PATH_EX3_FIREFOX = os.path.join(EXTENTION_EX3_FIREFOX, "manifest.json")

    EXTENTION_EX3_CHROMIUM = r"C:\RepProxy\Ext3"
    MANIFEST_PATH_EX3 = os.path.join(EXTENTION_EX3_CHROMIUM, "manifest.json")
    VERSION_LOCAL_EX3 = os.path.join(EXTENTION_EX3_CHROMIUM, "version.txt")

    TEMPLATE_DIRECTORY_FIREFOX = os.path.join(  TOOLS_DIR, "extensions Templete", "ExtensionTemplateFirefox" )
    TEMPLATE_DIRECTORY_CHROMIUM = os.path.join( TOOLS_DIR, "extensions Templete", "Extention_Family_Chrome"  )

    LOGS_DIRECTORY = os.path.join(TOOLS_DIR, "logs")
    RESULT_FILE_PATH = os.path.join(TOOLS_DIR, "result.txt")

    APP_NAME = "SecureDesk"
    APPDATA_DIR = os.path.join(APPDATA, APP_NAME)
    FIREFOX_PROFILES_INI = os.path.join(APPDATA, "Mozilla", "Firefox", "profiles.ini")

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

    INTERFACE_UI = os.path.abspath(
        os.path.join(BASE_DIR, "resources", "ui", "interface.ui")
    )
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

    LOG_DEV_FILE = os.path.abspath(os.path.join(BASE_DIR, "Log/LogDev/my_project.json"))
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    _LOGGER_NAME = "automailpro.application"
    _LOGGER = None
    _LOGGER_LOCK = threading.Lock()
    _LOG_SEQUENCE = 0
    _LOG_RUN_ID = uuid.uuid4().hex[:12]
    _MAX_LOG_MESSAGE_LENGTH = 800

    _SENSITIVE_KEY_PATTERN = re.compile(
        r"(?i)([\"']?)(password|passwd|pass|secret|token|api[_-]?key|authorization|cookie|"
        r"proxy[_-]?login|private[_-]?key|access[_-]?key|session[_-]?(?:data|id)|"
        r"inserted[_-]?id|key[_-]?hex|encrypted)"
        r"\1\s*([:=])\s*([\"']?)([^,;\s}\]]+)"
    )
    _SENSITIVE_BLOCK_PATTERN = re.compile(
        r"(?is)(payload|command)\s*([:=])\s*(.+?)(?=(?:\s+\w[\w -]*\s*[:=])|$)"
    )
    _EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    _IP_PATTERN = re.compile(r"\b(?:25[0-5]\.){3}(?:25[0-5])\b")
    _URL_PATTERN = re.compile(r"\bhttps?://[^\s\]}>,]+", re.IGNORECASE)
    _PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:\\)[^\n\r|,;]+")

    @classmethod
    def _stable_identifier(cls, value: str, label: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[
            :12
        ]
        return f"<{label}:{digest}>"

    @classmethod
    def _redact_log_message(cls, message) -> str:
        text = str(message)

        def redact_key_value(match):
            return f"{match.group(1)}{match.group(2)}{match.group(3)}<redacted>"

        text = cls._SENSITIVE_KEY_PATTERN.sub(redact_key_value, text)
        text = cls._SENSITIVE_BLOCK_PATTERN.sub(
            lambda match: f"{match.group(1)}{match.group(2)}<redacted>", text
        )
        text = cls._URL_PATTERN.sub("<url:redacted>", text)
        text = cls._EMAIL_PATTERN.sub(
            lambda match: cls._stable_identifier(match.group(0).lower(), "email"), text
        )
        text = cls._IP_PATTERN.sub(
            lambda match: cls._stable_identifier(match.group(0), "ip"), text
        )
        text = cls._PATH_PATTERN.sub(
            lambda match: cls._stable_identifier(match.group(0), "path"), text
        )
        return " ".join(text.split())

    @classmethod
    def _prepare_log_message(cls, message) -> str:
        safe_message = cls._redact_log_message(message)
        if len(safe_message) <= cls._MAX_LOG_MESSAGE_LENGTH:
            return safe_message
        return (
            f"{safe_message[: cls._MAX_LOG_MESSAGE_LENGTH]}... "
            f"[truncated_length={len(safe_message)}]"
        )

    @classmethod
    def _get_logger(cls):
        if cls._LOGGER is not None:
            return cls._LOGGER

        with cls._LOGGER_LOCK:
            if cls._LOGGER is not None:
                return cls._LOGGER

            logger = logging.getLogger(cls._LOGGER_NAME)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            log_path = Path(cls.LOG_DEV_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                log_path,
                maxBytes=cls.LOG_MAX_BYTES,
                backupCount=cls.LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            if not logger.handlers:
                logger.addHandler(handler)
            cls._LOGGER = logger
            return logger

    @classmethod
    def write_log_event(cls, event: str, level: str = "INFO", **context):
        try:
            safe_context = {
                str(key): cls._prepare_log_message(value)
                for key, value in context.items()
            }
            cls._write_log_record({"event": event, "context": safe_context}, level)
        except (OSError, TypeError, ValueError):
            pass

    @classmethod
    def _write_log_record(cls, fields, level: str):
        with cls._LOGGER_LOCK:
            cls._LOG_SEQUENCE += 1
            sequence = cls._LOG_SEQUENCE
        record = {
            "sequence": sequence,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": str(level).upper(),
            "run_id": cls._LOG_RUN_ID,
            "process_id": os.getpid(),
            "thread": threading.current_thread().name,
            **fields,
        }
        cls._get_logger().log(
            getattr(logging, str(level).upper(), logging.INFO),
            json.dumps(record, ensure_ascii=False, separators=(",", ":")),
        )

    @classmethod
    def write_log_dev_file(cls, message: str, level: str = "INFO"):
        try:
            cls._write_log_record({"message": cls._prepare_log_message(message)}, level)
        except (OSError, TypeError, ValueError):
            pass

    @classmethod
    def writeLogDevFile(cls, message: str, level: str = "INFO"):
        cls.write_log_dev_file(message, level)

    @classmethod
    def clear_log(cls):
        try:
            if cls._LOGGER is not None:
                for handler in cls._LOGGER.handlers:
                    handler.flush()
            log_path = Path(cls.LOG_DEV_FILE)
            if log_path.exists():
                open(log_path, "w", encoding="utf-8").close()
            else:
                cls.write_log_dev_file("Fichier log inexistant", "WARNING")
        except Exception as exc:
            cls.write_log_event(
                "log_clear_failed",
                "ERROR",
                exception_type=type(exc).__name__,
                error=str(exc),
            )

    @classmethod
    def clearLog(cls):
        cls.clear_log()

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
        ]
        for directory in directories:
            path = Path(directory)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    cls.write_log_event(
                        "directory_creation_failed",
                        "ERROR",
                        directory=str(path),
                        exception_type=type(exc).__name__,
                        error=str(exc),
                    )

    @classmethod
    def ensureDirectories(cls):
        cls.ensure_directories()

    @classmethod
    def get_encryption_key_bytes(cls) -> bytes:
        return bytes.fromhex(cls.ENCRYPTION_KEY_HEX)

    @classmethod
    def getEncryptionKeyBytes(cls) -> bytes:
        return cls.get_encryption_key_bytes()

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
            cls.write_log_dev_file("Node.js already installed", "INFO")
            return True

        cls.write_log_dev_file("Node.js not installed. Trying to install via Chocolatey...", "INFO")

        if shutil.which("choco") is None:
            cls.write_log_dev_file("Chocolatey not found. Installing...", "INFO")
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
            except subprocess.CalledProcessError as exc:
                cls.write_log_event(
                    "node_setup_failed",
                    "ERROR",
                    action="choco_install",
                    exception_type=type(exc).__name__,
                    error=str(exc),
                )
                return False

        try:
            subprocess.run(["choco", "install", "nodejs-lts", "-y"], check=True)
            return True
        except subprocess.CalledProcessError as exc:
            cls.write_log_event(
                "node_setup_failed",
                "ERROR",
                action="choco_install_node",
                exception_type=type(exc).__name__,
                error=str(exc),
            )
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
            cls.write_log_dev_file("Unable to continue without Node.js.", "WARNING")
            return
        if shutil.which("npm") is None:
            cls.write_log_dev_file("npm is not installed.", "ERROR")
            return
        if shutil.which("web-ext") is not None:
            cls.write_log_dev_file("web-ext already installed", "INFO")
            return
        try:
            npm_path = shutil.which("npm")
            subprocess.run([npm_path, "install", "--global", "web-ext"], check=True)
        except subprocess.CalledProcessError as exc:
            cls.write_log_event( "web_ext_install_failed",  "ERROR",  action="npm_install",   exception_type=type(exc).__name__,  error=str(exc) )

    @classmethod
    def ensureWebExtInstalled(cls):
        cls.ensure_web_ext_installed()


# Création d’une instance unique utilisée dans tout le projet
settings = Settings()

# Vérification et création des dossiers de base
settings.ensure_directories()
