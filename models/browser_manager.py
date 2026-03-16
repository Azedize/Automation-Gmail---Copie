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
import shutil
from typing import List, Dict, Any, Optional


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    # print(f"Error importing modules: {e}")
    pass


class BrowserManager:

    
    
    @staticmethod
    def get_browser_path(browser_name_or_exe: str) -> Optional[str]:
        """Récupère le chemin d'un navigateur via le registre Windows"""
        exe_name = Settings.SUPPORTED_BROWSERS.get(
            browser_name_or_exe.lower(), {}
        ).get("exe_name", browser_name_or_exe)
        #print(f"🔍 Recherche de l'exécutable : {exe_name}")

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
                        #print(f"✅ Navigateur trouvé : {path}")
                        return path
            except FileNotFoundError:
                Settings.WRITE_LOG_DEV_FILE(f"Navigateur introuvable ({hive})", "INFO")
                continue
            except Exception as e:
                Settings.WRITE_LOG_DEV_FILE(f"Erreur registre ({hive}): {e}", "ERROR")
                # print(f"⚠️ Erreur registre ({hive}): {e}")

        #print(f"❌ Navigateur {exe_name} introuvable")
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
            #print("❌ Firefox introuvable.")
            Settings.WRITE_LOG_DEV_FILE("Firefox introuvable.", "ERROR")
            return None

        existing_profiles = BrowserManager._get_firefox_profiles()
        #print("Profils existants avant création :", list(existing_profiles.keys()))

        profile_dir = os.path.join(Settings.FIREFOX_PROFILES, profile_name)
        os.makedirs(Settings.FIREFOX_PROFILES, exist_ok=True)

        if ValidationUtils.path_exists(profile_dir):
            #print(f"✅ Profil '{profile_name}' déjà existant : {profile_dir}")
            Settings.WRITE_LOG_DEV_FILE(f"Profil '{profile_name}' deja existant : {profile_dir}", "INFO")
            return profile_dir

        cmd = f"{profile_name} {profile_dir}"
        result = subprocess.run([firefox_path, '--CreateProfile', cmd], stdout=subprocess.PIPE,  stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            #print(f"❌ Échec création (code {result.returncode})")
            #print(result.stderr.strip())
            Settings.WRITE_LOG_DEV_FILE(f"Echec creation (code {result.returncode})", "ERROR")
            return None

        if ValidationUtils.path_exists(profile_dir):
            #print(f"✅ Profil créé : {profile_dir}")
            Settings.WRITE_LOG_DEV_FILE(f"Profil cree : {profile_dir}", "INFO")
            return profile_dir

        #print("❌ Le dossier du profil n'a pas été trouvé après création.")
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
            Settings.WRITE_LOG_DEV_FILE("Profil introuvable.", "ERROR")
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
                    Settings.WRITE_LOG_DEV_FILE("Profil introuvable.", "ERROR")
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
                    #print(f"✅ Fermeture : {window['profile']} - {window['title']}")
                except Exception as e:
                    Settings.WRITE_LOG_DEV_FILE(f"Erreur fermeture {window['profile']} : {e}", "ERROR")
                    # print(f"❌ Erreur fermeture {window['profile']}: {e}")

    # ---------------------- Chrome ----------------------
    
    
    

    
    #=======================================================
    # Run_Browser_Create_Profile
    #=======================================================
    # Crée un profil Chrome avec le nom spécifié et lance temporairement le navigateur.
    # Configure les options du profil et ferme le navigateur après quelques secondes.
    
    @staticmethod
    def Run_Browser_Create_Profile(profile_name: str):
        profile_path = os.path.join(Settings.CHROME_PROFILES, profile_name)
        os.makedirs(profile_path, exist_ok=True)
        #print(f"📂 Profil Chrome : {profile_path}")

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-sync")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            #print("✅ Chrome lancé")
            time.sleep(2)
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lancement Chrome : {e}", "ERROR")
            # print(f"❌ Erreur lancement Chrome : {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                # print("✅ Chrome fermé")


    # ---------------------- JSON Utilities ----------------------
    
    
    
    
    #=======================================================
    # Search_Keys
    #=======================================================
    # Parcourt récursivement un JSON (dict ou list),
    # cherche les clés spécifiées et ajoute les résultats dans la liste fournie.
    
    @staticmethod
    def Search_Keys(data: Any, search_keys: List[str], results: List[Dict[str, Any]], path_trace: str = ""):
        try:
            if isinstance(data, dict):
                for k, v in data.items():
                    current_path = f"{path_trace}/{k}" if path_trace else k
                    if k in search_keys:
                        results.append({k: v})
                        #print(f"🔑 Clé trouvée : {current_path} ➜ Valeur : {v}")
                    BrowserManager.Search_Keys(v, search_keys, results, current_path)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    current_path = f"{path_trace}[{idx}]"
                    BrowserManager.Search_Keys(item, search_keys, results, current_path)
        except Exception as e:
            # print(f"💥 Erreur lors de la recherche des clés à {path_trace}: {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la recherche des clés à {path_trace} : {e}", "ERROR")
            


    #=======================================================
    # Upload_EXTENSION_PROXY
    #=======================================================
    # Vérifie et lit le fichier 'Secure Preferences' d'un profil,
    # recherche les clés spécifiées et retourne la liste des résultats si trouvés,
    # sinon retourne None.
    
    
    @staticmethod

    def Upload_EXTENSION_PROXY(profile_name: str, search_keys: List[str], results: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        path_file = os.path.join(Settings.CONFIG_PROFILE, profile_name, "Secure Preferences")
        print(f"[DEBUG] Vérification du fichier Secure Preferences : {path_file}")

        if not ValidationUtils.path_exists(path_file):
            print(f"[ERROR] Fichier introuvable pour le profil {profile_name}")
            Settings.WRITE_LOG_DEV_FILE(f"Fichier introuvable pour le profil {profile_name}", "ERROR")
            return None

        try:
            print(f"[DEBUG] Lecture du fichier JSON en cours pour le profil {profile_name}...")
            with open(path_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("[DEBUG] Lecture réussie du fichier JSON.")

            results.clear()
            print(f"[DEBUG] Début de la recherche des clés : {search_keys}")
            BrowserManager.Search_Keys(data, search_keys, results)

            if results:
                print(f"[INFO] Résultats trouvés pour {profile_name}:")
                for idx, item in enumerate(results, start=1):
                    print(f"   {idx}. {item}")
                return results  # retourne la liste si des résultats trouvés
            else:
                print(f"[WARNING] Aucun résultat trouvé pour les clés spécifiées pour {profile_name}")
                return None  # retourne None si aucun résultat

        except json.JSONDecodeError as e:
            print(f"[ERROR] Erreur JSON : impossible de décoder le fichier {path_file} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur JSON : impossible de décoder le fichier {path_file} : {e}", "ERROR")
        except PermissionError:
            print(f"[ERROR] Permission refusée pour lire le fichier {path_file}")
            Settings.WRITE_LOG_DEV_FILE(f"Permission refusée pour lire le fichier {path_file}", "ERROR")
        except FileNotFoundError:
            print(f"[ERROR] Fichier non trouvé (malgré la vérification précédente) : {path_file}")
            Settings.WRITE_LOG_DEV_FILE(f"Fichier non trouvé (malgré la vérification précedente) : {path_file}", "ERROR")
        except Exception as e:
            print(f"[ERROR] Erreur inattendue lors du traitement de {path_file} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur inattendue lors du traitement de {path_file} : {e}", "ERROR")

        return None  



    @staticmethod
    def UpdateChromeProfileFromTemplate(profile_name: str):
        """
        Copie les fichiers template dans le profil Chrome cible après suppression des anciens fichiers.
        Affichage détaillé pour debug et logging.
        """
        try:
            # 📂 Définir chemins cibles
            profile_dir = os.path.join(Settings.CHROME_PROFILES, profile_name)
            secure_preferences_path = os.path.join(profile_dir, "Secure Preferences")
            local_state_path = os.path.join(profile_dir, "Local State")
            variations_path = os.path.join(profile_dir, "Variations")

            print(f"[DEBUG] Profil cible : {profile_dir}")
            print(f"[DEBUG] Secure Preferences : {secure_preferences_path}")
            print(f"[DEBUG] Local State : {local_state_path}")
            print(f"[DEBUG] Variations : {variations_path}")

            # 🔹 Supprimer fichiers existants si présents
            for path in [secure_preferences_path, local_state_path, variations_path]:
                if os.path.exists(path):
                    try:
                        if os.path.isdir(path):
                            print(f"[DEBUG] Suppression du dossier existant : {path}")
                            shutil.rmtree(path)
                        else:
                            print(f"[DEBUG] Suppression du fichier existant : {path}")
                            os.remove(path)
                    except Exception as e:
                        print(f"[ERROR] Erreur suppression fichier {path} : {e}")
                        Settings.WRITE_LOG_DEV_FILE(f"Erreur suppression fichier {path} : {e}", "ERROR")

            # 🔹 Vérifier que les templates existent avant copie
            if not os.path.exists(Settings.SECURE_PREFERENCES_TEMPLATE):
                raise FileNotFoundError(f"Template Secure Preferences introuvable : {Settings.SECURE_PREFERENCES_TEMPLATE}")
            if not os.path.exists(Settings.FICHIER_LOCAL_STATE):
                raise FileNotFoundError(f"Template Local State introuvable : {Settings.FICHIER_LOCAL_STATE}")
            if not os.path.isdir(Settings.FICHIER_VARIATIONS):
                raise FileNotFoundError(f"Template Variations introuvable ou pas un dossier : {Settings.FICHIER_VARIATIONS}")

            # 🔹 Copier fichiers templates
            print(f"[DEBUG] Copie de SECURE_PREFERENCES_TEMPLATE vers {os.path.join(profile_dir, profile_name)}")
            shutil.copy2(Settings.SECURE_PREFERENCES_TEMPLATE, os.path.join(profile_dir, profile_name))

            print(f"[DEBUG] Copie de FICHIER_LOCAL_STATE vers {profile_dir}")
            shutil.copy2(Settings.FICHIER_LOCAL_STATE, profile_dir)

            print(f"[DEBUG] Copie de FICHIER_VARIATIONS vers {profile_dir}")
            shutil.copytree(Settings.FICHIER_VARIATIONS, os.path.join(profile_dir, "Variations"))

            print(f"[INFO] Mise à jour du profil {profile_name} effectuée avec succès.")
            Settings.WRITE_LOG_DEV_FILE(f"Mise à jour du profil {profile_name} effectuée avec succès.", "INFO")
            return True

        except Exception as e:
            print(f"[ERROR] Erreur lors de la mise à jour du profil {profile_name} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la mise à jour du profil {profile_name} : {e}", "ERROR")
            return False




    
    
    @staticmethod
    def close_chrome_profile(profile_name: str, user_data_dir: str):
        closed_any = False

        # Parcours tous les process Chrome
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] != 'chrome.exe':
                    continue

                cmdline = " ".join(proc.info['cmdline'])
                
                # Vérifie que le profil et le user-data-dir correspondent
                if f"--profile-directory={profile_name}" in cmdline and f"--user-data-dir={user_data_dir}" in cmdline:
                    proc.terminate()  # fermeture propre
                    closed_any = True

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                Settings.WRITE_LOG_DEV_FILE(f"ERREUR CRITIQUE lors de la fermeture du profil {profile_name}", "ERROR")
                continue

        return closed_any
    


# le programme is runing dans une interface logique et graphique et va lancer des script capable de reduire des interfcaes intermedaires 

    
BrowserManager = BrowserManager()
