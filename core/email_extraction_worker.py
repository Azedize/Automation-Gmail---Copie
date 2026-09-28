# =============================================================================
# Module : email_extraction_worker.py
# Role   : thread de traitement (QThread) qui lance, pour chaque compte email,
#          un navigateur dedie (Firefox, IceDragon ou autre navigateur
#          Chromium) avec un profil propre et une URL chiffree contenant les
#          informations du compte. L'extension du navigateur execute ensuite
#          le scenario d'actions.
#
# Principe : traitement par lots (au plus « entered_number » navigateurs
# actifs a la fois), execution hors du thread graphique, communication via
# l'objet partage runtime_state et des signaux Qt.
# =============================================================================
#
# --- Imports de la bibliotheque standard ---
# datetime : horodatage du lancement des sessions Firefox.
import datetime

# json : serialisation du scenario d'actions et des informations de session.
import json

# os : chemins, creation de dossiers, liste des dossiers de logs.
import os

# shutil : suppression recursive des anciens dossiers de logs.
import shutil

# subprocess : lancement des navigateurs dans des processus separes.
import subprocess

# time : pauses entre les lancements.
import time

# traceback : pile d'appels complete dans les logs d'erreur.
import traceback

# deque : file d'attente efficace (retrait en tete en O(1)) des emails a traiter.
from collections import deque

# --- Import PyQt6 ---
# QThread : execution en arriere-plan ; pyqtSignal : declaration des signaux Qt.
from PyQt6.QtCore import QThread, pyqtSignal

# --- Imports internes au projet ---
# API_MANAGER : client de l'API distante (enregistrement des emails traites).
from api import API_MANAGER

# Settings : configuration centrale (chemins, cles, URL d'API, fonctions de log).
from config import Settings

# EncryptionService : chiffrement ; SessionManager : verification de la session.
from core import EncryptionService, SessionManager

# BrowserManager : profils, recherche de PID, sauvegarde des sessions navigateur.
from models import BrowserManager

# UIManager : utilitaires d'interface (reactivation du bouton Submit).
from ui_utils import UIManager

# ValidationUtils : lecture des champs, generation de mot de passe, dossiers.
from utils import ValidationUtils


# =============================================================================
# Classe EmailExtractionWorker
# -----------------------------------------------------------------------------
# Thread Qt parcourant la liste des comptes email et lancant un navigateur par
# compte, en limitant le nombre de navigateurs ouverts en meme temps.
# Le traitement se termine quand la file est vide ET qu'aucun email n'est
# encore actif, ou sur demande d'arret de l'utilisateur (stop_flag).
# =============================================================================
class EmailExtractionWorker(QThread):
    # --- Signaux Qt emis vers l'interface (communication thread-safe) ---
    # progress : message d'avancement (str).
    # finished : traitement termine (aucun argument).
    # stopped  : arret anticipe avec un message explicatif (str).
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    stopped = pyqtSignal(str)

    # Constructeur : recoit tout le necessaire au traitement.
    #   - window / main_window : fenetres de l'interface ;
    #   - data_list : comptes email a traiter (liste de dictionnaires) ;
    #   - SESSION_ID / unique_id : identifiants de session et de lot ;
    #   - entered_number : nombre maximum de navigateurs actifs en parallele ;
    #   - Browser_path / selected_Browser : executable et nom du navigateur ;
    #   - Isp : fournisseur de messagerie ; output_json_final : scenario d'actions ;
    #   - runtime_state : etat partage (files, emails actifs, PID, logs) ;
    #   - file_lock : verrou protegeant les acces concurrents a runtime_state.
    def __init__(self, window, data_list, SESSION_ID, entered_number, Browser_path, main_window, selected_Browser, Isp, unique_id, output_json_final, runtime_state, file_lock):
        # Initialise la classe mere QThread (obligatoire avant tout usage du thread).
        super().__init__()
        self.window = window
        self.data_list = data_list
        self.session_id = SESSION_ID
        self.entered_number = entered_number
        self.Browser_path = Browser_path
        # Drapeau d'arret : passe a True par l'exterieur pour interrompre la boucle.
        self.stop_flag = False
        self.emails_processed = 0
        # Nom du navigateur normalise (minuscules, sans espaces) ;
        # « unknown » si la valeur fournie n'est pas une chaine.
        self.selected_Browser = selected_Browser.strip().lower() if isinstance(selected_Browser, str) else "unknown"
        self.Isp = Isp
        self.unique_id = unique_id
        self.output_json_final = output_json_final
        self.runtime_state = runtime_state
        self.file_lock = file_lock

    # Ajoute un message a la liste de logs partagee (affichee par l'interface).
    def _logMessage(self, text):
        self.runtime_state.logs.append(text)

    # -------------------------------------------------------------------------
    # Construit l'URL chiffree passee au navigateur.
    #   1. Serialise le scenario (output_json_final) en JSON compact.
    #   2. Concatene toutes les infos du compte + session + scenario, separees
    #      par « ; ».
    #   3. Chiffre l'ensemble (AES-GCM) et l'ajoute en parametre « rep » de l'URL.
    # En cas d'erreur de chiffrement : journalise et renvoie une URL vide.
    # -------------------------------------------------------------------------
    def buildEncryptedUrl(self, ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email, output_json_final):
        # Etape 1 : JSON sans espaces superflus (separators) et accents conserves
        # (ensure_ascii=False).
        result_payload = json.dumps(output_json_final, ensure_ascii=False, separators=(",", ":"))
        # Etape 2 : assemblage de tous les champs dans une seule chaine.
        combined = f"{ip_address};{port};{login};{password};{profile_email};{profile_password};{recovery_email};{new_password};{new_recovery_email};{self.session_id};{result_payload}"
        try:
            # Etape 3 : chiffrement de la chaine puis construction de l'URL du proxy.
            b64 = EncryptionService.encrypt_aes_gcm("A9!fP3z$wQ8@rX7kM2#dN6^bH1&yL4t*", combined)
            url = f"{Settings.ENCRYPTED_PROXY_API}?rep={b64}"
        except Exception as error:
            Settings.write_log_dev_file(
                # Gestion d'erreur : journalise le contexte detaille (type d'exception, email,
                # proxy, session, navigateur) puis informe l'utilisateur ; l'URL reste vide.
                "Error encrypting data for URL "
                f"| exception={type(error).__name__}: {error} "
                f"| email={profile_email} "
                f"| proxy={ip_address}:{port} "
                f"| session_id={self.session_id} "
                f"| browser={self.selected_Browser}\n{traceback.format_exc()}",
                "ERROR",
            )
            self._logMessage(f"[ERROR] Echec du chiffrement de l'URL pour {profile_email} " f"({type(error).__name__})")
            url = ""
        return url

    # -------------------------------------------------------------------------
    # Convertit une valeur de PID (ex. « 1234;5678 ») en liste d'entiers.
    #   - None ou chaine vide -> liste vide (avec log de debogage) ;
    #   - decoupage sur « ; » ; seuls les segments numeriques sont convertis,
    #     les autres sont ignores avec un avertissement.
    # -------------------------------------------------------------------------
    def parsePidList(self, pid_value):
        # Aucune valeur fournie : rien a analyser.
        if pid_value is None:
            Settings.write_log_dev_file("_parse_pid_list received None pid_value", "DEBUG")
            return []
        # Normalisation en chaine sans espaces de bordure.
        pid_str = str(pid_value).strip()
        if not pid_str:
            Settings.write_log_dev_file("_parse_pid_list received empty pid string", "DEBUG")
            return []
        pids = []
        # Parcours de chaque segment separe par « ; ».
        for part in pid_str.split(";"):
            part = part.strip()
            # Seuls les segments composes uniquement de chiffres sont retenus.
            if part.isdigit():
                pids.append(int(part))
            # === Cas 3 : autres navigateurs Chromium (Chrome par defaut) ===
            else:
                Settings.write_log_dev_file(f"_parse_pid_list skipped non-digit segment: '{part}'", "WARNING")
        Settings.write_log_dev_file(f"_parse_pid_list parsed PIDs: {pids} from '{pid_str}'", "DEBUG")
        return pids

    # -------------------------------------------------------------------------
    # Methode principale du thread (appelee automatiquement par start()).
    #   1. Prepare la file d'attente et l'etat partage.
    #   2. Verifie la session (sinon arret immediat).
    #   3. Ecrit l'identifiant de session dans le fichier de l'extension.
    #   4. Boucle : tant qu'il reste des emails OU des emails actifs, lance le
    #      suivant selon le navigateur choisi, dans la limite autorisee.
    #   5. En fin de traitement : reactive le bouton Submit et emet finished.
    # -------------------------------------------------------------------------
    def run(self):
        self.runtime_state.selected_browser = self.selected_Browser
        # Etape 1 : file d'attente des emails a traiter.
        remaining_emails_queue = deque(self.data_list)
        self.runtime_state.remaining_emails = len(remaining_emails_queue)

        self._logMessage("[INFO] Processing started")
        Settings.write_log_dev_file(f"EmailExtractionWorker started with browser={self.selected_Browser} | Browser_path={self.Browser_path}", "INFO")

        # Etape 2 : verification de la validite de la session utilisateur.
        session_info = SessionManager.check_session()

        # Session invalide : signal d'arret vers l'interface, log, puis sortie.
        if not session_info["valid"]:
            self.stopped.emit("Session invalide. Veuillez vous reconnecter.")
            Settings.write_log_dev_file("Invalid session. Please reconnect.", "ERROR")
            return

        try:
            # Etape 3 : chemin du fichier de donnees de l'extension (dossier different
            # selon Firefox ou Chromium).
            extension_data_path = os.path.join((Settings.EXTENTION_EX3_FIREFOX if self.selected_Browser.lower() == "firefox" else Settings.EXTENTION_EX3_CHROMIUM), "data.txt")
            os.makedirs(os.path.dirname(extension_data_path), exist_ok=True)

            # Ecriture de l'identifiant de session dans ce fichier.
            with open(extension_data_path, "w", encoding="utf-8") as file:
                file.write(f"{self.session_id}\n")
            Settings.write_log_dev_file(f"Wrote session_id to extension data file: {extension_data_path}", "INFO")

        except Exception as error:
            Settings.write_log_dev_file(
                # Gestion d'erreur (non bloquante) : journalise le contexte (type, chemin,
                # session, navigateur) et informe l'utilisateur ; le traitement continue.
                "Failed to write session_id to extension data file "
                f"| exception={type(error).__name__}: {error} "
                f"| path={extension_data_path} "
                f"| session_id={self.session_id} "
                f"| browser={self.selected_Browser}\n{traceback.format_exc()}",
                "ERROR",
            )
            self._logMessage("[ERROR] Impossible d'ecrire le fichier de donnees de l'extension " f"({type(error).__name__})")

        # Etape 4 : boucle principale du traitement par lots.
        while remaining_emails_queue or self.runtime_state.active_emails:
            # Demande d'arret utilisateur : on stoppe proprement la boucle.
            if self.stop_flag:
                self.runtime_state.logs_running = False
                self._logMessage("[INFO] Processing interrupted by user.")
                Settings.write_log_dev_file("Processing interrupted by user.", "INFO")
                break

            if (
                # Nouveau lancement uniquement s'il reste de la place (actifs < limite)
                # et des emails en attente.
                len(self.runtime_state.active_emails) < self.entered_number
                and remaining_emails_queue
            ):
                # Retrait du prochain email en tete de file.
                next_email = remaining_emails_queue.popleft()
                self.runtime_state.remaining_emails = len(remaining_emails_queue)
                # Lecture de l'email en acceptant plusieurs orthographes de cle.
                email_value = ValidationUtils.getValueFromDictionary(next_email, ["email", "Email"])
                self._logMessage(f"[INFO] Processing the email:  {email_value}")
                Settings.write_log_dev_file(f"Processing the email: {email_value}", "INFO")

                try:
                    # Extraction de tous les champs du compte (email, mot de passe, proxy,
                    # identifiants, emails de recuperation), avec tolerance sur les noms de cle.
                    profile_email = ValidationUtils.getValueFromDictionary(next_email, ["email", "Email"])
                    profile_password = ValidationUtils.getValueFromDictionary(next_email, ["password_email", "passwordEmail"])
                    ip_address = ValidationUtils.getValueFromDictionary(next_email, ["ip_address", "ipAddress"])
                    port = ValidationUtils.getValueFromDictionary(next_email, ["port"])
                    login = ValidationUtils.getValueFromDictionary(next_email, ["login"])
                    password = ValidationUtils.getValueFromDictionary(next_email, ["password"])
                    recovery_email = ValidationUtils.getValueFromDictionary(next_email, ["recovery_email", "recoveryEmail"])
                    new_recovery_email = ValidationUtils.getValueFromDictionary(next_email, ["new_recovery_email", "neWrecoveryEmail"])

                    # Parametres envoyes a l'API pour enregistrer l'email en cours de traitement
                    # (identifiant chiffre ; proxy_login renseigne seulement si le login differe).
                    params = {
                        "l": EncryptionService.encrypt_message(session_info["username"], Settings.KEY),
                        "login": session_info["username"],
                        "entity": session_info["p_entity_Origine"],
                        "isp": self.Isp,
                        "action": json.dumps(self.output_json_final),
                        "email": email_value,
                        "password": "",
                        "proxy_ip": ip_address + ":" + port,
                        "proxy_login": (f"{login};{password}" if login != session_info["username"] else ""),
                        "email_recovery": "",
                        "line": "",
                        "app": "V4",
                        "e_pid": self.unique_id,
                    }

                    # Enregistrement cote API : renvoie l'identifiant insere.
                    inserted_id = str(API_MANAGER.saveEmail(params))
                    # Generation d'un mot de passe securise de 16 caracteres.
                    new_password = ValidationUtils.generateSecurePassword(16)

                    try:
                        # Nettoyage des dossiers de logs : on ne conserve que les plus recents.
                        os.makedirs(Settings.LOGS_DIRECTORY, exist_ok=True)
                        logs_subdirs = [
                            os.path.join(Settings.LOGS_DIRECTORY, directory) for directory in os.listdir(Settings.LOGS_DIRECTORY) if os.path.isdir(os.path.join(Settings.LOGS_DIRECTORY, directory))
                        ]
                        # Tri des sous-dossiers du plus ancien au plus recent (date de creation).
                        logs_subdirs.sort(key=os.path.getctime)

                        # S'il y a plus de 4 dossiers, on supprime les 4 plus anciens.
                        if len(logs_subdirs) > 4:
                            for directory_to_delete in logs_subdirs[:4]:
                                try:
                                    # Suppression recursive du dossier.
                                    shutil.rmtree(directory_to_delete)
                                except Exception as error:
                                    Settings.write_log_dev_file(
                                        # Gestion d'erreur : echec de suppression d'un dossier -> log detaille
                                        # (type, dossier, racine des logs), sans interrompre le nettoyage.
                                        "Error while deleting old log directory "
                                        f"| exception={type(error).__name__}: {error} "
                                        f"| directory={directory_to_delete} "
                                        f"| logs_root={Settings.LOGS_DIRECTORY}\n{traceback.format_exc()}",
                                        "ERROR",
                                    )

                    except Exception as error:
                        Settings.write_log_dev_file(
                            # Gestion d'erreur : acces/creation du dossier de logs impossible -> log
                            # detaille (type, racine, email, session) ; la liste est remise a vide.
                            "Error accessing or creating log directory "
                            f"| exception={type(error).__name__}: {error} "
                            f"| logs_root={Settings.LOGS_DIRECTORY} "
                            f"| email={profile_email} "
                            f"| session_id={self.session_id}\n{traceback.format_exc()}",
                            "ERROR",
                        )
                        logs_subdirs = []

                    # === Cas 1 : navigateur Firefox (lance via l'outil web-ext) ===
                    if self.selected_Browser.lower() == "firefox":
                        url = self.buildEncryptedUrl(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email, self.output_json_final)
                        # Creation (ou verification) du profil Firefox dedie a cet email.
                        firefox_profile_path = BrowserManager.createFirefoxProfile(profile_email)

                        # Echec de creation du profil : on passe a l'email suivant (continue).
                        if not firefox_profile_path:
                            Settings.write_log_dev_file(f"❌ [Firefox] Impossible de créer le profil Firefox pour {profile_email}", "ERROR")
                            self._logMessage(f"[ERROR] Impossible de créer le profil Firefox pour {profile_email}")
                            continue

                        Settings.write_log_dev_file(f"✅ [Firefox] Profil créé/vérifié: {firefox_profile_path}", "INFO")
                        # Recuperation du chemin de l'outil web-ext.
                        web_ext_path = Settings.get_web_ext_path()

                        # web-ext introuvable : on passe a l'email suivant.
                        if not web_ext_path:
                            Settings.write_log_dev_file("❌ [Firefox] web-ext non trouvé", "ERROR")
                            self._logMessage("[ERROR] web-ext introuvable")
                            continue

                        command = [
                            web_ext_path,
                            # Commande web-ext : profil, URL chiffree et options (conservation du
                            # profil, pas de rechargement automatique).
                            "run",
                            "--source-dir",
                            Settings.EXTENTION_EX3_FIREFOX,
                            "--firefox-profile",
                            os.path.join(Settings.FIREFOX_PROFILES, profile_email),
                            "--url",
                            f"{url}",
                            "--keep-profile-changes",
                            "--no-reload",
                        ]

                        Settings.write_log_dev_file(f"Launching Firefox with command: {command}", "DEBUG")
                        Settings.write_log_dev_file(f"Firefox profile directory: {os.path.join(Settings.FIREFOX_PROFILES, profile_email)}", "DEBUG")

                        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        # Memorisation du PID du processus lance dans l'etat partage.
                        self.runtime_state.process_pids.append(process.pid)
                        Settings.write_log_dev_file(f"Firefox web-ext PID: {process.pid}", "INFO")

                        # Recherche des PID reels de Firefox lies au profil ; si aucun n'est trouve,
                        # on attend 2 secondes et on reessaie (voir plus bas).
                        firefox_pids = BrowserManager.findFirefoxProcessIds(firefox_profile_path, process.pid)
                        if not firefox_pids:
                            Settings.write_log_dev_file("Aucune PID Firefox détectée immédiatement après lancement, attente de 2 secondes puis nouvelle recherche", "WARNING")
                            time.sleep(2)
                            firefox_pids = BrowserManager.findFirefoxProcessIds(firefox_profile_path, process.pid)

                        if not firefox_pids:
                            Settings.write_log_dev_file("Aucune PID Firefox fiable trouvée, utilisation du PID web-ext comme fallback", "WARNING")
                            firefox_pids = [process.pid]

                        # Dedoublonnage et tri des PID, puis assemblage en chaine « pid;pid ».
                        firefox_pids = sorted(set(firefox_pids))
                        firefox_pid_string = ";".join(str(pid) for pid in firefox_pids)
                        Settings.write_log_dev_file(f"Firefox PID list stored for profile {profile_email}: {firefox_pid_string}", "INFO")
                        # Dictionnaire decrivant la session Firefox (profil, PID, email, commande,
                        # horodatage), memorise dans l'etat partage.
                        firefox_session = {
                            "profile_name": profile_email,
                            "profile_path": firefox_profile_path,
                            "browser": "firefox",
                            "web_ext_pid": process.pid,
                            "firefox_pids": firefox_pids,
                            "email": profile_email,
                            "session_id": self.session_id,
                            "inserted_id": inserted_id,
                            "launch_command": command,
                            "launched_at": datetime.datetime.now().isoformat(),
                        }
                        self.runtime_state.firefox_sessions[profile_email] = firefox_session

                        Settings.write_log_dev_file(f"Firefox session map updated for {profile_email}: {json.dumps(firefox_session, ensure_ascii=False)}", "DEBUG")
                        # Sauvegarde des informations de session sur disque (suivi et fermeture
                        # ulterieure des processus).
                        BrowserManager.persistBrowserSessionInfo(
                            firefox_pids,
                            Settings.FIREFOX_PROFILES,
                            profile_email,
                            self.session_id,
                            self.selected_Browser.lower(),
                            inserted_id,
                            profile_path=firefox_profile_path,
                            web_ext_pid=process.pid,
                            profile_name=profile_email,
                        )
                        # Sous verrou : ajout de l'email a l'ensemble des emails actifs
                        # (protege les acces concurrents depuis d'autres threads).
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

                    # === Cas 2 : navigateur IceDragon (base Chromium) ===
                    elif self.selected_Browser == "icedragon":
                        url = self.buildEncryptedUrl(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email, self.output_json_final)
                        # Chemins et dossier de profils propres a IceDragon ; la commande charge
                        # l'extension et ouvre directement l'URL chiffree.
                        browser_paths = Settings.CHROMIUM_BROWSER_PATHS["icedragon"]
                        profile_dir = browser_paths["profiles"]
                        ValidationUtils.ensurePathExists(profile_dir, is_file=False)
                        command = [
                            self.Browser_path,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            f"--disable-extensions-except={Settings.EXTENTION_EX3_CHROMIUM}",
                            f"--load-extension={os.path.join(Settings.EXTENTION_EX3_CHROMIUM)}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                            f"{url}",
                        ]
                        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.runtime_state.process_pids.append(process.pid)
                        BrowserManager.persistBrowserSessionInfo(
                            process.pid, profile_dir, profile_email, self.session_id, self.selected_Browser, inserted_id, profile_path=os.path.join(profile_dir, profile_email)
                        )
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

                    else:
                        url = self.buildEncryptedUrl(ip_address, port, login, password, profile_email, profile_password, recovery_email, new_password, new_recovery_email, self.output_json_final)
                        # Dossier de profils selon le navigateur, avec repli sur les profils Chrome.
                        profile_dir = Settings.CHROMIUM_BROWSER_PATHS.get(self.selected_Browser, {"profiles": Settings.CHROME_PROFILES})["profiles"]
                        browser_executable = self.Browser_path
                        ValidationUtils.ensurePathExists(profile_dir, is_file=False)
                        command = [
                            browser_executable,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            "--lang=En-US",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                        ]
                        # Deux commandes : la premiere initialise le profil (sans URL), la seconde
                        # ouvre l'URL chiffree apres un delai.
                        command1 = [
                            browser_executable,
                            f"--user-data-dir={os.path.join(profile_dir, profile_email)}",
                            f"--profile-directory={profile_email}",
                            f"{url}",
                            "--lang=En-US",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-sync",
                            "--disable-popup-blocking",
                            "--disable-notifications",
                            "--disable-features=DownloadBubble",
                        ]
                        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.runtime_state.process_pids.append(process.pid)
                        # Pause pour laisser le profil s'initialiser avant d'ouvrir l'URL.
                        time.sleep(4)
                        process1 = subprocess.Popen(command1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.runtime_state.process_pids.append(process1.pid)
                        # Les deux PID sont enregistres ensemble (« pid;pid »).
                        session_pids = f"{process.pid};{process1.pid}"
                        BrowserManager.persistBrowserSessionInfo(
                            session_pids, profile_dir, profile_email, self.session_id, self.selected_Browser.lower(), inserted_id, profile_path=os.path.join(profile_dir, profile_email)
                        )
                        with self.file_lock:
                            self.runtime_state.active_emails.add(profile_email)

                    # Un email de plus a ete lance avec succes.
                    self.emails_processed += 1

                except Exception as error:
                    with self.file_lock:
                        self.runtime_state.active_emails.discard(profile_email)
                    Settings.write_log_dev_file(
                        # Gestion d'erreur du traitement d'un email : retrait de l'email des actifs
                        # (sous verrou), log tres detaille (type, email, navigateur, ISP, session,
                        # inserted_id, compteurs) et message d'echec affiche a l'utilisateur.
                        "Error processing email "
                        f"| exception={type(error).__name__}: {error} "
                        f"| email={profile_email} "
                        f"| browser={self.selected_Browser} "
                        f"| isp={self.Isp} "
                        f"| session_id={self.session_id} "
                        f"| inserted_id={locals().get('inserted_id', 'N/A')} "
                        f"| processed={self.emails_processed} "
                        f"| remaining={self.runtime_state.remaining_emails} "
                        f"| active={len(self.runtime_state.active_emails)}\n{traceback.format_exc()}",
                        "ERROR",
                    )
                    self._logMessage(f"[ERROR] Echec du traitement de l'email {profile_email} " f"({type(error).__name__}: {error})")
            # Pause d'une seconde entre deux tours de boucle (msleep = pause du thread Qt).
            self.msleep(1000)

        # Etape 5 : plus aucun email restant ; messages de fin de traitement.
        self.runtime_state.remaining_emails = 0
        self._logMessage("[INFO] Processing finished for all emails.")
        Settings.write_log_dev_file("Processing finished for all emails.", "INFO")
        # Reactivation du bouton Submit dans l'interface.
        UIManager.enableButton(self.window.submitButton)
        time.sleep(3)
        self.runtime_state.logs_running = False
        # Signal Qt informant l'interface que le traitement est termine.
        self.finished.emit()
