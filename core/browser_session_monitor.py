import datetime
import json
import os
import re
import shutil
import signal
import threading
import time
import traceback
from queue import Empty, Queue

import psutil
from platformdirs import user_downloads_dir
from PyQt6.QtCore import QThread, pyqtSignal
from watchdog.observers import Observer

from api import API_MANAGER
from config import Settings
from core.file_watcher import DownloadFileEventHandler
from core.runtime_state import runtime_state
from models import BrowserManager
from utils import ValidationUtils


class BrowserSessionMonitorThread(QThread):
    progress = pyqtSignal(str)

    def __init__(self, selected_Browser, username, session_id, file_lock):
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username = username
        self.session_id = session_id
        self.file_lock = file_lock
        self.stop_flag = False
        self.downloads_folder = user_downloads_dir()
        self.CURRENT_DATETIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.BASE_LOG_DIR = Settings.LOGS_DIRECTORY
        self.SESSION_DIR = os.path.join(self.BASE_LOG_DIR, f"{self.CURRENT_DATETIME}")
        os.makedirs(self.SESSION_DIR, exist_ok=True)
        self.completed_emails = set()
        self.reported_results = set()
        self.lock = threading.Lock()
        self.file_queue = Queue()
        self.observer = Observer()
        self.observer.schedule(
            DownloadFileEventHandler(self.file_queue),
            self.downloads_folder,
            recursive=False,
        )
        Settings.write_log_dev_file(
            f"Thread created | Browser={selected_Browser} | User={username} | downloads_folder={self.downloads_folder} | session_id={self.session_id} | session_dir={self.SESSION_DIR}",
            "INFO",
        )

    def releaseActiveEmail(self, email):
        if not email:
            return
        with self.file_lock:
            if email in runtime_state.active_emails:
                runtime_state.active_emails.remove(email)
                Settings.write_log_dev_file(
                    f"Active email slot released: {email} | remaining active accounts={len(runtime_state.active_emails)}",
                    "INFO",
                )

    @staticmethod
    def parseFilenameMetadata(file_name):
        file_name = os.path.basename(file_name)
        match = Settings.FILENAME_METADATA_PATTERN.match(file_name)
        if not match:
            return None

        data = match.groupdict()
        session_id = data.get("session_id") or data.get("legacy_session_id")
        email = data.get("email") or data.get("legacy_email")
        status = data.get("status") or data.get("legacy_status")
        category = data.get("category") or "session"

        if not session_id or not email or not status:
            return None

        return {
            "category": category,
            "session_id": session_id,
            "email": email,
            "status": status.lower(),
            "file_name": file_name,
        }

    def getEmailFolder(self, email, status):
        status_folder = (
            "Completed" if str(status).lower() == "completed" else "Not_Completed"
        )
        email_folder = os.path.join(
            self.SESSION_DIR, self.selected_Browser, status_folder, email
        )
        os.makedirs(email_folder, exist_ok=True)
        return email_folder

    def waitForStableFile(self, file_path):
        previous_size = None
        for _ in range(25):
            if self.stop_flag or not os.path.exists(file_path):
                return False
            current_size = os.path.getsize(file_path)
            if current_size == previous_size:
                return True
            previous_size = current_size
            time.sleep(0.2)
        return False

    def getScreenshotFiles(self):
        screenshots = []
        try:
            for entry in os.scandir(self.downloads_folder):
                if entry.is_file() and entry.name.lower().endswith(
                    (".png", ".jpg", ".jpeg")
                ):
                    screenshots.append(entry.name)
        except OSError as e:
            Settings.write_log_dev_file(
                f"[WATCHER] Failed to scan screenshots: {e}", "WARNING"
            )
        return screenshots

    def processEventFile(self, file_path):
        file_name = os.path.basename(file_path)
        lower_name = file_name.lower()
        if not lower_name.endswith(".txt") or not self.waitForStableFile(file_path):
            return

        metadata = self.parseFilenameMetadata(file_name)
        if not (
            file_name.startswith("log_")
            or metadata
            or file_name.startswith(self.session_id)
        ):
            return

        if file_name.startswith("log_"):
            self.processLogFile(file_name)
        else:
            self.processSessionFile(file_name, self.getScreenshotFiles())

    def run(self):
        self.observer.start()
        try:
            start_wait = time.time()
            Settings.write_log_dev_file(
                "Filesystem watcher started; waiting initial delay: 10s", "DEBUG"
            )
            while time.time() - start_wait < 10 and not self.stop_flag:
                time.sleep(0.2)

            while not self.stop_flag:
                try:
                    file_path = self.file_queue.get(timeout=0.5)
                except Empty:
                    if (
                        runtime_state.remaining_emails == 0
                        and not runtime_state.process_pids
                        and not runtime_state.active_emails
                        and self.file_queue.empty()
                    ):
                        break
                    continue

                try:
                    self.processEventFile(file_path)
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"[WATCHER] Error processing {file_path}: {e}\n{traceback.format_exc()}",
                        "ERROR",
                    )
        finally:
            self.observer.stop()
            self.observer.join(timeout=5)

        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        Settings.write_log_dev_file(
            f"Thread finished | End time: {end_time} | PROCESS_PIDS: {len(runtime_state.process_pids)} | REMAINING_EMAILS: {runtime_state.remaining_emails}",
            "INFO",
        )

    def resolveBrowserSessionFromProfile(self, email):
        if not email:
            return {
                "pid": None,
                "session_id": self.session_id,
                "inserted_id": None,
                "firefox_pids": [],
                "web_ext_pid": None,
                "profile_data_file": None,
            }

        browser_name = (self.selected_Browser or "").lower()
        session_data = {
            "pid": None,
            "session_id": self.session_id,
            "inserted_id": None,
            "firefox_pids": [],
            "web_ext_pid": None,
            "profile_data_file": None,
        }

        if browser_name == "firefox":
            if email in runtime_state.firefox_sessions:
                firefox_session = runtime_state.firefox_sessions[email]
                session_data["firefox_pids"] = firefox_session.get("firefox_pids", [])
                session_data["web_ext_pid"] = firefox_session.get("web_ext_pid")
                session_data["inserted_id"] = firefox_session.get("inserted_id")
                session_data["session_id"] = (
                    firefox_session.get("session_id") or self.session_id
                )
                if session_data["firefox_pids"]:
                    session_data["pid"] = session_data["firefox_pids"][0]
                elif session_data["web_ext_pid"]:
                    session_data["pid"] = session_data["web_ext_pid"]
                return session_data

            profile_dir = os.path.join(Settings.FIREFOX_PROFILES, email)
            profile_data_file = os.path.join(profile_dir, "data.txt")
            session_data["profile_data_file"] = profile_data_file
            if os.path.exists(profile_data_file):
                try:
                    with open(
                        profile_data_file, "r", encoding="utf-8", errors="replace"
                    ) as f:
                        content = f.read().strip()
                    if content:
                        parts = content.split(":")
                        if len(parts) >= 4:
                            pid_value = parts[0].strip()
                            session_data["pid"] = (
                                int(pid_value) if str(pid_value).isdigit() else None
                            )
                            session_data["session_id"] = (
                                parts[2].strip() or self.session_id
                            )
                            session_data["inserted_id"] = parts[3].strip() or None
                            if isinstance(session_data["pid"], int):
                                session_data["firefox_pids"] = [session_data["pid"]]
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"[LOG] Failed to read Firefox session data file {profile_data_file}: {e}",
                        "WARNING",
                    )
            return session_data

        profile_dir = None
        if browser_name == "chrome":
            profile_dir = Settings.CHROME_PROFILES
        elif browser_name in {"edge", "icedragon", "comodo"}:
            profile_dir = Settings.CHROMIUM_BROWSER_PATHS.get(browser_name, {}).get(
                "profiles"
            )

        if profile_dir:
            profile_data_file = os.path.join(profile_dir, email, "data.txt")
            session_data["profile_data_file"] = profile_data_file
            if os.path.exists(profile_data_file):
                try:
                    with open(
                        profile_data_file, "r", encoding="utf-8", errors="replace"
                    ) as f:
                        content = f.read().strip()
                    if content:
                        parts = content.split(":")
                        if len(parts) >= 4:
                            pid_value = parts[0].strip()
                            if ";" in pid_value:
                                session_data["pid"] = [
                                    int(value.strip())
                                    for value in pid_value.split(";")
                                    if value.strip().isdigit()
                                ]
                            else:
                                session_data["pid"] = (
                                    int(pid_value) if pid_value.isdigit() else None
                                )
                            session_data["session_id"] = (
                                parts[2].strip() or self.session_id
                            )
                            session_data["inserted_id"] = parts[3].strip() or None
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"[LOG] Failed to read profile session data file {profile_data_file}: {e}",
                        "WARNING",
                    )
        return session_data

    def moveAssociatedScreenshot(self, email, email_folder):
        try:
            if not os.path.isdir(email_folder):
                os.makedirs(email_folder, exist_ok=True)
            for file_name in os.listdir(self.downloads_folder):
                lower_name = file_name.lower()
                if lower_name.startswith("capture_") and email.lower() in lower_name:
                    source_path = os.path.join(self.downloads_folder, file_name)
                    target_path = os.path.join(email_folder, file_name)
                    if os.path.exists(source_path):
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        shutil.move(source_path, target_path)
                        Settings.write_log_dev_file(
                            f"[LOG] Screenshot moved to email folder: {target_path}",
                            "INFO",
                        )
                        return target_path
        except Exception as e:
            Settings.write_log_dev_file(
                f"⚠️ [SCREENSHOT] Error moving screenshot for {email}: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
        return None

    def processLogFile(self, log_file):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [LOG] Stop requested", "INFO")
            return

        full_path = os.path.join(self.downloads_folder, log_file)
        metadata = self.parseFilenameMetadata(full_path)
        Settings.write_log_dev_file(
            f"[LOG] Starting log file processing: {log_file} | full_path={full_path} | metadata={metadata}",
            "DEBUG",
        )

        try:
            if not os.path.exists(full_path):
                Settings.write_log_dev_file(
                    f"[LOG] File not found during processing: {full_path}", "ERROR"
                )
                return

            email = None
            status = None
            session_id = self.session_id
            if metadata:
                email = metadata.get("email")
                status = metadata.get("status")
                session_id = metadata.get("session_id") or session_id

            if not email:
                email = ValidationUtils.extractEmailFromLogFile(full_path)

            if not email:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    sample = f.read(256)
                Settings.write_log_dev_file(
                    f"No email found in log file content sample: {sample!r}", "ERROR"
                )
                return

            session_lookup = self.resolveBrowserSessionFromProfile(email)
            if not session_id:
                session_id = session_lookup.get("session_id") or self.session_id
            if not status:
                status = "unknown"
            pid = session_lookup.get("pid")
            inserted_id = session_lookup.get("inserted_id")
            firefox_pids = session_lookup.get("firefox_pids", [])
            web_ext_pid = session_lookup.get("web_ext_pid")

            Settings.write_log_dev_file(
                f"[LOG] Extracted email from log file: {email} | status={status} | session_id={session_id} | pid={pid}",
                "DEBUG",
            )

            if status:
                Settings.write_log_dev_file(
                    f"[LOG] Status parsed from filename: {status}", "INFO"
                )

            with self.lock:
                if email in self.completed_emails:
                    Settings.write_log_dev_file(
                        f"Email {email} already processed, skipping log file: {log_file}",
                        "INFO",
                    )
                    return

            email_folder = self.getEmailFolder(email, status)
            Settings.write_log_dev_file(
                f"[LOG] Email folder ensured: {email_folder}", "DEBUG"
            )

            target_log = os.path.join(
                email_folder, f"{email}_{self.CURRENT_DATETIME}.txt"
            )
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            Settings.write_log_dev_file(
                f"[LOG] Read log file content length: {len(content)}", "DEBUG"
            )

            with open(target_log, "a", encoding="utf-8") as tf:
                tf.write(content + "\n")
            Settings.write_log_dev_file(
                f"[LOG] Appended log to target file: {target_log}", "DEBUG"
            )

            self.moveAssociatedScreenshot(email, email_folder)

            if status and session_id and email:
                self.writeResultAndSendStatus(
                    session_id, pid, email, status, inserted_id
                )
                self.closeBrowserSession(
                    pid, email, self.selected_Browser, firefox_pids, web_ext_pid, "-LOG"
                )
                with self.lock:
                    self.completed_emails.add(email)
                self.releaseActiveEmail(email)

            os.remove(full_path)
            Settings.write_log_dev_file(
                f"✅ [LOG] Processed and removed source file: {full_path}", "INFO"
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ [LOG] Erreur processing log file {full_path}: {e}\n{traceback.format_exc()}",
                "ERROR",
            )

    def closeFirefoxSession(self, firefox_pids, web_ext_pid, email, flow_label=""):
        if firefox_pids:
            Settings.write_log_dev_file(
                f"[CLOSE{flow_label}] Closing Firefox PIDs: {firefox_pids} for {email}",
                "INFO",
            )
            for firefox_pid in firefox_pids:
                try:
                    if psutil.pid_exists(firefox_pid):
                        psutil.Process(firefox_pid).kill()
                        Settings.write_log_dev_file(
                            f"[CLOSE{flow_label}] Firefox PID {firefox_pid} killed successfully",
                            "INFO",
                        )
                    else:
                        Settings.write_log_dev_file(
                            f"[CLOSE{flow_label}] Firefox PID {firefox_pid} no longer exists",
                            "INFO",
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    Settings.write_log_dev_file(
                        f"[CLOSE{flow_label}] Error closing Firefox PID {firefox_pid}: {e}",
                        "WARNING",
                    )
        else:
            Settings.write_log_dev_file(
                f"No Firefox PIDs for {email} {flow_label}".strip(), "WARNING"
            )

        if web_ext_pid:
            try:
                if psutil.pid_exists(web_ext_pid):
                    psutil.Process(web_ext_pid).kill()
                    Settings.write_log_dev_file(
                        f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} killed successfully",
                        "INFO",
                    )
                else:
                    Settings.write_log_dev_file(
                        f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} no longer exists",
                        "INFO",
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                Settings.write_log_dev_file(
                    f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} already closed",
                    "INFO",
                )

        if web_ext_pid in runtime_state.process_pids:
            runtime_state.process_pids.remove(web_ext_pid)
            Settings.write_log_dev_file(
                f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} removed from PROCESS_PIDS queue",
                "INFO",
            )

    # ==========================================================
    # FERMETURE GÉNÉRIQUE DE LA SESSION DU NAVIGATEUR
    #
    # Point d'entrée unique pour fermer les processus du navigateur en
    # fonction du type de navigateur (Firefox ou navigateur basé sur Chromium).
    #
    # Responsabilités :
    # - Diriger la logique de fermeture selon le type de navigateur
    # - Utiliser le nettoyage spécifique à Firefox si le navigateur est Firefox
    # - Utiliser la terminaison générique des processus pour les navigateurs Chromium
    # - Prévoir un repli sûr quand le PID est absent
    # ==========================================================

    def closeBrowserSession(
        self, pid, email, browser, firefox_pids, web_ext_pid, flow_label=""
    ):
        if browser.lower() == "firefox":
            self.closeFirefoxSession(firefox_pids, web_ext_pid, email, flow_label)
        else:
            if pid:
                self.closeBrowserProcess(pid, email, browser)
                Settings.write_log_dev_file(
                    f"[CLOSE{flow_label}] Process {pid} closed for {email}", "INFO"
                )
            else:
                Settings.write_log_dev_file(
                    f"No PID for {email} {flow_label}".strip(), "WARNING"
                )

    # ==========================================================
    # ANALYSEUR ET TRAITEMENT DES FICHIERS DE SESSION
    #
    # Cette fonction gère les fichiers de session du navigateur et extrait
    # les informations sur l'état d'exécution.
    #
    # Responsabilités :
    # - Analyser session_id, e-mail et statut via regex
    # - Récupérer les informations sur les processus selon le navigateur
    # - Gérer les sessions Firefox depuis le registre mémoire
    # - Gérer les sessions Chromium depuis les fichiers de profil sur disque
    # - Exécuter la logique de succès ou d'erreur
    # - Fermer proprement les processus associés
    # - Déplacer les captures d'écran si le flux d'erreur est déclenché
    # - Nettoyer les fichiers de session après traitement
    # ==========================================================

    def processSessionFile(self, file_name, screenshots):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [SESSION] Stop requested", "INFO")
            return

        session_path = os.path.join(self.downloads_folder, file_name)
        Settings.write_log_dev_file(
            f"[SESSION] Starting processing: {file_name} | full_path={session_path}",
            "DEBUG",
        )

        if not os.path.exists(session_path):
            Settings.write_log_dev_file(
                f"Session file not found: {session_path}", "ERROR"
            )
            return

        try:
            with open(session_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            Settings.write_log_dev_file(
                f"[SESSION] Read content length={len(content)}", "DEBUG"
            )
            Settings.write_log_dev_file(
                f"[SESSION] Content preview: {content[:200]!r}",
                "TRACE" if hasattr(Settings, "TRACE") else "DEBUG",
            )

            regex = r"session_id:(\w+)_email:([\w.@+-]+)_etat:(\w+)"
            match = re.search(regex, content, re.IGNORECASE)
            Settings.write_log_dev_file(
                f"[SESSION] Using regex={regex} | match_found={bool(match)}", "DEBUG"
            )

            if not match:
                Settings.write_log_dev_file(
                    f"❌ [SESSION] Parsing failed for file: {file_name}", "ERROR"
                )
                return

            session_id, email, status = match.groups()
            pid = None
            inserted_id = None
            firefox_pids = []
            web_ext_pid = None
            profile_data_file = None
            Settings.write_log_dev_file(
                f"[SESSION] Parsed session_id={session_id} email={email} status={status}",
                "INFO",
            )

            if self.selected_Browser.lower() == "firefox":
                Settings.write_log_dev_file(
                    f"[SESSION] Firefox browser detected, looking up FIREFOX_SESSIONS[{email}]",
                    "DEBUG",
                )
                if email in runtime_state.firefox_sessions:
                    firefox_session = runtime_state.firefox_sessions[email]
                    Settings.write_log_dev_file(
                        f"[SESSION] Firefox session found: {json.dumps(firefox_session, ensure_ascii=False, default=str)}",
                        "DEBUG",
                    )
                    firefox_pids = firefox_session.get("firefox_pids", [])
                    web_ext_pid = firefox_session.get("web_ext_pid")
                    inserted_id = firefox_session.get("inserted_id")
                    pid = firefox_pids
                    Settings.write_log_dev_file(
                        f"[SESSION] Firefox extracted firefox_pids={firefox_pids} web_ext_pid={web_ext_pid} inserted_id={inserted_id}",
                        "INFO",
                    )
                else:
                    Settings.write_log_dev_file(
                        f"❌ [SESSION] Firefox session not found in FIREFOX_SESSIONS for email={email}",
                        "ERROR",
                    )
                    Settings.write_log_dev_file(
                        f"[SESSION] Available keys in FIREFOX_SESSIONS: {list(runtime_state.firefox_sessions.keys())}",
                        "WARNING",
                    )
            else:
                profile_dir = Settings.CHROME_PROFILES
                if self.selected_Browser.lower() == "edge":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["edge"]["profiles"]
                elif self.selected_Browser.lower() == "icedragon":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["icedragon"][
                        "profiles"
                    ]
                elif self.selected_Browser.lower() == "comodo":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["comodo"]["profiles"]

                profile_data_file = os.path.join(profile_dir, email, "data.txt")
                Settings.write_log_dev_file(
                    f"[SESSION] Chromium profile data path: {profile_data_file}",
                    "DEBUG",
                )
                if os.path.exists(profile_data_file):
                    with open(
                        profile_data_file, "r", encoding="utf-8", errors="replace"
                    ) as f:
                        profile_line = f.readline().strip()
                    Settings.write_log_dev_file(
                        f"[SESSION] Chromium profile data line: {profile_line}", "DEBUG"
                    )
                    try:
                        pid, email_chk, session_id_chk, inserted_id = (
                            profile_line.split(":")[:4]
                        )
                        Settings.write_log_dev_file(
                            f"[SESSION] Chromium extracted pid={pid} email_chk={email_chk} session_id_chk={session_id_chk} inserted_id={inserted_id}",
                            "INFO",
                        )
                    except ValueError as e:
                        Settings.write_log_dev_file(
                            f"🚨 [SESSION] Failed to parse Chromium profile line: {profile_line} | error={e}",
                            "ERROR",
                        )
                else:
                    Settings.write_log_dev_file(
                        f"Chromium profile data file not found for {email} at {profile_data_file}",
                        "ERROR",
                    )

            Settings.write_log_dev_file(
                f"Session found | Email: {email} | Status: {status} | PID: {pid} | inserted_id: {inserted_id}",
                "DEBUG",
            )
            email_folder = self.getEmailFolder(email, status)
            Settings.write_log_dev_file(
                f"[SESSION] Email folder ensured: {email_folder}", "DEBUG"
            )

            if status.lower() in ("completed", "bad_proxy"):
                Settings.write_log_dev_file(f"✅ LIGHT FLOW | {email}", "DEBUG")

                with self.lock:
                    self.completed_emails.add(email)

                self.writeResultAndSendStatus(
                    session_id, pid, email, status, inserted_id
                )
                self.closeBrowserSession(
                    pid, email, self.selected_Browser, firefox_pids, web_ext_pid
                )
                self.releaseActiveEmail(email)
                return

            Settings.write_log_dev_file(
                f"ERROR FLOW detected for session {session_id} email={email} status={status}",
                "DEBUG",
            )
            self.moveScreenshot(email, screenshots, email_folder)
            self.writeResultAndSendStatus(session_id, pid, email, status, inserted_id)
            self.closeBrowserSession(
                pid, email, self.selected_Browser, firefox_pids, web_ext_pid, "-ERROR"
            )
            self.releaseActiveEmail(email)
        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ [SESSION] Erreur: {e}\n{traceback.format_exc()}", "ERROR"
            )

        finally:
            try:
                if os.path.exists(session_path):
                    os.remove(session_path)
                    Settings.write_log_dev_file(
                        f"[CLEANUP] Removed session file: {session_path}", "DEBUG"
                    )
            except Exception as e:
                Settings.write_log_dev_file(
                    f"❌ [CLEANUP] Error removing session file: {e}", "DEBUG"
                )

            if self.selected_Browser.lower() == "firefox":
                if email in runtime_state.firefox_sessions:
                    del runtime_state.firefox_sessions[email]
                    Settings.write_log_dev_file(
                        f"[CLEANUP] Removed Firefox session for {email}", "DEBUG"
                    )
            else:
                try:
                    if profile_data_file and os.path.exists(profile_data_file):
                        os.remove(profile_data_file)
                        Settings.write_log_dev_file(
                            f"[CLEANUP] Removed chromium profile data file: {profile_data_file}",
                            "DEBUG",
                        )
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"❌ [CLEANUP] Error removing profile data file: {e}\n{traceback.format_exc()}",
                        "DEBUG",
                    )

    # ==========================================================
    # ENREGISTREMENT DU RÉSULTAT DE SESSION + ENVOI API
    #
    # Cette fonction gère le reporting final de la session en :
    #
    # Responsabilités :
    # - Écrire le résultat de la session dans un fichier local
    # - Formater le résultat sous la forme : session_id:pid:email:status
    # - Envoyer la mise à jour du statut à l'API externe
    # - Mapper le statut vers le format OK / NotOK
    # - Gérer proprement les cas d'échec de l'API
    # ==========================================================

    def writeResultAndSendStatus(self, session_id, pid, email, status, inserted_id):
        if self.stop_flag:
            Settings.write_log_dev_file("🛑 [RESULT] Stop requested", "INFO")
            return

        result_key = (str(email).strip().casefold(), str(status).strip().casefold())
        with self.lock:
            if result_key in self.reported_results:
                Settings.write_log_dev_file(
                    f"Duplicate result ignored for {email} with status {status}",
                    "WARNING",
                )
                return
            self.reported_results.add(result_key)

        try:
            result_line = f"{session_id}:{pid}:{email}:{status}"
            with open(Settings.RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(f"{result_line}\n")
            Settings.write_log_event(
                "result_written",
                "INFO",
                status=status,
                result_file=Settings.RESULT_FILE_PATH,
            )

            api_data = {
                "id": inserted_id,
                "login": self.username,
                "status": "OK" if status.lower() == "completed" else "NotOK",
                "error": "" if status.lower() == "completed" else status,
            }

            result = str(API_MANAGER.sendStatus(api_data))
            Settings.write_log_event(
                "status_api_response",
                "INFO",
                response_type=type(result).__name__,
                response_code=result
                if result in {"-1", "-2", "-3", "-4", "-5"}
                else "received",
            )

            if result == "-1":
                Settings.write_log_dev_file(
                    f"API returned -1 for {email}", level="ERROR"
                )
                raise RuntimeError(f"API returned -1 for {email}")

        except SystemExit:
            with self.lock:
                self.reported_results.discard(result_key)
            raise
        except Exception as e:
            with self.lock:
                self.reported_results.discard(result_key)
            Settings.write_log_dev_file(
                f"❌ [RESULT] Erreur: {e} details: {traceback.format_exc()}", "ERROR"
            )
            raise SystemExit(1)

    # ==========================================================
    # GESTIONNAIRE D'ORGANISATION DES CAPTURES D'ÉCRAN
    #
    # Cette fonction déplace les captures d'écran générées par le navigateur
    # vers le dossier correct de session/e-mail.
    #
    # Responsabilités :
    # - Associer les captures d'écran à la session e-mail correspondante
    # - Déplacer les images depuis le dossier de téléchargements vers le dossier de session
    # - Renommer ou organiser les captures d'écran pour un stockage structuré
    # - Vérifier qu'aucune capture en double ou hors sujet n'est déplacée
    # ==========================================================

    def moveScreenshot(self, email, screenshots, email_folder):
        try:
            for img in screenshots:
                if email.lower() in img.lower():
                    shutil.move(
                        os.path.join(self.downloads_folder, img),
                        os.path.join(email_folder, f"{email}.png"),
                    )
                    break
        except Exception as e:
            Settings.write_log_dev_file(
                f"⚠️ [SCREENSHOT] Erreur: {e}\n{traceback.format_exc()}", "ERROR"
            )

    # ==========================================================
    # TERMINAISON GÉNÉRIQUE DES PROCESSUS (NON-FIREFOX)
    #
    # Cette fonction termine proprement les processus du navigateur via leur PID.
    #
    # Responsabilités :
    # - Analyser les PID d'entrée (format unique ou liste)
    # - Tuer le processus via un signal système (SIGTERM)
    # - Forcer l'arrêt si le processus ne s'arrête pas
    # - Retirer le PID nettoyé de la liste PROCESS_PIDS
    # - Empêcher les processus zombie ou orphelins
    # ==========================================================

    def closeBrowserProcess(self, pid, email, browser):
        Settings.write_log_dev_file(
            f"_close_browser_process start | browser={browser} | email={email} | pid={repr(pid)} | pid_type={type(pid).__name__}",
            "DEBUG",
        )

        try:
            if pid is None:
                Settings.write_log_dev_file(
                    f"No PID provided for {email} ({browser})", "WARNING"
                )
                return

            pid_list = []
            if isinstance(pid, (list, tuple, set)):
                for item in pid:
                    item_str = str(item).strip()
                    if item_str.isdigit():
                        pid_list.append(int(item_str))
                    else:
                        Settings.write_log_dev_file(
                            f"Skipped non-numeric PID segment in list: {repr(item)}",
                            "WARNING",
                        )
            else:
                pid_str = str(pid).strip()
                if pid_str.isdigit():
                    pid_list = [int(pid_str)]
                else:
                    Settings.write_log_dev_file(
                        f"Invalid PID value for Chromium family: {repr(pid)}", "ERROR"
                    )
                    return

            Settings.write_log_dev_file(
                f"_close_browser_process computed pid_list={pid_list}", "DEBUG"
            )
            if not pid_list:
                Settings.write_log_dev_file(
                    f"No valid PID to close for {email} ({browser})", "WARNING"
                )
                return

            for current_pid in pid_list:
                try:
                    os.kill(current_pid, signal.SIGTERM)
                    time.sleep(2)
                    if psutil.pid_exists(current_pid):
                        p = psutil.Process(current_pid)
                        p.terminate()
                        p.wait(timeout=3)
                        Settings.write_log_dev_file(
                            f"Chrome closed via terminate() for PID {current_pid}",
                            "INFO",
                        )
                    else:
                        Settings.write_log_dev_file(
                            f"Chrome closed via SIGTERM for PID {current_pid}", "INFO"
                        )
                except Exception as e_chrome:
                    Settings.write_log_dev_file(
                        f"Error closing Chrome PID {current_pid}: {e_chrome}\n{traceback.format_exc()}",
                        "ERROR",
                    )

                if current_pid in runtime_state.process_pids:
                    runtime_state.process_pids.remove(current_pid)
                    Settings.write_log_dev_file(
                        f"PID {current_pid} removed from PROCESS_PIDS", "INFO"
                    )

        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ [CLOSE] Erreur: {e}\n{traceback.format_exc()}", "ERROR"
            )
