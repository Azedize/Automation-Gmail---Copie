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
import json
import traceback


# ==========================================================
# 🔹 VARIABLES GLOBALES
# ==========================================================

TOOLS_DIR = Path("Tools")
# EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"
LOG_DEV_FILE = os.path.abspath(os.path.join("Log/LogDev/my_project.log"))


print("🚀 [INIT] Initialisation du script principal...")
KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
KEY = bytes.fromhex(KEY_HEX)


HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ==========================================================
# 🔹 FIX UTF-8 POUR WINDOWS CONSOLE
# ==========================================================

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


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


def _sanitize_log_value(value):
    text = str(value)
    return text[:200] if len(text) > 200 else text


def write_log_dev_file(message: str, level: str = "INFO", **context):
    try:
        log_path = Path(LOG_DEV_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": str(level).upper(),
            "event": str(message),
            "context": {
                str(key): _sanitize_log_value(value)
                for key, value in context.items()
            },
        }
        with open(LOG_DEV_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
    except Exception:
        pass


# ==========================================================
# 🔹 FONCTION DE SUPPRESSION DU FICHIER DE LOG
# ==========================================================


def clear_log():
    try:
        log_path = Path(LOG_DEV_FILE)
        if log_path.exists():
            open(log_path, "w", encoding="utf-8").close()
    except Exception as e:
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
    # =========================================================
    # 🔹 INSTALLATION ET VÉRIFICATION DE PYWIN32
    # =========================================================

    @staticmethod
    def install_and_verify_pywin32():
        python_exe = sys.executable
        spec = importlib.util.find_spec("win32api")

        if spec:
            # print("pywin32 déjà installé")
            write_log_dev_file("pywin32 already installed", "INFO")
            return True

        # print("Installation de pywin32...")
        write_log_dev_file("Installing pywin32...", "INFO")
        site_packages = Path(python_exe).parent / "Lib" / "site-packages"
        folders_to_remove = ["win32", "pywin32_system32"]

        for folder in folders_to_remove:
            folder_path = site_packages / folder
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    # print(f"Suppression de {folder}")
                    write_log_dev_file(f"Removed {folder}", "INFO")
                except PermissionError:
                    # print(f"Impossible de supprimer {folder} (fermez IDE/console)")
                    write_log_dev_file(
                        f"Impossible de supprimer {folder} (fermez IDE/console)",
                        "ERROR",
                    )
        try:
            subprocess.run(
                [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--force-reinstall",
                    "pywin32==305",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # print("pywin32 installé avec succès")
            write_log_dev_file("pywin32 installed successfully", "INFO")
        except subprocess.CalledProcessError:
            # print("Échec installation pywin32")
            write_log_dev_file("Failed to install pywin32", "ERROR")
            return False

        postinstall_script = (
            Path(python_exe).parent / "Scripts" / "pywin32_postinstall.py"
        )
        if postinstall_script.exists():
            try:
                subprocess.run(
                    [python_exe, str(postinstall_script), "-install"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                # print("Post-installation terminée")
                write_log_dev_file("Post-installation completed", "INFO")
            except subprocess.CalledProcessError:
                # print("Échec post-installation pywin32")
                write_log_dev_file("Failed post-installation pywin32", "ERROR")
                return False

        # print("Redémarrage script dans 10s...")
        write_log_dev_file("Restarting script in 10s...", "INFO")
        time.sleep(10)
        subprocess.run([python_exe, sys.argv[0]])
        sys.exit(0)
        return True

    # =========================================================
    # 🔹 INSTALLATION ET IMPORTATION D'UNE DÉPENDANCE
    # =========================================================

    @staticmethod
    def install_and_import(
        package, module_name=None, required_import=None, version=None
    ):
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
            write_log_dev_file(f"Installing {package}...", "INFO")

            if not UPDATED_PIP_23_3:
                try:
                    # print("Mise à jour pip...")
                    write_log_dev_file("Updating pip...", "INFO")
                    subprocess.check_call(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "pip==23.3",
                        ]
                    )
                    UPDATED_PIP_23_3 = True
                except subprocess.CalledProcessError:
                    # print("Erreur mise à jour pip")
                    write_log_dev_file("Error updating pip", "ERROR")
                    sys.exit()

            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", install_spec]
                )
                # print(f"{package} installé")
                write_log_dev_file(f"{package} installed", "INFO")
            except subprocess.CalledProcessError:
                # print(f"Erreur installation {package}")
                write_log_dev_file(f"Error installing {package}", "ERROR")
                sys.exit()

            try:
                return importlib.import_module(module_to_import)
            except ImportError as e:
                # print(f"Erreur import {module_to_import}")
                write_log_dev_file(f"Error importing {module_to_import}", "ERROR")
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
            write_log_dev_file("Invalid AES key length", level="ERROR")
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
        write_log_dev_file(f"AES-CBC encryption failed: {e}", level="ERROR")
        return False


class UpdateManager:
    # =========================================================
    # 🔹 LECTURE VERSION LOCALE
    # ==========================================================

    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            # print("Version locale introuvable")
            write_log_dev_file("Local version not found", "ERROR")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            write_log_dev_file("Error reading local version", "ERROR")
            # print("Erreur lecture version locale")
            return None

    # =========================================================
    # 🔹 TÉLÉCHARGEMENT ET EXTRACTION DE L'UPDATE
    # ==========================================================

    @staticmethod
    def _download_and_extract(
        zip_url, target_dir, clean_target=False, extract_subdir=None
    ):
        try:
            # print("Téléchargement mise à jour depuis serveur")
            write_log_dev_file("Downloading update from server", "INFO")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests

                r = requests.get(
                    zip_url, stream=True, headers=HEADER, timeout=60, verify=False
                )
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                # print("ZIP téléchargé avec succès")
                write_log_dev_file("ZIP downloaded successfully", "INFO")

                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    # print("Ancien dossier cible supprimé")
                    write_log_dev_file("Old target directory removed", "INFO")

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                # print("Extraction ZIP temporaire terminée")
                write_log_dev_file("Temporary ZIP extraction completed", "INFO")

                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )

                extracted_dir = extracted_root
                if extract_subdir:
                    candidate = os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(candidate):
                        extracted_dir = candidate
                        # print(f"Sous-dossier extrait : {extract_subdir}")
                        write_log_dev_file(
                            f"Subdirectory extracted: {extract_subdir}", "INFO"
                        )

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
                write_log_dev_file(f"Extraction completed in: {target_dir}", "INFO")
                return True

        except Exception:
            # print("Erreur téléchargement/extraction update")
            write_log_dev_file("Error downloading/extracting update", "ERROR")
            raise

    # =========================================================
    # 🔹 FUNCTION CHECK AND UPDATE
    # ==========================================================

    @staticmethod
    def check_and_update():
        write_log_dev_file("Checking for updates", "INFO")

        import requests

        date_plain = datetime.datetime.now().strftime("%Y-%m-%d")
        # print("📅 Date (plain):", date_plain)

        date_encrypted = encrypt_message(date_plain, KEY)

        if not date_encrypted:
            write_log_dev_file("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")  # Arrêt immédiat

        url = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"
        # DownloadFiles = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"
        DownloadFiles = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, headers=HEADER, timeout=10)

                if response.status_code != 200:
                    write_log_dev_file(
                        f"Attempt {attempt}: Failed to fetch version.json (status {response.status_code})",
                        "ERROR",
                    )
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    sys.exit(
                        "❌ Server unreachable or error, exiting program."
                    )  # Arrêt si échec après max attempts

                data = response.json()
                server_program = data.get("version")
                server_ext = data.get("version_Extention")

                local_program = UpdateManager._read_local_version(
                    os.path.join("config", "version.txt")
                )
                # local_ext = UpdateManager._read_local_version(os.path.join(EXTENSIONS_DIR_TEMPLETE, "version.txt"))

                update_done = False  # Pour vérifier si une update a été faite

                # Vérifier update programme
                if not local_program or local_program != server_program:
                    write_log_dev_file("Required program update", "INFO")
                    if UpdateManager._download_and_extract(
                        DownloadFiles, ROOT_DIR, clean_target=False, extract_subdir=None
                    ):
                        update_done = True
                    else:
                        sys.exit("❌ Program update failed, exiting program.")

                # # Vérifier update extensions
                # if not local_ext or local_ext != server_ext:
                #     write_log_dev_file("Required extensions update", "INFO")
                #     tools_dir = TOOLS_DIR
                #     if not os.path.exists(tools_dir):
                #         os.makedirs(tools_dir)

                #     if UpdateManager._download_and_extract(DownloadFiles, tools_dir, clean_target=True, extract_subdir="tools"):
                #         update_done = True
                #     else:
                #         sys.exit("❌ Extensions update failed, exiting program.")

                # Si tout est OK et à jour
                if not update_done:
                    write_log_dev_file("Application up-to-date", "INFO")
                    return False  # Pas de mise à jour nécessaire

                return True  # Update effectué avec succès

            except Exception as e:
                write_log_dev_file(
                    f"Attempt {attempt}: Critical update error: {e}", "ERROR"
                )
                if attempt < max_attempts:
                    time.sleep(2)
                    continue
                sys.exit(
                    f"❌ Critical update error after {max_attempts} attempts, exiting program: {e}"
                )


# ==========================================================
# 🔹 FUNCTION INITIALISATION DÉPENDANCES
# ==========================================================


def initialize_dependencies():
    write_log_dev_file("Initialisation des dépendances", level="INFO")

    # Installer pywin32 pour Windows
    DependencyManager.install_and_verify_pywin32()

    global \
        requests, \
        urllib3, \
        PyQt6, \
        cryptography_module, \
        psutil, \
        pytz, \
        tqdm, \
        platformdirs, \
        selenium
    global colorama, sqlalchemy

    requests = DependencyManager.install_and_import("requests")
    urllib3 = DependencyManager.install_and_import("urllib3", version="2.2.3")
    if urllib3:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    PyQt6 = DependencyManager.install_and_import(
        "PyQt6", version="6.7.0", required_import="QtCore"
    )
    cryptography_module = DependencyManager.install_and_import(
        "cryptography", version="3.3.2"
    )
    psutil = DependencyManager.install_and_import("psutil")
    pytz = DependencyManager.install_and_import("pytz")
    tqdm = DependencyManager.install_and_import("tqdm")
    platformdirs = DependencyManager.install_and_import("platformdirs")
    selenium = DependencyManager.install_and_import(
        "selenium", required_import="webdriver", version="4.27.1"
    )
    colorama = DependencyManager.install_and_import("colorama")
    sqlalchemy = DependencyManager.install_and_import("sqlalchemy")


def main():

    # =========================================================
    # 🔹 DÉMARRAGE DE L'APPLICATION PRINCIPALE
    # ==========================================================

    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    try:
        clear_log()
        write_log_dev_file("Démarrage application principale", level="INFO")

        initialize_dependencies()

        pythonw_path = find_pythonw()
        if not pythonw_path:
            write_log_dev_file("pythonw.exe not found", "ERROR")
            sys.exit(1)

        # pythonw_path=r"C:\Users\tec-d\.pyenv\pyenv-win\versions\3.8.0\python.exe"

        # print("pythonw_path:", pythonw_path)
        # sys.stdout = open(os.devnull, 'w')
        # sys.stderr = open(os.devnull, 'w')
        # sys.stdin = open(os.devnull, 'r')

        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            updated = UpdateManager.check_and_update()

            if updated:
                write_log_dev_file("Update completed", "INFO")
            else:
                write_log_dev_file("Application up-to-date", "INFO")

        except Exception as e:
            write_log_dev_file(f"Fatal error during update: {e}", "CRITICAL")
            sys.exit(1)

        if len(sys.argv) == 1:
            write_log_dev_file("Launching main application", "INFO")
            encrypted_key, secret_key = generate_encrypted_key()

            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run(
                    [sys.executable, str(script_path), encrypted_key, secret_key],
                    # stdout=subprocess.DEVNULL,
                    # stderr=subprocess.DEVNULL,
                    # stdin=subprocess.DEVNULL,
                    # creationflags=subprocess.CREATE_NO_WINDOW
                )
                print("Application principale lancée avec succès")
            else:
                write_log_dev_file("Main script not found", "ERROR")
                sys.exit(1)

    except Exception as e:
        write_log_dev_file(
            "fatal_application_error",
            "ERROR",
            exception_type=type(e).__name__,
            error=str(e),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
