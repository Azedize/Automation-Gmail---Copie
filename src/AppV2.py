import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon , QCursor 
from PyQt6.QtCore import Qt , QTimer , QThread, pyqtSignal , QSize
from PyQt6 import  uic 
import shutil
import signal
import time
import subprocess
import random
import re
import datetime
import requests
import sys
import zipfile
import traceback
import urllib3
import psutil
from platformdirs import user_downloads_dir
import win32gui       
import win32process
import win32con
from PyQt6.QtGui import QColor, QPixmap
from PyQt6 import uic
from PyQt6.QtGui import QGuiApplication
import copy
import warnings
import tempfile
import stat

warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


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
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))






# 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


os.makedirs(Settings.APPDATA_DIR, exist_ok=True)

DATA = {
    "login": "rep.test",
    "password": "zsGEnntKD5q2Brp68yxT"
}

encrypted = EncryptionService.encrypt_message(json.dumps(DATA), Settings.KEY)

# DROPBOX_URL    = "https://www.dropbox.com/scl/fi/78a38bc4papwzlw80hxti/version.json?rlkey=n7dx5mb8tcctvprn0wq4ojw7m&st=ormvslid&dl=1"
# GITHUB_ZIP_URL = "https://github.com/Azedize/Extention-Repo/archive/refs/heads/main.zip"

CHECK_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted}"
SERVEUR_ZIP_URL_EX3 = f"http://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Ext3&k={encrypted}"


# Si ce n'est pas le cas, il tente de l'installer via Chocolatey (et installe aussi npm).
def ensure_node_installed():
    if shutil.which("node") is not None:
        print("✅ Node.js est déjà installé.")
        return True

    print("❌ Node.js n'est pas installé. Tentative d'installation via Chocolatey...")

    if shutil.which("choco") is None:
        print("🔍 Chocolatey non trouvé. Installation...")
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
        print("⚠️ Impossible de continuer sans Node.js.")
        return
    
    if shutil.which('npm') is None:
        return
    
    if shutil.which('web-ext') is not None:
        return
    
    try:
        subprocess.run('npm install --global web-ext', check=True, shell=True)
    except subprocess.CalledProcessError:
        print("❌ Échec de l'installation de 'web-ext' via npm.")






# 📝 Ajoute un message au journal global 'LOGS'
def log_message(text):
    global LOGS
    LOGS.append(text)






# 🧪 Exemple de génération d'un ID de session
SESSION_ID = ValidationUtils.generate_session_id()



def Stop_All_Processes(window):
    global EXTRACTION_THREAD, CLOSE_BROWSER_THREAD, PROCESS_PIDS, LOGS_RUNNING, SELECTED_BROWSER_GLOBAL

    print("Stopping all processes...")
    LOGS_RUNNING = False

    if EXTRACTION_THREAD:
        print("Stopping extraction thread...")
        EXTRACTION_THREAD.stop_flag = True
        EXTRACTION_THREAD.wait()
        EXTRACTION_THREAD = None
        print("Extraction thread stopped.")


    if CLOSE_BROWSER_THREAD:
        print("Stopping close Chrome thread...")
        CLOSE_BROWSER_THREAD.stop_flag = True
        CLOSE_BROWSER_THREAD.wait()
        CLOSE_BROWSER_THREAD = None
        print("Close Chrome thread stopped.")

    if EXTRACTION_THREAD and EXTRACTION_THREAD.isRunning():
        print("Waiting for extraction thread to finish before updating UI...")
        EXTRACTION_THREAD.finished.connect(
            lambda: QTimer.singleShot(100, 
            lambda: UIManager.Read_Result_Update_List(window))
        )

    if SELECTED_BROWSER_GLOBAL != "firefox":
        for pid in PROCESS_PIDS[:]:
            try:
                print(f"Attempting to terminate process with PID {pid}...")
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                print(f"Process {pid} terminated successfully.")
            except psutil.NoSuchProcess:
                print(f"The process with PID {pid} no longer exists.")
            except psutil.AccessDenied:
                print(f"Permission denied to terminate the process with PID {pid}.")
            except Exception as e:
                print(f"An error occurred while terminating PID {pid}: {e}")
            finally:
                if pid in PROCESS_PIDS:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")
    else:
            try:
                BrowserManager.Close_Windows_By_Profiles(FIREFOX_LAUNCH)
            except Exception as e:
                print(f"⚠️ Erreur lors de la fermeture des profils Firefox: {e}")
 
            finally:
                for pid in PROCESS_PIDS[:]:
                    PROCESS_PIDS.remove(pid)
                    print(f"PID {pid} removed from process list.")




# 🚀 Lance un thread pour fermer automatiquement les processus Chrome actifs.
def Launch_Close_Chrome(selected_Browser , username):
    global CLOSE_BROWSER_THREAD
    CLOSE_BROWSER_THREAD = CloseBrowserThread( selected_Browser ,username)
    CLOSE_BROWSER_THREAD.progress.connect(lambda msg: print(msg))
    CLOSE_BROWSER_THREAD.start()





# -----------------------------
# Génération complète de l'extension Chrome/Firefox
# -----------------------------

def Generate_User_Input_Data(window):
    # Récupération des données depuis l’UI
    input_data = window.textEdit_3.toPlainText().strip()
    entered_number_text = window.textEdit_4.toPlainText().strip()

    # Appel de la logique de validation
    validation_result = ValidationUtils.process_user_input(
        input_data,
        entered_number_text
    )

    # En cas d’erreur → affichage UI
    if not validation_result["success"]:
        UIManager.Show_Critical_Message(
            window,
            validation_result["error_title"],
            validation_result["error_message"],
            message_type=validation_result.get("error_type", "critical")
        )
        return None

    # Succès → même retour que la fonction originale
    return (
        validation_result["data_list"],
        validation_result["entered_number"]
    )









# 🛠️ Démarre le processus d'extraction en lançant le thread principal avec les paramètres utilisateur, après validation des entrées et préparation de l'environnement.
def Start_Extraction(window, data_list, entered_number , selected_Browser , Isp , unique_id , output_json_final , username):
    global EXTRACTION_THREAD 
    print("Starting extraction process...")
    
    ValidationUtils.ensure_path_exists(Settings.LOGS_DIRECTORY)
    
    try:
        entered_number = int(entered_number)
    except ValueError:
        UIManager.Show_Critical_Message(
            window,
            "Input Error - Invalid Format",
            "Numeric value required. Please check your input and try again.",
            message_type="critical"
        )


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
        return
    print("Selected entries:", entered_number)




    Launch_Close_Chrome(selected_Browser , username)
    browser_path = (
        BrowserManager.get_browser_path("chrome.exe") if selected_Browser == "chrome"
        else BrowserManager.get_browser_path("firefox") if selected_Browser == "firefox"
        else BrowserManager.get_browser_path("msedge.exe") if selected_Browser == "edge"
        else BrowserManager.get_browser_path("dragon.exe")  
    )
    print("browser path   :",   browser_path    or "Non найд")

    print("le programme is runing dans une interface superstar et tres professionnelle et 100% secure")

    if selected_Browser == "firefox":
        ensure_web_ext_installed()

    print("browser path   :",   browser_path    or "Non trouvé")

    # return browser_path;
    EXTRACTION_THREAD = ExtractionThread(
        data_list, SESSION_ID, entered_number, browser_path, Settings.BASE_DIRECTORY , window ,selected_Browser , Isp , unique_id , output_json_final
    )
    EXTRACTION_THREAD.progress.connect(lambda msg: print(msg))
    EXTRACTION_THREAD.finished.connect(lambda: QMessageBox.information(window, "Terminé", "L'extraction est terminée."))
    EXTRACTION_THREAD.stopped.connect(lambda msg: QMessageBox.warning(window, "Arrêté", msg))
    EXTRACTION_THREAD.start()




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











# Thread responsable du traitement de l'extraction des emails.
# Gère l'exécution des navigateurs avec les extensions, l'enregistrement des LOGS,
# et la gestion des processus.
class ExtractionThread(QThread):

    progress = pyqtSignal(str)  
    finished = pyqtSignal()  
    stopped = pyqtSignal(str)

    def __init__(self, data_list, SESSION_ID, entered_number, Browser_path, BASE_DIRECTORY, main_window ,selected_Browser,Isp , unique_id , output_json_final):  
        super().__init__()
        self.data_list = data_list  
        self.session_id = SESSION_ID  
        self.entered_number = entered_number  
        self.Browser_path = Browser_path 
        self.BASE_DIRECTORY = BASE_DIRECTORY  
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
            print("[SESSION] ❌ Session invalide. Impossible de continuer l’extraction.")
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            return
        

        if self.selected_Browser == "chrome":
            print(f"✅ Navigateur sélectionné : {self.selected_Browser}")


            Settings.RESULTATS_EX = BrowserManager.Upload_EXTENTION_PROXY("default", Settings.CLES_RECHERCHE, Settings.RESULTATS)
            print("↕️​↕️​↕️​↕️​↕️​ Résultats EX2 :")
            for item in Settings.RESULTATS_EX:
                print(json.dumps(item, indent=4, ensure_ascii=False))


        while remaining_emails or PROCESS_PIDS:

            if self.stop_flag:  
                LOGS_RUNNING=False 
                log_message("[INFO] Processing interrupted by user.")
                break


            if len(PROCESS_PIDS) < self.entered_number and remaining_emails:
                next_email = remaining_emails.pop(0)  
                email_value = ValidationUtils.get_key_from_dict(next_email, ["email", "Email"])
                log_message(f"[INFO] Processing the email:  {email_value}")

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

                    session_directory = os.path.join(Settings.LOGS_DIRECTORY, f"{CURRENT_DATE}_{CURRENT_HOUR}")
                    os.makedirs(session_directory, exist_ok=True)

                    logs_subdirs = [os.path.join(Settings.LOGS_DIRECTORY, d) for d in os.listdir(Settings.LOGS_DIRECTORY) if os.path.isdir(os.path.join(Settings.LOGS_DIRECTORY, d))]
                    logs_subdirs.sort(key=os.path.getctime)

                    if len(logs_subdirs) > 4:
                        to_delete = logs_subdirs[:4]
                        for dir_to_delete in to_delete:
                            try:
                                shutil.rmtree(dir_to_delete)
                            except Exception as e:
                                log_message(f"[INFO]  Erreur lors de la suppression de {dir_to_delete} : {e}")

                  
                    if self.selected_Browser == "firefox":

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
                            "--source-dir", os.path.join(self.BASE_DIRECTORY, profile_email),
                            "--firefox-profile", os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'firefox', profile_email),
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

                        ExtensionManager.add_pid_to_text_file(process.pid, profile_email , inserted_id , self.session_id)

                    elif self.selected_Browser in ["edge", "icedragon", "Comodo"]:

                        command = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(SCRIPT_DIR, '..', 'Tools', 'Profiles', 'chrome', profile_email)}",
                            f"--disable-extensions-except={os.path.join(self.BASE_DIRECTORY, profile_email)}",
                            f"--load-extension={os.path.join(self.BASE_DIRECTORY, profile_email)}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync"
                        ]
                        process = subprocess.Popen(command) 
                        PROCESS_PIDS.append(process.pid) 

                        ExtensionManager.add_pid_to_text_file(process.pid, profile_email , inserted_id ,self.session_id)
                    
                    else:

                        ValidationUtils.ensure_path_exists(Settings.CHROME_PROFILES, is_file=False)

                        if not ValidationUtils.path_exists(os.path.join(Settings.CHROME_PROFILES,profile_email)):

                            BrowserManager.Run_Browser_Create_Profile(profile_email)
                            time.sleep(3)



                        if not  Settings.RESULTATS_EX:
                            error_msg = (
                                "❌ An issue occurred while copying the JSON file to the template profile.\n"
                                "➡ Please contact support."
                            )
                            log_message(error_msg)   
                            self.stopped.emit(error_msg)  
                            self.stop_flag = True   
                            return                   
                        else:
                            BrowserManager.Updated_Secure_Preferences(profile_email, Settings.RESULTATS_EX)

                        time.sleep(2)
                        
                        # combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email}"
                        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email}"

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
                        print('➡️➡️➡️➡️➡️➡️ PROCESS_PIDS : ' ,PROCESS_PIDS)
                        # ExtensionManager.add_pid_to_text_file(process.pid, profile_email , inserted_id , )
             
                    self.emails_processed += 1  

                except Exception as e:
                    log_message(f"[ERROR] Erreur emojie  : {e}")
                    log_message(f"[INFO] Erreur : {e}")
            self.msleep(1000) 

        log_message("[INFO] Processing finished for all emails.") 
        time.sleep(3)
        LOGS_RUNNING=False
        self.finished.emit()







# et qui traite les fichiers de session et LOGS générés dans le dossier Downloads.
class CloseBrowserThread(QThread):


    progress = pyqtSignal(str)  



    def __init__(self , selected_Browser, username):
        super().__init__()
        self.selected_Browser = selected_Browser
        self.username =username
        self.session_id = SESSION_ID  
        self.stop_flag = False 
        self.downloads_folder = user_downloads_dir() 




    def run(self):

        time.sleep(10)
        session = ""
        if ValidationUtils.path_exists(Settings.SESSION_PATH):
            with open(Settings.SESSION_PATH, "r", encoding="utf-8") as f:
                session = f.read().strip()

        while not self.stop_flag:  

            if not PROCESS_PIDS:
                break

            files = [f for f in os.listdir(self.downloads_folder) if f.startswith(self.session_id) and f.endswith(".txt")]
            log_files = [f for f in os.listdir(self.downloads_folder) if f.startswith("log_") and f.endswith(".txt")]

    
            with ThreadPoolExecutor() as executor:
                futures = []
                for log_file in log_files:
                    futures.append(executor.submit(self.process_log_file, log_file, self.downloads_folder))

                for future in as_completed(futures):
                    result = future.result() 


            with ThreadPoolExecutor() as executor:
                futures = []
                for file_name in files:
                    futures.append(executor.submit(self.process_session_file, file_name, self.downloads_folder , self.selected_Browser, session))

                for future in as_completed(futures):
                    result = future.result() 

            time.sleep(1)


    

    def process_log_file(self, log_file, downloads_folder):
        try:
            global CURRENT_HOUR, CURRENT_DATE

            email = self.get_email_from_log_file(os.path.join(downloads_folder, log_file))  
            if not email:
                return f"⚠️ Erreur dans le fichier {log_file}: Email non trouvé."

            session_folder = f"{CURRENT_DATE}_{CURRENT_HOUR}"
            target_folder = os.path.join(Settings.LOGS_DIRECTORY , session_folder)
            target_file_path = os.path.join(target_folder, f"{email}_{CURRENT_HOUR}.txt")

            try:
                with open(os.path.join(downloads_folder, log_file), 'r', encoding='utf-8') as log_file_reader:
                    log_content = log_file_reader.read()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {log_file}: {e}"

            try:
                with open(target_file_path, 'a', encoding='utf-8') as target_file_writer:
                    target_file_writer.write(log_content + "\n")
            except Exception as e:
                return f"⚠️ Erreur lors de l'écriture dans {target_file_path}: {e}"


            try:
                os.remove(os.path.join(downloads_folder, log_file))
                return f"🗑️ Fichier log supprimé : {os.path.join(downloads_folder, log_file)}"
            except Exception as e:
                return f"⚠️ Erreur lors de la suppression du fichier {os.path.join(downloads_folder, log_file)}: {e}"

        except Exception as e:
            return f"⚠️ Erreur dans le fichier {log_file} : {e}"





    def process_session_file(self, file_name, downloads_folder , selected_Browser, session):
        try:
            try:
                with open(os.path.join(downloads_folder, file_name), 'r', encoding='utf-8') as file:
                    file_content = file.read().strip()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {file_name}: {e}"

            match = re.search(r"session_id:(\w+)_PID:(\d+)_Email:([\w.@]+)_Status:(\w+)", file_content)
            if not match:
                os.remove(os.path.join(downloads_folder, file_name))
                return f"⚠️ Format incorrect dans {file_name}: {file_content}"
            
            session_id, pid, email, etat  = match.groups()

            log_message(f"[INFO] Email {email} has completed  processing with status {etat}.")

            try:
                with open(os.path.join(Settings.BASE_DIRECTORY , email , "data.txt"), 'r', encoding='utf-8') as file:
                    first_line = file.readline().strip() 
                    parts = first_line.split(":")
                    if len(parts) >= 4:
                        inserted_id = parts[3]
                    else:
                        return f"⚠️ Format de ligne invalide dans le fichier : {first_line}"

            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {os.path.join(downloads_folder, file_name)}: {e}"

            try:
                with open(os.path.join(downloads_folder, file_name), 'r', encoding='utf-8') as file:
                    file_content = file.read().strip()
            except Exception as e:
                return f"⚠️ Erreur lors de la lecture du fichier {file_name}: {e}"
            
            try:
                with open(Settings.RESULT_FILE , 'a', encoding='utf-8') as result_file:
                    result_file.write(f"{session_id}:{pid}:{email}:{etat}\n")
                    params = {
                        'id': inserted_id,
                        'login': self.username,
                        'status': 'OK' if etat == "completed" else 'NotOK',
                        'error':  '' if etat == "completed" else etat
                    }

                    Send_Status(params)

            except Exception as e:
                return f"⚠️ Erreur lors de l'écriture dans le fichier {file_name}: {e}"

         
            pid = int(pid)
            if pid in PROCESS_PIDS: 
                log_message(f"[INFO] Attempting to terminate process:  {email}.")
                if selected_Browser == "firefox":
                    try:
                        print("browser : ", selected_Browser)
                        print('✅✅✅✅✅✅✅✅PID : ', pid)
                        self.find_firefox_window(email)
                        self.wait_then_close(email)
                        PROCESS_PIDS.remove(pid)   
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la fermeture du processus {pid} ({email}): {e}")
                    
                else:
                    try:
                        print('✅✅✅✅✅✅✅✅✅✅ PID : ', pid)
                        os.kill(pid, signal.SIGTERM) 
                        PROCESS_PIDS.remove(pid)   
                        print(f"Processus {pid} ({email}) terminé.")
    
                    except Exception as e:
                        return f"⚠️ Erreur lors de la fermeture du processus {file_name}: {e}"
            try:
                os.remove(os.path.join(Settings.BASE_DIRECTORY , email , "data.txt"))
                return f"🗑️ Fichier session supprimé : {os.path.join(Settings.BASE_DIRECTORY , email , 'data.txt')}"
            except Exception as e:
                return f"⚠️ Erreur lors de la suppression du fichier {file_name}: {e}"

        except Exception as e:
            return f"⚠️ Erreur dans le fichier {file_name} : {e}"



    

    def find_firefox_window(self, profile_email, timeout=30):
        entry = next((e for e in FIREFOX_LAUNCH if e['profile'] == profile_email), None)
        if not entry:
            raise ValueError(f"❌ ERREUR: Profil '{profile_email}' non trouvé.")

        target_title = f"EXT:{profile_email}"


        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1
            elapsed = time.time() - start_time

            found = [False]

            def window_processor(hwnd, _):
                if found[0]:
                    return False

                if not win32gui.IsWindowVisible(hwnd):
                    return True

                try:
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name != 'MozillaWindowClass':
                        return True

                    window_title = win32gui.GetWindowText(hwnd)

                    if target_title in window_title:
                        entry['hwnd'] = hwnd
                        found[0] = True
                        return False
                except Exception as e:
                    print(f"⚠️ Erreur lors du traitement de la fenêtre HWND={hwnd} : {e}")
                return True
            try:
                win32gui.EnumWindows(window_processor, None)
            except Exception as e:
                print(f"⚠️ Exception EnumWindows : {e}")
            if entry['hwnd']:
                return entry['hwnd']
            time.sleep(2)

        raise TimeoutError(f"Impossible de trouver la fenêtre pour {profile_email}")




    def wait_then_close(self, profile_email):
        entry = next((e for e in FIREFOX_LAUNCH if e['profile'] == profile_email), None)
        if not entry or not entry.get('hwnd'):
            print(f"❌ Aucune fenêtre trouvée pour {profile_email}.")
            return
        
        self.close_window_by_hwnd(entry['hwnd'], entry['proc'])




    def close_confirmation_dialogs(self, pid):
        def _enum(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, p = win32process.GetWindowThreadProcessId(hwnd)
                if p == pid and win32gui.GetClassName(hwnd) == '#32770':
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True

        win32gui.EnumWindows(_enum, None)





    def close_window_by_hwnd(self, hwnd, proc, wait_grace=2, wait_force=3):
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        time.sleep(wait_grace)

        if not win32gui.IsWindow(hwnd):
            return

        self.close_confirmation_dialogs(proc.pid)
        time.sleep(0.5)

        if not win32gui.IsWindow(hwnd):
            return

        try:
            proc.terminate()
            proc.wait(timeout=wait_force)
        except Exception:
            pass




    def get_email_from_log_file(self, file_name):
        file_name = os.path.basename(file_name)
        match = re.search(r"log_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z_([\w.+-]+@[\w.-]+\.[a-zA-Z]{2,6})\.txt", file_name)
        if match:
            print(f"   - Email extrait : {match.group(1)}")
            email = match.group(1)
            return email
        else:
            print(f"[Email Extraction] Aucun email trouvé dans {file_name}")
            return None
















def Process_Browser(window, selected_Browser):
    valid_browser, browser_msg = ValidationUtils.validate_browser_selection(selected_Browser)
    if not valid_browser:
        UIManager.Show_Critical_Message(
            window,
            "Browser Error",
            f"Unsupported browser: {selected_Browser}\n\n"
            f"Details: {browser_msg}",
            message_type="critical"
        )
        return False
    
    valid_dir, dir_msg = ValidationUtils.validate_directory_path(
        Settings.CONFIG_PROFILE, 
        must_exist=True
    )
    
    if not valid_dir:
        UIManager.Show_Critical_Message(
            window,
            "Configuration Error",
            f"Configuration folder not found.\n\n"
            f"Path: {Settings.CONFIG_PROFILE}\n"
            f"Details: {dir_msg}",
            message_type="critical"
        )
        return False
    

    
    valid_file, file_msg = ValidationUtils.validate_file_path(
        Settings.SECURE_PREFERENCES_TEMPLATE,
        must_exist=True
    )
    
    if not valid_file:
        UIManager.Show_Critical_Message(
            window,
            "Configuration Error",
            f"Secure preferences file not found.\n\n"
            f"Path: {Settings.SECURE_PREFERENCES_TEMPLATE}\n"
            f"Details: {file_msg}",
            message_type="critical"
        )
        return False

    try:
        with open(Settings.SECURE_PREFERENCES_TEMPLATE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        UIManager.Show_Critical_Message(
            window,
            "Configuration Error",
            f"Invalid JSON format in secure preferences.\n\n"
            f"Details: {str(e)}",
            message_type="critical"
        )
        return False
    except Exception as e:
        UIManager.Show_Critical_Message(
            window,
            "Configuration Error",
            f"Unable to read secure preferences file.\n\n"
            f"Details: {str(e)}",
            message_type="critical"
        )
        return False


    required_keys = []
    if selected_Browser == "chrome":
        required_keys = Settings.CLES_RECHERCHE 
    elif selected_Browser == "firefox":
        required_keys = ["extensions", "settings", "preferences"] 
    
    if required_keys:
        valid_structure, structure_msg = ValidationUtils.validate_json_structure(data, required_keys)
        if not valid_structure:
            print(f"❌ {structure_msg}")
            
            results_keys = []
            BrowserManager.Search_Keys(data, required_keys, results_keys)
            found_keys = [list(d.keys())[0] for d in results_keys]
            missing_keys = [key for key in required_keys if key not in found_keys]
            
            error_details = "\n".join([f"   {idx}. {key}" for idx, key in enumerate(missing_keys, 1)])
            
            UIManager.Show_Critical_Message(
                window,
                "Configuration Error",
                f"Missing required configuration keys.\n\n"
                f"Missing keys:\n{error_details}\n\n"
                f"Details: {structure_msg}",
                message_type="critical"
            )
            return False
    
    if not ValidationUtils.path_exists(Settings.EXTENTION_EX3):
        
        ext_dir = os.path.dirname(Settings.EXTENTION_EX3)
        valid_ext_dir, ext_dir_msg = ValidationUtils.validate_directory_path(
            ext_dir,
            must_exist=False
        )

        if not valid_ext_dir:
            UIManager.Show_Critical_Message(
                window,
                "Extension Error",
                f"Invalid extension directory.\n\n"
                f"Path: {ext_dir}\n"
                f"Details: {ext_dir_msg}",
                message_type="critical"
            )
            return False

        if Update_From_Serveur():
            log_message("✅ Extension installée avec succès.")
        else:
            UIManager.Show_Critical_Message(
                window,
                "Installation Failed",
                "We could not install the required extension.\n\n"
                "Please contact Support for assistance.",
                message_type="critical"
            )
            return False
    else:

        valid_ext_path, ext_path_msg = ValidationUtils.validate_directory_path(
            Settings.EXTENTION_EX3, 
            must_exist=True
        )
        
        if not valid_ext_path:
            UIManager.Show_Critical_Message(
                window,
                "Extension Error",
                f"Invalid extension path.\n\n"
                f"Path: {Settings.EXTENTION_EX3}\n"
                f"Details: {ext_path_msg}",
                message_type="critical"
            )
            return False
        
        remote_version = Check_Version_Extention(window)
        
        if isinstance(remote_version, str): 
            validations = [
                (True, f"Local extension found at: {Settings.EXTENTION_EX3}"),
                (True, f"Remote version available: {remote_version}"),
                (True, "Update process starting...")
            ]
            
            report = ValidationUtils.create_validation_report(validations)
            
            if Update_From_Serveur(remote_version):
                log_message("✅ Mise à jour réussie : l'extension a été mise à jour avec succès !")
            else:
                UIManager.Show_Critical_Message(
                    window,
                    "Update Failed",
                    "We could not update the browser extension.\n\n"
                    "Possible causes:\n"
                    " • Network connection issues\n"
                    " • Server temporarily unavailable\n"
                    " • Disk permissions\n\n"
                    "Please contact Support for assistance.",
                    message_type="critical"
                )
                return False
        elif remote_version is True:
            print("✅ L'extension locale est déjà à jour.")
                        
            if ValidationUtils.path_exists(os.path.join(Settings.EXTENTION_EX3, "manifest.json")):
                try:
                    with open(os.path.join(Settings.EXTENTION_EX3, "manifest.json"), "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    
                    manifest_keys = ["manifest_version", "name", "version"]
                    valid_manifest, manifest_msg = ValidationUtils.validate_json_structure(
                        manifest_data, 
                        manifest_keys
                    )
                except Exception as e:
                    print(f"⚠️ Impossible de valider le manifest: {e}")
        else:
            UIManager.Show_Critical_Message(
                window,
                "Version Check Failed",
                "Unable to verify extension version.\n\n"
                "Please check your internet connection and try again.\n"
                "If the problem persists, contact Support.",
                message_type="critical"
            )
            return False

    final_validations = [
        (True, f"Browser: {selected_Browser}"),
        (valid_dir, f"Config directory: {dir_msg}"),
        (valid_file, f"Secure preferences: {file_msg}"),
        (True, "JSON structure validated"),
        (True, "Extension validated/updated")
    ]
    
    final_report = ValidationUtils.create_validation_report(final_validations)
    
    if all(v[0] for v in final_validations):
        return True
    else:
        for detail in final_report['details']:
            if detail['status'] == 'FAIL':
                log_message(f"   • {detail['message']}")
        
        UIManager.Show_Critical_Message(
            window,
            "Validation Failed",
            "Browser configuration validation failed.\n\n"
            "Please check the configuration and try again.",
            message_type="critical"
        )
        return False














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
        """Setup all comboboxes"""
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
        """Setup log display system"""

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
        """
        Sends the current scenario state to the API and handles responses.
        Displays user-friendly messages for errors and success.
        """
        # 1️⃣ Check if there are any actions to save
        if not self.STATE_STACK:
            UIManager.Show_Critical_Message(self, "No Data", "No actions to save. Please add actions before saving.", message_type="critical")
            return

        # 2️⃣ Check if the session file exists
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            UIManager.Show_Critical_Message(self, "Session Not Found", "[❌] Your session file is missing. Please restart the application.", message_type="critical")
            return

        # 3️⃣ Read the encrypted session key
        with open(Settings.SESSION_PATH, "r", encoding="utf-8") as f:
            encrypted_key = f.read().strip()

        payload = {
            # ⚠️ Ton PHP attend "encrypted", pas "decrypted_key"
            "encrypted": encrypted_key,
            "state": self.STATE_STACK[-1],
            "state_stack": self.STATE_STACK
        }

        try:
            result = APIManager.handle_save_scenario(payload)
            if result.get("session") is False:
                UIManager.Show_Critical_Message(self, "Session Expired", "[❌] Your session has expired. Please log in again.", message_type="critical")
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
            else:
                UIManager.Show_Critical_Message(self, "API Error", "An error occurred while saving the scenario.", message_type="critical")


        except Exception as e:
            UIManager.Show_Critical_Message(self, "Error", "An error occurred while saving the scenario.", message_type="critical")





    def Load_Scenarios_Into_Combobox(self):
        if self.saveSanario is None:
            print("self.saveSanario is None")
            return
        else:
            print("self.saveSanario is not None")
    
        if not ValidationUtils.path_exists(Settings.SESSION_PATH):
            return

        encrypted_key =UIManager.read_file_content(Settings.SESSION_PATH)

        if not encrypted_key:
            return

        payload = {"encrypted": encrypted_key}
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
            log_message(f"[❌] Erreur lors de la récupération des scénarios: {e}")







            


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
            log_message(f"[LOGOUT ERROR] {e}")


    def Update_Logs_Display(self, log_entry):
        UIManager.Update_Logs_Display(self, log_entry, self.log_layout)



    def Save_Json_To_File(self, json_data, selected_browser):
        if selected_browser.lower() == "firefox":
            template_dir = Settings.TEMPLATE_DIRECTORY_FIREFOX
        elif selected_browser.lower() == "chrome":
            template_dir = Settings.EXTENTION_EX3
        else:
            template_dir = Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME  

        traitement_file = os.path.join(template_dir, 'traitement.json')

        try:
            os.makedirs(template_dir, exist_ok=True)
            with open(traitement_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            return "SUCCESS" if template_dir != Settings.EXTENTION_EX3 else "SUCCESS_FAMILY"
        except Exception as e:
            return "ERROR"



    def Process_Split_Json(self, input_json):
        output_json = []
        current_section = []
        current_start = None

        def finalize_section():
            if current_section:
                output_json.extend(current_section)

        for element in input_json:
            process_type = element.get("process")

            if process_type == "loop" and not element.get("sub_process"):
                continue

            if process_type in {"open_inbox", "open_spam"}:
                finalize_section()
                current_section = [element]
                current_start = process_type
                continue


            if process_type == "loop":
                sub_process = element.get("sub_process", [])

            
                allowed_items = {
                    "open_inbox": {"report_spam", "delete", "archive"},
                    "open_spam": {"not_spam", "delete", "report_spam"}
                }.get(current_start, set())

            
                has_select_all = any(sp.get("process") == "select_all" for sp in sub_process)
                has_allowed_item = any(sp.get("process") in allowed_items for sp in sub_process)

                
                if has_select_all or has_allowed_item:
                    sub_process = [
                        sp for sp in sub_process
                        if sp.get("process") not in {"return_back", "next"}
                    ]

                element["sub_process"] = sub_process
                current_section.append(element)
                continue
            current_section.append(element)
        finalize_section()
        return output_json


 
    def Process_Handle_Last_Element(self, input_json):
        output_json = []

        for element in input_json:
            process_type = element.get("process")

            if process_type in ["google_maps_actions", "save_location", "search_activities"]:
                continue

            if process_type == "loop" and "sub_process" in element:
                sub_process = element["sub_process"]

                if sub_process:
                    last = sub_process[-1].get("process")

                    if last == "next":
                        output_json.append({
                            "process": "open_message",
                            "sleep": random.randint(1, 3)
                        })

                        sub_process = [
                            sp for sp in sub_process
                            if sp.get("process") != "open_message"
                        ]

                    elif last not in ["delete", "archive", "not_spam", "report_spam"]:
                        for sp in sub_process:
                            if sp.get("process") == "open_message":
                                sp["process"] = "OPEN_MESSAGE_ONE_BY_ONE"


                    has_select_all = any(
                        sp.get("process") == "select_all"
                        for sp in sub_process
                    )
                    has_archive = any(
                        sp.get("process") == "archive"
                        for sp in sub_process
                    )
                    has_next_page = any(
                        sp.get("process") == "next_page"
                        for sp in sub_process
                    )

                    if has_select_all and not has_archive and not has_next_page:
                        sub_process.append({
                            "process": "next_page",
                            "sleep": 2
                        })
                element["sub_process"] = sub_process
            output_json.append(element)
        return output_json





    def Process_Modify_Json(self, input_json):
        output_json = []
        current_section = []
        found_open_message = False

        def finalize_section():
            if current_section:
                output_json.extend(current_section)

        for element in input_json:
            process_type = element.get("process")
            if process_type == "open_message":
                found_open_message = True

            if process_type == "loop":
                if found_open_message:
                    sub_process = element.get("sub_process", [])
                    if any(sp.get("process") == "next" for sp in sub_process):
                        element.pop("check", None)
                current_section.append(element)
                continue

            current_section.append(element)

        finalize_section()
        return output_json


    def Extraction_Finished(self, window):
        self.LOGS_THREAD.stop()  
        self.LOGS_THREAD.wait()  
        QTimer.singleShot(100, lambda: UIManager.Read_Result_Update_List(window))




    
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
                print(f"[ERREUR NETTOYAGE SESSION] ❌ {e}")

            return





        # Nettoyage des badges de notification
        try:
            if self.result_tab_widget:
                for tab_index, badge in NOTIFICATION_BADGES.items():
                    if badge:
                        badge.deleteLater()
                NOTIFICATION_BADGES.clear()

                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        for lw in list_widgets:
                            lw.clear()  
        except Exception as e:
            log_message(f"[BADGES ERROR] Erreur lors de la suppression des badges : {e}")





        # For PROGRAMM COMPLETE UPDATE
        try:
            UpdateManager.check_and_update(self)

        except SystemExit:
            return
        except Exception as e:
            log_message(f"[UPDATE ERROR] {e}")


        selected_Browser = self.browser.currentText().lower()

        # if not Process_Browser(window, selected_Browser):
        #     return

        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                tab_text = self.INTERFACE.tabText(i)
                if tab_text.startswith("Result"):
                    self.INTERFACE.setTabText(i, "Result")
                    break
        
        LOGS_RUNNING = True

        output_json = [
            {
                "process": "login",  
                "sleep": 1  
            }
        ]

        if self.scenario_layout.count() == 0:
            UIManager.Show_Critical_Message(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning"
            )
            return

        try:
            print("📦 JSON test:")
            result = Generate_User_Input_Data(window)

            if not result:  
                return
            data_list, entered_number = result  

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error while parsing the JSON: {e}")
            return
        
        current_time = datetime.datetime.now()
        CURRENT_DATE = current_time.strftime("%Y-%m-%d")
        CURRENT_HOUR = current_time.strftime("%H-%M-%S") 

        print("📦 JSON Final:")
        result_json = JsonManager.generate_json_data(self.scenario_layout)
        print(json.dumps(result_json, indent=2, ensure_ascii=False))

        # CORRECTION: Vérifier si result_json est vide au lieu de vérifier "ERROR"
        if not result_json or result_json == []:
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                "No valid actions could be generated or an error occurred while saving the configuration file.\n\n"
                "If the problem persists, contact Support.",
                message_type="critical"
            )
            return

        # Sauvegarde du fichier JSON de traitement
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
                return
            else:
                print(f"✅ Fichier JSON sauvegardé avec statut: {save_status}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du JSON: {e}")
            UIManager.Show_Critical_Message(
                window,
                "Error - Save Configuration",
                f"An error occurred while saving the configuration file:\n\n{e}",
                message_type="critical"
            )
            return

        try:
            with open(Settings.FILE_ISP, 'w', encoding='utf-8') as f:
                f.write(self.Isp.currentText().strip())
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture dans Isp.txt : {e}")

        json_string = json.dumps(result_json)

        parameters = { 
            'p_owner': session_info["username"],
            'p_entity': session_info["p_entity"],
            'p_isp': self.Isp.currentText(),
            'p_action_name': json_string,  # CORRECTION: Utiliser json_string au lieu de json.dumps(result_json)
            'p_app': 'V4',
            'p_python_version': f"{sys.version_info.major}.{sys.version_info.minor}", 
            'p_browser': self.browser.currentText(),
        }

        unique_id = self.Save_Process(parameters)

        if unique_id == -1:
            print("❌ Error getting process ID")
            UIManager.Show_Critical_Message(
                window,
                "Error - Process Save",
                "Failed to save the process in the database.\n\n"
                "Please check your connection and try again.",
                message_type="critical"
            )
            return

        print(f"✅ Process ID obtenu: {unique_id}")


        # with ThreadPoolExecutor(max_workers=2) as executor:
        #     executor.submit(Start_Extraction, window, data_list , entered_number, selected_Browser, self.Isp.currentText() , unique_id , result_json, session_info["username"])
        #     executor.submit(self.LOGS_THREAD.start)
        # EXTRACTION_THREAD.finished.connect(lambda: self.Extraction_Finished(window))




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
            print(f"[Warning] Icon not found at: {icon_path}")

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
                print(f"🔘 {label}")
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
        print("Scenario_Changed called with name_selected=%r", name_selected)

        encrypted_key =UIManager.read_file_content(Settings.SESSION_PATH)
        if not encrypted_key:
            return
        payload = {"encrypted": encrypted_key, "name": name_selected}
        #print("Payload prepared: %s", {k: ("<hidden>" if k == "encrypted" else v) for k, v in payload.items()})

        try:
            start_time = time.time()
            # timeout pour éviter le blocage infini
            response = requests.post(Settings.API_ENDPOINTS['_ON_SCENARIO_CHANGED_API'], json=payload, timeout=10)
            duration = time.time() - start_time
            #print("HTTP POST to %s finished in %.2fs; status_code=%s", _ON_SCENARIO_CHANGED_API, duration, response.status_code)
        except requests.exceptions.RequestException as e:
            #print("RequestException while calling API: %s", e)
            # enregistrer le contenu d'erreur si disponible
            return

        # تسجيل نص الاستجابة كاملة لو احتجنا لفحصها عند الأخطاء
        if response.status_code != 200:
            try:
                print("HTTP %s: %s", response.status_code, response.text[:1000])
            except Exception:
                print("HTTP %s and failed to read response.text", response.status_code)
            return

        # محاولة تحويل الاستجابة إلى JSON مع حماية
        try:
            result = response.json()
            #print("Response JSON keys: %s", list(result.keys()))
        except ValueError:
            # JSON غير صالح — حفظ النص لفحص لاحق
            print("Failed to parse JSON from response. Response text (first 2000 chars):\n%s", response.text[:2000])
        
            return

        # التحقق من حالة الجلسة
        try:
            session_ok = result.get("session", True)
            if session_ok is False:
                #print("Session expirée. Redirection vers login.")
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
                except Exception:
                    print("Erreur pendant l'affichage de la fenêtre de login")
                return
        except Exception:
            #print("Erreur en vérifiant la clé 'session' du résultat")
            return



        for i in reversed(range(self.scenario_layout.count())):
            item = self.scenario_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = widget.objectName() if widget.objectName() else widget.__class__.__name__
                    # print(f"   🗑️ Suppression du widget: {widget_name}")
                    widget.deleteLater()
                # else:
                    # print(f"   📦 Élément non-widget trouvé à l'index {i}")
        # إذا العملية ناجحة
        try:
            if result.get("success"):
                scenario = result.get("scenario")
                if scenario is None:
                    #print("Le champ 'scenario' est manquant dans la réponse.")
                    return

                # التأكد من وجود state_stack
                state_stack = scenario.get("state_stack")
                if not isinstance(state_stack, list):
                    print("state_stack n'est pas une liste (type=%s). Tentative de conversion...", type(state_stack))
                    # محاولة تصحيح إذا كانت سلسلة JSON
                    if isinstance(state_stack, str):
                        try:
                            state_stack = json.loads(state_stack)
                            #print("state_stack loaded from string; length=%d", len(state_stack))
                        except Exception:
                            #print("Impossible de parser state_stack string")
                            return
                    else:
                        #print("state_stack a un format inattendu: %r", state_stack)
                        return

                self.STATE_STACK = state_stack
                #print("Scénario récupéré avec %d états.", len(self.STATE_STACK))

                # نسخة للمعالجة
                state_stack_copy = copy.deepcopy(self.STATE_STACK)

                for index, state in enumerate(state_stack_copy, start=1):
                    #print("Processing state #%d", index)
                    # محاولة عرض حالة بشكل آمن (fallback to str)
                    try:
                        pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
                        #print("State #%d preview: %s", index, pretty[:2000])  # لا تطبع كل شيء لو كبير
                    except Exception:
                        print("Cannot JSON-dump state #%d; fallback to repr", index)
                        #print("State #%d repr: %s", index, repr(state)[:1000])

                    # استدعاء Load_State مع قياس الوقت
                    try:
                        t0 = time.time()
                        self.Load_State(state)
                        t1 = time.time()
                        #print("Load_State for #%d succeeded in %.3fs", index, t1 - t0)
                        # بعد كل تحميل حدّث الأزرار
                        try:
                            self.Update_Actions_Color_Handle_Last_Button()
                        except Exception:
                            print("Update_Actions_Color_Handle_Last_Button failed after state #%d", index)
                    except Exception as e:
                        print("Erreur pendant Load_State() pour l'état #%d: %s", index, e)
                        # لا نكسر الحلقة — نستمر في محاولة تحميل باقي الحالات
                        continue

                #print("Scénario chargé avec succès.")

                # حذف التكرارات بطريقة آمنة: نستخدم json.dumps(default=str) لتجنب TypeError
                try:
                    unique_states = []
                    seen = set()
                    for state in self.STATE_STACK:
                        try:
                            state_key = json.dumps(state, sort_keys=True, ensure_ascii=False, default=str)
                        except Exception:
                            #print("json.dumps failed for a state during dedup; using repr fallback")
                            state_key = repr(state)
                        if state_key not in seen:
                            seen.add(state_key)
                            unique_states.append(state)
                    self.STATE_STACK = unique_states
                    #print("self.STATE_STACK dédupliqué, nouveau length=%d", len(self.STATE_STACK))
                except Exception:
                    print("Échec de suppression des doublons")
            # else:
                # print("API returned success=false; error: %s", result.get("error"))
        except Exception:
            print("Erreur pendant le traitement du résultat JSON")





















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
            print(f"[SESSION ERROR] {e}")

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

        valid_session = SessionManager.create_session(username, decrypted_response_entity)
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

    if ValidationUtils.path_exists(Settings.APP_ICON):
        app.setWindowIcon(QIcon(Settings.APP_ICON))

    if session_valid:
        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding='utf-8') as file:
                json_data = json.load(file)

            if json_data:
                window = MainWindow(json_data)
            else:
                raise ValueError("Fichier de configuration vide")
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