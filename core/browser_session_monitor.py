# =============================================================================
# Module : browser_session_monitor.py
# Role   : thread de SURVEILLANCE (QThread) qui observe le dossier des
#          telechargements et reagit aux fichiers deposes par l'extension du
#          navigateur (fichiers de log et fichiers de session).
#
# Pour chaque compte email traite, il :
#   - detecte le fichier de resultat/log correspondant ;
#   - deplace le log et la capture d'ecran dans un dossier de session dedie ;
#   - ecrit le resultat (completed / not completed) et l'envoie a l'API ;
#   - ferme le navigateur (tue les processus) et libere le creneau de l'email.
# Il complete ainsi EmailExtractionWorker, qui lui ne fait que LANCER les
# navigateurs.
# =============================================================================
#
# --- Imports de la bibliotheque standard ---
# datetime : horodatage du dossier de session.
import datetime

# json : serialisation d'une session Firefox pour le log de debogage.
import json

# os : chemins, dossiers, suppression de fichiers, envoi de signaux (os.kill).
import os

# re : extraction des metadonnees (session/email/etat) d'un fichier de session.
import re

# shutil : deplacement des logs et captures d'ecran.
import shutil

# signal : SIGTERM pour demander l'arret des processus navigateur.
import signal

# threading : verrou (Lock) protegeant les ensembles partages du thread.
import threading

# time : attentes (fichier stable, delai initial, temporisations).
import time

# traceback : pile d'appels complete dans les logs d'erreur.
import traceback

# Queue : file alimentee par le watcher de fichiers ; Empty : leve quand la
# file est vide apres le delai d'attente.
from queue import Empty, Queue

# --- Imports tiers ---
# psutil : verification et arret fiable des processus (par PID).
import psutil

# user_downloads_dir : chemin du dossier « Telechargements » de l'utilisateur.
from platformdirs import user_downloads_dir

# QThread : execution en arriere-plan ; pyqtSignal : signal Qt.
from PyQt6.QtCore import QThread, pyqtSignal

# Observer : surveille le systeme de fichiers et notifie les evenements.
from watchdog.observers import Observer

# --- Imports internes au projet ---
# API_MANAGER : envoi du statut de chaque email a l'API distante.
from api import API_MANAGER

# Settings : configuration (chemins, motifs de nom de fichier, fonctions de log).
from config import Settings

# DownloadFileEventHandler : gestionnaire watchdog qui met les nouveaux
# fichiers dans la file.
from core.file_watcher import DownloadFileEventHandler

# runtime_state : etat partage global (emails actifs, PID, sessions Firefox).
from core.runtime_state import runtime_state

# BrowserManager : utilitaires navigateur.
from models import BrowserManager

# ValidationUtils : extraction de l'email depuis le contenu d'un log.
from utils import ValidationUtils


# =============================================================================
# Classe BrowserSessionMonitorThread
# -----------------------------------------------------------------------------
# Thread Qt qui surveille en continu le dossier des telechargements et traite
# les fichiers deposes par l'extension jusqu'a ce que plus aucun email ne soit
# en cours (ni restant, ni actif, ni processus vivant) ou qu'un arret soit
# demande (stop_flag).
# =============================================================================
class BrowserSessionMonitorThread(QThread):
    # Signal Qt d'avancement (str) vers l'interface.
    progress = pyqtSignal(str)

    # Constructeur : prepare le dossier de session horodate, les structures de
    # suivi (emails traites, resultats deja envoyes) et l'observateur du dossier
    # de telechargements.
    #   - selected_Browser : navigateur surveille ;
    #   - username : identifiant utilisateur (envoye a l'API) ;
    #   - session_id : identifiant de la session courante ;
    #   - file_lock : verrou partage avec EmailExtractionWorker (emails actifs).
    def __init__(self, selected_Browser, username, session_id, file_lock):
        # Initialise la classe mere QThread.
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username = username
        self.session_id = session_id
        self.file_lock = file_lock
        self.stop_flag = False
        # Dossier surveille : les telechargements de l'utilisateur.
        self.downloads_folder = user_downloads_dir()
        # Horodatage servant a nommer le dossier de session (unique par lancement).
        self.CURRENT_DATETIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.BASE_LOG_DIR = Settings.LOGS_DIRECTORY
        # Dossier de session dedie, cree immediatement, ou seront ranges logs et captures.
        self.SESSION_DIR = os.path.join(self.BASE_LOG_DIR, f"{self.CURRENT_DATETIME}")
        os.makedirs(self.SESSION_DIR, exist_ok=True)
        # Ensembles de suivi : emails deja traites et cles de resultats deja envoyees
        # (evitent les doublons).
        self.completed_emails = set()
        self.reported_results = set()
        # Verrou protegeant les ensembles ci-dessus (acces depuis plusieurs endroits).
        self.lock = threading.Lock()
        # File alimentee par le watcher : chaque nouveau fichier telecharge y arrive.
        self.file_queue = Queue()
        # Observateur watchdog + planification : surveille le dossier (non recursif)
        # et pousse les evenements de fichier dans la file.
        self.observer = Observer()
        self.observer.schedule(DownloadFileEventHandler(self.file_queue), self.downloads_folder, recursive=False)
        Settings.write_log_dev_file(
            f"Thread created | Browser={selected_Browser} | User={username} | downloads_folder={self.downloads_folder} | session_id={self.session_id} | session_dir={self.SESSION_DIR}", "INFO"
        )

    # -------------------------------------------------------------------------
    # Libere le « creneau » d'un email : le retire de l'ensemble des emails
    # actifs (sous le verrou partage file_lock), permettant a un nouvel email
    # d'etre lance a sa place par EmailExtractionWorker.
    # -------------------------------------------------------------------------
    def releaseActiveEmail(self, email):
        if not email:
            return
        # Sous verrou partage : modification thread-safe de l'ensemble des actifs.
        with self.file_lock:
            if email in runtime_state.active_emails:
                runtime_state.active_emails.remove(email)
                Settings.write_log_dev_file(f"Active email slot released: {email} | remaining active accounts={len(runtime_state.active_emails)}", "INFO")

    # -------------------------------------------------------------------------
    # Analyse le NOM d'un fichier pour en extraire les metadonnees
    # (categorie, session_id, email, statut) via un motif d'expression
    # reguliere. Gere aussi les anciens noms (cles « legacy_... »).
    # Renvoie None si le nom ne correspond pas ou si un champ requis manque.
    # -------------------------------------------------------------------------
    @staticmethod
    def parseFilenameMetadata(file_name):
        file_name = os.path.basename(file_name)
        # Application du motif de nom de fichier ; echec -> None.
        match = Settings.FILENAME_METADATA_PATTERN.match(file_name)
        if not match:
            return None

        # Recuperation des groupes nommes, avec repli sur les noms « legacy_... ».
        data = match.groupdict()
        session_id = data.get("session_id") or data.get("legacy_session_id")
        email = data.get("email") or data.get("legacy_email")
        status = data.get("status") or data.get("legacy_status")
        category = data.get("category") or "session"

        # Un champ essentiel manque : metadonnees inexploitables.
        if not session_id or not email or not status:
            return None

        return {"category": category, "session_id": session_id, "email": email, "status": status.lower(), "file_name": file_name}

    # -------------------------------------------------------------------------
    # Renvoie (en le creant) le dossier ou ranger les fichiers d'un email :
    # SESSION_DIR/<navigateur>/<Completed|Not_Completed>/<email>.
    # -------------------------------------------------------------------------
    def getEmailFolder(self, email, status):
        # Sous-dossier selon le statut : « Completed » ou « Not_Completed ».
        status_folder = "Completed" if str(status).lower() == "completed" else "Not_Completed"
        email_folder = os.path.join(self.SESSION_DIR, self.selected_Browser, status_folder, email)
        os.makedirs(email_folder, exist_ok=True)
        return email_folder

    # -------------------------------------------------------------------------
    # Attend qu'un fichier ait fini d'etre ecrit : on considere le fichier
    # stable quand sa taille ne change plus entre deux mesures (0,2 s).
    # Jusqu'a 25 tentatives (~5 s). Renvoie False si arret demande, fichier
    # absent, ou instabilite persistante.
    # -------------------------------------------------------------------------
    def waitForStableFile(self, file_path):
        previous_size = None
        # Au plus 25 verifications espacees de 0,2 s.
        for _ in range(25):
            if self.stop_flag or not os.path.exists(file_path):
                return False
            current_size = os.path.getsize(file_path)
            # Taille inchangee depuis la mesure precedente : le fichier est stable.
            if current_size == previous_size:
                return True
            previous_size = current_size
            time.sleep(0.2)
        return False

    # -------------------------------------------------------------------------
    # Liste les noms des images (.png/.jpg/.jpeg) presentes dans le dossier de
    # telechargements. Une erreur d'acces est journalisee sans interrompre.
    # -------------------------------------------------------------------------
    def getScreenshotFiles(self):
        screenshots = []
        try:
            # Parcours du dossier ; on ne retient que les fichiers image.
            for entry in os.scandir(self.downloads_folder):
                if entry.is_file() and entry.name.lower().endswith((".png", ".jpg", ".jpeg")):
                    screenshots.append(entry.name)
        except OSError as e:
            Settings.write_log_dev_file(
                "[WATCHER] Failed to scan screenshots " f"| exception={type(e).__name__}: {e} " f"| downloads_folder={self.downloads_folder}\n{traceback.format_exc()}", "WARNING"
            )
        return screenshots

    # -------------------------------------------------------------------------
    # Point d'entree pour chaque fichier signale par le watcher.
    #   1. Ne traite que les .txt stabilises (waitForStableFile).
    #   2. Ne retient que les fichiers pertinents (prefixe « log_ »,
    #      metadonnees valides, ou commencant par le session_id).
    #   3. Aiguille vers processLogFile (log) ou processSessionFile (session).
    # -------------------------------------------------------------------------
    def processEventFile(self, file_path):
        file_name = os.path.basename(file_path)
        lower_name = file_name.lower()
        # Ignore les fichiers non .txt ou non encore stables.
        if not lower_name.endswith(".txt") or not self.waitForStableFile(file_path):
            return

        # Filtre : seul un fichier reconnu (log_, metadonnees, ou session_id) est traite.
        metadata = self.parseFilenameMetadata(file_name)
        if not (file_name.startswith("log_") or metadata or file_name.startswith(self.session_id)):
            return

        # Aiguillage : fichier de log vs fichier de session.
        if file_name.startswith("log_"):
            self.processLogFile(file_name)
        else:
            self.processSessionFile(file_name, self.getScreenshotFiles())

    # -------------------------------------------------------------------------
    # Boucle principale du thread de surveillance.
    #   1. Demarre l'observateur de fichiers.
    #   2. Delai initial de 10 s (laisse le temps aux premiers navigateurs).
    #   3. Boucle : recupere un fichier de la file (timeout 0,5 s) et le traite ;
    #      s'arrete quand plus rien n'est en cours (aucun email restant/actif,
    #      aucun processus, file vide) ou sur stop_flag.
    #   4. Arrete proprement l'observateur (bloc finally) et journalise la fin.
    # -------------------------------------------------------------------------
    def run(self):
        # Etape 1 : demarrage de la surveillance du dossier.
        self.observer.start()
        try:
            start_wait = time.time()
            Settings.write_log_dev_file("Filesystem watcher started; waiting initial delay: 10s", "DEBUG")
            # Etape 2 : delai initial de 10 s, interruptible par stop_flag.
            while time.time() - start_wait < 10 and not self.stop_flag:
                time.sleep(0.2)

            # Etape 3 : boucle de consommation de la file de fichiers.
            while not self.stop_flag:
                try:
                    # Attend un fichier au plus 0,5 s ; leve Empty si rien n'arrive.
                    file_path = self.file_queue.get(timeout=0.5)
                except Empty:
                    # File vide ET plus aucun travail en cours -> fin de la surveillance.
                    if runtime_state.remaining_emails == 0 and not runtime_state.process_pids and not runtime_state.active_emails and self.file_queue.empty():
                        break
                    continue

                try:
                    # Traitement du fichier ; toute erreur est journalisee sans arreter la boucle.
                    self.processEventFile(file_path)
                except Exception as e:
                    Settings.write_log_dev_file(f"[WATCHER] Error processing {file_path}: {e}\n{traceback.format_exc()}", "ERROR")
        finally:
            # Etape 4 : arret et attente de l'observateur (toujours execute).
            self.observer.stop()
            self.observer.join(timeout=5)

        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        Settings.write_log_dev_file(f"Thread finished | End time: {end_time} | PROCESS_PIDS: {len(runtime_state.process_pids)} | REMAINING_EMAILS: {runtime_state.remaining_emails}", "INFO")

    # -------------------------------------------------------------------------
    # Retrouve les informations de session d'un email (PID, session_id,
    # inserted_id, PID Firefox, etc.) necessaires pour envoyer le resultat et
    # fermer le navigateur.
    # Sources, selon le navigateur :
    #   - Firefox : d'abord la table en memoire runtime_state.firefox_sessions,
    #     sinon le fichier data.txt du profil ;
    #   - Chromium (chrome/edge/icedragon/comodo) : le fichier data.txt du profil.
    # Renvoie toujours un dictionnaire (valeurs a None si rien n'est trouve).
    # -------------------------------------------------------------------------
    def resolveBrowserSessionFromProfile(self, email):
        if not email:
            return {"pid": None, "session_id": self.session_id, "inserted_id": None, "firefox_pids": [], "web_ext_pid": None, "profile_data_file": None}

        # Nom du navigateur en minuscules (gere le cas None).
        browser_name = (self.selected_Browser or "").lower()
        session_data = {"pid": None, "session_id": self.session_id, "inserted_id": None, "firefox_pids": [], "web_ext_pid": None, "profile_data_file": None}

        # === Cas Firefox ===
        if browser_name == "firefox":
            if email in runtime_state.firefox_sessions:
                firefox_session = runtime_state.firefox_sessions[email]
                session_data["firefox_pids"] = firefox_session.get("firefox_pids", [])
                session_data["web_ext_pid"] = firefox_session.get("web_ext_pid")
                session_data["inserted_id"] = firefox_session.get("inserted_id")
                session_data["session_id"] = firefox_session.get("session_id") or self.session_id
                if session_data["firefox_pids"]:
                    session_data["pid"] = session_data["firefox_pids"][0]
                elif session_data["web_ext_pid"]:
                    session_data["pid"] = session_data["web_ext_pid"]
                return session_data

            # Pas de session en memoire : on lit le fichier data.txt du profil Firefox.
            profile_dir = os.path.join(Settings.FIREFOX_PROFILES, email)
            profile_data_file = os.path.join(profile_dir, "data.txt")
            session_data["profile_data_file"] = profile_data_file
            if os.path.exists(profile_data_file):
                try:
                    with open(profile_data_file, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().strip()
                    if content:
                        # Format attendu : « pid:...:session_id:inserted_id » (au moins 4 champs).
                        parts = content.split(":")
                        if len(parts) >= 4:
                            pid_value = parts[0].strip()
                            session_data["pid"] = int(pid_value) if str(pid_value).isdigit() else None
                            session_data["session_id"] = parts[2].strip() or self.session_id
                            session_data["inserted_id"] = parts[3].strip() or None
                            if isinstance(session_data["pid"], int):
                                session_data["firefox_pids"] = [session_data["pid"]]
                except Exception as e:
                    Settings.write_log_dev_file(
                        "[LOG] Failed to read Firefox session data file " f"| exception={type(e).__name__}: {e} " f"| profile_data_file={profile_data_file}\n{traceback.format_exc()}", "WARNING"
                    )
            return session_data

        # === Cas Chromium (chrome / edge / icedragon / comodo) ===
        profile_dir = None
        # Choix du dossier de profils selon le navigateur.
        if browser_name == "chrome":
            profile_dir = Settings.CHROME_PROFILES
        elif browser_name in {"edge", "icedragon", "comodo"}:
            profile_dir = Settings.CHROMIUM_BROWSER_PATHS.get(browser_name, {}).get("profiles")

        if profile_dir:
            profile_data_file = os.path.join(profile_dir, email, "data.txt")
            session_data["profile_data_file"] = profile_data_file
            if os.path.exists(profile_data_file):
                try:
                    with open(profile_data_file, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().strip()
                    if content:
                        parts = content.split(":")
                        if len(parts) >= 4:
                            pid_value = parts[0].strip()
                            # Plusieurs PID separes par « ; » (cas de double lancement) -> liste d'entiers.
                            if ";" in pid_value:
                                session_data["pid"] = [int(value.strip()) for value in pid_value.split(";") if value.strip().isdigit()]
                            else:
                                session_data["pid"] = int(pid_value) if pid_value.isdigit() else None
                            session_data["session_id"] = parts[2].strip() or self.session_id
                            session_data["inserted_id"] = parts[3].strip() or None
                except Exception as e:
                    Settings.write_log_dev_file(
                        "[LOG] Failed to read profile session data file " f"| exception={type(e).__name__}: {e} " f"| profile_data_file={profile_data_file}\n{traceback.format_exc()}", "WARNING"
                    )
        return session_data

    # -------------------------------------------------------------------------
    # Deplace la capture d'ecran « capture_...<email>... » du dossier de
    # telechargements vers le dossier de l'email. Renvoie le chemin cible ou None.
    # -------------------------------------------------------------------------
    def moveAssociatedScreenshot(self, email, email_folder):
        try:
            if not os.path.isdir(email_folder):
                os.makedirs(email_folder, exist_ok=True)
            # Recherche d'un fichier capture correspondant a cet email.
            for file_name in os.listdir(self.downloads_folder):
                lower_name = file_name.lower()
                # Fichier capture associe a cet email : on le deplace (en ecrasant l'existant).
                if lower_name.startswith("capture_") and email.lower() in lower_name:
                    source_path = os.path.join(self.downloads_folder, file_name)
                    target_path = os.path.join(email_folder, file_name)
                    if os.path.exists(source_path):
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        shutil.move(source_path, target_path)
                        Settings.write_log_dev_file(f"[LOG] Screenshot moved to email folder: {target_path}", "INFO")
                        return target_path
        except Exception as e:
            Settings.write_log_dev_file(f"⚠️ [SCREENSHOT] Error moving screenshot for {email}: {e}\n{traceback.format_exc()}", "ERROR")
        return None

    # -------------------------------------------------------------------------
    # Traite un fichier de LOG depose par l'extension.
    #   1. Determine l'email/statut/session (metadonnees du nom, sinon contenu).
    #   2. Ignore l'email s'il a deja ete traite.
    #   3. Copie le log dans le dossier de l'email et deplace la capture.
    #   4. Ecrit le resultat, l'envoie a l'API, ferme le navigateur, libere
    #      l'email et supprime le fichier source.
    # -------------------------------------------------------------------------
    def processLogFile(self, log_file):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [LOG] Stop requested", "INFO")
            return

        full_path = os.path.join(self.downloads_folder, log_file)
        metadata = self.parseFilenameMetadata(full_path)
        Settings.write_log_dev_file(f"[LOG] Starting log file processing: {log_file} | full_path={full_path} | metadata={metadata}", "DEBUG")

        try:
            if not os.path.exists(full_path):
                Settings.write_log_dev_file(f"[LOG] File not found during processing: {full_path}", "ERROR")
                return

            email = None
            status = None
            session_id = self.session_id
            if metadata:
                email = metadata.get("email")
                status = metadata.get("status")
                session_id = metadata.get("session_id") or session_id

            if not email:
                # Email absent des metadonnees : on tente de l'extraire du contenu du log.
                email = ValidationUtils.extractEmailFromLogFile(full_path)

            if not email:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    sample = f.read(256)
                Settings.write_log_dev_file(f"No email found in log file content sample: {sample!r}", "ERROR")
                return

            # Recuperation des infos de session (PID, inserted_id...) pour cet email.
            session_lookup = self.resolveBrowserSessionFromProfile(email)
            if not session_id:
                session_id = session_lookup.get("session_id") or self.session_id
            if not status:
                status = "unknown"
            pid = session_lookup.get("pid")
            inserted_id = session_lookup.get("inserted_id")
            firefox_pids = session_lookup.get("firefox_pids", [])
            web_ext_pid = session_lookup.get("web_ext_pid")

            Settings.write_log_dev_file(f"[LOG] Extracted email from log file: {email} | status={status} | session_id={session_id} | pid={pid}", "DEBUG")

            if status:
                Settings.write_log_dev_file(f"[LOG] Status parsed from filename: {status}", "INFO")

            with self.lock:
                # Email deja traite : on ignore ce log (evite les doublons).
                if email in self.completed_emails:
                    Settings.write_log_dev_file(f"Email {email} already processed, skipping log file: {log_file}", "INFO")
                    return

            email_folder = self.getEmailFolder(email, status)
            Settings.write_log_dev_file(f"[LOG] Email folder ensured: {email_folder}", "DEBUG")

            # Copie du contenu du log dans un fichier dedie du dossier de l'email.
            target_log = os.path.join(email_folder, f"{email}_{self.CURRENT_DATETIME}.txt")
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            Settings.write_log_dev_file(f"[LOG] Read log file content length: {len(content)}", "DEBUG")

            with open(target_log, "a", encoding="utf-8") as tf:
                tf.write(content + "\n")
            Settings.write_log_dev_file(f"[LOG] Appended log to target file: {target_log}", "DEBUG")

            self.moveAssociatedScreenshot(email, email_folder)

            # Toutes les infos presentes : on finalise (resultat + API + fermeture +
            # liberation du creneau).
            if status and session_id and email:
                self.writeResultAndSendStatus(session_id, pid, email, status, inserted_id)
                self.closeBrowserSession(pid, email, self.selected_Browser, firefox_pids, web_ext_pid, "-LOG")
                with self.lock:
                    self.completed_emails.add(email)
                self.releaseActiveEmail(email)

            # Suppression du fichier de log source une fois traite.
            os.remove(full_path)
            Settings.write_log_dev_file(f"✅ [LOG] Processed and removed source file: {full_path}", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(
                # Gestion d'erreur : tout echec du traitement du log est journalise avec la
                # pile d'appels.
                f"❌ [LOG] Erreur processing log file {full_path}: {e}\n{traceback.format_exc()}",  "ERROR" )

    # -------------------------------------------------------------------------
    # Ferme une session Firefox : tue chaque PID Firefox connu, puis le PID de
    # web-ext, et retire ce dernier de la liste des processus suivis.
    # flow_label sert uniquement a distinguer l'origine dans les logs.
    # -------------------------------------------------------------------------
    def closeFirefoxSession(self, firefox_pids, web_ext_pid, email, flow_label=""):
        if firefox_pids:
            Settings.write_log_dev_file(f"[CLOSE{flow_label}] Closing Firefox PIDs: {firefox_pids} for {email}", "INFO")
            # Tentative d'arret de chaque processus Firefox (s'il existe encore).
            for firefox_pid in firefox_pids:
                try:
                    if psutil.pid_exists(firefox_pid):
                        psutil.Process(firefox_pid).kill()
                        Settings.write_log_dev_file(f"[CLOSE{flow_label}] Firefox PID {firefox_pid} killed successfully", "INFO")
                    else:
                        Settings.write_log_dev_file(f"[CLOSE{flow_label}] Firefox PID {firefox_pid} no longer exists", "INFO")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    Settings.write_log_dev_file(
                        f"[CLOSE{flow_label}] Error closing Firefox PID {firefox_pid} " f"| exception={type(e).__name__}: {e} " f"| email={email}\n{traceback.format_exc()}", "WARNING"
                    )
        else:
            Settings.write_log_dev_file(f"No Firefox PIDs for {email} {flow_label}".strip(), "WARNING")

        # Arret du processus web-ext associe.
        if web_ext_pid:
            try:
                if psutil.pid_exists(web_ext_pid):
                    psutil.Process(web_ext_pid).kill()
                    Settings.write_log_dev_file(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} killed successfully", "INFO")
                else:
                    Settings.write_log_dev_file(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} no longer exists", "INFO")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                Settings.write_log_dev_file(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} already closed", "INFO")

        # Retrait du PID web-ext de la liste des processus suivis.
        if web_ext_pid in runtime_state.process_pids:
            runtime_state.process_pids.remove(web_ext_pid)
            Settings.write_log_dev_file(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} removed from PROCESS_PIDS queue", "INFO")

    # -------------------------------------------------------------------------
    # Ferme la session du navigateur : delegue a closeFirefoxSession pour
    # Firefox, sinon ferme le(s) processus Chromium via closeBrowserProcess.
    # -------------------------------------------------------------------------
    def closeBrowserSession(self, pid, email, browser, firefox_pids, web_ext_pid, flow_label=""):
        if browser.lower() == "firefox":
            self.closeFirefoxSession(firefox_pids, web_ext_pid, email, flow_label)
        else:
            if pid:
                self.closeBrowserProcess(pid, email, browser)
                Settings.write_log_dev_file(f"[CLOSE{flow_label}] Process {pid} closed for {email}", "INFO")
            else:
                Settings.write_log_dev_file(f"No PID for {email} {flow_label}".strip(), "WARNING")

    # -------------------------------------------------------------------------
    # Traite un fichier de SESSION depose par l'extension.
    #   1. Lit le contenu et en extrait session_id/email/etat par expression
    #      reguliere.
    #   2. Recupere les PID selon le navigateur (Firefox en memoire, Chromium
    #      via data.txt).
    #   3. Flux « leger » (completed / bad_proxy) : resultat + fermeture + retour.
    #   4. Flux « erreur » : deplace la capture d'ecran puis resultat + fermeture.
    #   5. bloc finally : supprime le fichier de session et nettoie les donnees
    #      de session/profil.
    # -------------------------------------------------------------------------
    def processSessionFile(self, file_name, screenshots):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [SESSION] Stop requested", "INFO")
            return

        session_path = os.path.join(self.downloads_folder, file_name)
        Settings.write_log_dev_file(f"[SESSION] Starting processing: {file_name} | full_path={session_path}", "DEBUG")

        if not os.path.exists(session_path):
            Settings.write_log_dev_file(f"Session file not found: {session_path}", "ERROR")
            return

        try:
            with open(session_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            Settings.write_log_dev_file(f"[SESSION] Read content length={len(content)}", "DEBUG")
            Settings.write_log_dev_file(f"[SESSION] Content preview: {content[:200]!r}", "TRACE" if hasattr(Settings, "TRACE") else "DEBUG")

            # Etape 1 : extraction de session_id / email / etat depuis le contenu.
            regex = r"session_id:(\w+)_email:([\w.@+-]+)_etat:(\w+)"
            match = re.search(regex, content, re.IGNORECASE)
            Settings.write_log_dev_file(f"[SESSION] Using regex={regex} | match_found={bool(match)}", "DEBUG")

            if not match:
                Settings.write_log_dev_file(
                    # Contenu illisible : on abandonne le traitement de ce fichier.
                    f"❌ [SESSION] Parsing failed for file: {file_name}",
                    "ERROR",
                )
                return

            session_id, email, status = match.groups()
            pid = None
            inserted_id = None
            firefox_pids = []
            web_ext_pid = None
            profile_data_file = None
            Settings.write_log_dev_file(f"[SESSION] Parsed session_id={session_id} email={email} status={status}", "INFO")

            # Etape 2 : recuperation des PID selon le navigateur (cas Firefox).
            if self.selected_Browser.lower() == "firefox":
                Settings.write_log_dev_file(f"[SESSION] Firefox browser detected, looking up FIREFOX_SESSIONS[{email}]", "DEBUG")
                if email in runtime_state.firefox_sessions:
                    firefox_session = runtime_state.firefox_sessions[email]
                    Settings.write_log_dev_file(f"[SESSION] Firefox session found: {json.dumps(firefox_session, ensure_ascii=False, default=str)}", "DEBUG")
                    firefox_pids = firefox_session.get("firefox_pids", [])
                    web_ext_pid = firefox_session.get("web_ext_pid")
                    inserted_id = firefox_session.get("inserted_id")
                    pid = firefox_pids
                    Settings.write_log_dev_file(f"[SESSION] Firefox extracted firefox_pids={firefox_pids} web_ext_pid={web_ext_pid} inserted_id={inserted_id}", "INFO")
                else:
                    Settings.write_log_dev_file(f"❌ [SESSION] Firefox session not found in FIREFOX_SESSIONS for email={email}", "ERROR")
                    Settings.write_log_dev_file(f"[SESSION] Available keys in FIREFOX_SESSIONS: {list(runtime_state.firefox_sessions.keys())}", "WARNING")
            else:
                profile_dir = Settings.CHROME_PROFILES
                if self.selected_Browser.lower() == "edge":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["edge"]["profiles"]
                elif self.selected_Browser.lower() == "icedragon":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["icedragon"]["profiles"]
                elif self.selected_Browser.lower() == "comodo":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["comodo"]["profiles"]

                profile_data_file = os.path.join(profile_dir, email, "data.txt")
                Settings.write_log_dev_file(f"[SESSION] Chromium profile data path: {profile_data_file}", "DEBUG")
                if os.path.exists(profile_data_file):
                    with open(profile_data_file, "r", encoding="utf-8", errors="replace") as f:
                        # Cas Chromium : lecture de la premiere ligne de data.txt (pid:email:session:id).
                        profile_line = f.readline().strip()
                    Settings.write_log_dev_file(f"[SESSION] Chromium profile data line: {profile_line}", "DEBUG")
                    try:
                        pid, email_chk, session_id_chk, inserted_id = profile_line.split(":")[:4]
                        Settings.write_log_dev_file(f"[SESSION] Chromium extracted pid={pid} email_chk={email_chk} session_id_chk={session_id_chk} inserted_id={inserted_id}", "INFO")
                    except ValueError as e:
                        Settings.write_log_dev_file(
                            "🚨 [SESSION] Failed to parse Chromium profile line "
                            f"| exception={type(e).__name__}: {e} "
                            f"| profile_line={profile_line} "
                            f"| email={email}\n{traceback.format_exc()}",
                            "ERROR",
                        )
                else:
                    Settings.write_log_dev_file(f"Chromium profile data file not found for {email} at {profile_data_file}", "ERROR")

            Settings.write_log_dev_file(f"Session found | Email: {email} | Status: {status} | PID: {pid} | inserted_id: {inserted_id}", "DEBUG")
            email_folder = self.getEmailFolder(email, status)
            Settings.write_log_dev_file(f"[SESSION] Email folder ensured: {email_folder}", "DEBUG")

            # Etape 3 : flux « leger » (succes ou mauvais proxy) : on finalise et on sort.
            if status.lower() in ("completed", "bad_proxy"):
                Settings.write_log_dev_file(f"✅ LIGHT FLOW | {email}", "DEBUG")

                with self.lock:
                    self.completed_emails.add(email)

                self.writeResultAndSendStatus(session_id, pid, email, status, inserted_id)
                self.closeBrowserSession(pid, email, self.selected_Browser, firefox_pids, web_ext_pid)
                self.releaseActiveEmail(email)
                return

            Settings.write_log_dev_file(f"ERROR FLOW detected for session {session_id} email={email} status={status}", "DEBUG")
            # Etape 4 : flux « erreur » : on conserve la capture d'ecran comme preuve.
            self.moveScreenshot(email, screenshots, email_folder)
            self.writeResultAndSendStatus(session_id, pid, email, status, inserted_id)
            self.closeBrowserSession(pid, email, self.selected_Browser, firefox_pids, web_ext_pid, "-ERROR")
            self.releaseActiveEmail(email)
        except Exception as e:
            Settings.write_log_dev_file(
                # Gestion d'erreur du traitement de session (journalisee avec la trace).
                f"❌ [SESSION] Erreur: {e}\n{traceback.format_exc()}",
                "ERROR",
            )

        finally:
            try:
                # Etape 5 (finally) : suppression du fichier de session, quoi qu'il arrive.
                if os.path.exists(session_path):
                    os.remove(session_path)
                    Settings.write_log_dev_file(f"[CLEANUP] Removed session file: {session_path}", "DEBUG")
            except Exception as e:
                Settings.write_log_dev_file("❌ [CLEANUP] Error removing session file " f"| exception={type(e).__name__}: {e} " f"| session_path={session_path}\n{traceback.format_exc()}", "DEBUG")

            if self.selected_Browser.lower() == "firefox":
                if email in runtime_state.firefox_sessions:
                    # Nettoyage : retrait de la session Firefox en memoire.
                    del runtime_state.firefox_sessions[email]
                    Settings.write_log_dev_file(f"[CLEANUP] Removed Firefox session for {email}", "DEBUG")
            else:
                try:
                    # Nettoyage : suppression du fichier data.txt du profil Chromium.
                    if profile_data_file and os.path.exists(profile_data_file):
                        os.remove(profile_data_file)
                        Settings.write_log_dev_file(f"[CLEANUP] Removed chromium profile data file: {profile_data_file}", "DEBUG")
                except Exception as e:
                    Settings.write_log_dev_file(f"❌ [CLEANUP] Error removing profile data file: {e}\n{traceback.format_exc()}", "DEBUG")

    # -------------------------------------------------------------------------
    # Enregistre le resultat d'un email et l'envoie a l'API.
    #   1. Ignore les resultats en double (cle email+statut deja envoyee).
    #   2. Ecrit une ligne « session:pid:email:statut » dans le fichier resultat.
    #   3. Envoie le statut a l'API (OK si completed, sinon NotOK + motif).
    #   4. Gestion d'erreur : en cas d'echec, retire la cle des resultats envoyes
    #      et leve SystemExit(1) (l'API a -1 est traitee comme une erreur).
    # -------------------------------------------------------------------------
    def writeResultAndSendStatus(self, session_id, pid, email, status, inserted_id):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [RESULT] Stop requested", "INFO")
            return

        # Cle de dedoublonnage : email + statut, insensibles a la casse.
        result_key = (str(email).strip().casefold(), str(status).strip().casefold())
        with self.lock:
            # Resultat deja envoye pour ce couple email/statut : on ignore.
            if result_key in self.reported_results:
                Settings.write_log_dev_file(f"Duplicate result ignored for {email} with status {status}", "WARNING")
                return
            self.reported_results.add(result_key)

        try:
            # Etape 2 : ajout d'une ligne de resultat dans le fichier partage.
            result_line = f"{session_id}:{pid}:{email}:{status}"
            with open(Settings.RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(f"{result_line}\n")
            Settings.write_log_event("result_written", "INFO", status=status, result_file=Settings.RESULT_FILE_PATH)

            # Etape 3 : donnees envoyees a l'API (statut OK/NotOK et motif eventuel).
            api_data = {"id": inserted_id, "login": self.username, "status": "OK" if status.lower() == "completed" else "NotOK", "error": "" if status.lower() == "completed" else status}

            # Appel de l'API et journalisation du code de reponse.
            result = str(API_MANAGER.sendStatus(api_data))
            Settings.write_log_event("status_api_response", "INFO", response_type=type(result).__name__, response_code=(result if result in {"-1", "-2", "-3", "-4", "-5"} else "received"))

            # Reponse -1 : erreur cote API -> on leve une exception.
            if result == "-1":
                Settings.write_log_dev_file(f"API returned -1 for {email}", level="ERROR")
                raise RuntimeError(f"API returned -1 for {email}")

        # SystemExit : on annule l'enregistrement du resultat et on relaie l'arret.
        except SystemExit:
            with self.lock:
                self.reported_results.discard(result_key)
            raise
        except Exception as e:
            with self.lock:
                self.reported_results.discard(result_key)
            Settings.write_log_dev_file(
                # Autre erreur : annulation de la cle envoyee, log detaille, puis SystemExit(1).
                f"❌ [RESULT] Erreur: {e} details: {traceback.format_exc()}",
                "ERROR",
            )
            raise SystemExit(1)

    # -------------------------------------------------------------------------
    # Deplace la premiere capture d'ecran dont le nom contient l'email vers le
    # dossier de l'email, renommee « <email>.png ». Erreur journalisee.
    # -------------------------------------------------------------------------
    def moveScreenshot(self, email, screenshots, email_folder):
        try:
            # Recherche d'une capture correspondant a l'email.
            for img in screenshots:
                if email.lower() in img.lower():
                    shutil.move(os.path.join(self.downloads_folder, img), os.path.join(email_folder, f"{email}.png"))
                    break
        except Exception as e:
            Settings.write_log_dev_file(f"⚠️ [SCREENSHOT] Erreur: {e}\n{traceback.format_exc()}", "ERROR")

    # -------------------------------------------------------------------------
    # Ferme un (ou plusieurs) processus navigateur Chromium par PID.
    #   1. Normalise pid en liste d'entiers (accepte un entier, une chaine, ou
    #      une liste/ensemble ; ignore les valeurs non numeriques).
    #   2. Pour chaque PID : SIGTERM, puis, si toujours vivant, terminate() +
    #      attente ; chaque echec est journalise.
    #   3. Retire les PID fermes de la liste des processus suivis.
    # -------------------------------------------------------------------------
    def closeBrowserProcess(self, pid, email, browser):
        Settings.write_log_dev_file(f"_close_browser_process start | browser={browser} | email={email} | pid={repr(pid)} | pid_type={type(pid).__name__}", "DEBUG")

        try:
            if pid is None:
                Settings.write_log_dev_file(f"No PID provided for {email} ({browser})", "WARNING")
                return

            pid_list = []
            # Cas d'une collection de PID : on convertit chaque element en entier.
            if isinstance(pid, (list, tuple, set)):
                for item in pid:
                    item_str = str(item).strip()
                    if item_str.isdigit():
                        pid_list.append(int(item_str))
                    else:
                        Settings.write_log_dev_file(f"Skipped non-numeric PID segment in list: {repr(item)}", "WARNING")
            else:
                pid_str = str(pid).strip()
                if pid_str.isdigit():
                    pid_list = [int(pid_str)]
                else:
                    Settings.write_log_dev_file(f"Invalid PID value for Chromium family: {repr(pid)}", "ERROR")
                    return

            Settings.write_log_dev_file(f"_close_browser_process computed pid_list={pid_list}", "DEBUG")
            if not pid_list:
                Settings.write_log_dev_file(f"No valid PID to close for {email} ({browser})", "WARNING")
                return

            # Fermeture de chaque PID de la liste calculee, AVEC ses processus enfants
            # (Chrome/Comodo lance des sous-processus : renderers, GPU, utilitaires...).
            # On ne ferme QUE l'arbre de ce PID : les autres instances du navigateur
            # (autres arbres de processus) ne sont pas touchees.
            for current_pid in pid_list:
                try:
                    # Recupere le processus parent. S'il n'existe plus, il est deja ferme.
                    try:
                        parent = psutil.Process(current_pid)
                    except psutil.NoSuchProcess:
                        Settings.write_log_dev_file(f"PID {current_pid} n'existe plus (deja ferme)", "INFO")
                        parent = None

                    if parent is not None:
                        # IMPORTANT : on collecte les enfants AVANT de tuer le parent
                        # (sinon ils sont reparentes et deviennent introuvables).
                        try:
                            children = parent.children(recursive=True)
                        except psutil.NoSuchProcess:
                            children = []

                        # Cible = enfants d'abord, puis le parent.
                        procs_to_close = children + [parent]

                        # 1) Arret « doux » (terminate) de tout l'arbre.
                        for proc in procs_to_close:
                            try:
                                proc.terminate()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e_term:
                                Settings.write_log_dev_file(f"terminate() ignore pour PID {getattr(proc, 'pid', '?')}: {type(e_term).__name__}", "DEBUG")

                        # 2) Attend la fin, puis tue de force ceux qui survivent (kill).
                        _, alive = psutil.wait_procs(procs_to_close, timeout=3)
                        for proc in alive:
                            try:
                                proc.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e_kill:
                                Settings.write_log_dev_file(f"kill() ignore pour PID {getattr(proc, 'pid', '?')}: {type(e_kill).__name__}", "DEBUG")

                        Settings.write_log_dev_file(f"Chrome ferme | PID={current_pid} | enfants={len(children)}", "INFO")
                except Exception as e_chrome:
                    Settings.write_log_dev_file(
                        # Echec de fermeture d'un PID precis : journalise, on passe au suivant.
                        f"Error closing Chrome PID {current_pid}: {e_chrome}\n{traceback.format_exc()}", "ERROR" )

                if current_pid in runtime_state.process_pids:
                    runtime_state.process_pids.remove(current_pid)
                    Settings.write_log_dev_file(f"PID {current_pid} removed from PROCESS_PIDS", "INFO")

        except Exception as e:
            
                # Erreur globale de la procedure de fermeture (journalisee avec la trace).
            Settings.write_log_dev_file( f"❌ [CLOSE] Erreur: {e}\n{traceback.format_exc()}", "ERROR")
