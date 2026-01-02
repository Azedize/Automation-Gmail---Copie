# browser_manager.py

import os
import sys
import json
import subprocess
import configparser
from typing import Optional, List, Dict, Any
import psutil
import winreg
import win32gui
import win32process
import win32con
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
    from Log import DevLogger
except ImportError as e:
    DevLogger.error(f"Error importing modules: {e}")


class BrowserManager:

    @staticmethod
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
                        DevLogger.info(f"✅ Navigateur trouvé : {path}")
                        return path
            except FileNotFoundError:
                continue
            except Exception as e:
                DevLogger.error(f"⚠️ Erreur registre ({hive}): {e}")

        DevLogger.error(f"❌ Navigateur {exe_name} introuvable")
        return None

    # ---------------------- Firefox ----------------------
    @staticmethod
    def _get_firefox_profiles() -> Dict[str, str]:
        ini_path = os.path.join(Settings.APPDATA, 'Mozilla', 'Firefox', 'profiles.ini')
        if not ValidationUtils.path_exists(ini_path):
            return {}

        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')

        base_dir = os.path.dirname(ini_path)
        profiles = {}
        for section in config.sections():
            if section.startswith('Profile'):
                name = config.get(section, 'Name', fallback=None)
                path = config.get(section, 'Path', fallback=None)
                is_rel = config.getint(section, 'IsRelative', fallback=1)
                if name and path:
                    full_path = os.path.join(base_dir, path) if is_rel else path
                    profiles[name] = os.path.normpath(full_path)
        return profiles

    @staticmethod
    def create_firefox_profile(profile_name: str) -> Optional[str]:
        firefox_path = BrowserManager.get_browser_path("firefox.exe")
        if not firefox_path:
            DevLogger.error("❌ Firefox introuvable.")
            return None

        existing_profiles = BrowserManager._get_firefox_profiles()
        DevLogger.info("Profils existants avant création :", list(existing_profiles.keys()))

        profile_dir = os.path.join(Settings.FIREFOX_PROFILES, profile_name)
        os.makedirs(Settings.FIREFOX_PROFILES, exist_ok=True)

        if ValidationUtils.path_exists(profile_dir):
            DevLogger.info(f"✅ Profil '{profile_name}' déjà existant : {profile_dir}")
            return profile_dir

        cmd = f"{profile_name} {profile_dir}"
        result = subprocess.run([firefox_path, '--CreateProfile', cmd],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        if result.returncode != 0:
            DevLogger.error(f"❌ Échec création (code {result.returncode})")
            DevLogger.error(result.stderr.strip())
            return None

        if ValidationUtils.path_exists(profile_dir):
            DevLogger.info(f"✅ Profil créé : {profile_dir}")
            return profile_dir

        DevLogger.error("❌ Le dossier du profil n'a pas été trouvé après création.")
        return None

    @staticmethod
    def Get_Firefox_Profiles_In_Use() -> List[Dict[str, str]]:
        profiles = []
        if not ValidationUtils.path_exists(Settings.FIREFOX_PROFILES):
            return profiles

        for folder in os.listdir(Settings.FIREFOX_PROFILES):
            path = os.path.join(Settings.FIREFOX_PROFILES, folder)
            lock_file = os.path.join(path, 'parent.lock')
            if os.path.isdir(path) and os.pa(lock_file):
                profiles.append({'name': folder, 'path': path})
        return profiles

    @staticmethod
    def Get_Profile_By_Pid(pid: int, active_profiles: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        try:
            proc = psutil.Process(pid)
            for f in proc.open_files():
                for profile in active_profiles:
                    if os.path.commonpath([f.path, profile['path']]) == profile['path']:
                        return profile
                    if profile['name'] in f.path:
                        return profile
        except Exception:
            return None
        return None

    @staticmethod
    def Get_Firefox_Windows() -> List[Dict[str, Any]]:
        active_profiles = BrowserManager.Get_Firefox_Profiles_In_Use()
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetClassName(hwnd) == 'MozillaWindowClass':
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    profile = BrowserManager.Get_Profile_By_Pid(pid, active_profiles)
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

        win32gui.EnumWindows(callback, None)
        return windows

    @staticmethod
    def Close_Windows_By_Profiles(profiles_list: List[Dict[str, str]]):
        target_profiles = {p["profile"] for p in profiles_list}
        all_windows = BrowserManager.Get_Firefox_Windows()
        for window in all_windows:
            if window["profile"] in target_profiles:
                try:
                    win32gui.PostMessage(window["hwnd"], win32con.WM_CLOSE, 0, 0)
                    DevLogger.info(f"✅ Fermeture : {window['profile']} - {window['title']}")
                except Exception as e:
                    DevLogger.error(f"❌ Erreur fermeture {window['profile']}: {e}")

    # ---------------------- Chrome ----------------------
    @staticmethod
    def Run_Browser_Create_Profile(profile_name: str):
        profile_path = os.path.join(Settings.CHROME_PROFILES, profile_name)
        os.makedirs(profile_path, exist_ok=True)
        print(f"📂 Profil Chrome : {profile_path}")

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-sync")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome lancé")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erreur lancement Chrome : {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                print("✅ Chrome fermé")


    # ---------------------- JSON Utilities ----------------------
    @staticmethod
    def Search_Keys(data: Any, search_keys: List[str], results: List[Dict[str, Any]]):
        if isinstance(data, dict):
            for k, v in data.items():
                if k in search_keys:
                    results.append({k: v})
                BrowserManager.Search_Keys(v, search_keys, results)
        elif isinstance(data, list):
            for item in data:
                BrowserManager.Search_Keys(item, search_keys, results)

    @staticmethod
    def Upload_EXTENSION_PROXY(profile_name: str, search_keys: List[str], results: List[Dict[str, Any]]):
        path_file = os.path.join(Settings.CONFIG_PROFILE, profile_name, "Secure Preferences")
        if not ValidationUtils.path_exists(path_file):
            DevLogger.error(f"❌ Secure Preferences introuvable pour {profile_name}")
            return None

        try:
            with open(path_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.clear()
            BrowserManager.Search_Keys(data, search_keys, results)
            DevLogger.info(f"📌 Résultats pour {profile_name}: {results}")
            return results
        except Exception as e:
            DevLogger.error(f"❌ Erreur traitement Secure Preferences: {e}")
            return None




BrowserManager = BrowserManager()
