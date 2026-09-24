
import os
import sys
import subprocess
import configparser
import traceback
from typing import Optional, List, Dict, Any
import psutil
import winreg
import win32gui
import win32process
import win32con
import time
from pathlib import Path


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__} : {e}")
    sys.exit(1)


class BrowserManager:

    @staticmethod
    def get_browser_executable_path(browser_name: str) -> Optional[str]:
        executable = Settings.BROWSER_EXECUTABLES.get((browser_name or "").strip().lower())
        return BrowserManager.getBrowserExecutablePath(executable) if executable else None

    @staticmethod
    def getBrowserExecutablePath(browser_name_or_exe: str) -> Optional[str]:
        exe_name = Settings.SUPPORTED_BROWSERS.get(browser_name_or_exe.lower(), {}).get( "exe_name", browser_name_or_exe  )
        
        Settings.write_log_dev_file(f"🔍 Recherche du navigateur: {exe_name}", "INFO")
        HIVE_NAMES = { winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE", winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER" }
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
            (winreg.HKEY_CURRENT_USER, winreg.KEY_READ),
            (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ)
        ]

        key_app_paths = (  rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}" )
        for hive, access in registry_paths:
            hive_name = HIVE_NAMES.get(hive, str(hive))

            try:
                Settings.write_log_dev_file(f"🔎 Recherche dans: {hive_name}", "INFO")
                with winreg.OpenKey(hive, key_app_paths, 0, access) as key_obj:
                    path, _ = winreg.QueryValueEx(key_obj, None)

                    if path:
                        if ValidationUtils.pathExists(path):
                            Settings.write_log_dev_file(  f"✅ Navigateur trouvé: {exe_name}", "SUCCESS" )
                            Settings.write_log_dev_file(f"📂 Chemin: {path}", "SUCCESS")
                            return path
                        else:
                            Settings.write_log_dev_file(  f"⚠️ Chemin trouvé mais fichier inexistant: {path}", "WARNING"  )

            except FileNotFoundError:
                Settings.write_log_dev_file(f"❌ Non trouvé dans: {hive_name}", "INFO")
                continue
            except Exception as e:
                Settings.write_log_dev_file( f"🚨 Erreur registre ({hive_name}): {str(e)}\n{traceback.format_exc()}",  "ERROR" )
        Settings.write_log_dev_file(f"❌ Navigateur introuvable: {exe_name}", "ERROR")
        return None



    @staticmethod
    def persistBrowserSessionInfo(  pid: Any, Path_DiR: str, email: str , SESSION_ID: str,  browser: str, inserted_id: str,  profile_path: Optional[str] = None,  web_ext_pid: Optional[int] = None,  profile_name: Optional[str] = None) -> None:

        def _normalize_pid_value(pid_value: Any, browser_key: str) -> str:
            if browser_key == "firefox":
                if isinstance(pid_value, (list, tuple, set)):
                    return ";".join( str(int(p)) for p in pid_value if str(p).strip().isdigit() )
                if isinstance(pid_value, int):
                    return str(pid_value)
                if isinstance(pid_value, str):
                    return pid_value.strip()
                return str(pid_value)

            if isinstance(pid_value, int):
                return str(pid_value)
            if isinstance(pid_value, str):
                return pid_value.strip()
            return str(pid_value)


        def _write_and_verify(target_path: Path, content: str, label: str):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(f"{content}\n", encoding="utf-8")
            actual = target_path.read_text(encoding="utf-8").strip()
            Settings.write_log_event( "browser_session_write_verified", "INFO", label=label,expected_length=len(content.strip()), actual_length=len(actual),  file_written=target_path.name )
            if actual != content.strip():
                Settings.write_log_event("browser_session_write_mismatch", "ERROR",  label=label,  expected_length=len(content.strip()), actual_length=len(actual) )

        try:
            browser_key = browser.strip().lower()

            normalized_pid = _normalize_pid_value(pid, browser_key)
            Settings.write_log_event( "browser_session_info_prepared","INFO",  browser_key=browser_key, pid_value_type=type(pid).__name__,  has_profile_path=bool(profile_path),  has_web_ext_pid=bool(web_ext_pid),  has_email=bool(email),  has_session_id=bool(SESSION_ID) )

            session_entry = f"{normalized_pid}:{email}:{SESSION_ID}:{inserted_id}"
            session_file = Path(Path_DiR) / email / "data.txt"

            if browser_key in Settings.CHROME_FAMILY_BROWSERS:
                browser_label = browser_key.upper()
                Settings.write_log_dev_file(f"{browser_label} browser detected", "INFO")

                if profile_path is None and email:
                    profile_path = str(Path(Path_DiR) / email)
                    Settings.write_log_dev_file(f"Inferred profile_path for Chrome family browser: {profile_path}", "DEBUG")

                if profile_path:
                    profile_data_file = Path(profile_path) / "data.txt"
                    Settings.write_log_dev_file(f"Writing session entry to Chrome profile data file: {profile_data_file}", "INFO")
                    _write_and_verify(profile_data_file, session_entry, browser_label)
                else:
                    Settings.write_log_dev_file("No profile_path provided for Chrome session storage", "ERROR")
            else:
                Settings.write_log_dev_file(f"Firefox or other browser detected: {browser_key}", "INFO")
                Settings.write_log_dev_file(f"Session entry for Firefox write: '{session_entry}'", "DEBUG")
                Settings.write_log_dev_file(f"Writing session to {session_file}", "INFO")
                _write_and_verify(session_file, session_entry, "OTHER")

            Settings.write_log_dev_file("Session data stored successfully", "INFO")

        except Exception as exc:
            Settings.write_log_event( "browser_session_store_failed",  "ERROR", exception_type=type(exc).__name__ , error=str(exc), browser_key=browser_key if "browser_key" in locals() else "unknown")


    
    @staticmethod
    def getFirefoxProfileMap() -> Dict[str, str]:
        Settings.write_log_dev_file("[_get_firefox_profiles] Lecture des profils Firefox existants", "DEBUG")
        ini_path = getattr(Settings, "FIREFOX_PROFILES_INI", None) or os.path.join( Settings.APPDATA, "Mozilla", "Firefox", "profiles.ini")
        Settings.FIREFOX_PROFILES_INI = ini_path
        Settings.write_log_dev_file(f"[_get_firefox_profiles] Firefox profiles.ini path stored in Settings: {ini_path}", "DEBUG")

        if not os.path.exists(ini_path):
            Settings.write_log_dev_file(f"[_get_firefox_profiles] ⚠️ profiles.ini non trouvé: {ini_path}", "WARNING")
            return {}

        config = configparser.ConfigParser()
        try:
            config.read(ini_path, encoding="utf-8")
        except Exception as exc:
            Settings.write_log_event( "firefox_profiles_read_failed","ERROR",  exception_type=type(exc).__name__ ,  error=str(exc), ini_path=ini_path  )
            return {}

        base_dir = os.path.dirname(ini_path)
        profiles = {}

        try:
            for section in config.sections():
                if section.startswith("Profile"):
                    name = config.get(section, "Name", fallback=None)
                    path = config.get(section, "Path", fallback=None)
                    is_rel = config.getint(section, "IsRelative", fallback=1)
                    if name and path:
                        full_path = os.path.join(base_dir, path) if is_rel else path
                        profiles[name] = os.path.normpath(full_path)
                        Settings.write_log_dev_file(f"  📌 Profil trouvé: {name} -> {profiles[name]}", "DEBUG")
        except Exception as exc:
            Settings.write_log_event("firefox_profiles_parse_failed", "ERROR", exception_type=type(exc).__name__ ,  error=str(exc))
        Settings.write_log_event("firefox_profiles_loaded","INFO" ,  profile_count=len(profiles) )
        return profiles


    @staticmethod
    def findFirefoxProcessIds(profile_path: str, parent_pid: int) -> List[int]:
        Settings.write_log_dev_file( f"[find_firefox_pids] Recherche des PIDs Firefox pour profile_path={profile_path}, parent_pid={parent_pid}", "DEBUG" )
        pids = set()
        profile_lower = profile_path.lower()
        for proc in psutil.process_iter(["pid", "name", "ppid", "cmdline"]):
            try:
                name = (proc.info["name"] or "").lower()
                if "firefox" not in name:
                    continue
                cmdline = " ".join(proc.info["cmdline"] or []).lower()
                match_profile = profile_lower in cmdline
                match_parent = proc.info.get("ppid") == parent_pid
                if match_profile or match_parent:
                    pids.add(proc.pid)
                    Settings.write_log_dev_file( f"[find_firefox_pids] Match PID {proc.pid}: profile_match={match_profile}, parent_match={match_parent}, cmdline={cmdline[:200]}", "DEBUG" )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as exc:
                Settings.write_log_event("firefox_pid_scan_failed", "WARNING", exception_type=type(exc).__name__ ,  error=str(exc) )
                continue

        result = sorted(pids)
        Settings.write_log_dev_file( f"[find_firefox_pids] Firefox PIDs found: {result}", "INFO" )
        return result


    @staticmethod
    def findChromiumProcessIds(profile_path: str, browser_name: str) -> List[int]:
        Settings.write_log_dev_file(  f"[find_chromium_pids] Searching Chromium PIDs for profile_path={profile_path}, browser_name={browser_name}", "DEBUG" )
        pids = set()
        profile_lower = profile_path.lower()
        browser_name_lower = (browser_name or "").lower()

        allowed_names = Settings.BROWSER_PROCESS_PATTERNS.get( browser_name_lower , ("chrome", "edge", "msedge", "dragon", "comodo", "chromium"))
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = (proc.info["name"] or "").lower()
                if not any(term in name for term in allowed_names):
                    continue
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                if profile_lower in cmdline:
                    pids.add(proc.pid)
                    Settings.write_log_dev_file(f"[find_chromium_pids] Match PID {proc.pid}: name={name}, cmdline={cmdline[:200]}",  "DEBUG" )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                Settings.write_log_dev_file( f"[find_chromium_pids] Process scan error: {e}", "WARNING"  )
                continue
        result = sorted(pids)
        Settings.write_log_dev_file( f"[find_chromium_pids] Chromium PIDs found: {result}", "INFO" )
        return result



    @staticmethod
    def createFirefoxProfile(profile_name: str) -> Optional[str]:
        Settings.write_log_dev_file( f"[create_firefox_profile] Start: {profile_name}", "DEBUG" )
        firefox_path = BrowserManager.getBrowserExecutablePath("firefox.exe")
        if not firefox_path:
            Settings.write_log_dev_file("Firefox not found", "ERROR")
            return None
        base_dir = Settings.FIREFOX_PROFILES
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception as e:
            Settings.write_log_dev_file(f"Cannot create base dir: {e}", "ERROR")
            return None

        profile_dir = os.path.join(base_dir, profile_name)
        if os.path.exists(profile_dir):
            return profile_dir
        try:
            cmd = f"{profile_name} {profile_dir}"
            result = subprocess.run(  [firefox_path, "--CreateProfile", cmd] , stdout=subprocess.PIPE,  stderr=subprocess.PIPE, text=True,  timeout=15 )
            if result.returncode != 0:
                Settings.write_log_dev_file(f"Create failed: {result.stderr}", "ERROR")
                return None

        except Exception as e:
            Settings.write_log_dev_file(f"Subprocess error: {e}", "ERROR")
            return None

        for _ in range(20):  
            if os.path.exists(profile_dir):
                return profile_dir
            time.sleep(0.5)

        profiles = BrowserManager.getFirefoxProfileMap()
        return profiles.get(profile_name)


    @staticmethod
    def closeFirefoxProcesses(firefox_close_list: List[Any]):
        Settings.write_log_dev_file( f"close_windows_by_profiles called with {len(firefox_close_list)} entries", "INFO" )
        pid_list = []
        for entry in firefox_close_list:
            if isinstance(entry, dict):
                if "firefox_pids" in entry and entry["firefox_pids"] is not None:
                    if isinstance(entry["firefox_pids"], str):
                        pid_list.extend(  [  int(pid.strip())  for pid in entry["firefox_pids"].split(";") if pid.strip().isdigit() ] )
                    elif isinstance(entry["firefox_pids"], (list, tuple, set)):
                        pid_list.extend( [int(pid) for pid in entry["firefox_pids"]  if str(pid).strip().isdigit() ] )
                elif "pids" in entry and entry["pids"] is not None:
                    if isinstance(entry["pids"], str):
                        pid_list.extend( [ int(pid.strip())  for pid in entry["pids"].split(";") if pid.strip().isdigit() ] )
                    elif isinstance(entry["pids"], list):
                        pid_list.extend( [  int(pid) for pid in entry["pids"]  if str(pid).strip().isdigit()  ] )
                elif "pid" in entry and entry["pid"] is not None:
                    pid_str = str(entry["pid"]).strip()
                    if pid_str.isdigit():
                        pid_list.append(int(pid_str))
                elif entry.get("proc") is not None:
                    try:
                        pid_list.append(int(entry["proc"].pid))
                    except Exception:
                        Settings.write_log_dev_file( f"Unable to read pid from proc for entry {entry}", "WARNING" )
                elif entry.get("profile_path"):
                    derived = BrowserManager.findFirefoxProcessIds( entry["profile_path"], entry.get("web_ext_pid", 0) )
                    pid_list.extend(derived)
                    Settings.write_log_dev_file(  f"Derived Firefox PIDs from profile_path {entry['profile_path']}: {derived}", "DEBUG" )
            elif isinstance(entry, int):
                pid_list.append(entry)
            elif isinstance(entry, str):
                text = entry.strip()
                if text.isdigit():
                    pid_list.append(int(text))
                elif ";" in text:
                    pid_list.extend( [  int(pid.strip())  for pid in text.split(";")  if pid.strip().isdigit() ])

        pid_list = sorted(set(pid_list))
        Settings.write_log_dev_file(f"Resolved Firefox PID list: {pid_list}", "DEBUG")

        if not pid_list:
            Settings.write_log_dev_file("No Firefox PIDs to close", "WARNING")
            return

        for pid in pid_list:
            try:
                if not psutil.pid_exists(pid):
                    Settings.write_log_dev_file(  f"Firefox PID {pid} no longer exists", "INFO" )
                    continue
                process = psutil.Process(pid)
                Settings.write_log_dev_file(f"Terminating Firefox PID={pid}", "INFO")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    Settings.write_log_dev_file( f"Firefox PID {pid} terminated gracefully", "INFO" )
                except psutil.TimeoutExpired:
                    Settings.write_log_dev_file( f"Timeout terminating PID {pid}, forcing kill", "WARNING" )
                    process.kill()
                    try:
                        process.wait(timeout=3)
                        Settings.write_log_dev_file( f"Firefox PID {pid} killed forcefully", "INFO")
                    except psutil.NoSuchProcess:
                        Settings.write_log_dev_file( f"Firefox PID {pid} already exited after kill", "INFO" )
            except psutil.NoSuchProcess:
                Settings.write_log_dev_file(  f"Firefox PID {pid} already terminated", "INFO")
            except psutil.AccessDenied:
                Settings.write_log_dev_file(  f"Permission denied closing Firefox PID {pid}", "WARNING")
            except Exception as exc:
                Settings.write_log_event( "firefox_pid_close_failed",  "ERROR", pid=pid,  exception_type=type(exc).__name__ ,  error=str(exc) )

        Settings.write_log_dev_file("close_windows_by_profiles completed", "INFO")



    @staticmethod
    def search_keys(data: Any,  search_keys: List[str],  results: List[Dict[str, Any]],  path_trace: str = "" ):
        try:
            if isinstance(data, dict):
                for k, v in data.items():
                    current_path = f"{path_trace}/{k}" if path_trace else k
                    if k in search_keys:
                        results.append({k: v})
                        Settings.write_log_dev_file(f"Found JSON key: {k} at {current_path} -> {v}", "INFO")
                    BrowserManager.search_keys(v, search_keys, results, current_path)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    current_path = f"{path_trace}[{idx}]"
                    BrowserManager.search_keys(item, search_keys, results, current_path)
        except Exception as exc:
            Settings.write_log_event(  "json_key_search_failed",  "ERROR", path_trace=path_trace, exception_type=type(exc).__name__ ,  error=str(exc) )

  


BrowserManager = BrowserManager()
