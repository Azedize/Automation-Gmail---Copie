import datetime
import importlib
import json
import io
import os
import subprocess
import sys
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
import traceback


ROOT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = ROOT_DIR / "Tools"
LOG_DEV_FILE = ROOT_DIR / "Log" / "LogDev" / "my_project.json"


KEY = bytes.fromhex("f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2")
PROGRAM_DOWNLOAD_URL = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"


HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
SCRIPT_DIR = ROOT_DIR


def generate_encrypted_key():
    from cryptography.fernet import Fernet

    secret_key = Fernet.generate_key()
    return Fernet(secret_key).encrypt(b"authorized").decode(), secret_key.decode()


def _sanitize_log_value(value):
    text = str(value)
    return text[:200] if len(text) > 200 else text


def write_log_dev_file(message: str, level: str = "INFO", **context):
    try:
        LOG_DEV_FILE.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": str(level).upper(),
            "event": str(message),
            "context": {str(k): _sanitize_log_value(v) for k, v in context.items()},
        }
        with open(LOG_DEV_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")
    except Exception:
        pass


def clear_log():
    try:
        if LOG_DEV_FILE.exists():
            LOG_DEV_FILE.write_text("", encoding="utf-8")
    except Exception:
        pass


def show_update_network_warning():
    message = (
        "Impossible de vérifier la version du programme.\n\n"
        "L’application va continuer avec la version locale."
    )
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None, message, "AutoMailPro - Mise à jour", 0x30
        )
    else:
        print(message)


def find_pythonw():
    base_dir = os.path.dirname(sys.executable)
    candidate = os.path.join(base_dir, "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path.strip('"'), "pythonw.exe")
        if os.path.isfile(candidate):
            return candidate
    return None


class DependencyManager:
    @staticmethod
    def install_and_verify_pywin32():
        if importlib.util.find_spec("win32api"):
            write_log_dev_file("pywin32 already installed", "INFO")
            return True

        write_log_dev_file("Installing pywin32...", "INFO")
        site_packages = Path(sys.executable).parent / "Lib" / "site-packages"
        for folder in ("win32", "pywin32_system32"):
            path = site_packages / folder
            if path.exists():
                try:
                    shutil.rmtree(path)
                    write_log_dev_file(f"Removed {folder}", "INFO")
                except PermissionError:
                    write_log_dev_file(
                        f"Impossible de supprimer {folder} (fermez IDE/console)",
                        "ERROR",
                    )
        try:
            subprocess.run(
                [
                    sys.executable,
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
            write_log_dev_file("pywin32 installed successfully", "INFO")
        except subprocess.CalledProcessError:
            write_log_dev_file("Failed to install pywin32", "ERROR")
            return False

        postinstall_script = (
            Path(sys.executable).parent / "Scripts" / "pywin32_postinstall.py"
        )
        if postinstall_script.exists():
            try:
                subprocess.run(
                    [sys.executable, str(postinstall_script), "-install"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                write_log_dev_file("Post-installation completed", "INFO")
            except subprocess.CalledProcessError:
                write_log_dev_file("Failed post-installation pywin32", "ERROR")
                return False

        write_log_dev_file("Restarting script in 10s...", "INFO")
        time.sleep(10)
        subprocess.run([sys.executable, sys.argv[0]])
        sys.exit(0)

    @staticmethod
    def install_and_import(
        package, module_name=None, required_import=None, version=None
    ):
        module_to_import = module_name or package
        install_spec = f"{package}=={version}" if version else package
        try:
            module = importlib.import_module(module_to_import)
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")
            return module
        except (ModuleNotFoundError, ImportError):
            write_log_dev_file(f"Installing {package}...", "INFO")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"]
                )
            except subprocess.CalledProcessError:
                write_log_dev_file("Error updating pip", "ERROR")
                sys.exit(1)
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", install_spec]
                )
                write_log_dev_file(f"{package} installed", "INFO")
            except subprocess.CalledProcessError:
                write_log_dev_file(f"Error installing {package}", "ERROR")
                sys.exit(1)
            try:
                return importlib.import_module(module_to_import)
            except ImportError:
                write_log_dev_file(f"Error importing {module_to_import}", "ERROR")
                sys.exit(1)


def encrypt_message(plaintext: str, key_bytes: bytes):
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
        encrypted = base64.b64encode(
            iv + (encryptor.update(padded) + encryptor.finalize())
        ).decode("utf-8")
        return encrypted
    except Exception as e:
        write_log_dev_file(f"AES-CBC encryption failed: {e}", level="ERROR")
        return False


class UpdateManager:
    @staticmethod
    def _read_local_version(path):
        write_log_dev_file(
            f"Lecture de la version locale du programme: path={path}", "DEBUG"
        )
        if not path or not os.path.exists(path):
            write_log_dev_file(
                f"Version locale du programme introuvable: path={path}", "ERROR"
            )
            return None
        try:
            version = open(path, "r", encoding="utf-8").read().strip()
            write_log_dev_file(f"Version locale du programme lue: {version}", "INFO")
            return version
        except Exception as e:
            write_log_dev_file(
                f"Erreur lecture version locale du programme: {e}", "ERROR"
            )
            return None

    @staticmethod
    def _download_and_extract(
        zip_url, target_dir, clean_target=False, extract_subdir=None
    ):
        try:
            write_log_dev_file(
                f"Début téléchargement mise à jour programme: url={zip_url}, target={target_dir}, clean_target={clean_target}, extract_subdir={extract_subdir}",
                "INFO",
            )
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests

                r = requests.get(
                    zip_url, stream=True, headers=HEADER, timeout=60, verify=True
                )
                r.raise_for_status()
                write_log_dev_file(
                    f"Réponse téléchargement programme: status={r.status_code}, content_length={r.headers.get('content-length')}",
                    "DEBUG",
                )
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                write_log_dev_file(
                    f"ZIP programme téléchargé avec succès: path={zip_path}", "INFO"
                )
                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    write_log_dev_file(
                        f"Ancien dossier cible supprimé: {target_dir}", "INFO"
                    )
                with zipfile.ZipFile(zip_path, "r") as z:
                    write_log_dev_file(
                        f"Contenu ZIP programme: {len(z.namelist())} éléments", "DEBUG"
                    )
                    z.extractall(tmpdir)
                write_log_dev_file(
                    "Extraction temporaire du ZIP programme terminée.", "INFO"
                )
                extracted_root = next(
                    os.path.join(tmpdir, d)
                    for d in os.listdir(tmpdir)
                    if os.path.isdir(os.path.join(tmpdir, d))
                )
                extracted_dir = (
                    extracted_root
                    if not extract_subdir
                    else os.path.join(extracted_root, extract_subdir)
                    if os.path.exists(os.path.join(extracted_root, extract_subdir))
                    else extracted_root
                )
                write_log_dev_file(
                    f"Dossier source programme sélectionné: {extracted_dir}", "DEBUG"
                )
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                for item in os.listdir(extracted_dir):
                    src = os.path.join(extracted_dir, item)
                    dst = os.path.join(target_dir, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.move(src, dst)
                    else:
                        shutil.move(src, dst)
                write_log_dev_file(
                    f"Mise à jour programme extraite dans: {target_dir}", "INFO"
                )
                return True
        except Exception as e:
            write_log_dev_file(
                f"Erreur téléchargement/extraction mise à jour programme: {e}", "ERROR"
            )
            write_log_dev_file(traceback.format_exc(), "DEBUG")
            raise

    @staticmethod
    def check_and_update():
        write_log_dev_file("=== CHECK PROGRAM UPDATE START ===", "INFO")
        import requests

        session_date = datetime.datetime.now().strftime("%Y-%m-%d")
        write_log_dev_file(
            f"Date utilisée pour le check programme: {session_date}", "DEBUG"
        )
        date_encrypted = encrypt_message(session_date, KEY)
        if not date_encrypted:
            write_log_dev_file(
                "Échec chiffrement date pour le check programme.", "ERROR"
            )
            sys.exit("❌ Encryption failed, exiting program.")

        url = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"
        # download_files = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"

        download_files = PROGRAM_DOWNLOAD_URL

        write_log_dev_file(f"URL check version programme: {url}", "INFO")
        write_log_dev_file(f"URL téléchargement programme: {download_files}", "DEBUG")
        for attempt in range(1, 4):
            try:
                write_log_dev_file(
                    f"Tentative check version programme: {attempt}/3", "INFO"
                )
                response = requests.get(url, headers=HEADER, timeout=10)
                write_log_dev_file(
                    f"Réponse serveur programme: status={response.status_code}, content_length={response.headers.get('content-length')}",
                    "DEBUG",
                )
                if response.status_code != 200:
                    write_log_dev_file(
                        f"Échec récupération version programme: tentative={attempt}, status={response.status_code}",
                        "ERROR",
                    )
                    if attempt < 3:
                        time.sleep(2)
                        continue
                    write_log_dev_file(
                        "Check version indisponible; utilisation de la version locale.",
                        "WARNING",
                    )
                    return None
                data = response.json()
                write_log_dev_file(f"Données version programme reçues: {data}", "DEBUG")
                local_program = UpdateManager._read_local_version(
                    os.path.join("config", "version.txt")
                )
                remote_program = data.get("version")
                write_log_dev_file(
                    f"Comparaison versions programme: local={local_program}, remote={remote_program}",
                    "INFO",
                )
                if not local_program or local_program != data.get("version"):
                    write_log_dev_file(
                        f"Mise à jour programme requise: local={local_program}, remote={remote_program}",
                        "INFO",
                    )
                    if not UpdateManager._download_and_extract(
                        download_files,
                        ROOT_DIR,
                        clean_target=False,
                        extract_subdir=None,
                    ):
                        write_log_dev_file(
                            "Échec de la mise à jour programme après téléchargement/extraction.",
                            "ERROR",
                        )
                        sys.exit("❌ Program update failed, exiting program.")
                    write_log_dev_file(
                        "Mise à jour programme terminée avec succès.", "INFO"
                    )
                    write_log_dev_file(
                        "=== CHECK PROGRAM UPDATE END (UPDATED) ===", "INFO"
                    )
                    return True
                write_log_dev_file(
                    f"Programme à jour: local={local_program}, remote={remote_program}",
                    "INFO",
                )
                write_log_dev_file("=== CHECK PROGRAM UPDATE END (OK) ===", "INFO")
                return False
            except Exception as e:
                write_log_dev_file(
                    f"Erreur critique check programme: tentative={attempt}, erreur={e}",
                    "ERROR",
                )
                write_log_dev_file(traceback.format_exc(), "DEBUG")
                if attempt < 3:
                    time.sleep(2)
                    continue
                write_log_dev_file(
                    "Check version indisponible après 3 tentatives; utilisation de la version locale.",
                    "WARNING",
                )
                return None


def initialize_dependencies():
    write_log_dev_file("Initialisation des dépendances", level="INFO")
    DependencyManager.install_and_verify_pywin32()
    globals().update(
        {
            "requests": DependencyManager.install_and_import("requests"),
            "urllib3": DependencyManager.install_and_import("urllib3", version="2.2.3"),
            "PyQt6": DependencyManager.install_and_import(
                "PyQt6", version="6.7.0", required_import="QtCore"
            ),
            "cryptography_module": DependencyManager.install_and_import(
                "cryptography", version="3.3.2"
            ),
            "psutil": DependencyManager.install_and_import("psutil"),
            "pytz": DependencyManager.install_and_import("pytz"),
            "tqdm": DependencyManager.install_and_import("tqdm"),
            "platformdirs": DependencyManager.install_and_import("platformdirs"),
            "selenium": DependencyManager.install_and_import(
                "selenium", required_import="webdriver", version="4.27.1"
            ),
            "colorama": DependencyManager.install_and_import("colorama"),
            "sqlalchemy": DependencyManager.install_and_import("sqlalchemy"),
            "watchdog": DependencyManager.install_and_import(
                "watchdog", required_import="observers"
            ),
        }
    )
    if urllib3:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    try:
        clear_log()
        write_log_dev_file("Démarrage application principale", level="INFO")
        initialize_dependencies()
        write_log_dev_file("Initialisation des dépendances terminée.", "INFO")
        pythonw_path = find_pythonw()
        if not pythonw_path:
            write_log_dev_file(
                "pythonw.exe introuvable; lancement de l’application impossible.",
                "ERROR",
            )
            sys.exit(1)
        write_log_dev_file(f"pythonw.exe détecté: {pythonw_path}", "INFO")
        try:
            updated = UpdateManager.check_and_update()
            if updated is None:
                write_log_dev_file("Check version ignoré à cause du réseau.", "WARNING")
                show_update_network_warning()
            else:
                write_log_dev_file(
                    f"Résultat check programme: {'mise à jour appliquée' if updated else 'programme déjà à jour'}",
                    "INFO",
                )
        except Exception as e:
            write_log_dev_file(f"Fatal error during update: {e}", "CRITICAL")
            sys.exit(1)
        if len(sys.argv) == 1:
            write_log_dev_file(
                f"Lancement application principale: script={SCRIPT_DIR / 'src' / 'AppV2.py'}",
                "INFO",
            )
            encrypted_key, secret_key = generate_encrypted_key()
            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run(
                    [sys.executable, str(script_path), encrypted_key, secret_key]
                )
                write_log_dev_file("Application principale terminée.", "INFO")
            else:
                write_log_dev_file(
                    f"Script principal introuvable: {script_path}", "ERROR"
                )
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
