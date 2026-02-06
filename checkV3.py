# ==========================================================
# main.py
# ==========================================================

import os
import sys
import shutil
import zipfile
import importlib
import subprocess
import time
from pathlib import Path
import tempfile
import io
import datetime
import traceback



TOOLS_DIR = Path("Tools")
EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"
LOG_DEV_FILE = os.path.abspath(os.path.join( "Log/LogDev/my_project.log"))





# si casting contient 3 casting 
# ==========================================================
# 🔹 FIX UTF-8 POUR WINDOWS CONSOLE
# ==========================================================


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ==========================================================
# 🔹 IMPORTS INTERNES
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent





def generate_encrypted_key():
    from cryptography.fernet import Fernet
    secret_key = Fernet.generate_key()
    fernet = Fernet(secret_key)
    encrypted_message = fernet.encrypt(b"authorized")
    return encrypted_message.decode(), secret_key.decode()




def WRITE_LOG_DEV_FILE( message: str, level: str = "INFO"):
    try:
        # Génération de la date et heure actuelle pour le timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        # Vérifie que le dossier contenant le fichier de log existe, sinon le crée
        log_path = Path(LOG_DEV_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Ouvre le fichier en mode "append" pour ajouter la ligne de log à la fin
        with open(LOG_DEV_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
        # print(f"✅ [LOG] Log written: {LOG_DEV_FILE}")
    except Exception as e:
        # print(f"❌ [LOG] Erreur lors de l'écriture du log: {e}")
        pass





def clear_log():
    try:
        log_path = Path(LOG_DEV_FILE)
        if log_path.exists():
            # print(f"✅ [LOG] Fichier log trouvé: {LOG_DEV_FILE}")
            # Ouvre le fichier en mode "write" pour effacer tout son contenu
            open(log_path, "w", encoding="utf-8").close()
            # print(f"✅ [LOG] Fichier log vidé: {LOG_DEV_FILE}")
        # else:
        #     print(f"⚠️ [LOG] Fichier log inexistant: {LOG_DEV_FILE}")
    except Exception as e:
        # print(f"❌ [LOG] Erreur lors de la suppression du fichier log: {e}")
        pass





def find_pythonw():
    base_dir = os.path.dirname(sys.executable)
    candidate = os.path.join(base_dir, "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path.strip('"'), "pythonw.exe")
        if os.path.isfile(candidate):
            # print(f"✅ [LOG] pythonw.exe trouvé: {candidate}")
            return candidate
    return None





# ==========================================================
# 🔹 CLASSE GESTION DES DÉPENDANCES
# ==========================================================

class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():
        python_exe = sys.executable
        spec = importlib.util.find_spec("win32api")

        if spec:
            # print("pywin32 déjà installé")
            WRITE_LOG_DEV_FILE("pywin32 already installed", "INFO")
            return True

        # print("Installation de pywin32...")
        WRITE_LOG_DEV_FILE("Installing pywin32...", "INFO")
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]

        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    # print(f"Suppression de {folder}")
                    WRITE_LOG_DEV_FILE(f"Removed {folder}", "INFO")
                except PermissionError:
                    # print(f"Impossible de supprimer {folder} (fermez IDE/console)")
                    WRITE_LOG_DEV_FILE(f"Impossible de supprimer {folder} (fermez IDE/console)", "ERROR")
        try:
            subprocess.run( [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"], check=True,  stdout=subprocess.DEVNULL,  stderr=subprocess.DEVNULL)
            # print("pywin32 installé avec succès")
            WRITE_LOG_DEV_FILE("pywin32 installed successfully", "INFO")
        except subprocess.CalledProcessError:
            # print("Échec installation pywin32")
            WRITE_LOG_DEV_FILE("Failed to install pywin32", "ERROR")
            return False

        postinstall_script = Path(python_exe).parent / "Scripts" / "pywin32_postinstall.py"
        if postinstall_script.exists():
            try:
                subprocess.run(
                    [python_exe, str(postinstall_script), "-install"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # print("Post-installation terminée")
                WRITE_LOG_DEV_FILE("Post-installation completed", "INFO")
            except subprocess.CalledProcessError:
                # print("Échec post-installation pywin32")
                WRITE_LOG_DEV_FILE("Failed post-installation pywin32", "ERROR")
                return False

        # print("Redémarrage script dans 10s...")
        WRITE_LOG_DEV_FILE("Restarting script in 10s...", "INFO")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True

    
    
    
    
    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
        module_to_import = module_name or package
        install_spec = f"{package}=={version}" if version else package
        UPDATED_PIP_23_3 = False
        try:
            module = importlib.import_module(module_to_import)
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")
            return module
        except (ModuleNotFoundError, ImportError):
            # print(f"Installation de {package}...")
            WRITE_LOG_DEV_FILE(f"Installing {package}...", "INFO")

            if not UPDATED_PIP_23_3:
                try:
                    # print("Mise à jour pip...")
                    WRITE_LOG_DEV_FILE("Updating pip...", "INFO")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
                    UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    # print("Erreur mise à jour pip")
                    WRITE_LOG_DEV_FILE("Error updating pip", "ERROR")
                    sys.exit()

            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
                # print(f"{package} installé")
                WRITE_LOG_DEV_FILE(f"{package} installed", "INFO")
            except subprocess.CalledProcessError:
                # print(f"Erreur installation {package}")
                WRITE_LOG_DEV_FILE(f"Error installing {package}", "ERROR")
                sys.exit()

            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                # print(f"Erreur import {module_to_import}")
                WRITE_LOG_DEV_FILE(f"Error importing {module_to_import}", "ERROR")
                sys.exit()



# ==========================================================
# 🔹 CLASSE GESTION DES UPDATES
# ==========================================================

class UpdateManager:
    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            print("Version locale introuvable")
            WRITE_LOG_DEV_FILE("Local version not found", "ERROR")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            WRITE_LOG_DEV_FILE("Error reading local version", "ERROR")
            print("Erreur lecture version locale")
            return None




    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            # print("Téléchargement mise à jour depuis serveur")
            WRITE_LOG_DEV_FILE("Downloading update from server", "INFO")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests
                r = requests.get(zip_url, stream=True, timeout=60, verify=False)
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                # print("ZIP téléchargé avec succès")
                WRITE_LOG_DEV_FILE("ZIP downloaded successfully", "INFO")

                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    # print("Ancien dossier cible supprimé")
                    WRITE_LOG_DEV_FILE("Old target directory removed", "INFO")

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                # print("Extraction ZIP temporaire terminée")
                WRITE_LOG_DEV_FILE("Temporary ZIP extraction completed", "INFO")

                extracted_root = next( os.path.join(tmpdir, d)  for d in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, d)) )

                extracted_dir = extracted_root
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                        # print(f"Sous-dossier extrait : {extract_subdir}")
                        WRITE_LOG_DEV_FILE(f"Subdirectory extracted: {extract_subdir}", "INFO")

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                for item in os.listdir(extracted_dir):
                    s = os.path.join(extracted_dir, item)
                    d = os.path.join(target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.move(s, d)
                    else:
                        shutil.move(s, d)

                # print(f"Extraction terminée dans : {target_dir}")
                WRITE_LOG_DEV_FILE(f"Extraction completed in: {target_dir}", "INFO")
                return True

        except Exception:
            # print("Erreur téléchargement/extraction update")
            WRITE_LOG_DEV_FILE("Error downloading/extracting update", "ERROR")
            raise


    @staticmethod
    def check_and_update():

        
        # print("🔍 Checking for updates...")
        WRITE_LOG_DEV_FILE("Checking for updates", "INFO")

        import requests

        url = "https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k=e21c5f27e3e2561ad0d929f7373a4116ce961f52474183e5fd9e3863018d5d7e"
        DownloadFiles = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"
        

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"🌐 Attempt {attempt}/{max_attempts} → Sending request...")
                response = requests.get(url, timeout=10)

                # 🔎 Affichage de la réponse
                # print("📡 Response received!")
                # print(f"➡️ Status Code: {response.status_code}")
                # print("📄 Raw Response Text:")
                # print(response.text)

                if response.status_code != 200:
                    # print(f"❌ Server returned error status {response.status_code}")
                    WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Failed to fetch version.json (status {response.status_code})", "ERROR")
                    if attempt < max_attempts:
                        print("⏳ Retrying in 2 seconds...")
                        time.sleep(2)
                        continue
                    return True

                # print("🧠 Parsing JSON...")
                data = response.json()
                # print("🗂 Parsed JSON data:")
                # print(data)

                server_program = data.get("version")
                server_ext = data.get("version_Extention")

                local_program = UpdateManager._read_local_version(os.path.join("config", "version.txt"))
                local_ext = UpdateManager._read_local_version(os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt"))

                # print(f"📦 Local program version: {local_program}")
                # print(f"☁️ Server program version: {server_program}")

                if not local_program or local_program != server_program:
                    # print("⬇️ New program version detected! Downloading update...")
                    WRITE_LOG_DEV_FILE("Required program update", "INFO")
                    UpdateManager._download_and_extract(DownloadFiles, ROOT_DIR, clean_target=False, extract_subdir=None)
                    # print("✅ Program updated successfully!")
                    return True

                # print(f"🔌 Local extension version: {local_ext}")
                # print(f"☁️ Server extension version: {server_ext}")

                if not local_ext or local_ext != server_ext:
                    # print("⬇️ New extension version detected! Updating tools...")
                    WRITE_LOG_DEV_FILE("Required extensions update", "INFO")
                    tools_dir = TOOLS_DIR
                    if not os.path.exists(tools_dir):
                        os.makedirs(tools_dir)
                        # print("📁 Tools directory created")

                    UpdateManager._download_and_extract(DownloadFiles, tools_dir, clean_target=True, extract_subdir="tools")
                    # print("✅ Extensions updated successfully!")
                    return True

                # print("🎉 Application is up-to-date! No update needed.")
                WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")
                return False

            except Exception as e:
                # print(f"💥 Attempt {attempt}: Critical update error → {e}")
                WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Critical update error: {e}", "ERROR")
                if attempt < max_attempts:
                    # print("🔁 Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                # print("🚫 Update failed after multiple attempts.")
                return True




# le programme va runing dans une interface logique et capable

# ==========================================================
# 🔹 INITIALISATION DÉPENDANCES
# ==========================================================

def initialize_dependencies():
    # print("Initialisation des dépendances")

    WRITE_LOG_DEV_FILE("Initialisation des dépendances" , level="INFO")

    DependencyManager.install_and_verify_pywin32()

    global requests, urllib3, PyQt6, cryptography_module, psutil, pytz, tqdm, platformdirs, selenium
    requests = DependencyManager.install_and_import("requests")
    urllib3 = DependencyManager.install_and_import("urllib3", version="2.2.3")
    if urllib3:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    PyQt6 = DependencyManager.install_and_import("PyQt6", version="6.7.0", required_import="QtCore")
    cryptography_module = DependencyManager.install_and_import("cryptography", version="3.3.2")
    psutil = DependencyManager.install_and_import("psutil")
    pytz = DependencyManager.install_and_import("pytz")
    tqdm = DependencyManager.install_and_import("tqdm")
    platformdirs = DependencyManager.install_and_import("platformdirs")
    selenium = DependencyManager.install_and_import("selenium", required_import="webdriver", version="4.27.1")


# ==========================================================
# 🔹 MAIN
# # ==========================================================




def main():
    # print("Lancement de l'application principale")
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )

    try:
        clear_log()
        WRITE_LOG_DEV_FILE("Démarrage application principale", level="INFO")

        initialize_dependencies()
    

        pythonw_path = find_pythonw()
        if not pythonw_path:
            # DevLogger.critical("pythonw.exe introuvable")
            # print("pythonw.exe introuvable")
            WRITE_LOG_DEV_FILE("pythonw.exe not found", "ERROR")
            sys.exit(1)
        
        # pythonw_path=r"C:\Users\tec-d\.pyenv\pyenv-win\versions\3.8.0\python.exe"
        
        print("pythonw_path:", pythonw_path)
        # sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')
        # sys.stdin = open(os.devnull, 'r')
        
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        updated = UpdateManager.check_and_update()
        # print("updated:", updated)
        # if updated:
        #     print("UPDATE EFFECTUÉ")
        #     WRITE_LOG_DEV_FILE("Update completed", "INFO")
        # else:
        #     print("APPLICATION À JOUR")
        #     WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")

        if len(sys.argv) == 1:
            # print("Lancement de l'application principale")
            WRITE_LOG_DEV_FILE("Launching main application", "INFO")
            encrypted_key, secret_key = generate_encrypted_key()
            # ❌ Ne jamais logger ces clés

            script_path = SCRIPT_DIR / "src" / "AppV2.pyc"
            if script_path.is_file():
                subprocess.run(
                    [sys.executable, str(script_path), encrypted_key, secret_key],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # print("Script principal introuvable")
                WRITE_LOG_DEV_FILE("Main script not found", "ERROR")
                sys.exit(1)

    
    except Exception as e:
        print(f"Erreur fatale application: {e}")
        # Pour afficher plus de détails sur l'erreur
        print("Détails de l'erreur:")
        traceback.print_exc()  
        
        # Écriture dans le log
        WRITE_LOG_DEV_FILE(f"Fatal application error: {e}", "ERROR")
        
        # Pour conserver aussi la trace dans les logs
        error_details = traceback.format_exc()
        WRITE_LOG_DEV_FILE(f"Error details:\n{error_details}", "ERROR")
        
        sys.exit(1)  # Quitte l'application avec code d'erreur
        



if __name__ == "__main__":
    main()


# Nethwork Types Geographic :
# 1- LAN : Local Area Network C est un réseau local qui relie les ordinateurs et les périphériques d'un même réseau local (LAN) à l'aide de câbles ou de connexion sans fil.
# 2- WAN : Wide Area Network C'est un réseau qui couvre une grande zone géographique, comme un pays ou un continent, en reliant des réseaux locaux (LAN) à distance.
# 3- MAN : Metropolitan Area Network C'est un réseau qui couvre une zone géographique plus petite qu'un WAN, comme une ville ou un district, en reliant des réseaux locaux (LAN) à distance.
# 4- PAN : Personal Area Network C'est un réseau qui couvre une zone personnelle, comme une maison ou un bureau, en reliant des réseaux locaux (LAN) à distance.
# 5- SAN : Storage Area Network C'est un réseau qui permet de stocker des données sur un réseau de serveurs de stockage centralisé, permettant aux utilisateurs de partager et d'accéder aux données en temps réel.
# 6- CAN : Central Area Network C'est un réseau qui couvre une zone centrale, comme une ville ou un quartier, en reliant des réseaux locaux (LAN) à distance.





# RJ-45 : C'est un type de câble utilisé pour connecter des périphériques à un réseau Ethernet. Le câble RJ-45 est composé de 8 paires de fils conducteurs, qui sont utilisés pour transmettre des données sur le réseau.
# binary System : C'est un système de numération qui utilise seulement deux chiffres, 0 et 1, pour représenter les nombres. Le système binaire est utilisé pour coder les données informatiques et est la base du fonctionnement des ordinateurs.

# Packet tracer : C'est un outil de diagnostic réseau qui permet de visualiser et d'analyser les paquets de données qui circulent sur un réseau. Il permet de détecter les problèmes de réseau et de comprendre comment les données sont transmises entre les différents appareils connectés au réseau.
# DNS : C'est un protocole de communication utilisé pour la resolution de noms de domaine. Il permet de convertir des noms de domaine en adresses IP, et vice versa.

# Packet Tracer 9.0.0 Ubuntu 64bit
# CCNA : This is a certification offered by Cisco Systems, a leading provider of networking solutions. The CCNA certification is designed for network professionals who want to demonstrate their knowledge and skills in designing, implementing, and troubleshooting basic network infrastructure.
# CISCO : This is a security framework developed by the Center for Internet Security (CIS) to help organizations improve their security posture. It provides guidelines and best practices for securing various types of systems, including servers, workstations, and mobile devices.


# Python : Python is a high-level programming language that is known for its simplicity and readability. It is widely used for web development, data analysis, machine learning, and scientific computing. Python is also known for its extensive library of modules and packages, which make it easy to add functionality to your code.
# JavaScript : JavaScript is a programming language that is used to create interactive web pages. It is a client-side scripting language, which means that it runs on the user's web browser, rather than on a server. JavaScript is widely used for creating dynamic and interactive web applications, such as forms, animations, and games.
# PHP : PHP is a server-side scripting language that is used to create dynamic web pages. It is a popular choice for web development because it is easy to use and has a large community of developers who contribute to its development. PHP is often used in conjunction with HTML and CSS to create web pages that are interactive and dynamic.
# HTML : HTML stands for Hypertext Markup Language and is the standard markup language for creating web pages. It is used to structure the content of a web page and define the layout and formatting of the page. HTML is the foundation of web development and is used in conjunction with CSS and JavaScript to create interactive and dynamic web pages.
# CSS : CSS stands for Cascading Style Sheets and is used to define the presentation of a web page. It is used to control the layout, colors, fonts, and other visual aspects of a web page. CSS is used in conjunction with HTML to create web pages that are visually appealing and easy to navigate.
# SQL : SQL stands for Structured Query Language and is a programming language used to manage and manipulate relational databases. It is used to perform tasks such as creating, updating, and deleting data, as well as querying and retrieving data from the database. SQL is widely used in web development to store and retrieve data from databases.
# C : C is a general-purpose programming language that is widely used for system programming, game development, and embedded systems. It is a low-level language that provides direct access to hardware and memory, making it efficient for performance-critical applications. C is also used as a foundation for other programming languages, such as C++ and Objective-C.
# C++ : C++ is a general-purpose programming language that is an extension of the C programming language. It is widely used for system programming, game development, and scientific computing. C++ provides object-oriented programming features, such as classes and inheritance, which make it easier to create complex and modular code. C++ is also used as a foundation for other programming languages, such as Java and C#.
# GO : Go is a programming language that was developed by Google. It is designed to be simple, efficient, and easy to use. Go is often used for system programming, web development, and data analysis. It is known for its strong support for concurrent programming and its ability to compile quickly.
# R : R is a programming language and environment for statistical computing and graphics. It is widely used in academia and industry for data analysis, machine learning, and statistical modeling. R is known for its extensive library of statistical and graphical functions, as well as its ability to handle large datasets and complex statistical models.
# JAVA : Java is a programming language that is widely used for developing enterprise-level applications, mobile applications, and web applications. It is known for its platform independence, which means that Java code can run on any device that has a Java Virtual Machine (JVM). Java is also used as a foundation for other programming languages, such as Scala and Kotlin.
# C# : C# is a programming language that is widely used for developing Windows applications, web applications, and mobile applications. It is a strongly typed, object-oriented language that is designed to be easy to use and maintain. C# is often used in conjunction with the .NET framework, which provides a wide range of libraries and tools for building applications.



# Typologies Nethworking :
# BUS Topology : The bus typology is a network topology in which all devices are connected to a single cable, known as a bus. In this topology, data is transmitted in a single direction, from one device to another, and then back to the source device. The bus typology is simple and cost-effective, but it is not very reliable, as a failure in one device can cause the entire network to fail.
# Ring Topology : The ring typology is a network topology in which devices are connected in a circular arrangement. In this topology, data is transmitted in a single direction around the ring, and each device is responsible for relaying the data to the next device in the ring. The ring typology is reliable and efficient, but it can be difficult to troubleshoot and maintain.
# Star Topology : The star typology is a network topology in which all devices are connected to a central hub or switch. In this topology, data is transmitted from one device to another through the hub or switch. The star typology is reliable and easy to manage, but it can be expensive to implement, as it requires a central hub or switch for each device.
# Mesh Topology : The mesh typology is a network topology in which all devices are connected to each other. In this topology, data is transmitted directly between devices, without the need for a central hub or switch. The mesh typology is highly reliable and secure, but it can be complex and expensive to implement, as it requires a separate connection between each device.


# Model OSI :
# Layer 1 - Physical Layer : The physical layer is the lowest layer of the OSI model. It handles the physical transmission of data, such as the transmission of bits over copper or fiber optic cables.
# Layer 2 - Data Link Layer : The data link layer is the second layer of the OSI model. It handles the transmission of data between devices, such as the transmission of packets over a network.
# Layer 3 - Network Layer : The network layer is the third layer of the OSI model. It handles the transmission of data between networks, such as the transmission of packets over the internet.
# Layer 4 - Transport Layer : The transport layer is the fourth layer of the OSI model. It handles the transmission of data between applications, such as the transmission of packets over TCP/IP.
# Layer 5 - Session Layer : The session layer is the fifth layer of the OSI model. It handles the transmission of data between sessions, such as the transmission of packets over SSH.
# Layer 6 - Presentation Layer : The presentation layer is the sixth layer of the OSI model. It handles the presentation of data, such as the presentation of data over HTML.
# Layer 7 - Application Layer : The application layer is the seventh layer of the OSI model. It handles the presentation of data, such as the presentation of data over HTML.



# Model TCP/IP :
# The TCP/IP model is a simplified version of the OSI model, with only four layers:
# Layer 1 - Network Interface Layer : The network interface layer is the lowest layer of the TCP/IP model. It handles the physical transmission of data, such as the transmission of bits over copper or fiber optic cables.
# Layer 2 - Transport Layer : The transport layer is the second layer of the TCP/IP model. It handles the transmission of data between devices, such as the transmission of packets over a network.
# Layer 3 - Internet Layer : The internet layer is the third layer of the TCP/IP model. It handles the transmission of data between networks, such as the transmission of packets over the internet.
# Layer 4 - Application Layer : The application layer is the fourth layer of the TCP/IP model. It handles the presentation of data, such as the presentation of data over HTML.


# TCP VS UDP :
# TCP : TCP is a connection-oriented protocol that is used to transmit data over a network. It is reliable and provides a high level of data integrity and security.
# UDP : UDP is a connectionless protocol that is used to transmit data over a network. It is not reliable and provides a low level of data integrity and security.



# Model OSI - Data Name :
# Layer 1 - Physical Layer : Bits
# Layer 2 - Data Link Layer : Frames
# Layer 3 - Network Layer : Packets
# Layer 4 - Transport Layer : Segments
# Layer 5 - Session Layer : Data 
# Layer 6 - Presentation Layer : Data
# Layer 7 - Application Layer : Data


# Model OSI - Device Name :
# Layer 1 - Physical Layer : Cable , Hub , Repeater
# Layer 2 - Data Link Layer : Switch , Bridge
# Layer 3 - Network Layer : Router
# Layer 4 - Transport Layer : Firewall
# Layer 5 - Session Layer : Gateway / SSL Device
# Layer 6 - Presentation Layer : Firewall
# Layer 7 - Application Layer : Proxy / Server / WAF


# Cables :
# Cables are the physical connection between two devices. They are used to transmit data between devices.
# Cables are made of fiber optic or copper.
# Cables are used to transmit data between devices.
#  Types of cables :
#  Fiber optic cables : Cables made of fiber optic.
#  Copper cables : Cables made of copper.
#  Coaxial cables : Cables made of coaxial.
#  CAT5 cables : Cables made of CAT5.
#  CAT6 cables : Cables made of CAT6.
#  CAT7 cables : Cables made of CAT7.



#  Switch :
# A switch is a device that connects multiple devices together. It is used to transmit data between devices.
# Switches are used to transmit data between devices.
# Switches are used to connect multiple devices together.
# Switches are used to transmit data between devices.
# Switches are used to connect multiple devices together.
# Switches are used to transmit data between devices.



# Router :
# A router is a device that connects multiple devices together. It is used to transmit data between devices.
# Routers are used to transmit data between devices.
# Routers are used to connect multiple devices together.
# Routers are used to transmit data between devices.
# Routers are used to connect multiple devices together.
# Routers are used to transmit data between devices.







