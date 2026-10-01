#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browser_policy_manager.py
=========================

Gestionnaire centralisé et prêt pour la production des **stratégies
d'entreprise des navigateurs** (Browser Enterprise Policies) sous Windows.
Sa seule responsabilité est de forcer l'installation d'un ensemble fixe
d'extensions via les mécanismes *officiels* de stratégie :

    * Google Chrome            -> registre HKLM (ExtensionInstallForcelist)
    * Chromium / Comodo Dragon -> registre HKLM (ExtensionInstallForcelist)
    * Microsoft Edge           -> registre HKLM (ExtensionInstallForcelist)
    * Mozilla Firefox          -> distribution\\policies.json (Enterprise Policy)

Objectifs de conception
------------------------
* **Sûr**          : seule une configuration figée et validée est appliquée.
                     Aucun chemin de registre / URL / commande ne provient de
                     l'utilisateur.
* **Idempotent**   : les exécutions répétées ne créent jamais de doublons ; le
                     programme lit l'état courant et n'écrit que ce qui manque
                     ou ce qui est incorrect.
* **Isolé**        : chaque navigateur est traité indépendamment ; l'échec de
                     l'un n'interrompt jamais les autres.
* **Vérifiable**   : après chaque modification, la valeur est relue et confirmée.
* **Non destructif**: les valeurs de registre et les policies Firefox non gérées
                     par ce programme sont préservées. Une seule sauvegarde de
                     policies.json est conservée (pas une par exécution).
* **Aucune installation de navigateur** : cet outil ne télécharge ni ne modifie
                     un navigateur ; il configure uniquement les policies.

CLI
---
    python browser_policy_manager.py --apply     # applique les policies (défaut)
    python browser_policy_manager.py --check     # détecte + affiche, sans modifier
    python browser_policy_manager.py --verify    # vérifie les policies existantes
    python browser_policy_manager.py --dry-run   # montre ce que --apply ferait

Seul ``--apply`` (une écriture réelle) requiert les privilèges Administrateur.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Imports réservés à Windows. On les protège afin que le module reste
# importable ailleurs (par exemple pour l'analyse statique), tout en échouant
# clairement à l'exécution sur un système non Windows.
# ---------------------------------------------------------------------------
if os.name == "nt":
    import ctypes
    import winreg
else:  # pragma: no cover - l'outil est réservé à Windows.
    ctypes = None  # type: ignore
    winreg = None  # type: ignore


# Logger unique du module (configuré dans configure_logging()).
LOGGER = logging.getLogger("browser_policy_manager")


# ===========================================================================
# 0. DÉPENDANCES  (vérification / installation façon checkV3.py)
# ===========================================================================
# Cet outil n'utilise QUE la bibliothèque standard de Python (argparse, json,
# logging, os, re, shutil, subprocess, tempfile, ctypes, winreg...). Il n'a donc
# aucune dépendance tierce (PyPI) à installer. Le mécanisme ci-dessous reste
# néanmoins fourni — comme dans checkV3.py — pour vérifier que les modules
# requis sont bien disponibles et pour installer automatiquement toute future
# dépendance PyPI ajoutée à REQUIRED_PACKAGES.

# Chaque entrée est un triplet : (module_a_importer, package_pip, version | None).
# Laisser vide tant que l'outil ne dépend que de la bibliothèque standard.

REQUIRED_PACKAGES: Tuple[Tuple[str, str, Optional[str]], ...] = ()


def ensure_package(module_name: str, pip_package: Optional[str] = None, version: Optional[str] = None):
    """Vérifie qu'un module est importable ; sinon installe le package pip correspondant.

    Étapes (même logique que install_and_import de checkV3.py) :
      1. Tente d'importer le module : s'il est déjà présent, rien à faire.
      2. Sinon, installe le package via ``pip`` (le nom pip peut différer du
         nom du module ; une version précise peut être imposée).
      3. Réimporte le module pour confirmer que l'installation a réussi.
    """
    # Nom du package pip : celui fourni, sinon le nom du module.
    package = pip_package or module_name
    # Spécification d'installation avec version optionnelle (ex. requests==2.31.0).
    install_spec = f"{package}=={version}" if version else package
    try:
        # 1) Le module est-il déjà disponible ?
        return importlib.import_module(module_name)
    except ImportError:
        # 2) Absent -> installation via pip (jamais shell=True).
        LOGGER.info("Missing package, installing %s...", install_spec)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_spec])
        except subprocess.CalledProcessError as exc:
            # Échec d'installation : on journalise le contexte détaillé et on relève.
            LOGGER.error("Failed to install %s | exception=%s: %s | returncode=%s", install_spec, type(exc).__name__, exc, exc.returncode)
            raise
        # 3) Nouvelle tentative d'import après installation.
        return importlib.import_module(module_name)


def ensure_dependencies() -> None:
    """Vérifie/installe toutes les dépendances requises avant l'exécution.

    - Installe les éventuels packages PyPI listés dans REQUIRED_PACKAGES
      (aucun actuellement, l'outil étant 100 % bibliothèque standard).
    - Vérifie la présence des modules système Windows indispensables
      (``winreg`` et ``ctypes``) qui, eux, ne peuvent PAS être installés via
      pip : leur absence est une erreur d'environnement fatale.
    """
    # Dépendances tierces déclarées (vide tant qu'on reste en stdlib pur).
    for module_name, pip_package, version in REQUIRED_PACKAGES:
        ensure_package(module_name, pip_package, version)

    # Modules système Windows : présents par défaut, mais on le confirme.
    if os.name == "nt":
        for module_name in ("winreg", "ctypes"):
            try:
                importlib.import_module(module_name)
            except ImportError:
                LOGGER.error("Required system module not found: %s", module_name)
                raise

    LOGGER.info("Dependency check: OK")


# ===========================================================================
# 1. CONFIGURATION  (statique, validée, jamais issue de l'utilisateur)
# ===========================================================================

# Expression régulière décrivant un identifiant d'extension Chromium valide :
# exactement 32 caractères dans l'intervalle a-p (Chrome/Chromium/Edge utilisent
# cet alphabet pour les identifiants d'extension).
CHROMIUM_ID_PATTERN = re.compile(r"^[a-p]{32}$")

# Expression régulière décrivant un identifiant d'extension Firefox acceptable :
# un GUID entre accolades, un identifiant de type e-mail (nom@domaine) ou un
# identifiant pointé simple.
FIREFOX_ID_PATTERN = re.compile(r"^(\{[0-9A-Fa-f-]{36}\}|[^\s@]+@[^\s@]+|[A-Za-z0-9._-]+)$")

# Seuls ces schémas d'URL sont autorisés pour les URLs de mise à jour/installation.
ALLOWED_URL_SCHEMES = ("https://", "http://")


@dataclass(frozen=True)
class ChromiumExtension:
    """Une extension pour un navigateur de la famille Chromium (id + URL de mise à jour)."""

    extension_id: str
    update_url: str

    def forcelist_value(self) -> str:
        """Renvoie la chaîne ``id;update_url`` stockée dans le registre."""
        return f"{self.extension_id};{self.update_url}"


@dataclass(frozen=True)
class ChromiumBrowserConfig:
    """Configuration statique d'un navigateur Chromium piloté par le registre."""

    key: str  # clé interne courte, ex. "chrome"
    display_name: str  # libellé lisible utilisé dans les logs / le résumé
    registry_path: str  # sous-chemin sous HKLM (sans le préfixe de ruche)
    extensions: Tuple[ChromiumExtension, ...]
    # Exécutables recherchés sous "App Paths" pour déterminer si le navigateur existe.
    detection_executables: Tuple[str, ...]
    # Chemins absolus vérifiés en repli pour la détection d'installation.
    detection_paths: Tuple[str, ...]


@dataclass(frozen=True)
class FirefoxExtension:
    """Une entrée ExtensionSettings de Firefox (installée de force depuis une URL)."""

    extension_id: str
    install_url: str
    installation_mode: str = "force_installed"

    def as_policy_entry(self) -> Dict[str, str]:
        """Renvoie l'objet JSON stocké sous ExtensionSettings[id]."""
        return {"installation_mode": self.installation_mode, "install_url": self.install_url}


# --- Les deux extensions Chromium partagées (Chrome + Chromium/Comodo) -------
_GOOGLE_UPDATE_URL = "https://clients2.google.com/service/update2/crx"
_SHARED_CHROMIUM_EXTENSIONS = (ChromiumExtension("ndlkiebabdgljeimcdfegcmpcnbdkijg", _GOOGLE_UPDATE_URL), ChromiumExtension("hghhdgfngfdbplmeelbdhfejeinelmdg", _GOOGLE_UPDATE_URL))

# Racines "Program Files" résolues depuis l'environnement (jamais codées en dur aveuglément).
_PF = os.environ.get("ProgramFiles", r"C:\Program Files")
_PF_X86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

# --- Configurations des navigateurs de la famille Chromium ------------------
CHROMIUM_BROWSERS: Tuple[ChromiumBrowserConfig, ...] = (
    ChromiumBrowserConfig(
        key="chrome",
        display_name="Chrome",
        registry_path=r"SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist",
        extensions=_SHARED_CHROMIUM_EXTENSIONS,
        detection_executables=("chrome.exe",),
        detection_paths=(os.path.join(_PF, "Google", "Chrome", "Application", "chrome.exe"), os.path.join(_PF_X86, "Google", "Chrome", "Application", "chrome.exe")),
    ),
    ChromiumBrowserConfig(
        key="chromium",
        display_name="Chromium",
        registry_path=r"SOFTWARE\Policies\Chromium\ExtensionInstallForcelist",
        extensions=_SHARED_CHROMIUM_EXTENSIONS,
        detection_executables=("chromium.exe", "dragon.exe"),
        detection_paths=(os.path.join(_PF, "Chromium", "Application", "chrome.exe"), os.path.join(_PF, "COMODO", "Dragon", "dragon.exe"), os.path.join(_PF_X86, "COMODO", "Dragon", "dragon.exe")),
    ),
    ChromiumBrowserConfig(
        key="edge",
        display_name="Edge",
        registry_path=r"SOFTWARE\Policies\Microsoft\Edge\ExtensionInstallForcelist",
        extensions=(ChromiumExtension("jadamecphjcpbnmbdfgfehjbgphkgeid", "https://edge.microsoft.com/extensionwebstorebase/v1/crx"),),
        detection_executables=("msedge.exe",),
        detection_paths=(os.path.join(_PF_X86, "Microsoft", "Edge", "Application", "msedge.exe"), os.path.join(_PF, "Microsoft", "Edge", "Application", "msedge.exe")),
    ),
)

# --- Configuration Firefox --------------------------------------------------
FIREFOX_EXTENSIONS: Tuple[FirefoxExtension, ...] = (FirefoxExtension("gmail.automation.proxy@azedine.dev", "https://addons.mozilla.org/firefox/downloads/latest/auto-login-gmail-with-proxy/latest.xpi"))


# ===========================================================================
# 2. EXCEPTIONS & TYPES DE RÉSULTAT
# ===========================================================================


class PolicyError(Exception):
    """Classe de base de toutes les erreurs levées par ce module."""


class ConfigurationError(PolicyError):
    """Levée lorsque la configuration statique échoue à la validation."""


class PrivilegeError(PolicyError):
    """Levée lorsqu'une modification réelle est tentée sans droits admin."""


# Constantes de statut pour le résultat par navigateur.
STATUS_SUCCESS = "SUCCESS"
STATUS_SKIPPED = "SKIPPED"
STATUS_FAILED = "FAILED"


@dataclass
class PolicyResult:
    """Résultat du traitement d'un seul navigateur."""

    name: str
    status: str = STATUS_SKIPPED
    extensions_configured: int = 0
    message: str = ""


# ===========================================================================
# 3. VALIDATION
# ===========================================================================


def _validate_url(url: str) -> None:
    """Vérifie qu'une URL de mise à jour/installation utilise un schéma autorisé et ne contient pas d'espace."""
    if not isinstance(url, str) or not url:
        raise ConfigurationError("URL must be a non-empty string")
    if any(ch.isspace() for ch in url):
        raise ConfigurationError(f"URL must not contain whitespace: {url!r}")
    if not url.lower().startswith(ALLOWED_URL_SCHEMES):
        raise ConfigurationError(f"URL scheme not allowed (http/https only): {url!r}")


def _validate_chromium_extension(ext: ChromiumExtension) -> None:
    """Valide l'identifiant d'une extension Chromium et son URL de mise à jour."""
    if not isinstance(ext.extension_id, str) or not CHROMIUM_ID_PATTERN.match(ext.extension_id):
        raise ConfigurationError(f"Invalid Chromium extension id: {ext.extension_id!r}")
    _validate_url(ext.update_url)


def _validate_firefox_extension(ext: FirefoxExtension) -> None:
    """Valide l'identifiant d'une extension Firefox, son URL d'installation et son mode d'installation."""
    if not isinstance(ext.extension_id, str) or not FIREFOX_ID_PATTERN.match(ext.extension_id):
        raise ConfigurationError(f"Invalid Firefox extension id: {ext.extension_id!r}")
    _validate_url(ext.install_url)
    if ext.installation_mode not in ("force_installed", "normal_installed", "blocked", "allowed"):
        raise ConfigurationError(f"Invalid Firefox installation_mode: {ext.installation_mode!r}")


def validate_configuration() -> None:
    """Valide l'intégralité de la configuration statique avant toute action.

    Cette étape protège contre les fautes de frappe dans la configuration codée
    en dur et garantit qu'aucun id/URL malformé n'est jamais écrit sur le système.
    """
    for browser in CHROMIUM_BROWSERS:
        # Sécurité : on refuse tout chemin de registre hors de SOFTWARE\Policies.
        if not browser.registry_path.lower().startswith("software\\policies\\"):
            raise ConfigurationError(f"Refusing non-policy registry path: {browser.registry_path!r}")
        for ext in browser.extensions:
            _validate_chromium_extension(ext)
    for ext in FIREFOX_EXTENSIONS:
        _validate_firefox_extension(ext)
    LOGGER.debug("Static configuration validated successfully")


# ===========================================================================
# 4. PRIVILÈGES ADMINISTRATEUR
# ===========================================================================


def is_admin() -> bool:
    """Renvoie True si le processus courant possède les privilèges Administrateur."""
    if os.name != "nt":
        return False
    try:
        # API Windows officielle pour tester l'élévation.
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # pragma: no cover - défensif ; un échec d'API vaut "non".
        return False


def relaunch_as_admin(argv: List[str]) -> bool:
    """Tente de relancer ce programme en mode élevé via l'invite UAC.

    Renvoie True si une relance a été déclenchée (l'appelant doit alors quitter),
    False si l'élévation n'a pas pu être demandée.
    """
    if os.name != "nt":
        return False
    try:
        # Reconstruit la ligne de commande : ce script + tous les arguments
        # d'origine + le marqueur interne --relaunched. Ce marqueur empêche à la
        # fois une boucle d'élévation et indique à l'instance élevée de garder sa
        # fenêtre de console ouverte à la fin (sinon la nouvelle fenêtre se ferme
        # instantanément et l'utilisateur ne voit jamais le résultat).
        script = os.path.abspath(__file__)
        working_dir = os.path.dirname(script)
        params = " ".join(f'"{a}"' for a in [script, *argv, "--relaunched"])
        # lpDirectory = working_dir afin que le processus élevé conserve ce dossier
        # comme répertoire courant (UAC le démarrerait sinon dans System32).
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, working_dir, 1)
        # ShellExecuteW renvoie une valeur > 32 en cas de succès.
        return int(rc) > 32
    except Exception as exc:
        LOGGER.error("Failed to request UAC elevation | exception=%s: %s", type(exc).__name__, exc)
        return False


def _pause_if_relaunched(relaunched: bool) -> None:
    """Garde la fenêtre de console élevée ouverte pour que sa sortie reste visible.

    Lorsque le programme se relance lui-même avec les droits Administrateur,
    Windows ouvre une toute nouvelle fenêtre de console qui se ferme dès la fin
    du processus. Si nous avons été démarrés ainsi (``--relaunched``), on attend
    une touche pour que l'utilisateur puisse lire le résumé. Protégé afin de ne
    jamais planter en l'absence de console.
    """
    if not relaunched:
        return
    try:
        input("\nAppuyez sur Entrée pour fermer cette fenêtre...")
    except (EOFError, OSError):
        pass


# ===========================================================================
# 5. HELPERS REGISTRE  (winreg uniquement ; pas de reg.exe, pas de shell=True)
# ===========================================================================
# Toutes les clés se trouvent sous HKLM et sont ouvertes avec la vue 64 bits
# explicite afin que le comportement soit identique sur les interpréteurs
# Python 32 bits et 64 bits.


def _open_key_read(path: str):
    """Ouvre une sous-clé HKLM en lecture (vue 64 bits). Lève FileNotFoundError
    lorsque la clé n'existe pas."""
    return winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)


def _create_key_write(path: str):
    """Crée/ouvre une sous-clé HKLM en écriture (vue 64 bits)."""
    return winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)


def read_registry_values(path: str) -> Dict[str, str]:
    """Renvoie toutes les valeurs chaîne sous une clé HKLM sous forme ``{nom: valeur}``.

    Une clé absente renvoie un dictionnaire vide (et non une erreur) : la clé
    n'a simplement pas encore été créée.
    """
    values: Dict[str, str] = {}
    try:
        with _open_key_read(path) as key:
            index = 0
            while True:
                try:
                    name, data, _kind = winreg.EnumValue(key, index)
                except OSError:
                    # Plus aucune valeur sous cette clé.
                    break
                values[name] = str(data)
                index += 1
    except FileNotFoundError:
        LOGGER.debug("Registry key not present yet: HKLM\\%s", path)
    return values


def set_registry_value(path: str, name: str, value: str) -> None:
    """Crée la clé si nécessaire et écrit une unique valeur REG_SZ."""
    with _create_key_write(path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def read_single_registry_value(path: str, name: str) -> Optional[str]:
    """Renvoie une valeur REG_SZ, ou None si la clé/valeur est absente."""
    try:
        with _open_key_read(path) as key:
            data, _kind = winreg.QueryValueEx(key, name)
            return str(data)
    except FileNotFoundError:
        return None


def app_paths_executable(exe_name: str) -> Optional[str]:
    """Résout un programme via la zone de registre Windows "App Paths".

    Cherche dans les vues 64 bits ET 32 bits de
    ``SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\<exe>``.
    Renvoie le chemin de l'exécutable si la clé existe, sinon None.
    """
    sub_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path, 0, winreg.KEY_READ | view) as key:
                data, _kind = winreg.QueryValueEx(key, None)  # valeur par défaut
                if data:
                    return str(data)
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return None


# ===========================================================================
# 6. GESTIONNAIRE DE POLICY FAMILLE CHROMIUM (Chrome / Chromium / Edge)
# ===========================================================================


class ChromiumForcelistManager:
    """Applique une policy ExtensionInstallForcelist pour un navigateur Chromium.

    La clé de registre ``...\\ExtensionInstallForcelist`` contient des valeurs
    chaîne numérotées ("1", "2", ...) chacune égale à
    ``<extension_id>;<update_url>``. Ce gestionnaire garantit que chaque
    extension configurée est présente avec la bonne URL, sans toucher aux entrées
    numérotées non gérées.
    """

    def __init__(self, config: ChromiumBrowserConfig) -> None:
        self.config = config

    
    
    
    # -- détection ----------------------------------------------------------
    def is_installed(self) -> bool:
        """True si l'exécutable du navigateur est trouvé via App Paths ou sur le disque."""
        for exe in self.config.detection_executables:
            path = app_paths_executable(exe)
            if path and os.path.exists(path):
                return True
        return any(os.path.exists(p) for p in self.config.detection_paths)

    
    
    
    
    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _parse_forcelist(values: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
        """Construit ``extension_id -> (nom_de_valeur, update_url)`` depuis les entrées brutes."""
        parsed: Dict[str, Tuple[str, str]] = {}
        for name, raw in values.items():
            extension_id, _, url = raw.partition(";")
            parsed[extension_id.strip()] = (name, url.strip())
        return parsed

    
    
    def _plan(self) -> List[Tuple[str, str, str]]:
        """Calcule les changements nécessaires pour l'idempotence.

        Renvoie une liste de ``(nom_de_valeur, valeur, action)`` où ``action``
        vaut "add" (nouvelle valeur numérotée) ou "fix" (corrige une valeur
        existante). Une liste vide signifie que la policy est déjà correcte.
        """
        existing = read_registry_values(self.config.registry_path)
        by_id = self._parse_forcelist(existing)
        used_indexes = {int(n) for n in existing if n.isdigit()}
        next_index = 1

        plan: List[Tuple[str, str, str]] = []
        for ext in self.config.extensions:
            desired_value = ext.forcelist_value()
            if ext.extension_id in by_id:
                name, current_url = by_id[ext.extension_id]
                if current_url == ext.update_url:
                    continue  # déjà correct -> rien à faire
                plan.append((name, desired_value, "fix"))  # URL erronée -> correction sur place
            else:
                # Alloue le plus petit nom numérique inutilisé.
                while next_index in used_indexes:
                    next_index += 1
                used_indexes.add(next_index)
                plan.append((str(next_index), desired_value, "add"))
        return plan

    
    
    # -- opérations ---------------------------------------------------------
    def check(self) -> PolicyResult:
        """Lecture seule : indique l'installation et combien d'entrées correspondent déjà."""
        name = self.config.display_name
        if not self.is_installed():
            LOGGER.info("[SKIP] %s is not installed.", name)
            return PolicyResult(name, STATUS_SKIPPED, 0, "not installed")
        pending = self._plan()
        LOGGER.info("%s detected | configured=%d | pending changes=%d", name, len(self.config.extensions), len(pending))
        return PolicyResult(name, STATUS_SUCCESS, len(self.config.extensions), "checked")

    
    
    def apply(self, dry_run: bool) -> PolicyResult:
        """Garantit la présence de la policy. Idempotent et non destructif."""
        name = self.config.display_name
        if not self.is_installed():
            LOGGER.info("[SKIP] %s is not installed.", name)
            return PolicyResult(name, STATUS_SKIPPED, 0, "not installed")

        try:
            # Calcule d'abord ce qui doit changer (idempotence).
            plan = self._plan()
            if not plan:
                LOGGER.info("%s policy already up to date.", name)
                return PolicyResult(name, STATUS_SUCCESS, len(self.config.extensions), "already configured")

            if dry_run:
                # Mode simulation : on affiche ce qui serait écrit, sans rien modifier.
                LOGGER.info("[DRY RUN] %s: would write %d value(s):", name, len(plan))
                for value_name, value, action in plan:
                    LOGGER.info("[DRY RUN]   %s (%s) = %s", value_name, action, value)
                return PolicyResult(name, STATUS_SUCCESS, len(self.config.extensions), "dry-run")

            LOGGER.info("Writing %s policy...", name)
            for value_name, value, _action in plan:
                set_registry_value(self.config.registry_path, value_name, value)

            # Vérification systématique après écriture.
            LOGGER.info("Verifying %s policy...", name)
            verified = self.verify()
            if verified.status != STATUS_SUCCESS:
                return verified
            LOGGER.info("%s policy: OK", name)
            return PolicyResult(name, STATUS_SUCCESS, len(self.config.extensions), "configured")
        except PermissionError as exc:
            # Écriture registre refusée : il faut les droits Administrateur.
            LOGGER.error("%s: permission denied writing registry | exception=%s: %s", name, type(exc).__name__, exc)
            return PolicyResult(name, STATUS_FAILED, 0, "permission denied (run as Administrator)")
        except OSError as exc:
            LOGGER.error("%s: registry operation failed | exception=%s: %s", name, type(exc).__name__, exc)
            return PolicyResult(name, STATUS_FAILED, 0, str(exc))

    
    
    def verify(self) -> PolicyResult:
        """Relit le registre et confirme que chaque extension est correcte."""
        name = self.config.display_name
        if not self.is_installed():
            return PolicyResult(name, STATUS_SKIPPED, 0, "not installed")
        by_id = self._parse_forcelist(read_registry_values(self.config.registry_path))
        for ext in self.config.extensions:
            entry = by_id.get(ext.extension_id)
            if not entry or entry[1] != ext.update_url:
                LOGGER.error("%s verification failed for extension %s", name, ext.extension_id)
                return PolicyResult(name, STATUS_FAILED, 0, f"missing/incorrect entry for {ext.extension_id}")
        LOGGER.info("%s policy verified (%d extensions).", name, len(self.config.extensions))
        return PolicyResult(name, STATUS_SUCCESS, len(self.config.extensions), "verified")


# ===========================================================================
# 7. GESTIONNAIRE DE POLICY FIREFOX (distribution\policies.json)
# ===========================================================================


class FirefoxPolicyManager:
    """Applique les policies d'entreprise Firefox via ``distribution/policies.json``.

    Firefox ne lit PAS ici les policies du registre Windows ; le mécanisme
    supporté et multiplateforme est un fichier de policy JSON situé à côté du
    binaire Firefox. Ce gestionnaire détecte le dossier d'installation, fusionne
    nos ``ExtensionSettings`` dans tout fichier de policy existant (en préservant
    les policies non gérées) et conserve une seule sauvegarde.
    """

    display_name = "Firefox"

    def __init__(self, extensions: Tuple[FirefoxExtension, ...]) -> None:
        self.extensions = extensions
        self._install_dir: Optional[Path] = None

    # -- détection ----------------------------------------------------------
    def detect_install_dir(self) -> Optional[Path]:
        """Localise de façon fiable le dossier d'installation de Firefox.

        Ordre de découverte :
          1. Registre ``SOFTWARE\\Mozilla\\Mozilla Firefox`` version courante
             (vues 64 bits ET 32 bits).
          2. "App Paths\\firefox.exe".
          3. Emplacements classiques dans Program Files.
        """
        # Cache : on ne refait pas la détection si elle a déjà réussi.
        if self._install_dir is not None:
            return self._install_dir

        # 1) Registre : lit CurrentVersion, puis le "Install Directory" de cette version.
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Mozilla\Mozilla Firefox", 0, winreg.KEY_READ | view) as key:
                    current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Mozilla\Mozilla Firefox\{current_version}\Main", 0, winreg.KEY_READ | view) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "Install Directory")
                candidate = Path(str(install_dir))
                if (candidate / "firefox.exe").exists():
                    self._install_dir = candidate
                    return candidate
            except (FileNotFoundError, OSError):
                continue

        # 2) App Paths.
        exe = app_paths_executable("firefox.exe")
        if exe and os.path.exists(exe):
            candidate = Path(exe).parent
            if (candidate / "firefox.exe").exists():
                self._install_dir = candidate
                return candidate

        # 3) Emplacements d'installation classiques.
        for base in (os.path.join(_PF, "Mozilla Firefox"), os.path.join(_PF_X86, "Mozilla Firefox")):
            candidate = Path(base)
            if (candidate / "firefox.exe").exists():
                self._install_dir = candidate
                return candidate

        return None

    def is_installed(self) -> bool:
        """True si un dossier d'installation Firefox a pu être localisé."""
        return self.detect_install_dir() is not None

    def policies_path(self) -> Optional[Path]:
        """Renvoie ``<dossier_install>/distribution/policies.json`` (ou None)."""
        install_dir = self.detect_install_dir()
        return None if install_dir is None else install_dir / "distribution" / "policies.json"

    # -- helpers JSON -------------------------------------------------------
    @staticmethod
    def _load_existing(path: Path) -> Dict:
        """Lit et valide un policies.json existant, ou renvoie un dictionnaire neuf.

        Un fichier existant malformé est traité comme une erreur (il n'est pas
        écrasé silencieusement) ; c'est l'appelant qui décide de la suite.
        """
        if not path.exists():
            return {"policies": {}}
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)  # lève JSONDecodeError si le JSON est invalide
        if not isinstance(data, dict):
            raise PolicyError("policies.json root is not a JSON object")
        if "policies" not in data or not isinstance(data["policies"], dict):
            data["policies"] = {} if "policies" not in data else data["policies"]
            if not isinstance(data["policies"], dict):
                raise PolicyError("policies.json 'policies' is not an object")
        return data

    def _desired_extension_settings(self) -> Dict[str, Dict[str, str]]:
        """Construit le bloc ExtensionSettings géré par ce programme."""
        return {ext.extension_id: ext.as_policy_entry() for ext in self.extensions}

    def _merge(self, data: Dict) -> Tuple[Dict, bool]:
        """Fusionne nos ExtensionSettings dans ``data``.

        Renvoie ``(data_fusionné, changed)``. Les policies non gérées et les
        clés ExtensionSettings non gérées sont préservées ; seules nos propres
        clés sont définies.
        """
        policies = data.setdefault("policies", {})
        extension_settings = policies.setdefault("ExtensionSettings", {})
        if not isinstance(extension_settings, dict):
            raise PolicyError("policies.ExtensionSettings is not an object")

        changed = False
        for extension_id, entry in self._desired_extension_settings().items():
            # On ne réécrit une entrée que si elle diffère (idempotence).
            if extension_settings.get(extension_id) != entry:
                extension_settings[extension_id] = entry
                changed = True
        return data, changed

    def _backup(self, path: Path) -> Optional[Path]:
        """Crée/rafraîchit une unique ``policies.json.backup`` avant écriture.

        Une sauvegarde n'est faite que si un fichier original existe ; on garde
        exactement une sauvegarde (écrasée à chaque changement appliqué), jamais
        un historique illimité.
        """
        if not path.exists():
            return None
        backup_path = path.with_suffix(path.suffix + ".backup")
        shutil.copy2(path, backup_path)
        LOGGER.info("Backup written: %s", backup_path)
        return backup_path

    @staticmethod
    def _atomic_write(path: Path, data: Dict) -> None:
        """Écrit le JSON de façon atomique (fichier temporaire dans le même dossier + os.replace)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix="policies_", suffix=".json", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            os.replace(tmp_name, path)
        finally:
            # Nettoie le fichier temporaire s'il subsiste (échec avant os.replace).
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    # -- opérations ---------------------------------------------------------
    def check(self) -> PolicyResult:
        """Lecture seule : indique l'installation et si le fichier correspond déjà."""
        if not self.is_installed():
            LOGGER.info("[SKIP] Firefox is not installed.")
            return PolicyResult(self.display_name, STATUS_SKIPPED, 0, "not installed")
        path = self.policies_path()
        LOGGER.info("Firefox detected | policies.json target: %s", path)
        return PolicyResult(self.display_name, STATUS_SUCCESS, len(self.extensions), "checked")

    def apply(self, dry_run: bool) -> PolicyResult:
        """Fusionne nos ExtensionSettings dans policies.json. Idempotent."""
        if not self.is_installed():
            LOGGER.info("[SKIP] Firefox is not installed.")
            return PolicyResult(self.display_name, STATUS_SKIPPED, 0, "not installed")

        path = self.policies_path()
        assert path is not None  # garanti par is_installed()
        backup_path: Optional[Path] = None
        try:
            # Charge l'existant puis fusionne sur une COPIE (json round-trip)
            # pour ne pas modifier l'objet d'origine avant d'avoir décidé d'écrire.
            data = self._load_existing(path)
            merged, changed = self._merge(json.loads(json.dumps(data)))

            if not changed:
                LOGGER.info("Firefox policies.json already up to date.")
                return PolicyResult(self.display_name, STATUS_SUCCESS, len(self.extensions), "already configured")

            if dry_run:
                LOGGER.info("[DRY RUN] Firefox: would update ExtensionSettings in %s", path)
                for extension_id in self._desired_extension_settings():
                    LOGGER.info("[DRY RUN]   ExtensionSettings[%s]", extension_id)
                return PolicyResult(self.display_name, STATUS_SUCCESS, len(self.extensions), "dry-run")

            LOGGER.info("Writing Firefox policies.json...")
            # Sauvegarde puis écriture atomique.
            backup_path = self._backup(path)
            self._atomic_write(path, merged)

            LOGGER.info("Validating JSON...")
            LOGGER.info("Verifying ExtensionSettings...")
            verified = self.verify()
            if verified.status != STATUS_SUCCESS:
                raise PolicyError("post-write verification failed")
            LOGGER.info("Firefox policy: OK")
            return PolicyResult(self.display_name, STATUS_SUCCESS, len(self.extensions), "configured")

        except PermissionError as exc:
            # Écriture refusée : droits Administrateur nécessaires ; on restaure.
            LOGGER.error("Firefox: permission denied writing %s | exception=%s: %s", path, type(exc).__name__, exc)
            self._restore(backup_path, path)
            return PolicyResult(self.display_name, STATUS_FAILED, 0, "permission denied (run as Administrator)")
        except (OSError, ValueError, PolicyError) as exc:
            # ValueError couvre json.JSONDecodeError.
            LOGGER.error("Firefox: failed to update policies.json | exception=%s: %s", type(exc).__name__, exc)
            self._restore(backup_path, path)
            return PolicyResult(self.display_name, STATUS_FAILED, 0, str(exc))

    def _restore(self, backup_path: Optional[Path], path: Path) -> None:
        """Restaure au mieux le policies.json précédent après un échec."""
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, path)
                LOGGER.info("Restored previous policies.json from backup.")
            except OSError as exc:
                LOGGER.error("Failed to restore backup | exception=%s: %s", type(exc).__name__, exc)

    def verify(self) -> PolicyResult:
        """Confirme que le fichier est un JSON valide et contient nos ExtensionSettings."""
        if not self.is_installed():
            return PolicyResult(self.display_name, STATUS_SKIPPED, 0, "not installed")
        path = self.policies_path()
        assert path is not None
        try:
            if not path.exists():
                return PolicyResult(self.display_name, STATUS_FAILED, 0, "policies.json missing")
            data = self._load_existing(path)
            extension_settings = data.get("policies", {}).get("ExtensionSettings", {})
            for extension_id, entry in self._desired_extension_settings().items():
                if extension_settings.get(extension_id) != entry:
                    return PolicyResult(self.display_name, STATUS_FAILED, 0, f"missing/incorrect ExtensionSettings[{extension_id}]")
            LOGGER.info("Firefox policy verified (%d extensions).", len(self.extensions))
            return PolicyResult(self.display_name, STATUS_SUCCESS, len(self.extensions), "verified")
        except (OSError, ValueError, PolicyError) as exc:
            LOGGER.error("Firefox verification error | exception=%s: %s", type(exc).__name__, exc)
            return PolicyResult(self.display_name, STATUS_FAILED, 0, str(exc))


# ===========================================================================
# 8. ORCHESTRATION
# ===========================================================================


def build_managers() -> List[object]:
    """Instancie tous les gestionnaires de navigateur depuis la configuration statique."""
    managers: List[object] = [ChromiumForcelistManager(cfg) for cfg in CHROMIUM_BROWSERS]
    managers.append(FirefoxPolicyManager(FIREFOX_EXTENSIONS))
    return managers


def run(mode: str, dry_run: bool) -> List[PolicyResult]:
    """Exécute l'opération choisie sur chaque navigateur, en isolant les échecs.

    ``mode`` vaut "apply", "check" ou "verify". Chaque navigateur est traité dans
    son propre try/except afin qu'un échec n'interrompe jamais les autres.
    """
    results: List[PolicyResult] = []
    for manager in build_managers():
        display = getattr(manager, "display_name", None) or getattr(getattr(manager, "config", None), "display_name", "browser")
        try:
            if mode == "check":
                results.append(manager.check())  # type: ignore[attr-defined]
            elif mode == "verify":
                results.append(manager.verify())  # type: ignore[attr-defined]
            else:  # "apply"
                results.append(manager.apply(dry_run))  # type: ignore[attr-defined]
        except Exception as exc:  # isolation : un navigateur ne doit jamais tuer l'exécution
            LOGGER.error("%s: unexpected error | exception=%s: %s", display, type(exc).__name__, exc)
            results.append(PolicyResult(display, STATUS_FAILED, 0, str(exc)))
    return results


# ===========================================================================
# 9. RÉSUMÉ DES RÉSULTATS
# ===========================================================================


def print_summary(results: List[PolicyResult]) -> str:
    """Affiche le résumé final aligné et renvoie la chaîne de statut global."""
    line = "=" * 40
    print(line)
    print("Browser Policy Manager")
    print(line)
    print()
    for result in results:
        print(f"{result.name:<12} : {result.status}")
    print()
    print("Extensions configured:")
    for result in results:
        print(f"{result.name:<12} : {result.extensions_configured}")
    print()

    # Statut global : « avec erreurs » dès qu'un navigateur a échoué.
    has_failure = any(r.status == STATUS_FAILED for r in results)
    overall = "COMPLETED WITH ERRORS" if has_failure else "COMPLETED"
    print(f"Status: {overall}")
    print(line)
    return overall


# ===========================================================================
# 10. LOGGING & CLI
# ===========================================================================


def configure_logging(log_file: Optional[str]) -> None:
    """Configure un logging horodaté vers la console (et un fichier optionnel).

    Note : cet outil ne journalise jamais de mots de passe, jetons, cookies ou
    identifiants ; il ne manipule que des ids d'extension fixes et des URLs de
    mise à jour publiques.
    """
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=handlers)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Analyse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Configure browser enterprise extension policies (Windows).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Apply the policies (default action).")
    group.add_argument("--check", action="store_true", help="Detect browsers and show state without modifying.")
    group.add_argument("--verify", action="store_true", help="Verify that the expected policies are present.")
    parser.add_argument("--dry-run", action="store_true", help="With apply: show planned changes without modifying.")
    parser.add_argument("--log-file", default=None, help="Optional path to also write logs to a file.")
    parser.add_argument("--no-elevate", action="store_true", help="Do not attempt UAC self-elevation (run in the current console).")
    # Marqueur interne posé par relaunch_as_admin() : indique à cette instance
    # qu'elle a été lancée par UAC (donc : ne jamais ré-élever, et garder la
    # fenêtre ouverte à la fin).
    parser.add_argument("--relaunched", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Point d'entrée du programme. Renvoie un code de sortie (0 == succès)."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw_argv)
    configure_logging(args.log_file)

    LOGGER.info("Starting Browser Policy Manager")

    if os.name != "nt":
        LOGGER.error("This tool is only supported on Windows.")
        return 2

    # Vérifie/installe les dépendances requises (aucune dépendance tierce ici,
    # mais on confirme la disponibilité des modules système Windows).
    try:
        ensure_dependencies()
    except Exception as exc:
        LOGGER.error("Dependency check failed | exception=%s: %s", type(exc).__name__, exc)
        return 2

    # Détermine le mode : check / verify / apply (apply par défaut).
    if args.check:
        mode = "check"
    elif args.verify:
        mode = "verify"
    else:
        mode = "apply"

    # Valide la configuration statique en amont ; abandon en cas d'erreur de config.
    try:
        validate_configuration()
    except ConfigurationError as exc:
        LOGGER.error("Configuration invalid, aborting | %s", exc)
        return 2

    # Les privilèges Administrateur ne sont requis que pour un apply réel.
    # Une instance déjà lancée par UAC (--relaunched) ne doit jamais ré-élever.
    modifies_system = mode == "apply" and not args.dry_run
    if modifies_system:
        LOGGER.info("Checking administrator privileges...")
        if not is_admin():
            can_elevate = not args.no_elevate and not args.relaunched
            if can_elevate and relaunch_as_admin([a for a in raw_argv if a not in ("--no-elevate", "--relaunched")]):
                LOGGER.info("Re-launching with Administrator privileges (UAC)...")
                LOGGER.info("A new elevated window will open and complete the operation.")
                return 0
            LOGGER.error("Administrator privileges are required.")
            LOGGER.error("Please run this application as Administrator.")
            _pause_if_relaunched(args.relaunched)
            return 3
        LOGGER.info("Administrator privileges: OK")
    else:
        LOGGER.info("Read-only mode (%s%s): administrator privileges not required.", mode, ", dry-run" if args.dry_run else "")

    if args.dry_run and mode == "apply":
        LOGGER.info("[DRY RUN] No modification will be made.")

    # Exécute l'opération sur tous les navigateurs puis affiche le résumé.
    results = run(mode, dry_run=args.dry_run)
    overall = print_summary(results)
    LOGGER.info("Completed: %s", overall)

    # Garde la fenêtre élevée ouverte pour que l'utilisateur lise le résultat
    # avant sa fermeture (uniquement si cette instance a été auto-élevée via UAC).
    _pause_if_relaunched(args.relaunched)

    # Code de sortie : 0 si rien n'a échoué, 1 sinon.
    return 0 if all(r.status != STATUS_FAILED for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
