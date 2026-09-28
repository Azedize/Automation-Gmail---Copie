# utils/validation_utils.py

import os
import re
import random
import string
import traceback
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime

from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QTimer

import sys


# =========================================================
# IMPORT DE LA CONFIGURATION CENTRALE
# =========================================================

try:
    # Importe la classe Settings qui contient les configurations
    # centralisées de validation, les ports autorisés et le système de logs.
    from config import Settings

except ImportError as e:
    # Affiche l'erreur d'importation avant d'arrêter l'application.
    # Les messages utilisateur restent en anglais.
    print(f"Import error in file {__file__}: {e}")

    # Settings est indispensable au fonctionnement de ce module.
    sys.exit(1)


# =========================================================
# CONFIGURATION DU ROOT DU PROJET
# =========================================================

# Récupère le chemin absolu du dossier contenant le projet.
#
# __file__
#   -> fichier actuel
#
# dirname(__file__)
#   -> dossier utils
#
# dirname(dirname(__file__))
#   -> dossier racine du projet
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Ajoute le dossier racine dans sys.path uniquement
# s'il n'est pas déjà présent.
#
# Cela permet aux imports internes du projet
# de fonctionner correctement.
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# =========================================================
# CLASS CENTRALE DE VALIDATION
# =========================================================


class ValidationUtils:

    # =====================================================
    # REGEX CENTRALISÉS
    # =====================================================

    # Compile une seule fois le pattern email provenant de Settings.
    #
    # L'objectif est d'éviter de redéfinir le même Regex
    # dans plusieurs fichiers.
    _PATTERN_EMAIL = re.compile(Settings.VALIDATION_CONFIG["EMAIL"])

    # Pattern permettant de valider les valeurs numériques
    # simples ou sous forme de plage.
    #
    # Exemples possibles :
    #   50
    #   50,100
    _PATTERN_NUMERIC_RANGE = re.compile(Settings.VALIDATION_CONFIG["NUMERIC_RANGE"])

    # Pattern centralisé permettant de valider une adresse IPv4.
    _PATTERN_IP = re.compile(Settings.VALIDATION_CONFIG["IP_ADDRESS"])

    # =====================================================
    # ALIAS DES NOMS DE COLONNES
    # =====================================================

    # Ce dictionnaire permet de normaliser différents noms
    # de colonnes vers un nom interne unique.
    #
    # Exemple :
    #   Email          -> email
    #   password_email -> passwordEmail
    #   ip_address     -> ipAddress
    #
    # Cela permet d'accepter plusieurs formats d'entrée
    # sans dupliquer la logique de traitement.
    _INPUT_HEADER_ALIASES = {
        "Email": "email",
        "email": "email",
        "passwordEmail": "passwordEmail",
        "password_email": "passwordEmail",
        "ipAddress": "ipAddress",
        "ip_address": "ipAddress",
        "port": "port",
        "login": "login",
        "password": "password",
        "recoveryEmail": "recoveryEmail",
        "recovery_email": "recoveryEmail",
        "newrecoveryEmail": "new_recovery_email",
        "New_recovery_email": "new_recovery_email",
        "new_recovery_email": "new_recovery_email",
    }

    # =====================================================
    # VALIDATION EMAIL
    # =====================================================

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Vérifie si une adresse email respecte le pattern configuré.

        Retour :
            True  -> email valide
            False -> email invalide
        """

        # Vérifie que la valeur existe et qu'elle est bien une chaîne.
        if not email or not isinstance(email, str):
            return False

        # Applique le Regex centralisé.
        return ValidationUtils._PATTERN_EMAIL.match(email) is not None

    # =====================================================
    # VALIDATION IP
    # =====================================================

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """
        Vérifie si une adresse IP respecte le pattern IPv4 configuré.
        """

        # Refuse les valeurs vides ou les types incorrects.
        if not ip or not isinstance(ip, str):
            return False

        # Vérifie l'adresse avec le Regex centralisé.
        return ValidationUtils._PATTERN_IP.match(ip) is not None

    # =====================================================
    # VALIDATION D'UNE PLAGE NUMÉRIQUE
    # =====================================================

    @staticmethod
    def validate_numeric_range(text: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Valide une valeur numérique ou une plage numérique.

        Exemples :
            "50"       -> (True, (50, 50))
            "10,50"    -> (True, (10, 50))
            "50,10"    -> (True, (10, 50))
            "abc"      -> (False, None)
        """

        # Vérifie que le texte existe et qu'il est bien une chaîne.
        if not text or not isinstance(text, str):
            return False, None

        # Supprime les espaces inutiles autour de la valeur.
        text = text.strip()

        # Vérifie le format avec le Regex centralisé.
        match = ValidationUtils._PATTERN_NUMERIC_RANGE.match(text)

        # Aucun match = format invalide.
        if not match:
            return False, None

        # Récupère la première valeur numérique.
        min_val = int(match.group(1))

        # Si une deuxième valeur existe, elle devient le maximum.
        # Sinon, la valeur unique est utilisée pour les deux limites.
        max_val = int(match.group(2)) if match.group(2) else min_val

        # Si le minimum est supérieur au maximum,
        # les deux valeurs sont inversées.
        if min_val > max_val:
            min_val, max_val = max_val, min_val

        # Retourne le résultat et la plage normalisée.
        return True, (min_val, max_val)

    # =====================================================
    # TRAITEMENT PRINCIPAL DES DONNÉES UTILISATEUR
    # =====================================================

    @staticmethod
    def process_user_input(input_data: str, entered_number_text: str) -> Dict[str, Any]:
        """
        Parse et valide les données saisies par l'utilisateur.

        Étapes principales :
            1. Validation des entrées de base.
            2. Lecture du header.
            3. Normalisation des noms de colonnes.
            4. Vérification des colonnes obligatoires.
            5. Conversion des lignes en dictionnaires.
            6. Vérification du nombre de lignes demandé.
            7. Retour d'une structure standardisée.
        """

        # Journalise le début de la validation.
        Settings.write_log_event("user_input_validation_started", "INFO")

        # Structure de résultat standard utilisée
        # par les différentes branches de validation.
        result: Dict[str, Any] = {
            "success": False,
            "data_list": None,
            "entered_number": None,
            "error_title": "",
            "error_message": "",
            "error_type": "critical",
        }

        # =================================================
        # 1. VALIDATION DE BASE
        # =================================================

        # Vérifie que les données utilisateur existent.
        if not input_data or not input_data.strip():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": (
                        "No input data was detected. "
                        "Please provide the required data to proceed."
                    ),
                }
            )
            return result

        # Vérifie que le nombre de lignes demandé existe.
        if not entered_number_text or not entered_number_text.strip():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": (
                        "The number of rows to process is missing. "
                        "Please specify a valid number."
                    ),
                }
            )
            return result

        # Vérifie que la valeur contient uniquement des chiffres.
        if not entered_number_text.isdigit():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": (
                        "The entered number is invalid. "
                        "Please provide a positive integer value."
                    ),
                }
            )
            return result

        # Convertit le nombre de lignes de String vers Integer.
        entered_number = int(entered_number_text)

        # Journalise uniquement le nombre demandé,
        # sans enregistrer les données sensibles.
        Settings.write_log_event(
            "user_input_row_limit_validated", "INFO", requested_rows=entered_number
        )

        # =================================================
        # 2. PARSING DES LIGNES
        # =================================================

        try:

            # Sépare le contenu ligne par ligne.
            #
            # strip() supprime les espaces inutiles.
            # Les lignes vides sont ignorées.
            lines = [line.strip() for line in input_data.split("\n") if line.strip()]

            # Il faut au minimum :
            #   ligne 1 -> header
            #   ligne 2 -> données
            if len(lines) < 2:
                result.update(
                    {
                        "error_title": "Data Structure Error",
                        "error_message": (
                            "The input data contains a header "
                            "but no data rows were found."
                        ),
                    }
                )
                return result

            # Récupère le header et sépare ses colonnes avec ";".
            raw_header = [k.strip() for k in lines[0].split(";")]

            # Normalise chaque nom de colonne avec le dictionnaire
            # _INPUT_HEADER_ALIASES.
            header = [
                ValidationUtils._INPUT_HEADER_ALIASES.get(column, column)
                for column in raw_header
            ]

            # Toutes les lignes après le header sont les données.
            data_lines = lines[1:]

            # Journalise uniquement la structure générale.
            Settings.write_log_event(
                "user_input_parsing_started",
                "INFO",
                column_count=len(header),
                row_count=len(data_lines),
            )

            # =================================================
            # VÉRIFICATION DES COLONNES DUPLIQUÉES
            # =================================================

            # Si la longueur du Set est différente de la longueur
            # originale, cela signifie qu'une colonne est dupliquée.
            if len(set(header)) != len(header):

                # Construit la liste des colonnes présentes plusieurs fois.
                duplicate_columns = sorted(
                    {column for column in header if header.count(column) > 1}
                )

                result.update(
                    {
                        "error_title": "Column Validation Failed",
                        "error_message": (
                            "Duplicate columns were detected after "
                            "normalization: "
                            f"{', '.join(duplicate_columns)}. "
                            "Please keep only one column per field."
                        ),
                    }
                )
                return result

            # =================================================
            # 3. VALIDATION DES COLONNES OBLIGATOIRES
            # =================================================

            # Format obligatoire attendu.
            mandatory_patterns = [["email", "passwordEmail", "ipAddress", "port"]]

            # Colonnes optionnelles supportées.
            optional_patterns = [
                ["login", "password", "recoveryEmail", "new_recovery_email"]
            ]

            # Construit l'ensemble de toutes les colonnes acceptées.
            all_valid_keys = set(
                k for pat in (mandatory_patterns + optional_patterns) for k in pat
            )

            # Vérifie qu'au moins un format obligatoire
            # est entièrement présent dans le header.
            if not any(set(pat).issubset(header) for pat in mandatory_patterns):

                Settings.write_log_event(
                    "user_input_header_invalid",
                    "ERROR",
                    reason="mandatory_columns_missing",
                    column_count=len(header),
                )

                result.update(
                    {
                        "error_title": "Column Validation Failed",
                        "error_message": (
                            "Mandatory columns are missing from "
                            "the input data. Please ensure the header "
                            "contains all required fields."
                        ),
                    }
                )
                return result

            # Recherche les colonnes non reconnues.
            invalid_keys = [k for k in header if k not in all_valid_keys]

            # Si des colonnes inconnues existent, la validation échoue.
            if invalid_keys:

                Settings.write_log_event(
                    "user_input_header_invalid",
                    "ERROR",
                    reason="unsupported_columns",
                    invalid_column_count=len(invalid_keys),
                )

                result.update(
                    {
                        "error_title": "Column Validation Failed",
                        "error_message": (
                            "The following columns are not recognized: "
                            f"{', '.join(invalid_keys)}. "
                            "Please verify the header format."
                        ),
                    }
                )
                return result

            # =================================================
            # 4. CONVERSION DES LIGNES EN DICTIONNAIRES
            # =================================================

            # Liste finale contenant les lignes converties.
            data_list: List[Dict[str, str]] = []

            # Parcourt chaque ligne de données.
            # start=1 permet d'afficher un numéro de ligne utilisateur.
            for index, line in enumerate(data_lines, start=1):

                # Sépare les valeurs de la ligne.
                values = [v.strip() for v in line.split(";")]

                # Le nombre de valeurs doit correspondre
                # au nombre de colonnes du header.
                if len(values) != len(header):

                    Settings.write_log_event(
                        "user_input_row_invalid",
                        "ERROR",
                        row_number=index,
                        expected_column_count=len(header),
                        actual_column_count=len(values),
                    )

                    result.update(
                        {
                            "error_title": "Data Format Error",
                            "error_message": (
                                f"Row {index} does not match the "
                                "expected column count. Please ensure "
                                "all rows have the correct number "
                                "of columns."
                            ),
                        }
                    )
                    return result

                # Associe chaque colonne à sa valeur.
                #
                # Exemple :
                # header = ["email", "port"]
                # values = ["test@example.com", "8080"]
                #
                # devient :
                # {
                #     "email": "test@example.com",
                #     "port": "8080"
                # }
                data_list.append(dict(zip(header, values)))

            # =================================================
            # 5. VALIDATION DU NOMBRE DE LIGNES
            # =================================================

            # Empêche l'utilisateur de demander plus de lignes
            # que celles réellement disponibles.
            if entered_number > len(data_list):

                result.update(
                    {
                        "error_title": "Range Validation Failed",
                        "error_message": (
                            f"The specified number ({entered_number}) "
                            f"exceeds the available data rows "
                            f"({len(data_list)})."
                        ),
                    }
                )
                return result

            # =================================================
            # 6. VALIDATION RÉUSSIE
            # =================================================

            result.update(
                {
                    "success": True,
                    "data_list": data_list,
                    "entered_number": entered_number,
                    "error_title": "Validation Successful",
                    "error_message": (
                        "Input data has been successfully validated "
                        "and is ready for processing."
                    ),
                    "error_type": "success",
                }
            )

        except Exception as e:

            # Enregistre les détails techniques de l'exception.
            # Attention : le traceback ne doit pas contenir de données
            # sensibles dans un environnement de production.
            Settings.write_log_dev_file(
                f"Unexpected error during data processing: "
                f"{traceback.format_exc()}",
                "ERROR",
            )

            # Message générique destiné à l'utilisateur.
            result.update(
                {
                    "error_title": "Processing Error",
                    "error_message": (
                        "An unexpected error occurred during data "
                        "processing. Please verify your input and "
                        "try again. If the issue persists, "
                        "contact technical support."
                    ),
                }
            )

        # Journalise la fin de la validation.
        Settings.write_log_event(
            "user_input_validation_completed",
            "INFO",
            success=bool(result.get("success")),
            row_count=len(result.get("data_list") or []),
        )

        return result

    # =========================================================
    # GÉNÉRATION DES DONNÉES À PARTIR DE LA FENÊTRE UI
    # =========================================================

    @staticmethod
    def generateUserInputData(window) -> Dict[str, Any]:
        """
        Récupère les données depuis l'interface,
        les valide, récupère la configuration Proxy
        depuis l'API et construit les données finales.
        """

        try:

            # Récupère le contenu du premier champ texte.
            input_data = window.textEdit_3.toPlainText().strip()

            # Récupère le nombre de lignes demandé.
            entered_number_text = window.textEdit_4.toPlainText().strip()

            # Journalise uniquement des informations statistiques.
            Settings.write_log_event(
                "user_input_received",
                "INFO",
                input_length=len(input_data),
                input_line_count=len(input_data.splitlines()),
                has_requested_row_count=bool(entered_number_text),
            )

            # Effectue la première étape de validation.
            validation = ValidationUtils.process_user_input(
                input_data, entered_number_text
            )

            # Arrête le workflow si la validation échoue.
            if not validation["success"]:

                Settings.write_log_dev_file(
                    f"Validation failed: " f"{validation['error_message']}", "ERROR"
                )

                return {
                    "valid": False,
                    "data": None,
                    "entered_number": None,
                    "error": (
                        f"{validation['error_title']}:" f"{validation['error_message']}"
                    ),
                }

            # Récupère les données validées.
            data_list = validation["data_list"]
            entered_number = validation["entered_number"]

            Settings.write_log_event(
                "user_input_validated",
                "INFO",
                row_count=len(data_list),
                requested_rows=entered_number,
            )

            # =================================================
            # VALIDATION DES PORTS ET DES IP
            # =================================================

            ports_result = ValidationUtils.processPorts(data_list)

            # Si la validation des ports échoue, on arrête.
            if not ports_result["valid"]:

                Settings.write_log_dev_file(
                    "Ports processing failed: " f"{ports_result['error_message']}",
                    "ERROR",
                )

                Settings.write_log_event(
                    "port_processing_failed",
                    "ERROR",
                    error_type=type(ports_result.get("error")).__name__,
                )

                return {
                    "valid": False,
                    "data": ports_result.get("data"),
                    "entered_number": entered_number,
                    "error": (
                        f"{ports_result['error_title']}:"
                        f"{ports_result['error_message']}"
                    ),
                }

            # Récupère uniquement les comptes filtrés.
            filtered_accounts = ports_result["data"]["filtered"]

            Settings.write_log_dev_file(
                "Ports processed - filtered count: " f"{len(filtered_accounts)}", "INFO"
            )

            # =================================================
            # EXTRACTION DES IP UNIQUES
            # =================================================

            ip_result = ValidationUtils.collect_unique_proxy_addresses(
                filtered_accounts
            )

            # Arrête le traitement si l'extraction échoue.
            if not ip_result["valid"]:

                Settings.write_log_dev_file(
                    f"IP extraction failed: " f"{ip_result['error']}", "ERROR"
                )

                return {
                    "valid": False,
                    "data": None,
                    "entered_number": entered_number,
                    "error": (
                        f"{ip_result['error_title']}:" f"{ip_result['error_message']}"
                    ),
                }

            # Récupère le Set des IP uniques.
            unique_ips = ip_result["data"]

            Settings.write_log_dev_file(
                f"Unique IPs extracted: {len(unique_ips)}", "INFO"
            )

            # Ne journalise volontairement pas les valeurs IP.
            Settings.write_log_dev_file(
                "Unique IP values intentionally omitted from logs", "DEBUG"
            )

            # =================================================
            # IMPORTS DIFFÉRÉS
            # =================================================

            # Imports locaux effectués ici pour éviter
            # les imports circulaires ou le chargement inutile.
            from core import SessionManager
            from api import API_MANAGER

            # =================================================
            # VALIDATION DE SESSION
            # =================================================

            session_info = SessionManager.check_session()

            # Si la session est invalide, l'utilisateur doit
            # se reconnecter.
            if not session_info["valid"]:

                Settings.write_log_dev_file(
                    "Invalid session: " f"{session_info.get('error', 'Unknown error')}",
                    "ERROR",
                )

                Settings.write_log_event(
                    "session_validation_failed",
                    "ERROR",
                    error_code=session_info.get("error", "unknown"),
                )

                return {
                    "valid": False,
                    "data": None,
                    "entered_number": entered_number,
                    "error": ("Your session is invalid. " "Please log in again."),
                }

            # Récupère l'entité de la session.
            entity_used = session_info.get("p_entity_Nouveau", "UNKNOWN")

            Settings.write_log_dev_file("Session validated successfully", "INFO")

            Settings.write_log_event(
                "session_validation_succeeded",
                "INFO",
                has_entity=bool(entity_used and entity_used != "UNKNOWN"),
            )

            # =================================================
            # APPEL API
            # =================================================

            # Récupère les configurations Proxy associées
            # aux IP et à l'entité de la session.
            api_result = API_MANAGER.fetchProxyConfiguration(unique_ips, entity_used)

            # Vérifie le résultat de l'API.
            if not api_result["valid"]:

                api_error = api_result.get("error", "Unknown API error")

                Settings.write_log_dev_file(f"API call failed: {api_error}", "ERROR")

                Settings.write_log_event(
                    "proxy_configuration_failed",
                    "ERROR",
                    error_type=type(api_result.get("error")).__name__,
                )

                return {
                    "valid": False,
                    "data": None,
                    "entered_number": entered_number,
                    "error": api_error,
                }

            Settings.write_log_dev_file(
                "API call succeeded - returned entries: "
                f"{len(api_result['data']) if api_result.get('data') else 0}",
                "INFO",
            )

            # =================================================
            # MERGE DES DONNÉES
            # =================================================

            # Combine les données saisies par l'utilisateur
            # avec les informations retournées par l'API.
            merge_result = ValidationUtils.mergeValidatedData(
                api_result["data"], data_list
            )

            # Vérifie le résultat du merge.
            if not merge_result["valid"]:

                merge_error = merge_result["error"]

                Settings.write_log_event(
                    "validated_data_merge_failed",
                    "ERROR",
                    error=merge_error,
                )

                return {
                    "valid": False,
                    "data": None,
                    "entered_number": entered_number,
                    "error": merge_error,
                }

            # Récupère les données finales.
            final_data = merge_result["data"]

            Settings.write_log_dev_file(
                "Merge succeeded - final records: " f"{len(final_data)}", "INFO"
            )

            # Les données finales sensibles ne sont volontairement
            # pas écrites dans les logs.
            Settings.write_log_dev_file(
                "Final data sample intentionally omitted from logs",
                "DEBUG",
            )

            Settings.write_log_dev_file(
                "========== REQUEST COMPLETED SUCCESSFULLY ==========", "INFO"
            )

            # Retourne le résultat final.
            return {
                "valid": True,
                "data": final_data,
                "entered_number": entered_number,
                "error": None,
            }

        except Exception as e:

            # Journalise l'erreur technique complète.
            Settings.write_log_dev_file(
                "Unexpected error in generateUserInputData: "
                f"{str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )

            Settings.write_log_dev_file(
                "========== REQUEST FAILED WITH EXCEPTION ==========", "ERROR"
            )

            # Retourne un message générique à l'utilisateur.
            return {
                "valid": False,
                "data": None,
                "entered_number": None,
                "error": ("An unexpected error occurred. " "Please try again later."),
            }

    # =========================================================
    # ACCÈS SÉCURISÉ À UNE VALEUR DE DICTIONNAIRE
    # =========================================================

    @staticmethod
    def getValueSafely(item: dict, key: str, default=None):
        """
        Récupère une valeur d'un dictionnaire sans provoquer
        d'exception si l'objet n'est pas un dictionnaire.
        """

        # Si item est un dictionnaire, utilise get().
        #
        # Sinon, retourne directement la valeur par défaut.
        return item.get(key, default) if isinstance(item, dict) else default

    # =========================================================
    # NORMALISATION D'UNE ADRESSE IP
    # =========================================================

    @staticmethod
    def normalizeIpAddress(raw_ip: str) -> Dict[str, Any]:
        """
        Normalise une adresse Proxy vers le format :
            IP#PORT

        Exemple :
            192.168.1.10:8080
            ->
            192.168.1.10#8080
        """

        try:

            # Vérifie que l'adresse existe.
            if not raw_ip:

                Settings.write_log_dev_file("Empty IP provided", "ERROR")

                return {"valid": False, "data": None, "error": "Empty IP"}

            # Sépare les différentes parties avec ";".
            parts = raw_ip.split(";")

            # Si au moins trois parties existent,
            # la troisième partie est considérée comme l'adresse Proxy.
            if len(parts) >= 3:

                Settings.write_log_event("proxy_address_with_port_detected", "INFO")

                # Remplace ":" par "#".
                formatted = parts[2].replace(":", "#")

            else:

                Settings.write_log_event("proxy_address_without_port_detected", "INFO")

                # Conserve l'adresse telle quelle.
                formatted = raw_ip

            # Vérifie si un port est présent.
            if "#" in formatted:

                # Sépare IP et port.
                ip_parts = formatted.split("#")

                # Le format doit être exactement IP#PORT.
                if len(ip_parts) != 2:

                    Settings.write_log_event(
                        "proxy_address_invalid", "ERROR", reason="malformed_format"
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Malformed IP address format",
                    }

                ip, port = ip_parts

                # Vérifie que le port contient uniquement des chiffres.
                if not port.isdigit():

                    Settings.write_log_event(
                        "proxy_address_invalid", "ERROR", reason="invalid_port"
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Invalid port format",
                    }

            # Journalise uniquement l'événement,
            # sans écrire la valeur IP.
            Settings.write_log_event("proxy_address_normalized", "INFO")

            return {"valid": True, "data": formatted, "error": None}

        except Exception as e:

            # Enregistre le traceback technique.
            Settings.write_log_dev_file(
                "Unexpected error during IP formatting: " f"{traceback.format_exc()}",
                "ERROR",
            )

            Settings.write_log_dev_file(f"Error formatting IP: {e}", "ERROR")

            return {"valid": False, "data": None, "error": str(e)}

    # =========================================================
    # TRAITEMENT DES PORTS ET DES IP
    # =========================================================

    @staticmethod
    def processPorts(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valide les données IP/Port de chaque compte.

        Vérifications :
            - Structure du compte.
            - Présence du port.
            - Présence de l'IP.
            - Format de l'IP.
            - Port autorisé.
        """

        try:

            # Aucun compte à traiter.
            if not data_list:

                Settings.write_log_dev_file(
                    "No data provided for port processing", "WARNING"
                )

                return {
                    "valid": True,
                    "data": {"filtered": [], "invalid": [], "suspicious": []},
                    "error": None,
                    "error_title": "No Data",
                    "error_message": (
                        "No account data was provided " "for port processing."
                    ),
                }

            # Comptes dont la configuration est valide.
            valid_accounts = []

            # Comptes contenant un port non autorisé.
            invalid_accounts = []

            # Comptes classés comme suspicious selon
            # la logique actuelle du projet.
            suspicious_accounts = []

            # Parcourt tous les comptes.
            for index, item in enumerate(data_list):

                # Chaque entrée doit être un dictionnaire.
                if not isinstance(item, dict):

                    Settings.write_log_dev_file(
                        f"Data integrity error at index {index}: "
                        "item is not a dictionary",
                        "ERROR",
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Data integrity error",
                        "error_title": "Data Integrity Error",
                        "error_message": (
                            f"Item {index + 1} is not a valid " "data structure."
                        ),
                    }

                # Récupère le port de manière sécurisée.
                port = str(ValidationUtils.getValueSafely(item, "port", "")).strip()

                # Vérifie que le port existe.
                if not port:

                    Settings.write_log_dev_file(
                        f"Missing port at index {index}", "ERROR"
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing port",
                        "error_title": "Port Validation Failed",
                        "error_message": (
                            f"Port information is missing for " f"item {index + 1}."
                        ),
                    }

                # Récupère l'adresse IP.
                ip = str(ValidationUtils.getValueSafely(item, "ipAddress", "")).strip()

                # Vérifie que l'IP existe.
                if not ip:

                    Settings.write_log_dev_file(
                        f"Missing IP address at index {index}", "ERROR"
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing IP",
                        "error_title": "IP Validation Failed",
                        "error_message": (
                            f"IP address is missing for " f"item {index + 1}."
                        ),
                    }

                # Vérifie le format IPv4.
                if not ValidationUtils.validate_ip(ip):

                    # Ne met pas l'IP dans les logs
                    # afin d'éviter d'exposer une donnée réseau.
                    Settings.write_log_dev_file(
                        f"Invalid IP address format at index {index}", "ERROR"
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": "Invalid IP format",
                        "error_title": "IP Validation Failed",
                        "error_message": (
                            f"The IP address for item {index + 1} "
                            "is not in a valid IPv4 format."
                        ),
                    }

                # Vérifie que le port fait partie des ports
                # autorisés dans la configuration.
                if port not in Settings.PROXY_VALIDATION_PORTS:

                    # Ajoute le compte aux comptes invalides.
                    invalid_accounts.append(item)

                    # Passe directement au compte suivant.
                    continue

                # Le compte est considéré comme valide.
                valid_accounts.append(item)

                # =================================================
                # LOGIQUE ACTUELLE DU PROJET
                # =================================================
                #
                # Si le port est autorisé, le compte est également
                # ajouté à suspicious_accounts.
                #
                # Cette logique est conservée volontairement.
                if port in Settings.PROXY_VALIDATION_PORTS:
                    suspicious_accounts.append(item)

            # =================================================
            # COMPTES AVEC PORTS INVALIDES
            # =================================================

            if invalid_accounts:

                msg = (
                    f"Port validation failed for "
                    f"{len(invalid_accounts)} account(s). "
                    "Only authorized ports are allowed "
                    "for this operation. "
                    "Please review the port values."
                )

                Settings.write_log_dev_file(
                    "Validation failed: " f"{len(invalid_accounts)} invalid accounts",
                    "ERROR",
                )

                return {
                    "valid": False,
                    "data": {
                        "filtered": valid_accounts,
                        "invalid": invalid_accounts,
                        "suspicious": suspicious_accounts,
                    },
                    "error": msg,
                    "error_title": "Invalid Port Configuration",
                    "error_message": msg,
                }

            # Journalise uniquement le nombre,
            # sans exposer les comptes.
            Settings.write_log_dev_file(
                "Suspicious ports count: " f"{len(suspicious_accounts)}", "INFO"
            )

            # Retourne les résultats de validation.
            return {
                "valid": True,
                "data": {
                    "filtered": valid_accounts,
                    "invalid": [],
                    "suspicious": suspicious_accounts,
                },
                "error": None,
                "error_title": "Port Processing Successful",
                "error_message": (
                    "All ports and IP addresses were " "validated successfully."
                ),
            }

        except Exception as e:

            # Enregistre l'erreur technique.
            Settings.write_log_dev_file(
                "Unexpected error during data processing: "
                f"{e}\n{traceback.format_exc()}",
                "ERROR",
            )

            return {
                "valid": False,
                "data": None,
                "error": "Unexpected processing error",
                "error_title": "Processing Error",
                "error_message": (
                    "An unexpected system error occurred "
                    "during port processing. "
                    "Please contact technical support."
                ),
            }

    # =========================================================
    # MERGE DES DONNÉES UTILISATEUR + API
    # =========================================================

    @staticmethod
    def mergeValidatedData(api_data: dict, data_list: list) -> Dict[str, Any]:
        """
        Fusionne les données utilisateur avec les informations
        retournées par l'API.
        """

        try:

            # Liste contenant les données finales.
            final_list = []

            # Construit une map IP -> configuration API.
            #
            # Si la clé est :
            #     192.168.1.10#8080
            #
            # la clé interne devient :
            #     192.168.1.10
            api_map = {k.split("#")[0]: v for k, v in api_data.items()}

            # Parcourt toutes les données utilisateur.
            for item in data_list:

                # Récupère l'adresse Proxy utilisateur.
                raw_ip = ValidationUtils.getValueSafely(item, "ipAddress")

                # Normalise l'adresse.
                result = ValidationUtils.normalizeIpAddress(raw_ip)

                # Vérifie le résultat de la normalisation.
                if not result["valid"]:

                    Settings.write_log_event(
                        "validated_data_merge_failed",
                        "ERROR",
                        reason="invalid_proxy_address",
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": (
                            "There is an invalid IP address. " "Please check your data."
                        ),
                    }

                # Adresse normalisée.
                formatted_ip = result["data"]

                # Extrait uniquement l'IP.
                ip_only = formatted_ip.split("#")[0]

                # Cherche les informations correspondantes
                # retournées par l'API.
                api_info = api_map.get(ip_only)

                # Si aucune configuration API n'est trouvée,
                # la fusion ne peut pas continuer.
                if not api_info:

                    Settings.write_log_event(
                        "validated_data_merge_failed",
                        "ERROR",
                        reason="proxy_configuration_missing",
                    )

                    return {
                        "valid": False,
                        "data": None,
                        "error": ("Service data is missing for " "some IP addresses."),
                    }

                # Construit la structure finale utilisée
                # par le reste de l'application.
                final_list.append(
                    {
                        # Email du compte.
                        "email": ValidationUtils.getValueSafely(item, "email"),
                        # Mot de passe email.
                        "password_email": (
                            ValidationUtils.getValueSafely(item, "passwordEmail")
                        ),
                        # Adresse Proxy normalisée.
                        "ip_address": formatted_ip,
                        # Port fourni par l'API.
                        "port": api_info.get("port"),
                        # Login fourni par l'API.
                        "login": api_info.get("login"),
                        # Mot de passe fourni par l'API.
                        "password": api_info.get("pass"),
                        # Email de récupération.
                        "recovery_email": (
                            ValidationUtils.getValueSafely(item, "recoveryEmail")
                        ),
                        # Nouvelle adresse email de récupération.
                        "new_recovery_email": (
                            ValidationUtils.getValueSafely(item, "new_recovery_email")
                        ),
                    }
                )

            # Journalise uniquement le nombre de lignes.
            Settings.write_log_event(
                "validated_data_merge_completed",
                "INFO",
                input_row_count=len(data_list),
                output_row_count=len(final_list),
            )

            return {"valid": True, "data": final_list, "error": None}

        except Exception as e:

            Settings.write_log_dev_file(
                f"Error merging data: {e}\n" f"{traceback.format_exc()}", "ERROR"
            )

            return {
                "valid": False,
                "data": None,
                "error": ("An error occurred while merging the data."),
            }

    # =========================================================
    # VALIDATION DES FICHIERS ET DES CHEMINS
    # =========================================================

    @staticmethod
    def validate_path(
        path: str, must_exist: bool = True, is_file: bool = False
    ) -> bool:
        """
        Vérifie si un chemin est valide.

        is_file=True
            -> le chemin doit être un fichier.

        is_file=False
            -> le chemin doit être un dossier.
        """

        # Journalise l'opération.
        Settings.write_log_dev_file("Validating path", "INFO")

        # Vérifie le type et la présence du chemin.
        if not path or not isinstance(path, str):

            Settings.write_log_dev_file("Path is invalid or not a string", "ERROR")

            return False

        # Si le chemin doit exister, vérifie sa présence.
        if must_exist and not os.path.exists(path):

            Settings.write_log_dev_file("Path does not exist", "ERROR")

            return False

        try:

            if must_exist:

                # Si is_file=True, vérifie qu'il s'agit bien d'un fichier.
                if is_file and not os.path.isfile(path):

                    Settings.write_log_dev_file("Path is not a file", "ERROR")

                    return False

                # Sinon, vérifie qu'il s'agit bien d'un dossier.
                elif not is_file and not os.path.isdir(path):

                    Settings.write_log_dev_file("Path is not a directory", "ERROR")

                    return False

            # Normalise le chemin avant de confirmer la validation.
            normalized_path = os.path.normpath(path)

            Settings.write_log_dev_file("Path validation succeeded", "INFO")

            return True

        except Exception as e:

            Settings.write_log_dev_file(
                "Exception in validate_path: " f"{e}\n{traceback.format_exc()}", "ERROR"
            )

            return False

    # =========================================================
    # CRÉATION D'UN FICHIER OU DOSSIER
    # =========================================================

    @staticmethod
    def ensurePathExists(path: str, is_file: bool = True) -> bool:
        """
        Vérifie l'existence d'un fichier ou dossier.
        Le crée s'il n'existe pas.
        """

        Settings.write_log_dev_file("Ensuring path exists", "INFO")

        try:

            # =================================================
            # CAS D'UN FICHIER
            # =================================================

            if is_file:

                # Récupère le dossier parent.
                directory = os.path.dirname(path)

                # Crée le dossier parent s'il n'existe pas.
                if directory and not os.path.exists(directory):

                    Settings.write_log_dev_file("Creating required directory", "INFO")

                    os.makedirs(directory, exist_ok=True)

                # Crée le fichier s'il n'existe pas.
                if not os.path.exists(path):

                    Settings.write_log_dev_file("Creating required file", "INFO")

                    # Le mode "a" permet de créer le fichier
                    # sans supprimer son contenu s'il existe.
                    open(path, "a", encoding="utf-8").close()

                else:

                    Settings.write_log_dev_file("File already exists", "INFO")

            # =================================================
            # CAS D'UN DOSSIER
            # =================================================

            else:

                # Crée le dossier s'il n'existe pas.
                if not os.path.exists(path):

                    Settings.write_log_dev_file("Creating required directory", "INFO")

                    os.makedirs(path, exist_ok=True)

                else:

                    Settings.write_log_dev_file("Directory already exists", "INFO")

            return True

        except Exception as e:

            Settings.write_log_dev_file(
                "Exception in ensurePathExists: " f"{e}\n{traceback.format_exc()}",
                "ERROR",
            )

            return False

    # =========================================================
    # VÉRIFICATION SIMPLE D'EXISTENCE D'UN PATH
    # =========================================================

    @staticmethod
    def pathExists(path: str) -> bool:
        """
        Retourne True si le fichier ou dossier existe.
        """

        # Vérifie directement l'existence du chemin.
        exists = os.path.exists(path)

        Settings.write_log_dev_file(f"Path exists check result: {exists}", "INFO")

        return exists

    # =========================================================
    # VALIDATION DU FORMAT DE SESSION
    # =========================================================

    @staticmethod
    def validate_session_format(session_data: str) -> Tuple[bool, Optional[Dict]]:
        """
        Valide et parse le format d'une session.

        Format attendu :

        username::
        password::
        date::
        entityOriginal::
        entityNew::
        Id_User
        """

        # Vérifie que la session existe et contient le séparateur.
        if not session_data or "::" not in session_data:
            return False, None

        # Sépare les différentes parties.
        parts = session_data.split("::")

        # Le format attendu contient exactement 6 éléments.
        if len(parts) != 6:
            return False, None

        # Affecte chaque élément à sa variable.
        (username, password, date_str, entityOriginal, entityNew, Id_User) = parts

        try:

            # Vérifie le format de la date.
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        except ValueError:

            # Date invalide.
            return False, None

        # Retourne les données sous forme structurée.
        return True, {
            "username": username.strip(),
            "password": password.strip(),
            "date": date_str.strip(),
            "p_entity_Origine": entityOriginal.strip(),
            "p_entity_Nouveau": entityNew.strip(),
            "Id_User": Id_User.strip(),
        }

    # =========================================================
    # VALIDATION D'UN QLINEEDIT
    # =========================================================

    @staticmethod
    def validate_qlineedit_text(
        input_data: Union[QLineEdit, str],
        validator_type: str = "any",
        min_length: int = 0,
        max_length: int = 1000,
    ) -> Tuple[bool, str]:
        """
        Valide le contenu d'un QLineEdit ou d'une chaîne.

        Types supportés :
            any
            email
            numeric
            numeric_range
        """

        try:

            # =================================================
            # RÉCUPÉRATION DU TEXTE
            # =================================================

            # Si l'objet possède text(), il est probablement
            # un QLineEdit ou un widget similaire.
            if hasattr(input_data, "text"):

                text = input_data.text().strip()

            else:

                # Sinon, convertit simplement la valeur en chaîne.
                text = str(input_data).strip()

            # =================================================
            # VALIDATION DE BASE
            # =================================================

            # Champ obligatoire.
            if not text and min_length > 0:
                return False, "This field is required"

            # Vérifie la longueur minimale.
            if len(text) < min_length:
                return (False, f"Minimum {min_length} characters required")

            # Vérifie la longueur maximale.
            if len(text) > max_length:
                return (False, f"Maximum {max_length} characters allowed")

            # =================================================
            # VALIDATION SPÉCIFIQUE
            # =================================================

            if validator_type == "email":

                # Vérifie le format email.
                if not ValidationUtils.validate_email(text):
                    return False, "Invalid email format"

            elif validator_type == "numeric":

                # Vérifie que le texte contient uniquement des chiffres.
                if not text.isdigit():
                    return False, "Numeric value required"

            elif validator_type == "numeric_range":

                # Vérifie le format d'une plage numérique.
                valid, _ = ValidationUtils.validate_numeric_range(text)

                if not valid:
                    return (False, "Invalid format. Use: number or min,max")

            # Si toutes les validations passent.
            return True, "Valid text"

        except Exception as e:

            # Journalise l'erreur technique.
            Settings.write_log_dev_file(
                "Exception in validate_qlineedit_text: "
                f"{e}\n{traceback.format_exc()}",
                "ERROR",
            )

            return (False, f"Validation error: {str(e)}")

    # =========================================================
    # PARSING D'UNE PLAGE ALÉATOIRE
    # =========================================================

    @staticmethod
    def parse_random_range(text: str, default: int = 0) -> int:
        """
        Transforme :
            "10,20" -> nombre aléatoire entre 10 et 20
            "10"    -> 10

        En cas d'erreur :
            retourne default.
        """

        try:

            # Si une virgule existe, traite la valeur comme une plage.
            if "," in text:

                # Sépare les deux valeurs.
                min_val, max_val = map(int, text.split(","))

                # Retourne une valeur aléatoire dans la plage.
                return random.randint(min_val, max_val)

            # Sinon, traite le texte comme un nombre unique.
            return int(text)

        except (ValueError, TypeError) as error:

            Settings.write_log_dev_file(
                "Error parsing random range "
                f"| exception={type(error).__name__}: {error} "
                f"| text={text!r} "
                f"| default={default}\n{traceback.format_exc()}",
                "ERROR",
            )

            # Retourne la valeur par défaut.
            return default

    # =========================================================
    # VALIDATION ET CORRECTION D'UN QLINEEDIT
    # =========================================================

    @staticmethod
    def validate_and_correct_qlineedit(
        qlineedit: QLineEdit, default_value: str = "50,50"
    ) -> None:
        """
        Valide une valeur de type :
            50
            50,50

        Corrige automatiquement certaines valeurs invalides
        et applique un style visuel au champ.
        """

        # Récupère le contenu actuel du champ.
        text = qlineedit.text().strip()

        # Regex permettant :
        #   50
        #   50,100
        pattern = r"^\s*(\d+)" r"(?:\s*,\s*(\d+))?" r"\s*$"

        # Vérifie le contenu.
        match = re.match(pattern, text)

        # =================================================
        # CAS VALIDE
        # =================================================

        if match:

            # Première valeur.
            min_val = int(match.group(1))

            # Deuxième valeur si elle existe.
            # Sinon, utilise la première valeur.
            max_val = int(match.group(2)) if match.group(2) else min_val

            # =================================================
            # MIN > MAX
            # =================================================

            if min_val > max_val:

                # Conserve le comportement actuel :
                # la valeur maximale est remplacée par min_val.
                qlineedit.setText(f"{min_val},{min_val}")

                # Sauvegarde le style actuel.
                old_style = qlineedit.styleSheet()

                # Fonction exécutée après le cycle actuel de Qt.
                def apply_style():

                    # Ajoute la bordure d'erreur.
                    new_style = ValidationUtils.inject_border_into_style(old_style)

                    qlineedit.setStyleSheet(new_style)

                    # Message affiché à l'utilisateur.
                    qlineedit.setToolTip(
                        "The minimum value is greater than "
                        "the maximum value. The value was corrected."
                    )

                # Programme la modification UI.
                QTimer.singleShot(0, apply_style)

            # =================================================
            # VALEUR CORRECTE
            # =================================================

            else:

                # Récupère le style actuel.
                old_style = qlineedit.styleSheet()

                # Supprime une éventuelle bordure d'erreur.
                cleaned = ValidationUtils.remove_border_from_style(old_style)

                qlineedit.setStyleSheet(cleaned)

                # Supprime le tooltip.
                qlineedit.setToolTip("")

        # =================================================
        # FORMAT INVALIDE
        # =================================================

        else:

            # Remplace la valeur invalide par la valeur par défaut.
            qlineedit.setText(default_value)

            # Sauvegarde le style actuel.
            old_style = qlineedit.styleSheet()

            # Fonction exécutée après le cycle Qt.
            def apply_error():

                # Ajoute la bordure d'erreur.
                new_style = ValidationUtils.inject_border_into_style(old_style)

                qlineedit.setStyleSheet(new_style)

                # Explique le format attendu.
                qlineedit.setToolTip(
                    "Enter a value in the format " "'Min,Max' or a single number."
                )

            # Programme la modification UI.
            QTimer.singleShot(0, apply_error)

    # =========================================================
    # VALIDATION D'UN QLINEEDIT AVEC PLAGE
    # =========================================================

    @staticmethod
    def validate_qlineedit_with_range(
        qlineedit: QLineEdit,
        default_value: str = "50,50",
        callback: Optional[Callable] = None,
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Valide un QLineEdit contenant une plage numérique.
        """

        # Corrige d'abord le champ si nécessaire.
        ValidationUtils.validate_and_correct_qlineedit(qlineedit, default_value)

        # Récupère le texte après correction.
        corrected_text = qlineedit.text().strip()

        # Valide et parse la plage.
        valid, range_values = ValidationUtils.validate_numeric_range(corrected_text)

        # Exécute le callback si fourni.
        if callback:
            callback(qlineedit, valid, range_values)

        # Retourne l'état et la plage.
        return valid, range_values

    # =========================================================
    # GESTION DES STYLES CSS
    # =========================================================

    @staticmethod
    def inject_border_into_style(
        old_style: str, border_line: str = ("border: 2px solid #cc4c4c;")
    ) -> str:
        """
        Ajoute une bordure à un bloc QLineEdit existant.

        Si aucun bloc QLineEdit n'existe,
        un nouveau bloc est ajouté.
        """

        # Regex recherchant un bloc QLineEdit.
        pattern = r"(QLineEdit\s*{[^}]*?)\s*}"

        # Cherche le bloc dans le stylesheet.
        match = re.search(pattern, old_style, re.DOTALL)

        # =================================================
        # BLOC QLINEEDIT EXISTANT
        # =================================================

        if match:

            # Récupère le contenu avant la fermeture du bloc.
            before_close = match.group(1)

            # N'ajoute la bordure que si elle n'existe pas déjà.
            if "border" not in before_close:

                # Construit le nouveau bloc CSS.
                new_block = before_close + f"\n    {border_line}\n}}"

                # Remplace le bloc original.
                result = re.sub(pattern, new_block, old_style, flags=re.DOTALL)

                return result

            # Bordure déjà présente.
            return old_style

        # =================================================
        # AUCUN BLOC QLINEEDIT
        # =================================================

        # Ajoute un nouveau bloc CSS.
        appended = (
            old_style
            + f"""
            QLineEdit {{
                {border_line}
            }}"""
        )

        return appended

    # =========================================================
    # SUPPRESSION D'UNE BORDURE CSS
    # =========================================================

    @staticmethod
    def remove_border_from_style(style: str) -> str:
        """
        Supprime les propriétés CSS 'border' du stylesheet.
        """

        # Supprime toute déclaration border: ...;
        cleaned_style = re.sub(r"border\s*:\s*[^;]+;", "", style, flags=re.IGNORECASE)

        # Nettoie les espaces inutiles.
        return cleaned_style.strip()

    # =========================================================
    # GÉNÉRATION D'UN SESSION ID
    # =========================================================

    @staticmethod
    def generateSessionId(length: int = 5) -> str:
        """
        Génère un identifiant court basé sur UUID4.

        Exemple :
            UUID complet
                ↓
            suppression des '-'
                ↓
            récupération des N premiers caractères
        """

        # La longueur doit être strictement positive.
        if length <= 0:
            raise ValueError("Length must be a positive integer")

        # Génère un UUID aléatoire.
        session_uuid = uuid.uuid4()

        # Supprime les tirets et récupère la longueur demandée.
        return str(session_uuid).replace("-", "")[:length]

    # =========================================================
    # GÉNÉRATION D'UN MOT DE PASSE
    # =========================================================

    @staticmethod
    def generateSecurePassword(length: int = 12) -> str:
        """
        Génère un mot de passe contenant :
            - minuscules
            - majuscules
            - chiffres
            - caractères spéciaux

        Note :
            La logique actuelle utilise random.
            Pour un véritable secret cryptographique,
            secrets serait préférable.
        """

        # Refuse les mots de passe trop courts.
        if length < 12:
            raise ValueError("The minimum recommended length is 12 characters")

        # Liste des caractères disponibles.
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits

        special_chars = "!@#$%^&*()-_+=<>?/|"

        # Garantit au moins un caractère de chaque catégorie.
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special_chars),
        ]

        # Calcule le nombre de caractères restant à générer.
        remaining_length = length - len(password)

        # Combine toutes les catégories.
        all_chars = lowercase + uppercase + digits + special_chars

        # Génère les caractères restants.
        password += random.choices(all_chars, k=remaining_length)

        # Mélange les caractères.
        random.shuffle(password)

        # Convertit la liste en String.
        return "".join(password)

    # =========================================================
    # RÉCUPÉRATION D'UNE VALEUR DEPUIS PLUSIEURS CLÉS POSSIBLES
    # =========================================================

    @staticmethod
    def getValueFromDictionary(data_dict: Dict, possible_keys: List[str]) -> str:
        """
        Recherche la première clé disponible dans un dictionnaire.
        """

        # Parcourt les clés candidates dans l'ordre.
        for key in possible_keys:

            # Vérifie si la clé existe.
            if key in data_dict:

                # Conserve le comportement actuel :
                # si la valeur est vide, retourne le nom de la clé.
                if not data_dict[key]:
                    return key

                # Sinon, retourne la valeur.
                return data_dict[key]

        # Si aucune clé n'existe,
        # retourne la première clé candidate.
        return possible_keys[0] if possible_keys else ""

    # =========================================================
    # EXTRACTION D'EMAIL DEPUIS UN NOM DE FICHIER LOG
    # =========================================================

    @staticmethod
    def extractEmailFromLogFile(file_name):
        """
        Extrait un email depuis le nom d'un fichier log.

        Exemple attendu :
            log_2026-09-28T12-30-10-123Z_user@example.com.txt
        """

        # Conserve uniquement le nom du fichier.
        file_name = os.path.basename(file_name)

        # Recherche l'email selon le format attendu du fichier.
        match = re.search(
            r"log_\d{4}-\d{2}-\d{2}T"
            r"\d{2}-\d{2}-\d{2}-\d{3}Z_"
            r"([\w.+-]+@[\w.-]+\.[a-zA-Z]{2,6})"
            r"\.txt",
            file_name,
        )

        # Si un email est trouvé.
        if match:

            # Récupère l'email extrait.
            email = match.group(1)

            return email

        # Aucun email trouvé.
        return None

    # =========================================================
    # COLLECTE DES ADRESSES PROXY UNIQUES
    # =========================================================

    @staticmethod
    def collect_unique_proxy_addresses(
        data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extrait les adresses IP uniques des comptes.
        """

        try:

            # Vérifie si la liste contient des données.
            if not data_list:

                Settings.write_log_dev_file(
                    "No account data provided " "for proxy address collection",
                    "WARNING",
                )

                return {
                    "valid": True,
                    "data": set(),
                    "error": None,
                    "error_title": "No Data",
                    "error_message": (
                        "No account entries were provided "
                        "for proxy address collection."
                    ),
                }

            # Utilise un Set afin de supprimer automatiquement
            # les adresses IP dupliquées.
            unique_ips: set = set()

            # Parcourt chaque compte.
            for index, item in enumerate(data_list):

                # Récupère l'adresse IP.
                ip = ValidationUtils.getValueSafely(item, "ipAddress")

                # Ajoute l'adresse au Set si elle existe.
                if ip:

                    unique_ips.add(str(ip))

                else:

                    # Journalise uniquement l'index,
                    # pas la valeur sensible.
                    Settings.write_log_dev_file(
                        f"Missing ipAddress at index {index}", "WARNING"
                    )

            # Journalise le nombre total d'IP uniques.
            Settings.write_log_dev_file(
                "Proxy addresses collected - total: " f"{len(unique_ips)}", "INFO"
            )

            return {
                "valid": True,
                "data": unique_ips,
                "error": None,
                "error_title": ("Proxy Address Collection Successful"),
                "error_message": (
                    f"Collected {len(unique_ips)} " "unique proxy address(es)."
                ),
            }

        except Exception as e:

            # Journalise l'erreur technique.
            Settings.write_log_dev_file(
                "Error collecting unique proxy addresses: "
                f"{e}\n{traceback.format_exc()}",
                "ERROR",
            )

            return {
                "valid": False,
                "data": None,
                "error": str(e),
                "error_title": ("Proxy Address Collection Error"),
                "error_message": (
                    "An error occurred while collecting "
                    "proxy addresses. Please verify the "
                    "data format and retry."
                ),
            }


# =========================================================
# INSTANCE GLOBALE
# =========================================================

# Crée une instance globale afin de pouvoir utiliser :
#
#     ValidationUtils.validate_email(...)
#
# directement dans les autres modules.
#
# La plupart des méthodes sont staticmethod,
# donc elles ne dépendent pas réellement de l'instance.
ValidationUtils = ValidationUtils()
