# browser_manager.py

import os
import sys
import json
import subprocess
import configparser
import traceback
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
from pathlib import Path
from typing import List, Dict, Any, Optional


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__} : {e}")
    sys.exit(1)  # quitte immédiatement le script avec un code d'erreur


class BrowserManager:
    
    # ═══════════════════════════════════════════════════════════
    # 🌐 validate_and_setup_browser (from AppV2.Process_Browser)
    # ═══════════════════════════════════════════════════════════
    @staticmethod
    def validate_and_setup_browser(window, selected_browser: str) -> bool:
        """
        Valide et configure le navigateur avant extraction.
        
        Effectue les vérifications suivantes:
        1️⃣ Vérification du navigateur supporté (Chrome uniquement actuellement)
        2️⃣ Vérification du dossier de configuration
        3️⃣ Vérification et chargement du fichier secure_preferences
        4️⃣ Validation des clés JSON requises
        5️⃣ Vérification et mise à jour de l'extension
        
        Args:
            window: Fenêtre principale (pour les messages d'erreur UI)
            selected_browser: Nom du navigateur sélectionné
            
        Returns:
            bool: True si succès, False sinon
        """
        from Update import UpdateManager
        from ui_utils import UIManager
        
        # 1️⃣ Vérification du navigateur
        if selected_browser.lower() != "chrome":
            Settings.WRITE_LOG_DEV_FILE(f"Unsupported browser: {selected_browser}", "WARNING")
            return False

        # 2️⃣ Vérification du dossier de configuration
        config_profile = Settings.CONFIG_PROFILE
        if not os.path.exists(config_profile):
            Settings.WRITE_LOG_DEV_FILE(f"Configuration folder not found: {config_profile}", "WARNING")
            return False

        # 3️⃣ Vérification du fichier secure_preferences
        secure_prefs = Settings.SECURE_PREFERENCES_TEMPLATE
        if not os.path.exists(secure_prefs):
            Settings.WRITE_LOG_DEV_FILE(f"Secure preferences file not found: {secure_prefs}", "WARNING")
            return False

        # Lecture du fichier JSON
        try:
            with open(secure_prefs, "r", encoding="utf-8") as f:
                data = json.load(f)
            Settings.WRITE_LOG_DEV_FILE(f"Secure preferences file loaded successfully: {secure_prefs}", "INFO")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Error reading JSON file: {e}\n{traceback.format_exc()}", "ERROR")
            return False

        # 4️⃣ Vérification des clés JSON
        required_keys = Settings.CLES_RECHERCHE
        results_keys = []
        Settings.WRITE_LOG_DEV_FILE(f"Searching JSON for required keys: {required_keys}", "INFO")
        BrowserManager.Search_Keys(data, required_keys, results_keys)

        found_keys = [list(d.keys())[0] for d in results_keys]
        found_key_details = [
            (
                f"{list(d.keys())[0]} at {next(iter(d.values()))['path']}"
                if isinstance(next(iter(d.values())), dict) and "path" in next(iter(d.values()))
                else str(list(d.keys())[0])
            )
            for d in results_keys
        ]
        missing_keys = [key for key in required_keys if key not in found_keys]

        Settings.WRITE_LOG_DEV_FILE(f"Found keys: {found_keys}", "INFO")
        Settings.WRITE_LOG_DEV_FILE(f"Found key details: {found_key_details}", "INFO")
        Settings.WRITE_LOG_DEV_FILE(f"Total keys found: {len(found_keys)}", "INFO")

        if missing_keys:
            detailed_error = f"Missing keys in secure_preferences JSON file:\n"
            detailed_error += f"  - Required keys: {', '.join(required_keys)}\n"
            detailed_error += f"  - Found keys: {', '.join(found_keys) if found_keys else 'NONE'}\n"
            detailed_error += f"  - Missing keys: {', '.join(missing_keys)}\n"
            detailed_error += f"  - File path: {secure_prefs}\n"
            detailed_error += f"  - Search results detail: {found_key_details}"

            Settings.WRITE_LOG_DEV_FILE(detailed_error, "ERROR")
            UIManager.Show_Critical_Message(
                window,
                "Configuration Error",
                "The Chrome configuration file is missing required Settings.\n\n"
                "Please verify your configuration and try again.\n"
                "If the problem persists, please contact Support.",
                message_type="critical",
            )
            return False

        Settings.WRITE_LOG_DEV_FILE("All required JSON keys were found", "SUCCESS")

        # 5️⃣ Vérification et mise à jour de l'extension
        ext_path = Settings.EXTENTION_EX3
        if not ValidationUtils.path_exists(ext_path):
            Settings.WRITE_LOG_DEV_FILE(f"Extension not found, downloading...", "INFO")
            valid_ext_dir = ValidationUtils.validate_directory_path(ext_path, must_exist=False)
            if not valid_ext_dir:
                Settings.WRITE_LOG_DEV_FILE(f"Invalid extension path: {ext_path}", "WARNING")
                return False
            if UpdateManager.update_extension_from_server():
                Settings.WRITE_LOG_DEV_FILE(f"Extension installed successfully", "INFO")
            else:
                Settings.WRITE_LOG_DEV_FILE(f"Failed to install extension", "WARNING")
                return False
        else:
            Settings.WRITE_LOG_DEV_FILE(f"Extension found: {ext_path}", "INFO")
            manifest_file = os.path.join(ext_path, "manifest.json")
            if not os.path.exists(manifest_file):
                Settings.WRITE_LOG_DEV_FILE(f"manifest.json not found", "WARNING")
                return False

            remote_version = UpdateManager.check_version_extension(window)
            if isinstance(remote_version, str):
                Settings.WRITE_LOG_DEV_FILE(f"Update available: {remote_version}", "INFO")
                if UpdateManager.update_extension_from_server(remote_version):
                    Settings.WRITE_LOG_DEV_FILE(f"Extension updated successfully", "INFO")
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"Failed to update extension", "WARNING")
                    return False
            elif remote_version is True:
                Settings.WRITE_LOG_DEV_FILE("Extension already up to date", "INFO")
            else:
                Settings.WRITE_LOG_DEV_FILE(f"Failed to check extension version", "WARNING")
                return False

        Settings.WRITE_LOG_DEV_FILE(f"Processing completed successfully for Chrome browser", "INFO")
        return True
    

    
    
    @staticmethod
    def get_browser_path(browser_name_or_exe: str) -> Optional[str]:
        """Récupère le chemin d'un navigateur via le registre Windows avec logs détaillés"""

        exe_name = Settings.SUPPORTED_BROWSERS.get(
            browser_name_or_exe.lower(), {}
        ).get("exe_name", browser_name_or_exe)

        Settings.WRITE_LOG_DEV_FILE(f"🔍 Recherche du navigateur: {exe_name}", "INFO")

        # Mapping professionnel des hives
        HIVE_NAMES = {
            winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE",
            winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
        }

        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_CURRENT_USER, winreg.KEY_READ),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ),
        ]

        key_app_paths = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"

        for hive, access in registry_paths:
            hive_name = HIVE_NAMES.get(hive, str(hive))

            try:
                Settings.WRITE_LOG_DEV_FILE(
                    f"🔎 Recherche dans: {hive_name}",
                    "INFO"
                )

                with winreg.OpenKey(hive, key_app_paths, 0, access) as key_obj:
                    path, _ = winreg.QueryValueEx(key_obj, None)

                    if path:
                        if ValidationUtils.path_exists(path):
                            Settings.WRITE_LOG_DEV_FILE(
                                f"✅ Navigateur trouvé: {exe_name}",
                                "SUCCESS"
                            )
                            Settings.WRITE_LOG_DEV_FILE(
                                f"📂 Chemin: {path}",
                                "SUCCESS"
                            )
                            return path
                        else:
                            Settings.WRITE_LOG_DEV_FILE(
                                f"⚠️ Chemin trouvé mais fichier inexistant: {path}",
                                "WARNING"
                            )

            except FileNotFoundError:
                Settings.WRITE_LOG_DEV_FILE(
                    f"❌ Non trouvé dans: {hive_name}",
                    "INFO"
                )
                continue

            except Exception as e:
                Settings.WRITE_LOG_DEV_FILE(f"🚨 Erreur registre ({hive_name}): {str(e)}\n{traceback.format_exc()}", "ERROR")

        Settings.WRITE_LOG_DEV_FILE(
            f"❌ Navigateur introuvable: {exe_name}",
            "ERROR"
        )

        return None
    
    
    
    @staticmethod
    def store_browser_session_info(   pid: str,  Path_DiR: str,   email: str,  SESSION_ID: str, browser: str,  inserted_id: str ) -> None:
        def _write_and_verify(target_path: Path, content: str, label: str):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(f"{content}\n", encoding="utf-8")
            actual = target_path.read_text(encoding="utf-8").strip()
            Settings.WRITE_LOG_DEV_FILE(f"Content of {target_path} after write: '{actual}'", "INFO")
            if actual != content.strip():
                Settings.WRITE_LOG_DEV_FILE(
                    f"❌ [{label}] ERREUR: Contenu attendu '{content.strip()}', mais lu '{actual}'",
                    "ERROR",
                )

        try:
            browser_key = browser.strip().lower()
            chrome_family = Settings.CHROME_FAMILY_BROWSERS
            Settings.WRITE_LOG_DEV_FILE(
                f"store_browser_session_info called with PID={pid}, email={email}, SESSION_ID={SESSION_ID}, browser={browser_key}, inserted_id={inserted_id}",
                "INFO",
            )

            session_entry = f"{pid}:{email}:{SESSION_ID}:{inserted_id}"
            session_file = Path(Path_DiR) / email / "data.txt"

            if browser_key in chrome_family:
                browser_label = browser_key.upper()
                Settings.WRITE_LOG_DEV_FILE(f"{browser_label} browser detected", "INFO")

                extension_file = Path(Settings.EXTENTION_EX3) / "data.txt"
                existing_content = (
                    extension_file.read_text(encoding="utf-8").strip()
                    if extension_file.exists()
                    else None
                )
                if existing_content is not None:
                    Settings.WRITE_LOG_DEV_FILE(
                        f"Content of {extension_file} before write: '{existing_content}'",
                        "INFO",
                    )
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"{extension_file} does not exist yet", "INFO")

                Settings.WRITE_LOG_DEV_FILE(f"Writing SESSION_ID={SESSION_ID} to {extension_file}", "INFO")
                _write_and_verify(extension_file, SESSION_ID, browser_label)

                Settings.WRITE_LOG_DEV_FILE(f"Writing session to {session_file}", "INFO")
                _write_and_verify(session_file, session_entry, browser_label)
            else:
                Settings.WRITE_LOG_DEV_FILE(f"Other browser detected: {browser_key}", "INFO")
                Settings.WRITE_LOG_DEV_FILE(f"Writing session to {session_file}", "INFO")
                _write_and_verify(session_file, session_entry, "OTHER")

            Settings.WRITE_LOG_DEV_FILE("Session data stored successfully", "INFO")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(
                f"Error in store_browser_session_info: {e}\n{traceback.format_exc()}",
                "ERROR",
            )

    
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
            Settings.WRITE_LOG_DEV_FILE(f"🚨 Erreur proc ({pid}): {traceback.format_exc()}", "ERROR")
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
                    Settings.WRITE_LOG_DEV_FILE(f"🚨 Erreur proc ({hwnd}): {traceback.format_exc()}", "ERROR")
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
                    Settings.WRITE_LOG_DEV_FILE(f"Erreur fermeture {window['profile']} : {e}\n{traceback.format_exc()}", "ERROR")
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
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lancement Chrome : {e}\n{traceback.format_exc()}", "ERROR")
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
                        Settings.WRITE_LOG_DEV_FILE(f"Found JSON key: {k} at {current_path} -> {v}", "INFO")
                        # print(f"🔑 Clé trouvée : {current_path} ➜ Valeur : {v}")
                    BrowserManager.Search_Keys(v, search_keys, results, current_path)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    current_path = f"{path_trace}[{idx}]"
                    BrowserManager.Search_Keys(item, search_keys, results, current_path)
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la recherche des clés à {path_trace} : {e}\n{traceback.format_exc()}", "ERROR")
            # Settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la recherche des clés à {path_trace} : {e}", "ERROR")
            


    #=======================================================
    # Upload_EXTENSION_PROXY
    #=======================================================
    # Vérifie et lit le fichier 'Secure Preferences' d'un profil,
    # recherche les clés spécifiées et retourne la liste des résultats si trouvés,
    # sinon retourne None.
    
    
    @staticmethod
    def Upload_EXTENSION_PROXY(profile_name: str, search_keys: List[str], results: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        path_file = os.path.join(Settings.CONFIG_PROFILE, profile_name, "Secure Preferences")
        # print(f"[DEBUG] Vérification du fichier Secure Preferences : {path_file}")
        Settings.WRITE_LOG_DEV_FILE(f"Verification du fichier Secure Preferences : {path_file}", "INFO")

        if not ValidationUtils.path_exists(path_file):
            # print(f"[ERROR] Fichier introuvable pour le profil {profile_name}")
            Settings.WRITE_LOG_DEV_FILE(f"Fichier introuvable pour le profil {profile_name}", "ERROR")
            return None

        try:
            # print(f"[DEBUG] Lecture du fichier JSON en cours pour le profil {profile_name}...")
            with open(path_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # print("[DEBUG] Lecture réussie du fichier JSON.")

            results.clear()
            # print(f"[DEBUG] Début de la recherche des clés : {search_keys}")
            BrowserManager.Search_Keys(data, search_keys, results)

            if results:
                # print(f"[INFO] Résultats trouvés pour {profile_name}:")
                # for idx, item in enumerate(results, start=1):
                #     print(f"   {idx}. {item}")
                Settings.WRITE_LOG_DEV_FILE(f"Résultats trouvés pour {profile_name}: {results}", "INFO")
                return results  # retourne la liste si des résultats trouvés
            else:
                # print(f"[WARNING] Aucun résultat trouvé pour les clés spécifiées pour {profile_name}")
                Settings.WRITE_LOG_DEV_FILE(f"Aucun résultat trouvé pour les clés spécifiées pour {profile_name}", "WARNING")
                return None  # retourne None si aucun résultat

        except json.JSONDecodeError as e:
            # print(f"[ERROR] {error_msg}")
            Settings.WRITE_LOG_DEV_FILE( f"JSONDecodeError: impossible de décoder le fichier {path_file} : {e}\n{traceback.format_exc()}", "ERROR")

        except PermissionError as e:
            # print(f"[ERROR] {error_msg}")
            Settings.WRITE_LOG_DEV_FILE(f"PermissionError: Permission refusée pour lire le fichier {path_file} : {e}\n{traceback.format_exc()}", "ERROR")

        except FileNotFoundError as e:
            
            # print(f"[ERROR] {error_msg}")
            Settings.WRITE_LOG_DEV_FILE(f"FileNotFoundError: Fichier non trouvé : {path_file} : {e}\n{traceback.format_exc()}", "ERROR")

        except Exception as e:
            # print(f"[ERROR] {error_msg}")
            Settings.WRITE_LOG_DEV_FILE(f"UnexpectedError: Erreur inattendue lors du traitement de {path_file} : {e}\n{traceback.format_exc()}", "ERROR")

        return None  



    @staticmethod
    def UpdateChromeProfileFromTemplate(profile_name: str):
        """
        Copie les fichiers template (Secure Preferences, Local State, Variations)
        dans le profil Chrome cible après suppression des anciens fichiers.
        Affichage détaillé pour debug et logging.
        """
        try:
            # 📂 Définir chemins cibles
            profile_dir = os.path.join(Settings.CHROME_PROFILES, profile_name)
            secure_preferences_path = os.path.join(profile_dir,profile_name , "Secure Preferences")
            local_state_path = os.path.join(profile_dir, "Local State")
            variations_path = os.path.join(profile_dir, "Variations")

            # print(f"[DEBUG] Profil cible : {profile_dir}")
            # print(f"[DEBUG] Secure Preferences : {secure_preferences_path}")
            # print(f"[DEBUG] Local State : {local_state_path}")
            # print(f"[DEBUG] Variations : {variations_path}")

            Settings.WRITE_LOG_DEV_FILE(f"Profil cible : {profile_dir}", "DEBUG")
            Settings.WRITE_LOG_DEV_FILE(f"Secure Preferences : {secure_preferences_path}", "DEBUG")
            Settings.WRITE_LOG_DEV_FILE(f"Local State : {local_state_path}", "DEBUG")
            Settings.WRITE_LOG_DEV_FILE(f"Variations : {variations_path}", "DEBUG")

            # 🔹 Supprimer fichiers existants si présents
            for path in [secure_preferences_path, local_state_path, variations_path]:
                if os.path.exists(path):
                    try:
                        Settings.WRITE_LOG_DEV_FILE(f"Suppression du fichier existant : {path}", "DEBUG")
                        os.remove(path)
                    except Exception as e:
                        Settings.WRITE_LOG_DEV_FILE(f"Erreur suppression fichier {path} : {e}", "ERROR")

            # 🔹 Vérifier que les fichiers templates existent avant copie
            for template_path, name in [ (Settings.SECURE_PREFERENCES_TEMPLATE, "Secure Preferences"), (Settings.FICHIER_LOCAL_STATE, "Local State"), (Settings.FICHIER_VARIATIONS, "Variations")]:
                if not os.path.isfile(template_path):
                    # print(f"[ERROR] Template {name} introuvable ou pas un fichier : {template_path}")
                    Settings.WRITE_LOG_DEV_FILE(f"Template {name} introuvable ou pas un fichier : {template_path}", "ERROR")
                    raise FileNotFoundError(f"Template {name} introuvable ou pas un fichier : {template_path}")

            # 🔹 Copier fichiers templates
            # print(f"[DEBUG] Copie de SECURE_PREFERENCES_TEMPLATE vers {secure_preferences_path}")
            Settings.WRITE_LOG_DEV_FILE(f"Copie de SECURE_PREFERENCES_TEMPLATE vers {secure_preferences_path}", "DEBUG")
            shutil.copy2(Settings.SECURE_PREFERENCES_TEMPLATE, secure_preferences_path)

            # print(f"[DEBUG] Copie de FICHIER_LOCAL_STATE vers {local_state_path}")
            Settings.WRITE_LOG_DEV_FILE(f"Copie de FICHIER_LOCAL_STATE vers {local_state_path}", "DEBUG")
            shutil.copy2(Settings.FICHIER_LOCAL_STATE, local_state_path)

            # print(f"[DEBUG] Copie de FICHIER_VARIATIONS vers {variations_path}")
            Settings.WRITE_LOG_DEV_FILE(f"Copie de FICHIER_VARIATIONS vers {variations_path}", "DEBUG")
            shutil.copy2(Settings.FICHIER_VARIATIONS, variations_path)

            # print(f"[INFO] Mise à jour du profil {profile_name} effectuée avec succès.")
            Settings.WRITE_LOG_DEV_FILE(f"Mise à jour du profil {profile_name} effectuée avec succès.", "INFO")
            return True

        except Exception as e:
            # print(f"[ERROR] Erreur lors de la mise à jour du profil {profile_name} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Erreur lors de la mise à jour du profil {profile_name} : {e}\n{traceback.format_exc()}", "ERROR")
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
