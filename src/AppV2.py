import os
import json
from queue import Empty, Queue
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QCursor, QColor, QPixmap, QGuiApplication, QTextCursor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6 import uic
import shutil
import signal
import time
import subprocess
import re
import datetime
import sys
import urllib3
import psutil
from platformdirs import user_downloads_dir
import win32gui
import win32con
import copy
import warnings
import threading
from threading import Lock
from pathlib import Path
from PyQt6.QtWidgets import QInputDialog
import base64
import requests
from typing import List, Dict, Any, Set
import traceback
from collections import deque
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


try:
    from config import Settings as Settings
    from core import EncryptionService
    from core import SessionManager
    from models import BrowserManager
    from api import API_MANAGER
    from utils import ValidationUtils
    from ui_utils import UIManager
    from services import JsonManager
    from Update import UpdateManager
except ImportError as e:
    Settings.write_log_event(
        "app_import_failed",
        "ERROR",
        file=__file__,
        exception_type=type(e).__name__,
        error=str(e),
    )
    sys.exit(1)


file_lock = Lock()
FIREFOX_SESSIONS: Dict[str, Any] = {}
LOGS = deque()
PROCESS_PIDS = []
NOTIFICATION_BADGES = {}
EXTRACTION_THREAD = None
CLOSE_BROWSER_THREAD = None
NEW_VERSION = None
LOGS_RUNNING = True
SELECTED_BROWSER_GLOBAL = None
REMAINING_EMAILS = 0
ACTIVE_EMAILS = set()


SESSION_ID = ValidationUtils.generateSessionId()


def logMessage(text):
    global LOGS
    LOGS.append(text)


def stopAllProcesses(window, show_idle_warning=True):
    UIManager.disableButton(window.stopButton)
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD
    global PROCESS_PIDS, LOGS_RUNNING, FIREFOX_SESSIONS, ACTIVE_EMAILS
    global SELECTED_BROWSER_GLOBAL
    Settings.write_log_dev_file("Stopping all processes...", "INFO")
    LOGS_RUNNING = False

    try:
        if EXTRACTION_THREAD:
            Settings.write_log_dev_file("Stopping extraction thread...", "INFO")
            EXTRACTION_THREAD.stop_flag = True
            EXTRACTION_THREAD.wait()
            EXTRACTION_THREAD = None
            Settings.write_log_dev_file(
                "Extraction thread stopped successfully.", "INFO"
            )
    except Exception as e:
        Settings.write_log_event(
            "thread_stop_failed",
            "ERROR",
            thread_name="extraction",
            exception_type=type(e).__name__,
            error=str(e),
        )

    try:
        if CLOSE_BROWSER_THREAD:
            Settings.write_log_dev_file("Stopping close browser thread...", "INFO")
            CLOSE_BROWSER_THREAD.stop_flag = True
            CLOSE_BROWSER_THREAD.wait()
            CLOSE_BROWSER_THREAD = None
            Settings.write_log_dev_file(
                "Close browser thread stopped successfully.", "INFO"
            )
    except Exception as e:
        Settings.write_log_event(
            "thread_stop_failed",
            "ERROR",
            thread_name="browser_close",
            exception_type=type(e).__name__,
            error=str(e),
        )

    if not SELECTED_BROWSER_GLOBAL:
        Settings.write_log_dev_file(
            "Stop failed: No browser selected or no processes running.", "WARNING"
        )
        if show_idle_warning:
            UIManager.showCriticalMessage(
                window,
                "No Processes Running",
                "No processes are currently running.",
                message_type="warning",
            )
        UIManager.enableButton(window.submitButton)
        UIManager.enableButton(window.stopButton)
        ACTIVE_EMAILS.clear()
        return
    browser_name = SELECTED_BROWSER_GLOBAL.lower()

    if browser_name != "firefox":
        for pid in PROCESS_PIDS[:]:
            try:
                Settings.write_log_dev_file(
                    f"Attempting to terminate process with PID {pid}...", "INFO"
                )
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                    Settings.write_log_dev_file(
                        f"Process {pid} terminated successfully.", "INFO"
                    )
                except psutil.TimeoutExpired:
                    Settings.write_log_dev_file(
                        f"Timeout for PID {pid}, forcing kill...", "WARNING"
                    )
                    process.kill()
                    try:
                        process.wait(timeout=3)
                        Settings.write_log_dev_file(
                            f"Process {pid} killed successfully.", "INFO"
                        )
                    except psutil.NoSuchProcess:
                        Settings.write_log_dev_file(
                            f"Process {pid} already closed after kill.", "INFO"
                        )
                    except psutil.TimeoutExpired:
                        Settings.write_log_dev_file(
                            f"Failed to kill PID {pid} after timeout.", "ERROR"
                        )
                except psutil.NoSuchProcess:
                    Settings.write_log_dev_file(
                        f"Process {pid} already terminated.", "INFO"
                    )
            except psutil.NoSuchProcess:
                Settings.write_log_dev_file(f"Process {pid} no longer exists.", "INFO")
            except psutil.AccessDenied:
                Settings.write_log_dev_file(
                    f"Permission denied for PID {pid}.", "WARNING"
                )
            except Exception as e:
                Settings.write_log_dev_file(
                    f"Unexpected error terminating PID {pid}: {e}\n{traceback.format_exc()}",
                    "ERROR",
                )
            finally:
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                    Settings.write_log_dev_file(
                        f"PID {pid} removed from process list.", "INFO"
                    )
    else:
        try:
            Settings.write_log_dev_file(
                "Closing Firefox profiles using stored session entries...", "INFO"
            )
            if FIREFOX_SESSIONS:
                session_entries = list(FIREFOX_SESSIONS.values())
                Settings.write_log_dev_file(
                    f"Closing {len(session_entries)} Firefox session entries", "DEBUG"
                )
                BrowserManager.closeFirefoxProcesses(session_entries)
            else:
                Settings.write_log_dev_file(
                    "No Firefox sessions found, unable to close Firefox profiles.",
                    "WARNING",
                )
            Settings.write_log_dev_file("Firefox profiles closed successfully.", "INFO")
        except Exception as e:
            Settings.write_log_dev_file(
                f"Error closing Firefox profiles: {e}\n{traceback.format_exc()}",
                "WARNING",
            )
        finally:
            if PROCESS_PIDS:
                for pid in PROCESS_PIDS[:]:
                    PROCESS_PIDS.remove(pid)
                    Settings.write_log_dev_file(
                        f"PID {pid} removed from process list.", "INFO"
                    )
            if FIREFOX_SESSIONS:
                FIREFOX_SESSIONS.clear()
                Settings.write_log_dev_file("FIREFOX_SESSIONS cleared", "DEBUG")
            ACTIVE_EMAILS.clear()
    ACTIVE_EMAILS.clear()
    UIManager.enableButton(window.submitButton)
    UIManager.enableButton(window.stopButton)
    Settings.write_log_dev_file("All stop operations completed.", "INFO")


class ApplicationLogDisplayThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, LOGS, parent=None):
        super().__init__(parent)
        self.LOGS = LOGS
        self.stop_flag = False

    def run(self):
        global LOGS_RUNNING
        while LOGS_RUNNING:
            if self.LOGS:
                log_entry = self.LOGS.popleft()
                self.log_signal.emit(log_entry)
            else:
                time.sleep(1)

    def stopThread(self):
        self.stop_flag = True
        self.wait()


class DownloadFileEventHandler(FileSystemEventHandler):
    def __init__(self, file_queue):
        super().__init__()
        self.file_queue = file_queue

    def on_created(self, event):
        if not event.is_directory:
            self.file_queue.put(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.file_queue.put(event.dest_path)


class BrowserSessionMonitorThread(QThread):
    progress = pyqtSignal(str)

    def __init__(self, selected_Browser, username):
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username = username
        self.session_id = SESSION_ID
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
        with file_lock:
            if email in ACTIVE_EMAILS:
                ACTIVE_EMAILS.remove(email)
                Settings.write_log_dev_file(
                    f"Active email slot released: {email} | remaining active accounts={len(ACTIVE_EMAILS)}",
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
        global PROCESS_PIDS, REMAINING_EMAILS, ACTIVE_EMAILS

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
                        REMAINING_EMAILS == 0
                        and not PROCESS_PIDS
                        and not ACTIVE_EMAILS
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
            f"Thread finished | End time: {end_time} | PROCESS_PIDS: {len(PROCESS_PIDS)} | REMAINING_EMAILS: {REMAINING_EMAILS}",
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
            if email in FIREFOX_SESSIONS:
                firefox_session = FIREFOX_SESSIONS[email]
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

        if web_ext_pid in PROCESS_PIDS:
            PROCESS_PIDS.remove(web_ext_pid)
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
                if email in FIREFOX_SESSIONS:
                    firefox_session = FIREFOX_SESSIONS[email]
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
                        f"[SESSION] Available keys in FIREFOX_SESSIONS: {list(FIREFOX_SESSIONS.keys())}",
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
                if email in FIREFOX_SESSIONS:
                    del FIREFOX_SESSIONS[email]
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

                if current_pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(current_pid)
                    Settings.write_log_dev_file(
                        f"PID {current_pid} removed from PROCESS_PIDS", "INFO"
                    )

        except Exception as e:
            Settings.write_log_dev_file(
                f"❌ [CLOSE] Erreur: {e}\n{traceback.format_exc()}", "ERROR"
            )


def startExtraction(
    window,
    data_list,
    entered_number,
    selected_Browser,
    Isp,
    unique_id,
    output_json_final,
    username,
):

    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD

    try:
        entered_number = int(entered_number)
    except ValueError:
        UIManager.showCriticalMessage(
            window,
            "Input Error - Invalid Format",
            "Numeric value required. Please check your input and try again.",
            message_type="critical",
        )
        Settings.write_log_dev_file(
            "Numeric value required. Please check your input and try again.", "ERROR"
        )
        return

    email_count = len(data_list)
    if entered_number > email_count:
        UIManager.showCriticalMessage(
            window,
            "Range Error - Exceeded Limit",
            f"Maximum allowed entries: {email_count}\n Please enter a value between 1 and {email_count}.",
            message_type="critical",
        )
        Settings.write_log_dev_file(
            f"Maximum allowed entries: {email_count}\nPlease enter a value between 1 and {email_count}.",
            "ERROR",
        )
        return

    Settings.write_log_dev_file(f"Selected entries: {entered_number}", "INFO")
    browser_normalized = (
        selected_Browser.lower() if isinstance(selected_Browser, str) else "unknown"
    )
    Settings.write_log_dev_file(
        f"Browser selection normalized: {browser_normalized}", "INFO"
    )

    browser_path = BrowserManager.get_browser_executable_path(browser_normalized)

    browser_name = (
        selected_Browser.strip() if isinstance(selected_Browser, str) else "Unknown"
    )
    browser_path_display = browser_path or "Non trouvé"
    Settings.write_log_dev_file(
        f"Browser startup details | Browser selected: {browser_name} | Executable path: {browser_path_display} | Extraction stage: initialisation",
        "INFO",
    )

    if selected_Browser.lower() == "firefox":
        Settings.ensure_web_ext_installed()

    EXTRACTION_THREAD = EmailExtractionWorker(
        window,
        data_list,
        SESSION_ID,
        entered_number,
        browser_path,
        window,
        selected_Browser,
        Isp,
        unique_id,
        output_json_final,
    )

    EXTRACTION_THREAD.finished.connect(lambda: window.extraction_finished(window))
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.stopped.connect(
        lambda msg: UIManager.showCriticalMessage(
            window, "Arrêté", msg, message_type="warning"
        )
    )
    EXTRACTION_THREAD.finished.connect(
        lambda: UIManager.showCriticalMessage(
            window, "Terminé", "L'extraction est terminée.", message_type="success"
        )
    )
    EXTRACTION_THREAD.start()

    def launch_browser_session_monitor():
        global CLOSE_BROWSER_THREAD
        Settings.write_log_dev_file("Launching BrowserSessionMonitorThread...", "INFO")
        CLOSE_BROWSER_THREAD = BrowserSessionMonitorThread(selected_Browser, username)
        CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
        CLOSE_BROWSER_THREAD.start()

    QTimer.singleShot(0, launch_browser_session_monitor)


class EmailExtractionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    stopped = pyqtSignal(str)

    def __init__(
        self,
        window,
        data_list,
        SESSION_ID,
        entered_number,
        Browser_path,
        main_window,
        selected_Browser,
        Isp,
        unique_id,
        output_json_final,
    ):
        super().__init__()
        self.window = window
        self.data_list = data_list
        self.session_id = SESSION_ID
        self.entered_number = entered_number
        self.Browser_path = Browser_path
        self.stop_flag = False
        self.emails_processed = 0
        self.selected_Browser = (
            selected_Browser.strip().lower()
            if isinstance(selected_Browser, str)
            else "unknown"
        )
        self.main_window = main_window
        self.Isp = Isp
        self.unique_id = unique_id
        self.output_json_final = output_json_final

    def buildEncryptedUrl(
        self,
        ip_address,
        port,
        login,
        password,
        profile_email,
        profile_password,
        recovery_email,
        new_password,
        new_recovery_email,
        output_json_final,
    ):
        result_payload = json.dumps(
            output_json_final, ensure_ascii=False, separators=(",", ":")
        )
        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email};{self.session_id};{result_payload}"
        try:
            b64 = EncryptionService.encrypt_aes_gcm(
                "A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined
            )
            url = f"{Settings.ENCRYPTED_PROXY_API}?rep={b64}"
        except Exception:
            Settings.write_log_dev_file(
                f"Error encrypting data for URL: {traceback.format_exc()} ", "ERROR"
            )
            url = ""
        return url

    # ==========================================================
    # PID PARSING - Parse Firefox PID lists ("1001; 2002; abc; 3003" → [1001, 2002, 3003])
    # ==========================================================

    def parsePidList(self, pid_value):
        if pid_value is None:
            Settings.write_log_dev_file(
                "_parse_pid_list received None pid_value", "DEBUG"
            )
            return []
        pid_str = str(pid_value).strip()
        if not pid_str:
            Settings.write_log_dev_file(
                "_parse_pid_list received empty pid string", "DEBUG"
            )
            return []
        pids = []
        for part in pid_str.split(";"):
            part = part.strip()
            if part.isdigit():
                pids.append(int(part))
            else:
                Settings.write_log_dev_file(
                    f"_parse_pid_list skipped non-digit segment: '{part}'", "WARNING"
                )
        Settings.write_log_dev_file(
            f"_parse_pid_list parsed PIDs: {pids} from '{pid_str}'", "DEBUG"
        )
        return pids

    def run(self):
        global PROCESS_PIDS, LOGS_RUNNING, SELECTED_BROWSER_GLOBAL, REMAINING_EMAILS, ACTIVE_EMAILS
        SELECTED_BROWSER_GLOBAL = self.selected_Browser
        REMAINING_EMAILS_QUEUE = deque(self.data_list)
        REMAINING_EMAILS = len(REMAINING_EMAILS_QUEUE)

        logMessage("[INFO] Processing started")
        Settings.write_log_dev_file(
            f"EmailExtractionWorker started with browser={self.selected_Browser} | Browser_path={self.Browser_path}",
            "INFO",
        )

        session_info = SessionManager.check_session()

        if not session_info["valid"]:
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            Settings.write_log_dev_file("Invalid session. Please reconnect.", "ERROR")
            return

        try:
            if self.selected_Browser.lower() == "firefox":
                extension_data_path = os.path.join(
                    Settings.EXTENTION_EX3_FIREFOX, "data.txt"
                )
            else:
                extension_data_path = os.path.join(
                    Settings.EXTENTION_EX3_CHROMIUM, "data.txt"
                )

            os.makedirs(os.path.dirname(extension_data_path), exist_ok=True)

            with open(extension_data_path, "w", encoding="utf-8") as f:
                f.write(f"{self.session_id}\n")
            Settings.write_log_dev_file(
                f"Wrote session_id to extension data file: {extension_data_path}",
                "INFO",
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Failed to write session_id to extension data file: {extension_data_path} | error={e}\n{traceback.format_exc()}",
                "ERROR",
            )

        while REMAINING_EMAILS_QUEUE or ACTIVE_EMAILS:
            if self.stop_flag:
                LOGS_RUNNING = False
                logMessage("[INFO] Processing interrupted by user.")
                Settings.write_log_dev_file("Processing interrupted by user.", "INFO")
                break

            if len(ACTIVE_EMAILS) < self.entered_number and REMAINING_EMAILS_QUEUE:
                next_email = REMAINING_EMAILS_QUEUE.popleft()
                REMAINING_EMAILS = len(REMAINING_EMAILS_QUEUE)
                email_value = ValidationUtils.getValueFromDictionary(
                    next_email, ["email", "Email"]
                )
                logMessage(f"[INFO] Processing the email:  {email_value}")
                Settings.write_log_dev_file(
                    f"Processing the email: {email_value}", "INFO"
                )

                try:
                    profile_email = ValidationUtils.getValueFromDictionary(
                        next_email, ["email", "Email"]
                    )
                    profile_password = ValidationUtils.getValueFromDictionary(
                        next_email, ["password_email", "passwordEmail"]
                    )
                    ip_address = ValidationUtils.getValueFromDictionary(
                        next_email, ["ip_address", "ipAddress"]
                    )
                    port = ValidationUtils.getValueFromDictionary(next_email, ["port"])
                    login = ValidationUtils.getValueFromDictionary(
                        next_email, ["login"]
                    )
                    password = ValidationUtils.getValueFromDictionary(
                        next_email, ["password"]
                    )
                    recovery_email = ValidationUtils.getValueFromDictionary(
                        next_email, ["recovery_email", "recoveryEmail"]
                    )
                    new_recovery_email = ValidationUtils.getValueFromDictionary(
                        next_email, ["new_recovery_email", "neWrecoveryEmail"]
                    )

                    params = {
                        "l": EncryptionService.encrypt_message(
                            session_info["username"], Settings.KEY
                        ),
                        "login": session_info["username"],
                        "entity": session_info["p_entity_Origine"],
                        "isp": self.Isp,
                        "action": json.dumps(self.output_json_final),
                        "email": email_value,
                        "password": "",
                        "proxy_ip": ip_address + ":" + port,
                        "proxy_login": (
                            f"{login};{password}"
                            if login != session_info["username"]
                            else ""
                        ),
                        "email_recovery": "",
                        "line": "",
                        "app": "V4",
                        "e_pid": self.unique_id,
                    }

                    inserted_id = str(API_MANAGER.saveEmail(params))
                    new_password = ValidationUtils.generateSecurePassword(16)

                    try:
                        os.makedirs(Settings.LOGS_DIRECTORY, exist_ok=True)
                        logs_subdirs = [
                            os.path.join(Settings.LOGS_DIRECTORY, d)
                            for d in os.listdir(Settings.LOGS_DIRECTORY)
                            if os.path.isdir(os.path.join(Settings.LOGS_DIRECTORY, d))
                        ]
                        logs_subdirs.sort(key=os.path.getctime)

                        if len(logs_subdirs) > 4:
                            to_delete = logs_subdirs[:4]
                            for dir_to_delete in to_delete:
                                try:
                                    shutil.rmtree(dir_to_delete)
                                except Exception as e:
                                    Settings.write_log_dev_file(
                                        f"Error while deleting {dir_to_delete} : {e}\n{traceback.format_exc()}",
                                        "ERROR",
                                    )

                    except Exception as e:
                        Settings.write_log_dev_file(
                            f"Error accessing or creating log directory {Settings.LOGS_DIRECTORY} : {e}\n{traceback.format_exc()}",
                            "ERROR",
                        )
                        logs_subdirs = []

                    if self.selected_Browser.lower() == "firefox":
                        url = self.buildEncryptedUrl(
                            ip_address,
                            port,
                            login,
                            password,
                            profile_email,
                            profile_password,
                            recovery_email,
                            new_password,
                            new_recovery_email,
                            self.output_json_final,
                        )
                        firefox_profile_path = BrowserManager.createFirefoxProfile(
                            profile_email
                        )

                        if not firefox_profile_path:
                            Settings.write_log_dev_file(
                                f"❌ [Firefox] Impossible de créer le profil Firefox pour {profile_email}",
                                "ERROR",
                            )
                            logMessage(
                                f"[ERROR] Impossible de créer le profil Firefox pour {profile_email}"
                            )
                            continue

                        Settings.write_log_dev_file(
                            f"✅ [Firefox] Profil créé/vérifié: {firefox_profile_path}",
                            "INFO",
                        )

                        eb_ext_path = Settings.get_web_ext_path()

                        if not eb_ext_path:
                            Settings.write_log_dev_file(
                                f"❌ [Firefox] web-ext non trouvé", "ERROR"
                            )
                            logMessage("[ERROR] web-ext introuvable")
                            continue

                        command = [
                            eb_ext_path,
                            "run",
                            "--source-dir",
                            Settings.EXTENTION_EX3_FIREFOX,
                            "--firefox-profile",
                            os.path.join(Settings.FIREFOX_PROFILES, profile_email),
                            "--url",
                            f"{url}",
                            "--keep-profile-changes",
                            "--no-reload",
                        ]

                        Settings.write_log_dev_file(
                            f"Launching Firefox with command: {command}", "DEBUG"
                        )
                        Settings.write_log_dev_file(
                            f"Firefox profile directory: {os.path.join(Settings.FIREFOX_PROFILES, profile_email)}",
                            "DEBUG",
                        )

                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        PROCESS_PIDS.append(process.pid)
                        Settings.write_log_dev_file(
                            f"Firefox web-ext PID: {process.pid}", "INFO"
                        )

                        firefox_pids = BrowserManager.findFirefoxProcessIds(
                            firefox_profile_path, process.pid
                        )

                        if not firefox_pids:
                            Settings.write_log_dev_file(
                                "Aucune PID Firefox détectée immédiatement après lancement, attente de 2 secondes puis nouvelle recherche",
                                "WARNING",
                            )
                            time.sleep(2)
                            firefox_pids = BrowserManager.findFirefoxProcessIds(
                                firefox_profile_path, process.pid
                            )

                        if not firefox_pids:
                            Settings.write_log_dev_file(
                                "Aucune PID Firefox fiable trouvée, utilisation du PID web-ext comme fallback",
                                "WARNING",
                            )
                            firefox_pids = [process.pid]

                        firefox_pids = sorted(set(firefox_pids))

                        firefox_pid_string = ";".join(str(pid) for pid in firefox_pids)
                        Settings.write_log_dev_file(
                            f"Firefox PID list stored for profile {profile_email}: {firefox_pid_string}",
                            "INFO",
                        )

                        firefox_session = {
                            "profile_name": profile_email,
                            "profile_path": firefox_profile_path,
                            "browser": "firefox",
                            "web_ext_pid": process.pid,
                            "firefox_pids": firefox_pids,
                            "email": profile_email,
                            "session_id": self.session_id,
                            "inserted_id": inserted_id,
                            "launch_command": command,
                            "launched_at": datetime.datetime.now().isoformat(),
                        }

                        FIREFOX_SESSIONS[profile_email] = firefox_session

                        Settings.write_log_dev_file(
                            f"Firefox session map updated for {profile_email}: {json.dumps(firefox_session, ensure_ascii=False)}",
                            "DEBUG",
                        )

                        BrowserManager.persistBrowserSessionInfo(
                            firefox_pids,
                            Settings.FIREFOX_PROFILES,
                            profile_email,
                            self.session_id,
                            self.selected_Browser.lower(),
                            inserted_id,
                            profile_path=firefox_profile_path,
                            web_ext_pid=process.pid,
                            profile_name=profile_email,
                        )
                        with file_lock:
                            ACTIVE_EMAILS.add(profile_email)

                    elif self.selected_Browser == "icedragon":
                        url = self.buildEncryptedUrl(
                            ip_address,
                            port,
                            login,
                            password,
                            profile_email,
                            profile_password,
                            recovery_email,
                            new_password,
                            new_recovery_email,
                            self.output_json_final,
                        )

                        browser_paths = Settings.CHROMIUM_BROWSER_PATHS["icedragon"]
                        profile_dir = browser_paths["profiles"]
                        ValidationUtils.ensurePathExists(profile_dir, is_file=False)

                        command = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            f"--disable-extensions-except={Settings.EXTENTION_EX3_CHROMIUM}",
                            f"--load-extension={os.path.join(Settings.EXTENTION_EX3_CHROMIUM)}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                            f"{url}",
                        ]

                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        PROCESS_PIDS.append(process.pid)

                        BrowserManager.persistBrowserSessionInfo(
                            process.pid,
                            profile_dir,
                            profile_email,
                            self.session_id,
                            self.selected_Browser,
                            inserted_id,
                            profile_path=os.path.join(profile_dir, profile_email),
                        )
                        with file_lock:
                            ACTIVE_EMAILS.add(profile_email)

                    else:
                        url = self.buildEncryptedUrl(
                            ip_address,
                            port,
                            login,
                            password,
                            profile_email,
                            profile_password,
                            recovery_email,
                            new_password,
                            new_recovery_email,
                            self.output_json_final,
                        )

                        profile_dir = Settings.CHROMIUM_BROWSER_PATHS.get(
                            self.selected_Browser,
                            {"profiles": Settings.CHROME_PROFILES},
                        )["profiles"]
                        browser_executable = self.Browser_path
                        ValidationUtils.ensurePathExists(profile_dir, is_file=False)

                        command = [
                            browser_executable,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            "--lang=En-US",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                        ]

                        command1 = [
                            browser_executable,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            f"{url}",
                            "--lang=En-US",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                        ]

                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                        PROCESS_PIDS.append(process.pid)
                        time.sleep(4)

                        process1 = subprocess.Popen(
                            command1,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        PROCESS_PIDS.append(process1.pid)
                        session_pids = f"{process.pid};{process1.pid}"

                        BrowserManager.persistBrowserSessionInfo(
                            session_pids,
                            profile_dir,
                            profile_email,
                            self.session_id,
                            self.selected_Browser.lower(),
                            inserted_id,
                            profile_path=os.path.join(profile_dir, profile_email),
                        )
                        with file_lock:
                            ACTIVE_EMAILS.add(profile_email)

                    self.emails_processed += 1

                except Exception as e:
                    with file_lock:
                        ACTIVE_EMAILS.discard(profile_email)
                    Settings.write_log_dev_file(
                        f"Error processing email {profile_email}: {e}\n{traceback.format_exc()}",
                        "ERROR",
                    )
            self.msleep(1000)

        REMAINING_EMAILS = 0
        logMessage("[INFO] Processing finished for all emails.")
        Settings.write_log_dev_file("Processing finished for all emails.", "INFO")
        UIManager.enableButton(self.window.submitButton)
        time.sleep(3)
        LOGS_RUNNING = False
        self.finished.emit()


class AutomationMainWindow(QMainWindow):
    def __init__(self, json_data):
        super(AutomationMainWindow, self).__init__()
        self._init_ui()
        self._init_data(json_data)
        self._setup_ui_components()
        self._load_initial_state()

    def _init_ui(self):
        Settings.write_log_dev_file("Initializing user interface...", "INFO")
        uic.loadUi(Settings.INTERFACE_UI, self)

    def _init_data(self, json_data):
        self.states = json_data
        self.STATE_STACK = []

    def _setup_ui_components(self):
        self._setup_containers()
        self._setup_template_widgets()
        self._setup_buttons()
        self._setup_comboboxes()
        self._setup_tab_widgets()
        self._setup_log_system()
        self._setup_miscellaneous()

    def _find_widget(self, name, widget_type=None):
        widget = (
            self.findChild(widget_type, name)
            if widget_type
            else self.findChild(QWidget, name)
        )
        Settings.write_log_dev_file(
            f"Searching for widget: {name} (type: {widget_type})", "INFO"
        )
        return widget

    def _setup_containers(self):
        UIManager.setupContainers(self)

    def _setup_template_widgets(self):
        UIManager.setupTemplateWidgets(self)

    def _setup_buttons(self):
        self.Button_Initaile_state = self._setup_button(
            "Button_Initaile_state", self.load_initial_options
        )
        self.submit_button = self._setup_button(
            "submitButton", lambda: self.submit_button_clicked(self)
        )
        self.ClearButton = self._setup_icon_button(
            "ClearButton",
            "clear.png",
            self.clear_button_clicked,
            icon_size=(32, 32),
            button_size=(36, 36),
        )
        self.CopyButton = self._setup_icon_button(
            "CopyButton",
            "copyLog.png",
            self.copy_logs_to_clipboard,
            icon_size=(26, 26),
            button_size=(38, 38),
        )
        self.SaveButton = self._setup_icon_button(
            "saveButton", "save.png", self.handle_save, icon_size=(16, 16)
        )
        self.log_out_Button = UIManager.setupLogoutButton(self, self.log_out)

    def _setup_icon_button(
        self, button_name, icon_file, callback, icon_size=None, button_size=None
    ):
        return UIManager.setupIconButton(
            self, button_name, icon_file, callback, icon_size, button_size
        )

    def _setup_button(self, widget_name, callback):
        return UIManager.setupButton(self, widget_name, callback)

    def _setup_comboboxes(self):
        self._setup_browser_combobox()
        self._setup_isp_combobox()
        self._setup_scenario_combobox()

    def _setup_browser_combobox(self):
        UIManager.setupBrowserCombobox(self)

    def _setup_isp_combobox(self):
        UIManager.setupIspCombobox(self)

    def _setup_scenario_combobox(self):
        UIManager.setupScenarioCombobox(self)

    def _setup_tab_widgets(self):
        UIManager.setupResultTabWidget(self)
        UIManager.setupInterfaceTabWidget(self)

    def _setup_log_system(self):
        self.log_container = self._find_widget("log", QWidget)
        if self.log_container is not None:
            self.log_text_edit = QPlainTextEdit(self.log_container)
            self.log_text_edit.setReadOnly(True)  # Lecture seule pour les logs
            self.log_text_edit.setStyleSheet(
                "QPlainTextEdit { background-color: #161a1d; color: #ffffff; font-size: 14px; font-family: 'Segoe UI'; border: none; padding: 8px; }"
            )
            self.log_text_edit.setFrameShape(QFrame.Shape.NoFrame)
            self.log_text_edit.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.log_text_edit.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.log_text_edit.document().setMaximumBlockCount(1000)

            rect = self.log_container.rect()
            width = rect.width() if rect.width() > 0 else 1600
            height = rect.height() if rect.height() > 0 else 9000
            margin_top = 60
            margin_side = 10
            self.log_text_edit.setGeometry(
                margin_side,
                margin_top,
                max(0, width - 2 * margin_side),
                max(0, height - margin_top - margin_side),
            )

        self.LOGS_THREAD = ApplicationLogDisplayThread(LOGS)
        self.LOGS_THREAD.log_signal.connect(self.update_logs_display)

    def _setup_miscellaneous(self):
        UIManager.setupMiscellaneous(self)

    def _load_initial_state(self):
        self.load_scenarios_into_combobox()
        self.load_initial_options()

    def save_process(self, params):
        return API_MANAGER.saveProcess(params)

    def handle_save(self):
        Settings.write_log_dev_file(
            f"Checking STATE_STACK: {len(self.STATE_STACK) if self.STATE_STACK else 0} items",
            "INFO",
        )
        if not self.STATE_STACK:
            UIManager.showCriticalMessage(
                self,
                "No Data",
                "No actions to save. Please add actions before saving.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "No actions to save. Please add actions before saving.", "ERROR"
            )
            return

        scenario_name, ok = QInputDialog.getText(
            self, "Save Scenario", "Enter scenario name:"
        )

        if not ok:
            Settings.write_log_dev_file("User cancelled scenario name input", "INFO")
            return

        scenario_name = scenario_name.strip()
        Settings.write_log_dev_file(f"Scenario name entered: '{scenario_name}'", "INFO")

        if not scenario_name:
            Settings.write_log_dev_file("Scenario name cannot be empty", "ERROR")
            UIManager.showCriticalMessage(
                self,
                "Invalid Name",
                "Scenario name cannot be empty.",
                message_type="critical",
            )
            return

        Settings.write_log_dev_file(
            "Scenario name is valid, checking session file", "INFO"
        )
        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file(
                f"Session file not found at: {Settings.SESSION_PATH}", "ERROR"
            )
            UIManager.showCriticalMessage(
                self,
                "Session Not Found",
                "[❌] Your session file is missing. Please restart the application.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "Your session file is missing. Please restart the application.", "ERROR"
            )
            return

        Settings.write_log_dev_file(
            "Session file exists, checking session validity", "INFO"
        )
        session_info = SessionManager.check_session()
        Settings.write_log_event(
            "session_checked", "INFO", valid=session_info.get("valid")
        )

        if not session_info["valid"]:
            Settings.write_log_dev_file("Session is invalid, exiting", "ERROR")
            sys.exit()
            return False

        Settings.write_log_dev_file("Session is valid, encrypting session info", "INFO")
        encrypted_String = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        Settings.write_log_dev_file(
            f"Encrypted string generated (length: {len(encrypted_String)})", "INFO"
        )
        Settings.write_log_dev_file("Preparing payload", "INFO")

        try:
            state_json = json.dumps(self.STATE_STACK[-1], ensure_ascii=False)
            state_stack_json = json.dumps(self.STATE_STACK, ensure_ascii=False)
            state_b64 = base64.b64encode(state_json.encode("utf-8")).decode("utf-8")
            state_stack_b64 = base64.b64encode(state_stack_json.encode("utf-8")).decode(
                "utf-8"
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Error encoding state for saving: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return

        payload = {
            "user_id": session_info["Id_User"],
            "encrypted": encrypted_String,
            "name": scenario_name,
            "state": state_b64,
            "state_stack": state_stack_b64,
        }
        Settings.write_log_dev_file(f"Complete payload prepared for API call", "INFO")

        Settings.write_log_dev_file("Building API URL", "INFO")
        Api_Url = (
            f"{Settings.SCENARIO_API}?rv4=1&entity=IT&action=add&l={encrypted_String}"
        )

        Settings.write_log_dev_file(f"API URL: {Api_Url}", "INFO")
        Settings.write_log_dev_file("Calling API...", "INFO")

        try:
            result = API_MANAGER.handleSaveScenario(payload, Api_Url)
            Settings.write_log_event(
                "save_scenario_response_received",
                "INFO",
                response_type=type(result).__name__,
                success=result.get("status") if isinstance(result, dict) else None,
            )

            if result.get("status") is False:
                Settings.write_log_dev_file(
                    "API returned status=False, showing error message", "INFO"
                )
                UIManager.showCriticalMessage(
                    self,
                    "Action Not Saved",
                    " The action could not be saved.\n\n"
                    "Your session may have expired, or this name already exists.\n Please verify your session and make sure the name is unique, then try again.",
                    message_type="critical",
                )
                Settings.write_log_dev_file(
                    "Save failed: session expired or action name already exists.",
                    "ERROR",
                )
                return

            if result.get("status"):
                Settings.write_log_dev_file(
                    "API returned status=True, scenario saved successfully", "INFO"
                )
                self.load_scenarios_into_combobox()
                UIManager.showCriticalMessage(
                    self,
                    "Success",
                    "The scenario has been saved successfully.",
                    message_type="success",
                )
                Settings.write_log_dev_file(
                    "The scenario has been saved successfully.", "INFO"
                )
            else:
                Settings.write_log_dev_file(
                    "API returned status=None or unexpected, showing API error", "INFO"
                )
                UIManager.showCriticalMessage(
                    self,
                    "API Error",
                    "An error occurred while saving the scenario.",
                    message_type="critical",
                )
                Settings.write_log_dev_file(
                    "An error occurred while saving the scenario.", "ERROR"
                )

        except Exception as e:
            Settings.write_log_dev_file(f"Exception during API call: {e}", "ERROR")
            UIManager.showCriticalMessage(
                self,
                "Error",
                "An error occurred while saving the scenario.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                f"An error occurred while saving the scenario: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )

        Settings.write_log_dev_file("handle_save function completed", "INFO")

    def load_scenarios_into_combobox(self):
        Settings.write_log_dev_file("Starting load_scenarios_into_combobox()", "INFO")

        if self.saveSanario is None:
            Settings.write_log_dev_file("saveSanario is None", "ERROR")
            return

        if self.saveSanario is None:
            Settings.write_log_dev_file("saveSanario is None", "ERROR")
            return

        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file("Session file not found", "ERROR")
            return

        Settings.write_log_dev_file("Session file exists", "INFO")
        session_info = SessionManager.check_session()
        Settings.write_log_event(
            "session_checked", "INFO", valid=session_info.get("valid")
        )

        if not session_info.get("valid"):
            Settings.write_log_dev_file(
                "Session invalid. Redirecting to login.", "ERROR"
            )
            sys.exit()
            return False

        encrypted_String = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        Settings.write_log_dev_file(f"Encrypted string: {encrypted_String}", "INFO")
        Api_Url = (
            f"{Settings.SCENARIO_API}?rv4=1&action=get&entity=IT&l={encrypted_String}"
        )

        try:
            result = API_MANAGER.fetchScenarios(Api_Url)
            if isinstance(result, dict) and result.get("status") is False:
                Settings.write_log_dev_file(
                    f"API returned error: {result.get('error', 'Unknown error')}",
                    "ERROR",
                )
                self.saveSanario.clear()
                self.saveSanario.addItem("None")
                return

            scenarios = result if isinstance(result, list) else []
            Settings.write_log_dev_file(
                f"Number of scenarios loaded: {len(scenarios)}", "INFO"
            )

            self.saveSanario.clear()
            self.saveSanario.addItem("None")

            if scenarios:
                for index, scenario in enumerate(scenarios, 1):
                    name = scenario.get("name", f"Scénario {index}")
                    Settings.write_log_dev_file(
                        f"Adding scenario {index}: {name}", "INFO"
                    )
                    self.saveSanario.addItem(name)
            else:
                Settings.write_log_dev_file(
                    "No scenarios found, added 'None' only", "INFO"
                )
            Settings.write_log_dev_file("Combobox updated successfully", "INFO")
        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while loading scenarios: {str(e)}\n{traceback.format_exc()}",
                "CRITICAL",
            )

    def copy_logs_to_clipboard(self):
        UIManager.copyLogsToClipboard(self)

    def log_out(self):
        global SELECTED_BROWSER_GLOBAL
        try:
            SessionManager.clear_session()
            if SELECTED_BROWSER_GLOBAL:
                stopAllProcesses(self)

            self.login_window = AuthenticationWindow()
            self.login_window.setFixedSize(
                Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT
            )
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()
            self.close()

        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while logging out: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )

    def update_logs_display(self, log_entry):
        UIManager.updateLogsDisplay(log_entry, self.log_text_edit)

    def extraction_finished(self, window):
        self.LOGS_THREAD.stopThread()
        self.LOGS_THREAD.wait()
        Settings.write_log_dev_file("Extraction Finished", "INFO")
        QTimer.singleShot(
            100, lambda: UIManager.readResultUpdateList(window, NOTIFICATION_BADGES)
        )

    def verify_required_paths(self):
        Settings.write_log_dev_file("Starting required path verification", "INFO")

        paths = [
            (Settings.CONFIG_PROFILE, False),
            (Settings.EXTENTION_EX3_CHROMIUM, False),
            (Settings.SECURE_PREFERENCES_TEMPLATE, True),
            (Settings.FICHIER_LOCAL_STATE, True),
            (Settings.FICHIER_VARIATIONS, True),
        ]

        invalid_paths = []

        for path, is_file in paths:
            path_type = "file" if is_file else "directory"
            normalized_path = os.path.normpath(path) if path else path
            exists = os.path.exists(path)
            type_ok = os.path.isfile(path) if is_file else os.path.isdir(path)

            detail_msg = f"Path check: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok}"
            Settings.write_log_dev_file(detail_msg, "INFO")
            valid = ValidationUtils.validate_path(
                path, must_exist=True, is_file=is_file
            )

            if not valid:
                reason = (
                    "missing"
                    if not exists
                    else ("wrong type" if not type_ok else "unknown")
                )
                Settings.write_log_dev_file(
                    f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}",
                    "ERROR",
                )
                invalid_paths.append(
                    f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}"
                )

        if invalid_paths:
            Settings.write_log_dev_file(
                f"Required path verification failed: {len(invalid_paths)} invalid path(s)",
                "ERROR",
            )
        else:
            Settings.write_log_dev_file("All required paths are valid", "SUCCESS")
        return len(invalid_paths) == 0, invalid_paths

    def submit_button_clicked(self, window):
        global LOGS_RUNNING, NOTIFICATION_BADGES
        UIManager.disableButton(self.submitButton)
        session_info = SessionManager.check_session()
        if not session_info["valid"]:
            self.login_window = AuthenticationWindow()
            self.login_window.setFixedSize( Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT )

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()
            self.close()

            try:
                with open(Settings.SESSION_PATH, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                Settings.write_log_dev_file( f"An error occurred while cleaning the session: {str(e)}\n{traceback.format_exc()}", "ERROR")
            UIManager.enableButton(self.submitButton)
            return

        auth_result = SessionManager.check_api_credentials(  session_info.get("username"), session_info.get("password") )
        
        if isinstance(auth_result, int):
            messages = {
                -1: "Invalid credentials. Please login again.",
                -2: "This device is not authorized.",
                -3: "Unable to connect to the server.",
                -4: "Access denied for this application.",
                -5: "Unknown authentication error.",
            }

            self.erreur_label.setText( messages.get(auth_result, "Authentication failed.") )
            self.erreur_label.show()
            UIManager.enableButton(self.submitButton)
            return
        else:
            Settings.write_log_dev_file("Authentication successful", "INFO")

        is_valid, errors = self.verify_required_paths()
        if is_valid:
            Settings.write_log_dev_file("All required paths are valid.", "INFO")
        else:
            Settings.write_log_dev_file("Error with required paths.", "ERROR")
            error_details = "\n".join(errors)
            UIManager.showCriticalMessage( window ,  "Invalid Paths",  f"The following paths are invalid:\n\n{error_details}",  message_type="critical" )
            UIManager.enableButton(self.submitButton)
            return

        try:
            Settings.write_log_dev_file("Start badge cleanup", "INFO")
            if self.result_tab_widget:
                Settings.write_log_dev_file( f"Number of tabs in result_tab_widget = {self.result_tab_widget.count()}",  "INFO")

                for tab_index, badge in NOTIFICATION_BADGES.items():
                    if badge:
                        Settings.write_log_dev_file(  f"Badge removed tab_index={tab_index}", "INFO"   )
                        badge.deleteLater()
                        
                NOTIFICATION_BADGES.clear()
                Settings.write_log_dev_file("All existing badges removed and dictionary cleared", "INFO"  )

                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        for lw_index, lw in enumerate(list_widgets):
                            lw.clear()

            else:
                Settings.write_log_dev_file("result_tab_widget is None", "WARNING")

        except Exception as e:
            Settings.write_log_dev_file(  f"An error occurred while removing badges: {str(e)}\n{traceback.format_exc()}",  "ERROR" )
            UIManager.enableButton(self.submitButton)
            return

        update_progress = QProgressDialog(
            "Vérification de la version du programme...",
            "",  0,  100,  self  )
        update_progress.setWindowTitle("Mise à jour AutoMailPro")
        update_progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        update_progress.setAutoClose(False)
        update_progress.setAutoReset(False)
        update_progress.setCancelButton(None)
        update_progress.setValue(0)
        update_progress.show()
        QApplication.processEvents()

        def update_progress_callback(message, value):
            update_progress.setLabelText(message)
            update_progress.setValue(value)
            QApplication.processEvents()

        update_result = UpdateManager.checkAndUpdate(
            self,
            progress_callback=update_progress_callback,
        )
        update_progress.close()

        if update_result is False:
            UIManager.enableButton(self.submitButton)
            return

        if update_result is None:
            UIManager.showCriticalMessage(
                self,
                "Mise à jour indisponible",
                "Impossible de vérifier la version du programme. L’application va continuer avec la version locale.",
                message_type="warning",
            )

        selected_Browser = self.browser.currentText()
        QApplication.processEvents()

        browser_path = BrowserManager.get_browser_executable_path(selected_Browser)

        if browser_path is None:
            Settings.write_log_dev_file(
                f"Unable to find path for browser: {selected_Browser}", "ERROR"
            )
            UIManager.showCriticalMessage(
                window,
                "Browser Not Found",
                f"Unable to find the path for the selected browser: {selected_Browser}.\n\nPlease ensure the browser is installed and try again.",
                message_type="critical",
            )
            UIManager.enableButton(self.submitButton)
            return

        # browser_check_version = UpdateManager.checkExtensionVersion(window, selected_Browser.lower())
        # if browser_check_version is False:
        #     Settings.write_log_dev_file(f"Extension check bloqué pour le navigateur sélectionné: {selected_Browser}","ERROR")
        #     UIManager.enableButton(self.submitButton)
        #     return

        # if browser_check_version is not True:
        #     remote_version = browser_check_version if isinstance(browser_check_version, str) else None
        #     if remote_version is not None:
        #         valid_extension = UpdateManager.validateBrowserExtensionVersion(  selected_Browser, remote_version,  target_name="EX3",  window=window)
        #         if not valid_extension:
        #             UIManager.enableButton(self.submitButton)
        #             return
        #     elif selected_Browser:
        #         installed_version = UpdateManager.getInstalledBrowserExtensionVersion(selected_Browser.lower(), "EX3")
        #         if installed_version is None:
        #             UIManager.showCriticalMessage( window, "Extension not detected",  f"The EX3 extension could not be found in {selected_Browser}. Please contact support to validate the installation before continuing.",  message_type="warning")
        #             UIManager.enableButton(self.submitButton)
        #             return

        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                if UIManager.isResultTab(self.INTERFACE, i):
                    UIManager.resetResultTabLabel(self.INTERFACE, i)
        LOGS_RUNNING = True

        if self.scenario_layout.count() == 0:
            UIManager.showCriticalMessage(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning",
            )
            UIManager.enableButton(self.submitButton)
            Settings.write_log_dev_file(
                "No actions have been added. Please add actions before submitting.",
                "WARNING",
            )
            return

        try:
            result = ValidationUtils.generateUserInputData(window)

            if not isinstance(result, dict):
                Settings.write_log_dev_file(
                    "Invalid result format returned from ValidationUtils.generateUserInputData",
                    "ERROR",
                )
                UIManager.enableButton(self.submitButton)
                return

            if not result.get("valid"):
                Settings.write_log_dev_file(
                    "❌ [DATA ERROR] Input or proxy validation failed before browser processes were started.",
                    "ERROR",
                )

                title, detail_text = (
                    result.get("error", "Unknown error").split(":", 1)
                    if ":" in result.get("error", "Unknown error")
                    else (
                        result.get("error", "Unknown error"),
                        result.get("error", "Unknown error"),
                    )
                )

                Settings.write_log_dev_file(
                    f"Data error: {result.get('error', 'Unknown error')}", "ERROR"
                )
                Settings.write_log_dev_file(
                    f"Title: {title.strip()} | Detail: {detail_text.strip()}", "ERROR"
                )
                Settings.write_log_dev_file(
                    f"Generate_User_Input_Data failed: {result.get('error', 'Unknown error')}",
                    "ERROR",
                )
                UIManager.showCriticalMessage(
                    window, title.strip(), detail_text.strip(), message_type="warning"
                )
                UIManager.enableButton(self.submitButton)
                return

            data_list = result.get("data") or []
            entered_number = result.get("entered_number")

            if not isinstance(data_list, list):
                Settings.write_log_dev_file("Data list is not a list", "ERROR")
                UIManager.enableButton(self.submitButton)
                return

            Settings.write_log_dev_file(
                f"User input processed successfully | Records: {len(data_list)} | Entered number: {entered_number}",
                "INFO",
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Processing error: {e}\n{traceback.format_exc()}", "ERROR"
            )
            UIManager.showCriticalMessage(
                window,
                "Unexpected Error",
                "Something went wrong while processing your request.\n\nPlease try again or contact support.",
                message_type="critical",
            )
            UIManager.enableButton(self.submitButton)
            return

        Settings.write_log_dev_file("Final JSON:", "INFO")
        result_json = JsonManager.generateJson(self.scenario_layout, selected_Browser)
        Settings.write_log_dev_file(
            f"Final JSON generated. Data: {json.dumps(result_json, indent=2, ensure_ascii=False)}",
            "INFO",
        )
        Settings.write_log_dev_file("The final JSON has been generated.", "INFO")
        QApplication.processEvents()

        if not result_json or result_json == []:
            UIManager.showCriticalMessage(
                window,
                "Error - Save Configuration",
                "No valid actions could be generated or an error occurred while saving the configuration file.\n\nIf the problem persists, contact Support.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "No valid actions could be generated or an error occurred while saving the configuration file.",
                "ERROR",
            )
            UIManager.enableButton(self.submitButton)
            return

        QApplication.processEvents()
        try:
            with open(Settings.FILE_ISP, "w", encoding="utf-8") as f:
                f.write(self.Isp.currentText().strip())
        except Exception as e:
            UIManager.enableButton(self.submitButton)

            Settings.write_log_dev_file(
                f"Error writing to Isp.txt: {e}\n{traceback.format_exc()}", "ERROR"
            )

        QApplication.processEvents()
        json_string = json.dumps(result_json)

        parameters = {
            "p_owner": session_info["username"],
            "p_entity": session_info["p_entity_Origine"],
            "p_isp": self.Isp.currentText(),
            "p_action_name": json_string,
            "p_app": "V4",
            "p_python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "p_browser": self.browser.currentText(),
        }

        unique_id = self.save_process(parameters)
        if unique_id == -1:
            UIManager.showCriticalMessage(
                window,
                "Error - Process Save",
                "Failed to save the process in the database.\n\nPlease check your connection and try again.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "Failed to save the process in the database.", "ERROR"
            )
            UIManager.enableButton(self.submitButton)
            return

        QApplication.processEvents()

        startExtraction(
            window,
            data_list,
            entered_number,
            selected_Browser,
            self.Isp.currentText(),
            unique_id,
            result_json,
            session_info["username"],
        )
        self.LOGS_THREAD.start()
        QApplication.processEvents()

    def load_initial_options(self):
        while self.reset_options_layout.count() > 0:
            item = self.reset_options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for key, state in self.states.items():
            if state.get("showOnInit", False):
                self.create_option_button(state)

    def create_option_button(self, state):
        default_icon_path = os.path.join(Settings.ICONS_DIR, "icon.png")
        default_icon_path_Templete2 = os.path.join(Settings.ICONS_DIR, "next.png")
        is_multi = state.get("isMultiSelect", False)

        if is_multi:
            template_button = self.Temeplete_Button_2
            icon_path = default_icon_path_Templete2
        else:
            template_button = self.template_button
            icon_path = default_icon_path
        button = QPushButton(
            state.get("label", "Unnamed"), self.reset_options_container
        )
        button.setStyleSheet(template_button.styleSheet())
        button.setFixedSize(template_button.size())
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        button.clicked.connect(lambda _, s=state: self.load_state(s))
        if ValidationUtils.pathExists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            Settings.write_log_dev_file(
                f"[Warning] Icon not found at: {icon_path}", "WARNING"
            )
        self.reset_options_layout.addWidget(button)

    def load_state(self, state):
        is_multi = state.get("isMultiSelect", False)
        if not is_multi:
            self.STATE_STACK.append(state)

        if not is_multi:
            template = state.get("Template", "")
            UIManager.updateScenario(self, template, state)

        actions = state.get("actions", [])
        self.update_reset_options(actions)
        self.update_actions_color_handle_last_button()
        UIManager.removeCopier(self.scenario_layout, self.reset_options_layout)
        UIManager.removeInitial(self.scenario_layout, self.reset_options_layout)

    def update_actions_color_handle_last_button(self):
        UIManager.updateActionsColorHandleLastButton(
            self.scenario_layout, self.go_to_previous_state
        )

    def update_reset_options(self, actions):
        count = self.reset_options_layout.count()
        for i in reversed(range(count)):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if not actions:
            self.load_initial_options()
            return
        for action_key in actions:
            state = self.states.get(action_key)
            if state:
                label = state.get("label", action_key)
                self.create_option_button(state)

    def go_to_previous_state(self):
        if len(self.STATE_STACK) > 1:
            if self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(
                    self.scenario_layout.count() - 1
                )
                if last_item.widget():
                    last_item.widget().deleteLater()

            self.STATE_STACK.pop()
            previous_state = self.STATE_STACK[-1]
            self.update_reset_options(previous_state.get("actions", []))
        else:
            self.STATE_STACK.clear()
            while self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(0)
                if last_item.widget():
                    last_item.widget().deleteLater()
            self.load_initial_options()
        self.update_actions_color_handle_last_button()
        UIManager.removeCopier(self.scenario_layout, self.reset_options_layout)

    def clear_button_clicked(self):
        self.log_text_edit.clear()
        LOGS.clear()

    def scenario_changed(self, name_selected):
        session_info = SessionManager.check_session()
        if not session_info.get("valid"):
            Settings.write_log_dev_file(
                "Session invalid. Redirecting to login.", "ERROR"
            )
            sys.exit()
            return False

        encrypted_string = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        api_url = (
            f"{Settings.SCENARIO_API}?rv4=1&action=get&entity=IT&l={encrypted_string}"
        )

        try:
            raw_result = API_MANAGER.fetchScenarios(
                api_url, params={"name": name_selected}
            )
        except Exception as e:
            Settings.write_log_dev_file(
                f"API call failed: {e} \n {traceback.format_exc()}", "ERROR"
            )
            return

        if isinstance(raw_result, dict) and raw_result.get("status") is False:
            Settings.write_log_dev_file(
                f"API returned error: {raw_result.get('error', 'Unknown API error')}",
                "ERROR",
            )
            return

        if isinstance(raw_result, list):
            data_list = raw_result
        elif isinstance(raw_result, dict) and "data" in raw_result:
            data_list = raw_result["data"]
        else:
            Settings.write_log_dev_file(
                f"Unexpected API result format: {type(raw_result)}", "ERROR"
            )
            return

        if not data_list:
            Settings.write_log_dev_file("No scenario returned from API.", "WARNING")
            return

        scenario = next(
            (item for item in data_list if item.get("name") == name_selected),
            None,
        )
        if scenario is None:
            Settings.write_log_dev_file(
                f"Scenario not found in API response: {name_selected}",
                "WARNING",
            )
            return

        for i in reversed(range(self.scenario_layout.count())):
            item = self.scenario_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = (
                        widget.objectName()
                        if widget.objectName()
                        else widget.__class__.__name__
                    )
                    Settings.write_log_dev_file(
                        f"🗑️ Removing widget: {widget_name}", "INFO"
                    )
                    widget.deleteLater()

        state_stack = scenario.get("state_stack", [])
        if isinstance(state_stack, str):
            state_stack = state_stack.strip()
            try:
                state_stack = json.loads(state_stack)
            except json.JSONDecodeError:
                try:
                    state_stack = json.loads(
                        base64.b64decode(state_stack).decode("utf-8")
                    )
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"Failed to parse state_stack: {e}\n{traceback.format_exc()}",
                        "WARNING",
                    )
                    return

        if not isinstance(state_stack, list):
            Settings.write_log_dev_file(
                "Scenario state_stack has an invalid format.", "WARNING"
            )
            return

        self.STATE_STACK = state_stack
        Settings.write_log_dev_file(
            f"📥 Scenario loaded with {len(self.STATE_STACK)} states.", "INFO"
        )

        state_stack_copy = copy.deepcopy(self.STATE_STACK)

        for index, state in enumerate(state_stack_copy, start=1):
            try:
                pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
            except Exception:
                pretty = repr(state)

            try:
                t0 = time.time()
                self.load_state(state)
                t1 = time.time()
                Settings.write_log_dev_file(
                    f"✅ load_state for #{index} succeeded in {t1 - t0:.3f}s", "INFO"
                )
                try:
                    self.update_actions_color_handle_last_button()
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"⚠️ update_actions_color_handle_last_button failed after state #{index}: {e} \n {traceback.format_exc()}",
                        "WARNING",
                    )
            except Exception as e:
                Settings.write_log_dev_file(
                    f"❌ Error during load_state() for state #{index}: {e}\n{traceback.format_exc()}",
                    "WARNING",
                )
                continue

        try:
            unique_states = []
            seen = set()
            for state in self.STATE_STACK:
                try:
                    state_key = json.dumps(
                        state, sort_keys=True, ensure_ascii=False, default=str
                    )
                except Exception:
                    state_key = repr(state)
                if state_key not in seen:
                    seen.add(state_key)
                    unique_states.append(state)
            self.STATE_STACK = unique_states
        except Exception as e:
            Settings.write_log_dev_file(
                f"⚠️ Failed to deduplicate STATE_STACK: {e}\n{traceback.format_exc()}",
                "ERROR",
            )


class EntitySelectionDialog(QDialog):
    def __init__(self, pattern=None, default_entity=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Entity - AutoMailPro")
        self.setModal(True)
        self.setFixedSize(500, 320)
        self.setWindowIcon(QIcon(os.path.join(Settings.ICONS_DIR, "logo.jpg")))
        self.pattern = pattern
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(12)
        title_label = QLabel("Entity Selection")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        instruction_label = QLabel(
            "Please enter the entity you want to use for this session : "
        )
        instruction_label.setStyleSheet(
            "font-size: 14px; color: #555; margin-bottom: 5px;"
        )
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        if self.pattern:
            format_info = QLabel("Format: opm followed by digits (e.g., opm74, opm19)")
            format_info.setStyleSheet(
                "font-size: 12px; color: #859cb5; margin-bottom: 10px; font-style: italic;"
            )
            main_layout.addWidget(format_info)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter entity (opm + number)...")
        if default_entity:
            self.input_field.setText(default_entity)
        self.input_field.setStyleSheet(
            "QLineEdit { font-size: 14px; padding: 8px; border: 2px solid #ccc; border-radius: 5px; background-color: #fff; min-width: 200px; } QLineEdit:hover { border-color: #0078d4; } QLineEdit:focus { border: 2px solid #0078d4; outline: none; }"
        )
        main_layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        self.error_label = QLabel()
        self.error_label.setStyleSheet(
            "font-size: 12px; color: #d32f2f; margin-top: 8px; margin-bottom: 8px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(40)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        main_layout.addSpacing(20)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(
            "QPushButton { font-size: 14px; padding: 10px 20px; background-color: #f3f2f1; border: 1px solid #ccc; border-radius: 5px; color: #333; text-align: center; } QPushButton:hover { background-color: #e1dfdd; } QPushButton:pressed { background-color: #c8c6c4; }"
        )
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet(
            "QPushButton { font-size: 14px; padding: 10px 20px; background-color: #0078d4; border: none; border-radius: 5px; color: white; text-align: center; } QPushButton:hover { background-color: #106ebe; } QPushButton:pressed { background-color: #005a9e; }"
        )
        self.confirm_button.clicked.connect(self.validate_and_accept)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        main_layout.addLayout(button_layout)
        self.setStyleSheet("QDialog { background-color: #f8f8f8; }")

    def validate_and_accept(self):
        """Validate input against pattern and accept if valid."""
        import re

        entity_text = self.input_field.text().strip()
        if not entity_text:
            self.error_label.setText("Entity name cannot be empty.")
            self.error_label.show()
            return

        if self.pattern:
            if not re.match(self.pattern, entity_text):
                self.error_label.setText(
                    f"Invalid entity format. Expected format: opm followed by digits (e.g., opm74)"
                )
                self.error_label.show()
                return

        self.error_label.hide()
        self.accept()

    def get_selected_entity(self):
        """Returns the entered entity or None if canceled."""
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.input_field.text().strip()
        return None


class AuthenticationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui_path = self.select_ui_file()
        uic.loadUi(self.ui_path, self)
        if "Auth.ui" in self.ui_path:
            self.initialize_login_ui()
            Settings.write_log_dev_file("Login UI initialized", "INFO")
        self.setWindowTitle("AutoMailPro")

    def select_ui_file(self) -> str:
        try:
            session_info = SessionManager.check_session()
            if session_info["valid"]:
                return Settings.INTERFACE_UI
        except Exception as e:
            Settings.write_log_dev_file(
                f"[SESSION ERROR] {e}\n{traceback.format_exc()}", "WARNING"
            )
            sys.exit()
        return Settings.AUTH_UI

    def initialize_login_ui(self):
        self.login_input = self.findChild(QLineEdit, "loginInput")
        self.password_input = self.findChild(QLineEdit, "passwordInput")
        self.login_button = self.findChild(QPushButton, "loginButton")
        self.title = self.findChild(QPushButton, "title")
        self.erreur_label = self.findChild(QLabel, "erreur")

        if self.erreur_label:
            Settings.write_log_dev_file(
                f"[INFO] Erreur label found: {self.erreur_label.text()}", "INFO"
            )
            self.erreur_label.hide()

        if self.title:
            self.title.clicked.connect(self.handle_show_session_date)
            Settings.write_log_dev_file(
                f"[INFO] Title label found: {self.title.text()}", "INFO"
            )
        if self.login_button:
            self.login_button.clicked.connect(self.handle_login)
            Settings.write_log_dev_file(
                f"[INFO] Login button found: {self.login_button.text()}", "INFO"
            )

        right_frame = self.findChild(QWidget, "rightFrame")
        if right_frame:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(25)
            shadow.setXOffset(0)
            shadow.setYOffset(8)
            shadow.setColor(QColor(0, 0, 0, 80))
            right_frame.setGraphicsEffect(shadow)

        self.background_image_path = Settings.AUTH_BACKGROUND
        self.background_frame = self.findChild(QFrame, "background")
        if self.background_frame:
            self.background_label = QLabel(self.background_frame)
            self.background_label.setStyleSheet(
                "border-top-left-radius: 30px; border-bottom-left-radius: 30px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; overflow: hidden;"
            )
            self.background_label.setScaledContents(True)
            self.background_label.lower()
            self.update_background_image()

            self.logoFrame = self.findChild(QFrame, "logoFrame")

            if self.logoFrame:
                self.logo_label = QLabel(self.logoFrame)
                self.logo_label.setScaledContents(True)
                logo_path = os.path.join(Settings.ICONS_DIR, "logo.jpg")
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setGeometry(
                        0, 0, self.logoFrame.width(), self.logoFrame.height()
                    )
                    self.logo_label.show()

            self.UseFrame = self.findChild(QFrame, "userFrame")
            if self.UseFrame:
                self.user_label = QLabel(self.UseFrame)
                self.user_label.setScaledContents(True)
                user_path = os.path.join(Settings.ICONS_DIR, "user.png")
                user_pixmap = QPixmap(user_path)
                if not user_pixmap.isNull():
                    self.user_label.setPixmap(user_pixmap)
                    self.user_label.setGeometry(
                        0, 0, self.UseFrame.width(), self.UseFrame.height()
                    )
                    self.user_label.show()

    def update_background_image(self):
        if hasattr(self, "background_frame") and hasattr(self, "background_label"):
            pixmap = QPixmap(self.background_image_path)
            if not pixmap.isNull():
                self.background_label.resize(self.background_frame.size())
                self.background_label.setPixmap(pixmap)

    def handle_login(self):
        UIManager.disableButton(self.login_button)
        username = (
            self.login_input.text().strip()
            if hasattr(self.login_input, "text")
            else str(self.login_input).strip()
        )
        password = (
            self.password_input.text().strip()
            if hasattr(self.password_input, "text")
            else str(self.password_input).strip()
        )

        if len(username) <= 4:
            Settings.write_log_dev_file(
                "❌ Username must contain more than 4 characters.", "WARNING"
            )
            UIManager.enableButton(self.login_button)
            self.erreur_label.setText("Username must contain more than 4 characters.")
            self.erreur_label.show()
            return

        if len(password) <= 4:
            Settings.write_log_dev_file(
                "❌ Password must contain more than 4 characters.", "WARNING"
            )
            UIManager.enableButton(self.login_button)
            self.erreur_label.setText("Password must contain more than 4 characters.")
            self.erreur_label.show()
            return

        Settings.write_log_dev_file("Calling check_api_credentials...", "INFO")
        auth_result = SessionManager.check_api_credentials(username, password)
        Settings.write_log_event(
            "authentication_response",
            "INFO",
            response_type=type(auth_result).__name__,
            success=not isinstance(auth_result, int) or auth_result == 0,
        )

        if isinstance(auth_result, int):
            UIManager.enableButton(self.login_button)

            messages = {
                -1: "Invalid credentials. Please try again.",
                -2: "This device is not authorized. Please contact support.",
                -3: "Unable to connect to the server. Please try again later.",
                -4: "Access to this application has been denied.",
                -5: "Unknown error occurred during authentication.",
            }

            error_message = messages.get(auth_result, "Unknown error occurred.")
            Settings.write_log_dev_file(
                f"Authentication error code: {auth_result} → {error_message}", "WARNING"
            )
            self.erreur_label.setText(error_message)
            self.erreur_label.show()
            return

        id_user, p_entity_Origine = auth_result
        if username == "rep.test":
            entity_pattern = r"^opm\d+$"

            dialog = EntitySelectionDialog(
                pattern=entity_pattern, default_entity=p_entity_Origine, parent=self
            )
            selected_entity = dialog.get_selected_entity()

            if selected_entity is None:
                UIManager.enableButton(self.login_button)
                Settings.write_log_dev_file(
                    "Entity selection canceled. Login aborted.", "WARNING"
                )
                self.erreur_label.setText(
                    "Entity selection is required for this user. Login aborted."
                )
                self.erreur_label.show()
                return

            p_entity_Nouveau = selected_entity
            Settings.write_log_dev_file(
                f"✅ Entity overridden to: {p_entity_Nouveau}", "INFO"
            )
        else:
            p_entity_Nouveau = p_entity_Origine

        try:
            valid_session = SessionManager.create_session(
                username, password, p_entity_Origine, p_entity_Nouveau, id_user
            )
            if not valid_session:
                Settings.write_log_dev_file(
                    "Failed to create user session for unknown reasons.", "ERROR"
                )
                UIManager.enableButton(self.login_button)
                self.erreur_label.setText("Failed to create user session.")
                self.erreur_label.show()
                return
        except Exception as e:
            UIManager.enableButton(self.login_button)
            Settings.write_log_dev_file(
                f"Exception during session creation: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )
            self.erreur_label.setText(
                f"Exception during session creation: {str(e)}\n{traceback.format_exc()}"
            )
            self.erreur_label.show()
            return

        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            if not json_data:
                Settings.write_log_dev_file(
                    f"Configuration file is empty: {Settings.FILE_ACTIONS_JSON}",
                    "WARNING",
                )
                raise ValueError("Fichier de configuration vide")

            Settings.write_log_dev_file(
                "Configuration file loaded successfully.", "INFO"
            )

            UIManager.enableButton(self.login_button)
            self.main_window = AutomationMainWindow(json_data)
            self.main_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
            self.main_window.setWindowTitle("AutoMailPro")
            self.main_window.stopButton.clicked.connect(
                lambda: stopAllProcesses(self.main_window)
            )

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.main_window.width()) // 2
            y = (screen_geometry.height() - self.main_window.height()) // 2
            self.main_window.move(x, y)
            self.main_window.show()
            self.close()
            Settings.write_log_dev_file(
                "Main window displayed, login completed successfully.", "INFO"
            )

        except Exception as e:
            UIManager.enableButton(self.login_button)
            Settings.write_log_dev_file(
                f"An error occurred while loading AutomationMainWindow: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            SessionManager.clear_session()
            self.erreur_label.setText("Unable to open the main application window.")
            self.erreur_label.show()

    def handle_show_session_date(self):
        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file(
                "Session file not found at expected path.", "WARNING"
            )
            self.erreur_label.setText("Session file not found .")
            self.erreur_label.show()
            return
        session_info = SessionManager.check_session()

        if session_info.get("valid"):
            session_data = (
                f"Username: {session_info.get('username')}\n"
                f"Entity: {session_info.get('p_entity_Nouveau')}\n"
                f"Session date: {session_info.get('date')}"
            )
            Settings.write_log_dev_file(
                "Session data retrieved without exposing credentials.", "INFO"
            )
            self.erreur_label.setText(f"Session data:\n{session_data}")
        else:
            Settings.write_log_dev_file(
                f"Session file is not valid: {session_info.get('error', 'Unknown error')}",
                "WARNING",
            )
            self.erreur_label.setText("Session file is not valid.")
        self.erreur_label.show()


def main():
    Settings.write_log_dev_file("\n\n========== [APP START] ==========\n", "INFO")
    Settings.write_log_dev_file("Application starting...", "INFO")
    Settings.write_log_dev_file(f"Received arguments: {sys.argv}", "DEBUG")

    if len(sys.argv) < 3:
        Settings.write_log_dev_file(
            "Insufficient arguments provided. Expected encrypted_key and secret_key.",
            "ERROR",
        )
        Settings.write_log_dev_file(
            "Usage: python AppV2.py <encrypted_key> <secret_key>", "ERROR"
        )
        sys.exit(1)

    encrypted_key = sys.argv[1]
    secret_key = sys.argv[2]

    Settings.write_log_dev_file(f"Encrypted key and secret key received.", "DEBUG")
    Settings.write_log_dev_file("Arguments parsed successfully.", "DEBUG")

    Settings.write_log_dev_file("Verifying key...", "DEBUG")
    if not EncryptionService.verify_key(encrypted_key, secret_key):
        Settings.write_log_dev_file("Invalid key. Access denied.", "ERROR")
        sys.exit(1)
    else:
        Settings.write_log_dev_file("Key is valid.", "INFO")

    Settings.write_log_dev_file("Checking user session...", "DEBUG")
    session_info = SessionManager.check_session_full()
    session_valid = session_info.get("valid", False)

    Settings.write_log_dev_file(f"Session valid: {session_valid}", "DEBUG")
    Settings.write_log_event(
        "application_session_checked", "DEBUG", valid=session_valid
    )

    app = QApplication(sys.argv)
    Settings.write_log_dev_file("QApplication initialized.", "DEBUG")

    icon_path = Path(Settings.APP_ICON)

    if ValidationUtils.pathExists(icon_path):
        app.setWindowIcon(QIcon(str(icon_path)))
        Settings.write_log_dev_file("Application icon set successfully.", "INFO")
    else:
        Settings.write_log_dev_file(f"Icon file not found at: {icon_path}", "WARNING")

    window = None

    if session_valid:
        Settings.write_log_dev_file(
            "Valid session found. Attempting to open AutomationMainWindow.", "INFO"
        )
        try:
            Settings.write_log_dev_file(
                f"Loading config file: {Settings.FILE_ACTIONS_JSON}", "DEBUG"
            )
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            if not json_data:
                Settings.write_log_dev_file(
                    f"Configuration file is empty: {Settings.FILE_ACTIONS_JSON}",
                    "WARNING",
                )
                raise ValueError("Fichier de configuration vide")

            Settings.write_log_dev_file(
                "Configuration file loaded successfully.", "INFO"
            )

            window = AutomationMainWindow(json_data)
            Settings.write_log_dev_file("AutomationMainWindow initialized.", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while loading AutomationMainWindow: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            SessionManager.clear_session()
            window = AuthenticationWindow()

    else:
        Settings.write_log_dev_file(
            "No valid session found. Opening AuthenticationWindow.", "INFO"
        )
        SessionManager.clear_session()
        window = AuthenticationWindow()

    if window is None:
        Settings.write_log_dev_file(
            "Critical error: No window could be created.", "CRITICAL"
        )
        sys.exit(1)

    window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

    screen = QGuiApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()

    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2

    window.move(x, y)

    if hasattr(window, "stopButton"):
        Settings.write_log_dev_file(
            "stopButton detected in window. Attempting to connect.", "DEBUG"
        )
        Settings.write_log_dev_file(
            "stopButton found. Connecting to stopAllProcesses.", "DEBUG"
        )
        try:
            window.stopButton.clicked.connect(lambda: stopAllProcesses(window))
            Settings.write_log_dev_file("stopButton connected successfully.", "INFO")
        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while connecting stopButton: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
    else:
        Settings.write_log_dev_file("No stopButton found in window.", "INFO")

    window.setWindowTitle("AutoMailPro")
    window.show()
    Settings.write_log_dev_file(
        "Application started successfully, window displayed.", "INFO"
    )
    Settings.write_log_dev_file("\n\n========== [APP RUNNING] ==========\n", "INFO")
    Settings.write_log_dev_file("Application is now running.", "INFO")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
