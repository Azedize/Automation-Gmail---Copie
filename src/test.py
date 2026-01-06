import os
import time
import subprocess
import winreg
import psutil
from typing import Optional


# ============================================================
# 🔧 SETTINGS
# ============================================================

class Settings:
    SUPPORTED_BROWSERS = {
        "chrome": {
            "exe_name": "chrome.exe"
        }
    }


# ============================================================
# 🧠 LOGGER SIMPLE
# ============================================================

class DevLogger:
    @staticmethod
    def info(msg: str):
        print(msg)

    @staticmethod
    def warning(msg: str):
        print(msg)

    @staticmethod
    def error(msg: str):
        print(msg)


# ============================================================
# 🛡️ VALIDATION
# ============================================================

class ValidationUtils:
    @staticmethod
    def path_exists(path: str) -> bool:
        return os.path.exists(path)


# ============================================================
# 🔍 CHROME PATH FROM REGISTRY
# ============================================================

def get_browser_path(browser_name_or_exe: str) -> Optional[str]:
    """Récupère le chemin d'un navigateur via le registre Windows"""

    exe_name = Settings.SUPPORTED_BROWSERS.get(
        browser_name_or_exe.lower(), {}
    ).get("exe_name", browser_name_or_exe)

    DevLogger.info(f"🔍 Recherche de l'exécutable : {exe_name}")

    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_CURRENT_USER, winreg.KEY_READ),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ),
    ]

    key_app_paths = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"

    for hive, access in registry_paths:
        try:
            with winreg.OpenKey(hive, key_app_paths, 0, access) as key_obj:
                path, _ = winreg.QueryValueEx(key_obj, None)
                if path and ValidationUtils.path_exists(path):
                    DevLogger.info(f"✅ Chrome trouvé : {path}")
                    return path
        except FileNotFoundError:
            continue
        except Exception as e:
            DevLogger.error(f"⚠️ Erreur registre : {e}")

    DevLogger.error("❌ Chrome introuvable")
    return None


# ============================================================
# 🚀 LAUNCH CHROME WITH PROFILE
# ============================================================

def launch_chrome_with_profile(
    profile_name: str,
    user_data_dir: str,
    url: str
):
    chrome_path = get_browser_path("chrome")

    if not chrome_path:
        return

    # ✅ Création automatique du user-data-dir si inexistant
    if not os.path.isdir(user_data_dir):
        DevLogger.warning(f"📂 Création user-data-dir : {user_data_dir}")
        os.makedirs(user_data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_name}",
        "--new-window",
        url
    ]

    DevLogger.info("🚀 Lancement Chrome")
    DevLogger.info(f"   👤 Profil : {profile_name}")
    DevLogger.info(f"   📂 UserData : {user_data_dir}")

    subprocess.Popen(cmd, shell=False)


# ============================================================
# ❌ CLOSE CHROME BY PROFILE (NO PID)
# ============================================================

def close_chrome_by_profile_after_delay(
    profile_name: str,
    user_data_dir: str,
    delay: int = 10
):
    DevLogger.info(f"⏳ Attente {delay}s avant fermeture du profil : {profile_name}")
    time.sleep(delay)

    closed = False

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] != "chrome.exe":
                continue

            cmdline = " ".join(proc.info['cmdline'])

            if (
                f"--profile-directory={profile_name}" in cmdline
                and f"--user-data-dir={user_data_dir}" in cmdline
            ):
                DevLogger.info(f"❌ Fermeture Chrome (profil={profile_name})")
                proc.terminate()
                closed = True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not closed:
        DevLogger.warning("⚠️ Aucun Chrome trouvé pour ce profil")


# ============================================================
# ▶️ MAIN
# ============================================================

if __name__ == "__main__":

    PROFILE_NAME = "User01"
    USER_DATA_DIR = r"D:\ChromeProfiles\User01"  # dossier sera créé automatiquement si inexistant
    URL = "https://www.google.com"

    launch_chrome_with_profile(
        profile_name=PROFILE_NAME,
        user_data_dir=USER_DATA_DIR,
        url=URL
    )

    close_chrome_by_profile_after_delay(
        profile_name=PROFILE_NAME,
        user_data_dir=USER_DATA_DIR,
        delay=10
    )
