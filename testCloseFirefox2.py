import os
import sys
import time
import psutil
import threading
import subprocess
from datetime import datetime
from typing import Dict, List
 
 
# ==========================================================
# SETTINGS
# ==========================================================
class Settings:
 
    WEB_EXT_PATH     = r"C:\Users\tec-d\AppData\Roaming\npm\web-ext.cmd"
    EXTENSION_DIR    = r"C:\Users\tec-d\Documents\Ext3 Firefox"
    PROFILES_DIR     = r"D:\FirefoxProfiles"
    BASE_URL         = "https://example.com"
    WAIT_AFTER_START = 8   # secondes d'attente après lancement Firefox
 
 
# ==========================================================
# LOGGER
# ==========================================================
class Logger:
 
    _lock = threading.Lock()
 
    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 
    @staticmethod
    def line():
        with Logger._lock:
            print("=" * 80)
 
    @staticmethod
    def info(msg):
        with Logger._lock:
            print(f"[{Logger.now()}] [INFO]    {msg}")
 
    @staticmethod
    def debug(msg):
        with Logger._lock:
            print(f"[{Logger.now()}] [DEBUG]   {msg}")
 
    @staticmethod
    def success(msg):
        with Logger._lock:
            print(f"[{Logger.now()}] [SUCCESS] {msg}")
 
    @staticmethod
    def warning(msg):
        with Logger._lock:
            print(f"[{Logger.now()}] [WARNING] {msg}")
 
    @staticmethod
    def error(msg):
        with Logger._lock:
            print(f"[{Logger.now()}] [ERROR]   {msg}")
 
 
# ==========================================================
# VALIDATION
# ==========================================================
class Validator:
 
    @staticmethod
    def validate():
 
        Logger.line()
        Logger.info("VALIDATING CONFIGURATION")
        Logger.line()
        Logger.debug(f"WEB_EXT_PATH     = {Settings.WEB_EXT_PATH}")
        Logger.debug(f"EXTENSION_DIR    = {Settings.EXTENSION_DIR}")
        Logger.debug(f"PROFILES_DIR     = {Settings.PROFILES_DIR}")
        Logger.debug(f"BASE_URL         = {Settings.BASE_URL}")
        Logger.debug(f"WAIT_AFTER_START = {Settings.WAIT_AFTER_START}")
 
        if not os.path.exists(Settings.WEB_EXT_PATH):
            raise FileNotFoundError(
                f"web-ext introuvable:\n{Settings.WEB_EXT_PATH}"
            )
        Logger.success("web-ext trouvé")
 
        if not os.path.exists(Settings.EXTENSION_DIR):
            raise FileNotFoundError(
                f"Extension introuvable:\n{Settings.EXTENSION_DIR}"
            )
        Logger.success("Extension trouvée")
 
        os.makedirs(Settings.PROFILES_DIR, exist_ok=True)
        Logger.success(f"Dossier profils prêt: {Settings.PROFILES_DIR}")
 
 
# ==========================================================
# PROFILE MANAGER
# ==========================================================
class ProfileManager:
 
    @staticmethod
    def get_profile_path(profile_name: str) -> str:
        profile_path = os.path.join(Settings.PROFILES_DIR, profile_name)
        Logger.debug(f"Computed profile path for '{profile_name}': {profile_path}")
        return profile_path
 
    @staticmethod
    def ensure_profile(profile_name: str) -> str:
        profile_path = ProfileManager.get_profile_path(profile_name)
        Logger.info(f"Ensuring profile directory exists for '{profile_name}'")
        os.makedirs(profile_path, exist_ok=True)
        Logger.success(f"Profil prêt: {profile_name} -> {profile_path}")
        return profile_path
 
 
# ==========================================================
# PID FINDER  — méthode fiable pour parallélisme
# ==========================================================
class PidFinder:
    """
    Trouve les PIDs Firefox liés à un profil spécifique.
 
    Stratégie double (fonctionne en parallèle) :
      1. cmdline  → le morceau --profile <profile_path> est unique par instance
      2. ppid     → Firefox lancé par web-ext hérite de son PID comme parent
 
    Les deux critères sont combinés en OR pour maximiser la détection.
    """
 
    @staticmethod
    def find(profile_path: str, webext_pid: int) -> List[int]:
        print(f"Recherche des PIDs Firefox pour le profil: {profile_path}")
 
        Logger.line()
        Logger.info(f"Recherche des PIDs Firefox pour le profil: {profile_path}")
        Logger.debug(f"Critère profile path (lower): {profile_path.lower()}")
        Logger.debug(f"Critère web-ext PID      : {webext_pid}")
 
        found: set = set()
        profile_lower = profile_path.lower()
        scanned = 0
        matched = 0
 
        for proc in psutil.process_iter(["pid", "name", "ppid", "cmdline"]):
            scanned += 1
            try:
                name = (proc.info["name"] or "").lower()
                cmdline = " ".join(proc.info["cmdline"] or []).lower()
                ppid = proc.info["ppid"]
 
                if "firefox" not in name:
                    Logger.debug(f"Ignorer PID {proc.pid} (nom={name})")
                    continue
 
                by_cmdline = profile_lower in cmdline
                by_ppid = ppid == webext_pid
 
                if by_cmdline or by_ppid:
                    found.add(proc.pid)
                    matched += 1
                    Logger.debug(f"Match PID {proc.pid}: by_cmdline={by_cmdline}, by_ppid={by_ppid}, cmdline={cmdline}")
                else:
                    Logger.debug( f"Non-match Firefox PID {proc.pid}: ppid={ppid}, cmdline snippet={cmdline[:120]}" )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                Logger.warning(f"Process scan skipped: PID {getattr(proc, 'pid', '?')} -> {e}")
 
        Logger.info(f"Processus scannés: {scanned}, correspondances Firefox: {matched}")
        Logger.success(f"Firefox PID search complete: {sorted(found)}")
        return list(found)
 
 
# ==========================================================
# WEB EXT MANAGER
# ==========================================================
class WebExtManager:
 
    def __init__(self):
        self.running: Dict[str, Dict] = {}
        self._lock = threading.Lock()
 
    # ----------------------------------------------------------
    def _build_url(self, profile_name: str) -> str:
        return f"{Settings.BASE_URL}?profile={profile_name}"
 
    # ----------------------------------------------------------
    # LAUNCH (thread-safe)
    # ----------------------------------------------------------
    def launch(self, profile_name: str) -> bool:
 
        profile_path = ProfileManager.ensure_profile(profile_name)
        url          = self._build_url(profile_name)

        cmd = [
            Settings.WEB_EXT_PATH,
            "run",
            "--source-dir",       Settings.EXTENSION_DIR,
            "--firefox-profile",  profile_path,
            "--keep-profile-changes",
            "--no-reload",
            "--url",              url,
        ]
 
        Logger.line()
        Logger.info(f"START PROFILE : {profile_name}")
        Logger.info(f"Profile path  : {profile_path}")
        Logger.info(f"URL           : {url}")
        Logger.debug(f"Commande web-ext: {' '.join(cmd)}")
 
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
 
        webext_pid = process.pid
        Logger.info(f"WEB-EXT PID   : {webext_pid}")
        Logger.debug(f"Process web-ext lancé, pid={webext_pid}, thread={threading.current_thread().name}")
 
        Logger.info(f"Attente de {Settings.WAIT_AFTER_START} secondes pour démarrage Firefox")
        time.sleep(Settings.WAIT_AFTER_START)
 
        firefox_pids = PidFinder.find(profile_path, webext_pid)
 
        if firefox_pids:
            Logger.success(f"Firefox détecté pour '{profile_name}' : {firefox_pids}")
        else:
            Logger.warning(f"Aucun PID Firefox trouvé pour '{profile_name}' après attente")
 
        with self._lock:
            self.running[profile_name] = {
                "process":      process,
                "pid":          webext_pid,
                "profile_path": profile_path,
                "url":          url,
                "firefox_pids": firefox_pids,
                "started_at":   Logger.now(),
            }
 
        Logger.success(f"{profile_name} lancé ✓")
        return True
 
    # ----------------------------------------------------------
    # LAUNCH PARALLEL — tous les profils en même temps
    # ----------------------------------------------------------
    def launch_all_parallel(self, profiles: List[str]):
 
        Logger.line()
        Logger.info("DÉMARRAGE PARALLÈLE DE TOUS LES PROFILS")
        Logger.debug(f"Profils à démarrer: {profiles}")
        Logger.line()
 
        threads = []
 
        for profile in profiles:
            Logger.debug(f"Création du thread de lancement pour '{profile}'")
            t = threading.Thread(
                target=self.launch,
                args=(profile,),
                name=f"launch-{profile}",
                daemon=True,
            )
            threads.append(t)
 
        for t in threads:
            Logger.debug(f"Démarrage du thread {t.name}")
            t.start()
 
        for t in threads:
            Logger.debug(f"Attente de la fin du thread {t.name}")
            t.join()
 
        Logger.line()
        Logger.success(f"Tous les profils sont démarrés ({len(profiles)})")
 
    # ----------------------------------------------------------
    # STATUS
    # ----------------------------------------------------------
    def show_status(self):
 
        Logger.line()
        Logger.info("PROFILS ACTIFS")
        Logger.line()
 
        with self._lock:
            if not self.running:
                Logger.warning("Aucun profil actif")
                return
 
            Logger.debug(f"Nombre de profils en cours: {len(self.running)}")
            for name, data in self.running.items():
                status = "RUNNING" if data["process"].poll() is None else "STOPPED"
                Logger.info(f"Status du profil '{name}'")
                print(
                    f"  PROFILE  : {name}\n"
                    f"  PID      : {data['pid']}\n"
                    f"  STATUS   : {status}\n"
                    f"  URL      : {data['url']}\n"
                    f"  STARTED  : {data['started_at']}\n"
                    f"  FF PIDS  : {data['firefox_pids']}\n"
                )
 
    # ----------------------------------------------------------
    # STOP
    # ----------------------------------------------------------
    def stop(self, profile_name: str):
 
        with self._lock:
            if profile_name not in self.running:
                Logger.warning(f"Profil introuvable: {profile_name}")
                return
            data = self.running[profile_name]
 
        Logger.line()
        Logger.info(f"STOP PROFILE : {profile_name}")
        Logger.debug(f"Données de fermeture: {data}")
 
        killed = 0
        firefox_pids = data.get("firefox_pids", [])
        Logger.info(f"Tentative de fermeture de {len(firefox_pids)} PID(s) Firefox connus")
 
        for pid in firefox_pids:
            try:
                psutil.Process(pid).kill()
                Logger.info(f"KILL Firefox PID {pid}")
                killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Erreur lors de la tentative de fermeture du PID {pid}: {e}")
                Logger.warning(f"Impossible de tuer PID {pid}: {e}")
 
        try:
            webext = data["process"]
            if webext.poll() is None:
                webext.kill()
                Logger.info(f"KILL web-ext PID {webext.pid}")
            else:
                Logger.debug(f"web-ext PID {webext.pid} déjà arrêté")
        except Exception as e:
            print(f"Erreur en fermant web-ext PID {data.get('pid', '?')}: {e}")
            Logger.warning(f"Erreur en fermant web-ext: {e}")
 
        profile_lower = data["profile_path"].lower()
        Logger.info("Vérification de secours des processus Firefox restants")
        fallback_count = 0
 
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = (proc.info["name"] or "").lower()
                if "firefox" not in name:
                    continue
                cmdline = " ".join(proc.info["cmdline"] or []).lower()
                if profile_lower in cmdline:
                    proc.kill()
                    Logger.info(f"FORCE KILL Firefox PID {proc.pid} via cmdline match")
                    killed += 1
                    fallback_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Erreur lors de la tentative de fermeture du PID {getattr(proc, 'pid', '?')} : {e}")
                Logger.debug(f"Fallback skip PID {getattr(proc, 'pid', '?')} : {e}")
 
        Logger.debug(f"Fallback Firefox scan terminé, tués: {fallback_count}")
 
        with self._lock:
            del self.running[profile_name]
 
        Logger.success(f"{profile_name} arrêté — {killed} processus Firefox tué(s)")
 
    # ----------------------------------------------------------
    # STOP ALL
    # ----------------------------------------------------------
    def stop_all(self):
        with self._lock:
            profiles = list(self.running.keys())
        Logger.line()
        Logger.info(f"Arrêt de tous les profils actifs: {profiles}")
        for profile in profiles:
            self.stop(profile)
        Logger.success("Tous les profils ont été arrêtés")
 
 
# ==========================================================
# MAIN
# ==========================================================
def main():
 
    Validator.validate()
 
    manager  = WebExtManager()
    profiles = ["Profile_A", "Profile_B", "Profile_C" , "Profile_D", "Profile_E"]
 
    # ✅ Lancement parallèle — PIDs correctement isolés
    manager.launch_all_parallel(profiles)
 
    while True:
 
        manager.show_status()
 
        raw  = input("\nclose <profile> | status | exit : ").strip()
        Logger.debug(f"Commande saisie: '{raw}'")
        cmd  = raw.lower()          # pour comparer les mots-clés uniquement
 
        if cmd == "exit":
            Logger.info("Arrêt de tous les profils...")
            manager.stop_all()
            break
 
        elif cmd == "status":
            Logger.info("Affichage de l'état des profils")
            continue
 
        elif cmd.startswith("close "):
            profile_name = raw[len("close "):].strip()
            Logger.info(f"Commande de fermeture reçue pour le profil: '{profile_name}'")
            manager.stop(profile_name)
 
        else:
            Logger.warning(f"Commande inconnue: '{raw}'")
            print(f"Commandes valides: 'close <profile>', 'status', 'exit'")
 
 
# ==========================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Logger.warning("Programme interrompu par l'utilisateur")
        print(f"Traceback complet:\n{traceback.format_exc()}")
    except Exception as e:
        Logger.error(f"Exception inattendue: {e}")
        print(f"Traceback complet:\n{traceback.format_exc()}")
        sys.exit(1)
 
