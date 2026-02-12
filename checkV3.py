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



# ==========================================================
# 🔹 VARIABLES GLOBALES
# ==========================================================

TOOLS_DIR = Path("Tools")
EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"
LOG_DEV_FILE = os.path.abspath(os.path.join( "Log/LogDev/my_project.log"))



        
KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
KEY     = bytes.fromhex(KEY_HEX)


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




# ==========================================================
# 🔹 FONCTION DE CRYPTAGE
# ==========================================================

def generate_encrypted_key():
    from cryptography.fernet import Fernet
    secret_key = Fernet.generate_key()
    fernet = Fernet(secret_key)
    encrypted_message = fernet.encrypt(b"authorized")
    return encrypted_message.decode(), secret_key.decode()





# ==========================================================
# 🔹 FONCTION DE LOG
# ==========================================================

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





# ==========================================================
# 🔹 FONCTION DE SUPPRESSION DU FICHIER DE LOG
# ==========================================================

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



# ==========================================================
# 🔹 FONCTION DE RECHERCHE DE PYTHONW.EXE
# ==========================================================

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


    #=========================================================
    # 🔹 INSTALLATION ET VÉRIFICATION DE PYWIN32
    #=========================================================
    
    
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

    
    


    # =========================================================
    # 🔹 INSTALLATION ET IMPORTATION D'UNE DÉPENDANCE
    #=========================================================
    
    
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




def encrypt_message(plaintext: str, key_bytes: bytes):
    import os
    import base64
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    try:
        if len(key_bytes) != 32:
            WRITE_LOG_DEV_FILE("Invalid AES key length", level="ERROR")
            return False

        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted = base64.b64encode(iv + ciphertext).decode("utf-8")
        return encrypted

    except Exception as e:
        WRITE_LOG_DEV_FILE(f"AES-CBC encryption failed: {e}", level="ERROR")
        return False


class UpdateManager:

    # =========================================================
    # 🔹 LECTURE VERSION LOCALE
    # ==========================================================

    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            # print("Version locale introuvable")
            WRITE_LOG_DEV_FILE("Local version not found", "ERROR")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            WRITE_LOG_DEV_FILE("Error reading local version", "ERROR")
            # print("Erreur lecture version locale")
            return None



    # =========================================================
    # 🔹 TÉLÉCHARGEMENT ET EXTRACTION DE L'UPDATE
    # ==========================================================
    
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


    # =========================================================
    # 🔹 FUNCTION CHECK AND UPDATE
    # ==========================================================

    @staticmethod
    def check_and_update():
        WRITE_LOG_DEV_FILE("Checking for updates", "INFO")

        import requests

        date_plain = datetime.datetime.now().strftime("%Y-%m-%d")
        # print("📅 Date (plain):", date_plain)

        date_encrypted = encrypt_message(date_plain, KEY)

        if not date_encrypted:
            WRITE_LOG_DEV_FILE("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")  # Arrêt immédiat

        url = "https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}" 

        DownloadFiles = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"


        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Failed to fetch version.json (status {response.status_code})", "ERROR")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    sys.exit("❌ Server unreachable or error, exiting program.")  # Arrêt si échec après max attempts

                data = response.json()
                server_program = data.get("version")
                server_ext = data.get("version_Extention")

                local_program = UpdateManager._read_local_version(os.path.join("config", "version.txt"))
                local_ext = UpdateManager._read_local_version(os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt"))

                update_done = False  # Pour vérifier si une update a été faite

                # Vérifier update programme
                if not local_program or local_program != server_program:
                    WRITE_LOG_DEV_FILE("Required program update", "INFO")
                    if UpdateManager._download_and_extract(DownloadFiles, ROOT_DIR, clean_target=False, extract_subdir=None):
                        update_done = True
                    else:
                        sys.exit("❌ Program update failed, exiting program.")

                # Vérifier update extensions
                if not local_ext or local_ext != server_ext:
                    WRITE_LOG_DEV_FILE("Required extensions update", "INFO")
                    tools_dir = TOOLS_DIR
                    if not os.path.exists(tools_dir):
                        os.makedirs(tools_dir)

                    if UpdateManager._download_and_extract(DownloadFiles, tools_dir, clean_target=True, extract_subdir="tools"):
                        update_done = True
                    else:
                        sys.exit("❌ Extensions update failed, exiting program.")

                # Si tout est OK et à jour
                if not update_done:
                    WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")
                    return False  # Pas de mise à jour nécessaire

                return True  # Update effectué avec succès

            except Exception as e:
                WRITE_LOG_DEV_FILE(f"Attempt {attempt}: Critical update error: {e}", "ERROR")
                if attempt < max_attempts:
                    time.sleep(2)
                    continue
                sys.exit(f"❌ Critical update error after {max_attempts} attempts, exiting program: {e}")





# ==========================================================
# 🔹 FUNCTION INITIALISATION DÉPENDANCES
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





# le programme is runing dans une interface logique et capable de renitailisation 
#  أبسط شرح للراوتنج Routing | الفرق بين Static Routing و Dynamic Routing 

def main():
    # =========================================================
    # 🔹 DÉMARRAGE DE L'APPLICATION PRINCIPALE
    # ==========================================================

    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 0)


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
        
        # print("pythonw_path:", pythonw_path)
        # sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')
        # sys.stdin = open(os.devnull, 'r')
        
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        updated = UpdateManager.check_and_update()
        # print("updated:", updated)
        if updated:
            # print("UPDATE EFFECTUÉ")
            WRITE_LOG_DEV_FILE("Update completed", "INFO")
        else:
            # print("APPLICATION À JOUR")
            WRITE_LOG_DEV_FILE("Application up-to-date", "INFO")

        if len(sys.argv) == 1:
            # print("Lancement de l'application principale")
            WRITE_LOG_DEV_FILE("Launching main application", "INFO")
            encrypted_key, secret_key = generate_encrypted_key()
            # ❌ Ne jamais logger ces clés

            script_path = SCRIPT_DIR / "src" / "AppV2.py"
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
        # print(f"Erreur fatale application: {e}")
        # Pour afficher plus de détails sur l'erreur
        # print("Détails de l'erreur:")
        traceback.print_exc()  
        # Écriture dans le log
        WRITE_LOG_DEV_FILE(f"Fatal application error: {e}", "ERROR")
        
        # Pour conserver aussi la trace dans les logs
        error_details = traceback.format_exc()
        WRITE_LOG_DEV_FILE(f"Error details:\n{error_details}", "ERROR")
        sys.exit(1)  
        



if __name__ == "__main__":
    main()








# Routing in Networking: Static vs Dynamic Routing
# Routing is the process of selecting paths in a network along which to send data packets. There are two primary types of routing: static routing and dynamic routing.
# 1. Static Routing:
# - In static routing, the routes are manually configured by a network administrator. The administrator specifies the paths that data packets should take to reach their destination.
# - Static routes do not change unless manually updated. If there is a change in the network topology (e.g., a link failure), the static route will not adapt, and manual intervention is required to update the routing table.
# - Static routing is simple and has low overhead since it does not require the exchange of routing information between routers. However, it is not scalable for large networks and can lead to issues if the network changes frequently.
# 2. Dynamic Routing:
# - In dynamic routing, routers automatically discover and maintain routes by exchanging routing information with each other. This is done using routing protocols such as OSPF, EIGRP, or BGP.
# - Dynamic routes can adapt to changes in the network topology. If a link fails, the routing protocol will automatically recalculate the routes and find an alternative path to the destination.
# - Dynamic routing is more scalable and flexible than static routing, making it suitable for larger and more complex networks. However, it has higher overhead due to the need for routers to exchange routing information and maintain routing tables.    


# ALL Commands In Routing : 
# 1. show ip route: Displays the routing table of a router, showing all known routes and their associated metrics.
# 2. show ip route [destination]: Displays the routing information for a specific destination IP address.
# 3. show ip route [protocol]: Displays routes learned through a specific routing protocol (e.g., OSPF, EIGRP).
# 4. show ip route [interface]: Displays routes associated with a specific interface.
# 5. enable: Enters privileged EXEC mode, allowing access to more advanced commands.
# 6. configure terminal: Enters global configuration mode, where you can configure routing protocols and other settings.
# 7. ip route [destination] [mask] [next-hop]: Configures a static route to a specific destination network, specifying the subnet mask and the next-hop IP address.
# 8. router [protocol]: Enters routing protocol configuration mode for a specific protocol (e.g., OSPF, EIGRP).
# 9. network [network] [mask]: Specifies the networks that should be advertised by the routing protocol.
# 10. no ip route [destination] [mask] [next-hop]: Removes a previously configured static route.
# 11. no router [protocol]: Disables a routing protocol.
# 12. no network [network] [mask]: Removes a network from the routing protocol's advertisement list.
# 13. debug ip routing: Enables debugging for IP routing, providing detailed information about routing operations and errors.
# 14. clear ip route *: Clears all routes from the routing table, effectively resetting the routing configuration.
# 15. show running-config: Displays the current running configuration of the router, including all configured routes and routing protocols.
# 16. show startup-config: Displays the startup configuration of the router, which is the configuration that will be loaded when the router boots up.
# 17. copy running-config startup-config: Copies the current running configuration to the startup configuration, ensuring that the configuration is saved and will be loaded on the next boot.
# 18. write memory: Saves the current running configuration to non-volatile storage, making it persistent across reboots.
# 19. reload: Reboots the router, loading the startup configuration.
# 20. exit: Exits the current mode (e.g., global configuration mode, interface configuration mode) and returns to the previous mode.
# 21. end: Exits the current mode and returns to privileged EXEC mode.
# 22. show interfaces: Displays the status and configuration of all interfaces on the router.
# 23. show interfaces [interface]: Displays the status and configuration of a specific interface.
# 24. show interfaces status: Displays the status of all interfaces, including whether they are up or down.
# 25. show interfaces [interface] status: Displays the status of a specific interface, including whether it is up or down.
# 26. show ip interface brief: Displays a brief summary of all IP interfaces, including their IP addresses, subnet masks, and administrative status.
# 27. show ip interface [interface]: Displays the detailed configuration and status of a specific IP interface.
# 28. show ip protocols: Displays the status and configuration of all routing protocols running on the router.
# 29. show ip protocols [protocol]: Displays the status and configuration of a specific routing protocol.
# 30. show ip protocol [protocol] neighbors: Displays the neighbors of a specific routing protocol, showing the IP addresses and status of neighboring routers.
# 31. show ip protocol [protocol] routes: Displays the routes learned through a specific routing protocol, including the destination network, next-hop IP address, and metric.
# 32. show ip protocol [protocol] database: Displays the routing database of a specific routing protocol, showing the routes and their associated metrics.
# 33. show ip protocol [protocol] redistribute [protocol]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol and the redistribution metric.
# 34. show ip protocol [protocol] summary: Displays a summary of the routing protocol, including the number of routes learned, the number of neighbors, and the uptime of the protocol.
# 35. show ip protocol [protocol] redistribute [protocol] metric [metric]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the redistribution metric, and the metric value.
# 36. show ip protocol [protocol] redistribute [protocol] route-map [route-map]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, and the route-map configuration.
# 37. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, and the redistribution metric.
# 38. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, the redistribution metric, and whether subnets are included in the redistribution.
# 39. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, the redistribution metric, whether subnets are included in the redistribution, and the route-map used for filtering the redistributed routes.
# 40. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric]: Displays the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, the redistribution metric, whether subnets are included in the redistribution, the route-map used for filtering the redistributed routes, and the metric value for the redistributed routes.
# 41. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary: Displays a summary of the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, the redistribution metric, whether subnets are included in the redistribution, the route-map used for filtering the redistributed routes, the metric value for the redistributed routes, and a summary of the redistribution configuration.
# 42. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing the source protocol, the route-map used for redistribution, the route-map configuration, the redistribution metric, whether subnets are included in the redistribution, the route-map used for filtering the redistributed routes, the metric value for the redistributed routes, and a detailed summary of the redistribution configuration.
# 43. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | include [keyword]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing only lines that include a specific keyword.
# 44. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | exclude [keyword]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing only lines that do not include a specific keyword.
# 45. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | begin [keyword]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, starting from the first line that includes a specific keyword.
# 46. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | end [keyword]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, ending at the last line that includes a specific keyword.
# 47. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | count [count]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing only the first [count] lines.
# 48. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | more: Displays a detailed summary of the redistribution configuration for a specific routing protocol, pausing after each screen of output.
# 49. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | less: Displays a detailed summary of the redistribution configuration for a specific routing protocol, allowing you to scroll through the output using the less pager.
# 50. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | grep [pattern]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing only lines that match a specific pattern.
# 51. show ip protocol [protocol] redistribute [protocol] route-map [route-map] metric [metric] subnets route-map [route-map] metric [metric] summary detail | awk [pattern]: Displays a detailed summary of the redistribution configuration for a specific routing protocol, showing only lines that match a specific pattern using the awk command.


# Note: The above commands are examples and may vary based on the specific router model and operating system. Always refer to the documentation for your specific router for accurate command syntax and options.
# 1. show ip route: Displays the current routing table, showing the destination network, next hop, and metric for each route.
# 2. show ip route [network]: Displays the routing table for a specific network, showing the next hop and metric for each route to that network.
# 3. show ip route [protocol]: Displays the routing table for a specific routing protocol (e.g., OSPF, EIGRP), showing the routes learned through that protocol.
# 4. show ip route [interface]: Displays the routing table for a specific interface, showing the routes associated with that interface.
# 5. show ip route [route-type]: Displays the routing table for a specific route                        type (e.g., connected, static, dynamic), showing the routes of that type.
# 6. show ip route [next-hop]: Displays the routing table for a specific next hop, showing the routes that use that next hop.
# 7. show ip route [metric]: Displays the routing table for a specific metric, showing the routes with that metric.
# 8. show ip route [destination] [mask]: Displays the routing table for a specific destination network and subnet mask, showing the next hop and metric for each route to that network.
# 9. show ip route [destination] [mask] [protocol]: Displays the routing table for a specific destination network, subnet mask, and routing protocol, showing the next hop and metric for each route to that network learned through that protocol.
# 10. show ip route [destination] [mask] [interface]: Displays the routing table for a specific destination network, subnet mask, and interface, showing the next hop and metric for each route to that network associated with that interface.
# 11. show ip route [destination] [mask] [route-type]: Displays the routing table for a specific destination network, subnet mask, and route type, showing the next hop and metric for each route to that network of that type.
# 12. show ip route [destination] [mask] [next-hop]: Displays the routing table for a specific destination network, subnet mask, and next hop, showing the routes to that network that use that next hop.
# 13. show ip route [destination] [mask] [metric]: Displays the routing table for a specific destination network, subnet mask, and metric, showing the routes to that network with that metric.
# 14. show ip route [destination] [mask] [protocol] [interface]: Displays the routing table for a specific destination network, subnet mask, routing protocol, and interface, showing the next hop and metric for each route to that network learned through that protocol and associated with that interface.
# 15. show ip route [destination] [mask] [protocol] [route-type]: Displays the routing table for a specific destination network, subnet mask, routing protocol, and route type, showing the next hop and metric for each route to that network learned through that protocol of that type.              
# 16. show ip route [destination] [mask] [protocol] [next-hop]: Displays the routing table for a specific destination network, subnet mask, routing protocol, and next hop, showing the routes to that network learned through that protocol that use that next hop.
# 17. show ip route [destination] [mask] [protocol] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, and metric, showing the routes to that network learned through that protocol with that metric.
# 18. show ip route [destination] [mask] [interface] [route-type]: Displays the routing table for a specific destination network, subnet mask, interface, and route type, showing the next hop and metric for each route to that network associated with that interface of that type.
# 19. show ip route [destination] [mask] [interface] [next-hop]: Displays the routing table for a specific destination network, subnet mask, interface, and next hop, showing the routes to that network associated with that interface that use that next hop.
# 20. show ip route [destination] [mask] [interface] [metric]: Displays the routing table for a specific destination network, subnet mask, interface, and metric, showing the routes to that network associated with that interface with that metric.
# 21. show ip route [destination] [mask] [route-type] [next-hop]: Displays the routing table for a specific destination network, subnet mask, route type, and next hop, showing the routes to that network of that type that use that next hop.
# 22. show ip route [destination] [mask] [route-type] [metric]: Displays the routing table for a specific destination network, subnet mask, route type, and metric, showing the routes to that network of that type with that metric.   
# 23. show ip route [destination] [mask] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, next hop, and metric, showing the routes to that network that use that next hop with that metric.
# 24. show ip route [destination] [mask] [protocol] [interface] [route-type]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, and route type, showing the next hop and metric for each route to that network learned through that protocol, associated with that interface, and of that type.
# 25. show ip route [destination] [mask] [protocol] [interface] [next-hop]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, and next hop, showing the routes to that network learned through that protocol, associated with that interface, and that use that next hop.
# 26. show ip route [destination] [mask] [protocol] [interface] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, and metric, showing the routes to that network learned through that protocol, associated with that interface, and with that metric.
# 27. show ip route [destination] [mask] [protocol] [route-type] [next-hop]: Displays the routing table for a specific destination network, subnet mask, routing protocol, route type, and next hop, showing the routes to that network learned through that protocol, of that type, and that use that next hop.
# 28. show ip route [destination] [mask] [protocol] [route-type] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, route type, and metric, showing the routes to that network learned through that protocol, of that type, and with that metric.
# 29. show ip route [destination] [mask] [interface] [route-type] [next-hop]: Displays the routing table for a specific destination network, subnet mask, interface, route type, and next hop, showing the routes to that network associated with that interface, of that type, and that use that next hop.
# 30. show ip route [destination] [mask] [interface] [route-type] [metric]: Displays the routing table for a specific destination network, subnet mask, interface, route type, and metric, showing the routes to that network associated with that interface, of that type, and with that metric.   
# 31. show ip route [destination] [mask] [interface] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, interface, next hop, and metric, showing the routes to that network associated with that interface that use that next hop with that metric.
# 32. show ip route [destination] [mask] [route-type] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, route type, next hop, and metric, showing the routes to that network of that type that use that next hop with that metric.
# 33. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, and next hop, showing the routes to that network learned through that protocol, associated with that interface, of that type, and that use that next hop.
# 34. show ip route [destination] [mask] [protocol] [interface] [route-type] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, and metric, showing the routes to that network learned through that protocol, associated with that interface, of that type, and with that metric.
# 35. show ip route [destination] [mask] [protocol] [route-type] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, route type, next hop, and metric, showing the routes to that network learned through that protocol, of that type, that use that next hop with that metric.
# 36. show ip route [destination] [mask] [interface] [route-type] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, interface, route type, next hop, and metric, showing the routes to that network associated with that interface, of that type, that use that next hop with that metric.
# 37. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, and metric, showing the routes to that network learned through that protocol, associated with that interface, of that type, that use that next hop with that metric.
# 38. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing the routes to that network learned through that protocol, associated with that interface, of that type, that use that next hop with that metric, and with additional details about each route.
# 39. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | include [keyword]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing only lines that include a specific keyword.
# 40. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | exclude [keyword]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing only lines that do not include a specific keyword.
# 41. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | begin [keyword]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, starting from the first line that includes a specific keyword.
# 42. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | end [keyword]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, ending at the last line that includes a specific keyword.
# 43. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | count [count]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing only the first [count] lines.
# 44. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | more: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, pausing after each screen of output.
# 45. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | less: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, allowing you to scroll through the output using the less pager.
# 46. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | grep [pattern]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing only lines that match a specific pattern using the grep command.
# 47. show ip route [destination] [mask] [protocol] [interface] [route-type] [next-hop] [metric] [detail] | awk [pattern]: Displays the routing table for a specific destination network, subnet mask, routing protocol, interface, route type, next hop, metric, and detail level, showing only lines that match a specific pattern using the awk command.         




# la defference entre IGP et EGP :
# IGP (Interior Gateway Protocol) and EGP (Exterior Gateway Protocol) are two types of routing protocols used in computer networks to exchange routing information between routers. The main difference between IGP and EGP lies in their scope and the type of networks they are designed to operate within.
# 1. IGP (Interior Gateway Protocol):
# - IGP is used for routing within a single autonomous system (AS), which is a collection of networks under a common administrative control. IGPs are designed to manage routing within an organization's internal network.
# - Examples of IGPs include OSPF (Open Shortest Path First), EIGRP (Enhanced Interior Gateway Routing Protocol), and RIP (Routing Information Protocol).
# - IGPs typically use metrics such as hop count, bandwidth, or delay to determine the best path for routing traffic within the AS. They are optimized for fast convergence and efficient routing within a single administrative domain.
# 2. EGP (Exterior Gateway Protocol):   
# - EGP is used for routing between different autonomous systems (ASes) on the internet. EGPs are designed to manage routing between different organizations or service providers.
# - The most common EGP is BGP (Border Gateway Protocol), which is the standard protocol used for routing between ASes on the internet.
# - EGPs typically use attributes such as AS path, next hop, and local preference to determine the best path for routing traffic between ASes. They are optimized for scalability and policy-based routing across the global internet.
# In summary, IGP and EGP are two types of routing protocols used in computer networks to exchange routing information between routers. IGP is used for routing within a single autonomous system, while EGP is used for routing between different autonomous systems on the internet.


# IGP : Distance Vector vs Link State :
# IGP (Interior Gateway Protocol) can be further categorized into two main types: Distance Vector and Link State protocols. The primary difference between these two types of IGPs lies in how they determine the best path for routing traffic within a network.
# 1. Distance Vector Protocols:   
# - Distance Vector protocols, such as RIP (Routing Information Protocol) and EIGRP (Enhanced Interior Gateway Routing Protocol), use a distance vector algorithm to determine the best path for routing traffic.
# - Distance Vector protocols exchange routing information in the form of distance vectors, which are lists of destination networks and their associated metrics (such as hop count or cost).
# - Each router maintains a routing table that contains the distance to each destination network and the next hop to reach that network. Routers periodically exchange their routing tables with their neighbors, allowing them to update their routing information based on the distance vectors received from their neighbors.
# - Distance Vector protocols are relatively simple to configure and manage, but they can be slower to converge and may be prone to routing loops if not properly configured.
# 2. Link State Protocols:   
# - Link State protocols, such as OSPF (Open Shortest Path First) and IS-IS (Intermediate System to Intermediate System), use a link state algorithm to determine the best path for routing traffic.    
# - Link State protocols exchange routing information in the form of link state advertisements (LSAs), which contain information about the state of each link in the network (such as bandwidth, delay, and reliability).
# - Each router maintains a link state database that contains information about the state of all links in the network. Routers use this information to construct a complete map of the network topology and calculate the best path to each destination network using algorithms such as Dijkstra's algorithm.
# - Link State protocols typically converge faster than Distance Vector protocols and are less prone to routing loops, but they can be more complex to configure and manage due to the need to maintain a link state database and exchange LSAs with all routers in the network.
# In summary, IGP can be further categorized into Distance Vector and Link State protocols based on how they determine the best path for routing traffic within a network. Distance Vector protocols exchange routing information in the form of distance vectors, while Link State protocols exchange routing information in the form of link state advertisements.


# RIP : Routing Information Protocol
# EIGRP : Enhanced Interior Gateway Routing Protocol
# OSPF : Open Shortest Path First
# IS-IS : Intermediate System to Intermediate System

# OSPF (Open Shortest Path First) is a widely used Interior Gateway Protocol (IGP) that operates within a single autonomous system (AS). It is a link-state routing protocol that uses the Dijkstra algorithm to calculate the shortest path to each destination network. OSPF is designed for fast convergence and efficient routing within a single administrative domain. It supports hierarchical routing through the use of areas, allowing for scalability in larger networks. OSPF also supports authentication and can be used in both IPv4 and IPv6 networks.
# EIGRP (Enhanced Interior Gateway Routing Protocol) is a Cisco proprietary IGP that combines features of both distance vector and link-state protocols. It uses a distance vector algorithm to determine the best path for routing traffic, but it also maintains a topology table that contains information about all known routes in the network. EIGRP supports fast convergence and efficient routing within a single administrative domain. It also supports authentication and can be used in both IPv4 and IPv6 networks.
# RIP (Routing Information Protocol) is one of the oldest distance vector routing protocols. It uses hop count as its metric to determine the best path for routing traffic. RIP has a maximum hop count of 15, which limits its use in larger networks. It is relatively simple to configure and manage, but it can be slow to converge and is prone to routing loops if not properly configured. RIP is typically used in small networks or as a backup routing protocol.
# IS-IS (Intermediate System to Intermediate System) is a link-state routing protocol that operates within a single autonomous system (AS). It is similar to OSPF in terms of its functionality and features, but it uses a different protocol format and is often used in service provider networks. IS-IS supports hierarchical routing through the use of areas, allowing for scalability in larger networks. It also supports authentication and can be used in both IPv4 and IPv6 networks. IS-IS is known for its efficiency and scalability, making it a popular choice for large enterprise and service provider networks.
# In summary, OSPF, EIGRP, RIP, and IS-IS are all dynamic routing protocols that operate within a single autonomous system (AS). OSPF and IS-IS are link-state protocols that use the Dijkstra algorithm to calculate the shortest path to each destination network, while EIGRP is a hybrid protocol that combines features of both distance vector and link-state protocols. RIP is a distance vector protocol that uses hop count as its metric. Each protocol has its own strengths and weaknesses, and the choice of which protocol to use depends on the specific requirements of the network being designed.
# In summary, dynamic routing is a method of routing in which routers automatically exchange routing information with each other using routing protocols. Dynamic routes can adapt to changes in the network topology and are more scalable and flexible than static routes, but they have higher overhead due to the need for routers to exchange routing information and maintain routing tables.
# Dynamic routing is a method of routing in which routers automatically exchange routing information with each other using routing protocols. Dynamic routes can adapt to changes in the network topology and are more scalable and flexible than static routes, but they have higher overhead due to the need for routers to exchange routing information and maintain routing tables.

