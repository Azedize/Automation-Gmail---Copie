import os
import sys
import json
import stat
import shutil
import zipfile
import tempfile
import traceback
import subprocess
from pathlib import Path
from typing import Any, Optional
import requests
import datetime
import urllib.parse


from config import settings as Settings

settings = Settings


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


try:
    from core import EncryptionService
    from core import SessionManager
    from api.base_client import API_MANAGER
    from ui_utils import UIManager

except ImportError as e:
    Settings.write_log_dev_file(
        f"❌ Erreur d'importation dans file {__file__}: {e}\n{traceback.format_exc()}",
        level="ERROR",
    )
    sys.exit(1)

SessionManager: Any


class UpdateManager:
    @staticmethod
    def readLocalVersion(path: str) -> Optional[str]:
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            Settings.write_log_dev_file(
                f"Error reading local version from {path}\n{traceback.format_exc()}",
                "ERROR",
            )
            return None

    @staticmethod
    def checkAndUpdate(window=None, progress_callback=None) -> Optional[bool]:

        def report_progress(message, value):
            if progress_callback:
                progress_callback(message, value)

        Settings.write_log_dev_file("=== CHECK PROGRAM VERSION START ===", "INFO")
        report_progress("Vérification de la version du programme...", 10)
        Settings.write_log_dev_file(f"Browser window provided: {bool(window)}", "DEBUG")

        SESSION_INFO = SessionManager.check_session()

        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer la vérification de version du programme.",
                "ERROR",
            )
            return None

        session_dt = SESSION_INFO.get("date")

        if not isinstance(session_dt, datetime.datetime):
            Settings.write_log_dev_file(
                f"SESSION date type incorrect pour la mise à jour du programme: {type(session_dt)}",
                "ERROR",
            )
            return False

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file(
            f"Date de session utilisée pour la vérification du programme: {session_date_plain}",
            "INFO",
        )
        settings.write_log_dev_file(
            "Session de programme valide: type datetime détecté.", "INFO"
        )

        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            if not date_encrypted:
                raise Exception("Encryption failed")

            encrypted_safe = urllib.parse.quote(date_encrypted)
            settings.write_log_dev_file(
                f"Date chiffrée pour le check programme: {encrypted_safe}", "INFO"
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Échec du chiffrement pour la vérification du programme : {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return False

        CHECK_URL_PROGRAMM = f"{Settings.PROGRAM_CHECK_ENDPOINT}?nv=1&rv4=1&event=check&type=V4&ext={Settings.PROGRAM_CHECK_EXTENSION}&k={encrypted_safe}"

        # SERVER_ZIP_URL_PROGRAM = (
        #     f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
        #     f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={encrypted_safe}"
        # )
        SERVER_ZIP_URL_PROGRAM = Settings.PROGRAM_DOWNLOAD_URL

        settings.write_log_dev_file(
            f"URL finale API programme: {CHECK_URL_PROGRAMM}", "INFO"
        )
        settings.write_log_dev_file(
            f"URL de téléchargement programme: {SERVER_ZIP_URL_PROGRAM}", "DEBUG"
        )

        try:
            settings.write_log_dev_file(
                "Vérification de mise à jour du programme en cours...", "INFO"
            )
            response = API_MANAGER.makeRequest(
                CHECK_URL_PROGRAMM, method="GET", timeout=10
            )

            settings.write_log_dev_file(
                f"Réponse brute API programme: {response}", "DEBUG"
            )
            settings.write_log_dev_file(
                f"Type de la réponse API programme: {type(response)}", "DEBUG"
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                settings.write_log_dev_file(
                    f"Serveur programme indisponible: {response}", "WARNING"
                )
                settings.write_log_dev_file(
                    "Aucune mise à jour du programme appliquée; on continue sans changement.",
                    "WARNING",
                )
                return None

            data = response.get("data")

            if isinstance(data, str) and "Invalid token" in data:
                Settings.write_log_dev_file(
                    f"Invalid token détecté sur le check programme: {data}", "ERROR"
                )

                try:
                    SessionManager.clear_session()
                    settings.write_log_dev_file(
                        "Session du programme effacée après token invalide.", "INFO"
                    )
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"Erreur lors du nettoyage de session après token invalide\n{traceback.format_exc()}",
                        "ERROR",
                    )

                os._exit(1)

            if not isinstance(data, dict):
                Settings.write_log_dev_file(
                    f"Réponse serveur programme invalide: {data}", "ERROR"
                )
                return False

            server_program = data.get("version")
            settings.write_log_dev_file(
                f"Version serveur du programme reçue: {server_program}",
                "INFO",
            )

            local_program = UpdateManager.readLocalVersion(
                Settings.VERSION_LOCAL_PROGRAMM
            )

            settings.write_log_dev_file(
                f"Version locale programme détectée: {local_program}", "INFO"
            )
            settings.write_log_dev_file(
                f"Chemin version locale programme: {Settings.VERSION_LOCAL_PROGRAMM}",
                "DEBUG",
            )

            if not local_program or local_program != server_program:
                Settings.write_log_dev_file(
                    f"Mise à jour du programme nécessaire: local={local_program}, remote={server_program}",
                    "INFO",
                )
                report_progress("Mise à jour disponible.", 35)

                if window and hasattr(window, "close"):
                    settings.write_log_dev_file(
                        "Fermeture de la fenêtre avant relancement du programme d'installation.",
                        "DEBUG",
                    )
                    window.close()

                report_progress("Téléchargement de la mise à jour...", 50)
                report_progress("Installation de la mise à jour...", 65)
                UpdateManager.launchNewWindow()
                report_progress("Redémarrage de l’application...", 100)
                settings.write_log_dev_file(
                    "Relancement du programme déclenché après différence de version.",
                    "INFO",
                )
                return False
            report_progress("Programme à jour.", 100)
            Settings.write_log_dev_file(
                f"Programme à jour: local={local_program}, remote={server_program}",
                "INFO",
            )
            Settings.write_log_dev_file("=== CHECK PROGRAM VERSION END ===", "INFO")
            return True
        except ImportError:
            Settings.write_log_dev_file(
                "API_MANAGER non disponible lors du check du programme.", "INFO"
            )
            return None
        except Exception as e:
            Settings.write_log_dev_file(
                f"Erreur critique lors de la vérification de mise à jour du programme: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return None

    @staticmethod
    def launchNewWindow() -> bool:
        """Lance une nouvelle instance de l'application"""
        script_path = os.path.join(Settings.BASE_DIR, "checkV3.py")
        if not os.path.isfile(script_path):
            return False

        try:
            python_exe = sys.executable
            if sys.platform == "win32":
                pythonw_candidate = os.path.join(
                    os.path.dirname(python_exe), "pythonw.exe"
                )
                if os.path.isfile(pythonw_candidate):
                    python_exe = pythonw_candidate

            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            subprocess.Popen(
                [python_exe, script_path],
                cwd=Settings.BASE_DIR,
                close_fds=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            return True

        except Exception as e:
            Settings.write_log_dev_file(
                f"Échec du lancement de la nouvelle instance: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            traceback.print_exc()
            return False

    @staticmethod
    def _find_version_in_extension_root(extensions_root, target_name):
        extensions_root = Path(extensions_root)
        if not extensions_root.is_dir():
            Settings.write_log_dev_file(
                f"Dossier extensions introuvable: {extensions_root}", "DEBUG"
            )
            return None

        try:
            for extension_dir in extensions_root.iterdir():
                if not extension_dir.is_dir():
                    continue

                version_dirs = [
                    path for path in extension_dir.iterdir() if path.is_dir()
                ]
                for version_dir in version_dirs:
                    manifest_path = version_dir / "manifest.json"
                    if not manifest_path.is_file():
                        continue

                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as e:
                        Settings.write_log_dev_file(
                            f"Manifest extension illisible: {manifest_path}; erreur={e}",
                            "WARNING",
                        )
                        continue

                    extension_name = manifest.get("name") or manifest.get("short_name")
                    if (
                        extension_name == target_name
                        or target_name.lower() in str(extension_name).lower()
                    ):
                        version = manifest.get("version") or version_dir.name
                        Settings.write_log_dev_file(
                            f"Extension correspondante trouvée: name={extension_name}, manifest={manifest_path}, version={version}",
                            "DEBUG",
                        )
                        return version
        except (OSError, PermissionError) as e:
            Settings.write_log_dev_file(
                f"Erreur accès dossier extensions {extensions_root}: {e}", "ERROR"
            )
        return None

    @staticmethod
    def _find_firefox_extension_version(profile_dir, target_id):
        extensions_dir = Path(profile_dir) / "extensions"
        if not extensions_dir.is_dir():
            return None

        try:
            for extension_file in extensions_dir.iterdir():
                if extension_file.suffix.lower() == ".xpi":
                    try:
                        with zipfile.ZipFile(extension_file) as archive:
                            manifest = json.loads(
                                archive.read("manifest.json").decode("utf-8")
                            )
                    except (
                        OSError,
                        KeyError,
                        json.JSONDecodeError,
                        zipfile.BadZipFile,
                    ) as e:
                        Settings.write_log_dev_file(
                            f"XPI Firefox illisible: {extension_file}; erreur={e}",
                            "WARNING",
                        )
                        continue

                    gecko = manifest.get("browser_specific_settings", {}).get(
                        "gecko", {}
                    )
                    legacy_gecko = manifest.get("applications", {}).get("gecko", {})
                    extension_id = gecko.get("id") or legacy_gecko.get("id")
                    if extension_id == target_id:
                        version = manifest.get("version")
                        Settings.write_log_dev_file(
                            f"Extension Firefox trouvée: id={extension_id}, fichier={extension_file}, version={version}",
                            "INFO",
                        )
                        return version
        except (OSError, PermissionError) as e:
            Settings.write_log_dev_file(
                f"Erreur accès extensions Firefox {extensions_dir}: {e}", "ERROR"
            )

        return None

    @staticmethod
    def _normalize_extension_target(browser_name, target_name):
        browser_name = (browser_name or "").strip().lower()
        if browser_name == "firefox" and target_name == Settings.EXTENSION_TARGET_NAME:
            target_name = Settings.FIREFOX_EXTENSION_ID
        return browser_name, target_name

    @staticmethod
    def _iter_extension_roots(candidate):
        candidate = Path(candidate)
        roots = []
        if candidate.is_dir():
            roots.append(candidate)

        user_data_root = candidate.parent.parent
        if user_data_root.is_dir():
            try:
                roots.extend(
                    profile_dir / "Extensions"
                    for profile_dir in user_data_root.iterdir()
                    if profile_dir.is_dir()
                )
            except OSError as e:
                Settings.write_log_dev_file(
                    f"Impossible de parcourir les profils Chromium {user_data_root}: {e}",
                    "WARNING",
                )

        seen = set()
        for root in roots:
            root_key = str(root).lower()
            if root_key not in seen:
                seen.add(root_key)
                yield root

    @staticmethod
    def getInstalledBrowserExtensionVersion(browser_name, target_name="EX3"):
        browser_name, target_name = UpdateManager._normalize_extension_target(
            browser_name, target_name
        )
        if not browser_name:
            Settings.write_log_dev_file(
                "Aucun navigateur fourni pour la détection de version de l'extension.",
                "WARNING",
            )
            return None

        Settings.write_log_dev_file(
            f"Début détection extension {target_name} pour navigateur: {browser_name}",
            "INFO",
        )

        user_root = Path.home()
        candidates = [
            user_root.joinpath(*relative_path)
            for relative_path in Settings.BROWSER_EXTENSION_CANDIDATES.get(
                browser_name, ()
            )
        ]

        for candidate in candidates:
            Settings.write_log_dev_file(
                f"Recherche extension dans le dossier navigateur: {candidate}", "DEBUG"
            )
            if browser_name == "firefox":
                if not candidate.exists():
                    Settings.write_log_dev_file(
                        f"Dossier Firefox non trouvé: {candidate}", "DEBUG"
                    )
                    continue
                for profile_dir in candidate.iterdir():
                    if not profile_dir.is_dir():
                        continue
                    Settings.write_log_dev_file(
                        f"Scan du profil Firefox: {profile_dir}", "DEBUG"
                    )
                    version = UpdateManager._find_firefox_extension_version(
                        profile_dir, target_name
                    )
                    if version:
                        return version
                    for extension_root in (profile_dir / "extensions", profile_dir):
                        version = UpdateManager._find_version_in_extension_root(
                            extension_root, target_name
                        )
                        if version:
                            Settings.write_log_dev_file(
                                f"Version extension {target_name} détectée dans Firefox via {extension_root}: {version}",
                                "INFO",
                            )
                            return version
                continue

            for extension_root in UpdateManager._iter_extension_roots(candidate):
                version = UpdateManager._find_version_in_extension_root(
                    extension_root, target_name
                )
                if version:
                    Settings.write_log_dev_file(
                        f"Version extension {target_name} détectée dans {browser_name} via {extension_root}: {version}",
                        "INFO",
                    )
                    return version

        Settings.write_log_dev_file(
            f"Aucune version de l'extension {target_name} détectée pour {browser_name} dans les chemins connus.",
            "WARNING",
        )
        return None

    @staticmethod
    def validateBrowserExtensionVersion(
        browser_name, remote_version, target_name="EX3", window=None
    ):
        browser_name, target_name = UpdateManager._normalize_extension_target(
            browser_name, target_name
        )
        Settings.write_log_dev_file(
            f"=== VALIDATION VERSION EXTENSION START === browser={browser_name} remote={remote_version} target={target_name}",
            "INFO",
        )
        installed_version = UpdateManager.getInstalledBrowserExtensionVersion(
            browser_name, target_name
        )

        if installed_version is None:
            Settings.write_log_dev_file(
                f"Extension {target_name} non trouvée pour le navigateur {browser_name} lors de la validation.",
                "WARNING",
            )
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Extension not detected",
                    f"The {target_name} extension could not be found in {browser_name}. Please contact support to validate the installation before continuing.",
                    message_type="warning",
                )
            return False

        if str(installed_version) != str(remote_version):
            Settings.write_log_dev_file(
                f"Version de l'extension {target_name} différente pour {browser_name}: local={installed_version}, remote={remote_version}",
                "WARNING",
            )
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Extension update required",
                    f"The {target_name} extension is outdated on {browser_name}.\n\nInstalled version: {installed_version}\nCurrent version: {remote_version}\n\nPlease contact support to complete the extension update. The application itself will not be modified.",
                    message_type="warning",
                )
            Settings.write_log_dev_file(
                "=== VALIDATION VERSION EXTENSION END (MISMATCH) ===", "INFO"
            )
            return False

        Settings.write_log_dev_file(
            f"Extension {target_name} validée pour {browser_name}: local={installed_version}, remote={remote_version}",
            "INFO",
        )
        Settings.write_log_dev_file(
            "=== VALIDATION VERSION EXTENSION END (OK) ===", "INFO"
        )
        return True

    @staticmethod
    def checkExtensionVersion(window=None, browser_name=None):

        Settings.write_log_dev_file("=== CHECK EXTENSION VERSION START ===", "INFO")
        Settings.write_log_dev_file(
            f"Paramètres check extension: browser_name={browser_name}, window={bool(window)}",
            "INFO",
        )

        # ================================================
        # 🔹 Vérification session
        # ================================================
        SESSION_INFO = SessionManager.check_session()
        if not SESSION_INFO.get("valid"):
            Settings.write_log_dev_file(
                "Session invalide. Impossible de continuer la vérification de l’extension.",
                "ERROR",
            )
            return False

        # ================================================
        # 🔹 Gestion sécurisée du champ date (datetime uniquement)
        # ================================================
        session_dt = SESSION_INFO.get("date")
        if not isinstance(session_dt, datetime.datetime):
            settings.write_log_dev_file(
                f"SESSION date type incorrect pour l’extension: {type(session_dt)}",
                "ERROR",
            )
            return False

        settings.write_log_dev_file(
            "Session d’extension valide: type datetime détecté.", "INFO"
        )

        session_date_plain = session_dt.strftime("%Y-%m-%d")
        settings.write_log_dev_file(
            f"Session date utilisée pour l’extension (format YYYY-MM-DD): {session_date_plain}",
            "INFO",
        )

        # ================================================
        # 🔹 Chiffrement
        # ================================================
        try:
            date_encrypted = EncryptionService.encrypt_message(
                session_date_plain, Settings.KEY
            )
            settings.write_log_dev_file(
                f"Date chiffrée pour le check extension: {date_encrypted}", "INFO"
            )
        except Exception as e:
            settings.write_log_dev_file(
                f"Échec du chiffrement pour le check extension: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            traceback.print_exc()
            return False

        if not date_encrypted:
            Settings.write_log_dev_file(
                "Chiffrement de la date de session pour l’extension impossible.",
                "ERROR",
            )
            return False

        encrypted_safe = urllib.parse.quote(date_encrypted)
        CHECK_URL_EX3 = f"{Settings.PROGRAM_CHECK_ENDPOINT}?nv=1&rv4=1&event=check&type=V4&ext={Settings.EXTENSION_CHECK_EXTENSION}&k={encrypted_safe}"
        settings.write_log_dev_file(f"URL API extension: {CHECK_URL_EX3}", "INFO")

        # ================================================
        # 🔹 Requête GET
        # ================================================
        try:
            settings.write_log_dev_file(
                "Appel API pour récupérer la version distante de l’extension...", "INFO"
            )
            response = requests.get(
                CHECK_URL_EX3,
                headers=Settings.HEADER,
                verify=Settings.VERIFY_SSL,
                timeout=10,
            )
            response.raise_for_status()
            settings.write_log_dev_file(
                f"Réponse API extension: {response.text[:500]}", "DEBUG"
            )

            try:
                data = response.json()
            except json.JSONDecodeError:
                try:
                    data = json.loads(response.text)
                    settings.write_log_dev_file(
                        "Content-Type non standard, mais le JSON a été parsé correctement.",
                        "WARNING",
                    )
                except Exception as e:
                    settings.write_log_dev_file(
                        f"Échec de parsing JSON de la réponse extension: {e}\n{traceback.format_exc()}",
                        level="ERROR",
                    )
                    return None

            if not isinstance(data, dict):
                settings.write_log_dev_file(
                    "Réponse API extension invalide: objet JSON attendu.", "ERROR"
                )
                return None

            remote_version = data.get("version_Extention")
            settings.write_log_dev_file(
                f"Version distante extension reçue: {remote_version}", "INFO"
            )

        except Exception as e:
            settings.write_log_dev_file(
                f"Échec de récupération de la version distante de l’extension: {e}\n{traceback.format_exc()}",
                level="ERROR",
            )
            traceback.print_exc()
            if window:
                UIManager.showCriticalMessage(
                    window,
                    "Network Error",
                    "Unable to check for updates. Please check your internet connection.",
                    message_type="critical",
                )
            return None

        if remote_version is None:
            settings.write_log_dev_file(
                "Version distante extension absente: version_Extention non trouvé dans la réponse API.",
                "ERROR",
            )
            return None

        # ================================================
        # 🔹 Version locale détectée depuis le navigateur installé
        # ================================================
        browser_candidates = []
        if browser_name:
            browser_candidates.append(browser_name.strip().lower())
        else:
            browser_candidates = ["chrome", "edge", "firefox", "comodo", "icedragon"]

        settings.write_log_dev_file(
            f"Navigateurs à vérifier pour l’extension: {browser_candidates}", "INFO"
        )

        local_version = None
        detected_browser = None
        for candidate in browser_candidates:
            version = UpdateManager.getInstalledBrowserExtensionVersion(
                candidate, Settings.EXTENSION_TARGET_NAME
            )
            if version:
                local_version = version
                detected_browser = candidate
                settings.write_log_dev_file(
                    f"Version locale extension détectée avec {candidate}: {local_version}",
                    "INFO",
                )
                break

        if local_version is None:
            settings.write_log_dev_file(
                "Version locale non détectée depuis l’extension installée du navigateur.",
                "ERROR",
            )
            return None

        settings.write_log_dev_file(
            f"Version locale détectée depuis {detected_browser}: {local_version}, version distante: {remote_version}",
            "INFO",
        )

        # ================================================
        # 🔹 Différence de version
        # ================================================
        if str(local_version) != str(remote_version):
            settings.write_log_dev_file(
                f"Mise à jour de l’extension requise: local={local_version}, remote={remote_version}",
                "INFO",
            )
            settings.write_log_dev_file(
                "=== CHECK EXTENSION VERSION END (VERSION MISMATCH) ===", "INFO"
            )
            return remote_version
        settings.write_log_dev_file(
            f"Extension à jour: local={local_version}, remote={remote_version}", "INFO"
        )
        settings.write_log_dev_file("=== CHECK EXTENSION VERSION END (OK) ===", "INFO")
        return True
