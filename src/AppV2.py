import os
import json
from concurrent.futures import ThreadPoolExecutor
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
import json
from typing import List, Dict, Any, Set
import traceback

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
    # from models import ExtensionManager
    from api import APIManager
    from utils import ValidationUtils
    from ui_utils import UIManager
    from services import JsonManager
    from Update import UpdateManager
except ImportError as e:
    Settings.WRITE_LOG_DEV_FILE(f"Import error in file {__file__}: {e}\n{traceback.format_exc()}", "ERROR")
    sys.exit(1)


# ==========================================================
# 🔹 VARIABLES GLOBALES
# ==========================================================

file_lock = Lock()

FIREFOX_SESSIONS: Dict[str, Any] = {}


LOGS = []
PROCESS_PIDS = []
NOTIFICATION_BADGES = {}
EXTRACTION_THREAD = None
CLOSE_BROWSER_THREAD = None
NEW_VERSION = None
LOGS_RUNNING = True
SELECTED_BROWSER_GLOBAL = None
REMAINING_EMAILS = 0


SESSION_ID = ValidationUtils.generate_session_id()



# ==========================================================
# 🔹 FUNCTION LOG MESSAGE
# ==========================================================


def log_message(text):
    global LOGS
    LOGS.append(text)





# ==========================================================
# 🔹 FUNCTION STOP ALL PROCESSES
# ==========================================================
def Stop_All_Processes(window):
    """Stop all running threads and processes safely."""

    UIManager.disable_button(window.stopButton)
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD
    global PROCESS_PIDS, LOGS_RUNNING, FIREFOX_SESSIONS
    global SELECTED_BROWSER_GLOBAL

    Settings.WRITE_LOG_DEV_FILE("Stopping all processes...", "INFO")
    LOGS_RUNNING = False

    # ==========================================================
    # 🔹 STOP THREADS
    # ==========================================================
    try:
        if EXTRACTION_THREAD:
            Settings.WRITE_LOG_DEV_FILE("Stopping extraction thread...", "INFO")
            EXTRACTION_THREAD.stop_flag = True
            EXTRACTION_THREAD.wait()
            EXTRACTION_THREAD = None
            Settings.WRITE_LOG_DEV_FILE("Extraction thread stopped successfully.", "INFO")
    except Exception as e:
        Settings.WRITE_LOG_DEV_FILE(f"Error stopping extraction thread: {e}\n{traceback.format_exc()}", "ERROR")
    try:
        if CLOSE_BROWSER_THREAD:
            Settings.WRITE_LOG_DEV_FILE("Stopping close browser thread...", "INFO")
            CLOSE_BROWSER_THREAD.stop_flag = True
            CLOSE_BROWSER_THREAD.wait()
            CLOSE_BROWSER_THREAD = None
            Settings.WRITE_LOG_DEV_FILE("Close browser thread stopped successfully.", "INFO")
    except Exception as e:
        Settings.WRITE_LOG_DEV_FILE(f"Error stopping close browser thread: {e}\n{traceback.format_exc()}", "ERROR")
    # ==========================================================
    # 🔹 CHECK SELECTED BROWSER
    # ==========================================================
    if not SELECTED_BROWSER_GLOBAL:
        Settings.WRITE_LOG_DEV_FILE("Stop failed: No browser selected or no processes running.", "WARNING")
        UIManager.Show_Critical_Message(window, "No Processes Running", "No processes are currently running.", message_type="warning")
        UIManager.enable_button(window.submitButton)
        UIManager.enable_button(window.stopButton)
        return
    browser_name = SELECTED_BROWSER_GLOBAL.lower()

    # ==========================================================
    # 🔹 CHROME / CHROMIUM / EDGE
    # ==========================================================
    if browser_name != "firefox":
        for pid in PROCESS_PIDS[:]:
            try:
                Settings.WRITE_LOG_DEV_FILE(f"Attempting to terminate process with PID {pid}...", "INFO")
                process = psutil.Process(pid)
                # --------------------------------------------------
                # NORMAL TERMINATION
                # --------------------------------------------------
                process.terminate()
                try:
                    process.wait(timeout=5)
                    Settings.WRITE_LOG_DEV_FILE(f"Process {pid} terminated successfully.", "INFO")
                # --------------------------------------------------
                # FORCE KILL
                # --------------------------------------------------
                except psutil.TimeoutExpired:
                    Settings.WRITE_LOG_DEV_FILE(f"Timeout for PID {pid}, forcing kill...", "WARNING")
                    process.kill()
                    try:
                        process.wait(timeout=3)
                        Settings.WRITE_LOG_DEV_FILE(f"Process {pid} killed successfully.", "INFO")
                    except psutil.NoSuchProcess:
                        Settings.WRITE_LOG_DEV_FILE(f"Process {pid} already closed after kill.", "INFO")
                    except psutil.TimeoutExpired:
                        Settings.WRITE_LOG_DEV_FILE(f"Failed to kill PID {pid} after timeout.", "ERROR")
                except psutil.NoSuchProcess:
                    Settings.WRITE_LOG_DEV_FILE(f"Process {pid} already terminated.", "INFO")
            # ======================================================
            # NO SUCH PROCESS
            # ======================================================
            except psutil.NoSuchProcess:
                Settings.WRITE_LOG_DEV_FILE(f"Process {pid} no longer exists.", "INFO")
            # ======================================================
            # ACCESS DENIED
            # ======================================================
            except psutil.AccessDenied:
                Settings.WRITE_LOG_DEV_FILE(f"Permission denied for PID {pid}.", "WARNING")
            # ======================================================
            # UNKNOWN ERROR
            # ======================================================
            except Exception as e:
                Settings.WRITE_LOG_DEV_FILE(f"Unexpected error terminating PID {pid}: {e}\n{traceback.format_exc()}", "ERROR")
            # ======================================================
            # CLEAN LIST
            # ======================================================
            finally:
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                    Settings.WRITE_LOG_DEV_FILE(f"PID {pid} removed from process list.", "INFO")
    # ==========================================================
    # 🔹 FIREFOX
    # ==========================================================
    else:
        try:
            Settings.WRITE_LOG_DEV_FILE("Closing Firefox profiles using stored session entries...", "INFO")
            if FIREFOX_SESSIONS:
                session_entries = list(FIREFOX_SESSIONS.values())
                Settings.WRITE_LOG_DEV_FILE(f"Closing {len(session_entries)} Firefox session entries", "DEBUG")
                BrowserManager.Close_Windows_By_Profiles(session_entries)
            else:
                Settings.WRITE_LOG_DEV_FILE("No Firefox sessions found, unable to close Firefox profiles.", "WARNING")
            Settings.WRITE_LOG_DEV_FILE("Firefox profiles closed successfully.", "INFO")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Error closing Firefox profiles: {e}\n{traceback.format_exc()}", "WARNING")
        finally:
            if PROCESS_PIDS:
                for pid in PROCESS_PIDS[:]:
                    PROCESS_PIDS.remove(pid)
                    Settings.WRITE_LOG_DEV_FILE(f"PID {pid} removed from process list.", "INFO")
            if FIREFOX_SESSIONS:
                FIREFOX_SESSIONS.clear()
                Settings.WRITE_LOG_DEV_FILE("FIREFOX_SESSIONS cleared", "DEBUG")
    # ==========================================================
    # 🔹 ENABLE BUTTONS
    # ==========================================================
    UIManager.enable_button(window.submitButton)
    UIManager.enable_button(window.stopButton)
    Settings.WRITE_LOG_DEV_FILE("All stop operations completed.", "INFO")




class LogsDisplayThread(QThread):

    log_signal = pyqtSignal(str)

    def __init__(self, LOGS, parent=None):
        super().__init__(parent)
        self.LOGS = LOGS
        self.stop_flag = False
    
    # =====================================================
    # 🔁 THREAD PRINCIPAL
    # =====================================================
    def run(self):
        global LOGS_RUNNING
        while LOGS_RUNNING:
            if self.LOGS:
                log_entry = self.LOGS.pop(0)
                self.log_signal.emit(log_entry)
            else:
                time.sleep(1)

    def stop(self):
        self.stop_flag = True
        self.wait()










# ==========================================================
# CLOSE BROWSER MONITORING THREAD
#
# This QThread continuously monitors the downloads directory
# to detect and process generated session files, logs, and
# screenshots while tracking active browser processes.
#
# Responsibilities:
# - Monitor filesystem changes in real time
# - Process session and log files using parallel workers
# - Track active browser processes (PROCESS_PIDS)
# - Safely handle termination conditions
# - Automatically stop when no active work remains
#
# The thread is designed to be:
# - Interruptible via stop_flag
# - CPU efficient with controlled sleep cycles
# - Thread-safe for shared global resources
# Exemples of session file and log file names:
#         log_2026-06-03T10-15-30-123Z_test@gmail.com.txt
#         ABC123_test@gmail.com_success.txt
# ==========================================================

class CloseBrowserThread(QThread):

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

        # ✅ tracking success emails (thread-safe)
        self.completed_emails = set()
        self.lock = threading.Lock()

        Settings.WRITE_LOG_DEV_FILE(f"Thread created | Browser={selected_Browser} | User={username} | downloads_folder={self.downloads_folder} | session_id={self.session_id} | session_dir={self.SESSION_DIR}", "INFO")
        
    # ======================================================
    # 🔁 THREAD PRINCIPAL
    # ======================================================
    def run(self):
        global PROCESS_PIDS, REMAINING_EMAILS

        # Attente interruptible de 10 secondes
        start_wait = time.time()
        Settings.WRITE_LOG_DEV_FILE(f"Waiting initial delay before processing files: 10s", "DEBUG")
        while time.time() - start_wait < 10 and not self.stop_flag:
            time.sleep(1)

        if self.stop_flag:
            Settings.WRITE_LOG_DEV_FILE("🛑 [THREAD] Stop requested during initial wait", "INFO")
            return

        empty_counter = 0

        while not self.stop_flag:
            try:
                all_files = os.listdir(self.downloads_folder)

                session_files = [  f for f in all_files if f.startswith(self.session_id) and f.endswith(".txt")  ]
                log_files = [  f  for f in all_files  if f.startswith("log_") and f.endswith(".txt") ]
                screenshots = [ f  for f in all_files if f.lower().endswith((".png", ".jpg", ".jpeg")) ]

                current_time = time.strftime("%H:%M:%S", time.localtime())
                Settings.WRITE_LOG_DEV_FILE( f"[LOOP] {current_time} | stop_flag={self.stop_flag} | PROCESS_PIDS={len(PROCESS_PIDS)} | REMAINING_EMAILS={REMAINING_EMAILS} | session_files={len(session_files)} | log_files={len(log_files)} | screenshots={len(screenshots)} | empty_counter={empty_counter}",  "DEBUG"  )
                Settings.WRITE_LOG_DEV_FILE(f"[LOOP] downloaded files: {all_files}", "TRACE" if hasattr(Settings, 'TRACE') else "DEBUG")

                if PROCESS_PIDS:
                    empty_counter = 0

                    # 🔹 logs
                    if log_files:
                        Settings.WRITE_LOG_DEV_FILE(f"Processing log files: {len(log_files)} -> {log_files}", "DEBUG")
                        with ThreadPoolExecutor(max_workers=4) as executor:
                            executor.map(self.process_log_file, log_files)
                        Settings.WRITE_LOG_DEV_FILE("Finished processing log files", "DEBUG")

                    # 🔹 sessions
                    if session_files:
                        Settings.WRITE_LOG_DEV_FILE(f"Processing session files: {len(session_files)} -> {session_files}", "DEBUG")
                        with ThreadPoolExecutor(max_workers=4) as executor:
                            executor.map(lambda f: self.process_session_file(f, screenshots), session_files)
                        Settings.WRITE_LOG_DEV_FILE("Finished processing session files", "DEBUG")

                    Settings.WRITE_LOG_DEV_FILE(f"PROCESS_PIDS after processing: {len(PROCESS_PIDS)} | REMAINING_EMAILS: {REMAINING_EMAILS}", "DEBUG")

                else:
                    if REMAINING_EMAILS == 0 and not log_files and not session_files:
                        Settings.WRITE_LOG_DEV_FILE("🛑 Aucun PID actif et aucun email restant → arrêt immédiat du thread", "INFO")
                        break

                    empty_counter += 1
                    Settings.WRITE_LOG_DEV_FILE(f"No active PIDs but files remain: log_files={len(log_files)}, session_files={len(session_files)} | empty_counter={empty_counter}", "WARNING")
                    if empty_counter >= 15:
                        Settings.WRITE_LOG_DEV_FILE("🛑 PROCESS_PIDS vide → arrêt du thread après attente", "WARNING")
                        break

                Settings.WRITE_LOG_DEV_FILE(f"📊 Fin d'itération: logs={len(log_files)}, sessions={len(session_files)}, screenshots={len(screenshots)}", "DEBUG")

                start_sleep = time.time()
                while time.time() - start_sleep < 1 and not self.stop_flag:
                    time.sleep(0.1)

            except Exception as e:
                Settings.WRITE_LOG_DEV_FILE(  f"❌ [THREAD] Erreur: {e}\n{ traceback.format_exc()}", "ERROR" )
                # print(f"❌ [THREAD] Erreur: {e}")

        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # print(f"\n🛑 [THREAD] CloseBrowserThread TERMINÉ")
        # print(f"  ⏰ Fin: {end_time}")
        # print(f"  📊 PROCESS_PIDS: {PROCESS_PIDS} | REMAINING_EMAILS: {REMAINING_EMAILS}")
        Settings.WRITE_LOG_DEV_FILE(  f"Thread finished | End time: {end_time} | PROCESS_PIDS: {len(PROCESS_PIDS)} | REMAINING_EMAILS: {REMAINING_EMAILS}",  "INFO"  )


    # ==========================================================
    # LOG FILE PROCESSING PIPELINE
    #
    # This function processes browser-generated log files from
    # the downloads directory.
    #
    # Responsibilities:
    # - Safely stop processing when thread is requested to stop
    # - Extract user email from log file content
    # - Prevent duplicate processing using thread-safe locking
    # - Organize logs into structured directories:
    #     SESSION_DIR / Browser / Email /
    # - Copy log content into a persistent structured file
    # - Remove original temporary log file after processing
    #
    # This ensures:
    # - Clean downloads directory
    # - Structured session-based log storage
    # - No duplicate processing of the same email
    # ==========================================================
    
    def process_log_file(self, log_file):
        if self.stop_flag:
            Settings.WRITE_LOG_DEV_FILE("🛑 [LOG] Stop requested", "INFO")
            return

        full_path = os.path.join(self.downloads_folder, log_file)
        Settings.WRITE_LOG_DEV_FILE(f"[LOG] Starting log file processing: {log_file} | full_path={full_path}", "DEBUG")

        try:
            if not os.path.exists(full_path):
                Settings.WRITE_LOG_DEV_FILE(f"[LOG] File not found during processing: {full_path}", "ERROR")
                return

            email = ValidationUtils.get_email_from_log_file(full_path)
            Settings.WRITE_LOG_DEV_FILE(f"[LOG] Extracted email from log file: {email}", "DEBUG")

            if not email:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    sample = f.read(256)
                Settings.WRITE_LOG_DEV_FILE( f"No email found in log file content sample: {sample!r}", "ERROR")
                return

            with self.lock:
                if email in self.completed_emails:
                    Settings.WRITE_LOG_DEV_FILE(f"Email {email} already processed, skipping log file: {log_file}", "INFO")
                    return

            email_folder = os.path.join(self.SESSION_DIR, self.selected_Browser, email)
            os.makedirs(email_folder, exist_ok=True)
            Settings.WRITE_LOG_DEV_FILE(f"[LOG] Email folder ensured: {email_folder}", "DEBUG")

            target_log = os.path.join(email_folder, f"{email}_{self.CURRENT_DATETIME}.txt")
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            Settings.WRITE_LOG_DEV_FILE(f"[LOG] Read log file content length: {len(content)}", "DEBUG")

            with open(target_log, "a", encoding="utf-8") as tf:
                tf.write(content + "\n")
            Settings.WRITE_LOG_DEV_FILE(f"[LOG] Appended log to target file: {target_log}", "DEBUG")

            os.remove(full_path)
            Settings.WRITE_LOG_DEV_FILE(f"✅ [LOG] Processed and removed source file: {full_path}", "INFO")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"❌ [LOG] Erreur processing log file {full_path}: {e}\n{ traceback.format_exc()}", "ERROR")



    # ==========================================================
    # FIREFOX PROCESS CLEANUP HANDLER
    #
    # This function is responsible for safely terminating all
    # Firefox-related processes associated with a session.
    #
    # Responsibilities:
    # - Kill all Firefox PIDs linked to a profile/session
    # - Safely terminate the web-ext process (extension runner)
    # - Remove cleaned PIDs from global PROCESS_PIDS registry
    # - Handle missing or already terminated processes safely
    # - Prevent process leaks after session completion
    # ==========================================================
    
    def _close_firefox_session(self, firefox_pids, web_ext_pid, email, flow_label=""):
        if firefox_pids:
            Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] Closing Firefox PIDs: {firefox_pids} for {email}", "INFO")
            for firefox_pid in firefox_pids:
                try:
                    if psutil.pid_exists(firefox_pid):
                        psutil.Process(firefox_pid).kill()
                        Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] Firefox PID {firefox_pid} killed successfully", "INFO")
                    else:
                        Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] Firefox PID {firefox_pid} no longer exists", "INFO")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] Error closing Firefox PID {firefox_pid}: {e}", "WARNING")
        else:
            Settings.WRITE_LOG_DEV_FILE(f"No Firefox PIDs for {email} {flow_label}".strip(), "WARNING")

        if web_ext_pid:
            try:
                if psutil.pid_exists(web_ext_pid):
                    psutil.Process(web_ext_pid).kill()
                    Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} killed successfully", "INFO")
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} no longer exists", "INFO")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} already closed", "INFO")

        if web_ext_pid in PROCESS_PIDS:
            PROCESS_PIDS.remove(web_ext_pid)
            Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] web-ext PID {web_ext_pid} removed from PROCESS_PIDS queue", "INFO")


    # ==========================================================
    # GENERIC BROWSER SESSION CLOSURE
    #
    # Unified entry point to close browser processes depending
    # on the browser type (Firefox or Chromium-based browsers).
    #
    # Responsibilities:
    # - Route closure logic based on browser type
    # - Use Firefox-specific cleanup if browser is Firefox
    # - Use generic process termination for Chromium browsers
    # - Ensure safe fallback when PID is missing
    # ==========================================================
    def _close_session(self, pid, email, browser, firefox_pids, web_ext_pid, flow_label=""):
        if browser.lower() == "firefox":
            self._close_firefox_session(firefox_pids, web_ext_pid, email, flow_label)
        else:
            if pid:
                self._close_browser_process(pid, email, browser)
                Settings.WRITE_LOG_DEV_FILE(f"[CLOSE{flow_label}] Process {pid} closed for {email}", "INFO")
            else:
                Settings.WRITE_LOG_DEV_FILE(f"No PID for {email} {flow_label}".strip(), "WARNING")

    
    # ==========================================================
    # SESSION FILE PARSER AND PROCESSOR
    #
    # This function handles browser session files and extracts
    # execution state information.
    #
    # Responsibilities:
    # - Parse session_id, email, and status using regex
    # - Retrieve browser-specific process information
    # - Handle Firefox sessions from memory registry
    # - Handle Chromium sessions from disk profile files
    # - Execute success or error flow logic
    # - Close related browser processes safely
    # - Move screenshots if error flow is triggered
    # - Clean up session files after processing
    # ==========================================================
    def process_session_file(self, file_name, screenshots):
        if self.stop_flag:
            Settings.WRITE_LOG_DEV_FILE("🛑 [SESSION] Stop requested", "INFO")
            return

        session_path = os.path.join(self.downloads_folder, file_name)
        Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Starting processing: {file_name} | full_path={session_path}", "DEBUG")

        if not os.path.exists(session_path):
            Settings.WRITE_LOG_DEV_FILE(f"Session file not found: {session_path}", "ERROR")
            return

        try:
            with open(session_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Read content length={len(content)}", "DEBUG")
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Content preview: {content[:200]!r}", "TRACE" if hasattr(Settings, 'TRACE') else "DEBUG")

            regex = r"session_id:(\w+)_email:([\w.@+-]+)_etat:(\w+)"
            match = re.search(regex, content, re.IGNORECASE)
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Using regex={regex} | match_found={bool(match)}", "DEBUG")

            if not match:
                Settings.WRITE_LOG_DEV_FILE(f"❌ [SESSION] Parsing failed for file: {file_name}", "ERROR")
                return

            session_id, email, status = match.groups()
            pid = None
            inserted_id = None
            firefox_pids = []
            web_ext_pid = None
            profile_data_file = None
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Parsed session_id={session_id} email={email} status={status}", "INFO")

            if self.selected_Browser.lower() == "firefox":
                Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Firefox browser detected, looking up FIREFOX_SESSIONS[{email}]", "DEBUG")
                if email in FIREFOX_SESSIONS:
                    firefox_session = FIREFOX_SESSIONS[email]
                    Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Firefox session found: {json.dumps(firefox_session, ensure_ascii=False, default=str)}", "DEBUG")
                    firefox_pids = firefox_session.get("firefox_pids", [])
                    web_ext_pid = firefox_session.get("web_ext_pid")
                    inserted_id = firefox_session.get("inserted_id")
                    pid = firefox_pids 
                    Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Firefox extracted firefox_pids={firefox_pids} web_ext_pid={web_ext_pid} inserted_id={inserted_id}", "INFO")
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"❌ [SESSION] Firefox session not found in FIREFOX_SESSIONS for email={email}", "ERROR")
                    Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Available keys in FIREFOX_SESSIONS: {list(FIREFOX_SESSIONS.keys())}", "WARNING")
            else:
                profile_dir = Settings.CHROME_PROFILES
                if self.selected_Browser.lower() == "edge":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["edge"]["profiles"]
                elif self.selected_Browser.lower() == "icedragon":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["icedragon"]["profiles"]
                elif self.selected_Browser.lower() == "comodo":
                    profile_dir = Settings.CHROMIUM_BROWSER_PATHS["comodo"]["profiles"]

                profile_data_file = os.path.join(profile_dir, email, "data.txt")
                Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Chromium profile data path: {profile_data_file}", "DEBUG")
                if os.path.exists(profile_data_file):
                    with open(profile_data_file, "r", encoding="utf-8", errors="replace") as f:
                        profile_line = f.readline().strip()
                    Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Chromium profile data line: {profile_line}", "DEBUG")
                    try:
                        pid, email_chk, session_id_chk, inserted_id = profile_line.split(":")[:4]
                        Settings.WRITE_LOG_DEV_FILE(f"[SESSION] Chromium extracted pid={pid} email_chk={email_chk} session_id_chk={session_id_chk} inserted_id={inserted_id}", "INFO")
                    except ValueError as e:
                        Settings.WRITE_LOG_DEV_FILE(f"🚨 [SESSION] Failed to parse Chromium profile line: {profile_line} | error={e}", "ERROR")
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"Chromium profile data file not found for {email} at {profile_data_file}", "ERROR")

            Settings.WRITE_LOG_DEV_FILE(f"Session found | Email: {email} | Status: {status} | PID: {pid} | inserted_id: {inserted_id}", "DEBUG")

            # ✅ LIGHT FLOW (completed / bad_proxy)
            if status.lower() in ("completed", "bad_proxy"):
                Settings.WRITE_LOG_DEV_FILE(f"✅ LIGHT FLOW | {email}", "DEBUG")

                with self.lock:
                    self.completed_emails.add(email)

                self.write_result_and_send_status(session_id, pid, email, status, inserted_id)
                self._close_session(pid, email, self.selected_Browser, firefox_pids, web_ext_pid)
                return

            # ❌ ERROR FLOW
            Settings.WRITE_LOG_DEV_FILE(f"ERROR FLOW detected for session {session_id} email={email} status={status}", "DEBUG")

            email_folder = os.path.join(self.SESSION_DIR, self.selected_Browser, email)
            os.makedirs(email_folder, exist_ok=True)

            self._move_screenshot(email, screenshots, email_folder)

            self.write_result_and_send_status(session_id, pid, email, status, inserted_id)
            self._close_session(pid, email, self.selected_Browser, firefox_pids, web_ext_pid, "-ERROR")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(  f"❌ [SESSION] Erreur: {e}\n{ traceback.format_exc()}", "ERROR"  )

        finally:
            # ✅ Nettoyage
            try:
                if os.path.exists(session_path):
                    os.remove(session_path)
                    Settings.WRITE_LOG_DEV_FILE(f"[CLEANUP] Removed session file: {session_path}", "DEBUG")
            except Exception as e:
                Settings.WRITE_LOG_DEV_FILE( f"❌ [CLEANUP] Error removing session file: {e}", "DEBUG"  )

            if self.selected_Browser.lower() == "firefox":
                if email in FIREFOX_SESSIONS:
                    del FIREFOX_SESSIONS[email]
                    Settings.WRITE_LOG_DEV_FILE(f"[CLEANUP] Removed Firefox session for {email}", "DEBUG")
            else:
                try:
                    if profile_data_file and os.path.exists(profile_data_file):
                        os.remove(profile_data_file)
                        Settings.WRITE_LOG_DEV_FILE(f"[CLEANUP] Removed chromium profile data file: {profile_data_file}", "DEBUG")
                except Exception as e:
                    Settings.WRITE_LOG_DEV_FILE( f"❌ [CLEANUP] Error removing profile data file: {e}\n{ traceback.format_exc()}", "DEBUG"  )


    # ==========================================================
    # SESSION RESULT LOGGER + API SENDER
    #
    # This function handles final session reporting by:
    #
    # Responsibilities:
    # - Writing session result to local result file
    # - Formatting result as: session_id:pid:email:status
    # - Sending status update to external API
    # - Mapping status to OK / NotOK format
    # - Handling API failure cases safely
    # ==========================================================

    def write_result_and_send_status(self, session_id, pid, email, status, inserted_id):
        """Écrire le résultat et envoyer l'état"""
        # print(f"\n📝 [RESULT] {email} | Status: {status}")

        if self.stop_flag:
            # print("🛑 [RESULT] Arrêt demandé")
            Settings.WRITE_LOG_DEV_FILE("🛑 [RESULT] Stop requested", "INFO")
            return

        try:
            result_line = f"{session_id}:{pid}:{email}:{status}"
            with open(Settings.RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(f"{result_line}\n")
            Settings.WRITE_LOG_DEV_FILE(f"💾 [RESULT] Résultat écrit: {result_line}", "INFO")

            api_data = { "id": inserted_id,  "login": self.username, "status": "OK" if status.lower() == "completed" else "NotOK",   "error": "" if status.lower() == "completed" else status }

            result = str(APIManager.send_status(api_data))
            # print(f"📡 [RESULT] API result: {result}")
            Settings.WRITE_LOG_DEV_FILE(f"API result: {result}", "INFO")

            if result == -1:
                
                Settings.WRITE_LOG_DEV_FILE(f"API returned -1 for {email}", level="ERROR")
                # print(f"❌ [RESULT] API returned -1 for {email}")
                raise RuntimeError(f"API returned -1 for {email}")

            # print(f"✅ [RESULT] Terminé pour {email}")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"❌ [RESULT] Erreur: {e} details: {traceback.format_exc()}", "ERROR")
            # print(f"❌ [RESULT] Erreur: {e}")
            raise SystemExit(1)

    # ==========================================================
    # SCREENSHOT ORGANIZATION HANDLER
    #
    # This function moves browser-generated screenshots into
    # the correct session/email folder.
    #
    # Responsibilities:
    # - Match screenshots with corresponding email session
    # - Move image files from downloads folder to session folder
    # - Rename or organize screenshots for structured storage
    # - Ensure no duplicate or unrelated screenshots are moved
    # ==========================================================
    
    def _move_screenshot(self, email, screenshots, email_folder):
        try:
            for img in screenshots:
                if email.lower() in img.lower():
                    shutil.move( os.path.join(self.downloads_folder, img),   os.path.join(email_folder, f"{email}.png")  )
                    break
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(  f"⚠️ [SCREENSHOT] Erreur: {e}\n{ traceback.format_exc()}", "ERROR" )
            # print(f"⚠️ Screenshot error: {e}")

    
    # ==========================================================
    # GENERIC PROCESS TERMINATION (NON-FIREFOX)
    #
    # This function safely terminates browser processes using PID.
    #
    # Responsibilities:
    # - Parse PID input (single or list format)
    # - Kill process using OS signal (SIGTERM)
    # - Force terminate if process does not stop
    # - Remove cleaned PID from PROCESS_PIDS list
    # - Prevent zombie or orphan processes
    # ==========================================================
    
    def _close_browser_process(self, pid, email, browser):
        Settings.WRITE_LOG_DEV_FILE(  f"_close_browser_process start | browser={browser} | email={email} | pid={repr(pid)} | pid_type={type(pid).__name__}",  "DEBUG" )

        try:
            if pid is None:
                Settings.WRITE_LOG_DEV_FILE(f"No PID provided for {email} ({browser})", "WARNING")
                return

            pid_list = []
            if isinstance(pid, (list, tuple, set)):
                for item in pid:
                    item_str = str(item).strip()
                    if item_str.isdigit():
                        pid_list.append(int(item_str))
                    else:
                        Settings.WRITE_LOG_DEV_FILE(f"Skipped non-numeric PID segment in list: {repr(item)}", "WARNING"  )
            else:
                pid_str = str(pid).strip()
                if pid_str.isdigit():
                    pid_list = [int(pid_str)]
                else:
                    Settings.WRITE_LOG_DEV_FILE(  f"Invalid PID value for Chromium family: {repr(pid)}", "ERROR"
                    )
                    return

            Settings.WRITE_LOG_DEV_FILE(f"_close_browser_process computed pid_list={pid_list}", "DEBUG")
            if not pid_list:
                Settings.WRITE_LOG_DEV_FILE(f"No valid PID to close for {email} ({browser})", "WARNING")
                return

            for current_pid in pid_list:
                try:
                    os.kill(current_pid, signal.SIGTERM)
                    time.sleep(2)
                    if psutil.pid_exists(current_pid):
                        p = psutil.Process(current_pid)
                        p.terminate()
                        p.wait(timeout=3)
                        Settings.WRITE_LOG_DEV_FILE(f"Chrome closed via terminate() for PID {current_pid}", "INFO")
                    else:
                        Settings.WRITE_LOG_DEV_FILE(f"Chrome closed via SIGTERM for PID {current_pid}", "INFO")
                except Exception as e_chrome:
                    Settings.WRITE_LOG_DEV_FILE(
                        f"Error closing Chrome PID {current_pid}: {e_chrome}\n{traceback.format_exc()}",
                        "ERROR"
                    )

                if current_pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(current_pid)
                    Settings.WRITE_LOG_DEV_FILE(f"PID {current_pid} removed from PROCESS_PIDS", "INFO")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(
                f"❌ [CLOSE] Erreur: {e}\n{traceback.format_exc()}", "ERROR"
            )

    












# ======================================================
# 🚀 FONCTIONS EXTRACTION
# ======================================================


def Start_Extraction(  window, data_list, entered_number, selected_Browser, Isp, unique_id, output_json_final, username):

    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD

    # ValidationUtils.ensure_path_exists(Path(Settings.LOGS_DIRECTORY))

    try:
        entered_number = int(entered_number)
    except ValueError:
        UIManager.Show_Critical_Message( window, "Input Error - Invalid Format",  "Numeric value required. Please check your input and try again.",  message_type="critical")
        Settings.WRITE_LOG_DEV_FILE( "Numeric value required. Please check your input and try again.", "ERROR")
        return

    email_count = len(data_list)
    if entered_number > email_count:
        UIManager.Show_Critical_Message(  window, "Range Error - Exceeded Limit", f"Maximum allowed entries: {email_count}\n" f"Please enter a value between 1 and {email_count}.", message_type="critical")
        Settings.WRITE_LOG_DEV_FILE( f"Maximum allowed entries: {email_count}\nPlease enter a value between 1 and {email_count}.", "ERROR" )
        return


    Settings.WRITE_LOG_DEV_FILE(f"Selected entries: {entered_number}", "INFO")

    browser_normalized = ( selected_Browser.lower() if isinstance(selected_Browser, str) else "unknown")
    Settings.WRITE_LOG_DEV_FILE(f"Browser selection normalized: {browser_normalized}", "INFO")

    browser_path = (
        BrowserManager.get_browser_path("chrome.exe")
        if browser_normalized == "chrome"
        else (
            BrowserManager.get_browser_path("firefox")
            if browser_normalized == "firefox"
            else (
                BrowserManager.get_browser_path("msedge.exe")
                if browser_normalized == "edge"
                else BrowserManager.get_browser_path("dragon.exe")
            )
        )
    )

    browser_name = selected_Browser.strip() if isinstance(selected_Browser, str) else "Unknown"
    browser_path_display = browser_path or "Non trouvé"
    Settings.WRITE_LOG_DEV_FILE( f"Browser startup details | Browser selected: {browser_name} | Executable path: {browser_path_display} | Extraction stage: initialisation",  "INFO" )



    if selected_Browser.lower() == "firefox":
        Settings.ensure_web_ext_installed()


    EXTRACTION_THREAD = ExtractionThread( window, data_list,  SESSION_ID,  entered_number,  browser_path,  window,  selected_Browser,  Isp,  unique_id,  output_json_final)

    EXTRACTION_THREAD.finished.connect(lambda: window.Extraction_Finished(window))
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.stopped.connect(lambda msg: QMessageBox.warning(window, "Arrêté", msg))
    EXTRACTION_THREAD.finished.connect(  lambda: QMessageBox.information(window, "Terminé", "L'extraction est terminée.") )
    EXTRACTION_THREAD.start()

    time.sleep(10)
    Settings.WRITE_LOG_DEV_FILE("Launching CloseBrowserThread...", "INFO")
    CLOSE_BROWSER_THREAD = CloseBrowserThread(selected_Browser, username)
    CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
    CLOSE_BROWSER_THREAD.start()




class ExtractionThread(QThread):

    progress = pyqtSignal(str)
    finished = pyqtSignal()
    stopped = pyqtSignal(str)

    def __init__(  self,  window, data_list, SESSION_ID, entered_number,  Browser_path, main_window, selected_Browser,  Isp, unique_id,  output_json_final ):
        super().__init__()
        self.window = window
        self.data_list = data_list
        self.session_id = SESSION_ID
        self.entered_number = entered_number
        self.Browser_path = Browser_path
        self.stop_flag = False
        self.emails_processed = 0
        self.selected_Browser = ( selected_Browser.strip().lower() if isinstance(selected_Browser, str) else "unknown" )
        self.main_window = main_window
        self.Isp = Isp
        self.unique_id = unique_id
        self.output_json_final = output_json_final


    def _build_encrypted_url(self, ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email):

        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email}"
        try:
            b64 = EncryptionService.encrypt_aes_gcm("A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined)
            url = f"https://example.com/?rep={b64}"
        except Exception:
            Settings.WRITE_LOG_DEV_FILE(f"Error encrypting data for URL: {traceback.format_exc()} ", "ERROR")
            url = ""
        return url, combined


    # ==========================================================
    # PID PARSING - Parse Firefox PID lists ("1001; 2002; abc; 3003" → [1001, 2002, 3003])
    # ==========================================================

    def _parse_pid_list(self, pid_value):
        if pid_value is None:
            Settings.WRITE_LOG_DEV_FILE("_parse_pid_list received None pid_value", "DEBUG")
            return []
        pid_str = str(pid_value).strip()
        if not pid_str:
            Settings.WRITE_LOG_DEV_FILE("_parse_pid_list received empty pid string", "DEBUG")
            return []
        pids = []
        for part in pid_str.split(";"):
            part = part.strip()
            if part.isdigit():
                pids.append(int(part))
            else:
                Settings.WRITE_LOG_DEV_FILE(f"_parse_pid_list skipped non-digit segment: '{part}'", "WARNING")
        Settings.WRITE_LOG_DEV_FILE(f"_parse_pid_list parsed PIDs: {pids} from '{pid_str}'", "DEBUG")
        return pids


    def run(self):

        global PROCESS_PIDS, LOGS_RUNNING, SELECTED_BROWSER_GLOBAL, REMAINING_EMAILS
        SELECTED_BROWSER_GLOBAL = self.selected_Browser
        remaining_emails = self.data_list[:]
        REMAINING_EMAILS = len(remaining_emails)
        log_message("[INFO] Processing started")
        Settings.WRITE_LOG_DEV_FILE( f"ExtractionThread started with browser={self.selected_Browser} | Browser_path={self.Browser_path}",  "INFO")

        session_info = SessionManager.check_session()

        if not session_info["valid"]:
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            Settings.WRITE_LOG_DEV_FILE("Invalid session. Please reconnect.", "ERROR")
            return

        if self.selected_Browser.lower() == "chrome" :
            Settings.RESULTATS_EX = BrowserManager.Upload_EXTENSION_PROXY( "default", Settings.CLES_RECHERCHE, Settings.RESULTATS )

            # 🔹 Vérification si RESULTATS_EX est None
            if Settings.RESULTATS_EX is None:
                UIManager.Show_Critical_Message(self.window, "An issue occurred while copying the JSON file to the template profile ➡ Please contact support.", message_type="critical")
                self.stopped.emit("An issue occurred while copying the JSON file to the template profile ➡ Please contact support.")
                self.stop_flag = True
                Settings.WRITE_LOG_DEV_FILE("An issue occurred while copying the JSON file to the template profile ➡ Please contact support.", "ERROR")
                return  

        # ==========================================================
        # SESSION STORAGE - Save session_id into extension data.txt
        # (Firefox / Chromium) before email processing starts
        # ==========================================================

        try:
            if self.selected_Browser.lower() == "firefox":
                extension_data_path = os.path.join(Settings.EXTENTION_EX3_FIREFOX, "data.txt")
            else:
                extension_data_path = os.path.join(Settings.EXTENTION_EX3_CHROMIUM, "data.txt")
            os.makedirs(os.path.dirname(extension_data_path), exist_ok=True)
            with open(extension_data_path, "w", encoding="utf-8") as f:
                f.write(f"{self.session_id}\n")
            Settings.WRITE_LOG_DEV_FILE(f"Wrote session_id to extension data file: {extension_data_path}", "INFO")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Failed to write session_id to extension data file: {extension_data_path} | error={e}\n{traceback.format_exc()}", "ERROR")

        
        while remaining_emails or PROCESS_PIDS:
            if self.stop_flag:
                LOGS_RUNNING = False
                log_message("[INFO] Processing interrupted by user.")
                Settings.WRITE_LOG_DEV_FILE("Processing interrupted by user.", "INFO")
                break

            if len(PROCESS_PIDS) < self.entered_number and remaining_emails:
                next_email = remaining_emails.pop(0)
                REMAINING_EMAILS = len(remaining_emails)
                email_value = ValidationUtils.get_key_from_dict(next_email, ["email", "Email"])
                log_message(f"[INFO] Processing the email:  {email_value}")
                Settings.WRITE_LOG_DEV_FILE(f"Processing the email: {email_value}", "INFO")

                try:
                    profile_email = ValidationUtils.get_key_from_dict(  next_email, ["email", "Email"])
                    profile_password = ValidationUtils.get_key_from_dict( next_email, ["password_email", "passwordEmail"] )
                    ip_address = ValidationUtils.get_key_from_dict(  next_email, ["ip_address", "ipAddress"] )
                    port = ValidationUtils.get_key_from_dict(next_email, ["port"])
                    login = ValidationUtils.get_key_from_dict(next_email, ["login"])
                    password = ValidationUtils.get_key_from_dict(next_email, ["password"])
                    recovery_email = ValidationUtils.get_key_from_dict(  next_email, ["recovery_email", "recoveryEmail"])
                    new_recovery_email = ValidationUtils.get_key_from_dict(  next_email, ["new_recovery_email", "neWrecoveryEmail"])

                    params = {
                        "l": EncryptionService.encrypt_message( session_info["username"], Settings.KEY ),
                        "login": session_info["username"],
                        "entity": session_info["p_entity_Origine"],
                        "isp": self.Isp,
                        "action": json.dumps(self.output_json_final),
                        "email": email_value,
                        "password": "",
                        "proxy_ip": ip_address + ":" + port,
                        "proxy_login": ( f"{login};{password}" if login != session_info["username"] else ""),
                        "email_recovery": "",
                        "line": "",
                        "app": "V4",
                        "e_pid": self.unique_id
                    }

                    inserted_id = str(APIManager.save_email(params))
                    new_password = ValidationUtils.generate_secure_password(16)

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
                                    Settings.WRITE_LOG_DEV_FILE(  f"Error while deleting {dir_to_delete} : {e}\n{traceback.format_exc()}",  "ERROR"  )
                    except Exception as e:
                        Settings.WRITE_LOG_DEV_FILE( f"Error accessing or creating log directory {Settings.LOGS_DIRECTORY} : {e}\n{traceback.format_exc()}", "ERROR" )
                        logs_subdirs = []

                    if self.selected_Browser.lower() == "firefox":

                        url, combined = self._build_encrypted_url(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email)

                        firefox_profile_path = BrowserManager.create_firefox_profile(profile_email)

                        if not firefox_profile_path:
                            Settings.WRITE_LOG_DEV_FILE(f"❌ [Firefox] Impossible de créer le profil Firefox pour {profile_email}", "ERROR")
                            log_message(f"[ERROR] Impossible de créer le profil Firefox pour {profile_email}")
                            # enregistrer dans le fichier de log que le profil n'a pas pu être créé pour cet email et result "Others"
                            continue

                        Settings.WRITE_LOG_DEV_FILE(f"✅ [Firefox] Profil créé/vérifié: {firefox_profile_path}", "INFO")


                        # ==========================================================
                        # FIREFOX WEB-EXT LAUNCH - Run Firefox extension using web-ext
                        # inside a specific Firefox profile, launch target URL,
                        # start process in background, and store PID for later control
                        # ==========================================================
                        
                        eb_ext_path = Settings.get_web_ext_path()

                        if not eb_ext_path:
                            Settings.WRITE_LOG_DEV_FILE(f"❌ [Firefox] web-ext non trouvé", "ERROR")
                            log_message("[ERROR] web-ext introuvable")
                            continue

                        command = [
                            eb_ext_path,
                            "run",
                            "--source-dir",
                             Settings.EXTENTION_EX3_FIREFOX,
                            "--firefox-profile",
                            os.path.join(Settings.FIREFOX_PROFILES, profile_email),
                            "--url", f"{url}",
                            "--keep-profile-changes",
                            "--no-reload",
                        ]


                        Settings.WRITE_LOG_DEV_FILE( f"Launching Firefox with command: {command}",  "DEBUG"  )
                        Settings.WRITE_LOG_DEV_FILE( f"Firefox profile directory: {os.path.join(Settings.FOLDER_EXTENTIONS_FIREFOX, profile_email)}", "DEBUG" )

                        process = subprocess.Popen(command ,  stdout=subprocess.DEVNULL,   stderr=subprocess.DEVNULL,)
                        PROCESS_PIDS.append(process.pid)
                        Settings.WRITE_LOG_DEV_FILE(f"Firefox web-ext PID: {process.pid}", "INFO")

                        firefox_pids = BrowserManager.find_firefox_pids(firefox_profile_path, process.pid)
                        if not firefox_pids:
                            Settings.WRITE_LOG_DEV_FILE( "Aucune PID Firefox détectée immédiatement après lancement, attente de 2 secondes puis nouvelle recherche",  "WARNING"  )
                            time.sleep(2)
                            firefox_pids = BrowserManager.find_firefox_pids(firefox_profile_path, process.pid)

                        # ==============================================================
                        # If no reliable Firefox PID is found, use the web-ext PID
                        # as a fallback to keep control over the launched session
                        # ==============================================================
                        if not firefox_pids:
                            Settings.WRITE_LOG_DEV_FILE( "Aucune PID Firefox fiable trouvée, utilisation du PID web-ext comme fallback", "WARNING"  )
                            firefox_pids = [process.pid]

                        
                        # ==============================================================
                        # Remove duplicates and sort the PID list
                        # ==============================================================
                        firefox_pids = sorted(set(firefox_pids))

                        # ==============================================================
                        # Convert PID list into a semicolon-separated string
                        # Example: [1234, 5678, 9012] -> "1234;5678;9012"
                        # ==============================================================

                        firefox_pid_string = ";".join(str(pid) for pid in firefox_pids)
                        Settings.WRITE_LOG_DEV_FILE(  f"Firefox PID list stored for profile {profile_email}: {firefox_pid_string}",  "INFO"   )
                        # ==============================================================
                        # Create a complete Firefox session descriptor containing
                        # profile information, process identifiers, launch details,
                        # session identifiers and runtime metadata
                        # ==============================================================

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

                        # ===============================================================
                        # Register the session in the in-memory session registry
                        # for fast runtime access and process management
                        # FIREFOX_SESSIONS = {
                        #     "test@gmail.com": {...},
                        #     "user2@gmail.com": {...}
                        # }
                        # ==============================================================
                        FIREFOX_SESSIONS[profile_email] = firefox_session
                        Settings.WRITE_LOG_DEV_FILE(f"Firefox session map updated for {profile_email}: {json.dumps(firefox_session, ensure_ascii=False)}", "DEBUG")

                        BrowserManager.store_browser_session_info(
                            firefox_pids,
                            Settings.FOLDER_EXTENTIONS_FIREFOX,
                            profile_email,
                            self.session_id,
                            self.selected_Browser.lower(),
                            inserted_id,
                            profile_path=firefox_profile_path,
                            web_ext_pid=process.pid,
                            profile_name=profile_email
                        )

                    elif self.selected_Browser in ["edge", "icedragon", "comodo"]:



                        url, combined = self._build_encrypted_url(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email)

                        if self.selected_Browser == "edge":
                            browser_paths = Settings.CHROMIUM_BROWSER_PATHS["edge"]
                        elif self.selected_Browser == "icedragon":
                            browser_paths = Settings.CHROMIUM_BROWSER_PATHS["icedragon"]
                        else:
                            browser_paths = Settings.CHROMIUM_BROWSER_PATHS["comodo"]

                        profile_dir = browser_paths["profiles"]
                        ValidationUtils.ensure_path_exists(profile_dir, is_file=False)

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
                            "--disable-features=DownloadBubble"
                         ]
                        
                        command1 = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                            f"{url}"
                        ]

                        process = subprocess.Popen(command)
                        time.sleep(3)
                        process1 = subprocess.Popen(command1)
                        PROCESS_PIDS.append(process.pid)

                        BrowserManager.store_browser_session_info(
                            process.pid,
                            profile_dir,
                            profile_email,
                            self.session_id,
                            self.selected_Browser,
                            inserted_id,
                            profile_path=os.path.join(profile_dir, profile_email),
                        )

                    else:

                        url, combined = self._build_encrypted_url(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email)

                        ValidationUtils.ensure_path_exists(Settings.CHROME_PROFILES, is_file=False)

                        if not ValidationUtils.path_exists( os.path.join(Settings.CHROME_PROFILES, profile_email) ):
                            BrowserManager.Run_Browser_Create_Profile(profile_email)

                            if not Settings.RESULTATS_EX:
                                UIManager.Show_Critical_Message(  self.window, "An issue occurred while copying the JSON file to the template profile  ➡ Please contact support.", message_type="critical")
                                self.stopped.emit( "An issue occurred while copying the JSON file to the template profile  ➡ Please contact support." )
                                self.stop_flag = True
                                Settings.WRITE_LOG_DEV_FILE(  "An issue occurred while copying the JSON file to the template profile  ➡ Please contact support.",  "ERROR" )
                                return
                            else:
                                success = BrowserManager.UpdateChromeProfileFromTemplate( profile_email  )
                                if success:
                                    # print(f"✅ Profil {profile_email} mis à jour avec succès.")
                                    Settings.WRITE_LOG_DEV_FILE(f"Profile {profile_email} updated successfully.", "INFO")
                                else:
                                    # print(f"❌ Échec de la mise à jour du profil {profile_email}.")
                                    Settings.WRITE_LOG_DEV_FILE(f"Failed to update profile {profile_email}.", "ERROR")
                                    return

                            time.sleep(1)

                            # reuse previously-built `url`

                            command = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f"--profile-directory={profile_email}",
                                "--lang=En-US",
                                "--no-first-run",
                            ]

                            time.sleep(1)
                            command1 = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f"--profile-directory={profile_email}",
                                f"{url}",
                                "--lang=En-US",
                                "--no-first-run",
                            ]
                            process = subprocess.Popen(command)
                            time.sleep(2)
                            process1 = subprocess.Popen(command1)
                            PROCESS_PIDS.append(process.pid)
                            # print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)
                            # print(f"🚀 PID de processus : {process.pid}")
                            # print(f"🚀 PID de processus 1 : {process1.pid}")
                        else:
                            # reuse previously-built `url`
                            command = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f"--profile-directory={profile_email}",
                                f"{url}",
                                "--lang=En-US",
                                "--no-first-run",
                            ]
                            process = subprocess.Popen(command)
                            PROCESS_PIDS.append(process.pid)

                        BrowserManager.store_browser_session_info(
                            process.pid,
                            Settings.CHROME_PROFILES,
                            profile_email,
                            self.session_id,
                            self.selected_Browser.lower(),
                            inserted_id,
                            profile_path=os.path.join(Settings.CHROME_PROFILES, profile_email),
                        )
                    
                    self.emails_processed += 1

                except Exception as e:
                    # print(f"[INFO] Erreur : {e}")
                    Settings.WRITE_LOG_DEV_FILE( f"Error processing email {profile_email}: {e}\n{traceback.format_exc()}", "ERROR" )

            self.msleep(1000)

        REMAINING_EMAILS = 0
        log_message("[INFO] Processing finished for all emails.")
        Settings.WRITE_LOG_DEV_FILE("Processing finished for all emails.", "INFO")
        UIManager.enable_button(self.window.submitButton)
        time.sleep(3)
        LOGS_RUNNING = False
        self.finished.emit()































# =====================================================
# 🚀 FONCTION CHECK SESSION
# =====================================================

# def Process_Browser(window, selected_Browser) -> bool:

#     # 1️⃣ Vérification du navigateur
#     if selected_Browser.lower() != "chrome":
#         Settings.WRITE_LOG_DEV_FILE(f"Unsupported browser: {selected_Browser}", "WARNING")
#         return False
#     # print("✅ Navigateur : Chrome supporté")

#     # 2️⃣ Vérification du dossier de configuration
#     config_profile = Settings.CONFIG_PROFILE
#     if not os.path.exists(config_profile):
#         Settings.WRITE_LOG_DEV_FILE(f"Configuration folder not found: {config_profile}", "WARNING")
#         return False

#     # 3️⃣ Vérification du fichier secure_preferences
#     secure_prefs = Settings.SECURE_PREFERENCES_TEMPLATE
#     if not os.path.exists(secure_prefs):
#         Settings.WRITE_LOG_DEV_FILE(f"Secure preferences file not found: {secure_prefs}", "WARNING")
#         return False

#     # Lecture du fichier JSON
#     try:
#         with open(secure_prefs, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         Settings.WRITE_LOG_DEV_FILE( f"Secure preferences file loaded successfully: {secure_prefs}", "INFO" )
#     except Exception as e:
#         Settings.WRITE_LOG_DEV_FILE( f"Error reading JSON file: {e}\n{traceback.format_exc()}", "ERROR" )
#         return False

#     required_keys = Settings.CLES_RECHERCHE
#     results_keys = []
#     Settings.WRITE_LOG_DEV_FILE(f"Searching JSON for required keys: {required_keys}", "INFO")
#     BrowserManager.Search_Keys(data, required_keys, results_keys)

#     found_keys = [list(d.keys())[0] for d in results_keys]
#     found_key_details = [
#         (
#             f"{list(d.keys())[0]} at {next(iter(d.values()))['path']}"
#             if isinstance(next(iter(d.values())), dict) and "path" in next(iter(d.values()))
#             else str(list(d.keys())[0])
#         )
#         for d in results_keys
#     ]
#     missing_keys = [key for key in required_keys if key not in found_keys]

#     Settings.WRITE_LOG_DEV_FILE(f"Found keys: {found_keys}", "INFO")
#     Settings.WRITE_LOG_DEV_FILE(f"Found key details: {found_key_details}", "INFO")
#     Settings.WRITE_LOG_DEV_FILE(f"Total keys found: {len(found_keys)}", "INFO")

#     if missing_keys:
#         detailed_error = f"Missing keys in secure_preferences JSON file:\n"
#         detailed_error += f"  - Required keys: {', '.join(required_keys)}\n"
#         detailed_error += f"  - Found keys: {', '.join(found_keys) if found_keys else 'NONE'}\n"
#         detailed_error += f"  - Missing keys: {', '.join(missing_keys)}\n"
#         detailed_error += f"  - File path: {secure_prefs}\n"
#         detailed_error += f"  - Search results detail: {found_key_details}"

#         Settings.WRITE_LOG_DEV_FILE(detailed_error, "ERROR")

#         UIManager.Show_Critical_Message(
#             window,
#             "Configuration Error",
#             "The Chrome configuration file is missing required Settings.\n\n"
#             "Please verify your configuration and try again.\n"
#             "If the problem persists, please contact Support.",
#             message_type="critical",
#         )
#         return False

#     Settings.WRITE_LOG_DEV_FILE("All required JSON keys were found", "SUCCESS")

#     # 5️⃣ Vérification et mise à jour de l'extension
#     ext_path = Settings.EXTENTION_EX3_CHROMIUM
#     if not ValidationUtils.path_exists(ext_path):
#         Settings.WRITE_LOG_DEV_FILE(f"Extension not found, downloading...", "INFO")
#         valid_ext_dir = ValidationUtils.validate_directory_path(ext_path, must_exist=False)
#         if not valid_ext_dir:
#             Settings.WRITE_LOG_DEV_FILE(f"Invalid extension path: {ext_path}", "WARNING")
#             return False
#         if UpdateManager.update_extension_from_server():
#             Settings.WRITE_LOG_DEV_FILE(f"Extension installed successfully", "INFO")
#         else:
#             Settings.WRITE_LOG_DEV_FILE(f"Failed to install extension", "WARNING")
#             return False
#     else:
#         Settings.WRITE_LOG_DEV_FILE(f"Extension found: {ext_path}", "INFO")
#         manifest_file = os.path.join(ext_path, "manifest.json")
#         if not os.path.exists(manifest_file):
#             Settings.WRITE_LOG_DEV_FILE(f"manifest.json not found", "WARNING")
#             return False

#         remote_version = UpdateManager.check_version_extension(window)
#         if isinstance(remote_version, str):
#             Settings.WRITE_LOG_DEV_FILE(f"Update available: {remote_version}", "INFO")
#             if UpdateManager.update_extension_from_server(remote_version):
#                 Settings.WRITE_LOG_DEV_FILE(f"Extension updated successfully", "INFO")
#             else:
#                 Settings.WRITE_LOG_DEV_FILE(f"Failed to update extension", "WARNING")
#                 return False
#         elif remote_version is True:
#             Settings.WRITE_LOG_DEV_FILE("✅ Extension déjà à jour", "INFO")
#         else:
#             Settings.WRITE_LOG_DEV_FILE(f"Failed to check extension version", "WARNING")
#             return False
    

#     Settings.WRITE_LOG_DEV_FILE(f"Processing completed successfully for Chrome browser", "INFO")
#     return True





class MainWindow(QMainWindow):

    
    def __init__(self, json_data):
        super(MainWindow, self).__init__()
        self._init_ui()
        self._init_data(json_data)
        self._setup_ui_components()
        self._load_initial_state()

    def _init_ui(self):
        # print("🟢 Initialisation de l'interface utilisateur...")
        Settings.WRITE_LOG_DEV_FILE("Initializing user interface...", "INFO")
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
        widget = self.findChild(widget_type, name) if widget_type else self.findChild(QWidget, name)
        # print(f"🔍 Recherche du widget : {name} ({widget_type})")
        Settings.WRITE_LOG_DEV_FILE(f"Searching for widget: {name} (type: {widget_type})", "INFO")
        return widget

    
    def _setup_containers(self):
        UIManager._setup_containers(self)

    
    def _setup_template_widgets(self):
        UIManager._setup_template_widgets(self)

    
    def _setup_buttons(self):
        self.Button_Initaile_state = self._setup_button(  "Button_Initaile_state", self.Load_Initial_Options)
        # print(f"🟢 Bouton 'Initial State' configuré avec succès")

        # Submit button
        self.submit_button = self._setup_button( "submitButton", lambda: self.Submit_Button_Clicked(self))
        # print(f"🟢 Bouton 'Submit' configuré avec succès")

        # Clear button with icon
        self.ClearButton = self._setup_icon_button(  "ClearButton", "clear.png",  self.Clear_Button_Clicked, icon_size=(32, 32), button_size=(36, 36))

        # print(f"🟢 Bouton 'Clear' configuré avec succès")
        # Copy button with icon
        self.CopyButton = self._setup_icon_button( "CopyButton",  "copyLog.png",  self.Copy_Logs_To_Clipboard, icon_size=(26, 26),  button_size=(38, 38) )
        
        # print(f"🟢 Bouton 'Copy' configuré avec succès")

        # Save button with icon
        self.SaveButton = self._setup_icon_button( "saveButton", "save.png", self.Handle_Save, icon_size=(16, 16) )
        # print(f"🟢 Bouton 'Save' configuré avec succès")

        # Logout button
        self.log_out_Button = UIManager._setup_logout_button(self, self.logOut)

    def _setup_icon_button(  self, button_name, icon_file, callback, icon_size=None, button_size=None ):
        return UIManager._setup_icon_button(  self, button_name, icon_file, callback, icon_size, button_size )

    def _setup_button(self, widget_name, callback):
        return UIManager._setup_button(self, widget_name, callback)

    def _setup_comboboxes(self):
        self._setup_browser_combobox()
        self._setup_isp_combobox()
        self._setup_scenario_combobox()

    def _setup_browser_combobox(self):
        UIManager._setup_browser_combobox(self)

    def _setup_isp_combobox(self):
        UIManager._setup_isp_combobox(self)

    def _setup_scenario_combobox(self):
        UIManager._setup_scenario_combobox(self)

    def _setup_tab_widgets(self):
        UIManager._setup_result_tab_widget(self)
        UIManager._setup_interface_tab_widget(self)

    def _setup_log_system(self):
        # Chercher le container des logs
        self.log_container = self._find_widget("log", QWidget)
        if self.log_container is not None:
            # Créer un QPlainTextEdit au lieu de QVBoxLayout
            self.log_text_edit = QPlainTextEdit(self.log_container)
            self.log_text_edit.setReadOnly(True)  # Lecture seule pour les logs
            self.log_text_edit.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #161a1d;
                    color: #ffffff;
                    font-size: 14px;
                    font-family: 'Segoe UI';
                    border: none;
                    padding: 8px;
                }
            """)
            self.log_text_edit.setFrameShape(QFrame.Shape.NoFrame)
            self.log_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.log_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.log_text_edit.document().setMaximumBlockCount(1000)

            # Positionner le champ de logs sous les boutons Clear / Copy existants
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

        # Créer le thread de logs et connecter le signal
        self.LOGS_THREAD = LogsDisplayThread(LOGS)
        self.LOGS_THREAD.log_signal.connect(self.Update_Logs_Display)

    def _setup_miscellaneous(self):
        UIManager._setup_miscellaneous(self)

    def _load_initial_state(self):
        self.Load_Scenarios_Into_Combobox()
        self.Load_Initial_Options()

    def Save_Process(self, params):
        return APIManager.save_process(params)

    def Handle_Save(self):
        # print("🔄 [Handle_Save] Starting Handle_Save function...")

        # 1️⃣ Check if there is data to save
        # print(  f"🔍 [Handle_Save] Checking STATE_STACK: {len(self.STATE_STACK) if self.STATE_STACK else 0} items" )
        Settings.WRITE_LOG_DEV_FILE(f"Checking STATE_STACK: {len(self.STATE_STACK) if self.STATE_STACK else 0} items", "INFO")
        if not self.STATE_STACK:
            # print("❌ [Handle_Save] STATE_STACK is empty, showing error message")
            UIManager.Show_Critical_Message(
                self,
                "No Data",
                "No actions to save. Please add actions before saving.",
                message_type="critical",
            )
            Settings.WRITE_LOG_DEV_FILE( "No actions to save. Please add actions before saving.", "ERROR" )
            return

        # print("✅ [Handle_Save] STATE_STACK has data, proceeding to get scenario name")
        scenario_name, ok = QInputDialog.getText(self, "Save Scenario", "Enter scenario name:")

        if not ok:
            # print("⚠️ [Handle_Save] User cancelled scenario name input")
            Settings.WRITE_LOG_DEV_FILE("User cancelled scenario name input", "INFO")
            # User clicked Cancel
            return

        scenario_name = scenario_name.strip()
        # print(f"📝 [Handle_Save] Scenario name entered: '{scenario_name}'")
        Settings.WRITE_LOG_DEV_FILE(f"Scenario name entered: '{scenario_name}'", "INFO")

        if not scenario_name:
            # print("❌ [Handle_Save] Scenario name is empty, showing error message")
            Settings.WRITE_LOG_DEV_FILE("Scenario name cannot be empty", "ERROR")
            UIManager.Show_Critical_Message(  self, "Invalid Name", "Scenario name cannot be empty.", message_type="critical")
            return

        # print("✅ [Handle_Save] Scenario name is valid, checking session file")
        Settings.WRITE_LOG_DEV_FILE("Scenario name is valid, checking session file", "INFO")
        # 3️⃣ Check if session file exists
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            # print(f"❌ [Handle_Save] Session file not found at: {Settings.SESSION_PATH}")
            Settings.WRITE_LOG_DEV_FILE(f"Session file not found at: {Settings.SESSION_PATH}", "ERROR")
            UIManager.Show_Critical_Message(
                self,
                "Session Not Found",
                "[❌] Your session file is missing. Please restart the application.",
                message_type="critical",
            )
            Settings.WRITE_LOG_DEV_FILE( "Your session file is missing. Please restart the application.", "ERROR")
            return

        # print("✅ [Handle_Save] Session file exists, checking session validity")
        Settings.WRITE_LOG_DEV_FILE("Session file exists, checking session validity", "INFO")
        # 4️⃣ Check session validity
        session_info = SessionManager.check_session()
        # print( f"🔐 [Handle_Save] Session info: valid={session_info.get('valid')}, user={session_info.get('username')}")
        Settings.WRITE_LOG_DEV_FILE(f"Session info: valid={session_info.get('valid')}, user={session_info.get('username')}", "INFO")

        if not session_info["valid"]:
            # print("❌ [Handle_Save] Session is invalid, exiting")
            Settings.WRITE_LOG_DEV_FILE("Session is invalid, exiting", "ERROR")
            sys.exit()
            return False

        # print("✅ [Handle_Save] Session is valid, encrypting session info")
        Settings.WRITE_LOG_DEV_FILE("Session is valid, encrypting session info", "INFO")
        # 5️⃣ Encrypt session info
        encrypted_String = EncryptionService.encrypt_message( f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT", Settings.KEY)
        # print(f"🔒 [Handle_Save] Encrypted string generated (length: {len(encrypted_String)})")
        Settings.WRITE_LOG_DEV_FILE(f"Encrypted string generated (length: {len(encrypted_String)})", "INFO")

        Settings.WRITE_LOG_DEV_FILE("Preparing payload", "INFO" )
        # 6️⃣ Prepare payload
        try:
            state_json = json.dumps(self.STATE_STACK[-1], ensure_ascii=False)
            state_stack_json = json.dumps(self.STATE_STACK, ensure_ascii=False)

            state_b64 = base64.b64encode(state_json.encode("utf-8")).decode("utf-8")
            state_stack_b64 = base64.b64encode(state_stack_json.encode("utf-8")).decode("utf-8")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE( f"Error encoding state for saving: {e}\n{traceback.format_exc()}", "ERROR" )
            # print("❌ Error encoding state:", e)
            return

        payload = {
            "user_id": session_info["Id_User"],
            "encrypted": encrypted_String,
            "name": scenario_name,
            "state": state_b64,
            "state_stack": state_stack_b64,
        }
        # print(  f"📋 [Handle_Save] Complete payload: {json.dumps(payload, indent=2, ensure_ascii=False)}" )
        Settings.WRITE_LOG_DEV_FILE(f"Complete payload prepared for API call", "INFO")

        # print("🌐 [Handle_Save] Building API URL")
        Settings.WRITE_LOG_DEV_FILE("Building API URL", "INFO")
        # 7️⃣ API URL
        Api_Url = f"https://reporting.nrb-apps.com/pub/ReportingV4/senario.php?rv4=1&entity=IT&action=add&l={encrypted_String}"

        # print(f"🔗 [Handle_Save] API URL: {Api_Url}")
        Settings.WRITE_LOG_DEV_FILE(f"API URL: {Api_Url}", "INFO")
        # return

        # print("📡 [Handle_Save] Calling API...")
        Settings.WRITE_LOG_DEV_FILE("Calling API...", "INFO")
        # 8️⃣ Call API
        try:
            result = APIManager.handle_save_scenario(payload, Api_Url)
            # print(f"📥 [Handle_Save] API response received: {result}")
            Settings.WRITE_LOG_DEV_FILE(f"API response received: {result}", "INFO")

            if result.get("status") is False:
                # print("❌ [Handle_Save] API returned status=False, showing error message")
                Settings.WRITE_LOG_DEV_FILE("API returned status=False, showing error message", "INFO")
                UIManager.Show_Critical_Message(
                    self,
                    "Action Not Saved",
                    "❌ The action could not be saved.\n\n"
                    "Your session may have expired, or this name already exists.\n"
                    "Please verify your session and make sure the name is unique, then try again.",
                    message_type="critical",
                )
                Settings.WRITE_LOG_DEV_FILE( "Save failed: session expired or action name already exists.", "ERROR" )
                return

            if result.get("status"):
                # print("✅ [Handle_Save] API returned status=True, scenario saved successfully")
                Settings.WRITE_LOG_DEV_FILE("API returned status=True, scenario saved successfully", "INFO")
                self.Load_Scenarios_Into_Combobox()
                UIManager.Show_Critical_Message(
                    self,
                    "Success",
                    "The scenario has been saved successfully.",
                    message_type="success",
                )
                Settings.WRITE_LOG_DEV_FILE("The scenario has been saved successfully.", "INFO")
            else:
                # print("⚠️ [Handle_Save] API returned status=None or unexpected, showing API error")
                Settings.WRITE_LOG_DEV_FILE("API returned status=None or unexpected, showing API error", "INFO")
                UIManager.Show_Critical_Message(
                    self,
                    "API Error",
                    "An error occurred while saving the scenario.",
                    message_type="critical",
                )
                Settings.WRITE_LOG_DEV_FILE("An error occurred while saving the scenario.", "ERROR")

        except Exception as e:
            # print(f"💥 [Handle_Save] Exception during API call: {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Exception during API call: {e}", "ERROR")
            UIManager.Show_Critical_Message(
                self,
                "Error",
                "An error occurred while saving the scenario.",
                message_type="critical",
            )
            Settings.WRITE_LOG_DEV_FILE(  f"An error occurred while saving the scenario: {str(e)}\n{traceback.format_exc()}",  "ERROR" )

        # print("🏁 [Handle_Save] Handle_Save function completed")
        Settings.WRITE_LOG_DEV_FILE("Handle_Save function completed", "INFO")

    def Load_Scenarios_Into_Combobox(self):
        # print("\n🔄 [LOAD_SCENARIOS] Starting Load_Scenarios_Into_Combobox()")
        Settings.WRITE_LOG_DEV_FILE("Starting Load_Scenarios_Into_Combobox()", "INFO")

        if self.saveSanario is None:
            # print("❌ [ERROR] saveSanario is None")
            Settings.WRITE_LOG_DEV_FILE("saveSanario is None", "ERROR")
            return

        if self.saveSanario is None:
            # print("❌ [ERROR] saveSanario is None")
            Settings.WRITE_LOG_DEV_FILE("saveSanario is None", "ERROR")
            return

        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            # print("❌ [ERROR] Session file not found")
            Settings.WRITE_LOG_DEV_FILE("Session file not found", "ERROR")
            return

        # print("📁 [OK] Session file exists")
        Settings.WRITE_LOG_DEV_FILE("Session file exists", "INFO")

        # 🔐 Vérification de session
        session_info = SessionManager.check_session()
        # print(f"🔐 [SESSION] Raw session info: {session_info}")
        Settings.WRITE_LOG_DEV_FILE(f"Raw session info: {session_info}", "INFO")

        if not session_info.get("valid"):
            # print("⛔ [SESSION] Invalid session. Redirecting to login.")
            Settings.WRITE_LOG_DEV_FILE("Session invalid. Redirecting to login.", "ERROR")
            sys.exit()
            return False

        # 🔑 Chiffrement
        encrypted_String = EncryptionService.encrypt_message( f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",  Settings.KEY)

        # print(f"🔐 [ENCRYPT] Encrypted string: {encrypted_String}")
        Settings.WRITE_LOG_DEV_FILE(f"Encrypted string: {encrypted_String}", "INFO")

        Api_Url = f"https://reporting.nrb-apps.com/pub/ReportingV4/senario.php?rv4=1&action=get&entity=IT&l={encrypted_String}"
        # print(f"🌐 [API] URL: {Api_Url}")

        try:
            # print("📡 [API] Sending request to load scenarios...")
            result = APIManager.load_scenarios(Api_Url)  # Peut retourner une liste ou un dict
            # print(f"📥 [API] Raw result: {result}")
            # Settings.WRITE_LOG_DEV_FILE(f"[API RESULT] {result}", "DEBUG")

            # 🔹 Si c'est un dict et contient status=False → erreur
            if isinstance(result, dict) and result.get("status") is False:
                # print(f"❌ [API ERROR] {result.get('error', 'Unknown error')}")
                Settings.WRITE_LOG_DEV_FILE(f"API returned error: {result.get('error', 'Unknown error')}", "ERROR")

                # Ajouter None directement à la combobox
                self.saveSanario.clear()
                self.saveSanario.addItem("None")
                return # Ne pas continuer l'ajout de scénarios

            # 🔹 Si c'est une liste → traitement direct
            scenarios = result if isinstance(result, list) else []
            # print(f"ℹ️ [API] Nombre de scénarios: {len(scenarios)}")
            Settings.WRITE_LOG_DEV_FILE(f"Number of scenarios loaded: {len(scenarios)}", "INFO")

            # Mettre à jour la combobox
            self.saveSanario.clear()
            self.saveSanario.addItem("None")

            if scenarios:
                for index, scenario in enumerate(scenarios, 1):
                    name = scenario.get("name", f"Scénario {index}")
                    # print(f"➕ [ADD] Scenario {index}: {name}")
                    Settings.WRITE_LOG_DEV_FILE(f"Adding scenario {index}: {name}", "INFO")
                    self.saveSanario.addItem(name)
            else:
                # print("⚠️ [API] No scenarios found, added 'None' only")
                Settings.WRITE_LOG_DEV_FILE("No scenarios found, added 'None' only", "INFO")

            # print("✅ [LOAD_SCENARIOS] Combobox updated successfully")
            Settings.WRITE_LOG_DEV_FILE("Combobox updated successfully", "INFO")

        except Exception as e:
            # print(f"🔥 [EXCEPTION] Error while loading scenarios: {e}")
            Settings.WRITE_LOG_DEV_FILE( f"An error occurred while loading scenarios: {str(e)}\n{traceback.format_exc()}",  "CRITICAL")

    def Copy_Logs_To_Clipboard(self):
        UIManager.Copy_Logs_To_Clipboard(self)

    def logOut(self):
        global SELECTED_BROWSER_GLOBAL
        try:
            SessionManager.clear_session()

            if SELECTED_BROWSER_GLOBAL:
                Stop_All_Processes(self)

            self.login_window = LoginWindow()
            self.login_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()
            self.close()

        except Exception as e:
            # log_message(f"[LOGOUT ERROR] {e}")
            Settings.WRITE_LOG_DEV_FILE( f"An error occurred while logging out: {str(e)}\n{traceback.format_exc()}", "ERROR" )

    def Update_Logs_Display(self, log_entry):
        UIManager.Update_Logs_Display(log_entry, self.log_text_edit)

    def Extraction_Finished(self, window):
        self.LOGS_THREAD.stop()
        self.LOGS_THREAD.wait()
        # print("🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​Extraction Finished ​")
        Settings.WRITE_LOG_DEV_FILE("Extraction Finished", "INFO")
        QTimer.singleShot( 100, lambda: UIManager.Read_Result_Update_List(window, NOTIFICATION_BADGES) )

    def verify_required_paths(self):
        Settings.WRITE_LOG_DEV_FILE("Starting required path verification", "INFO")

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

            detail_msg = (
                f"Path check: {normalized_path} | expected={path_type} | exists={exists} "
                f"| type_ok={type_ok}"
            )
            # print(detail_msg)
            Settings.WRITE_LOG_DEV_FILE(detail_msg, "INFO")

            valid = ValidationUtils.validate_path(path, must_exist=True, is_file=is_file)

            if not valid:
                reason = "missing" if not exists else ("wrong type" if not type_ok else "unknown")

                # print(f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}")
                Settings.WRITE_LOG_DEV_FILE(f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}", "ERROR")
                invalid_paths.append(f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}")

        if invalid_paths:
            Settings.WRITE_LOG_DEV_FILE( f"Required path verification failed: {len(invalid_paths)} invalid path(s)", "ERROR"  )
        else:
            Settings.WRITE_LOG_DEV_FILE("All required paths are valid", "SUCCESS")

        return len(invalid_paths) == 0, invalid_paths

    def Submit_Button_Clicked(self, window):
        global LOGS_RUNNING, NOTIFICATION_BADGES

        UIManager.disable_button(self.submitButton)

        # Vérification de session
        session_info = SessionManager.check_session()
        if not session_info["valid"]:
            self.login_window = LoginWindow()
            self.login_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

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
                # print(f"[ERREUR NETTOYAGE SESSION] ❌ {e}")
                Settings.WRITE_LOG_DEV_FILE(  f"An error occurred while cleaning the session: {str(e)}\n{traceback.format_exc()}", "ERROR")
            UIManager.enable_button(self.submitButton)
            return

        auth_result = SessionManager.check_api_credentials( session_info.get("username"), session_info.get("password"))
        if isinstance(auth_result, int):
            messages = {
                -1: "Invalid credentials. Please login again.",
                -2: "This device is not authorized.",
                -3: "Unable to connect to the server.",
                -4: "Access denied for this application.",
                -5: "Unknown authentication error.",
            }

            self.erreur_label.setText(messages.get(auth_result, "Authentication failed."))
            self.erreur_label.show()

            # Settings.WRITE_LOG_DEV_FILE(
            #     f"Authentication failed (code {auth_result}): {msg}",
            #     "ERROR"
            # )
            UIManager.enable_button(self.submitButton)
            return
        else:
            Settings.WRITE_LOG_DEV_FILE("Authentication successful", "INFO")

        is_valid, errors = self.verify_required_paths()

        if is_valid:
            # print("Tous les chemins sont valides.")
            Settings.WRITE_LOG_DEV_FILE("All required paths are valid.", "INFO")
        else:
            # print("Erreur avec les chemins.")
            Settings.WRITE_LOG_DEV_FILE("Error with required paths.", "ERROR")

            # 🔹 Construire message détaillé
            error_details = "\n".join(errors)

            UIManager.Show_Critical_Message(
                window,
                "Invalid Paths",
                f"The following paths are invalid:\n\n{error_details}",
                message_type="critical",
            )

            UIManager.enable_button(self.submitButton)
            return

        try:
            # print("🔄 [BADGES] Début suppression des badges existants")
            Settings.WRITE_LOG_DEV_FILE("Start badge cleanup", "INFO")
            if self.result_tab_widget:
                # print( f"📌 [BADGES] Nombre de tabs dans result_tab_widget = {self.result_tab_widget.count()}"  )
                Settings.WRITE_LOG_DEV_FILE( f"Number of tabs in result_tab_widget = {self.result_tab_widget.count()}",  "INFO" )

                # Supprimer badges existants
                for tab_index, badge in NOTIFICATION_BADGES.items():
                    if badge:
                        # print(f"🗑️ [BADGES] Suppression badge tab_index={tab_index}")
                        Settings.WRITE_LOG_DEV_FILE(f"Badge removed tab_index={tab_index}", "INFO")
                        badge.deleteLater()
                NOTIFICATION_BADGES.clear()
                # print("✅ [BADGES] Tous les badges existants supprimés et dictionnaire vidé")
                Settings.WRITE_LOG_DEV_FILE( "All existing badges removed and dictionary cleared", "INFO" )

                # Vider tous les QListWidget dans les tabs
                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        # print(f"📂 [TAB {i}] Nombre de QListWidget = {len(list_widgets)}")
                        for lw_index, lw in enumerate(list_widgets):
                            lw.clear()
                            # print(f"🧹 [TAB {i}][LIST {lw_index}] Liste vidée")

            else:
                # print("⚠️ [BADGES] result_tab_widget est None")
                Settings.WRITE_LOG_DEV_FILE("result_tab_widget is None", "WARNING")

        except Exception as e:
            # print(f"❌ [BADGES ERROR] Erreur pendant la suppression des badges: {type(e).__name__} : {e}")
            Settings.WRITE_LOG_DEV_FILE(  f"An error occurred while removing badges: {str(e)}\n{traceback.format_exc()}", "ERROR" )
            UIManager.enable_button(self.submitButton)
            return

        # 🔹 Vérification complète des mises à jour du programme
        try:
            # Appel de la fonction check_and_update
            update_ok = UpdateManager.check_and_update(self)
            # print(f"🔄 [UPDATE] Update check result: {update_ok}")
            Settings.WRITE_LOG_DEV_FILE(f"Update check result: {update_ok}", "INFO")

            if not update_ok:
                # S'il y a une erreur ou si la mise à jour a échoué → arrêter le traitement immédiatement
                # print("❌ Update failed or application not up-to-date, exiting process.")
                UIManager.enable_button(self.submitButton)
                Settings.WRITE_LOG_DEV_FILE( "Update failed or application not up-to-date, exiting process.", "ERROR"  )

                return

        except SystemExit:
            Settings.WRITE_LOG_DEV_FILE("Application update triggered, exiting for update.", "INFO")
            UIManager.enable_button(self.submitButton)
            # Si la fonction check_and_update a fait sys.exit (update programme)
            return

        except Exception as e:
            # Tous les autres erreurs critiques
            # print(f"[UPDATE ERROR] {e}")
            Settings.WRITE_LOG_DEV_FILE(  f"An error occurred while checking for updates: {str(e)}\n{traceback.format_exc()}",  "ERROR" )
            UIManager.enable_button(self.submitButton)
            return

        selected_Browser = self.browser.currentText()

        # check sur browser if exist selected_Browser

        if selected_Browser:
            if not BrowserManager.validate_and_setup_browser(self, selected_Browser):
                Settings.WRITE_LOG_DEV_FILE(f"Browser not processed: {selected_Browser}", "WARNING")
                UIManager.enable_button(self.submitButton)
                return
        QApplication.processEvents()  

        browser_path = (
            BrowserManager.get_browser_path("chrome.exe")
            if selected_Browser.lower() == "chrome"
            else (
                BrowserManager.get_browser_path("firefox")
                if selected_Browser.lower() == "firefox"
                else (
                    BrowserManager.get_browser_path("msedge.exe")
                    if selected_Browser.lower() == "edge"
                    else BrowserManager.get_browser_path("dragon.exe")
                )
            )
        )

        if browser_path is None:
            Settings.WRITE_LOG_DEV_FILE( f"Unable to find path for browser: {selected_Browser}", "ERROR"  )
            UIManager.Show_Critical_Message( window, "Browser Not Found",  f"Unable to find the path for the selected browser: {selected_Browser}.\n\nPlease ensure the browser is installed and try again.", message_type="critical" )
            UIManager.enable_button(self.submitButton)
            return

        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                if UIManager.Is_Result_Tab(self.INTERFACE, i):
                    UIManager.Reset_Result_Tab_Label(self.INTERFACE, i)
        LOGS_RUNNING = True

        if self.scenario_layout.count() == 0:

            UIManager.Show_Critical_Message(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning",
            )
            UIManager.enable_button(self.submitButton)

            Settings.WRITE_LOG_DEV_FILE( "No actions have been added. Please add actions before submitting.", "WARNING")
            return

        try:
            result = ValidationUtils.generate_user_input_data(window)

            # =======================
            # 🔴 Check result structure
            # =======================
            if not isinstance(result, dict):
                Settings.WRITE_LOG_DEV_FILE(  "Invalid result format returned from ValidationUtils.generate_user_input_data", "ERROR" )
                UIManager.enable_button(self.submitButton)
                return

            if not result.get("valid"):

                # 🔹 Affichage dans la console pour debug
                # print(f"❌ [DATA ERROR] {result.get('error', 'Unknown error')}")

                title, detail_text = (
                    result.get("error", "Unknown error").split(":", 1)
                    if ":" in result.get("error", "Unknown error")
                    else (
                        result.get("error", "Unknown error"),
                        result.get("error", "Unknown error"),
                    )
                )

                # print(f" Title: {title.strip()}")
                # print(f" Detail: {detail_text.strip()}")
                Settings.WRITE_LOG_DEV_FILE(f"Data error: {result.get('error', 'Unknown error')}", "ERROR")
                Settings.WRITE_LOG_DEV_FILE(f"Title: {title.strip()} | Detail: {detail_text.strip()}", "ERROR")

                # 🔹 Log complet pour le développeur
                Settings.WRITE_LOG_DEV_FILE( f"Generate_User_Input_Data failed: {result.get('error', 'Unknown error')}", "ERROR"  )

                # 🔹 Affichage QMessageBox pro pour l'utilisateur
                UIManager.Show_Critical_Message(
                    window,
                    title.strip(),
                    detail_text.strip(),
                    message_type="warning",
                )

                UIManager.enable_button(self.submitButton)
                return
            # =======================
            # 🟢 Extract data safely
            # =======================
            data_list = result.get("data") or []
            entered_number = result.get("entered_number")

            # Protection supplémentaire
            if not isinstance(data_list, list):
                Settings.WRITE_LOG_DEV_FILE("Data list is not a list", "ERROR")
                UIManager.enable_button(self.submitButton)
                return

            # =======================
            # 📊 Enregistrement
            # =======================
            Settings.WRITE_LOG_DEV_FILE(  f"User input processed successfully | Records: {len(data_list)} | Entered number: {entered_number}","INFO")

            # =======================
            # 👉 Continuer le traitement ici
            # =======================
            # Exemple:
            # process_final_data(data_list)

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Processing error: {e}\n{traceback.format_exc()}", "ERROR")

            UIManager.Show_Critical_Message(
                window,
                "Unexpected Error",
                "Something went wrong while processing your request.\n\nPlease try again or contact support.",
                message_type="critical",
            )

            UIManager.enable_button(self.submitButton)
            return

        # current_time = datetime.datetime.now()
        # CURRENT_DATE = current_time.strftime("%Y-%m-%d")
        # CURRENT_HOUR = current_time.strftime("%H-%M-%S")
        # print("✅ Current date and hour set:", CURRENT_DATE, CURRENT_HOUR)
        # Settings.WRITE_LOG_DEV_FILE(f"Current date and hour set: {CURRENT_DATE} {CURRENT_HOUR}", "INFO")

        # print("📦 JSON Final:")
        Settings.WRITE_LOG_DEV_FILE("Final JSON:", "INFO")
        result_json = JsonManager.generate(self.scenario_layout, selected_Browser)
        # print(json.dumps(result_json, indent=2, ensure_ascii=False))
        # print( "✅ Final JSON generated. Data:", json.dumps(result_json, indent=2, ensure_ascii=False) )
        Settings.WRITE_LOG_DEV_FILE(  f"Final JSON generated. Data: {json.dumps(result_json, indent=2, ensure_ascii=False)}",  "INFO" )
        Settings.WRITE_LOG_DEV_FILE("The final JSON has been generated.", "INFO")
        QApplication.processEvents()  # Traite les événements UI en attente pour garder l'interface réactive

        if not result_json or result_json == []:
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                "No valid actions could be generated or an error occurred while saving the configuration file.\n\n"
                "If the problem persists, contact Support.",
                message_type="critical",
            )
            Settings.WRITE_LOG_DEV_FILE( "No valid actions could be generated or an error occurred while saving the configuration file.",  "ERROR" )
            UIManager.enable_button(self.submitButton)

            return

        try:
            save_status = JsonManager.save_json_to_file(result_json, selected_Browser)

            if save_status == "ERROR":
                UIManager.Show_Critical_Message(
                    window,
                    "Error - Save Configuration",
                    "An error occurred while saving the configuration file.\n\n"
                    "If the problem persists, contact Support.",
                    message_type="critical",
                )
                Settings.WRITE_LOG_DEV_FILE(  "An error occurred while saving the configuration file.", "ERROR"  )
                UIManager.enable_button(self.submitButton)
                return
            # else:
            #     print("✅ JSON file saved with status:", save_status)

        except Exception as e:
            # print(f"❌ Erreur lors de la sauvegarde du JSON: {e}")
            Settings.WRITE_LOG_DEV_FILE( f"An error occurred while saving the configuration file: {e} \n{traceback.format_exc()}", "ERROR")
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                f"An error occurred while saving the configuration file:\n\n{e}",
                message_type="critical",
            )
            UIManager.enable_button(self.submitButton)
            return
        QApplication.processEvents()  # Traite les événements UI après sauvegarde du JSON

        try:
            with open(Settings.FILE_ISP, "w", encoding="utf-8") as f:
                f.write(self.Isp.currentText().strip())
        except Exception as e:
            UIManager.enable_button(self.submitButton)

            # print("❌ Error writing to Isp.txt:", e)
            # print(f"❌ Erreur lors de l'écriture dans Isp.txt : {e}")
            Settings.WRITE_LOG_DEV_FILE(  f"Error writing to Isp.txt: {e}\n{traceback.format_exc()}", "ERROR" )
        QApplication.processEvents()  # Traite les événements UI après écriture du fichier ISP

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

        unique_id = self.Save_Process(parameters)

        if unique_id == -1:
            # print("❌ Error getting process ID")
            # print("❌ Error getting process ID")
            UIManager.Show_Critical_Message(
                window,
                "Error - Process Save",
                "Failed to save the process in the database.\n\n"
                "Please check your connection and try again.",
                message_type="critical",
            )
            Settings.WRITE_LOG_DEV_FILE("Failed to save the process in the database.", "ERROR")
            UIManager.enable_button(self.submitButton)

            return
        # print("✅ Obtained Process ID:", unique_id)
        # print(f"✅ Process ID obtenu: {unique_id}")
        QApplication.processEvents()  # Traite les événements UI après sauvegarde du processus

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(  Start_Extraction,  window,  data_list,  entered_number, selected_Browser,   self.Isp.currentText(),  unique_id,  result_json,  session_info["username"] )
            executor.submit(self.LOGS_THREAD.start)
        EXTRACTION_THREAD.finished.connect(lambda: self.Extraction_Finished(window))
        QApplication.processEvents()  # Traite les événements UI après lancement de l'extraction

    def Load_Initial_Options(self):
        while self.reset_options_layout.count() > 0:
            item = self.reset_options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for key, state in self.states.items():
            if state.get("showOnInit", False):
                self.Create_Option_Button(state)

    def Create_Option_Button(self, state):
        default_icon_path = os.path.join(Settings.ICONS_DIR, "icon.png")
        default_icon_path_Templete2 = os.path.join(Settings.ICONS_DIR, "next.png")
        is_multi = state.get("isMultiSelect", False)

        if is_multi:
            template_button = self.Temeplete_Button_2
            icon_path = default_icon_path_Templete2
        else:
            template_button = self.template_button
            icon_path = default_icon_path

        button = QPushButton(state.get("label", "Unnamed"), self.reset_options_container)
        button.setStyleSheet(template_button.styleSheet())
        button.setFixedSize(template_button.size())

        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        button.clicked.connect(lambda _, s=state: self.Load_State(s))

        if ValidationUtils.path_exists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            # print(f"[Warning] Icon not found at: {icon_path}")
            Settings.WRITE_LOG_DEV_FILE(f"[Warning] Icon not found at: {icon_path}", "WARNING")

        self.reset_options_layout.addWidget(button)

    def Load_State(self, state):
        UIManager.Display_State_Stack_As_Table(self)
        is_multi = state.get("isMultiSelect", False)
        if not is_multi:
            self.STATE_STACK.append(state)

        UIManager.Display_State_Stack_As_Table(self)

        if not is_multi:
            template = state.get("Template", "")
            UIManager.Update_Scenario(self, template, state)

        actions = state.get("actions", [])
        self.Update_Reset_Options(actions)
        self.Update_Actions_Color_Handle_Last_Button()

        UIManager.Remove_Copier(self.scenario_layout, self.reset_options_layout)
        UIManager.Remove_Initaile(self.scenario_layout, self.reset_options_layout)

        UIManager.Display_State_Stack_As_Table(self)

    def Update_Actions_Color_Handle_Last_Button(self):
        UIManager.Update_Actions_Color_Handle_Last_Button(  self.scenario_layout, self.Go_To_Previous_State )

    def Update_Reset_Options(self, actions):
        count = self.reset_options_layout.count()
        for i in reversed(range(count)):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not actions:
            self.Load_Initial_Options()
            return

        for action_key in actions:
            state = self.states.get(action_key)
            if state:
                label = state.get("label", action_key)
                self.Create_Option_Button(state)

    def Go_To_Previous_State(self):
        UIManager.Display_State_Stack_As_Table(self)
        if len(self.STATE_STACK) > 1:

            if self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(self.scenario_layout.count() - 1)
                if last_item.widget():
                    last_item.widget().deleteLater()

            self.STATE_STACK.pop()
            previous_state = self.STATE_STACK[-1]

            self.Update_Reset_Options(previous_state.get("actions", []))
        else:
            self.STATE_STACK.clear()

            while self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(0)
                if last_item.widget():
                    last_item.widget().deleteLater()

            self.Load_Initial_Options()

        self.Update_Actions_Color_Handle_Last_Button()

        UIManager.Remove_Copier(self.scenario_layout, self.reset_options_layout)
        UIManager.Display_State_Stack_As_Table(self)

    def Clear_Button_Clicked(self):
        self.log_text_edit.clear()  # Effacer tout le texte
        global LOGS
        LOGS = []

    def Scenario_Changed(self, name_selected):
        # print("\n" + "="*80)
        # print(f"🔹 Scenario_Changed called with name_selected={name_selected}")
        # print("="*80 + "\n")

        # 🔐 Check session
        session_info = SessionManager.check_session()
        # print(f"🔐 [SESSION] Raw session info: {session_info}")

        if not session_info.get("valid"):
            # print("⛔ [SESSION] Invalid session. Redirecting to login.")
            Settings.WRITE_LOG_DEV_FILE("Session invalid. Redirecting to login.", "ERROR")
            sys.exit()
            return False

        # 🔑 Encrypt session string
        encrypted_string = EncryptionService.encrypt_message( f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT", Settings.KEY )
        # print(f"🔐 [ENCRYPT] Encrypted string: {encrypted_string}")

        # 🔗 Build API URL
        api_url = f"https://reporting.nrb-apps.com/pub/ReportingV4/senario.php?rv4=1&action=get&entity=IT&l={encrypted_string}"
        # print(f"🌐 [API] URL: {api_url}")

        payload = {"name": name_selected}

        # 🟢 Call API
        try:
            raw_result = APIManager.handle_save_scenario(payload, api_url)
            # print(f"🟦 [RAW RESULT] {raw_result}")
        except Exception as e:
            # print(f"❌ API call failed: {e}")
            Settings.WRITE_LOG_DEV_FILE( f"API call failed: {e} \n {traceback.format_exc()}", "ERROR"  )
            return

        # 🔹 Case 3: API returns error dict
        if isinstance(raw_result, dict) and raw_result.get("status") is False:
            Settings.WRITE_LOG_DEV_FILE( f"API returned error: {raw_result.get('error', 'Unknown API error')}",  "ERROR" )
            return

        # 🔹 Case 1 & 2: API returns list (data) or empty list
        if isinstance(raw_result, list):
            if not raw_result:  # empty list -> case 2
                # print("⚠️ No scenario returned from API.")
                Settings.WRITE_LOG_DEV_FILE("No scenario returned from API.", "WARNING")
                # self.STATE_STACK = []  # clear state stack
                return
            else:  # list with data -> case 1
                scenario = raw_result[0]  # take first scenario
        elif isinstance(raw_result, dict) and "data" in raw_result:
            data_list = raw_result["data"]
            if not data_list:
                # print("⚠️ No scenario returned in 'data'.")
                Settings.WRITE_LOG_DEV_FILE("No scenario returned in 'data'.", "WARNING")
                # self.STATE_STACK = []
                return
            scenario = data_list[0]
        else:
            # print(f"❌ Unexpected API result format: {type(raw_result)}")
            Settings.WRITE_LOG_DEV_FILE( f"Unexpected API result format: {type(raw_result)}", "ERROR" )
            return

        # 🧹 Clear previous widgets
        for i in reversed(range(self.scenario_layout.count())):
            item = self.scenario_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = ( widget.objectName() if widget.objectName() else widget.__class__.__name__ )
                    Settings.WRITE_LOG_DEV_FILE(f"🗑️ Removing widget: {widget_name}", "INFO")
                    widget.deleteLater()

        # 🔄 Process scenario's state_stack
        state_stack = scenario.get("state_stack", [])
        if isinstance(state_stack, str):
            try:
                state_stack = json.loads(state_stack)
                # print(f"✅ state_stack loaded from string; length={len(state_stack)}")
            except Exception as e:
                # print(f"❌ Failed to parse state_stack: {e}")
                Settings.WRITE_LOG_DEV_FILE( f"Failed to parse state_stack: {e}\n{traceback.format_exc()}", "WARNING" )
                return

        self.STATE_STACK = state_stack
        Settings.WRITE_LOG_DEV_FILE(  f"📥 Scenario loaded with {len(self.STATE_STACK)} states.", "INFO" )

        # Deep copy to safely iterate
        state_stack_copy = copy.deepcopy(self.STATE_STACK)

        for index, state in enumerate(state_stack_copy, start=1):
            # print(f"\n[🧩] Processing state #{index}")
            try:
                pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
                # print(f"Preview state #{index} (first 200 chars): {pretty[:200]}...")
            except Exception:
                pretty = repr(state)

            try:
                t0 = time.time()
                self.Load_State(state)
                t1 = time.time()
                Settings.WRITE_LOG_DEV_FILE( f"✅ Load_State for #{index} succeeded in {t1 - t0:.3f}s", "INFO" )
                try:
                    self.Update_Actions_Color_Handle_Last_Button()
                except Exception as e:
                    # print(f"⚠️ Update_Actions_Color_Handle_Last_Button failed after state #{index}: {e}")
                    Settings.WRITE_LOG_DEV_FILE( f"⚠️ Update_Actions_Color_Handle_Last_Button failed after state #{index}: {e} \n {traceback.format_exc()}",  "WARNING")
            except Exception as e:
                # print(f"❌ Error during Load_State() for state #{index}: {e}")
                Settings.WRITE_LOG_DEV_FILE( f"❌ Error during Load_State() for state #{index}: {e}\n{traceback.format_exc()}",  "WARNING" )
                continue

        # Remove duplicates
        try:
            unique_states = []
            seen = set()
            for state in self.STATE_STACK:
                try:
                    state_key = json.dumps(state, sort_keys=True, ensure_ascii=False, default=str)
                except Exception:
                    state_key = repr(state)
                if state_key not in seen:
                    seen.add(state_key)
                    unique_states.append(state)
            self.STATE_STACK = unique_states
        except Exception as e:
            # print(f"⚠️ Failed to deduplicate STATE_STACK: {e}")
            Settings.WRITE_LOG_DEV_FILE( f"⚠️ Failed to deduplicate STATE_STACK: {e}\n{traceback.format_exc()}", "ERROR" )

        # print("\n🎉 Scenario loaded successfully.\n")




class EntitySelectionDialog(QDialog):

    def __init__(self, pattern=None, default_entity=None, parent=None):
        super().__init__(parent)
        # self.setObjectName("EntitySelectionDialog")
        self.setWindowTitle("Select Entity - AutoMailPro")
        self.setModal(True)
        self.setFixedSize(500, 320)
        self.setWindowIcon(QIcon(os.path.join(Settings.ICONS_DIR, "logo.jpg")))
        self.pattern = pattern  # Regex pattern for validation

        # Main layout with margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(12)

        # Title label
        title_label = QLabel("Entity Selection")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Instruction label
        instruction_label = QLabel("Please enter the entity you want to use for this session:")
        instruction_label.setStyleSheet("""
            font-size: 14px;
            color: #555;
            margin-bottom: 5px;
        """)
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        # Format info label
        if self.pattern:
            format_info = QLabel("Format: opm followed by digits (e.g., opm74, opm19)")
            format_info.setStyleSheet("""
                font-size: 12px;
                color: #859cb5;
                margin-bottom: 10px;
                font-style: italic;
            """)
            main_layout.addWidget(format_info)

        # LineEdit with styling
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter entity (opm + number)...")
        if default_entity:
            self.input_field.setText(default_entity)
        self.input_field.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
                min-width: 200px;
            }
            QLineEdit:hover {
                border-color: #0078d4;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
                outline: none;
            }
        """)
        main_layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            font-size: 12px;
            color: #d32f2f;
            margin-top: 8px;
            margin-bottom: 8px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(40)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        # Spacer
        main_layout.addSpacing(20)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #f3f2f1;
                border: 1px solid #ccc;
                border-radius: 5px;
                color: #333;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e1dfdd;
            }
            QPushButton:pressed {
                background-color: #c8c6c4;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # Confirm button
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #0078d4;
                border: none;
                border-radius: 5px;
                color: white;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.confirm_button.clicked.connect(self.validate_and_accept)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)

        main_layout.addLayout(button_layout)

        # Set overall dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f8f8;
            }
        """)

    def validate_and_accept(self):
        """Validate input against pattern and accept if valid."""
        import re

        entity_text = self.input_field.text().strip()

        if not entity_text:
            self.error_label.setText("Entity name cannot be empty.")
            self.error_label.show()
            return

        # Validate against pattern if provided
        if self.pattern:
            if not re.match(self.pattern, entity_text):
                self.error_label.setText( f"Invalid entity format. Expected format: opm followed by digits (e.g., opm74)" )
                self.error_label.show()
                return

        # Validation passed
        self.error_label.hide()
        self.accept()

    def get_selected_entity(self):
        """Returns the entered entity or None if canceled."""
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.input_field.text().strip()
        return None




class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui_path = self.Select_Ui_File()
        uic.loadUi(self.ui_path, self)
        if "Auth.ui" in self.ui_path:
            self.Initialize_Login_Ui()
            Settings.WRITE_LOG_DEV_FILE("Login UI initialized", "INFO")
        self.setWindowTitle("AutoMailPro")

    def Select_Ui_File(self) -> str:

        try:
            session_info = SessionManager.check_session()

            if session_info["valid"]:
                return Settings.INTERFACE_UI
        except Exception as e:
            # print(f"[SESSION ERROR] {e}")
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION ERROR] {e}\n{traceback.format_exc()}", "WARNING")
            sys.exit()

        return Settings.AUTH_UI

    def Initialize_Login_Ui(self):
        self.login_input = self.findChild(QLineEdit, "loginInput")
        self.password_input = self.findChild(QLineEdit, "passwordInput")
        self.login_button = self.findChild(QPushButton, "loginButton")
        self.title = self.findChild(QPushButton, "title")
        self.erreur_label = self.findChild(QLabel, "erreur")

        if self.erreur_label:
            Settings.WRITE_LOG_DEV_FILE( f"[INFO] Erreur label found: {self.erreur_label.text()}", "INFO"  )
            self.erreur_label.hide()

        if self.title:
            self.title.clicked.connect(self.Handle_Show_Session_Date)
            Settings.WRITE_LOG_DEV_FILE(f"[INFO] Title label found: {self.title.text()}", "INFO")
        if self.login_button:
            self.login_button.clicked.connect(self.Handle_Login)
            Settings.WRITE_LOG_DEV_FILE( f"[INFO] Login button found: {self.login_button.text()}", "INFO" )

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
            self.background_label.setStyleSheet("""
                border-top-left-radius: 30px;
                border-bottom-left-radius: 30px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                overflow: hidden;
            """)
            self.background_label.setScaledContents(True)
            self.background_label.lower()
            self.Update_Background_Image()

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
                    self.user_label.setGeometry(0, 0, self.UseFrame.width(), self.UseFrame.height())
                    self.user_label.show()

    def Update_Background_Image(self):
        if hasattr(self, "background_frame") and hasattr(self, "background_label"):
            pixmap = QPixmap(self.background_image_path)
            if not pixmap.isNull():
                self.background_label.resize(self.background_frame.size())
                self.background_label.setPixmap(pixmap)

    def Handle_Login(self):
        # print("🔹 Starting Handle_Login")
        UIManager.disable_button(self.login_button)
        # 1️⃣ Get input from UI
        username = ( self.login_input.text().strip()  if hasattr(self.login_input, "text")  else str(self.login_input).strip())
        password = ( self.password_input.text().strip()  if hasattr(self.password_input, "text")  else str(self.password_input).strip() )
        # print(f"📝 Inputs received: username='{username}', password='{'*' * len(password)}'")

        # 2️⃣ Validate username and password length
        if len(username) <= 4:

            # print(f"❌ Username must contain more than 4 characters.")
            Settings.WRITE_LOG_DEV_FILE(  f"❌ Username must contain more than 4 characters.", "WARNING")
            self.erreur_label.setText("Username must contain more than 4 characters.")
            self.erreur_label.show()
            return

        if len(password) <= 4:
            # print(f"❌ Password must contain more than 4 characters.")
            Settings.WRITE_LOG_DEV_FILE(  f"❌ Password must contain more than 4 characters.", "WARNING"  )
            self.erreur_label.setText("Password must contain more than 4 characters.")
            self.erreur_label.show()
            return

        # 3️⃣ Call check_api_credentials
        # print("📡 Calling check_api_credentials...")
        Settings.WRITE_LOG_DEV_FILE("Calling check_api_credentials...", "INFO")
        auth_result = SessionManager.check_api_credentials(username, password)
        # print(f"🔍 API result: {auth_result}")
        Settings.WRITE_LOG_DEV_FILE(f"API result: {auth_result}", "INFO")

        # 4️⃣ Handle API error codes
        # 4️⃣ Handle API error codes
        if isinstance(auth_result, int):
            UIManager.enable_button(self.login_button)

            messages = {
                -1: "Invalid credentials. Please try again.",
                -2: "This device is not authorized. Please contact support.",
                -3: "Unable to connect to the server. Please try again later.",
                -4: "Access to this application has been denied.",
                -5: "Unknown error occurred during authentication.",
            }

            error_message = messages.get(auth_result, "Unknown error occurred.")

            # print(f"❌ Error code: {auth_result} → {error_message}")
            Settings.WRITE_LOG_DEV_FILE( f"Authentication error code: {auth_result} → {error_message}", "WARNING" )

            self.erreur_label.setText(error_message)
            self.erreur_label.show()
            return


        # 5️⃣ Entity is already decrypted
        id_user, p_entity_Origine = auth_result
        # print(f"✅ Authentication successful: idUser={id_user}, entity={p_entity_Origine}")

        # Special case for 'rep.test' user: allow entity selection
        if username == "rep.test":
            # Entity validation pattern: "opm" followed by digits
            entity_pattern = r"^opm\d+$"

            dialog = EntitySelectionDialog(  pattern=entity_pattern, default_entity=p_entity_Origine, parent=self  )
            selected_entity = dialog.get_selected_entity()

            if selected_entity is None:
                # User canceled, abort login
                UIManager.enable_button(self.login_button)
                # print(f"Entity selection canceled. Login aborted.")
                Settings.WRITE_LOG_DEV_FILE("Entity selection canceled. Login aborted.", "WARNING")
                self.erreur_label.setText(  "Entity selection is required for this user. Login aborted."  )
                self.erreur_label.show()
                return

            p_entity_Nouveau = selected_entity
            # print(f"✅ Entity overridden to: {p_entity_Nouveau}")
            Settings.WRITE_LOG_DEV_FILE(f"✅ Entity overridden to: {p_entity_Nouveau}", "INFO")
        else:
            p_entity_Nouveau = p_entity_Origine

        # 6️⃣ Create user session
        # print("🛠️ Creating user session...")

        try:
            valid_session = SessionManager.create_session(  username, password, p_entity_Origine, p_entity_Nouveau, id_user  )
            if not valid_session:
                Settings.WRITE_LOG_DEV_FILE( "Failed to create user session for unknown reasons.", "ERROR" )
                self.erreur_label.setText("Failed to create user session.")
                self.erreur_label.show()
                return
            # print("✅ Session created successfully")
        except Exception as e:
            UIManager.enable_button(self.login_button)
            # print(f"❌ {msg}")
            Settings.WRITE_LOG_DEV_FILE( f"Exception during session creation: {str(e)}\n{traceback.format_exc()}", "ERROR"  )
            self.erreur_label.setText( f"Exception during session creation: {str(e)}\n{traceback.format_exc()}" )
            self.erreur_label.show()
            return

        # 7️⃣ Read JSON configuration file
        # print(f"📂 Reading configuration file: {Settings.FILE_ACTIONS_JSON}")
        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            if not json_data:
                Settings.WRITE_LOG_DEV_FILE("Configuration file is empty.", "ERROR")
                raise ValueError("Configuration file is empty.")
            # print("✅ JSON file loaded successfully")
        except Exception as e:
            UIManager.enable_button(self.login_button)
            Settings.WRITE_LOG_DEV_FILE(f"Configuration error: {str(e)}\n{traceback.format_exc()}", "ERROR" )
            # print(f"❌ {msg}")
            self.erreur_label.setText(f"Configuration error: {str(e)}\n{traceback.format_exc()}")
            self.erreur_label.show()
            return

        # 8️⃣ Initialize and show MainWindow
        # print("🖥️ Initializing main window...")
        UIManager.enable_button(self.login_button)  # Re-enable login button before opening main window
        self.main_window = MainWindow(json_data)
        self.main_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
        self.main_window.setWindowTitle("AutoMailPro")
        self.main_window.stopButton.clicked.connect(lambda: Stop_All_Processes(self.main_window))

        # Center the window
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.main_window.width()) // 2
        y = (screen_geometry.height() - self.main_window.height()) // 2
        self.main_window.move(x, y)

        # Show main window and close login
        self.main_window.show()
        self.close()
        Settings.WRITE_LOG_DEV_FILE("Main window displayed, login completed successfully.", "INFO")
        # print("✅ Main window displayed, login completed successfully")

    def Handle_Show_Session_Date(self):
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            Settings.WRITE_LOG_DEV_FILE("Session file not found at expected path.", "WARNING")
            self.erreur_label.setText("Session file not found .")
            self.erreur_label.show()
            return

        is_valid, session_data = ValidationUtils.validate_session_file(Settings.SESSION_PATH)

        if is_valid:
            Settings.WRITE_LOG_DEV_FILE(f"Session data retrieved: {session_data}", "INFO")
            self.erreur_label.setText(f"Session data: {session_data}")
        else:
            Settings.WRITE_LOG_DEV_FILE("Session file is not valid.", "WARNING")
            self.erreur_label.setText(f"Session file is not valid.")
        self.erreur_label.show()





def main():
    # print("\n========== [APP START] ==========\n")
    Settings.WRITE_LOG_DEV_FILE("\n\n========== [APP START] ==========\n", "INFO")
    Settings.WRITE_LOG_DEV_FILE("Application starting...", "INFO")
    # 1️⃣ Vérification des arguments
    # print(f"[DEBUG] Arguments reçus: {sys.argv}")
    Settings.WRITE_LOG_DEV_FILE(f"Received arguments: {sys.argv}", "DEBUG")
    # Settings.WRITE_LOG_DEV_FILE(f"Received arguments: {sys.argv}", "DEBUG")

    if len(sys.argv) < 3:
        Settings.WRITE_LOG_DEV_FILE(  "Insufficient arguments provided. Expected encrypted_key and secret_key.", "ERROR" )
        # print("[ERROR] Arguments insuffisants.")
        # print("Usage: python AppV2.py <encrypted_key> <secret_key>")
        Settings.WRITE_LOG_DEV_FILE(  "Usage: python AppV2.py <encrypted_key> <secret_key>", "ERROR" )
        sys.exit(1)

    encrypted_key = sys.argv[1]
    secret_key = sys.argv[2]

    # print(f"[DEBUG] encrypted_key: {encrypted_key}")
    # print(f"[DEBUG] secret_key: {secret_key}")
    Settings.WRITE_LOG_DEV_FILE(f"Encrypted key and secret key received.", "DEBUG")
    Settings.WRITE_LOG_DEV_FILE("Arguments parsed successfully.", "DEBUG")

    # 2️⃣ Vérification de la clé
    # print("[DEBUG] Vérification de la clé...")
    Settings.WRITE_LOG_DEV_FILE("Verifying key...", "DEBUG")
    if not EncryptionService.verify_key(encrypted_key, secret_key):
        # print("[ERROR] Clé invalide. Accès refusé.")
        Settings.WRITE_LOG_DEV_FILE("Invalid key. Access denied.", "ERROR")
        sys.exit(1)
    else:
        # print("[SUCCESS] Clé valide.")
        Settings.WRITE_LOG_DEV_FILE("Key is valid.", "INFO")

    # 3️⃣ Vérification session
    # print("[DEBUG] Vérification de la session...")
    Settings.WRITE_LOG_DEV_FILE("Checking user session...", "DEBUG")
    session_info = SessionManager.check_session_full()
    session_valid = session_info.get("valid", False)
    # Settings.WRITE_LOG_DEV_FILE(f"Session check result: valid={session_valid}, info={session_info}", "DEBUG")

    # print(f"[DEBUG] Session valid: {session_valid}")
    # print(f"[DEBUG] Session info: {session_info}")
    Settings.WRITE_LOG_DEV_FILE(f"Session valid: {session_valid}", "DEBUG")
    Settings.WRITE_LOG_DEV_FILE(f"Session info: {session_info}", "DEBUG")

    # 4️⃣ Initialisation app Qt
    app = QApplication(sys.argv)
    # print("[DEBUG] QApplication initialisée.")
    Settings.WRITE_LOG_DEV_FILE("QApplication initialized.", "DEBUG")

    # 5️⃣ Icône application
    icon_path = Path(Settings.APP_ICON)
    # print(f"[DEBUG] Chemin icône: {icon_path}")

    if ValidationUtils.path_exists(icon_path):
        app.setWindowIcon(QIcon(str(icon_path)))
        Settings.WRITE_LOG_DEV_FILE("Application icon set successfully.", "INFO")
        # print("[SUCCESS] Icône appliquée.")
    else:
        # print("[WARNING] Fichier d'icône introuvable.")
        Settings.WRITE_LOG_DEV_FILE(f"Icon file not found at: {icon_path}", "WARNING")

    # 6️⃣ Choix de la fenêtre
    window = None

    if session_valid:
        # print("[INFO] Session valide → tentative d'ouverture MainWindow")
        Settings.WRITE_LOG_DEV_FILE("Valid session found. Attempting to open MainWindow.", "INFO")
        try:
            # print(f"[DEBUG] Chargement fichier config: {Settings.FILE_ACTIONS_JSON}")
            Settings.WRITE_LOG_DEV_FILE(  f"Loading config file: {Settings.FILE_ACTIONS_JSON}", "DEBUG" )

            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            if not json_data:
                # print("[WARNING] Fichier JSON vide.")
                Settings.WRITE_LOG_DEV_FILE( f"Configuration file is empty: {Settings.FILE_ACTIONS_JSON}", "WARNING" )
                raise ValueError("Fichier de configuration vide")

            # print("[SUCCESS] Configuration chargée.")
            Settings.WRITE_LOG_DEV_FILE("Configuration file loaded successfully.", "INFO")

            window = MainWindow(json_data)
            # print("[SUCCESS] MainWindow initialisée.")
            Settings.WRITE_LOG_DEV_FILE("MainWindow initialized.", "INFO")

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE( f"An error occurred while loading MainWindow: {e}\n{traceback.format_exc()}",  "ERROR" )
            # print(f"[ERROR] Impossible de charger MainWindow: {e}")
            # print("[INFO] Fallback → LoginWindow")
            SessionManager.clear_session()  # Clear session if loading MainWindow fails
            window = LoginWindow()

    else:
        # print("[INFO] Session invalide → ouverture LoginWindow")
        Settings.WRITE_LOG_DEV_FILE("No valid session found. Opening LoginWindow.", "INFO")
        SessionManager.clear_session()  # Clear session if loading MainWindow fails
        window = LoginWindow()

    # 7️⃣ Vérification sécurité
    if window is None:
        # print("[CRITICAL] Aucune fenêtre créée !")
        Settings.WRITE_LOG_DEV_FILE("Critical error: No window could be created.", "CRITICAL")
        sys.exit(1)

    # 8️⃣ Taille et position
    # print("[DEBUG] Configuration taille et position fenêtre...")

    window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

    screen = QGuiApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()

    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2

    window.move(x, y)

    # print(f"[DEBUG] Position fenêtre: x={x}, y={y}")

    # 9️⃣ Connexion stop button
    if hasattr(window, "stopButton"):
        # print("[DEBUG] stopButton détecté → connexion")
        Settings.WRITE_LOG_DEV_FILE("stopButton detected in window. Attempting to connect.", "DEBUG")
        Settings.WRITE_LOG_DEV_FILE("stopButton found. Connecting to Stop_All_Processes.", "DEBUG")
        try:
            window.stopButton.clicked.connect(lambda: Stop_All_Processes(window))
            # print("[SUCCESS] stopButton connecté.")
            Settings.WRITE_LOG_DEV_FILE("stopButton connected successfully.", "INFO")
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE( f"An error occurred while connecting stopButton: {e}\n{traceback.format_exc()}", "ERROR"  )
            # print(f"[ERROR] Erreur connexion stopButton: {e}")
    else:
        # print("[INFO] Aucun stopButton trouvé.")
        Settings.WRITE_LOG_DEV_FILE("No stopButton found in window.", "INFO")

    # 🔟 Finalisation
    window.setWindowTitle("AutoMailPro")
    window.show()
    Settings.WRITE_LOG_DEV_FILE("Application started successfully, window displayed.", "INFO")

    # print("[SUCCESS] Fenêtre affichée.")
    # print("\n========== [APP RUNNING] ==========\n")
    Settings.WRITE_LOG_DEV_FILE("\n\n========== [APP RUNNING] ==========\n", "INFO")
    Settings.WRITE_LOG_DEV_FILE("Application is now running.", "INFO")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

