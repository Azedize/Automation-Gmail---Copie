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

    # Import Fernet -> utilisé pour le chiffrement
    from cryptography.fernet import Fernet

    # Génère une nouvelle clé secrète
    # Exemple -> secret_key = b'ABC123...'
    secret_key = Fernet.generate_key()

    # Chiffre "authorized" avec la clé générée
    # "authorized" -> encrypted value
    encrypted_key = Fernet(secret_key).encrypt(b"authorized").decode()

    # Convertit la clé secrète de bytes -> string
    secret_key = secret_key.decode()

    # Retourne les deux valeurs :
    # First  -> encrypted_key
    # Second -> secret_key
    return encrypted_key, secret_key


def _sanitize_log_value(value):

    # Convertit la valeur en chaîne de caractères
    # Exemple -> 123 -> "123" / None -> "None"
    text = str(value)

    # Limite la longueur de la valeur à 200 caractères maximum
    # > 200 caractères -> conserve uniquement les 200 premiers
    # <= 200 caractères -> conserve la valeur complète
    return text[:200] if len(text) > 200 else text


def write_log_dev_file(message: str, level: str = "INFO", **context):

    try:

        # Crée le dossier du fichier de log s'il n'existe pas
        # parents=True -> crée également les dossiers parents nécessaires
        # exist_ok=True -> ne génère pas d'erreur si le dossier existe déjà
        LOG_DEV_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Prépare la structure du log sous forme de dictionnaire
        # timestamp -> date et heure actuelles en UTC au format ISO 8601
        # level -> niveau du log converti en majuscules
        # event -> message principal de l'événement
        # context -> informations supplémentaires nettoyées avant l'écriture
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": str(level).upper(),
            "event": str(message),
            "context": {str(k): _sanitize_log_value(v) for k, v in context.items()},
        }

        # Ouvre le fichier en mode ajout sans supprimer les logs existants
        # encoding="utf-8" -> permet de gérer correctement les caractères spéciaux
        with open(LOG_DEV_FILE, "a", encoding="utf-8") as f:

            # Convertit le dictionnaire en JSON et l'écrit sur une seule ligne
            # ensure_ascii=False -> conserve correctement les caractères non ASCII
            # separators=(",", ":") -> réduit les espaces inutiles dans le JSON
            f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

            # Ajoute un retour à la ligne pour séparer chaque événement de log
            f.write("\n")

    except Exception:
        # affiche erreur detaille
        print("Erreur lors de l'écriture du fichier de log de développement :", sys.exc_info()[1])
        # Ignore toute erreur d'écriture afin que le système de logs
        # n'interrompe pas le fonctionnement principal de l'application
        pass


def clear_log():

    try:

        # Vérifie si le fichier de log existe avant de modifier son contenu
        # exists() -> retourne True si le fichier existe, sinon False
        if LOG_DEV_FILE.exists():

            # Vide complètement le contenu du fichier de log
            # "" -> remplace tout le contenu existant par une chaîne vide
            # encoding="utf-8" -> garantit un encodage compatible avec les caractères spéciaux
            LOG_DEV_FILE.write_text("", encoding="utf-8")

    except Exception:
        # Ignore toute erreur afin qu'un problème lors du nettoyage du log
        # n'interrompe pas le fonctionnement principal de l'application
        pass


def show_update_network_warning():

    # Prépare le message affiché lorsque la dernière version ne peut pas être détectée
    # \n\n -> ajoute une ligne vide entre les deux phrases
    message = "Unable to detect the latest version from the update server.\n\n" "Please contact support for assistance."

    # Vérifie si l'application est exécutée sous Windows
    # sys.platform == "win32" -> identifie l'environnement Windows
    if sys.platform == "win32":

        # Importe ctypes pour accéder aux fonctions de l'API Windows
        import ctypes

        # Affiche une boîte de dialogue Windows avec le message d'avertissement
        # None -> aucune fenêtre parente associée
        # message -> contenu affiché dans la boîte de dialogue
        # "AutoMailPro - Mise à jour" -> titre de la fenêtre
        # 0x30 -> affiche une icône d'avertissement
        ctypes.windll.user32.MessageBoxW(None, message, "AutoMailPro - Update", 0x30)
    else:
        # Affiche le message dans la console pour les systèmes non Windows
        print(message)


def show_update_failure_warning():

    # Prépare le message affiché lorsque le téléchargement de la mise à jour obligatoire échoue
    # \n\n -> ajoute une ligne vide entre les deux phrases
    message = "The required update could not be downloaded.\n\n" "The application will now close. Please try again later or contact support."

    # Vérifie si l'application est exécutée sous Windows
    # sys.platform == "win32" -> identifie l'environnement Windows
    if sys.platform == "win32":

        # Importe ctypes pour accéder aux fonctions de l'API Windows
        import ctypes

        # Affiche une boîte de dialogue Windows avec le message d'erreur
        # None -> aucune fenêtre parente associée
        # message -> contenu affiché dans la boîte de dialogue
        # "AutoMailPro - Update Failure" -> titre de la fenêtre
        # 0x10 -> affiche une icône d'erreur
        ctypes.windll.user32.MessageBoxW(None, message, "AutoMailPro - Update Failure", 0x10)
    else:

        # Affiche le message dans la console pour les systèmes non Windows
        print(message)


def find_pythonw():

    # Récupère le répertoire contenant l'exécutable Python actuellement utilisé
    # sys.executable -> chemin complet de l'interpréteur Python en cours d'exécution
    base_dir = os.path.dirname(sys.executable)

    # Construit le chemin vers pythonw.exe dans le même répertoire que Python
    candidate = os.path.join(base_dir, "pythonw.exe")

    # Vérifie si pythonw.exe existe à côté de l'interpréteur Python actuel
    # Si le fichier existe, retourne immédiatement son chemin complet
    if os.path.isfile(candidate):
        return candidate

    # Parcourt tous les répertoires définis dans la variable d'environnement PATH
    # PATH -> liste des répertoires dans lesquels rechercher les exécutables
    # os.pathsep -> séparateur utilisé par le système pour séparer les chemins
    for path in os.environ.get("PATH", "").split(os.pathsep):

        # Supprime les guillemets éventuels du chemin et ajoute pythonw.exe
        # Exemple -> "C:\Python311" devient C:\Python311\pythonw.exe
        candidate = os.path.join(path.strip('"'), "pythonw.exe")

        # Vérifie si pythonw.exe existe dans le répertoire courant
        # Si le fichier existe, retourne son chemin complet
        if os.path.isfile(candidate):
            return candidate

    # Retourne None si pythonw.exe n'a été trouvé dans aucun des emplacements recherchés
    return None


class DependencyManager:

    @staticmethod
    def install_and_verify_pywin32():

        # Vérifie si le module win32api est déjà installé
        # find_spec() -> retourne les informations du module s'il existe, sinon None
        if importlib.util.find_spec("win32api"):
            write_log_dev_file("pywin32 already installed", "INFO")
            return True

        # Enregistre le début de l'installation de pywin32 dans le fichier de log
        write_log_dev_file("Installing pywin32...", "INFO")

        # Construit le chemin vers le dossier site-packages de l'interpréteur Python actuel
        site_packages = Path(sys.executable).parent / "Lib" / "site-packages"

        # Parcourt les anciens dossiers liés à pywin32 qui peuvent empêcher une réinstallation propre
        for folder in ("win32", "pywin32_system32"):

            # Construit le chemin complet du dossier à vérifier
            path = site_packages / folder

            # Vérifie si le dossier existe avant de tenter sa suppression
            if path.exists():

                try:

                    # Supprime complètement le dossier et tout son contenu
                    shutil.rmtree(path)

                    # Enregistre la suppression du dossier dans le fichier de log
                    write_log_dev_file(f"Removed {folder}", "INFO")

                except PermissionError as exc:

                    # Enregistre une erreur si le dossier est utilisé ou protégé par un autre processus
                    write_log_dev_file(f"Impossible de supprimer {folder} (fermez IDE/console) " f"| exception={type(exc).__name__}: {exc}\n{traceback.format_exc()}", "ERROR")

        try:

            # Réinstalle la version 305 de pywin32 avec le même interpréteur Python que l'application
            # --force-reinstall -> force la réinstallation même si le package est déjà présent
            subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "pywin32==305"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Enregistre la réussite de l'installation de pywin32
            write_log_dev_file("pywin32 installed successfully", "INFO")

        except subprocess.CalledProcessError as exc:

            # Enregistre l'échec de l'installation de pywin32
            write_log_dev_file("Failed to install pywin32 " f"| exception={type(exc).__name__}: {exc} " f"| returncode={exc.returncode}\n{traceback.format_exc()}", "ERROR")
            return False

        # Construit le chemin vers le script de post-installation de pywin32
        postinstall_script = Path(sys.executable).parent / "Scripts" / "pywin32_postinstall.py"

        # Vérifie si le script de post-installation existe
        if postinstall_script.exists():

            try:

                # Exécute le script de post-installation de pywin32
                # -install -> effectue les opérations nécessaires après l'installation
                subprocess.run([sys.executable, str(postinstall_script), "-install"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Enregistre la réussite de la post-installation
                write_log_dev_file("Post-installation completed", "INFO")

            except subprocess.CalledProcessError as exc:

                # Enregistre l'échec de la post-installation de pywin32
                write_log_dev_file("Failed post-installation pywin32 " f"| exception={type(exc).__name__}: {exc} " f"| returncode={exc.returncode}\n{traceback.format_exc()}", "ERROR")
                return False

        # Enregistre le redémarrage prochain de l'application
        write_log_dev_file("Restarting script in 10s...", "INFO")

        # Attend 10 secondes avant de redémarrer l'application
        time.sleep(10)

        # Relance le script actuel avec le même interpréteur Python
        subprocess.run([sys.executable, sys.argv[0]])

        # Arrête le processus actuel après le lancement de la nouvelle instance
        # 0 -> indique une sortie normale du programme
        sys.exit(0)

    @staticmethod
    def install_and_import(package, module_name=None, required_import=None, version=None):

        # Utilise le nom du module fourni ou, à défaut, le nom du package
        module_to_import = module_name or package

        # Construit le nom du package à installer avec sa version si elle est spécifiée
        # Exemple -> requests + 2.31.0 devient requests==2.31.0
        install_spec = f"{package}=={version}" if version else package

        try:

            # Tente d'importer le module pour vérifier s'il est déjà disponible
            module = importlib.import_module(module_to_import)

            # Vérifie également l'import d'un sous-module requis s'il est spécifié
            if required_import:
                importlib.import_module(f"{module_to_import}.{required_import}")

            # Retourne le module lorsqu'il est disponible
            return module

        except (ModuleNotFoundError, ImportError):

            # Enregistre le début de l'installation du package
            write_log_dev_file(f"Installing {package}...", "INFO")

            try:

                # Met à jour pip vers la version 23.3 avant l'installation du package
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip==23.3"])

            except subprocess.CalledProcessError as exc:

                # Enregistre l'échec de la mise à jour de pip
                write_log_dev_file("Error updating pip " f"| exception={type(exc).__name__}: {exc} " f"| returncode={exc.returncode}\n{traceback.format_exc()}", "ERROR")
                sys.exit(1)

            try:

                # Installe le package avec la version demandée si elle est spécifiée
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])

                # Enregistre la réussite de l'installation du package
                write_log_dev_file(f"{package} installed", "INFO")

            except subprocess.CalledProcessError as exc:

                # Enregistre l'échec de l'installation du package
                write_log_dev_file( f"Error installing {package} " f"| exception={type(exc).__name__}: {exc} " f"| install_spec={install_spec} " f"| returncode={exc.returncode}\n{traceback.format_exc()}", "ERROR" )
                sys.exit(1)

            try:

                # Réimporte le module après son installation pour vérifier qu'il est maintenant disponible
                return importlib.import_module(module_to_import)

            except ImportError as exc:

                # Enregistre l'échec de l'importation après l'installation
                write_log_dev_file(f"Error importing {module_to_import} " f"| exception={type(exc).__name__}: {exc} " f"| package={package}\n{traceback.format_exc()}", "ERROR")
                sys.exit(1)


def encrypt_message(plaintext: str, key_bytes: bytes):
    # Importe Base64 pour convertir les données binaires chiffrées
    # en une chaîne de caractères facilement stockable ou transmissible
    import base64

    # Importe le module de padding PKCS7 utilisé pour compléter les données
    # afin qu'elles correspondent à la taille des blocs AES
    from cryptography.hazmat.primitives import padding

    # Importe les composants nécessaires pour créer le chiffrement AES-CBC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    try:
        # Vérifie que la clé AES contient exactement 32 octets
        # 32 octets = 256 bits -> clé AES-256
        if len(key_bytes) != 32:
            # Enregistre une erreur si la taille de la clé est incorrecte
            write_log_dev_file("Invalid AES key length", level="ERROR")

            # Indique que le chiffrement n'a pas pu être effectué
            return False

        # Crée un objet PKCS7 permettant d'ajouter le padding nécessaire
        # AES fonctionne avec des blocs de 128 bits, soit 16 octets
        padder = padding.PKCS7(128).padder()

        # Convertit le texte en bytes avec l'encodage UTF-8
        # puis ajoute le padding PKCS7 nécessaire avant le chiffrement
        padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

        # Génère un IV aléatoire de 16 octets
        # L'IV correspond à la taille d'un bloc AES et doit être différent
        # pour chaque opération de chiffrement
        iv = os.urandom(16)

        # Configure le chiffrement AES-256 avec le mode CBC
        # key_bytes -> clé secrète utilisée pour le chiffrement
        # iv -> vecteur d'initialisation utilisé par le mode CBC
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))

        # Crée l'objet chargé d'effectuer le chiffrement des données
        encryptor = cipher.encryptor()

        # Chiffre les données après padding puis finalise le chiffrement
        # Le résultat contient l'IV au début afin qu'il puisse être utilisé
        # ultérieurement lors du déchiffrement
        encrypted = base64.b64encode(iv + (encryptor.update(padded) + encryptor.finalize())).decode("utf-8")

        # Retourne les données chiffrées sous forme de chaîne Base64
        return encrypted

    except Exception as e:
        # Enregistre l'erreur sans exposer le contenu du message ou de la clé
        # (la traceback ne contient que le code, jamais les valeurs sensibles)
        write_log_dev_file("AES-CBC encryption failed " f"| exception={type(e).__name__}: {e}\n{traceback.format_exc()}", level="ERROR")

        # Indique que le chiffrement a échoué
        return False


class UpdateManager:

    @staticmethod
    def _read_local_version(path):
        # Enregistre le début de la lecture de la version locale
        # path -> chemin du fichier contenant la version du programme
        write_log_dev_file(f"Reading local program version: path={path}", "DEBUG")

        # Vérifie que le chemin est fourni et que le fichier existe
        if not path or not os.path.exists(path):
            # Enregistre l'absence du fichier de version locale
            write_log_dev_file(f"Local program version not found: path={path}", "ERROR")

            # Retourne None pour indiquer qu'aucune version locale n'a été trouvée
            return None

        try:
            # Ouvre le fichier en lecture avec l'encodage UTF-8
            # read() -> récupère le contenu complet du fichier
            # strip() -> supprime les espaces et retours à la ligne inutiles
            version = open(path, "r", encoding="utf-8").read().strip()

            # Enregistre la version locale récupérée
            write_log_dev_file(f"Local program version read: {version}", "INFO")

            # Retourne la version locale
            return version

        except Exception as e:
            # Enregistre l'erreur rencontrée pendant la lecture
            write_log_dev_file("Error reading local program version " f"| exception={type(e).__name__}: {e} " f"| path={path}\n{traceback.format_exc()}", "ERROR")

            # Retourne None pour indiquer que la lecture a échoué
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir, clean_target=False, extract_subdir=None, progress_callback=None):
        try:
            # Enregistre les paramètres utilisés pour le téléchargement
            # zip_url -> URL de l'archive
            # target_dir -> dossier de destination
            # clean_target -> indique si le dossier cible doit être supprimé
            # extract_subdir -> sous-dossier éventuel à utiliser après extraction
            write_log_dev_file(f"Starting program update download: url={zip_url}, " f"target={target_dir}, clean_target={clean_target}, " f"extract_subdir={extract_subdir}", "INFO")

            # Crée un dossier temporaire automatiquement supprimé à la fin du bloc
            with tempfile.TemporaryDirectory() as tmpdir:
                # Définit le chemin du fichier ZIP temporaire
                zip_path = os.path.join(tmpdir, "update.zip")

                # Importe requests uniquement lorsque la fonction est utilisée
                import requests

                # Télécharge l'archive ZIP progressivement
                # stream=True -> évite de charger tout le fichier en mémoire
                # timeout=60 -> limite l'attente à 60 secondes
                # verify=True -> vérifie le certificat HTTPS
                with requests.get(zip_url, stream=True, headers=HEADER, timeout=60, verify=True) as r:
                    # Génère une exception si la réponse HTTP indique une erreur
                    r.raise_for_status()

                    # Enregistre les informations principales de la réponse HTTP
                    write_log_dev_file(
                        "Program update download response: "
                        f"status={r.status_code}, "
                        f"content_type={r.headers.get('Content-Type', '')}, "
                        f"content_length={r.headers.get('Content-Length', '')}, "
                        f"content_disposition={r.headers.get('Content-Disposition', '')}",
                        "DEBUG",
                    )

                    # Initialise le nombre total d'octets téléchargés
                    downloaded_bytes = 0

                    # Stocke les premiers octets pour faciliter l'identification du contenu
                    first_bytes = b""

                    # Récupère la taille totale annoncée par le serveur
                    content_length = int(r.headers.get("Content-Length") or 0)

                    # Ouvre le fichier ZIP temporaire en écriture binaire
                    with open(zip_path, "wb") as f:
                        # Parcourt la réponse par blocs de 8192 octets
                        for chunk in r.iter_content(8192):
                            # Ignore les blocs vides
                            if chunk:
                                # Conserve les 32 premiers octets reçus
                                if not first_bytes:
                                    first_bytes = chunk[:32]

                                # Met à jour le compteur d'octets téléchargés
                                downloaded_bytes += len(chunk)

                                # Écrit le bloc dans le fichier ZIP
                                f.write(chunk)

                                # Met à jour la progression du téléchargement
                                if progress_callback and content_length:
                                    progress_callback("Downloading update...", min(75, int(downloaded_bytes * 75 / content_length)))

                # Enregistre la taille reçue et la signature du fichier
                write_log_dev_file(f"Download response body received: bytes={downloaded_bytes}, " f"signature={first_bytes[:4].hex() if first_bytes else 'empty'}", "DEBUG")

                # Vérifie que le serveur a envoyé des données
                if downloaded_bytes == 0:
                    raise RuntimeError("The server returned HTTP 200 but the ZIP response body is empty.")

                # Vérifie que le fichier téléchargé est bien une archive ZIP
                if not zipfile.is_zipfile(zip_path):
                    # Enregistre les premiers octets pour faciliter le diagnostic
                    write_log_dev_file(f"Non-ZIP response detected: prefix={first_bytes[:32]!r}", "ERROR")

                    # Signale que la réponse n'est pas une archive ZIP valide
                    raise zipfile.BadZipFile("The server response is not a valid ZIP archive.")

                # Enregistre que le téléchargement est terminé
                write_log_dev_file(f"Program ZIP downloaded successfully: path={zip_path}, bytes={downloaded_bytes}", "INFO")

                # Supprime le dossier cible uniquement si cela a été demandé
                if clean_target and os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    write_log_dev_file(f"Previous target directory removed: {target_dir}", "INFO")

                # Ouvre l'archive ZIP en lecture
                with zipfile.ZipFile(zip_path, "r") as z:
                    # Indique que l'installation de la mise à jour commence
                    if progress_callback:
                        progress_callback("Installing update...", 85)

                    # Enregistre le nombre d'éléments présents dans le ZIP
                    write_log_dev_file(f"Program ZIP contents: {len(z.namelist())} entries", "DEBUG")

                    # Extrait tous les fichiers dans le dossier temporaire
                    z.extractall(tmpdir)

                # Enregistre la fin de l'extraction
                write_log_dev_file("Temporary ZIP extraction completed.", "INFO")

                # Récupère les éléments extraits sauf le fichier ZIP
                extracted_entries = [entry for entry in os.listdir(tmpdir) if entry != "update.zip"]

                # Récupère uniquement les dossiers extraits
                extracted_directories = [entry for entry in extracted_entries if os.path.isdir(os.path.join(tmpdir, entry))]

                # Détermine si l'archive contient un seul dossier racine
                if len(extracted_entries) == 1 and len(extracted_directories) == 1:
                    # Utilise le dossier unique comme racine des fichiers
                    extracted_root = os.path.join(tmpdir, extracted_directories[0])

                    # Indique la structure détectée
                    extraction_layout = "single_root_directory"
                else:
                    # Les fichiers sont directement présents à la racine
                    extracted_root = tmpdir

                    # Indique la structure détectée
                    extraction_layout = "project_files_at_archive_root"

                # Enregistre la structure de l'archive détectée
                write_log_dev_file(f"Detected ZIP structure: layout={extraction_layout}, entries={len(extracted_entries)}", "DEBUG")

                # Détermine le dossier source à installer
                # Si extract_subdir n'est pas fourni, utilise la racine détectée
                extracted_dir = (  extracted_root if not extract_subdir else (os.path.join(extracted_root, extract_subdir) if os.path.exists(os.path.join(extracted_root, extract_subdir)) else extracted_root))

                # Enregistre le dossier source sélectionné
                write_log_dev_file(f"Selected program source directory: {extracted_dir}", "DEBUG")

                # Crée le dossier cible s'il n'existe pas
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Parcourt tous les fichiers et dossiers à installer
                for item in os.listdir(extracted_dir):
                    # Construit le chemin source
                    src = os.path.join(extracted_dir, item)

                    # Construit le chemin destination
                    dst = os.path.join(target_dir, item)

                    # Vérifie si l'élément est un dossier
                    if os.path.isdir(src):
                        # Supprime le dossier existant avant de placer la nouvelle version
                        if os.path.exists(dst):
                            shutil.rmtree(dst)

                        # Déplace le nouveau dossier vers la destination
                        shutil.move(src, dst)
                    else:
                        # Déplace directement le fichier vers la destination
                        shutil.move(src, dst)

                # Enregistre la fin de l'installation
                write_log_dev_file(f"Program update extracted to: {target_dir}", "INFO")

                # Informe l'interface que la mise à jour est terminée
                if progress_callback:
                    progress_callback("Update completed.", 100)

                # Indique que le téléchargement et l'installation ont réussi
                return True

        except Exception as e:
            # Enregistre l'erreur principale
            write_log_dev_file(f"Program update download/extraction error: {e}", "ERROR")

            # Enregistre la stack trace complète pour faciliter le diagnostic
            write_log_dev_file(traceback.format_exc(), "DEBUG")

            # Relance l'exception afin que la fonction appelante puisse la gérer
            raise

    @staticmethod
    def check_and_update(progress_callback=None):
        # Fonction locale utilisée pour transmettre la progression
        # uniquement lorsqu'un callback a été fourni
        def report_progress(message, value):
            if progress_callback:
                progress_callback(message, value)

        # Enregistre le début de la vérification des mises à jour
        write_log_dev_file("=== CHECK PROGRAM UPDATE START ===", "INFO")

        # Informe l'interface que la vérification commence
        report_progress("Checking program version...", 10)

        # Importe requests pour communiquer avec le serveur
        import requests

        # Récupère la date actuelle au format YYYY-MM-DD
        session_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Enregistre la date utilisée pour le contrôle
        write_log_dev_file(f"Date used for program update check: {session_date}", "DEBUG")

        # Chiffre la date avec la clé configurée
        date_encrypted = encrypt_message(session_date, KEY)

        # Vérifie que le chiffrement a réussi
        if not date_encrypted:
            # Enregistre l'échec du chiffrement
            write_log_dev_file("Failed to encrypt date for program update check.", "ERROR")

            # Arrête le programme car la vérification ne peut pas continuer
            sys.exit("Encryption failed, exiting program.")

        # Construit l'URL utilisée pour vérifier la version distante
        url = f"https://reporting.nrb-apps.com/APP_R/redirect.php?" f"nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"

        # Ancienne URL de téléchargement conservée uniquement comme référence
        # PROGRAM_DOWNLOAD_URL = f"https://reporting.nrb-apps.com/APP_R/redirect.php?nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"

        # Ancienne version multi-ligne du lien de téléchargement
        # PROGRAM_DOWNLOAD_URL = (
        #     "https://reporting.nrb-apps.com/APP_R/redirect.php?"
        #     f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"
        # )

        # Définit l'URL actuellement utilisée pour télécharger la mise à jour
        PROGRAM_DOWNLOAD_URL = "https://github.com/Azedize/Automation-Gmail---Copie/archive/refs/heads/main.zip"

        # Enregistre l'URL utilisée pour vérifier la version
        write_log_dev_file(f"Program version check URL: {url}", "INFO")

        # Enregistre uniquement une indication générale du point de téléchargement
        # afin d'éviter d'exposer un éventuel token dans les logs
        write_log_dev_file("Program download URL: reporting.nrb-apps.com/APP_R/redirect.php (token hidden)", "DEBUG")

        # Effectue au maximum trois tentatives de vérification
        for attempt in range(1, 4):
            try:
                # Enregistre le numéro de la tentative actuelle
                write_log_dev_file(f"Program version check attempt: {attempt}/3", "INFO")

                # Envoie la requête au serveur de vérification
                response = requests.get(url, headers=HEADER, timeout=10)

                # Enregistre le statut HTTP et la taille de la réponse
                write_log_dev_file(f"Program server response: status={response.status_code}, " f"content_length={response.headers.get('content-length')}", "DEBUG")

                # Vérifie que le serveur a retourné HTTP 200
                if response.status_code != 200:
                    # Enregistre l'échec de la tentative
                    write_log_dev_file(f"Failed to retrieve program version: " f"attempt={attempt}, status={response.status_code}", "ERROR")

                    # Réessaie après deux secondes si des tentatives sont disponibles
                    if attempt < 3:
                        time.sleep(2)
                        continue

                    # Après trois échecs, le programme continue avec la version locale
                    write_log_dev_file("Version check unavailable; using local program version.", "WARNING")

                    # None indique que la vérification distante n'a pas abouti
                    return None

                # Convertit la réponse JSON en objet Python
                data = response.json()

                # Informe l'interface que la version distante a été reçue
                report_progress("Program version received.", 25)

                # Enregistre les données retournées par le serveur
                write_log_dev_file(f"Program version data received: {data}", "DEBUG")

                # Lit la version actuellement installée
                local_program = UpdateManager._read_local_version(os.path.join("config", "version.txt"))

                # Récupère la version disponible sur le serveur
                remote_program = data.get("version")

                # Enregistre les deux versions pour le diagnostic
                write_log_dev_file(f"Comparing program versions: local={local_program}, remote={remote_program}", "INFO")

                # Vérifie si une mise à jour est nécessaire
                # Une mise à jour est demandée si la version locale est absente
                # ou si elle est différente de la version distante
                if not local_program or local_program != remote_program:
                    # Enregistre qu'une mise à jour est nécessaire
                    write_log_dev_file(f"Program update required: local={local_program}, remote={remote_program}", "INFO")

                    try:
                        # Télécharge, extrait et installe la nouvelle version
                        downloaded = UpdateManager._download_and_extract(PROGRAM_DOWNLOAD_URL, ROOT_DIR, clean_target=False, extract_subdir=None, progress_callback=report_progress)

                    except Exception as e:
                        # Enregistre l'échec de la mise à jour
                        write_log_dev_file("Required program update download failed " f"| exception={type(e).__name__}: {e} " f"| url={PROGRAM_DOWNLOAD_URL}\n{traceback.format_exc()}", "ERROR")

                        # Retourne un état spécifique indiquant l'échec
                        return "update_failed"

                    # Vérifie que l'installation a réellement réussi
                    if not downloaded:
                        # Enregistre l'échec de l'installation
                        write_log_dev_file("Program update failed after download/extraction.", "ERROR")

                        # Retourne l'état d'échec
                        return "update_failed"

                    # Enregistre la réussite de la mise à jour
                    write_log_dev_file("Program update completed successfully.", "INFO")

                    # Enregistre la fin du processus avec mise à jour
                    write_log_dev_file("=== CHECK PROGRAM UPDATE END (UPDATED) ===", "INFO")

                    # True indique qu'une mise à jour a été installée
                    return True

                # Enregistre que le programme est déjà à jour
                write_log_dev_file(f"Program is up to date: local={local_program}, remote={remote_program}", "INFO")

                # Informe l'interface que le programme est à jour
                report_progress("Program is up to date.", 100)

                # Enregistre la fin du processus sans mise à jour
                write_log_dev_file("=== CHECK PROGRAM UPDATE END (OK) ===", "INFO")

                # False indique qu'aucune mise à jour n'était nécessaire
                return False

            except Exception as e:
                # Enregistre toute erreur inattendue pendant la tentative actuelle
                write_log_dev_file(f"Critical program update check error: attempt={attempt}, error={e}", "ERROR")

                # Enregistre la stack trace complète pour le diagnostic
                write_log_dev_file(traceback.format_exc(), "DEBUG")

                # Effectue une nouvelle tentative après deux secondes
                if attempt < 3:
                    time.sleep(2)
                    continue

                # Après trois échecs, continue avec la version locale
                write_log_dev_file("Version check unavailable after 3 attempts; using local program version.", "WARNING")

                # None indique que le serveur de version n'a pas pu être vérifié
                return None


def initialize_dependencies():

    # Enregistre le début de l'initialisation des dépendances
    write_log_dev_file("Dependency initialization started", level="INFO")

    # Vérifie et installe pywin32 si nécessaire
    # Cette dépendance peut également nécessiter une étape de post-installation
    DependencyManager.install_and_verify_pywin32()

    # Initialise toutes les dépendances nécessaires dans l'espace global
    # Chaque dépendance est importée et installée automatiquement si nécessaire
    globals().update(
        {
            # Importe requests et l'installe automatiquement si elle est absente
            "requests": DependencyManager.install_and_import("requests"),
            # Importe urllib3 avec une version précise
            "urllib3": DependencyManager.install_and_import("urllib3", version="2.2.3"),
            # Importe PyQt6 avec une version précise
            # required_import="QtCore" vérifie également que PyQt6.QtCore est disponible
            "PyQt6": DependencyManager.install_and_import("PyQt6", version="6.7.0", required_import="QtCore"),
            # Importe cryptography avec la version spécifiée
            "cryptography_module": DependencyManager.install_and_import("cryptography", version="3.3.2"),
            # Importe psutil et l'installe automatiquement si nécessaire
            "psutil": DependencyManager.install_and_import("psutil"),
            # Importe pytz et l'installe automatiquement si nécessaire
            "pytz": DependencyManager.install_and_import("pytz"),
            # Importe tqdm et l'installe automatiquement si nécessaire
            "tqdm": DependencyManager.install_and_import("tqdm"),
            # Importe platformdirs et l'installe automatiquement si nécessaire
            "platformdirs": DependencyManager.install_and_import("platformdirs"),
            # Importe Selenium avec une version précise
            # required_import="webdriver" vérifie également selenium.webdriver
            "selenium": DependencyManager.install_and_import("selenium", required_import="webdriver", version="4.27.1"),
            # Importe colorama et l'installe automatiquement si nécessaire
            "colorama": DependencyManager.install_and_import("colorama"),
            # Importe SQLAlchemy et l'installe automatiquement si nécessaire
            "sqlalchemy": DependencyManager.install_and_import("sqlalchemy"),
            # Importe watchdog et vérifie également la disponibilité de son module observers
            "watchdog": DependencyManager.install_and_import("watchdog", required_import="observers"),
        }
    )

    # Vérifie que urllib3 a bien été initialisé
    if urllib3:
        # Désactive uniquement les avertissements InsecureRequestWarning
        # Cela masque les avertissements liés à certaines connexions HTTPS
        # mais ne rend pas une connexion non sécurisée plus sûre
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    # Vérifie si l'application est exécutée sous Windows
    if sys.platform == "win32":
        import ctypes

        # Récupère la fenêtre console actuelle puis la masque
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    try:
        # Vide le fichier de log avant de démarrer une nouvelle exécution
        clear_log()

        # Enregistre le démarrage de l'application
        write_log_dev_file("Main application startup", level="INFO")

        # Initialise et vérifie toutes les dépendances nécessaires
        initialize_dependencies()

        # Enregistre la fin de l'initialisation des dépendances
        write_log_dev_file("Dependency initialization completed.", "INFO")

        # Recherche pythonw.exe dans l'installation Python et dans le PATH
        pythonw_path = find_pythonw()

        # Arrête l'application si pythonw.exe est introuvable
        if not pythonw_path:
            write_log_dev_file("pythonw.exe not found; application startup is impossible.", "ERROR")
            sys.exit(1)

        # Enregistre le chemin de pythonw.exe détecté
        write_log_dev_file(f"pythonw.exe detected: {pythonw_path}", "INFO")

        # Référence vers l'application Qt utilisée par la fenêtre de progression
        progress_app = None

        # Référence vers la fenêtre de progression de mise à jour
        update_progress = None

        # Stocke le moment où la vérification de mise à jour commence
        update_started_at = None

        def update_progress_callback(message, value):
            nonlocal progress_app, update_progress, update_started_at

            # Crée la fenêtre de progression uniquement lors du premier appel
            if update_progress is None:
                from PyQt6.QtCore import Qt
                from PyQt6.QtWidgets import QApplication, QProgressDialog

                # Récupère l'application Qt existante ou crée une nouvelle instance
                progress_app = QApplication.instance() or QApplication(sys.argv)

                # Crée la boîte de dialogue de progression
                update_progress = QProgressDialog("Starting application...", "", 0, 100)

                # Définit le titre de la fenêtre
                update_progress.setWindowTitle("AutoMailPro Update")

                # Bloque les autres fenêtres pendant la vérification
                update_progress.setWindowModality(Qt.WindowModality.ApplicationModal)

                # Empêche la fermeture automatique de la fenêtre
                update_progress.setAutoClose(False)

                # Empêche la réinitialisation automatique de la progression
                update_progress.setAutoReset(False)

                # Supprime le bouton d'annulation
                update_progress.setCancelButton(None)

                # Affiche immédiatement la fenêtre
                update_progress.setMinimumDuration(0)

                # Initialise la progression à 0 %
                update_progress.setValue(0)

                # Affiche la fenêtre
                update_progress.show()

                # Enregistre le moment de création de la fenêtre
                update_started_at = time.monotonic()

                # Force Qt à traiter les événements de l'interface
                progress_app.processEvents()

            # Vérifie que la fenêtre de progression existe
            if update_progress is None:
                return

            # Met à jour le texte affiché
            update_progress.setLabelText(message)

            # Met à jour le pourcentage
            update_progress.setValue(value)

            # Rafraîchit immédiatement l'interface Qt
            progress_app.processEvents()

        try:
            # Affiche le début de la vérification de version
            update_progress_callback("Starting update check...", 0)

            # Vérifie la version distante et applique une mise à jour si nécessaire
            updated = UpdateManager.check_and_update(progress_callback=update_progress_callback)

            # Ferme la fenêtre de progression après la vérification
            if update_progress is not None:

                # Maintient la fenêtre visible pendant environ 5 secondes
                # lorsque le programme est déjà à jour
                if updated is False and update_started_at is not None:
                    while time.monotonic() - update_started_at < 5:
                        progress_app.processEvents()
                        time.sleep(0.05)

                # Ferme la fenêtre de progression
                update_progress.close()

            # Vérifie si le téléchargement de la mise à jour obligatoire a échoué
            if updated == "update_failed":
                write_log_dev_file("Required update failed; application will exit.", "ERROR")

                # Informe l'utilisateur de l'échec de la mise à jour
                show_update_failure_warning()

                # Arrête l'application
                sys.exit(1)

            # Vérifie si la version distante n'a pas pu être vérifiée
            if updated is None:
                write_log_dev_file("Unable to verify the latest program version; application will exit.", "ERROR")

                # Informe l'utilisateur que la version ne peut pas être vérifiée
                show_update_network_warning()

                # Arrête l'application car la vérification de version est obligatoire
                sys.exit(1)

            # Prépare le résultat de la vérification pour le log
            result = "update applied" if updated else "application already up to date"

            # Enregistre le résultat final de la vérification
            write_log_dev_file(f"Program update check result: {result}", "INFO")

        except Exception as e:
            # Ferme la fenêtre de progression en cas d'erreur
            if update_progress is not None:
                update_progress.close()

            # Enregistre l'erreur critique pendant la vérification de mise à jour
            write_log_dev_file("Fatal error during update " f"| exception={type(e).__name__}: {e}\n{traceback.format_exc()}", "CRITICAL")

            # Arrête l'application après une erreur critique
            sys.exit(1)

        # Vérifie si le programme a été lancé sans arguments supplémentaires
        if len(sys.argv) == 1:

            # Définit le chemin du script principal
            script_path = SCRIPT_DIR / "src" / "AppV2.py"

            # Enregistre le lancement du script principal
            write_log_dev_file(f"Starting main application: script={script_path}", "INFO")

            # Génère les clés nécessaires au lancement du programme principal
            encrypted_key, secret_key = generate_encrypted_key()

            # Vérifie que le script principal existe
            if script_path.is_file():

                # Lance le programme principal avec les clés générées
                subprocess.run([sys.executable, str(script_path), encrypted_key, secret_key])

                # Enregistre la fin du programme principal
                write_log_dev_file("Main application terminated.", "INFO")

            else:
                # Enregistre l'absence du script principal
                write_log_dev_file(f"Main application script not found: {script_path}", "ERROR")

                # Arrête l'application
                sys.exit(1)

    except Exception as e:
        # Enregistre toute erreur non gérée avec son type et son message
        write_log_dev_file("fatal_application_error", "ERROR", exception_type=type(e).__name__, error=str(e))

        # Arrête l'application après une erreur fatale
        sys.exit(1)


if __name__ == "__main__":
    # Lance l'application lorsque ce fichier est exécuté directement
    main()
