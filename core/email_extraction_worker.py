import datetime
import json
import os
import shutil
import subprocess
import time
import traceback
from collections import deque

from PyQt6.QtCore import QThread, pyqtSignal

from api import API_MANAGER
from config import Settings
from core import EncryptionService, SessionManager
from models import BrowserManager
from ui_utils import UIManager
from utils import ValidationUtils


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
        runtime_state,
        file_lock,
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
        self.Isp = Isp
        self.unique_id = unique_id
        self.output_json_final = output_json_final
        self.runtime_state = runtime_state
        self.file_lock = file_lock

    def _logMessage(self, text):
        self.runtime_state.logs.append(text)

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
        self.runtime_state.selected_browser = self.selected_Browser
        remaining_emails_queue = deque(self.data_list)
        self.runtime_state.remaining_emails = len(remaining_emails_queue)

        self._logMessage("[INFO] Processing started")
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
            extension_data_path = os.path.join(
                Settings.EXTENTION_EX3_FIREFOX
                if self.selected_Browser.lower() == "firefox"
                else Settings.EXTENTION_EX3_CHROMIUM,
                "data.txt",
            )
            os.makedirs(os.path.dirname(extension_data_path), exist_ok=True)

            with open(extension_data_path, "w", encoding="utf-8") as file:
                file.write(f"{self.session_id}\n")
            Settings.write_log_dev_file(
                f"Wrote session_id to extension data file: {extension_data_path}",
                "INFO",
            )

        except Exception as error:
            Settings.write_log_dev_file(
                f"Failed to write session_id to extension data file: {extension_data_path} | error={error}\n{traceback.format_exc()}",
                "ERROR",
            )

        while remaining_emails_queue or self.runtime_state.active_emails:
            if self.stop_flag:
                self.runtime_state.logs_running = False
                self._logMessage("[INFO] Processing interrupted by user.")
                Settings.write_log_dev_file("Processing interrupted by user.", "INFO")
                break

            if (
                len(self.runtime_state.active_emails) < self.entered_number
                and remaining_emails_queue
            ):
                next_email = remaining_emails_queue.popleft()
                self.runtime_state.remaining_emails = len(remaining_emails_queue)
                email_value = ValidationUtils.getValueFromDictionary(
                    next_email, ["email", "Email"]
                )
                self._logMessage(f"[INFO] Processing the email:  {email_value}")
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
                            os.path.join(Settings.LOGS_DIRECTORY, directory)
                            for directory in os.listdir(Settings.LOGS_DIRECTORY)
                            if os.path.isdir(
                                os.path.join(Settings.LOGS_DIRECTORY, directory)
                            )
                        ]
                        logs_subdirs.sort(key=os.path.getctime)

                        if len(logs_subdirs) > 4:
                            for directory_to_delete in logs_subdirs[:4]:
                                try:
                                    shutil.rmtree(directory_to_delete)
                                except Exception as error:
                                    Settings.write_log_dev_file(
                                        f"Error while deleting {directory_to_delete} : {error}\n{traceback.format_exc()}",
                                        "ERROR",
                                    )

                    except Exception as error:
                        Settings.write_log_dev_file(
                            f"Error accessing or creating log directory {Settings.LOGS_DIRECTORY} : {error}\n{traceback.format_exc()}",
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
                            self._logMessage(
                                f"[ERROR] Impossible de créer le profil Firefox pour {profile_email}"
                            )
                            continue

                        Settings.write_log_dev_file(
                            f"✅ [Firefox] Profil créé/vérifié: {firefox_profile_path}",
                            "INFO",
                        )
                        web_ext_path = Settings.get_web_ext_path()

                        if not web_ext_path:
                            Settings.write_log_dev_file(
                                "❌ [Firefox] web-ext non trouvé", "ERROR"
                            )
                            self._logMessage("[ERROR] web-ext introuvable")
                            continue

                        command = [
                            web_ext_path,
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
                        self.runtime_state.process_pids.append(process.pid)
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
                        self.runtime_state.firefox_sessions[profile_email] = (
                            firefox_session
                        )

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
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

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
                        self.runtime_state.process_pids.append(process.pid)
                        BrowserManager.persistBrowserSessionInfo(
                            process.pid,
                            profile_dir,
                            profile_email,
                            self.session_id,
                            self.selected_Browser,
                            inserted_id,
                            profile_path=os.path.join(profile_dir, profile_email),
                        )
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

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
                        self.runtime_state.process_pids.append(process.pid)
                        time.sleep(4)
                        process1 = subprocess.Popen(
                            command1,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        self.runtime_state.process_pids.append(process1.pid)
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
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

                    self.emails_processed += 1

                except Exception as error:
                    with self.file_lock:
                        self.runtime_state.active_emails.discard(profile_email)
                    Settings.write_log_dev_file(
                        f"Error processing email {profile_email}: {error}\n{traceback.format_exc()}",
                        "ERROR",
                    )
            self.msleep(1000)

        self.runtime_state.remaining_emails = 0
        self._logMessage("[INFO] Processing finished for all emails.")
        Settings.write_log_dev_file("Processing finished for all emails.", "INFO")
        UIManager.enableButton(self.window.submitButton)
        time.sleep(3)
        self.runtime_state.logs_running = False
        self.finished.emit()
