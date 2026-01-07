import os
import sys
import json
from pathlib import Path


class Settings:
    # ═══════════════════════════════════════════════════════════
    # 🔐 DATA AUTH
    # ═══════════════════════════════════════════════════════════

    KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
    KEY = bytes.fromhex(KEY_HEX)

    # ═══════════════════════════════════════════════════════════
    # 🌐 SUPPORTED BROWSERS
    # ═══════════════════════════════════════════════════════════

    SUPPORTED_BROWSERS = {
        "chrome": {"exe_name": "chrome.exe", "display_name": "Google Chrome"},
        "firefox": {"exe_name": "firefox.exe", "display_name": "Mozilla Firefox"},
        "edge": {"exe_name": "msedge.exe", "display_name": "Microsoft Edge"},
        "icedragon": {"exe_name": "dragon.exe", "display_name": "Ice Dragon"},
        "comodo": {"exe_name": "chrome.exe", "display_name": "Comodo Dragon"},
    }

    # ═══════════════════════════════════════════════════════════
    # 🌐 API
    # ═══════════════════════════════════════════════════════════

    API_BASE_URL = "https://reporting.nrb-apps.com"
    API_TIMEOUT = 15
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 5

    HEADER = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    }

    # ═══════════════════════════════════════════════════════════
    # 📁 PATHS (Pathlib only)
    # ═══════════════════════════════════════════════════════════

    BASE_DIR = Path(__file__).resolve().parent.parent
    RESOURCES_DIR = BASE_DIR / "resources"
    UI_DIR = RESOURCES_DIR / "ui"
    TEMPLATES_DIR = RESOURCES_DIR / "templates"
    ICONS_DIR = RESOURCES_DIR / "icons"

    TOOLS_DIR = BASE_DIR / "Tools"
    EXTENSIONS_DIR = TOOLS_DIR / "Extensions"
    PROFILES_DIR = TOOLS_DIR / "Profiles"

    CHROME_PROFILES = PROFILES_DIR / "chrome"
    FIREFOX_PROFILES = PROFILES_DIR / "firefox"
    FAMILY_CHROME_DIR_PROFILES = PROFILES_DIR / "Family_Chrome"

    EXTENTIONS_DIR_FIREFOX = TOOLS_DIR / "extensions" / "FIREFOX_EXTENTIONS"
    EXTENSIONS_DIR_FAMILY_CHROME = TOOLS_DIR / "extensions" / "FAMILY_CHROME_EXTENTIONS"

    LOGS_DIRECTORY = TOOLS_DIR / "logs"
    RESULT_FILE_PATH = TOOLS_DIR / "result.txt"

    APPDATA = Path(os.getenv("APPDATA", Path.home()))
    APP_NAME = "AutoMailPro"
    APPDATA_DIR = APPDATA / APP_NAME
    SESSION_PATH = APPDATA_DIR / "session.txt"

    # ═══════════════════════════════════════════════════════════
    # 🔑 ENCRYPTION
    # ═══════════════════════════════════════════════════════════

    ENCRYPTION_KEY_HEX = KEY_HEX
    AES_BLOCK_SIZE = 128
    AES_KEY_LENGTH = 32
    AES_IV_LENGTH = 16
    PBKDF2_ITERATIONS = 100_000

    # ═══════════════════════════════════════════════════════════
    # 🖥️ UI SETTINGS
    # ═══════════════════════════════════════════════════════════

    WINDOW_WIDTH = 1710
    WINDOW_HEIGHT = 1005

    PRIMARY_COLOR = "#669bbc"
    SECONDARY_COLOR = "#b2cddd"
    ACCENT_COLOR = "#d90429"

    FONT_FAMILY = "Times New Roman"
    FONT_SIZE_SMALL = 12
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_LARGE = 16

    # ═══════════════════════════════════════════════════════════
    # ⚙️ APP SETTINGS
    # ═══════════════════════════════════════════════════════════

    SESSION_VALIDITY_DAYS = 2
    SESSION_TIMEZONE = "Africa/Casablanca"

    # ═══════════════════════════════════════════════════════════
    # 🛠️ PATH INITIALIZATION (CRITICAL)
    # ═══════════════════════════════════════════════════════════

    @classmethod
    def ensure_directories(cls):
        """
        🔍 Vérifie et crée tous les dossiers nécessaires
        ❌ Empêche les erreurs Windows (file vs directory)
        """

        directories = [
            cls.APPDATA_DIR,
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

    # ═══════════════════════════════════════════════════════════
    # 🧠 UTILS
    # ═══════════════════════════════════════════════════════════

    @classmethod
    def get_encryption_key_bytes(cls) -> bytes:
        return bytes.fromhex(cls.ENCRYPTION_KEY_HEX)

    @classmethod
    def find_pythonw(cls):
        base_dir = Path(sys.executable).parent
        candidate = base_dir / "pythonw.exe"
        if candidate.exists():
            return candidate

        for path in os.environ.get("PATH", "").split(os.pathsep):
            candidate = Path(path.strip('"')) / "pythonw.exe"
            if candidate.exists():
                return candidate

        return None


# ═══════════════════════════════════════════════════════════
# 🚀 INITIALIZATION
# ═══════════════════════════════════════════════════════════

settings = Settings()
Settings.ensure_directories()
