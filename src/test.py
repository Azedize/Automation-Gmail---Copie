import winreg
import os
from typing import Optional


class ValidationUtils:
    @staticmethod
    def path_exists(path: str) -> bool:
        return os.path.exists(path)


class Settings:
    SUPPORTED_BROWSERS = {
        "chrome": {
            "exe_name": "chrome.exe"
        }
    }


def get_browser_path(browser_name_or_exe: str):
    exe_name = Settings.SUPPORTED_BROWSERS.get(browser_name_or_exe.lower(), {}).get("exe_name", browser_name_or_exe)

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
                    return path
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️ خطأ في الريجستري: {e}")

    return None


# =========================
# 🔍 TEST
# =========================



 
if __name__ == "__main__":
    chrome_path = get_browser_path("chrome")

    if chrome_path:
        print("✅ تم العثور على Google Chrome")
        print("📍 المسار:", chrome_path)
    else:
        print("❌ لم يتم العثور على Google Chrome")
