import datetime
import importlib
import json
import os
import sys
import shutil
import zipfile
import importlib
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
import tempfile
import io
import datetime
import json
import traceback


# ==========================================================
# 🔹 VARIABLES GLOBALES
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = ROOT_DIR / "Tools"
LOG_DEV_FILE = ROOT_DIR / "Log" / "LogDev" / "my_project.json"


print("🚀 [INIT] Initialisation du script principal...")
KEY = bytes.fromhex("f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2")
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
                    write_log_dev_file(f"Impossible de supprimer {folder} (fermez IDE/console)", "ERROR")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "pywin32==305"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            write_log_dev_file("pywin32 installed successfully", "INFO")
        except subprocess.CalledProcessError:
            write_log_dev_file("Failed to install pywin32", "ERROR")
            return False

        postinstall_script = Path(sys.executable).parent / "Scripts" / "pywin32_postinstall.py"
        if postinstall_script.exists():
            try:
                subprocess.run([sys.executable, str(postinstall_script), "-install"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                write_log_dev_file("Post-installation completed", "INFO")
            except subprocess.CalledProcessError:
                write_log_dev_file("Failed post-installation pywin32", "ERROR")
                return False

        write_log_dev_file("Restarting script in 10s...", "INFO")
        time.sleep(10)
        subprocess.run([sys.executable, sys.argv[0]])
        sys.exit(0)

    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):
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
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])
            except subprocess.CalledProcessError:
                write_log_dev_file("Error updating pip", "ERROR")
                sys.exit(1)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
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
        encrypted = base64.b64encode(iv + (encryptor.update(padded) + encryptor.finalize())).decode("utf-8")
        return encrypted
    except Exception as e:
        write_log_dev_file(f"AES-CBC encryption failed: {e}", level="ERROR")
        return False


class UpdateManager:
    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            write_log_dev_file("Local version not found", "ERROR")
            return None
        try:
            return open(path, "r", encoding="utf-8").read().strip()
        except Exception:
            write_log_dev_file("Error reading local version", "ERROR")
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None):
        try:
            write_log_dev_file("Downloading update from server", "INFO")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests
                r = requests.get(zip_url, stream=True, headers=HEADER, timeout=60, verify=False)
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                write_log_dev_file("ZIP downloaded successfully", "INFO")
                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    write_log_dev_file("Old target directory removed", "INFO")
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
                write_log_dev_file("Temporary ZIP extraction completed", "INFO")
                extracted_root = next(os.path.join(tmpdir, d) for d in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, d)))
                extracted_dir = extracted_root if not extract_subdir else os.path.join(extracted_root, extract_subdir) if os.path.exists(os.path.join(extracted_root, extract_subdir)) else extracted_root
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
                write_log_dev_file(f"Extraction completed in: {target_dir}", "INFO")
                return True
        except Exception:
            write_log_dev_file("Error downloading/extracting update", "ERROR")
            raise

    @staticmethod
    def check_and_update():
        write_log_dev_file("Checking for updates", "INFO")
        import requests
        date_encrypted = encrypt_message(datetime.datetime.now().strftime("%Y-%m-%d"), KEY)
        if not date_encrypted:
            write_log_dev_file("Date encryption failed", "ERROR")
            sys.exit("❌ Encryption failed, exiting program.")
        url = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"
        download_files = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"
        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=HEADER, timeout=10)
                if response.status_code != 200:
                    write_log_dev_file(f"Attempt {attempt}: Failed to fetch version.json (status {response.status_code})", "ERROR")
                    if attempt < 3:
                        time.sleep(2)
                        continue
                    sys.exit("❌ Server unreachable or error, exiting program.")
                data = response.json()
                local_program = UpdateManager._read_local_version(os.path.join("config", "version.txt"))
                if not local_program or local_program != data.get("version"):
                    write_log_dev_file("Required program update", "INFO")
                    if not UpdateManager._download_and_extract(download_files, ROOT_DIR, clean_target=False, extract_subdir=None):
                        sys.exit("❌ Program update failed, exiting program.")
                    return True
                write_log_dev_file("Application up-to-date", "INFO")
                return False
            except Exception as e:
                write_log_dev_file(f"Attempt {attempt}: Critical update error: {e}", "ERROR")
                if attempt < 3:
                    time.sleep(2)
                    continue
                sys.exit(f"❌ Critical update error after 3 attempts, exiting program: {e}")


def initialize_dependencies():
    write_log_dev_file("Initialisation des dépendances", level="INFO")
    DependencyManager.install_and_verify_pywin32()
    globals().update({
        "requests": DependencyManager.install_and_import("requests"),
        "urllib3": DependencyManager.install_and_import("urllib3", version="2.2.3"),
        "PyQt6": DependencyManager.install_and_import("PyQt6", version="6.7.0", required_import="QtCore"),
        "cryptography_module": DependencyManager.install_and_import("cryptography", version="3.3.2"),
        "psutil": DependencyManager.install_and_import("psutil"),
        "pytz": DependencyManager.install_and_import("pytz"),
        "tqdm": DependencyManager.install_and_import("tqdm"),
        "platformdirs": DependencyManager.install_and_import("platformdirs"),
        "selenium": DependencyManager.install_and_import("selenium", required_import="webdriver", version="4.27.1"),
        "colorama": DependencyManager.install_and_import("colorama"),
        "sqlalchemy": DependencyManager.install_and_import("sqlalchemy"),
    })
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
        pythonw_path = find_pythonw()
        if not pythonw_path:
            write_log_dev_file("pythonw.exe not found", "ERROR")
            sys.exit(1)
        try:
            updated = UpdateManager.check_and_update()
            write_log_dev_file("Update completed" if updated else "Application up-to-date", "INFO")
        except Exception as e:
            write_log_dev_file(f"Fatal error during update: {e}", "CRITICAL")
            sys.exit(1)
        if len(sys.argv) == 1:
            write_log_dev_file("Launching main application", "INFO")
            encrypted_key, secret_key = generate_encrypted_key()
            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])
                print("Application principale lancée avec succès")
            else:
                write_log_dev_file("Main script not found", "ERROR")
                sys.exit(1)
    except Exception as e:
        write_log_dev_file("fatal_application_error", "ERROR", exception_type=type(e).__name__, error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
