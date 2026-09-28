import os
import sys
import subprocess
import configparser
import traceback
from typing import Optional, List, Dict, Any
import psutil
import winreg
import win32gui
import win32process
import win32con
import time
from pathlib import Path


# ==========================================================
# Détermination de la racine du projet
# ==========================================================
#
# __file__ représente le fichier Python actuellement exécuté.
#
# Exemple :
#
# Project/
# ├── config.py
# ├── utils/
# └── browser/
#     └── browser_manager.py
#
# os.path.abspath(__file__)
#     -> chemin absolu de browser_manager.py
#
# os.path.dirname(...)
#     -> remonte vers le dossier browser/
#
# deuxième os.path.dirname(...)
#     -> remonte vers la racine Project/
#
# Cette valeur est ensuite utilisée pour permettre les imports
# absolus depuis la racine du projet.
# ==========================================================
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ==========================================================
# Ajout de la racine du projet dans sys.path
# ==========================================================
#
# sys.path contient les répertoires dans lesquels Python
# recherche les modules lors d'un import.
#
# On ajoute ROOT_DIR uniquement s'il n'est pas déjà présent
# afin d'éviter les doublons.
# ==========================================================
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# ==========================================================
# Importation des composants internes du projet
# ==========================================================
#
# Settings contient la configuration globale de l'application :
#
# - chemins des navigateurs ;
# - navigateurs supportés ;
# - chemins Firefox ;
# - patterns des processus ;
# - configuration du logging ;
# - etc.
#
# ValidationUtils contient les fonctions de validation utilisées
# par BrowserManager, notamment la vérification des chemins.
#
# Si un import échoue, l'application ne peut pas utiliser
# correctement BrowserManager.
# ==========================================================
try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    if "Settings" in globals():
        Settings.write_log_event(
            "browser_manager_import_failed",
            "ERROR",
            file=__file__,
            exception_type=type(e).__name__,
            error=str(e),
            traceback=traceback.format_exc(),
        )
    else:
        print(
            f"❌ Erreur d'importation dans file {__file__} : {e}\n"
            f"{traceback.format_exc()}"
        )
    sys.exit(1)


class BrowserManager:

    # ======================================================
    # get_browser_executable_path
    # ======================================================
    #
    # Recherche le chemin réel de l'exécutable d'un navigateur
    # à partir de son nom logique.
    #
    # Exemple :
    #
    #     "chrome"
    #
    # peut être converti en :
    #
    #     "chrome.exe"
    #
    # puis transmis à getBrowserExecutablePath() qui effectue
    # la recherche réelle dans le Registry Windows.
    #
    # Retour :
    #
    #     str  -> chemin trouvé
    #     None -> navigateur introuvable
    # ======================================================
    @staticmethod
    def get_browser_executable_path( browser_name: str ) -> Optional[str]:

        # --------------------------------------------------
        # Normalise le nom reçu :
        #
        # - browser_name or "" évite une erreur si la valeur
        #   reçue est None ;
        # - strip() supprime les espaces inutiles ;
        # - lower() permet une recherche insensible à la casse.
        # --------------------------------------------------
        executable = Settings.BROWSER_EXECUTABLES.get((browser_name or "").strip().lower()  )

        # --------------------------------------------------
        # Si un exécutable correspondant est trouvé dans
        # la configuration, délègue la recherche réelle à
        # getBrowserExecutablePath().
        #
        # Sinon, retourne None.
        # --------------------------------------------------
        return (  BrowserManager.getBrowserExecutablePath(executable)  if executable  else None )

    # ======================================================
    # getBrowserExecutablePath
    # ======================================================
    #
    # Recherche le chemin complet d'un navigateur dans
    # le Windows Registry.
    #
    # La méthode teste plusieurs emplacements :
    #
    # - HKEY_LOCAL_MACHINE 32 bits
    # - HKEY_LOCAL_MACHINE 64 bits
    # - HKEY_CURRENT_USER
    # - HKEY_LOCAL_MACHINE standard
    #
    # Cette stratégie permet de gérer plusieurs types
    # d'installation Windows.
    # ======================================================
    @staticmethod
    def getBrowserExecutablePath( browser_name_or_exe: str) -> Optional[str]:

        # --------------------------------------------------
        # Recherche d'abord si le nom fourni possède une
        # configuration détaillée dans Settings.SUPPORTED_BROWSERS.
        #
        # Si la configuration contient "exe_name", cette valeur
        # est utilisée.
        #
        # Sinon, la valeur reçue est conservée telle quelle.
        # --------------------------------------------------
        exe_name = Settings.SUPPORTED_BROWSERS.get(  browser_name_or_exe.lower(), {} ).get( "exe_name",  browser_name_or_exe   )

        # --------------------------------------------------
        # Journalise le début de la recherche.
        # --------------------------------------------------
        Settings.write_log_dev_file(
            f"🔍 Recherche du navigateur: {exe_name}",
            "INFO" )

        # --------------------------------------------------
        # Association entre les constantes Registry Windows
        # et leur représentation textuelle.
        #
        # Cela permet d'avoir des logs plus lisibles.
        # --------------------------------------------------
        HIVE_NAMES = {  winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE",  winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER"}

        # --------------------------------------------------
        # Liste des emplacements Registry à tester.
        #
        # KEY_WOW64_32KEY :
        #     recherche dans la vue 32 bits du Registry.
        #
        # KEY_WOW64_64KEY :
        #     recherche dans la vue 64 bits.
        #
        # Cela est important sur un Windows 64 bits lorsqu'un
        # navigateur est installé comme application 32 bits.
        # --------------------------------------------------
        registry_paths = [
            (
                winreg.HKEY_LOCAL_MACHINE,
                winreg.KEY_READ | winreg.KEY_WOW64_32KEY
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            ),
            (
                winreg.HKEY_CURRENT_USER,
                winreg.KEY_READ
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                winreg.KEY_READ
            )
        ]

        # --------------------------------------------------
        # Windows fournit un emplacement standard "App Paths"
        # permettant de retrouver le chemin d'un exécutable.
        #
        # Exemple :
        #
        # SOFTWARE\Microsoft\Windows\CurrentVersion\
        # App Paths\chrome.exe
        # --------------------------------------------------
        key_app_paths = (
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion"
            rf"\App Paths\{exe_name}" )

        # --------------------------------------------------
        # Teste chaque emplacement Registry.
        # --------------------------------------------------
        for hive, access in registry_paths:

            # ------------------------------------------------
            # Récupère un nom lisible du Registry Hive pour
            # les logs.
            # ------------------------------------------------
            hive_name = HIVE_NAMES.get(
  hive,   str(hive) )

            try:
                Settings.write_log_dev_file(
                    f"🔎 Recherche dans: {hive_name}",
                    "INFO"
                )

                # --------------------------------------------
                # Ouvre la clé Registry.
                #
                # Le contexte "with" garantit que la clé sera
                # correctement fermée après utilisation.
                # --------------------------------------------
                with winreg.OpenKey(
                    hive,
                    key_app_paths,
                    0,
                    access
                ) as key_obj:

                    # ----------------------------------------
                    # Récupère la valeur par défaut de la clé.
                    #
                    # Cette valeur contient normalement le
                    # chemin complet de l'exécutable.
                    # ----------------------------------------
                    path, _ = winreg.QueryValueEx(
                        key_obj,
                        None
                    )

                    if path:

                        # ------------------------------------
                        # Vérifie que le fichier existe réellement.
                        # ------------------------------------
                        if ValidationUtils.pathExists(path):

                            Settings.write_log_dev_file(
                                f"✅ Navigateur trouvé: {exe_name}",
                                "SUCCESS"
                            )

                            Settings.write_log_dev_file(
                                f"📂 Chemin: {path}",
                                "SUCCESS"
                            )

                            return path

                        else:
                            # --------------------------------
                            # Le Registry contient un chemin,
                            # mais le fichier n'existe plus.
                            # --------------------------------
                            Settings.write_log_dev_file(
                                "⚠️ Chemin trouvé mais "
                                f"fichier inexistant: {path}",
                                "WARNING"
                            )

            except FileNotFoundError:

                # ------------------------------------------------
                # La clé Registry n'existe pas dans cet emplacement.
                #
                # Ce n'est pas nécessairement une erreur critique :
                # le navigateur peut être installé ailleurs.
                # ------------------------------------------------
                Settings.write_log_dev_file(
                    f"❌ Non trouvé dans: {hive_name}",
                    "INFO"
                )

                continue

            except Exception as e:

                # ------------------------------------------------
                # Capture toute erreur inattendue liée au Registry.
                #
                # traceback.format_exc() fournit le stack trace
                # complet pour faciliter le diagnostic.
                # ------------------------------------------------
                Settings.write_log_dev_file(
                    f"🚨 Erreur registre ({hive_name}): "
                    f"{str(e)}\n{traceback.format_exc()}",
                    "ERROR"
                )

        # ------------------------------------------------------
        # Aucun emplacement Registry n'a permis de trouver
        # l'exécutable.
        # ------------------------------------------------------
        Settings.write_log_dev_file(
            f"❌ Navigateur introuvable: {exe_name}",
            "ERROR"
        )

        return None

    # ======================================================
    # persistBrowserSessionInfo
    # ======================================================
    #
    # Sauvegarde les informations nécessaires à une session
    # navigateur dans un fichier data.txt.
    #
    # Le format de l'entrée sauvegardée est :
    #
    #     PID:EMAIL:SESSION_ID:INSERTED_ID
    #
    # Selon le navigateur :
    #
    # Chrome/Chromium
    #     -> utilise le profile_path
    #
    # Firefox/autre
    #     -> utilise Path_DiR/email/data.txt
    # ======================================================
    @staticmethod
    def persistBrowserSessionInfo(
        pid: Any,
        Path_DiR: str,
        email: str,
        SESSION_ID: str,
        browser: str,
        inserted_id: str,
        profile_path: Optional[str] = None,
        web_ext_pid: Optional[int] = None,
        profile_name: Optional[str] = None
    ) -> None:

        # ==================================================
        # Normalisation du PID
        # ==================================================
        #
        # Firefox peut avoir plusieurs PIDs.
        # Les autres navigateurs sont généralement représentés
        # par un seul PID.
        # ==================================================
        def _normalize_pid_value(
            pid_value: Any,
            browser_key: str
        ) -> str:

            # ------------------------------------------------
            # Firefox peut recevoir plusieurs PIDs sous forme
            # de liste, tuple ou set.
            #
            # Ils sont convertis vers :
            #
            #     PID1;PID2;PID3
            # ------------------------------------------------
            if browser_key == "firefox":

                if isinstance(
                    pid_value,
                    (list, tuple, set)
                ):
                    return ";".join(
                        str(int(p))
                        for p in pid_value
                        if str(p).strip().isdigit()
                    )

                # --------------------------------------------
                # PID unique sous forme entière.
                # --------------------------------------------
                if isinstance(pid_value, int):
                    return str(pid_value)

                # --------------------------------------------
                # PID déjà sous forme de texte.
                # --------------------------------------------
                if isinstance(pid_value, str):
                    return pid_value.strip()

                # --------------------------------------------
                # Dernier fallback pour tout autre type.
                # --------------------------------------------
                return str(pid_value)

            # ------------------------------------------------
            # Pour les navigateurs autres que Firefox,
            # le comportement reste basé sur un PID unique.
            # ------------------------------------------------
            if isinstance(pid_value, int):
                return str(pid_value)

            if isinstance(pid_value, str):
                return pid_value.strip()

            return str(pid_value)

        # ==================================================
        # Écriture puis vérification du fichier
        # ==================================================
        #
        # Cette fonction interne réalise :
        #
        #     création dossier
        #          ↓
        #     écriture fichier
        #          ↓
        #     lecture fichier
        #          ↓
        #     comparaison
        #
        # Cela permet de détecter immédiatement une différence
        # entre le contenu demandé et le contenu réellement
        # enregistré sur disque.
        # ==================================================
        def _write_and_verify(
            target_path: Path,
            content: str,
            label: str
        ):

            # ------------------------------------------------
            # Crée les dossiers parents si nécessaire.
            #
            # parents=True :
            #     crée également les dossiers intermédiaires.
            #
            # exist_ok=True :
            #     ne provoque pas d'erreur si le dossier existe
            #     déjà.
            # ------------------------------------------------
            target_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # ------------------------------------------------
            # Écrit le contenu dans le fichier.
            # ------------------------------------------------
            target_path.write_text(
                f"{content}\n",
                encoding="utf-8"
            )

            # ------------------------------------------------
            # Relit immédiatement le fichier pour vérifier
            # ce qui a réellement été écrit.
            # ------------------------------------------------
            actual = target_path.read_text(
                encoding="utf-8"
            ).strip()

            # ------------------------------------------------
            # Journalise uniquement les tailles afin d'éviter
            # d'exposer directement le contenu du fichier.
            # ------------------------------------------------
            Settings.write_log_event(
                "browser_session_write_verified",
                "INFO",
                label=label,
                expected_length=len(content.strip()),
                actual_length=len(actual),
                file_written=target_path.name
            )

            # ------------------------------------------------
            # Compare le contenu attendu avec le contenu réel.
            # ------------------------------------------------
            if actual != content.strip():

                Settings.write_log_event(
                    "browser_session_write_mismatch",
                    "ERROR",
                    label=label,
                    expected_length=len(content.strip()),
                    actual_length=len(actual)
                )

        # ==================================================
        # Traitement principal de la sauvegarde
        # ==================================================
        try:

            # ------------------------------------------------
            # Normalise le nom du navigateur.
            # ------------------------------------------------
            browser_key = browser.strip().lower()

            # ------------------------------------------------
            # Normalise le ou les PIDs.
            # ------------------------------------------------
            normalized_pid = _normalize_pid_value(
                pid,
                browser_key
            )

            # ------------------------------------------------
            # Journalise les informations générales de la session.
            #
            # Les valeurs sensibles ne sont pas directement
            # enregistrées ici.
            # ------------------------------------------------
            Settings.write_log_event(
                "browser_session_info_prepared",
                "INFO",
                browser_key=browser_key,
                pid_value_type=type(pid).__name__,
                has_profile_path=bool(profile_path),
                has_web_ext_pid=bool(web_ext_pid),
                has_email=bool(email),
                has_session_id=bool(SESSION_ID)
            )

            # ------------------------------------------------
            # Construction de l'entrée qui sera stockée.
            #
            # Format :
            #
            # PID:EMAIL:SESSION_ID:INSERTED_ID
            # ------------------------------------------------
            session_entry = (
                f"{normalized_pid}:"
                f"{email}:"
                f"{SESSION_ID}:"
                f"{inserted_id}"
            )

            # ------------------------------------------------
            # Chemin utilisé pour Firefox/autres navigateurs.
            # ------------------------------------------------
            session_file = (
                Path(Path_DiR)
                / email
                / "data.txt"
            )

            # ==================================================
            # Gestion des navigateurs de la famille Chrome
            # ==================================================
            if browser_key in Settings.CHROME_FAMILY_BROWSERS:

                # ------------------------------------------------
                # Convertit le nom du navigateur en majuscules
                # pour les logs.
                # ------------------------------------------------
                browser_label = browser_key.upper()

                Settings.write_log_dev_file(
                    f"{browser_label} browser detected",
                    "INFO"
                )

                # ------------------------------------------------
                # Si aucun profile_path n'a été fourni, le code
                # utilise par défaut :
                #
                # Path_DiR/email
                # ------------------------------------------------
                if profile_path is None and email:

                    profile_path = str(
                        Path(Path_DiR) / email
                    )

                    Settings.write_log_dev_file(
                        "Inferred profile_path for Chrome "
                        f"family browser: {profile_path}",
                        "DEBUG"
                    )

                # ------------------------------------------------
                # Si le profile path est disponible, écrit
                # data.txt directement dans ce profile.
                # ------------------------------------------------
                if profile_path:

                    profile_data_file = (
                        Path(profile_path)
                        / "data.txt"
                    )

                    Settings.write_log_dev_file(
                        "Writing session entry to Chrome "
                        f"profile data file: {profile_data_file}",
                        "INFO"
                    )

                    _write_and_verify(
                        profile_data_file,
                        session_entry,
                        browser_label
                    )

                else:

                    # --------------------------------------------
                    # Impossible de déterminer où stocker la session.
                    # --------------------------------------------
                    Settings.write_log_dev_file(
                        "No profile_path provided for "
                        "Chrome session storage",
                        "ERROR"
                    )

            # ==================================================
            # Firefox ou autre navigateur
            # ==================================================
            else:

                Settings.write_log_dev_file(
                    f"Firefox or other browser detected: "
                    f"{browser_key}",
                    "INFO"
                )

                Settings.write_log_dev_file(
                    f"Session entry for Firefox write: "
                    f"'{session_entry}'",
                    "DEBUG"
                )

                Settings.write_log_dev_file(
                    f"Writing session to {session_file}",
                    "INFO"
                )

                _write_and_verify(
                    session_file,
                    session_entry,
                    "OTHER"
                )

            # ------------------------------------------------
            # Indique que le traitement est terminé.
            # ------------------------------------------------
            Settings.write_log_dev_file(
                "Session data stored successfully",
                "INFO"
            )

        except Exception as exc:

            # ------------------------------------------------
            # Capture toute erreur inattendue lors de la
            # sauvegarde de la session.
            # ------------------------------------------------
            Settings.write_log_event(
                "browser_session_store_failed",
                "ERROR",
                exception_type=type(exc).__name__,
                error=str(exc),
                browser_key=(
                    browser_key
                    if "browser_key" in locals()
                    else "unknown"
                ),
                traceback=traceback.format_exc(),
            )

    # ======================================================
    # getFirefoxProfileMap
    # ======================================================
    #
    # Lit le fichier Firefox profiles.ini et construit une
    # correspondance :
    #
    #     Nom du profil -> chemin complet
    #
    # Exemple :
    #
    # {
    #     "default": "C:\\...\\default",
    #     "work": "C:\\...\\work"
    # }
    # ======================================================
    @staticmethod
    def getFirefoxProfileMap() -> Dict[str, str]:

        Settings.write_log_dev_file(
            "[_get_firefox_profiles] "
            "Lecture des profils Firefox existants",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Récupère le chemin configuré dans Settings.
        #
        # Si aucun chemin n'est disponible, construit le chemin
        # standard de Firefox dans APPDATA.
        # ------------------------------------------------------
        ini_path = (
            getattr(
                Settings,
                "FIREFOX_PROFILES_INI",
                None
            )
            or os.path.join(
                Settings.APPDATA,
                "Mozilla",
                "Firefox",
                "profiles.ini"
            )
        )

        # ------------------------------------------------------
        # Conserve le chemin calculé dans Settings afin que
        # les appels suivants puissent le réutiliser.
        # ------------------------------------------------------
        Settings.FIREFOX_PROFILES_INI = ini_path

        Settings.write_log_dev_file(
            "[_get_firefox_profiles] Firefox profiles.ini "
            f"path stored in Settings: {ini_path}",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Vérifie que profiles.ini existe.
        # ------------------------------------------------------
        if not os.path.exists(ini_path):

            Settings.write_log_dev_file(
                "[_get_firefox_profiles] ⚠️ profiles.ini "
                f"non trouvé: {ini_path}",
                "WARNING"
            )

            return {}

        # ------------------------------------------------------
        # Création du lecteur INI.
        # ------------------------------------------------------
        config = configparser.ConfigParser()

        try:

            # --------------------------------------------------
            # Lecture du fichier profiles.ini.
            # --------------------------------------------------
            config.read(
                ini_path,
                encoding="utf-8"
            )

        except Exception as exc:

            Settings.write_log_event(
                "firefox_profiles_read_failed",
                "ERROR",
                exception_type=type(exc).__name__,
                error=str(exc),
                ini_path=ini_path,
                traceback=traceback.format_exc(),
            )

            return {}

        # ------------------------------------------------------
        # Le dossier contenant profiles.ini est la base utilisée
        # pour les chemins relatifs.
        # ------------------------------------------------------
        base_dir = os.path.dirname(ini_path)

        # ------------------------------------------------------
        # Dictionnaire final :
        #
        #     profile_name -> profile_path
        # ------------------------------------------------------
        profiles = {}

        try:

            # --------------------------------------------------
            # Parcourt toutes les sections du fichier INI.
            # --------------------------------------------------
            for section in config.sections():

                # ------------------------------------------------
                # On s'intéresse uniquement aux sections Profile.
                # ------------------------------------------------
                if section.startswith("Profile"):

                    # --------------------------------------------
                    # Nom du profil.
                    # --------------------------------------------
                    name = config.get(
                        section,
                        "Name",
                        fallback=None
                    )

                    # --------------------------------------------
                    # Chemin du profil.
                    # --------------------------------------------
                    path = config.get(
                        section,
                        "Path",
                        fallback=None
                    )

                    # --------------------------------------------
                    # IsRelative indique si le chemin est relatif.
                    #
                    # 1 -> relatif
                    # 0 -> absolu
                    # --------------------------------------------
                    is_rel = config.getint(
                        section,
                        "IsRelative",
                        fallback=1
                    )

                    # --------------------------------------------
                    # On ne crée une entrée que si Name et Path
                    # sont disponibles.
                    # --------------------------------------------
                    if name and path:

                        # ----------------------------------------
                        # Transforme le chemin relatif en chemin
                        # absolu à partir du dossier de Firefox.
                        # ----------------------------------------
                        full_path = (
                            os.path.join(base_dir, path)
                            if is_rel
                            else path
                        )

                        # ----------------------------------------
                        # Normalise le chemin pour supprimer les
                        # différences de format entre slash,
                        # backslash, etc.
                        # ----------------------------------------
                        profiles[name] = os.path.normpath(
                            full_path
                        )

                        Settings.write_log_dev_file(
                            f"  📌 Profil trouvé: {name} -> "
                            f"{profiles[name]}",
                            "DEBUG"
                        )

        except Exception as exc:

            Settings.write_log_event(
                "firefox_profiles_parse_failed",
                "ERROR",
                exception_type=type(exc).__name__,
                error=str(exc),
                ini_path=ini_path,
                traceback=traceback.format_exc(),
            )

        # ------------------------------------------------------
        # Journalise le nombre final de profils trouvés.
        # ------------------------------------------------------
        Settings.write_log_event(
            "firefox_profiles_loaded",
            "INFO",
            profile_count=len(profiles)
        )

        return profiles

    # ======================================================
    # findFirefoxProcessIds
    # ======================================================
    #
    # Recherche les PIDs Firefox associés à un profil donné
    # ou à un processus parent donné.
    #
    # Deux critères sont utilisés :
    #
    # 1. Le profile_path apparaît dans la command line.
    #
    # 2. Le PPID du processus correspond à parent_pid.
    #
    # Un seul des deux critères suffit.
    # ======================================================
    @staticmethod
    def findFirefoxProcessIds(
        profile_path: str,
        parent_pid: int
    ) -> List[int]:

        Settings.write_log_dev_file(
            "[find_firefox_pids] Recherche des PIDs Firefox "
            f"pour profile_path={profile_path}, "
            f"parent_pid={parent_pid}",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Utilisation d'un set pour éviter automatiquement
        # les doublons de PID.
        # ------------------------------------------------------
        pids = set()

        # ------------------------------------------------------
        # Normalise le profile path pour comparer sans tenir
        # compte de la casse.
        # ------------------------------------------------------
        profile_lower = profile_path.lower()

        # ------------------------------------------------------
        # Parcourt les processus actifs.
        #
        # Seules les informations nécessaires sont demandées.
        # ------------------------------------------------------
        for proc in psutil.process_iter(
            ["pid", "name", "ppid", "cmdline"]
        ):

            try:

                # ------------------------------------------------
                # Récupère le nom du processus.
                # ------------------------------------------------
                name = (
                    proc.info["name"] or ""
                ).lower()

                # ------------------------------------------------
                # Ignore immédiatement les processus qui ne sont
                # pas Firefox.
                # ------------------------------------------------
                if "firefox" not in name:
                    continue

                # ------------------------------------------------
                # Transforme la command line en une seule chaîne.
                # ------------------------------------------------
                cmdline = " ".join(
                    proc.info["cmdline"] or []
                ).lower()

                # ------------------------------------------------
                # Premier critère :
                # le chemin du profil est présent dans la
                # command line du processus.
                # ------------------------------------------------
                match_profile = (
                    profile_lower in cmdline
                )

                # ------------------------------------------------
                # Deuxième critère :
                # le processus possède le parent attendu.
                # ------------------------------------------------
                match_parent = (
                    proc.info.get("ppid")
                    == parent_pid
                )

                # ------------------------------------------------
                # Si l'un des deux critères correspond,
                # on considère le processus comme appartenant
                # à la session Firefox recherchée.
                # ------------------------------------------------
                if match_profile or match_parent:

                    pids.add(proc.pid)

                    Settings.write_log_dev_file(
                        "[find_firefox_pids] Match PID "
                        f"{proc.pid}: "
                        f"profile_match={match_profile}, "
                        f"parent_match={match_parent}, "
                        f"cmdline={cmdline[:200]}",
                        "DEBUG"
                    )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):
                # ------------------------------------------------
                # Le processus peut disparaître pendant le scan
                # ou être inaccessible.
                #
                # Ce comportement est normal avec un processus
                # système dynamique.
                # ------------------------------------------------
                continue

            except Exception as exc:

                Settings.write_log_event(
                    "firefox_pid_scan_failed",
                    "WARNING",
                    exception_type=type(exc).__name__,
                    error=str(exc),
                    profile_path=profile_path,
                    parent_pid=parent_pid,
                    traceback=traceback.format_exc(),
                )

                continue

        # ------------------------------------------------------
        # Conversion du set en liste triée.
        # ------------------------------------------------------
        result = sorted(pids)

        Settings.write_log_dev_file(
            f"[find_firefox_pids] Firefox PIDs found: {result}",
            "INFO"
        )

        return result

    # ======================================================
    # findChromiumProcessIds
    # ======================================================
    #
    # Recherche les PIDs des navigateurs Chromium liés à
    # un profile donné.
    #
    # La méthode utilise Settings.BROWSER_PROCESS_PATTERNS
    # afin de savoir quels noms de processus correspondent
    # au navigateur demandé.
    # ======================================================
    @staticmethod
    def findChromiumProcessIds(
        profile_path: str,
        browser_name: str
    ) -> List[int]:

        Settings.write_log_dev_file(
            "[find_chromium_pids] Searching Chromium PIDs "
            f"for profile_path={profile_path}, "
            f"browser_name={browser_name}",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Set utilisé pour éviter les doublons.
        # ------------------------------------------------------
        pids = set()

        # ------------------------------------------------------
        # Normalisation du profile path.
        # ------------------------------------------------------
        profile_lower = profile_path.lower()

        # ------------------------------------------------------
        # Normalisation du nom du navigateur.
        # ------------------------------------------------------
        browser_name_lower = (
            browser_name or ""
        ).lower()

        # ------------------------------------------------------
        # Récupère les patterns spécifiques au navigateur.
        #
        # Si aucun pattern n'est configuré, utilise une liste
        # de valeurs par défaut.
        # ------------------------------------------------------
        allowed_names = (
            Settings.BROWSER_PROCESS_PATTERNS.get(
                browser_name_lower,
                (
                    "chrome",
                    "edge",
                    "msedge",
                    "dragon",
                    "comodo",
                    "chromium"
                )
            )
        )

        # ------------------------------------------------------
        # Parcourt les processus.
        # ------------------------------------------------------
        for proc in psutil.process_iter(
            ["pid", "name", "cmdline"]
        ):

            try:

                # ------------------------------------------------
                # Récupère et normalise le nom du processus.
                # ------------------------------------------------
                name = (
                    proc.info["name"] or ""
                ).lower()

                # ------------------------------------------------
                # Vérifie si le nom du processus correspond à
                # au moins un des patterns autorisés.
                # ------------------------------------------------
                if not any(
                    term in name
                    for term in allowed_names
                ):
                    continue

                # ------------------------------------------------
                # Récupère la command line du processus.
                # ------------------------------------------------
                cmdline = " ".join(
                    proc.info.get("cmdline") or []
                ).lower()

                # ------------------------------------------------
                # Le processus est considéré comme appartenant
                # au profile si le profile path apparaît dans
                # sa command line.
                # ------------------------------------------------
                if profile_lower in cmdline:

                    pids.add(proc.pid)

                    Settings.write_log_dev_file(
                        "[find_chromium_pids] Match PID "
                        f"{proc.pid}: "
                        f"name={name}, "
                        f"cmdline={cmdline[:200]}",
                        "DEBUG"
                    )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):
                # ------------------------------------------------
                # Le processus peut avoir disparu ou être
                # inaccessible pendant le scan.
                # ------------------------------------------------
                continue

            except Exception as exc:
                Settings.write_log_event(
                    "chromium_pid_scan_failed",
                    "WARNING",
                    exception_type=type(exc).__name__,
                    error=str(exc),
                    profile_path=profile_path,
                    browser_name=browser_name,
                    traceback=traceback.format_exc(),
                )

                continue

        # ------------------------------------------------------
        # Convertit le set en liste triée.
        # ------------------------------------------------------
        result = sorted(pids)

        Settings.write_log_dev_file(
            f"[find_chromium_pids] Chromium PIDs found: "
            f"{result}",
            "INFO"
        )

        return result

    # ======================================================
    # createFirefoxProfile
    # ======================================================
    #
    # Crée un nouveau profil Firefox.
    #
    # Le processus est :
    #
    #     rechercher firefox.exe
    #             ↓
    #     créer le dossier de base
    #             ↓
    #     vérifier si le profil existe
    #             ↓
    #     exécuter Firefox --CreateProfile
    #             ↓
    #     attendre la création du dossier
    #             ↓
    #     fallback via profiles.ini
    # ======================================================
    @staticmethod
    def createFirefoxProfile(
        profile_name: str
    ) -> Optional[str]:

        Settings.write_log_dev_file(
            f"[create_firefox_profile] Start: {profile_name}",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Recherche de l'exécutable Firefox.
        # ------------------------------------------------------
        firefox_path = (
            BrowserManager.getBrowserExecutablePath(
                "firefox.exe"
            )
        )

        # ------------------------------------------------------
        # Firefox est obligatoire pour créer le profil.
        # ------------------------------------------------------
        if not firefox_path:

            Settings.write_log_dev_file(
                "Firefox not found",
                "ERROR"
            )

            return None

        # ------------------------------------------------------
        # Récupère le dossier racine des profils Firefox.
        # ------------------------------------------------------
        base_dir = Settings.FIREFOX_PROFILES

        try:

            # --------------------------------------------------
            # Crée le dossier si nécessaire.
            # --------------------------------------------------
            os.makedirs(
                base_dir,
                exist_ok=True
            )

        except Exception as e:
            Settings.write_log_event(
                "firefox_profile_directory_creation_failed",
                "ERROR",
                profile_name=profile_name,
                directory=base_dir,
                exception_type=type(e).__name__,
                error=str(e),
                traceback=traceback.format_exc(),
            )

            return None

        # ------------------------------------------------------
        # Construit le chemin final du profil.
        # ------------------------------------------------------
        profile_dir = os.path.join(
            base_dir,
            profile_name
        )

        # ------------------------------------------------------
        # Si le profil existe déjà, aucune création n'est nécessaire.
        # ------------------------------------------------------
        if os.path.exists(profile_dir):
            return profile_dir

        try:

            # --------------------------------------------------
            # Firefox attend le nom et le chemin du profil
            # dans cet argument.
            # --------------------------------------------------
            cmd = (
                f"{profile_name} {profile_dir}"
            )

            # --------------------------------------------------
            # Lance Firefox en mode création de profil.
            #
            # stdout et stderr sont capturés afin de pouvoir
            # analyser les erreurs sans les afficher directement.
            #
            # timeout protège l'application contre une commande
            # qui resterait bloquée indéfiniment.
            # --------------------------------------------------
            result = subprocess.run(
                [
                    firefox_path,
                    "--CreateProfile",
                    cmd
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )

            # --------------------------------------------------
            # Un returncode différent de 0 indique que Firefox
            # a signalé une erreur.
            # --------------------------------------------------
            if result.returncode != 0:

                Settings.write_log_dev_file(
                    f"Create failed: {result.stderr}",
                    "ERROR"
                )

                return None

        except Exception as e:
            Settings.write_log_event(
                "firefox_profile_creation_failed",
                "ERROR",
                profile_name=profile_name,
                profile_path=profile_dir,
                exception_type=type(e).__name__,
                error=str(e),
                traceback=traceback.format_exc(),
            )

            return None

        # ------------------------------------------------------
        # Attend que le dossier apparaisse réellement.
        #
        # 20 itérations × 0.5 seconde = environ 10 secondes.
        # ------------------------------------------------------
        for _ in range(20):

            if os.path.exists(profile_dir):
                return profile_dir

            time.sleep(0.5)

        # ------------------------------------------------------
        # Dernier mécanisme de récupération :
        #
        # relit profiles.ini pour essayer de retrouver le profil
        # même si le test direct du dossier n'a pas fonctionné.
        # ------------------------------------------------------
        profiles = (
            BrowserManager.getFirefoxProfileMap()
        )

        return profiles.get(profile_name)

    # ======================================================
    # closeFirefoxProcesses
    # ======================================================
    #
    # Ferme les processus Firefox correspondant aux entrées
    # fournies par firefox_close_list.
    #
    # La fonction accepte plusieurs formats :
    #
    #     int
    #     str
    #     "1234;5678"
    #     {"pid": 1234}
    #     {"pids": [1234, 5678]}
    #     {"firefox_pids": "1234;5678"}
    #     {"proc": process}
    #     {"profile_path": "..."}
    #
    # Cela permet de supporter différentes structures utilisées
    # par le reste de l'application.
    # ======================================================
    @staticmethod
    def closeFirefoxProcesses(
        firefox_close_list: List[Any]
    ):

        Settings.write_log_dev_file(
            "close_windows_by_profiles called with "
            f"{len(firefox_close_list)} entries",
            "INFO"
        )

        # ------------------------------------------------------
        # Liste temporaire contenant tous les PIDs détectés.
        # ------------------------------------------------------
        pid_list = []

        # ------------------------------------------------------
        # Parcourt toutes les entrées fournies.
        # ------------------------------------------------------
        for entry in firefox_close_list:

            # ==================================================
            # Cas Dictionary
            # ==================================================
            if isinstance(entry, dict):

                # ------------------------------------------------
                # Premier format accepté :
                #
                # {"firefox_pids": ...}
                # ------------------------------------------------
                if (
                    "firefox_pids" in entry
                    and entry["firefox_pids"] is not None
                ):

                    # --------------------------------------------
                    # Plusieurs PIDs sous forme de chaîne :
                    #
                    # "1234;5678"
                    # --------------------------------------------
                    if isinstance(
                        entry["firefox_pids"],
                        str
                    ):

                        pid_list.extend(
                            [
                                int(pid.strip())
                                for pid in
                                entry["firefox_pids"].split(";")
                                if pid.strip().isdigit()
                            ]
                        )

                    # --------------------------------------------
                    # Plusieurs PIDs sous forme de collection.
                    # --------------------------------------------
                    elif isinstance(
                        entry["firefox_pids"],
                        (list, tuple, set)
                    ):

                        pid_list.extend(
                            [
                                int(pid)
                                for pid in entry["firefox_pids"]
                                if str(pid).strip().isdigit()
                            ]
                        )

                # ------------------------------------------------
                # Deuxième format :
                #
                # {"pids": ...}
                # ------------------------------------------------
                elif (
                    "pids" in entry
                    and entry["pids"] is not None
                ):

                    if isinstance(
                        entry["pids"],
                        str
                    ):

                        pid_list.extend(
                            [
                                int(pid.strip())
                                for pid in entry["pids"].split(";")
                                if pid.strip().isdigit()
                            ]
                        )

                    elif isinstance(
                        entry["pids"],
                        list
                    ):

                        pid_list.extend(
                            [
                                int(pid)
                                for pid in entry["pids"]
                                if str(pid).strip().isdigit()
                            ]
                        )

                # ------------------------------------------------
                # Troisième format :
                #
                # {"pid": 1234}
                # ------------------------------------------------
                elif (
                    "pid" in entry
                    and entry["pid"] is not None
                ):

                    pid_str = str(
                        entry["pid"]
                    ).strip()

                    if pid_str.isdigit():
                        pid_list.append(
                            int(pid_str)
                        )

                # ------------------------------------------------
                # Quatrième format :
                #
                # {"proc": process_object}
                # ------------------------------------------------
                elif entry.get("proc") is not None:

                    try:

                        pid_list.append(
                            int(entry["proc"].pid)
                        )

                    except Exception as exc:
                        Settings.write_log_event(
                            "firefox_process_pid_read_failed",
                            "WARNING",
                            exception_type=type(exc).__name__,
                            error=str(exc),
                            process_type=type(entry["proc"]).__name__,
                            traceback=traceback.format_exc(),
                        )

                # ------------------------------------------------
                # Cinquième format :
                #
                # {"profile_path": "..."}
                #
                # Si aucun PID direct n'est fourni, le code essaie
                # de retrouver les PIDs Firefox à partir du profile.
                # ------------------------------------------------
                elif entry.get("profile_path"):

                    derived = (
                        BrowserManager.findFirefoxProcessIds(
                            entry["profile_path"],
                            entry.get("web_ext_pid", 0)
                        )
                    )

                    pid_list.extend(derived)

                    Settings.write_log_dev_file(
                        "Derived Firefox PIDs from profile_path "
                        f"{entry['profile_path']}: {derived}",
                        "DEBUG"
                    )

            # ==================================================
            # Cas Integer
            # ==================================================
            elif isinstance(entry, int):

                pid_list.append(entry)

            # ==================================================
            # Cas String
            # ==================================================
            elif isinstance(entry, str):

                text = entry.strip()

                # ------------------------------------------------
                # PID unique :
                #
                # "1234"
                # ------------------------------------------------
                if text.isdigit():

                    pid_list.append(
                        int(text)
                    )

                # ------------------------------------------------
                # Plusieurs PIDs :
                #
                # "1234;5678"
                # ------------------------------------------------
                elif ";" in text:

                    pid_list.extend(
                        [
                            int(pid.strip())
                            for pid in text.split(";")
                            if pid.strip().isdigit()
                        ]
                    )

        # ------------------------------------------------------
        # Supprime les doublons et trie les PIDs.
        # ------------------------------------------------------
        pid_list = sorted(
            set(pid_list)
        )

        Settings.write_log_dev_file(
            f"Resolved Firefox PID list: {pid_list}",
            "DEBUG"
        )

        # ------------------------------------------------------
        # Aucun PID trouvé.
        # ------------------------------------------------------
        if not pid_list:

            Settings.write_log_dev_file(
                "No Firefox PIDs to close",
                "WARNING"
            )

            return

        # ------------------------------------------------------
        # Traite chaque PID individuellement.
        # ------------------------------------------------------
        for pid in pid_list:

            try:

                # ------------------------------------------------
                # Vérifie si le PID existe toujours.
                # ------------------------------------------------
                if not psutil.pid_exists(pid):

                    Settings.write_log_dev_file(
                        f"Firefox PID {pid} "
                        "no longer exists",
                        "INFO"
                    )

                    continue

                # ------------------------------------------------
                # Obtient l'objet Process.
                # ------------------------------------------------
                process = psutil.Process(pid)

                Settings.write_log_dev_file(
                    f"Terminating Firefox PID={pid}",
                    "INFO"
                )

                # ------------------------------------------------
                # Première tentative :
                # fermeture normale du processus.
                # ------------------------------------------------
                process.terminate()

                try:

                    # --------------------------------------------
                    # Attend jusqu'à 5 secondes.
                    # --------------------------------------------
                    process.wait(
                        timeout=5
                    )

                    Settings.write_log_dev_file(
                        f"Firefox PID {pid} "
                        "terminated gracefully",
                        "INFO"
                    )

                except psutil.TimeoutExpired:

                    # --------------------------------------------
                    # Firefox n'a pas terminé dans le délai prévu.
                    # --------------------------------------------
                    Settings.write_log_dev_file(
                        f"Timeout terminating PID {pid}, "
                        "forcing kill",
                        "WARNING"
                    )

                    # --------------------------------------------
                    # Force l'arrêt.
                    # --------------------------------------------
                    process.kill()

                    try:

                        # ----------------------------------------
                        # Attend que le processus disparaisse.
                        # ----------------------------------------
                        process.wait(
                            timeout=3
                        )

                        Settings.write_log_dev_file(
                            f"Firefox PID {pid} "
                            "killed forcefully",
                            "INFO"
                        )

                    except psutil.NoSuchProcess:

                        # ----------------------------------------
                        # Le processus a disparu après kill.
                        # ----------------------------------------
                        Settings.write_log_dev_file(
                            f"Firefox PID {pid} "
                            "already exited after kill",
                            "INFO"
                        )

            except psutil.NoSuchProcess:

                Settings.write_log_dev_file(
                    f"Firefox PID {pid} "
                    "already terminated",
                    "INFO"
                )

            except psutil.AccessDenied:

                Settings.write_log_dev_file(
                    f"Permission denied closing "
                    f"Firefox PID {pid}",
                    "WARNING"
                )

            except Exception as exc:

                Settings.write_log_event(
                    "firefox_pid_close_failed",
                    "ERROR",
                    pid=pid,
                    exception_type=type(exc).__name__,
                    error=str(exc),
                    traceback=traceback.format_exc(),
                )

        # ------------------------------------------------------
        # Toutes les opérations sont terminées.
        # ------------------------------------------------------
        Settings.write_log_dev_file(
            "close_windows_by_profiles completed",
            "INFO"
        )

    # ======================================================
    # search_keys
    # ======================================================
    #
    # Recherche récursivement certaines clés dans une structure
    # Python provenant généralement d'un JSON.
    #
    # La fonction accepte :
    #
    #     dict
    #     list
    #     valeurs imbriquées
    #
    # Exemple :
    #
    # {
    #     "user": {
    #         "email": "test@example.com"
    #     },
    #     "settings": {
    #         "email": "another@example.com"
    #     }
    # }
    #
    # Avec :
    #
    # search_keys = ["email"]
    #
    # les deux clés "email" seront trouvées.
    # ======================================================
    @staticmethod
    def search_keys(
        data: Any,
        search_keys: List[str],
        results: List[Dict[str, Any]],
        path_trace: str = ""
    ):

        try:

            # ==================================================
            # Cas Dictionary
            # ==================================================
            if isinstance(data, dict):

                # ------------------------------------------------
                # Parcourt toutes les paires key/value.
                # ------------------------------------------------
                for k, v in data.items():

                    # --------------------------------------------
                    # Construit le chemin logique de la clé.
                    #
                    # Exemple :
                    #
                    # user/email
                    # --------------------------------------------
                    current_path = (
                        f"{path_trace}/{k}"
                        if path_trace
                        else k
                    )

                    # --------------------------------------------
                    # Vérifie si la clé actuelle fait partie
                    # des clés recherchées.
                    # --------------------------------------------
                    if k in search_keys:

                        # ----------------------------------------
                        # Ajoute le résultat.
                        # ----------------------------------------
                        results.append({
                            k: v
                        })

                        Settings.write_log_dev_file(
                            f"Found JSON key: {k} "
                            f"at {current_path} -> {v}",
                            "INFO"
                        )

                    # --------------------------------------------
                    # Continue récursivement dans la valeur.
                    #
                    # Si v est un dict ou une list, la fonction
                    # descendra automatiquement à l'intérieur.
                    # --------------------------------------------
                    BrowserManager.search_keys(
                        v,
                        search_keys,
                        results,
                        current_path
                    )

            # ==================================================
            # Cas List
            # ==================================================
            elif isinstance(data, list):

                # ------------------------------------------------
                # enumerate permet d'obtenir :
                #
                # idx  -> position
                # item -> valeur
                # ------------------------------------------------
                for idx, item in enumerate(data):

                    # --------------------------------------------
                    # Construit un chemin de type :
                    #
                    # users[0]
                    # users[1]
                    # --------------------------------------------
                    current_path = (
                        f"{path_trace}[{idx}]"
                    )

                    # --------------------------------------------
                    # Continue récursivement dans l'élément.
                    # --------------------------------------------
                    BrowserManager.search_keys(
                        item,
                        search_keys,
                        results,
                        current_path
                    )

        except Exception as exc:

            # --------------------------------------------------
            # Capture toute erreur pendant la traversée récursive.
            # --------------------------------------------------
            Settings.write_log_event(
                "json_key_search_failed",
                "ERROR",
                path_trace=path_trace,
                exception_type=type(exc).__name__,
                error=str(exc),
                traceback=traceback.format_exc(),
            )


# ==========================================================
# Instance globale de BrowserManager
# ==========================================================
#
# Cette ligne crée une instance globale du BrowserManager.
#
# Les méthodes étant statiques, elles peuvent être appelées
# sans utiliser l'état interne de cette instance.
#
# Exemple :
#
#     BrowserManager.getBrowserExecutablePath(...)
#     BrowserManager.findFirefoxProcessIds(...)
#     BrowserManager.createFirefoxProfile(...)
#
# Le nom BrowserManager représente donc désormais l'instance
# globale après cette affectation.
# ==========================================================
BrowserManager = BrowserManager()