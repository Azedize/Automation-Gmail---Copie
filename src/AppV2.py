import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon , QCursor,QColor, QPixmap , QGuiApplication
from PyQt6.QtCore import Qt , QTimer , QThread, pyqtSignal 
from PyQt6 import  uic 
import shutil
import signal
import time
import subprocess
import re
import datetime
import requests
import sys
import urllib3
import psutil
from platformdirs import user_downloads_dir
import win32gui       
import win32process
import win32con
import copy
import warnings
from threading import Lock
from pathlib import Path

warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)



try:
    from config import settings as Settings
    from core import EncryptionService
    from core import SessionManager
    from models import BrowserManager
    from models import ExtensionManager
    from api import APIManager
    from utils import ValidationUtils
    from ui_utils import UIManager
    from services import JsonManager
    from Update import UpdateManager
except ImportError as e:
    print(f"[ERROR] Import modules failed: {e}")



file_lock = Lock()

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
FIREFOX_LAUNCH = []
LOGS= []
PROCESS_PIDS = []
NOTIFICATION_BADGES = {}
EXTRACTION_THREAD = None 
CLOSE_BROWSER_THREAD = None 
NEW_VERSION = None
LOGS_RUNNING = True  
SELECTED_BROWSER_GLOBAL=None













# Si ce n'est pas le cas, il tente de l'installer via Chocolatey (et installe aussi npm).
def ensure_node_installed():
    if shutil.which("node") is not None:
        # print("✅ Node.js est déjà installé.")
        Settings.WRITE_LOG_DEV_FILE("Node.js already installed", "INFO")
        return True

    # print("❌ Node.js n'est pas installé. Tentative d'installation via Chocolatey...")
    Settings.WRITE_LOG_DEV_FILE("Node.js not installed. Trying to install via Chocolatey...", "INFO")

    if shutil.which("choco") is None:
        # print("🔍 Chocolatey non trouvé. Installation...")
        Settings.WRITE_LOG_DEV_FILE("Chocolatey not found. Installing...", "INFO")
        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                    "[System.Net.ServicePointManager]::SecurityProtocol = "
                    "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                    "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
                ],
                check=True
            )
        except subprocess.CalledProcessError:
            return False

    try:
        subprocess.run(["choco", "install", "nodejs-lts", "-y"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False




# Cette fonction retourne le chemin de l'exécutable web-ext s'il est trouvé
def get_web_ext_path():
    path = shutil.which("web-ext")
    if path:
        return path
    else:
        return None




# 🔍📦 Vérifie si 'web-ext' est installé, sinon l'installe globalement via npm
def ensure_web_ext_installed():
    if not ensure_node_installed():
        # print("⚠️ Impossible de continuer sans Node.js.")
        Settings.WRITE_LOG_DEV_FILE("Unable to continue without Node.js.", "WARNING")
        return
    
    if shutil.which('npm') is None:
        # print("❌ npm n'est pas installé.")
        Settings.WRITE_LOG_DEV_FILE("npm is not installed.", "ERROR")
        return
    
    if shutil.which('web-ext') is not None:
        Settings.WRITE_LOG_DEV_FILE("web-ext already installed", "INFO")
        return
    
    try:
        subprocess.run('npm install --global web-ext', check=True, shell=True)
    except subprocess.CalledProcessError:
        Settings.WRITE_LOG_DEV_FILE("Error installing web-ext via npm", "ERROR")
        # print("❌ Échec de l'installation de 'web-ext' via npm.")






# 📝 Ajoute un message au journal global 'LOGS'
def log_message(text):
    global LOGS
    LOGS.append(text)






# 🧪 Exemple de génération d'un ID de session
SESSION_ID = ValidationUtils.generate_session_id()



def Stop_All_Processes(window):
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD, PROCESS_PIDS, LOGS_RUNNING, SELECTED_BROWSER_GLOBAL

    # print("Stopping all processes...")
    Settings.WRITE_LOG_DEV_FILE("Stopping all processes...", "INFO")
    LOGS_RUNNING = False

    if EXTRACTION_THREAD:
        # print("Stopping extraction thread...")
        Settings.WRITE_LOG_DEV_FILE("Stopping extraction thread...", "INFO")
        EXTRACTION_THREAD.stop_flag = True
        EXTRACTION_THREAD.wait()
        EXTRACTION_THREAD = None
        # print("Extraction thread stopped.")
        Settings.WRITE_LOG_DEV_FILE("Extraction thread stopped.", "INFO")


    if CLOSE_BROWSER_THREAD:
        # print("Stopping close Chrome thread...")
        Settings.WRITE_LOG_DEV_FILE("Stopping close Chrome thread...", "INFO")
        CLOSE_BROWSER_THREAD.stop_flag = True
        CLOSE_BROWSER_THREAD.wait()
        CLOSE_BROWSER_THREAD = None
        # print("Close Chrome thread stopped.")
        Settings.WRITE_LOG_DEV_FILE("Close Chrome thread stopped.", "INFO")

    if EXTRACTION_THREAD and EXTRACTION_THREAD.isRunning():
        # print("Waiting for extraction thread to finish before updating UI...")
        Settings.WRITE_LOG_DEV_FILE("Waiting for extraction thread to finish before updating UI...", "INFO")
        EXTRACTION_THREAD.finished.connect(
            lambda: QTimer.singleShot(100, 
            lambda: UIManager.Read_Result_Update_List(window,NOTIFICATION_BADGES))
        )

    if SELECTED_BROWSER_GLOBAL.lower() != "firefox":
        for pid in PROCESS_PIDS[:]:
            try:
                print(f"Attempting to terminate process with PID {pid}...")
                Settings.WRITE_LOG_DEV_FILE(f"Attempting to terminate process with PID {pid}...", "INFO")
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                # print(f"Process {pid} terminated successfully.")
                Settings.WRITE_LOG_DEV_FILE(f"Process {pid} terminated successfully.", "INFO")
            except psutil.NoSuchProcess:
                # print(f"The process with PID {pid} no longer exists.")
                Settings.WRITE_LOG_DEV_FILE(f"The process with PID {pid} no longer exists.", "INFO")
            except psutil.AccessDenied:
                # print(f"Permission denied to terminate the process with PID {pid}.")
                Settings.WRITE_LOG_DEV_FILE(f"Permission denied to terminate the process with PID {pid}.", "INFO")
            except Exception as e:
                print(f"An error occurred while terminating PID {pid}: {e}")
                Settings.WRITE_LOG_DEV_FILE(f"An error occurred while terminating PID {pid}: {e}", "ERROR")
            finally:
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")
                    Settings.WRITE_LOG_DEV_FILE(f"PID {pid} removed from process list.", "INFO")
    else:
            try:
                BrowserManager.Close_Windows_By_Profiles(FIREFOX_LAUNCH)
            except Exception as e:
                print(f"⚠️ Erreur lors de la fermeture des profils Firefox: {e}")
                Settings.WRITE_LOG_DEV_FILE(f"Error closing Firefox profiles: {e}", "WARNING")
 
            finally:
                for pid in PROCESS_PIDS[:]:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")
                    Settings.WRITE_LOG_DEV_FILE(f"PID {pid} removed from process list.", "INFO")








class CloseBrowserThread(QThread):

    progress = pyqtSignal(str)

    def __init__(self, selected_Browser, username):
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username = username
        self.session_id = SESSION_ID
        self.stop_flag = False
        self.downloads_folder = user_downloads_dir()

        print(f"🧩 [INIT] Thread créé | Browser={selected_Browser} | User={username}")
        Settings.WRITE_LOG_DEV_FILE(f"Thread created | Browser={selected_Browser} | User={username}", "INFO")

    # ======================================================
    # 🔁 THREAD PRINCIPAL
    # ======================================================
    def run(self):
        try:
            if os.path.exists(Settings.RESULT_FILE_PATH):
                print(f"🧹 [RESULT] Fichier existant trouvé: {Settings.RESULT_FILE_PATH}")
                Settings.WRITE_LOG_DEV_FILE(f"Existing file found: {Settings.RESULT_FILE_PATH}", "INFO")
                # On vide le fichier
                open(Settings.RESULT_FILE_PATH, "w", encoding="utf-8").close()
                print(f"✅ [RESULT] Contenu ancien supprimé avec succès")
                Settings.WRITE_LOG_DEV_FILE(f"Old content removed successfully", "INFO")
            else:
                print(f"⚠️ [RESULT] Fichier {Settings.RESULT_FILE_PATH} n'existe pas, création à venir à l'enregistrement")
                Settings.WRITE_LOG_DEV_FILE(f"File {Settings.RESULT_FILE_PATH} does not exist, creation to be made at recording", "WARNING")
        except Exception as e:
            print(f"❌ [RESULT] Erreur lors de la suppression du contenu ancien: {type(e).__name__} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Error removing old content: {type(e).__name__} : {e}", "ERROR")



        print("🚀 [THREAD] CloseBrowserThread démarré")
        Settings.WRITE_LOG_DEV_FILE("CloseBrowserThread started", "INFO")
        time.sleep(15)

        print(f"🧪 [THREAD] stop_flag initial = {self.stop_flag}")
        Settings.WRITE_LOG_DEV_FILE(f"Initial stop_flag value = {self.stop_flag}", "INFO")

        while not self.stop_flag and PROCESS_PIDS:
            print("🌀 [LOOP] Boucle principale en cours")
            print(f"🛑 [STATE] stop_flag = {self.stop_flag}")
            print(f"📌 [STATE] PROCESS_PIDS = {PROCESS_PIDS}")
            print(f"🔢 [STATE] PID restants = {len(PROCESS_PIDS)}")


            try:
                files = [
                    f for f in os.listdir(self.downloads_folder)
                    if f.startswith(self.session_id) and f.endswith(".txt")
                ]

                log_files = [
                    f for f in os.listdir(self.downloads_folder)
                    if f.startswith("log_") and f.endswith(".txt")
                ]

                print(f"📄 [SCAN] Sessions={len(files)} | Logs={len(log_files)}")

                with ThreadPoolExecutor(max_workers=4) as executor:
                    executor.map(
                        lambda f: self.process_log_file(f, self.downloads_folder),
                        log_files
                    )

                with ThreadPoolExecutor(max_workers=4) as executor:
                    executor.map(
                        lambda f: self.process_session_file(
                            f, self.downloads_folder, self.selected_Browser
                        ),
                        files
                    )

            except Exception as e:
                print(f"❌ [THREAD] Erreur boucle principale: {e}")
                Settings.WRITE_LOG_DEV_FILE(f"Error in main loop: {e}", "ERROR")

            time.sleep(2)

        print("🛑 [THREAD] CloseBrowserThread terminé")
        Settings.WRITE_LOG_DEV_FILE("CloseBrowserThread ended", "INFO")
    # ======================================================
    # 📄 TRAITEMENT DES LOGS
    # ======================================================
    def process_log_file(self, log_file, downloads_folder):
        print(f"📄 [LOG] Traitement du fichier {log_file}")
        Settings.WRITE_LOG_DEV_FILE(f"Processing log file {log_file}", "INFO")
        try:
            email = ValidationUtils.get_email_from_log_file(
                os.path.join(downloads_folder, log_file)
            )

            if not email:
                print(f"⚠️ [LOG] Email introuvable dans {log_file}")
                Settings.WRITE_LOG_DEV_FILE(f"Email not found in {log_file}", "WARNING")
                return

            print(f"📧 [LOG] Email détecté: {email}")
            Settings.WRITE_LOG_DEV_FILE(f"Email detected: {email}", "INFO")

            CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
            CURRENT_HOUR = datetime.datetime.now().strftime("%H")

            session_folder = f"{CURRENT_DATE}_{CURRENT_HOUR}"
            target_folder = Path(Settings.LOGS_DIRECTORY) / session_folder
            os.makedirs(target_folder, exist_ok=True)

            target_file = os.path.join(target_folder, f"{email}_{CURRENT_HOUR}.txt")
            print(f"📂 [LOG] Écriture dans {target_file}")
            Settings.WRITE_LOG_DEV_FILE(f"Writing to {target_file}", "INFO")

            with open(os.path.join(downloads_folder, log_file), "r", encoding="utf-8") as f:
                content = f.read()

            with open(target_file, "a", encoding="utf-8") as tf:
                tf.write(content + "\n")

            os.remove(os.path.join(downloads_folder, log_file))
            print(f"🗑️ [LOG] Fichier supprimé {log_file}")
            Settings.WRITE_LOG_DEV_FILE(f"File deleted {log_file}", "INFO")
        except Exception as e:
            print(f"❌ [LOG] Erreur {log_file}: {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Error {log_file}: {e}", "ERROR")
    # ======================================================
    # 📄 TRAITEMENT DES SESSIONS
    # ======================================================
    def process_session_file(self, file_name, downloads_folder, selected_Browser):
        profile_data_file = None 
        print(f"📄 [SESSION] Début analyse du fichier: {file_name}")
        Settings.WRITE_LOG_DEV_FILE(f"Starting analysis of file: {file_name}", "INFO")

        try:
            # -----------------------------
            # 🔹 Chemin complet du fichier
            # -----------------------------
            session_path = os.path.join(downloads_folder, file_name)
            print(f"📂 [PATH] Chemin complet du fichier: {session_path}")
            Settings.WRITE_LOG_DEV_FILE(f"Full path of file: {session_path}", "INFO")

            if not os.path.exists(session_path):
                print(f"⚠️ [SESSION] Fichier introuvable, arrêt traitement")
                Settings.WRITE_LOG_DEV_FILE(f"File not found, stopping processing", "WARNING")
                return

            # -----------------------------
            # 🔹 Lecture du contenu
            # -----------------------------
            with open(session_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                print(f"⚠️ [SESSION] Fichier vide, rien à traiter")
                Settings.WRITE_LOG_DEV_FILE(f"Empty file, nothing to process", "WARNING")
                return

            print(f"🧠 [SESSION] Contenu lu: {content}")
            Settings.WRITE_LOG_DEV_FILE(f"Content read: {content}", "INFO")

            # -----------------------------
            # 🔹 Regex selon navigateur
            # -----------------------------
            if selected_Browser.lower() == "chrome":
                print("🌐 [NAV] Chrome détecté → extraction SESSION_ID")
                Settings.WRITE_LOG_DEV_FILE("Chrome detected → SESSION_ID extraction", "INFO")
                match = re.search( r"session_id:(\w+)_email:([\w.@+-]+)_etat:(\w+)",  content, re.IGNORECASE)

            else:
                print(f"🌐 [NAV] {selected_Browser} détecté → Regex standard avec PID")
                Settings.WRITE_LOG_DEV_FILE(f"{selected_Browser} detected → standard regex with PID", "INFO")
                match = re.search(
                    r"session_id:(\w+)_PID:(\d+)_Email:([\w.@]+)_Status:(\w+)",
                    content
                )

            if not match:
                print("❌ [SESSION] Format invalide → suppression fichier")
                Settings.WRITE_LOG_DEV_FILE("Invalid format → file deleted", "ERROR")
                os.remove(session_path)  # optional
                return

            # -----------------------------
            # 🔹 Extraction des valeurs
            # -----------------------------
            if selected_Browser.lower() == "chrome":
                session_id = match.group(1)
                email = match.group(2)
                status = match.group(3)
                pid = None
                inserted_id = None

                # 🔹 Affichage des valeurs extraites directement depuis match
                print(f"🔹 [MATCH] Valeurs extraites depuis regex → SESSION_ID={session_id}, Email={email}")
                Settings.WRITE_LOG_DEV_FILE(f"Values extracted from regex → SESSION_ID={session_id}, Email={email}", "INFO")

                # Lecture des informations depuis data.txt du profile Chrome
                profile_data_file = os.path.join(Settings.CHROME_PROFILES, email, "data.txt")  # ou email/profile
                if os.path.exists(profile_data_file):
                    with open(profile_data_file, "r", encoding="utf-8") as f:
                        line = f.readline().strip()
                        parts = line.split(":")
                        if len(parts) >= 4:
                            pid = parts[0]
                            email = parts[1]
                            session_id_from_data = parts[2]
                            inserted_id = parts[3]
                            print(f"🟢 [DATA] Info récupérées depuis data.txt → PID={pid}, Email={email}, SESSION_ID={session_id_from_data}, inserted_id={inserted_id} , status={status}")
                            Settings.WRITE_LOG_DEV_FILE(f"Info retrieved from data.txt → PID={pid}, Email={email}, SESSION_ID={session_id_from_data}, inserted_id={inserted_id} , status={status}", "INFO")


            else:
                session_id, pid, email, status = match.groups()
                pid = int(pid)
                inserted_id = None
                print(f"🟢 [SESSION] Extractions → SESSION_ID={session_id}, PID={pid}, Email={email}, Status={status}")
                Settings.WRITE_LOG_DEV_FILE(f"Extractions → SESSION_ID={session_id}, PID={pid}, Email={email}, Status={status}", "INFO")

            # -----------------------------
            # 🔹 Enregistrement résultat
            # -----------------------------
            with open(Settings.RESULT_FILE_PATH, "a", encoding="utf-8") as rf:
                rf.write(f"{session_id}:{pid}:{email}:{status}\n")
            print(f"📝 [RESULT] Résultat enregistré dans {Settings.RESULT_FILE_PATH}")
            Settings.WRITE_LOG_DEV_FILE(f"Result saved in {Settings.RESULT_FILE_PATH}", "INFO")

            # -----------------------------
            # 🔹 Envoi status à l'API
            # -----------------------------
            print(f"📤 [API] Envoi status pour {email}...")
            Settings.WRITE_LOG_DEV_FILE(f"Sending status for {email}...", "INFO")
            Send_Status({
                "id": inserted_id,
                "login": self.username,
                "status": "OK" if status == "completed" else "NotOK",
                "error": "" if status == "completed" else status
            })
            print(f"✅ [API] Status envoyé avec succès pour {email}")
            Settings.WRITE_LOG_DEV_FILE(f"Status sent successfully for {email}", "INFO")

            # -----------------------------
            # 🔹 Fermeture navigateur Chrome
            # -----------------------------
            if pid:
                print(f"🧨 [PROC] Fermeture du navigateur PID={pid}")
                Settings.WRITE_LOG_DEV_FILE(f"Closing browser with PID={pid}", "INFO")
                self._close_browser_process(pid, email, selected_Browser)
            elif selected_Browser.lower() == "chrome":
                print("🖥️ [PROC] Chrome détecté → gestion fermeture spécifique si nécessaire")
                Settings.WRITE_LOG_DEV_FILE("Chrome detected → specific closing if necessary", "INFO")

            # -----------------------------
            # 🔹 Nettoyage fichiers
            # -----------------------------
            os.remove(session_path)
            print(f"🗑️ [CLEAN] Session supprimée: {session_path}")
            Settings.WRITE_LOG_DEV_FILE(f"Session deleted: {session_path}", "INFO")

            if profile_data_file and os.path.exists(profile_data_file):
                os.remove(profile_data_file)
                print(f"🗑️ [CLEAN] data.txt du profile supprimé: {profile_data_file}")
                Settings.WRITE_LOG_DEV_FILE(f"data.txt from profile deleted: {profile_data_file}", "INFO")

            print(f"🎉 [SESSION] Traitement terminé avec succès pour {email}\n")
            Settings.WRITE_LOG_DEV_FILE(f"Processing completed successfully for {email}", "INFO")

        except Exception as e:
            print(f"❌ [SESSION] Erreur inattendue pour {file_name}: {type(e).__name__} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Unexpected error for {file_name}: {type(e).__name__} : {e}", "ERROR")



    # ======================================================
    # 🌐 NAVIGATEURS
    # ======================================================
    def _get_profile_base_path(self, browser):
        print(f"🌐 [BROWSER] Résolution chemin pour {browser}")
        Settings.WRITE_LOG_DEV_FILE(f"Resolving path for {browser}", "INFO")
        b = browser.lower()
        if b == "firefox":
            return Settings.FIREFOX_PROFILES
        elif b in ["edge", "icedragon", "comodo"]:
            return Settings.FAMILY_CHROME_DIR_PROFILES
        return Settings.CHROME_PROFILES
    


    def _close_browser_process(self, pid, email, browser):
        try:
            pid = int(pid)
            # 🔹 تحقق واش PID موجود فعلياً
            if not psutil.pid_exists(pid):
                print(f"⚠️ [PROC] PID بالفعل تسد {pid}")
                Settings.WRITE_LOG_DEV_FILE(f"PID already exists: {pid}", "WARNING")
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                return

            print(f"🧨 [PROC] Fermeture {browser} | PID={pid} | {email}")

            if browser.lower() == "firefox":
                try:
                    hwnd = self.find_firefox_window(email)
                    self.wait_then_close(email)
                except Exception as e:
                    print(f"❌ [FIREFOX] Erreur fermeture fenêtre: {e}")

            else:  # Chrome ou autre navigateur basé sur Chromium
                try:
                    # 🔹 تسد العملية مباشرة
                    os.kill(pid, signal.SIGTERM)
                    # 🔹 تأكد بعد 2 ثواني واش العملية تسدات، وإلا force kill
                    time.sleep(2)
                    if psutil.pid_exists(pid):
                        p = psutil.Process(pid)
                        p.terminate()
                        p.wait(timeout=3)
                        print(f"🧨 [PROC] PID={pid} terminé de force")
                        Settings.WRITE_LOG_DEV_FILE(f"PID={pid} terminated force", "INFO")
                except Exception as e:
                    print(f"❌ [CHROME] Erreur fermeture PID={pid}: {e}")

            # 🔹 حدف PID من القائمة PROCESS_PIDS
            if pid in PROCESS_PIDS:
                PROCESS_PIDS.remove(pid)

            print(f"✅ [PROC] Process fermé PID={pid}")
            Settings.WRITE_LOG_DEV_FILE(f"Process closed PID={pid}", "INFO")

        except Exception as e:
            print(f"🔥 [PROC] Erreur inattendue PID={pid} | {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Unexpected error PID={pid} | {e}", "ERROR")

    # ======================================================
    # 🪟 FIREFOX
    # ======================================================
    def find_firefox_window(self, profile_email, timeout=30):
        print(f"🪟 [FIREFOX] Recherche fenêtre pour {profile_email}")
        Settings.WRITE_LOG_DEV_FILE(f"Searching window for {profile_email}", "INFO")
        entry = next((e for e in FIREFOX_LAUNCH if e["profile"] == profile_email), None)
        if not entry:
            Settings.WRITE_LOG_DEV_FILE(f"Firefox profile not found", "ERROR")
            raise ValueError("Profil Firefox introuvable")

        target_title = f"EXT:{profile_email}"
        start = time.time()

        while time.time() - start < timeout:
            def enum_proc(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        if win32gui.GetClassName(hwnd) == "MozillaWindowClass":
                            if target_title in win32gui.GetWindowText(hwnd):
                                entry["hwnd"] = hwnd
                                print("🎯 [FIREFOX] Fenêtre trouvée")
                                Settings.WRITE_LOG_DEV_FILE("Firefox window found", "INFO")
                                return False
                    except:
                        pass
                return True

            win32gui.EnumWindows(enum_proc, None)
            if entry.get("hwnd"):
                return entry["hwnd"]

            time.sleep(2)
        Settings.WRITE_LOG_DEV_FILE("Firefox window not found", "ERROR")
        raise TimeoutError("⏱️ Fenêtre Firefox introuvable")




    def wait_then_close(self, profile_email):
        print(f"❌ [FIREFOX] Fermeture fenêtre {profile_email}")
        Settings.WRITE_LOG_DEV_FILE(f"Closing window for {profile_email}", "INFO")
        entry = next((e for e in FIREFOX_LAUNCH if e["profile"] == profile_email), None)
        if entry and entry.get("hwnd"):
            self.close_window_by_hwnd(entry["hwnd"], entry["proc"])





    def close_confirmation_dialogs(self, pid):
        print("⚠️ [DIALOG] Recherche confirmation Firefox")
        Settings.WRITE_LOG_DEV_FILE("Searching Firefox confirmation dialog", "INFO")
        def enum_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, p = win32process.GetWindowThreadProcessId(hwnd)
                if p == pid and win32gui.GetClassName(hwnd) == "#32770":
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True

        win32gui.EnumWindows(enum_proc, None)




    def close_window_by_hwnd(self, hwnd, proc, wait_grace=2, wait_force=3):
        print("🪟 [WINDOW] Fermeture fenêtre principale")
        Settings.WRITE_LOG_DEV_FILE("Closing main window", "INFO")
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        time.sleep(wait_grace)

        if win32gui.IsWindow(hwnd):
            self.close_confirmation_dialogs(proc.pid)
            try:
                proc.terminate()
                proc.wait(timeout=wait_force)
                print("🧨 [WINDOW] Process terminé de force")
                Settings.WRITE_LOG_DEV_FILE("Process terminated force", "INFO")
            except:
                pass

    




# -----------------------------
# Génération complète de l'extension Chrome/Firefox
# -----------------------------
def Generate_User_Input_Data(window):
    # print("🟢 [START] Generate_User_Input_Data")

    # Récupération des données depuis l’UI
    # print("📝 Lecture des données depuis l'interface...")
    input_data = window.textEdit_3.toPlainText().strip()
    entered_number_text = window.textEdit_4.toPlainText().strip()
    # print(f"🔹 Données brutes:\n{input_data[:100]}{'...' if len(input_data) > 100 else ''}")
    # print(f"🔹 Numéro saisi: {entered_number_text}")
    Settings.WRITE_LOG_DEV_FILE(f"Raw data:\n{input_data[:100]}{'...' if len(input_data) > 100 else ''}", "INFO")
    Settings.WRITE_LOG_DEV_FILE(f"Entered number: {entered_number_text}", "INFO")

    # Appel de la logique de validation
    print("⚙️ Appel de process_user_input pour validation...")
    validation_result = ValidationUtils.process_user_input(
        input_data,
        entered_number_text
    )

    # En cas d’erreur → affichage UI
    if not validation_result["success"]:
        #print(f"❌ Validation échouée: {validation_result['error_title']} - {validation_result['error_message']}")
        Settings.WRITE_LOG_DEV_FILE(f"Validation failed: {validation_result['error_title']} - {validation_result['error_message']}", "ERROR")
        UIManager.Show_Critical_Message(
            window,
            validation_result["error_title"],
            validation_result["error_message"],
            message_type=validation_result.get("error_type", "critical")
        )
        # print("🟢 [END] Generate_User_Input_Data (Erreur)")
        return None

    # Succès → même retour que la fonction originale
    # print(f"✅ Validation réussie! Nombre de lignes valides: {len(validation_result['data_list'])}")
    # print("🟢 [END] Generate_User_Input_Data (Succès)")
    Settings.WRITE_LOG_DEV_FILE(f"Validation succeeded! Number of valid lines: {len(validation_result['data_list'])}", "INFO")
    return (
        validation_result["data_list"],
        validation_result["entered_number"]
    )

# le programme is runing dans une interface 




def Start_Extraction(window, data_list, entered_number , selected_Browser , Isp , unique_id , output_json_final , username):
    global EXTRACTION_THREAD , CLOSE_BROWSER_THREAD
    # print("Starting extraction process...")
    # print("🚀 Starting extraction process...")
    
    # ValidationUtils.ensure_path_exists(Path(Settings.LOGS_DIRECTORY))
    
    try:
        entered_number = int(entered_number)
    except ValueError:
        UIManager.Show_Critical_Message(
            window,
            "Input Error - Invalid Format",
            "Numeric value required. Please check your input and try again.",
            message_type="critical"
        )
        Settings.WRITE_LOG_DEV_FILE("Numeric value required. Please check your input and try again.", "ERROR")
        return

    email_count = len(data_list)
    if entered_number > email_count:
        UIManager.Show_Critical_Message(
            window,
            "Range Error - Exceeded Limit",
            f"Maximum allowed entries: {email_count}\n"
            f"Please enter a value between 1 and {email_count}.",
            message_type="critical"
        )
        Settings.WRITE_LOG_DEV_FILE(f"Maximum allowed entries: {email_count}\nPlease enter a value between 1 and {email_count}.", "ERROR")
        return
    # print("Selected entries:", entered_number)
    # print("✅ Selected entries:", entered_number)
    Settings.WRITE_LOG_DEV_FILE(f"Selected entries: {entered_number}", "INFO")
  
    browser_path = (
        BrowserManager.get_browser_path("chrome.exe") if selected_Browser.lower() == "chrome"
        else BrowserManager.get_browser_path("firefox") if selected_Browser.lower() == "firefox"
        else BrowserManager.get_browser_path("msedge.exe") if selected_Browser.lower() == "edge"
        else BrowserManager.get_browser_path("dragon.exe")  
    )
  
    # 	tanger 90053 TANGER MA
    

    # le programme is run dans une interface logique et capable 

           
    if selected_Browser.lower() == "firefox":
        ensure_web_ext_installed()

    # print("browser path   :",   browser_path    or "Non trouvé")
    # print("✅ browser path   :",   browser_path    or "Non trouvé")

    EXTRACTION_THREAD = ExtractionThread(
       window , data_list, SESSION_ID, entered_number, browser_path , window ,selected_Browser , Isp , unique_id , output_json_final
    )
    

    # EXTRACTION_THREAD.finished.connect(lambda: window.Extraction_Finished(window))
    
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.stopped.connect(lambda msg: QMessageBox.warning(window, "Arrêté", msg))
    EXTRACTION_THREAD.finished.connect(lambda: QMessageBox.information(window, "Terminé", "L'extraction est terminée."))

    EXTRACTION_THREAD.start()

    time.sleep(10)
    # print("Launching CloseBrowserThread...")
    Settings.WRITE_LOG_DEV_FILE("Launching CloseBrowserThread...", "INFO")
    CLOSE_BROWSER_THREAD = CloseBrowserThread( selected_Browser ,username)
    CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
    CLOSE_BROWSER_THREAD.start()





def Save_Email(params):
    return str(APIManager.save_email(params))






def Send_Status(params):
    return str(APIManager.send_status(params))






# Émet un signal log_signal à chaque nouvelle entrée de log.
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



def store_browser_session_info(pid: str, Path_DiR: str, email: str, SESSION_ID: str, browser: str, inserted_id):
    try:
        print(f"📌 [START] store_browser_session_info pour {email} sur {browser}")
        print(f"🧭 [INPUT] PID={pid} | SESSION_ID={SESSION_ID} | inserted_id={inserted_id}")
        print(f"📁 [INPUT] Path_DiR={Path_DiR}")


        # ================================
        # 🟢 CASE : CHROME
        # ================================
        if browser.lower() == "chrome":
            print("🌐 [CHROME] Navigateur Chrome détecté")
            Settings.WRITE_LOG_DEV_FILE("Chrome browser detected", "INFO")

            # 1️⃣ Écriture SESSION_ID dans EXTENTION_EX3/data.txt
            chrome_file = Path(Settings.EXTENTION_EX3) / "data.txt"
            print(f"🧹 [CHROME] Nettoyage du fichier: {chrome_file}")
            chrome_file.write_text("", encoding="utf-8")  # vider contenu ancien

            print(f"✍️ [CHROME] Écriture SESSION_ID={SESSION_ID} dans {chrome_file}")
            chrome_file.write_text(f"{SESSION_ID}\n", encoding="utf-8")

            # Vérification contenu écrit
            with open(chrome_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            print(f"📄 [CHROME] Contenu actuel de {chrome_file}:\n{content}")

            # 2️⃣ Écriture pid:email:SESSION_ID:inserted_id dans un autre fichier
            second_file = Path(Path_DiR) / email / "data.txt"
            second_file.parent.mkdir(parents=True, exist_ok=True)
            entry = f"{pid}:{email}:{SESSION_ID}:{inserted_id}"
            print(f"✍️ [CHROME] Écriture secondaire → {second_file}")
            print(f"📄 [CHROME] Contenu à écrire: {entry}")

            with open(second_file, "w", encoding="utf-8") as f:
                f.write(entry + "\n")

            # Vérification contenu écrit
            with open(second_file, "r", encoding="utf-8") as f:
                content2 = f.read().strip()
            print(f"📄 [CHROME] Contenu actuel de {second_file}:\n{content2}")

        # ================================
        # 🔵 CASE : AUTRES NAVIGATEURS
        # ================================
        else:
            print(f"🗂️ [OTHER] Navigateur non-Chrome détecté: {browser}")

            text_file = Path(Path_DiR) / email / "data.txt"
            text_file.parent.mkdir(parents=True, exist_ok=True)
            entry = f"{pid}:{email}:{SESSION_ID}:{inserted_id}"
            print(f"✍️ [OTHER] Écriture → {text_file}")
            print(f"📄 [OTHER] Contenu à écrire: {entry}")

            with open(text_file, "w", encoding="utf-8") as f:
                f.write(entry + "\n")

            # Vérification contenu écrit
            with open(text_file, "r", encoding="utf-8") as f:
                content_other = f.read().strip()
            print(f"📄 [OTHER] Contenu actuel de {text_file}:\n{content_other}")

        print("🎉 [SUCCESS] Données session enregistrées avec succès\n")
        Settings.WRITE_LOG_DEV_FILE("Session data stored successfully", "INFO")

    except Exception as e:
        Settings.WRITE_LOG_DEV_FILE(f"Error in store_browser_session_info: {e}", "ERROR")
        print(f"❌ [ERROR] {type(e).__name__} : {e}")







# Thread responsable du traitement de l'extraction des emails.
# Gère l'exécution des navigateurs avec les extensions, l'enregistrement des LOGS,
# et la gestion des processus.

class ExtractionThread(QThread):

    progress = pyqtSignal(str)  
    finished = pyqtSignal()  
    stopped = pyqtSignal(str)

    def __init__(self, window, data_list, SESSION_ID, entered_number, Browser_path, main_window ,selected_Browser,Isp , unique_id , output_json_final):  
        super().__init__()
        self.window = window
        self.data_list = data_list  
        self.session_id = SESSION_ID  
        self.entered_number = entered_number  
        self.Browser_path = Browser_path 
        self.stop_flag = False
        self.emails_processed = 0 
        self.selected_Browser = selected_Browser
        self.main_window = main_window 
        self.Isp=Isp
        self.unique_id=unique_id
        self.output_json_final = output_json_final

    def run(self):

        global PROCESS_PIDS, LOGS_RUNNING  ,SELECTED_BROWSER_GLOBAL 
        SELECTED_BROWSER_GLOBAL=self.selected_Browser
        remaining_emails = self.data_list[:]  
        log_message("[INFO] Processing started")

        session_info = SessionManager.check_session()

        if not session_info["valid"]:
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            Settings.WRITE_LOG_DEV_FILE("Invalid session. Please reconnect.", "ERROR")
            return
        

        if self.selected_Browser.lower() == "chrome":
            Settings.RESULTATS_EX = BrowserManager.Upload_EXTENSION_PROXY("default", Settings.CLES_RECHERCHE, Settings.RESULTATS)

        while remaining_emails or PROCESS_PIDS:

            if self.stop_flag:  
                LOGS_RUNNING=False 
                log_message("[INFO] Processing interrupted by user.")
                Settings.WRITE_LOG_DEV_FILE("Processing interrupted by user.", "INFO")
                break


            if len(PROCESS_PIDS) < self.entered_number and remaining_emails:
                next_email = remaining_emails.pop(0)  
                email_value = ValidationUtils.get_key_from_dict(next_email, ["email", "Email"])
                log_message(f"[INFO] Processing the email:  {email_value}")
                Settings.WRITE_LOG_DEV_FILE(f"Processing the email: {email_value}", "INFO")

                try:
                    profile_email = ValidationUtils.get_key_from_dict(next_email, ["email", "Email"])
                    profile_password = ValidationUtils.get_key_from_dict(next_email, ["password_email", "passwordEmail"])
                    ip_address =ValidationUtils.get_key_from_dict(next_email, ["ip_address", "ipAddress"])
                    port = ValidationUtils.get_key_from_dict(next_email, ["port"])
                    login = ValidationUtils.get_key_from_dict(next_email, ["login"])
                    password = ValidationUtils.get_key_from_dict(next_email, ["password"])
                    recovery_email = ValidationUtils.get_key_from_dict(next_email, ["recovery_email", "recoveryEmail"])
                    new_recovery_email = ValidationUtils.get_key_from_dict(next_email, ["new_recovery_email", "neWrecoveryEmail"])

                    params = {
                        'l': EncryptionService.encrypt_message(session_info["username"],Settings.KEY),
                        'login': session_info["username"],
                        'entity': session_info["p_entity"],
                        'isp': self.Isp,
                        'action': json.dumps(self.output_json_final),
                        'email': email_value,
                        'password': '',
                        'proxy_ip': ip_address+":"+port,
                        'proxy_login': f"{login};{password}" if login != session_info["username"] else "",
                        'email_recovery': '',
                        'line': '',
                        'app': "V4",
                        'e_pid':self.unique_id
                    }

                    inserted_id=Save_Email(params)
                    new_password = ValidationUtils.generate_secure_password(16)

                    # 🔹 Création du chemin du dossier de session
                    session_directory = Path(Settings.LOGS_DIRECTORY) / f"{CURRENT_DATE}_{CURRENT_HOUR}"

                    try:
                        # Crée le dossier seulement s'il n'existe pas déjà
                        if not session_directory.exists():
                            session_directory.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass

                    logs_subdirs = [os.path.join(Settings.LOGS_DIRECTORY, d) for d in os.listdir(Settings.LOGS_DIRECTORY) if os.path.isdir(os.path.join(Settings.LOGS_DIRECTORY, d))]
                    logs_subdirs.sort(key=os.path.getctime)

                    if len(logs_subdirs) > 4:
                        to_delete = logs_subdirs[:4]
                        for dir_to_delete in to_delete:
                            try:
                                shutil.rmtree(dir_to_delete)
                            except Exception as e:
                                # log_message(f"[INFO]  Error while deleting {dir_to_delete} : {e}")
                                Settings.WRITE_LOG_DEV_FILE(f"Error while deleting {dir_to_delete} : {e}", "ERROR")

                  
                    if self.selected_Browser.lower() == "firefox":

                        ExtensionManager.create_extension_for_email(
                            profile_email, profile_password,
                            f'"{ip_address}"', f'"{port}"',
                            f'"{login}"', f'"{password}"', f'{recovery_email}',
                            new_password, new_recovery_email, f'"{self.session_id}"' , self.selected_Browser 
                        )

                        BrowserManager.create_firefox_profile(profile_email)


                        eb_ext_path = get_web_ext_path()

                        command = [
                            eb_ext_path,
                            "run",
                            "--source-dir", os.path.join(Settings.FOLDER_EXTENTIONS_FIREFOX, profile_email),
                            "--firefox-profile", os.path.join(Settings.FIREFOX_PROFILES, profile_email),
                            "--keep-profile-changes",  
                            "--no-reload"
                        ]
                        process = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 
                        
                        ts   = time.time()
                        FIREFOX_LAUNCH.append({
                            'profile': profile_email,
                            'create_time': ts,
                            'proc': process,
                            'hwnd': None
                        })

                        store_browser_session_info(process.pid , Settings.EXTENTIONS_DIR_FIREFOX , profile_email  , self.session_id , self.selected_Browser.lower() , inserted_id)

                    elif self.selected_Browser in ["edge", "icedragon", "Comodo"]:

                        ExtensionManager.create_extension_for_email(
                            profile_email, profile_password,
                            f'"{ip_address}"', f'"{port}"',
                            f'"{login}"', f'"{password}"', f'{recovery_email}',
                            new_password, new_recovery_email, f'"{self.session_id}"' , self.selected_Browser 
                        )

                        command = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(Settings.FAMILY_CHROME_DIR_PROFILES, profile_email)}",
                            f"--disable-extensions-except={os.path.join(Settings.FOLDER_EXTENTIONS_FAMILY_CHROME, profile_email)}",
                            f"--load-extension={os.path.join(Settings.FOLDER_EXTENTIONS_FAMILY_CHROME, profile_email)}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync"
                        ]
                        
                        process = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 

                        store_browser_session_info(process.pid , Settings.FOLDER_EXTENTIONS_FAMILY_CHROME, profile_email  ,self.session_id , self.selected_Browser.lower() , inserted_id)
                    
                    else:
                        # Définir la variable 'combined' ici pour qu'elle soit accessible partout
                        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email}"
                        
                        ValidationUtils.ensure_path_exists(Settings.CHROME_PROFILES, is_file=False)

                        

                        if not ValidationUtils.path_exists(os.path.join(Settings.CHROME_PROFILES,profile_email)):

                            BrowserManager.Run_Browser_Create_Profile(profile_email)

                            if not  Settings.RESULTATS_EX:
                                UIManager.Show_Critical_Message(self.window ,  "An issue occurred while copying the JSON file to the template profile  ➡ Please contact support." , message_type="critical")
                                self.stopped.emit("An issue occurred while copying the JSON file to the template profile  ➡ Please contact support.")  
                                self.stop_flag = True  
                                Settings.WRITE_LOG_DEV_FILE("An issue occurred while copying the JSON file to the template profile  ➡ Please contact support.", "ERROR") 
                                return                   
                            else:
                                BrowserManager.Updated_Secure_Preferences(profile_email, Settings.RESULTATS_EX)

                            time.sleep(1)
                            
                            b64 = EncryptionService.encrypt_aes_gcm("A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined)
                            url =f"https://example.com/?rep={b64}"
                        
                            command = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f'--profile-directory={profile_email}',
                                '--lang=En-US',
                                '--no-first-run',
                            ]

                            time.sleep(1)
                            command1 = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f'--profile-directory={profile_email}',
                                f'{url}',
                                '--lang=En-US',
                                '--no-first-run',
                            ]
                            process = subprocess.Popen(command) 
                            time.sleep(4)
                            process1 = subprocess.Popen(command1)
                            PROCESS_PIDS.append(process.pid)  
                            # print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)
                            # print(f"🚀 PID de processus : {process.pid}")
                            # print(f"🚀 PID de processus 1 : {process1.pid}")
                        else:
                            b64 = EncryptionService.encrypt_aes_gcm("A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined)
                            url =f"https://example.com/?rep={b64}"
                            command = [
                                BrowserManager.get_browser_path("chrome.exe"),
                                f"--user-data-dir={os.path.join(Settings.CHROME_PROFILES, profile_email)}",
                                f'--profile-directory={profile_email}',
                                f'{url}',
                                '--lang=En-US',
                                '--no-first-run',
                            ]
                            process = subprocess.Popen(command) 
                            PROCESS_PIDS.append(process.pid)

                        store_browser_session_info(process.pid , Settings.CHROME_PROFILES , profile_email  , self.session_id , self.selected_Browser.lower(),inserted_id)

                    self.emails_processed += 1  

                except Exception as e:
                    print(f"[INFO] Erreur : {e}")
                    Settings.WRITE_LOG_DEV_FILE(f"Error processing email {profile_email}: {e}", "ERROR")
                    
            self.msleep(1000) 

        log_message("[INFO] Processing finished for all emails.") 
        Settings.WRITE_LOG_DEV_FILE("Processing finished for all emails.", "INFO")
        time.sleep(3)
        LOGS_RUNNING=False
        self.finished.emit()










def Process_Browser(window, selected_Browser) -> bool:
    # print(f"\n🌐 Démarrage du traitement du navigateur : {selected_Browser}")
    
    # 1️⃣ Vérification du navigateur
    if selected_Browser.lower() != "chrome":
        # print(f"❌ Navigateur non supporté : {selected_Browser}")
        Settings.WRITE_LOG_DEV_FILE(f"Unsupported browser: {selected_Browser}", "WARNING")
        return False
    # print("✅ Navigateur : Chrome supporté")

    # 2️⃣ Vérification du dossier de configuration
    config_profile = Settings.CONFIG_PROFILE
    if not os.path.exists(config_profile):
        Settings.WRITE_LOG_DEV_FILE(f"Configuration folder not found: {config_profile}", "WARNING")
        # print(f"❌ Dossier de configuration introuvable : {config_profile}")
        return False
    # print(f"✅ Dossier de configuration trouvé : {config_profile}")

    # 3️⃣ Vérification du fichier secure_preferences
    secure_prefs = Settings.SECURE_PREFERENCES_TEMPLATE
    if not os.path.exists(secure_prefs):
        Settings.WRITE_LOG_DEV_FILE(f"Secure preferences file not found: {secure_prefs}", "WARNING")
        # print(f"❌ Fichier sécurisé introuvable : {secure_prefs}")
        return False

    # Lecture du fichier JSON
    try:
        with open(secure_prefs, "r", encoding="utf-8") as f:
            data = json.load(f)
        Settings.WRITE_LOG_DEV_FILE(f"Secure preferences file loaded successfully: {secure_prefs}", "INFO")
        # print("✅ Fichier JSON chargé avec succès")
    except Exception as e:
        # print(f"❌ Erreur lecture fichier JSON : {e}")
        return False

    # 4️⃣ Vérification des clés JSON
    required_keys = Settings.CLES_RECHERCHE
    results_keys = []
    BrowserManager.Search_Keys(data, required_keys, results_keys)

    found_keys = [list(d.keys())[0] for d in results_keys]
    missing_keys = [key for key in required_keys if key not in found_keys]

    if missing_keys:
        Settings.WRITE_LOG_DEV_FILE(f"Missing keys in JSON file !!", "WARNING")
        # print("❌ Clés manquantes :")
        # for idx, key in enumerate(missing_keys, start=1):
        #     print(f"   {idx}. {key}")
        return False
    # print(f"✅ Toutes les clés JSON requises sont présentes ({len(found_keys)}/{len(required_keys)})")

    # 5️⃣ Vérification et mise à jour de l'extension
    ext_path = Settings.EXTENTION_EX3
    if not ValidationUtils.path_exists(ext_path):
        # print("📥 Extension manquante, téléchargement...")
        Settings.WRITE_LOG_DEV_FILE(f"Extension not found, downloading...", "INFO")
        valid_ext_dir= ValidationUtils.validate_directory_path(ext_path, must_exist=False)
        if not valid_ext_dir:
            # print(f"❌ Chemin extension invalide : ")
            Settings.WRITE_LOG_DEV_FILE(f"Invalid extension path: {ext_path}", "WARNING")
            return False
        if UpdateManager.update_extension_from_server():
            print("✅ Extension installée avec succès")
            Settings.WRITE_LOG_DEV_FILE(f"Extension installed successfully", "INFO")
        else:
            Settings.WRITE_LOG_DEV_FILE(f"Failed to install extension", "WARNING")
            # print("❌ Échec installation extension")
            return False
    else:
        # print(f"📂 Extension trouvée : {ext_path}")
        manifest_file = os.path.join(ext_path, "manifest.json")
        if not os.path.exists(manifest_file):
            # print("❌ manifest.json manquant")
            Settings.WRITE_LOG_DEV_FILE(f"manifest.json not found", "WARNING")
            return False
        
        remote_version = UpdateManager.check_version_extension(window)
        if isinstance(remote_version, str):
            # print(f"🔄 Mise à jour disponible : {remote_version}")
            Settings.WRITE_LOG_DEV_FILE(f"Update available: {remote_version}", "INFO")
            if UpdateManager.update_extension_from_server(remote_version):
                print("✅ Extension mise à jour avec succès")
                Settings.WRITE_LOG_DEV_FILE(f"Extension updated successfully", "INFO")
            else:
                # print("❌ Échec mise à jour extension")
                Settings.WRITE_LOG_DEV_FILE(f"Failed to update extension", "WARNING")
                return False
        elif remote_version is True:
            print("✅ Extension déjà à jour")
        else:
            Settings.WRITE_LOG_DEV_FILE(f"Failed to check extension version", "WARNING")
            # print("❌ Impossible de vérifier la version de l'extension")
            return False



    # ✅ Tout est OK
    # print("🎉 Traitement terminé avec succès pour le navigateur Chrome")
    Settings.WRITE_LOG_DEV_FILE(f"Processing completed successfully for Chrome browser", "INFO")
    return True






class MainWindow(QMainWindow):

    
    def __init__(self, json_data):
        super(MainWindow, self).__init__()
        self._init_ui()
        self._init_data(json_data)
        self._setup_ui_components()
        self._load_initial_state()

    
    
    def _init_ui(self):
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
        return widget
    

    
    
    def _setup_containers(self):
        UIManager._setup_containers(self)




    def _setup_template_widgets(self):
        UIManager._setup_template_widgets(self)



    def _setup_buttons(self):
        self.Button_Initaile_state = self._setup_button(
            "Button_Initaile_state", self.Load_Initial_Options
        )
        
        # Submit button
        self.submit_button = self._setup_button(
            "submitButton", lambda: self.Submit_Button_Clicked(self)
        )
        
        # Clear button with icon
        self.ClearButton = self._setup_icon_button(
            "ClearButton", "clear.png", self.Clear_Button_Clicked,
            icon_size=(32, 32), button_size=(36, 36)
        )
        
        # Copy button with icon
        self.CopyButton = self._setup_icon_button(
            "CopyButton", "copyLog.png", self.Copy_Logs_To_Clipboard,
            icon_size=(26, 26), button_size=(38, 38)
        )
        
        # Save button with icon
        self.SaveButton = self._setup_icon_button(
            "saveButton", "save.png", self.Handle_Save,
            icon_size=(16, 16)
        )
        
        # Logout button
        self.log_out_Button = UIManager._setup_logout_button(self, self.logOut)





    def _setup_icon_button(self, button_name, icon_file, callback, icon_size=None, button_size=None):
        UIManager._setup_icon_button(self, button_name, icon_file, callback, icon_size, button_size)





    def _setup_button(self, widget_name, callback):
        UIManager._setup_button(self, widget_name, callback)



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
            # Créer un layout vertical
            self.log_layout = QVBoxLayout(self.log_container)
            self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Ajuster la taille du container
            self.log_container.adjustSize()
            self.log_container.setFixedWidth(1627)

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
        if not self.STATE_STACK:
            UIManager.Show_Critical_Message(self, "No Data", "No actions to save. Please add actions before saving.", message_type="critical")
            Settings.WRITE_LOG_DEV_FILE("No actions to save. Please add actions before saving.", "ERROR")
            return

        # 2️⃣ Check if the session file exists
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            UIManager.Show_Critical_Message(self, "Session Not Found", "[❌] Your session file is missing. Please restart the application.", message_type="critical")
            Settings.WRITE_LOG_DEV_FILE("Your session file is missing. Please restart the application.", "ERROR")
            return

        # 3️⃣ Read the encrypted session key
        with open(Settings.SESSION_PATH, "r", encoding="utf-8") as f:
            encrypted_key = f.read().strip()

        # 4️⃣ Prepare the payload
        if encrypted_key == "":
            UIManager.Show_Critical_Message(self, "Invalid Session", "[❌] Your session file is invalid. Please restart the application.", message_type="critical")
            Settings.WRITE_LOG_DEV_FILE("Your session file is invalid. Please restart the application.", "ERROR")
            return
        # else :
        #     print("Encrypted key read successfully.")


        payload = {
            # ⚠️ Ton PHP attend "encrypted", pas "decrypted_key"
            "encrypted": encrypted_key,
            "state": self.STATE_STACK[-1],
            "state_stack": self.STATE_STACK
        }

        # print(f"Payload: {payload}")

        try:
            result = APIManager.handle_save_scenario(payload)
            if result.get("session") is False:
                UIManager.Show_Critical_Message(self, "Session Expired", "[❌] Your session has expired. Please log in again.", message_type="critical")
                Settings.WRITE_LOG_DEV_FILE("Your session has expired. Please log in again.", "ERROR")
                self.login_window = LoginWindow()
                self.login_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - self.login_window.width()) // 2
                y = (screen_geometry.height() - self.login_window.height()) // 2
                self.login_window.move(x, y)
                self.login_window.show()

                self.close()
                return

            if result.get("success"):
                UIManager.Show_Critical_Message(self, "Success", "The scenario has been saved successfully.", message_type="success")
                Settings.WRITE_LOG_DEV_FILE("The scenario has been saved successfully.", "INFO")
            else:
                UIManager.Show_Critical_Message(self, "API Error", "An error occurred while saving the scenario.", message_type="critical")
                Settings.WRITE_LOG_DEV_FILE("An error occurred while saving the scenario.", "ERROR")


        except Exception as e:
            UIManager.Show_Critical_Message(self, "Error", "An error occurred while saving the scenario.", message_type="critical")
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while saving the scenario: {str(e)}", "ERROR")





    def Load_Scenarios_Into_Combobox(self):
        if self.saveSanario is None:
            # print("self.saveSanario is None")
            Settings.WRITE_LOG_DEV_FILE("self.saveSanario is None", "ERROR")
            return
        # else:
        #     print("self.saveSanario is not None")
    
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            return

        encrypted_key =UIManager.read_file_content(Settings.SESSION_PATH)

        if not encrypted_key:
            return

        # payload = {"encrypted": encrypted_key}
        try:

            result = APIManager.load_scenarios(encrypted_key)

            if result.get("session") is False:
                self.login_window = LoginWindow()
                self.login_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)

                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - self.login_window.width()) // 2
                y = (screen_geometry.height() - self.login_window.height()) // 2
                self.login_window.move(x, y)
                self.login_window.show()

                self.close()
                return

            scenarios = result.get("scenarios", [])
            if scenarios:
                self.saveSanario.clear()
                self.saveSanario.addItem("None")

                for index, scenario in enumerate(scenarios, 1):
                    name = scenario.get("name", f"Scénario {index}")
                    self.saveSanario.addItem(name)
            else:
                self.saveSanario.addItem("None")

        except Exception as e:
            # log_message(f"[❌] Erreur lors de la récupération des scénarios: {e}")
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while loading scenarios: {str(e)}", "ERROR")







            


    def Copy_Logs_To_Clipboard(self):
        UIManager.Copy_Logs_To_Clipboard(self)





    def logOut(self  ):
        global SELECTED_BROWSER_GLOBAL;
        try:
            SessionManager.clear_session()

            if(SELECTED_BROWSER_GLOBAL):
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
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while logging out: {str(e)}", "ERROR")


    def Update_Logs_Display(self, log_entry):
        UIManager.Update_Logs_Display( log_entry, self.log_layout)





    def Extraction_Finished(self, window):
        self.LOGS_THREAD.stop()  
        self.LOGS_THREAD.wait()  
        print("🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​🎶​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​📗​Extraction Finished ​")
        Settings.WRITE_LOG_DEV_FILE("Extraction Finished", "INFO")
        QTimer.singleShot(100, lambda: UIManager.Read_Result_Update_List(window,NOTIFICATION_BADGES))




    
    def Submit_Button_Clicked(self, window):
        global CURRENT_HOUR, CURRENT_DATE, LOGS_RUNNING, NOTIFICATION_BADGES  

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
                Settings.WRITE_LOG_DEV_FILE(f"An error occurred while cleaning the session: {str(e)}", "ERROR")

            return





        # Nettoyage des badges de notification
        try:
            print("🔄 [BADGES] Début suppression des badges existants")
            Settings.WRITE_LOG_DEV_FILE("Start badge cleanup", "INFO")
            if self.result_tab_widget:
                print(f"📌 [BADGES] Nombre de tabs dans result_tab_widget = {self.result_tab_widget.count()}")
                Settings.WRITE_LOG_DEV_FILE(f"Number of tabs in result_tab_widget = {self.result_tab_widget.count()}", "INFO")
                
                # Supprimer badges existants
                for tab_index, badge in NOTIFICATION_BADGES.items():
                    if badge:
                        print(f"🗑️ [BADGES] Suppression badge tab_index={tab_index}")
                        Settings.WRITE_LOG_DEV_FILE(f"Badge removed tab_index={tab_index}", "INFO")
                        badge.deleteLater()
                NOTIFICATION_BADGES.clear()
                print("✅ [BADGES] Tous les badges existants supprimés et dictionnaire vidé")
                Settings.WRITE_LOG_DEV_FILE("All existing badges removed and dictionary cleared", "INFO")

                # Vider tous les QListWidget dans les tabs
                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        print(f"📂 [TAB {i}] Nombre de QListWidget = {len(list_widgets)}")
                        for lw_index, lw in enumerate(list_widgets):
                            lw.clear()
                            print(f"🧹 [TAB {i}][LIST {lw_index}] Liste vidée")

            else:
                print("⚠️ [BADGES] result_tab_widget est None")
                Settings.WRITE_LOG_DEV_FILE("result_tab_widget is None", "WARNING")

        except Exception as e:
            print(f"❌ [BADGES ERROR] Erreur pendant la suppression des badges: {type(e).__name__} : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while removing badges: {str(e)}", "ERROR")





        # For PROGRAMM COMPLETE UPDATE
        try:
            UpdateManager.check_and_update(self)

        except SystemExit:
            return
        except Exception as e:
            print(f"[UPDATE ERROR] {e}")
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while checking for updates: {str(e)}", "ERROR")


        selected_Browser = self.browser.currentText()

        if  selected_Browser and selected_Browser.lower() == "chrome":
            if not Process_Browser(window, selected_Browser):
                # print("❌ Navigateur non traité :", selected_Browser)
                Settings.WRITE_LOG_DEV_FILE(f"Browser not processed: {selected_Browser}", "WARNING")
                return

        # print("🌐 Navigateur traité avec succès :", selected_Browser)

        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                tab_text = self.INTERFACE.tabText(i)
                if tab_text.startswith("Result"):
                    self.INTERFACE.setTabText(i, "Result")
                    break
        
        LOGS_RUNNING = True

      
        if self.scenario_layout.count() == 0:
            UIManager.Show_Critical_Message(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning"
            )
            Settings.WRITE_LOG_DEV_FILE("No actions have been added. Please add actions before submitting.", "WARNING")
            return

        try:
            result = Generate_User_Input_Data(window)

            if not result:  
                return
            data_list, entered_number = result  
            # print("✅ User input data generated successfully. Data list:", data_list, "Entered number:", entered_number)

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error while parsing the JSON: {e}")
            return
        
        current_time = datetime.datetime.now()
        CURRENT_DATE = current_time.strftime("%Y-%m-%d")
        CURRENT_HOUR = current_time.strftime("%H-%M-%S") 
        # print("✅ Current date and hour set:", CURRENT_DATE, CURRENT_HOUR)
        Settings.WRITE_LOG_DEV_FILE(f"Current date and hour set: {CURRENT_DATE} {CURRENT_HOUR}", "INFO")

        # print("📦 JSON Final:")
        Settings.WRITE_LOG_DEV_FILE("Final JSON:", "INFO")
        result_json = JsonManager.generate(self.scenario_layout , selected_Browser)
        # print(json.dumps(result_json, indent=2, ensure_ascii=False))
        # print("✅ Final JSON generated. Data:", json.dumps(result_json, indent=2, ensure_ascii=False))
        Settings.WRITE_LOG_DEV_FILE(f"Final JSON generated. Data: {json.dumps(result_json, indent=2, ensure_ascii=False)}", "INFO")



        if not result_json or result_json == []:
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                "No valid actions could be generated or an error occurred while saving the configuration file.\n\n"
                "If the problem persists, contact Support.",
                message_type="critical"
            )
            Settings.WRITE_LOG_DEV_FILE("No valid actions could be generated or an error occurred while saving the configuration file.", "ERROR")
            return


        try:
            save_status = JsonManager.save_json_to_file(result_json, selected_Browser)

            if save_status == "ERROR":
                UIManager.Show_Critical_Message(
                    window,
                    "Error - Save Configuration",
                    "An error occurred while saving the configuration file.\n\n"
                    "If the problem persists, contact Support.",
                    message_type="critical"
                )
                Settings.WRITE_LOG_DEV_FILE("An error occurred while saving the configuration file.", "ERROR")
                return
            # else:
            #     print("✅ JSON file saved with status:", save_status)

        except Exception as e:
            # print(f"❌ Erreur lors de la sauvegarde du JSON: {e}")
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                f"An error occurred while saving the configuration file:\n\n{e}",
                message_type="critical"
            )
            Settings.WRITE_LOG_DEV_FILE(f"An error occurred while saving the configuration file: {e}", "ERROR")
            return

        try:
            with open(Settings.FILE_ISP, 'w', encoding='utf-8') as f:
                f.write(self.Isp.currentText().strip())
        except Exception as e:
            # print("❌ Error writing to Isp.txt:", e)
            print(f"❌ Erreur lors de l'écriture dans Isp.txt : {e}")
            Settings.WRITE_LOG_DEV_FILE(f"Error writing to Isp.txt: {e}", "ERROR")

        json_string = json.dumps(result_json)

        parameters = { 
            'p_owner': session_info["username"],
            'p_entity': session_info["p_entity"],
            'p_isp': self.Isp.currentText(),
            'p_action_name': json_string,  
            'p_app': 'V4',
            'p_python_version': f"{sys.version_info.major}.{sys.version_info.minor}", 
            'p_browser': self.browser.currentText(),
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
                message_type="critical"
            )
            Settings.WRITE_LOG_DEV_FILE("Failed to save the process in the database.", "ERROR")
            return
        # print("✅ Obtained Process ID:", unique_id)
        # print(f"✅ Process ID obtenu: {unique_id}")


        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(Start_Extraction, window, data_list , entered_number, selected_Browser, self.Isp.currentText() , unique_id , result_json, session_info["username"])
            executor.submit(self.LOGS_THREAD.start)
        EXTRACTION_THREAD.finished.connect(lambda: self.Extraction_Finished(window))




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

        UIManager.Remove_Copier( self.scenario_layout, self.reset_options_layout)
        UIManager.Remove_Initaile( self.scenario_layout, self.reset_options_layout)

        UIManager.Display_State_Stack_As_Table(self)



    def Update_Actions_Color_Handle_Last_Button(self):
        UIManager.Update_Actions_Color_Handle_Last_Button( self.scenario_layout, self.Go_To_Previous_State)




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
                label = state.get('label', action_key)
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

        UIManager.Remove_Copier( self.scenario_layout, self.reset_options_layout)
        UIManager.Display_State_Stack_As_Table(self)


    



    def Clear_Button_Clicked(self):
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        global LOGS
        LOGS = []








    def Scenario_Changed(self, name_selected):
        # print("\n" + "="*80)
        # print(f"🔹 Scenario_Changed called with name_selected={name_selected}")
        # print("="*80 + "\n")

        # قراءة session
        encrypted_key = UIManager.read_file_content(Settings.SESSION_PATH)
        if not encrypted_key:
            # print("⚠️ Session vide ou fichier introuvable:", Settings.SESSION_PATH)
            Settings.WRITE_LOG_DEV_FILE(f"⚠️ Session vide ou fichier introuvable", "WARNING")
            return
        # print(f"🔑 Encrypted key loaded: {len(encrypted_key)} chars")

        payload = {"encrypted": encrypted_key, "name": name_selected}
        # print(f"📤 Payload prepared: {payload}")

        # إرسال الطلب
        try:
            t0_req = time.time()
            response = requests.post(Settings.API_ENDPOINTS['_ON_SCENARIO_CHANGED_API'], json=payload, timeout=10)
            t1_req = time.time()
            # print(f"✅ Request sent successfully in {t1_req - t0_req:.3f}s. HTTP Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # print(f"❌ RequestException while calling API: {e}")
            return

        # التحقق من حالة HTTP
        if response.status_code != 200:
            try:
                print(f"❌ HTTP {response.status_code}:\n{response.text[:1000]}")
            except Exception:
                print(f"❌ HTTP {response.status_code} and failed to read response.text")
            return

        # قراءة JSON
        try:
            result = response.json()
            # print(f"🔍 Response JSON keys: {list(result.keys())}")
        except ValueError:
            # print(f"❌ Failed to parse JSON from response. Response text (first 2000 chars):\n{response.text[:2000]}")
            return

        # التحقق من session
        try:
            session_ok = result.get("session", True)
            if session_ok is False:
                # print("🔒 Session expirée. Redirection vers login.")
                Settings.WRITE_LOG_DEV_FILE(f"🔒 Session expirée. Redirection vers login.", "WARNING")
                try:
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
                    print("❌ Erreur pendant l'affichage de la fenêtre de login:", e)
                return
            else:
                Settings.WRITE_LOG_DEV_FILE(f"🔑 Session OK", "INFO")
        except Exception as e:
            # print("⚠️ Erreur en vérifiant la clé 'session' du résultat:", e)
            Settings.WRITE_LOG_DEV_FILE(f"⚠️ Erreur en vérifiant la clé 'session' du 결과", "WARNING")
            return

        # حذف كل widgets القديمة
        # print("\n🧹 Nettoyage de la layout avant chargement du scénario...")
        for i in reversed(range(self.scenario_layout.count())):
            item = self.scenario_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = widget.objectName() if widget.objectName() else widget.__class__.__name__
                    # print(f"🗑️ Suppression du widget: {widget_name}")
                    Settings.WRITE_LOG_DEV_FILE(f"🗑️ Suppression du widget: {widget_name}", "INFO")
                    widget.deleteLater()
                else:
                    # print(f"📦 Élément non-widget trouvé à l'index {i}")
                    Settings.WRITE_LOG_DEV_FILE(f"📦 Élément non-widget trouvé à l'index {i}", "INFO")

        # معالجة السيناريو
        try:
            if not result.get("success"):
                # print(f"❌ API returned success=false; error: {result.get('error')}")
                Settings.WRITE_LOG_DEV_FILE(f"❌ API returned success=false; error: {result.get('error')}", "WARNING")
                return

            scenario = result.get("scenario")
            if scenario is None:
                Settings.WRITE_LOG_DEV_FILE(f"❌ Le champ 'scenario' est manquant dans la réponse.", "WARNING")
                # print("❌ Le champ 'scenario' est manquant dans la réponse.")
                return

            state_stack = scenario.get("state_stack")
            if not isinstance(state_stack, list):
                # print(f"⚠️ state_stack n'est pas une liste (type={type(state_stack)}). Tentative de conversion...")
                Settings.WRITE_LOG_DEV_FILE(f"⚠️ state_stack n'est pas une liste (type={type(state_stack)}). Tentative de conversion...", "WARNING")
                if isinstance(state_stack, str):
                    try:
                        state_stack = json.loads(state_stack)
                        Settings.WRITE_LOG_DEV_FILE(f"✅ state_stack loaded from string; length={len(state_stack)}", "INFO")
                        # print(f"✅ state_stack loaded from string; length={len(state_stack)}")
                    except Exception as e:
                        Settings.WRITE_LOG_DEV_FILE(f"❌ Impossible de parser state_stack string: {str(e)}", "WARNING")
                        # print("❌ Impossible de parser state_stack string:", e)
                        return
                else:
                    Settings.WRITE_LOG_DEV_FILE(f"❌ state_stack a un format inattendu: {repr(state_stack)}", "WARNING")
                    # print("❌ state_stack a un format inattendu:", repr(state_stack))
                    return

            self.STATE_STACK = state_stack
            # print(f"📥 Scénario récupéré avec {len(self.STATE_STACK)} états.\n")
            Settings.WRITE_LOG_DEV_FILE(f"📥 Scénario récupéré avec {len(self.STATE_STACK)} états.", "INFO")
            # نسخ آمن للمعالجة
            state_stack_copy = copy.deepcopy(self.STATE_STACK)

            # تحميل كل حالة
            for index, state in enumerate(state_stack_copy, start=1):
                print(f"\n[🧩] Processing state #{index}")
                try:
                    pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
                    # print(f"Preview state #{index} (first 500 chars):\n{pretty[:500]}...")
                except Exception:
                    print(f"⚠️ Cannot JSON-dump state #{index}; fallback to repr")
                    Settings.WRITE_LOG_DEV_FILE(f"⚠️ Cannot JSON-dump state #{index}; fallback to repr", "WARNING")
                    # print(repr(state)[:500], "...")

                try:
                    t0 = time.time()
                    self.Load_State(state)
                    t1 = time.time()
                    # print(f"✅ Load_State for #{index} succeeded in {t1 - t0:.3f}s")
                    Settings.WRITE_LOG_DEV_FILE(f"✅ Load_State for #{index} succeeded in {t1 - t0:.3f}s", "INFO")

                    try:
                        self.Update_Actions_Color_Handle_Last_Button()
                        # print("✅ Update_Actions_Color_Handle_Last_Button succeeded")
                    except Exception as e:
                        Settings.WRITE_LOG_DEV_FILE(f"⚠️ Update_Actions_Color_Handle_Last_Button failed after state #{index}: {e}", "WARNING")
                        print(f"⚠️ Update_Actions_Color_Handle_Last_Button failed after state #{index}: {e}")
                except Exception as e:
                    Settings.WRITE_LOG_DEV_FILE(f"❌ Erreur pendant Load_State() pour l'état #{index}: {e}", "WARNING")
                    print(f"❌ Erreur pendant Load_State() pour l'état #{index}: {e}")
                    continue

            # print("\n🎉 Scénario chargé avec succès.\n")

            
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
                # print(f"🧹 self.STATE_STACK dédupliqué, nouveau length={len(self.STATE_STACK)}")
            except Exception as e:
                print("⚠️ Échec de suppression des doublons:", e)

        except Exception as e:
            print("❌ Erreur pendant le traitement du résultat JSON:", e)

        # print("\n" + "="*80 + "\n")












class LoginWindow(QMainWindow):



    def __init__(self):
        super().__init__()

        self.ui_path = self.Select_Ui_File()
        uic.loadUi(self.ui_path, self)
        if "Auth.ui" in self.ui_path:
            self.Initialize_Login_Ui()
        self.setWindowTitle("AutoMailPro")




    def Select_Ui_File(self) -> str:

        try:
            session_info = SessionManager.check_session()

            if session_info["valid"]:
                return Settings.INTERFACE_UI 
        except Exception as e:
            # print(f"[SESSION ERROR] {e}")
            Settings.WRITE_LOG_DEV_FILE(f"[SESSION ERROR] {e}", "WARNING")

        return Settings.AUTH_UI




    def Initialize_Login_Ui(self):
        self.login_input = self.findChild(QLineEdit, "loginInput")
        self.password_input = self.findChild(QLineEdit, "passwordInput")
        self.login_button = self.findChild(QPushButton, "loginButton")
        self.title = self.findChild(QPushButton, "title")
        self.erreur_label = self.findChild(QLabel, "erreur")

        if self.erreur_label:
            self.erreur_label.hide()

        if self.title:
            self.title.clicked.connect(self.Handle_Show_Session_Date)
        if self.login_button:
            self.login_button.clicked.connect(self.Handle_Login)

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
                logo_path = os.path.join(SCRIPT_DIR, "icons", "logo.jpg")
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setGeometry(0, 0, self.logoFrame.width(), self.logoFrame.height())
                    self.logo_label.show()
 
            self.UseFrame = self.findChild(QFrame, "userFrame")
            if self.UseFrame:
                self.user_label = QLabel(self.UseFrame)
                self.user_label.setScaledContents(True)
                user_path = os.path.join(SCRIPT_DIR, "icons", "user.png")
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
        username = self.login_input.text().strip() if hasattr(self.login_input, "text") else str(self.login_input).strip()
        password = self.password_input.text().strip() if hasattr(self.password_input, "text") else str(self.password_input).strip()

        if len(username) <= 4:
            self.erreur_label.setText("Username must contain more than 4 characters.")
            self.erreur_label.show()
            return

        if len(password) <= 4:
            self.erreur_label.setText("Password must contain more than 4 characters.")
            self.erreur_label.show()
            return

        auth_result = SessionManager.check_api_credentials(username, password)

        if isinstance(auth_result, int):
            messages = {
                -1: "Invalid credentials. Please try again.",
                -2: "This device is not authorized. Please contact support.",
                -3: "Unable to connect to the server. Please try again later.",
                -4: "Access to this application has been denied.",
                -5: "Unknown error occurred during authentication."
            }
            self.erreur_label.setText(messages.get(auth_result, "An unknown error occurred."))
            self.erreur_label.show()
            return

        entity, encrypted_response = auth_result

        try:
            decrypted_response_entity = EncryptionService.decrypt_message(
                encrypted_response,
                Settings.KEY
            )
        except Exception as e:
            self.erreur_label.setText(f"Session decryption error: {str(e)}")
            self.erreur_label.show()
            return

        valid_session = SessionManager.create_session(username, password, decrypted_response_entity)
        if not valid_session:
            self.erreur_label.setText("Failed to create user session.")
            self.erreur_label.show()
            return

        self.erreur_label.hide()

        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            if not json_data:
                raise ValueError("Configuration file is empty.")
        except Exception as e:
            self.erreur_label.setText(f"Configuration error: {str(e)}")
            self.erreur_label.show()
            return

        self.main_window = MainWindow(json_data)
        self.main_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
        self.main_window.setWindowTitle("AutoMailPro")
        self.main_window.stopButton.clicked.connect(
            lambda: Stop_All_Processes(self.main_window)
        )

        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.main_window.width()) // 2
        y = (screen_geometry.height() - self.main_window.height()) // 2
        self.main_window.move(x, y)

        self.main_window.show()
        self.close()




    def Handle_Show_Session_Date(self):
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            self.erreur_label.setText("Session file not found .") 
            self.erreur_label.show()
            return
        
        is_valid, session_data = ValidationUtils.validate_session_file(Settings.SESSION_PATH)

        if is_valid:
            self.erreur_label.setText(f"Session data: {session_data}") 
        else:
            self.erreur_label.setText(f"Session file is not valid.")
        self.erreur_label.show()







def main():


    if len(sys.argv) < 3:
        sys.exit(1)

    encrypted_key = sys.argv[1]
    secret_key = sys.argv[2]

    if not EncryptionService.verify_key(encrypted_key, secret_key):
        sys.exit(1)

    session_info = SessionManager.check_session_full()
    session_valid = session_info["valid"]

    app = QApplication(sys.argv)


    if ValidationUtils.path_exists(Path(Settings.APP_ICON)):
        app.setWindowIcon(QIcon(str(Path(Settings.APP_ICON))))  
    else:
        print("⚠️ [LOG] Fichier d'icone introuvable")

    if session_valid:
        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding='utf-8') as file:
                json_data = json.load(file)

            if json_data:
                window = MainWindow(json_data)
            else:
                raise ValueError("Fichier de configuration vide")
                Settings.WRITE_LOG_DEV_FILE("Session valid", "INFO")
        except Exception as e:
            window = LoginWindow()
    else:
        window = LoginWindow()

    window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
    screen = QGuiApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    x = (screen_geometry.width() - window.width()) // 2
    y = (screen_geometry.height() - window.height()) // 2
    window.move(x, y)

    if hasattr(window, "stopButton"):
        window.stopButton.clicked.connect(lambda: Stop_All_Processes(window))

    window.setWindowTitle("AutoMailPro")
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()