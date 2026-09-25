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

# PROGRAM_DOWNLOAD_URL = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"

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


def show_update_failure_warning():
    message = (
        "Une mise à jour obligatoire n’a pas pu être téléchargée.\n\n"
        "L’application va être arrêtée. Veuillez réessayer plus tard ou contacter le support."
    )
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None, message, "AutoMailPro - Échec de mise à jour", 0x10
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
        zip_url,
        target_dir,
        clean_target=False,
        extract_subdir=None,
        progress_callback=None,
    ):
        try:
            write_log_dev_file(
                f"Début téléchargement mise à jour programme: url={zip_url}, target={target_dir}, clean_target={clean_target}, extract_subdir={extract_subdir}",
                "INFO",
            )
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                import requests

                with requests.get(
                    zip_url, stream=True, headers=HEADER, timeout=60, verify=True
                ) as r:
                    r.raise_for_status()
                    write_log_dev_file(
                        "Réponse téléchargement programme: "
                        f"status={r.status_code}, "
                        f"content_type={r.headers.get('Content-Type', '')}, "
                        f"content_length={r.headers.get('Content-Length', '')}, "
                        f"content_disposition={r.headers.get('Content-Disposition', '')}",
                        "DEBUG",
                    )
                    downloaded_bytes = 0
                    first_bytes = b""
                    content_length = int(r.headers.get("Content-Length") or 0)
                    with open(zip_path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                if not first_bytes:
                                    first_bytes = chunk[:32]
                                downloaded_bytes += len(chunk)
                                f.write(chunk)
                                if progress_callback and content_length:
                                    progress_callback(
                                        "Téléchargement de la mise à jour...",
                                        min(
                                            75,
                                            int(downloaded_bytes * 75 / content_length),
                                        ),
                                    )
                write_log_dev_file(
                    f"Corps de réponse téléchargement reçu: bytes={downloaded_bytes}, "
                    f"signature={first_bytes[:4].hex() if first_bytes else 'empty'}",
                    "DEBUG",
                )
                if downloaded_bytes == 0:
                    raise RuntimeError(
                        "Le serveur a répondu 200 mais le corps ZIP est vide."
                    )
                if not zipfile.is_zipfile(zip_path):
                    write_log_dev_file(
                        f"Réponse non-ZIP détectée: prefix={first_bytes[:32]!r}",
                        "ERROR",
                    )
                    raise zipfile.BadZipFile(
                        "La réponse serveur n’est pas une archive ZIP valide."
                    )
                write_log_dev_file(
                    f"ZIP programme téléchargé avec succès: path={zip_path}, bytes={downloaded_bytes}",
                    "INFO",
                )
                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    write_log_dev_file(
                        f"Ancien dossier cible supprimé: {target_dir}", "INFO"
                    )
                with zipfile.ZipFile(zip_path, "r") as z:
                    if progress_callback:
                        progress_callback("Installation de la mise à jour...", 85)
                    write_log_dev_file(
                        f"Contenu ZIP programme: {len(z.namelist())} éléments", "DEBUG"
                    )
                    z.extractall(tmpdir)
                write_log_dev_file(
                    "Extraction temporaire du ZIP programme terminée.", "INFO"
                )
                extracted_entries = [
                    entry for entry in os.listdir(tmpdir) if entry != "update.zip"
                ]
                extracted_directories = [
                    entry
                    for entry in extracted_entries
                    if os.path.isdir(os.path.join(tmpdir, entry))
                ]
                if len(extracted_entries) == 1 and len(extracted_directories) == 1:
                    extracted_root = os.path.join(tmpdir, extracted_directories[0])
                    extraction_layout = "single_root_directory"
                else:
                    extracted_root = tmpdir
                    extraction_layout = "project_files_at_archive_root"
                write_log_dev_file(
                    f"Structure ZIP détectée: layout={extraction_layout}, entries={len(extracted_entries)}",
                    "DEBUG",
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
                if progress_callback:
                    progress_callback("Mise à jour terminée.", 100)
                return True
        except Exception as e:
            write_log_dev_file(
                f"Erreur téléchargement/extraction mise à jour programme: {e}", "ERROR"
            )
            write_log_dev_file(traceback.format_exc(), "DEBUG")
            raise

    @staticmethod
    def check_and_update(progress_callback=None):
        def report_progress(message, value):
            if progress_callback:
                progress_callback(message, value)

        write_log_dev_file("=== CHECK PROGRAM UPDATE START ===", "INFO")
        report_progress("Vérification de la version du programme...", 10)
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
        # PROGRAM_DOWNLOAD_URL = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"

        # PROGRAM_DOWNLOAD_URL = (
        #     "https://reporting.nrb-apps.com/APP_R/redirect.php?"
        #     f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"
        # )

        PROGRAM_DOWNLOAD_URL = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"

        write_log_dev_file(f"URL check version programme: {url}", "INFO")
        write_log_dev_file(
            "URL téléchargement programme: reporting.nrb-apps.com/APP_R/redirect.php "
            "(token masqué)",
            "DEBUG",
        )
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
                report_progress("Version du programme reçue.", 25)
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
                    report_progress("Mise à jour disponible...", 30)
                    try:
                        downloaded = UpdateManager._download_and_extract(
                            PROGRAM_DOWNLOAD_URL,
                            ROOT_DIR,
                            clean_target=False,
                            extract_subdir=None,
                            progress_callback=report_progress,
                        )
                    except Exception as e:
                        write_log_dev_file(
                            f"Échec du téléchargement de la mise à jour obligatoire: {e}",
                            "ERROR",
                        )
                        return "update_failed"
                    if not downloaded:
                        write_log_dev_file(
                            "Échec de la mise à jour programme après téléchargement/extraction.",
                            "ERROR",
                        )
                        return "update_failed"
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
                report_progress("Programme à jour.", 100)
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
            write_log_dev_file( "pythonw.exe introuvable; lancement de l’application impossible.", "ERROR" )
            sys.exit(1)

        write_log_dev_file(f"pythonw.exe détecté: {pythonw_path}", "INFO")
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import (
            QApplication,
            QDialog,
            QLabel,
            QProgressBar,
            QVBoxLayout,
        )

        progress_app = QApplication.instance() or QApplication(sys.argv)

        class StartupWindow(QDialog):
            def __init__(self):
                super().__init__()
                self.setFixedSize(560, 250)
                self.setWindowTitle("AutoMailPro")
                self.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                self.setStyleSheet(
                    """
                    QDialog {
                        background-color: #F9F9F9;
                        color: #333333;
                        font-family: "Segoe UI";
                        font-size: 12px;
                    }
                    QLabel, QProgressBar {
                        font-family: "Segoe UI";
                    }
                    QLabel#brand {
                        color: #0E94A0;
                        font-size: 26px;
                        font-weight: bold;
                    }
                    QLabel#subtitle { color: #666666; font-size: 13px; }
                    QLabel#status { color: #333333; font-size: 14px; }
                    QProgressBar {
                        height: 9px;
                        border: 1px solid #CCCCCC;
                        border-radius: 4px;
                        background-color: #FFFFFF;
                    }
                    QProgressBar::chunk {
                        border-radius: 4px;
                        background-color: #0E94A0;
                    }
                    """
                )
                layout = QVBoxLayout(self)
                layout.setContentsMargins(42, 34, 42, 34)
                layout.setSpacing(12)
                brand = QLabel("AutoMailPro")
                brand.setObjectName("brand")
                subtitle = QLabel("Préparation de votre espace de travail")
                subtitle.setObjectName("subtitle")
                self.status = QLabel("Démarrage sécurisé...")
                self.status.setObjectName("status")
                self.progress = QProgressBar()
                self.progress.setRange(0, 100)
                self.progress.setValue(8)
                self.progress.setTextVisible(False)
                layout.addWidget(brand)
                layout.addWidget(subtitle)
                layout.addSpacing(12)
                layout.addWidget(self.status)
                layout.addWidget(self.progress)

            def update(self, message, value):
                self.status.setText(message)
                self.progress.setValue(max(0, min(100, value)))
                self.progress_app.processEvents()

            def show_update_mode(self):
                self.status.setText("Mise à jour de l’application...")

        startup_window = StartupWindow()
        startup_window.progress_app = progress_app
        startup_window.show()
        progress_app.processEvents()
        startup_started_at = time.monotonic()

        def update_progress_callback(message, value):
            if "mise à jour disponible" in message.lower():
                startup_window.show_update_mode()
            startup_window.update(message, value)

        try:
            updated = UpdateManager.check_and_update( progress_callback=update_progress_callback )
            if updated == "update_failed":
                startup_window.close()
                write_log_dev_file(
                    "Mise à jour obligatoire échouée; arrêt du programme.", "ERROR"
  )
                show_update_failure_warning()
                sys.exit(1)
            if updated is None:
                write_log_dev_file("Check version ignoré à cause du réseau.", "WARNING")
                show_update_network_warning()
            else:
                startup_window.update(
                    "Mise à jour terminée. Lancement de l’application..."
                    if updated
                    else "Application à jour. Lancement...",
                    100,
                )
                write_log_dev_file(
                    f"Résultat check programme: {'mise à jour appliquée' if updated else 'programme déjà à jour'}",
                    "INFO",
                )
        except Exception as e:
            startup_window.close()
            write_log_dev_file(f"Fatal error during update: {e}", "CRITICAL")
            sys.exit(1)
        while time.monotonic() - startup_started_at < 3:
            progress_app.processEvents()
            time.sleep(0.05)
        startup_window.close()
        progress_app.processEvents()
        if len(sys.argv) == 1:
            write_log_dev_file( f"Lancement application principale: script={SCRIPT_DIR / 'src' / 'AppV2.py'}", "INFO" )
            encrypted_key, secret_key = generate_encrypted_key()
            script_path = SCRIPT_DIR / "src" / "AppV2.py"
            if script_path.is_file():
                subprocess.run(  [sys.executable, str(script_path), encrypted_key, secret_key]  )
                write_log_dev_file("Application principale terminée.", "INFO")
            else:
                write_log_dev_file(  f"Script principal introuvable: {script_path}", "ERROR" )
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
