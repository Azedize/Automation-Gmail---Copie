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
    from core.browser_session_monitor import BrowserSessionMonitorThread
    from core.file_watcher import DownloadFileEventHandler
    from core.email_extraction_worker import EmailExtractionWorker
    from core.runtime_state import runtime_state
    from models import BrowserManager
    from api import API_MANAGER
    from utils import ValidationUtils
    from ui_utils import UIManager
    from ui_utils.authentication_window import AuthenticationWindow
    from ui_utils.automation_main_window import AutomationMainWindow
    from ui_utils.entity_selection_dialog import EntitySelectionDialog
    from ui_utils.log_display_thread import ApplicationLogDisplayThread
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
FIREFOX_SESSIONS: Dict[str, Any] = runtime_state.firefox_sessions
LOGS = runtime_state.logs
PROCESS_PIDS = runtime_state.process_pids
NOTIFICATION_BADGES = runtime_state.notification_badges
EXTRACTION_THREAD = None
CLOSE_BROWSER_THREAD = None
NEW_VERSION = None
ACTIVE_EMAILS = runtime_state.active_emails


SESSION_ID = ValidationUtils.generateSessionId()


def logMessage(text):
    global LOGS
    LOGS.append(text)


def stopAllProcesses(window, show_idle_warning=True):
    UIManager.disableButton(window.stopButton)
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD
    global PROCESS_PIDS, FIREFOX_SESSIONS, ACTIVE_EMAILS
    Settings.write_log_dev_file("Stopping all processes...", "INFO")
    runtime_state.logs_running = False

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

    if not runtime_state.selected_browser:
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
    browser_name = runtime_state.selected_browser.lower()

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
    browser_path_display = browser_path or "Non trouvÃ©"
    Settings.write_log_dev_file(
        f"Browser startup details | Browser selected: {browser_name} | Executable path: {browser_path_display} | Extraction stage: initialisation",
        "INFO",
    )

    if selected_Browser.lower() == "firefox":
        Settings.ensure_web_ext_installed()

    EXTRACTION_THREAD = EmailExtractionWorker( window,  data_list,  SESSION_ID,  entered_number,  browser_path, window,  selected_Browser, Isp, unique_id,  output_json_final, runtime_state,  file_lock )

    EXTRACTION_THREAD.finished.connect(lambda: window.extraction_finished(window))
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.stopped.connect(  lambda msg: UIManager.showCriticalMessage( window, "ArrÃªtÃ©", msg, message_type="warning" )   )
    EXTRACTION_THREAD.finished.connect(  lambda: UIManager.showCriticalMessage( window, "TerminÃ©", "L'extraction est terminÃ©e.", message_type="success" ) )
    EXTRACTION_THREAD.start()

    def launch_browser_session_monitor():
        global CLOSE_BROWSER_THREAD
        Settings.write_log_dev_file("Launching BrowserSessionMonitorThread...", "INFO")
        CLOSE_BROWSER_THREAD = BrowserSessionMonitorThread(
            selected_Browser, username, SESSION_ID, file_lock
        )
        CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
        CLOSE_BROWSER_THREAD.start()

    QTimer.singleShot(0, launch_browser_session_monitor)



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
            Settings.write_log_dev_file( f"Loading config file: {Settings.FILE_ACTIONS_JSON}", "DEBUG")
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            if not json_data:
                Settings.write_log_dev_file( f"Configuration file is empty: {Settings.FILE_ACTIONS_JSON}",  "WARNING" )
                raise ValueError("Fichier de configuration vide")

            Settings.write_log_dev_file(  "Configuration file loaded successfully.", "INFO"  )

            window = AutomationMainWindow(
                json_data, stopAllProcesses, startExtraction, runtime_state
            )
            Settings.write_log_dev_file("AutomationMainWindow initialized.", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(   f"An error occurred while loading AutomationMainWindow: {e}\n{traceback.format_exc()}","ERROR")
            SessionManager.clear_session()
            window = AuthenticationWindow(
                AutomationMainWindow,
                stopAllProcesses,
                startExtraction,
                runtime_state,
            )

    else:
        Settings.write_log_dev_file("No valid session found. Opening AuthenticationWindow.", "INFO" )
        SessionManager.clear_session()
        window = AuthenticationWindow(
            AutomationMainWindow,
            stopAllProcesses,
            startExtraction,
            runtime_state,
        )

    if window is None:
        Settings.write_log_dev_file( "Critical error: No window could be created.", "CRITICAL" )
        sys.exit(1)

    window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

    screen = QGuiApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()

    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2

    window.move(x, y)

    if hasattr(window, "stopButton"):
        Settings.write_log_dev_file( "stopButton detected in window. Attempting to connect.", "DEBUG" )
        Settings.write_log_dev_file(  "stopButton found. Connecting to stopAllProcesses.", "DEBUG" )
        try:
            window.stopButton.clicked.connect(lambda: stopAllProcesses(window))
            Settings.write_log_dev_file("stopButton connected successfully.", "INFO")
        except Exception as e:
            Settings.write_log_dev_file( f"An error occurred while connecting stopButton: {e}\n{traceback.format_exc()}", "ERROR" )
    else:
        Settings.write_log_dev_file("No stopButton found in window.", "INFO")

    window.setWindowTitle("AutoMailPro")
    window.show()
    Settings.write_log_dev_file( "Application started successfully, window displayed.", "INFO")
    Settings.write_log_dev_file("\n\n========== [APP RUNNING] ==========\n", "INFO")
    Settings.write_log_dev_file("Application is now running.", "INFO")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

