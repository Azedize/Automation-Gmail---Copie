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
    

    # ==================== VALIDATION JSON ET STRUCTURES ====================
    
    @staticmethod
    def validate_json_structure(json_data: Dict, required_keys: List[str]) -> Tuple[bool, str]:
        
        if not isinstance(json_data, dict):
            return False, "Data must be a JSON dictionary"
        
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            return False, f"Missing keys in JSON: {', '.join(missing_keys)}"
        
        return True, "Valid JSON structure"


    
    
    
    
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
    


    # ==================== FONCTIONS DE GÉNÉRATION ====================
    
    @staticmethod
    def generate_session_id(length: int = 5) -> str:
        if length <= 0:
            raise ValueError("La longueur doit être un entier positif")
        return str(uuid.uuid4()).replace("-", "")[:length]
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
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
    def get_key_from_dict(data_dict: Dict, possible_keys: List[str]) -> str:
        for key in possible_keys:
            if key in data_dict:
                if not data_dict[key]:  
                    return key
                return data_dict[key]
        return possible_keys[0] if possible_keys else ""
    


# Instance globale pour une utilisation facile
ValidationUtils = ValidationUtils()