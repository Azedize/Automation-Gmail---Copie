# utils/validation_utils.py
import os
import json
import re
import random
import string
import uuid
import zipfile
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
from urllib.parse import urlparse
from PyQt6.QtWidgets import QLineEdit, QMessageBox, QApplication
from PyQt6.QtCore import QTimer
import traceback

class ValidationUtils:
    """Classe de validation unifiée pour toutes les validations et générations"""
    
    # Patterns regex pré-compilés pour meilleure performance
    _PATTERN_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    _PATTERN_IP = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
    _PATTERN_NUMERIC_RANGE = re.compile(r'^\s*(\d+)(?:\s*,\s*(\d+))?\s*$')
    
    # Constantes pour les validations
    VALID_BROWSERS = ["chrome", "firefox", "edge", "comodo", "icedragon"]
    VALID_ISPS = ["Gmail", "Hotmail", "Yahoo", "Others"]
    
    # ==================== VALIDATION DE DONNÉES ====================
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide le format d'un email"""
        if not email or not isinstance(email, str):
            return False
        return ValidationUtils._PATTERN_EMAIL.match(email) is not None
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """Valide un mot de passe selon des critères de sécurité"""
        if not password or len(password) < min_length:
            return False, f"Le mot de passe doit contenir au moins {min_length} caractères"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()-_+=<>?/|" for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial"
        
        return True, "Mot de passe valide"
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Valide une adresse IP"""
        if not ip or not isinstance(ip, str):
            return False
        
        match = ValidationUtils._PATTERN_IP.match(ip)
        if not match:
            return False
        
        for num in match.groups():
            if not 0 <= int(num) <= 255:
                return False
        
        return True
    
    @staticmethod
    def validate_port(port: str) -> bool:
        """Valide un numéro de port"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_proxy_info(ip: str, port: str) -> Tuple[bool, str]:
        """Valide les informations de proxy"""
        if not ValidationUtils.validate_ip_address(ip):
            return False, "Adresse IP invalide"
        
        if not ValidationUtils.validate_port(port):
            return False, "Port invalide (doit être entre 1 et 65535)"
        
        return True, "Proxy valide"
    
    @staticmethod
    def validate_numeric_range(text: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Valide un texte représentant un nombre ou une plage
        Formats acceptés: "50", "50,100", "1,10"
        """
        if not text or not isinstance(text, str):
            return False, None
        
        text = text.strip()
        match = ValidationUtils._PATTERN_NUMERIC_RANGE.match(text)
        
        if not match:
            return False, None
        
        min_val = int(match.group(1))
        max_val = int(match.group(2)) if match.group(2) else min_val
        
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        
        return True, (min_val, max_val)
    
    @staticmethod
    def validate_user_input_format(lines: List[str]) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Valide le format des données utilisateur (email, proxy, etc.)
        """
        if not lines:
            return False, None, "Aucune donnée fournie"
        
        data_list = []
        
        for line_num, line in enumerate(lines, 1):
            parts = [p.strip() for p in line.split(";")]
            
            # Format minimal attendu : email;password;ip;port
            if len(parts) < 4:
                return False, None, f"Ligne {line_num}: Format invalide (au moins 4 champs requis)"
            
            email = parts[0]
            password_email = parts[1] if len(parts) > 1 else ""
            ip_address = parts[2] if len(parts) > 2 else ""
            port = parts[3] if len(parts) > 3 else ""
            
            # Validation de l'email
            if not ValidationUtils.validate_email(email):
                return False, None, f"Ligne {line_num}: Email invalide: {email}"
            
            # Validation de l'adresse IP
            if ip_address and not ValidationUtils.validate_ip_address(ip_address):
                return False, None, f"Ligne {line_num}: Adresse IP invalide: {ip_address}"
            
            # Validation du port
            if port and not ValidationUtils.validate_port(port):
                return False, None, f"Ligne {line_num}: Port invalide: {port}"
            
            # Construction de l'entrée
            entry = {
                "email": email,
                "password_email": password_email,
                "ip_address": ip_address,
                "port": port
            }
            
            # Ajout des champs optionnels
            if len(parts) > 4:
                entry["login"] = parts[4]
            if len(parts) > 5:
                entry["password"] = parts[5]
            if len(parts) > 6:
                entry["recovery_email"] = parts[6]
            if len(parts) > 7:
                entry["new_recovery_email"] = parts[7]
            
            data_list.append(entry)
        
        return True, data_list, f"Format valide - {len(data_list)} entrées traitées"
    
    @staticmethod
    def process_user_input(input_data: str, entered_number_text: str) -> dict:
        """
        Traite et valide les données d'entrée utilisateur complètes
        """
        print("🔵 [START] process_user_input")

        result = {
            "success": False,
            "data_list": None,
            "entered_number": None,
            "error_title": "",
            "error_message": "",
            "error_type": "critical"
        }

        # --------------------
        # Validation de base
        # --------------------
        if not input_data or not input_data.strip():
            result.update({
                "error_title": "Error - Missing Data",
                "error_message": "Please enter the required information before proceeding."
            })
            return result

        if not entered_number_text or not entered_number_text.strip():
            result.update({
                "error_title": "Error - Missing Number",
                "error_message": "Please enter the number of operations to process."
            })
            return result

        if not entered_number_text.isdigit():
            result.update({
                "error_title": "Error - Invalid Input",
                "error_message": "Please enter a valid numerical value in the number field."
            })
            return result

        entered_number = int(entered_number_text)

        try:
            # --------------------
            # Parsing des lignes
            # --------------------
            lines = [line.strip() for line in input_data.split("\n") if line.strip()]

            if len(lines) < 2:
                result.update({
                    "error_title": "Error - Invalid Format",
                    "error_message": "Header detected but no data rows found."
                })
                return result

            header = [k.strip() for k in lines[0].split(";")]
            data_lines = lines[1:]

            # --------------------
            # Définition des patterns (comme la fonction originale)
            # --------------------
            mandatory_patterns = [
                ["email", "passwordEmail", "ipAddress", "port"],
                ["Email", "password_email", "ip_address", "port"]
            ]

            optional_patterns = [
                ["login", "password", "recoveryEmail", "newrecoveryEmail"],
                ["login", "password", "recovery_email", "New_recovery_email"]
            ]

            all_valid_keys = set()
            for pat in mandatory_patterns + optional_patterns:
                all_valid_keys.update(pat)

            # --------------------
            # Vérification des clés
            # --------------------
            if not any(set(pat).issubset(header) for pat in mandatory_patterns):
                result.update({
                    "error_title": "Error - Required Keys Missing",
                    "error_message": (
                        "Please include required keys using one of the supported formats."
                    )
                })
                return result

            invalid_keys = [k for k in header if k not in all_valid_keys]
            if invalid_keys:
                result.update({
                    "error_title": "Error - Invalid Keys",
                    "error_message": f"Invalid keys detected: {', '.join(invalid_keys)}"
                })
                return result

            # --------------------
            # Conversion en data_list
            # --------------------
            data_list = []

            for index, line in enumerate(data_lines, start=1):
                values = [v.strip() for v in line.split(";")]

                if len(values) != len(header):
                    result.update({
                        "error_title": "Error - Key/Value Mismatch",
                        "error_message": f"Line {index}: number of values does not match header."
                    })
                    return result

                data_list.append(dict(zip(header, values)))

            # --------------------
            # Validation de la plage
            # --------------------
            if entered_number > len(data_list):
                result.update({
                    "error_title": "Error - Invalid Range",
                    "error_message": (
                        f"Please enter a value between 1 and {len(data_list)}."
                    )
                })
                return result

            # --------------------
            # Succès
            # --------------------
            result.update({
                "success": True,
                "data_list": data_list,
                "entered_number": entered_number,
                "error_title": "Success",
                "error_message": "Input data validated successfully",
                "error_type": "success"
            })

        except Exception as e:
            result.update({
                "error_title": "Operation Failed - System Error",
                "error_message": f"Critical failure during data processing: {str(e)}"
            })

        print("🔵 [END] process_user_input")
        return result


    
    @staticmethod
    def _validate_entries_detailed(data_list: List[Dict]) -> Dict[str, Any]:
        """Validation détaillée de chaque entrée"""
        errors = []
        
        for i, entry in enumerate(data_list, start=2):
            line_errors = []
            
            # Identifier les clés
            keys = list(entry.keys())
            email_key = ValidationUtils._get_email_key(keys)
            ip_key = ValidationUtils._get_ip_key(keys)
            port_key = ValidationUtils._get_port_key(keys)
            
            # Valider l'email
            if email_key and email_key in entry and entry[email_key]:
                if not ValidationUtils.validate_email(entry[email_key]):
                    line_errors.append(f"Invalid email format: {entry[email_key]}")
            
            # Valider le proxy
            if ip_key and port_key and ip_key in entry and port_key in entry:
                if entry[ip_key] and entry[port_key]:
                    is_valid, proxy_msg = ValidationUtils.validate_proxy_info(entry[ip_key], entry[port_key])
                    if not is_valid:
                        line_errors.append(f"Invalid proxy: {proxy_msg}")
            
            # Valider le mot de passe email (s'il existe)
            password_keys = [k for k in keys if "password" in k.lower() and "email" in k.lower()]
            for pass_key in password_keys:
                if pass_key in entry and entry[pass_key]:
                    is_valid, pass_msg = ValidationUtils.validate_password(entry[pass_key], min_length=6)
                    if not is_valid:
                        line_errors.append(f"Weak password: {pass_msg}")
            
            if line_errors:
                errors.append(f"Line {i}: {', '.join(line_errors)}")
        
        if errors:
            error_count = len(errors)
            display_errors = errors[:5]
            error_text = "<br>".join(display_errors)
            
            if error_count > 5:
                error_text += f"<br>... and {error_count - 5} more errors"
            
            return {
                "valid": False,
                "message": f"Validation errors detected:<br>{error_text}"
            }
        
        return {
            "valid": True,
            "message": "All entries validated successfully"
        }
    
    @staticmethod
    def get_input_statistics(data_list: List[Dict]) -> Dict[str, Any]:
        """Génère des statistiques sur les données d'entrée"""
        if not data_list:
            return {"error": "No data available"}
        
        stats = {
            "total_entries": len(data_list),
            "fields_per_entry": len(data_list[0]) if data_list else 0,
            "unique_fields": set(),
            "validation_summary": {
                "valid_emails": 0,
                "valid_proxies": 0,
                "complete_entries": 0
            }
        }
        
        for entry in data_list:
            stats["unique_fields"].update(entry.keys())
            
            # Valider les emails
            email_key = ValidationUtils._get_email_key(list(entry.keys()))
            if email_key and email_key in entry and entry[email_key]:
                if ValidationUtils.validate_email(entry[email_key]):
                    stats["validation_summary"]["valid_emails"] += 1
            
            # Valider les proxies
            ip_key = ValidationUtils._get_ip_key(list(entry.keys()))
            port_key = ValidationUtils._get_port_key(list(entry.keys()))
            if all([ip_key, port_key, ip_key in entry, port_key in entry, 
                   entry[ip_key], entry[port_key]]):
                is_valid, _ = ValidationUtils.validate_proxy_info(entry[ip_key], entry[port_key])
                if is_valid:
                    stats["validation_summary"]["valid_proxies"] += 1
            
            # Vérifier les entrées complètes
            if all([email_key, email_key in entry, entry[email_key],
                   ip_key, ip_key in entry, entry[ip_key],
                   port_key, port_key in entry, entry[port_key]]):
                stats["validation_summary"]["complete_entries"] += 1
        
        stats["unique_fields"] = list(stats["unique_fields"])
        return stats
    
    @staticmethod
    def format_input_for_display(data_list: List[Dict], max_entries: int = 3) -> str:
        """Formate les données d'entrée pour l'affichage"""
        if not data_list:
            return "No data available"
        
        stats = ValidationUtils.get_input_statistics(data_list)
        
        formatted = (
            f"✅ Input validated successfully!<br><br>"
            f"• Total entries: {stats['total_entries']}<br>"
            f"• Fields per entry: {stats['fields_per_entry']}<br>"
            f"• Valid emails: {stats['validation_summary']['valid_emails']}<br>"
            f"• Valid proxies: {stats['validation_summary']['valid_proxies']}<br>"
            f"• Complete entries: {stats['validation_summary']['complete_entries']}<br><br>"
        )
        
        # Ajouter un aperçu des premières entrées
        if data_list:
            formatted += "Sample entries:<br>"
            for i, entry in enumerate(data_list[:max_entries], 1):
                entry_preview = []
                for key, value in list(entry.items())[:3]:
                    if value:
                        truncated = value[:20] + "..." if len(value) > 20 else value
                        entry_preview.append(f"{key}: {truncated}")
                
                formatted += f"{i}. {', '.join(entry_preview)}<br>"
            
            if len(data_list) > max_entries:
                formatted += f"... and {len(data_list) - max_entries} more entries"
        
        return formatted
    
    @staticmethod
    def _get_email_key(keys: List[str]) -> Optional[str]:
        """Trouve la clé correspondant à l'email"""
        for key in keys:
            if key.lower() in ["email", "mail"]:
                return key
        return None
    
    @staticmethod
    def _get_ip_key(keys: List[str]) -> Optional[str]:
        """Trouve la clé correspondant à l'IP"""
        for key in keys:
            if "ip" in key.lower():
                return key
        return None
    
    @staticmethod
    def _get_port_key(keys: List[str]) -> Optional[str]:
        """Trouve la clé correspondant au port"""
        for key in keys:
            if "port" in key.lower():
                return key
        return None
    
    # ==================== VALIDATION DE FICHIERS ET CHEMINS ====================
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = True) -> Tuple[bool, str]:
        """Valide un chemin de fichier"""
        if not path or not isinstance(path, str):
            return False, "Chemin de fichier invalide"
        
        if must_exist and not os.path.exists(path):
            return False, f"Le fichier n'existe pas: {path}"
        
        try:
            os.path.normpath(path)
            return True, "Chemin valide"
        except Exception:
            return False, "Chemin de fichier invalide"
    
    @staticmethod
    def validate_directory_path(path: str, must_exist: bool = True) -> Tuple[bool, str]:
        """Valide un chemin de dossier"""
        if not path or not isinstance(path, str):
            return False, "Chemin de dossier invalide"
        
        if must_exist and not os.path.exists(path):
            return False, f"Le dossier n'existe pas: {path}"
        
        try:
            if must_exist and not os.path.isdir(path):
                return False, "Le chemin spécifié n'est pas un dossier"
            
            os.path.normpath(path)
            return True, "Chemin de dossier valide"
        except Exception:
            return False, "Chemin de dossier invalide"
    
    @staticmethod
    def ensure_path_exists(path: str, is_file: bool = True) -> bool:
        """S'assure qu'un chemin existe, le crée si nécessaire"""
        try:
            if is_file:
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)

                if not os.path.exists(path):
                    open(path, "a", encoding="utf-8").close()
                    
            else:
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
            return True

        except Exception as e:
            print(f"Error ensuring path exists: {e}")
            return False
    
    @staticmethod
    def path_exists(path: str) -> bool:
        """Vérifie si un chemin existe"""
        return os.path.exists(path)
    
    @staticmethod
    def validate_zip_file(zip_path: str) -> Tuple[bool, str]:
        """Valide l'intégrité d'un fichier ZIP"""
        try:
            if not os.path.exists(zip_path):
                return False, f"Fichier ZIP introuvable: {zip_path}"
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test d'ouverture
                bad_file = zip_ref.testzip()
                if bad_file:
                    return False, f"Fichier corrompu dans le ZIP: {bad_file}"
                
                # Vérifier qu'il n'est pas vide
                if not zip_ref.namelist():
                    return False, "Le fichier ZIP est vide"
                
                # Vérifier la sécurité des chemins
                for member in zip_ref.namelist():
                    member_path = os.path.abspath(os.path.join("/tmp", member))
                    if not member_path.startswith(os.path.abspath("/tmp")):
                        return False, f"Chemin non sécurisé détecté: {member}"
            
            return True, "Fichier ZIP valide"
            
        except zipfile.BadZipFile:
            return False, "Fichier ZIP corrompu ou invalide"
        except Exception as e:
            return False, f"Erreur lors de la validation du ZIP: {str(e)}"
    
    @staticmethod
    def validate_directory_permissions(directory_path: str) -> Tuple[bool, str]:
        """Valide les permissions d'écriture sur un dossier"""
        try:
            if not os.path.exists(directory_path):
                return True, "Le dossier n'existe pas mais peut être créé"
            
            # Test d'écriture
            test_file = os.path.join(directory_path, ".permission_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return True, "Permissions d'écriture valides"
            except PermissionError:
                return False, "Permission d'écriture refusée sur le dossier"
            except Exception:
                return False, "Impossible d'écrire dans le dossier"
                
        except Exception as e:
            return False, f"Erreur lors de la vérification des permissions: {str(e)}"
    
    @staticmethod
    def validate_result_file_format(file_path: str) -> Tuple[bool, List[Dict]]:
        """Valide le format du fichier de résultats"""
        results = []
        
        try:
            if not os.path.exists(file_path):
                return False, []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Format attendu: session_id:pid:email:status
                    parts = line.split(":")
                    if len(parts) != 4:
                        continue  # Ignorer les lignes mal formatées
                    
                    session_id, pid, email, status = [p.strip() for p in parts]
                    
                    # Validation basique
                    if not email or not status:
                        continue
                    
                    results.append({
                        "session_id": session_id,
                        "pid": pid,
                        "email": email,
                        "status": status,
                        "line_number": line_num
                    })
            
            return True, results
            
        except Exception:
            return False, []
    
    # ==================== VALIDATION JSON ET STRUCTURES ====================
    
    @staticmethod
    def validate_json_structure(json_data: Dict, required_keys: List[str]) -> Tuple[bool, str]:
        """Valide la structure d'un objet JSON"""
        if not isinstance(json_data, dict):
            return False, "Les données doivent être un dictionnaire JSON"
        
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            return False, f"Clés manquantes dans JSON: {', '.join(missing_keys)}"
        
        return True, "Structure JSON valide"
    
    @staticmethod
    def validate_configuration_structure(config_data: Dict, required_keys: List[str]) -> Tuple[bool, str]:
        """Valide la structure d'une configuration JSON"""
        if not isinstance(config_data, dict):
            return False, "Les données de configuration doivent être un dictionnaire"
        
        missing_keys = [key for key in required_keys if key not in config_data]
        if missing_keys:
            return False, f"Clés de configuration manquantes: {', '.join(missing_keys)}"
        
        return True, "Configuration valide"
    
    @staticmethod
    def validate_extension_manifest(manifest_path: str) -> Tuple[bool, str]:
        """Valide un fichier manifest.json d'extension"""
        try:
            if not os.path.exists(manifest_path):
                return False, f"Fichier manifest introuvable: {manifest_path}"
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            required_keys = ["manifest_version", "name", "version"]
            for key in required_keys:
                if key not in manifest:
                    return False, f"Clé '{key}' manquante dans le manifest"
            
            return True, f"Manifest valide: {manifest.get('name')} v{manifest.get('version')}"
            
        except json.JSONDecodeError:
            return False, "Format JSON invalide dans le manifest"
        except Exception as e:
            return False, f"Erreur lors de la lecture du manifest: {str(e)}"
    
    @staticmethod
    def validate_session_file(session_path: str) -> Tuple[bool, Optional[Dict]]:
        """Valide le fichier de session"""
        try:
            if not os.path.exists(session_path):
                return False, None
            
            with open(session_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return False, None
            
            # Format attendu: username::date::entity
            if "::" not in content:
                return False, None
            
            parts = content.split("::", 2)
            if len(parts) != 3:
                return False, None
            
            username, date_str, entity = parts
            
            # Valider le format de la date
            try:
                datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return False, None
            
            return True, {
                "username": username,
                "date": date_str,
                "entity": entity
            }
            
        except Exception:
            return False, None
    
    @staticmethod
    def validate_session_format(session_data: str) -> Tuple[bool, Optional[Dict]]:
        """Valide le format des données de session"""
        if not session_data or "::" not in session_data:
            return False, None
        
        parts = session_data.split("::", 2)
        if len(parts) != 3:
            return False, None
        
        username, date_str, entity = parts
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, None
        
        return True, {
            "username": username.strip(),
            "date": date_str.strip(),
            "entity": entity.strip()
        }
    
    # ==================== VALIDATION D'INTERFACE UTILISATEUR ====================
    
    @staticmethod
    def validate_qlineedit_text(input_data: Union[QLineEdit, str], 
                                validator_type: str = "any",
                                min_length: int = 0,
                                max_length: int = 1000) -> Tuple[bool, str]:
        """Valide le texte d'un QLineEdit"""
        try:
            # Récupérer le texte
            if hasattr(input_data, "text"):
                text = input_data.text().strip()
            else:
                text = str(input_data).strip()
            
            # Validation de base
            if not text and min_length > 0:
                return False, "Ce champ est obligatoire"
            
            if len(text) < min_length:
                return False, f"Minimum {min_length} caractères requis"
            
            if len(text) > max_length:
                return False, f"Maximum {max_length} caractères autorisés"
            
            # Validation spécifique au type
            if validator_type == "email":
                if not ValidationUtils.validate_email(text):
                    return False, "Format d'email invalide"
            
            elif validator_type == "numeric":
                if not text.isdigit():
                    return False, "Valeur numérique requise"
            
            elif validator_type == "numeric_range":
                valid, _ = ValidationUtils.validate_numeric_range(text)
                if not valid:
                    return False, "Format invalide. Utilisez: nombre ou min,max"
            
            return True, "Texte valide"
        
        except Exception as e:
            return False, f"Erreur de validation: {str(e)}"
    
    @staticmethod
    def parse_random_range(text: str, default: int = 0) -> int:
        """Parse une chaîne représentant un nombre ou une plage aléatoire"""
        try:
            if ',' in text:
                min_val, max_val = map(int, text.split(','))
                return random.randint(min_val, max_val)
            return int(text)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_qlineedit_range(qlineedit: QLineEdit, default_value: str = "50,50") -> bool:
        """Valide et corrige un QLineEdit contenant une plage numérique"""
        text = qlineedit.text().strip()
        
        if not text:
            qlineedit.setText(default_value)
            return False
        
        # Valider le format
        pattern = r'^\s*(\d+)(?:\s*,\s*(\d+))?\s*$'
        match = re.match(pattern, text)
        
        if not match:
            qlineedit.setText(default_value)
            return False
        
        min_val = int(match.group(1))
        max_val = int(match.group(2)) if match.group(2) else min_val
        
        # Corriger si min > max
        if min_val > max_val:
            qlineedit.setText(f"{min_val},{min_val}")
            return False
        
        return True
    
    @staticmethod
    def validate_and_correct_qlineedit(qlineedit: QLineEdit, default_value: str = "50,50") -> None:
        """Valide et corrige automatiquement un QLineEdit (version compatible avec la logique spécifiée)"""
        text = qlineedit.text().strip()
        pattern = r"^\s*(\d+)(?:\s*,\s*(\d+))?\s*$"
        match = re.match(pattern, text)

        if match:
            min_val = int(match.group(1))
            max_val = int(match.group(2)) if match.group(2) else min_val

            if min_val > max_val:
                qlineedit.setText(f"{min_val},{min_val}")
                old_style = qlineedit.styleSheet()
                def apply_style():
                    new_style = ValidationUtils.inject_border_into_style(old_style)
                    qlineedit.setStyleSheet(new_style)
                    qlineedit.setToolTip("La valeur Min est supérieure à Max. Correction appliquée.")
                QTimer.singleShot(0, apply_style)
            else:
                old_style = qlineedit.styleSheet()
                cleaned = ValidationUtils.remove_border_from_style(old_style)
                qlineedit.setStyleSheet(cleaned)
                qlineedit.setToolTip("")
        else:
            qlineedit.setText(default_value)
            old_style = qlineedit.styleSheet()
            def apply_error():
                new_style = ValidationUtils.inject_border_into_style(old_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip("Veuillez entrer une valeur sous la forme 'Min,Max' ou un seul nombre.")
            QTimer.singleShot(0, apply_error)
    
    @staticmethod
    def validate_qlineedit_with_range(
        qlineedit: QLineEdit, 
        default_value: str = "50,50",
        callback: Optional[Callable] = None
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Valide un QLineEdit contenant une plage numérique avec gestion d'erreurs (version compatible)"""
        text = qlineedit.text().strip()
        
        # Utilise la méthode validate_and_correct_qlineedit pour la validation
        ValidationUtils.validate_and_correct_qlineedit(qlineedit, default_value)
        
        # Récupère le texte corrigé
        corrected_text = qlineedit.text().strip()
        
        # Parse les valeurs
        valid, range_values = ValidationUtils.validate_numeric_range(corrected_text)
        
        if callback:
            callback(qlineedit, valid, range_values)
        
        return valid, range_values
    
    @staticmethod
    def validate_qlineedit_with_callback(
        qlineedit: QLineEdit,
        validator_type: str = "numeric_range",
        default_value: str = "50,50",
        on_valid: Optional[Callable] = None,
        on_invalid: Optional[Callable] = None
    ) -> None:
        """Valide un QLineEdit avec des callbacks pour les résultats"""
        def delayed_validation():
            if validator_type == "numeric_range":
                # Utilise la méthode de validation compatible
                ValidationUtils.validate_and_correct_qlineedit(qlineedit, default_value)
                
                # Récupère le texte final
                text = qlineedit.text().strip()
                valid, range_values = ValidationUtils.validate_numeric_range(text)
                
                if valid and on_valid:
                    on_valid(qlineedit, range_values)
                elif not valid and on_invalid:
                    on_invalid(qlineedit, range_values)
            
            elif validator_type == "email":
                is_valid, message = ValidationUtils.validate_qlineedit_text(
                    qlineedit, "email"
                )
                
                if is_valid:
                    old_style = qlineedit.styleSheet()
                    cleaned = ValidationUtils.remove_border_from_style(old_style)
                    qlineedit.setStyleSheet(cleaned)
                    qlineedit.setToolTip("")
                    if on_valid:
                        on_valid(qlineedit, qlineedit.text())
                else:
                    old_style = qlineedit.styleSheet()
                    new_style = ValidationUtils.inject_border_into_style(old_style)
                    qlineedit.setStyleSheet(new_style)
                    qlineedit.setToolTip(message)
                    if on_invalid:
                        on_invalid(qlineedit, message)
        
        QTimer.singleShot(0, delayed_validation)
    
    @staticmethod
    def validate_checkbox_linked_qlineedit(
        qlineedit: QLineEdit,
        checkbox_state: bool,
        default_text: str = "Google",
        min_length: int = 4
    ) -> Tuple[bool, str]:
        """Valide un QLineEdit lié à une checkbox"""
        if qlineedit is None:
            return False, "QLineEdit est None"
        
        text = qlineedit.text().strip()
        
        # Si la checkbox est cochée, le texte doit être valide
        if checkbox_state:
            if not text or len(text) < min_length or text.isdigit():
                qlineedit.setText(default_text)
                old_style = qlineedit.styleSheet()
                new_style = ValidationUtils.inject_border_into_style(
                    old_style,
                    "border: 2px solid #d32f2f;"  # Rouge pour erreur
                )
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip(f"Texte invalide. Doit avoir au moins {min_length} caractères non numériques.")
                return False, "Texte invalide, valeur par défaut appliquée"
            else:
                old_style = qlineedit.styleSheet()
                cleaned = ValidationUtils.remove_border_from_style(old_style)
                qlineedit.setStyleSheet(cleaned)
                qlineedit.setToolTip("")
                return True, "Texte valide"
        else:
            # Checkbox non cochée, validation différente
            is_valid, range_values = ValidationUtils.validate_numeric_range(text)
            
            if is_valid:
                old_style = qlineedit.styleSheet()
                cleaned = ValidationUtils.remove_border_from_style(old_style)
                qlineedit.setStyleSheet(cleaned)
                qlineedit.setToolTip("")
                return True, "Plage numérique valide"
            else:
                # Pour les champs non-checkbox, on accepte aussi du texte
                if text and len(text) >= min_length and not text.isdigit():
                    old_style = qlineedit.styleSheet()
                    cleaned = ValidationUtils.remove_border_from_style(old_style)
                    qlineedit.setStyleSheet(cleaned)
                    qlineedit.setToolTip("")
                    return True, "Texte valide"
                else:
                    qlineedit.setText(default_text)
                    old_style = qlineedit.styleSheet()
                    new_style = ValidationUtils.inject_border_into_style(
                        old_style,
                        "border: 2px solid #d32f2f;"  # Rouge pour erreur
                    )
                    qlineedit.setStyleSheet(new_style)
                    qlineedit.setToolTip(f"Doit être une plage numérique (ex: '1,10') ou du texte ({min_length}+ caractères)")
                    return False, "Format invalide"
    
    @staticmethod
    def batch_validate_qlineedits(
        qlineedits: List[QLineEdit],
        validator_type: str = "numeric_range",
        default_value: str = "50,50"
    ) -> Dict[str, Any]:
        """Valide plusieurs QLineEdit en une seule opération"""
        results = {
            "total": len(qlineedits),
            "valid": 0,
            "invalid": 0,
            "details": []
        }
        
        for idx, qlineedit in enumerate(qlineedits):
            if validator_type == "numeric_range":
                # Utilise la méthode de validation compatible
                ValidationUtils.validate_and_correct_qlineedit(qlineedit, default_value)
                
                # Récupère le texte final
                text = qlineedit.text().strip()
                is_valid, range_values = ValidationUtils.validate_numeric_range(text)
                
                result = {
                    "index": idx,
                    "valid": is_valid,
                    "value": text,
                    "range": range_values if is_valid else None,
                    "widget_id": qlineedit.objectName() or f"qlineedit_{idx}"
                }
            else:
                is_valid, message = ValidationUtils.validate_qlineedit_text(
                    qlineedit, validator_type
                )
                
                result = {
                    "index": idx,
                    "valid": is_valid,
                    "value": qlineedit.text(),
                    "message": message,
                    "widget_id": qlineedit.objectName() or f"qlineedit_{idx}"
                }
            
            results["details"].append(result)
            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
        
        return results
    
    @staticmethod
    def _apply_error_style(qlineedit: QLineEdit, tooltip: str = "") -> None:
        """Applique un style d'erreur à un QLineEdit (compatible)"""
        old_style = qlineedit.styleSheet()
        new_style = ValidationUtils.inject_border_into_style(old_style, "border: 2px solid #d32f2f;")
        qlineedit.setStyleSheet(new_style)
        qlineedit.setToolTip(tooltip)
    
    @staticmethod
    def _remove_error_style(qlineedit: QLineEdit) -> None:
        """Supprime le style d'erreur d'un QLineEdit (compatible)"""
        old_style = qlineedit.styleSheet()
        cleaned = ValidationUtils.remove_border_from_style(old_style)
        qlineedit.setStyleSheet(cleaned)
        qlineedit.setToolTip("")
    
    # === Méthodes pour la gestion des styles CSS ===
    
    @staticmethod
    def inject_border_into_style(old_style: str, border_line: str = "border: 2px solid #cc4c4c;") -> str:
        """Injecte une bordure dans le style CSS d'un QLineEdit (exactement comme la logique spécifiée)"""
        pattern = r"(QLineEdit\s*{[^}]*?)\s*}"
        match = re.search(pattern, old_style, re.DOTALL)

        if match:
            before_close = match.group(1)
            if "border" not in before_close:
                new_block = before_close + f"\n    {border_line}\n}}"
                result = re.sub(pattern, new_block, old_style, flags=re.DOTALL)
                return result
            else:
                return old_style
        else:
            appended = old_style + f"""
            QLineEdit {{
                {border_line}
            }}"""
            return appended
    
    @staticmethod
    def remove_border_from_style(style: str) -> str:
        """Supprime toutes les déclarations de bordure d'un style CSS (exactement comme la logique spécifiée)"""
        cleaned_style = re.sub(r'border\s*:\s*[^;]+;', '', style, flags=re.IGNORECASE)
        return cleaned_style.strip()
    
    # ==================== VALIDATION DE SCÉNARIO ====================
    
    @staticmethod
    def validate_scenario_actions(actions: List[Dict]) -> Tuple[bool, str]:
        """Valide la liste des actions d'un scénario"""
        if not actions:
            return False, "Le scénario ne contient aucune action"
        
        required_keys = ["process"]
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                return False, f"Action {i}: doit être un dictionnaire"
            
            if "process" not in action:
                return False, f"Action {i}: clé 'process' manquante"
            
            # Valider les sous-processus pour les boucles
            if action.get("process") == "loop":
                if "sub_process" not in action:
                    return False, f"Action {i}: boucle sans 'sub_process'"
                
                if not isinstance(action["sub_process"], list):
                    return False, f"Action {i}: 'sub_process' doit être une liste"
        
        return True, "Scénario valide"
    
    @staticmethod
    def validate_browser_selection(browser: str) -> Tuple[bool, str]:
        """Valide la sélection du navigateur"""
        if browser.lower() not in ValidationUtils.VALID_BROWSERS:
            return False, f"Navigateur non supporté: {browser}. Options: {', '.join(ValidationUtils.VALID_BROWSERS)}"
        
        return True, "Navigateur valide"
    
    @staticmethod
    def validate_browser_path(browser_name: str) -> Tuple[bool, Optional[str]]:
        """
        Valide et trouve le chemin d'exécution d'un navigateur
        """
        import shutil
        
        browser_executables = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "dragon": "dragon.exe",
            "icedragon": "icedragon.exe",
            "comodo": "comodo.exe"
        }
        
        if browser_name.lower() not in browser_executables:
            return False, f"Navigateur non supporté: {browser_name}"
        
        exe_name = browser_executables[browser_name.lower()]
        
        # Recherche dans les chemins courants
        path = shutil.which(exe_name)
        
        if path:
            return True, path
        
        return False, f"Exécutable {exe_name} non trouvé dans le PATH"
    
    @staticmethod
    def validate_isp_selection(isp: str) -> Tuple[bool, str]:
        """Valide la sélection du fournisseur de service"""
        if isp not in ValidationUtils.VALID_ISPS:
            return False, f"ISP non supporté: {isp}. Options: {', '.join(ValidationUtils.VALID_ISPS)}"
        
        return True, "ISP valide"
    
    # ==================== VALIDATION D'URL ====================
    
    @staticmethod
    def validate_url_format(url: str) -> bool:
        """Valide le format d'une URL"""
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except Exception:
            return False
    
    # ==================== FONCTIONS DE GÉNÉRATION ====================
    
    @staticmethod
    def generate_session_id(length: int = 5) -> str:
        """Génère un ID de session unique"""
        if length <= 0:
            raise ValueError("La longueur doit être un entier positif")
        return str(uuid.uuid4()).replace("-", "")[:length]
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Génère un mot de passe sécurisé"""
        if length < 12:
            raise ValueError("La longueur minimale recommandée est 12 caractères")
        
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*()-_+=<>?/|"
        
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special_chars),
        ]
        
        remaining_length = length - len(password)
        all_chars = lowercase + uppercase + digits + special_chars
        password += random.choices(all_chars, k=remaining_length)
        random.shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def generate_random_number(min_val: int, max_val: int) -> int:
        """Génère un nombre aléatoire dans une plage donnée"""
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        return random.randint(min_val, max_val)
    
    @staticmethod
    def generate_timestamp_filename(prefix: str = "", extension: str = "txt") -> str:
        """Génère un nom de fichier avec timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            return f"{prefix}_{timestamp}.{extension}"
        return f"{timestamp}.{extension}"
    
    # ==================== UTILITAIRES DE DÉBOGAGE ====================
    
    @staticmethod
    def log_validation_error(context: str, error: Exception) -> None:
        """Log une erreur de validation"""
        error_msg = f"[VALIDATION ERROR] {context}: {str(error)}"
        print(error_msg)
        traceback.print_exc()
    
    @staticmethod
    def create_validation_report(validations: List[Tuple[bool, str]]) -> Dict[str, Any]:
        """Crée un rapport de validation"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(validations),
            "passed": sum(1 for v in validations if v[0]),
            "failed": sum(1 for v in validations if not v[0]),
            "details": []
        }
        
        for i, (is_valid, message) in enumerate(validations, 1):
            report["details"].append({
                "check_number": i,
                "status": "PASS" if is_valid else "FAIL",
                "message": message
            })
        
        return report
    
    @staticmethod
    def create_comprehensive_validation_report(
        data_list: Optional[List[Dict]] = None,
        scenario_actions: Optional[List[Dict]] = None,
        browser: Optional[str] = None,
        isp: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Crée un rapport de validation complet pour tout le processus.
        """
        validations = []
        
        # Validation des données d'entrée
        if data_list:
            stats = ValidationUtils.get_input_statistics(data_list)
            validations.append((
                stats['total_entries'] > 0,
                f"Données d'entrée: {stats['total_entries']} entrées"
            ))
            validations.append((
                stats['validation_summary']['valid_emails'] > 0,
                f"Emails valides: {stats['validation_summary']['valid_emails']}"
            ))
            validations.append((
                stats['validation_summary']['valid_proxies'] > 0,
                f"Proxies valides: {stats['validation_summary']['valid_proxies']}"
            ))
        
        # Validation du scénario
        if scenario_actions:
            is_valid, message = ValidationUtils.validate_scenario_actions(scenario_actions)
            validations.append((is_valid, f"Scénario: {message}"))
        
        # Validation du navigateur
        if browser:
            is_valid, message = ValidationUtils.validate_browser_selection(browser)
            validations.append((is_valid, f"Navigateur: {message}"))
        
        # Validation de l'ISP
        if isp:
            is_valid, message = ValidationUtils.validate_isp_selection(isp)
            validations.append((is_valid, f"ISP: {message}"))
        
        # Validation des chemins de fichiers
        if file_paths:
            for path in file_paths:
                is_valid, message = ValidationUtils.validate_file_path(path)
                validations.append((is_valid, f"Fichier {os.path.basename(path)}: {message}"))
        
        # Créer le rapport
        report = ValidationUtils.create_validation_report(validations)
        
        # Ajouter des statistiques supplémentaires
        report["summary"] = {
            "overall_status": "PASS" if all(v[0] for v in validations) else "FAIL",
            "critical_checks_passed": sum(1 for v in validations if v[0]),
            "critical_checks_failed": sum(1 for v in validations if not v[0]),
            "timestamp_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return report
    
    @staticmethod
    def get_key_from_dict(data_dict: Dict, possible_keys: List[str]) -> str:
        for key in possible_keys:
            if key in data_dict:
                if not data_dict[key]:  
                    return key
                return data_dict[key]
        return possible_keys[0] if possible_keys else ""
    


# Instance globale pour une utilisation facile
ValidationUtils = ValidationUtils()