import os
import subprocess
import winreg
from typing import Optional


# ==========================================================
# 🔍 Recherche du chemin de Google Chrome
# ==========================================================

def get_chrome_path() -> Optional[str]:
    exe_name = "chrome.exe"

    registry_hives = [
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
        (winreg.HKEY_CURRENT_USER, winreg.KEY_READ),
    ]

    key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"

    # 🔹 Recherche via registre
    for hive, access in registry_hives:
        try:
            with winreg.OpenKey(hive, key_path, 0, access) as key:
                chrome_path, _ = winreg.QueryValueEx(key, None)
                if chrome_path and os.path.exists(chrome_path):
                    return chrome_path
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[REGISTRY ERROR] {e}")

    # 🔹 Fallback : chemins standards
    fallback_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for path in fallback_paths:
        if os.path.exists(path):
            return path

    return None




# ==========================================================
# 📁 Création du dossier de profil Chrome
# ==========================================================

def ensure_chrome_profile(base_dir: str, profile_name: str) -> str:
    os.makedirs(base_dir, exist_ok=True)

    profile_path = os.path.join(base_dir, profile_name)
    os.makedirs(profile_path, exist_ok=True)

    return profile_path



# ==========================================================
# 🚀 Lancer Chrome avec un profil spécifique
# ==========================================================

def launch_chrome_with_profile(profile_name: str):
    chrome_path = get_chrome_path()

    if not chrome_path:
        raise FileNotFoundError("❌ Google Chrome introuvable sur le système")


    CHROME_PROFILES_DIR = r"C:\ChromeProfiles\Profile1"

    ensure_chrome_profile(CHROME_PROFILES_DIR, profile_name)

    command = [
        chrome_path,
        f"--user-data-dir={CHROME_PROFILES_DIR}",  
        f"--profile-directory={profile_name}",     
        "--lang=en-US",
        "--no-first-run",
        "--start-maximized",
    ]

    print("🚀 Lancement Chrome avec la commande :")
    print(" ".join(command))
    
    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS
    )
    




if __name__ == "__main__":
    profile_name = "Profile1"
    launch_chrome_with_profile(profile_name)


