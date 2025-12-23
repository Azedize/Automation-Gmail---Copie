# utils/validation_utils.py
import os
import json
import re
import random
import string
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from PyQt6.QtWidgets import QLineEdit, QMessageBox, QApplication
from PyQt6.QtCore import QTimer
import traceback

class ValidationUtils:
    """Classe de validation unifiée pour toutes les validations et générations"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide le format d'un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """Valide un mot de passe selon des critères de sécurité"""
        if len(password) < min_length:
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
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
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
        except ValueError:
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
        text = text.strip()
        pattern = r'^\s*(\d+)(?:\s*,\s*(\d+))?\s*$'
        match = re.match(pattern, text)
        
        if not match:
            return False, None
        
        min_val = int(match.group(1))
        max_val = int(match.group(2)) if match.group(2) else min_val
        
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        
        return True, (min_val, max_val)
    
    @staticmethod
    def validate_input_format(input_data: str) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        Valide le format des données d'entrée utilisateur
        Format attendu: clés sur la première ligne, valeurs sur les lignes suivantes
        """
        lines = [line.strip() for line in input_data.split("\n") if line.strip()]
        
        if len(lines) < 2:
            return False, None, "Au moins une ligne d'en-tête et une ligne de données sont requises"
        
        # Valider les clés de l'en-tête
        keys = [key.strip() for key in lines[0].split(";")]
        
        # Vérifier les clés obligatoires
        mandatory_patterns = [
            ["email", "passwordEmail", "ipAddress", "port"],
            ["Email", "password_email", "ip_address", "port"]
        ]
        
        if not any(set(pat).issubset(keys) for pat in mandatory_patterns):
            missing_keys = []
            for pat in mandatory_patterns:
                missing = [k for k in pat if k not in keys]
                missing_keys.extend(missing)
            error_msg = "Clés obligatoires manquantes. Format requis : email; passwordEmail; ipAddress; port"
            return False, None, error_msg
        
        # Vérifier les clés invalides
        optional_patterns = [
            ["login", "password", "recoveryEmail", "newrecoveryEmail"],
            ["login", "password", "recovery_email", "New_recovery_email"]
        ]
        
        all_valid_keys = set()
        for pat in mandatory_patterns + optional_patterns:
            all_valid_keys.update(pat)
        
        invalid_keys = [k for k in keys if k not in all_valid_keys]
        if invalid_keys:
            error_msg = f"Clés invalides détectées: {', '.join(invalid_keys)}"
            return False, None, error_msg
        
        # Valider chaque ligne de données
        data_list = []
        for i, line in enumerate(lines[1:], start=2):
            values = [v.strip() for v in line.split(";")]
            
            if len(values) != len(keys):
                error_msg = f"Ligne {i}: nombre de valeurs ({len(values)}) ne correspond pas au nombre de clés ({len(keys)})"
                return False, None, error_msg
            
            # Créer le dictionnaire et valider les données essentielles
            entry = dict(zip(keys, values))
            
            # Valider l'email
            email_key = ValidationUtils._get_email_key(keys)
            if email_key in entry and not ValidationUtils.validate_email(entry[email_key]):
                error_msg = f"Ligne {i}: email invalide: {entry[email_key]}"
                return False, None, error_msg
            
            # Valider le proxy si présent
            ip_key = ValidationUtils._get_ip_key(keys)
            port_key = ValidationUtils._get_port_key(keys)
            
            if ip_key in entry and port_key in entry:
                valid_proxy, proxy_msg = ValidationUtils.validate_proxy_info(entry[ip_key], entry[port_key])
                if not valid_proxy:
                    error_msg = f"Ligne {i}: {proxy_msg}"
                    return False, None, error_msg
            
            data_list.append(entry)
        
        return True, data_list, "Format valide"
    
    @staticmethod
    def process_user_input(input_data: str, entered_number_text: str) -> Dict[str, Any]:
        """
        Traite et valide les données d'entrée utilisateur complètes
        Returns: {
            "success": bool,
            "data_list": Optional[List[Dict]],
            "entered_number": Optional[int],
            "error_title": str,
            "error_message": str,
            "error_type": str
        }
        """
        result = {
            "success": False,
            "data_list": None,
            "entered_number": None,
            "error_title": "",
            "error_message": "",
            "error_type": "critical"
        }
        
        # Validation de base
        if not input_data.strip():
            result.update({
                "error_title": "Error - Missing Data",
                "error_message": "Please enter the required information before proceeding.",
                "error_type": "critical"
            })
            return result
        
        if not entered_number_text.strip():
            result.update({
                "error_title": "Error - Missing Number",
                "error_message": "Please enter the number of operations to process.",
                "error_type": "critical"
            })
            return result
        
        # Validation du nombre
        if not entered_number_text.isdigit():
            result.update({
                "error_title": "Error - Invalid Input",
                "error_message": "Please enter a valid numerical value in the number field.",
                "error_type": "critical"
            })
            return result
        
        entered_number = int(entered_number_text)
        
        try:
            # Validation du format des données
            is_valid, data_list, error_msg = ValidationUtils.validate_input_format(input_data)
            
            if not is_valid:
                result.update({
                    "error_title": "Error - Invalid Format",
                    "error_message": error_msg,
                    "error_type": "critical"
                })
                return result
            
            # Validation de la plage
            if entered_number > len(data_list):
                result.update({
                    "error_title": "Error - Invalid Range",
                    "error_message": (
                        f"Please enter a value between 1 and {len(data_list)}.<br>"
                        f"Selected entries cannot exceed available items."
                    ),
                    "error_type": "critical"
                })
                return result
            
            # Validation détaillée de chaque entrée
            detailed_validation = ValidationUtils._validate_entries_detailed(data_list)
            if not detailed_validation["valid"]:
                result.update({
                    "error_title": "Error - Data Validation",
                    "error_message": detailed_validation["message"],
                    "error_type": "critical"
                })
                return result
            
            # Succès
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
                "error_message": (
                    f"Critical failure during data processing:<br>"
                    f"(Technical details: {str(e).capitalize()})"
                ),
                "error_type": "critical"
            })
        
        return result
    
    @staticmethod
    def _validate_entries_detailed(data_list: List[Dict]) -> Dict[str, Any]:
        """
        Validation détaillée de chaque entrée
        """
        errors = []
        
        for i, entry in enumerate(data_list, start=2):  # start=2 car la ligne 1 est l'en-tête
            line_errors = []
            
            # Identifier les clés
            keys = list(entry.keys())
            email_key = ValidationUtils._get_email_key(keys)
            ip_key = ValidationUtils._get_ip_key(keys)
            port_key = ValidationUtils._get_port_key(keys)
            
            # Valider l'email
            if email_key and email_key in entry:
                if entry[email_key] and not ValidationUtils.validate_email(entry[email_key]):
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
            display_errors = errors[:5]  # Limite à 5 erreurs
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
        """
        Génère des statistiques sur les données d'entrée
        """
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
            # Collecter les champs uniques
            stats["unique_fields"].update(entry.keys())
            
            # Valider les emails
            email_key = ValidationUtils._get_email_key(list(entry.keys()))
            if email_key and email_key in entry and entry[email_key]:
                if ValidationUtils.validate_email(entry[email_key]):
                    stats["validation_summary"]["valid_emails"] += 1
            
            # Valider les proxies
            ip_key = ValidationUtils._get_ip_key(list(entry.keys()))
            port_key = ValidationUtils._get_port_key(list(entry.keys()))
            if (ip_key and port_key and ip_key in entry and port_key in entry and 
                entry[ip_key] and entry[port_key]):
                is_valid, _ = ValidationUtils.validate_proxy_info(entry[ip_key], entry[port_key])
                if is_valid:
                    stats["validation_summary"]["valid_proxies"] += 1
            
            # Vérifier les entrées complètes (email + proxy)
            if (email_key and email_key in entry and entry[email_key] and
                ip_key and ip_key in entry and entry[ip_key] and
                port_key and port_key in entry and entry[port_key]):
                stats["validation_summary"]["complete_entries"] += 1
        
        stats["unique_fields"] = list(stats["unique_fields"])
        return stats
    
    @staticmethod
    def format_input_for_display(data_list: List[Dict], max_entries: int = 3) -> str:
        """
        Formate les données d'entrée pour l'affichage
        """
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
                # Formater chaque entrée de manière lisible
                entry_preview = []
                for key, value in list(entry.items())[:3]:  # Afficher les 3 premières clés
                    if value:
                        entry_preview.append(f"{key}: {value[:20]}{'...' if len(value) > 20 else ''}")
                
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
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = True) -> Tuple[bool, str]:
        """Valide un chemin de fichier"""
        if not path or not isinstance(path, str):
            return False, "Chemin de fichier invalide"
        
        if must_exist and not os.path.exists(path):
            return False, f"Le fichier n'existe pas: {path}"
        
        try:
            # Vérifier que le chemin est absolu ou relatif valide
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
            # Vérifier que c'est un dossier
            if must_exist and not os.path.isdir(path):
                return False, "Le chemin spécifié n'est pas un dossier"
            
            os.path.normpath(path)
            return True, "Chemin de dossier valide"
        except Exception:
            return False, "Chemin de dossier invalide"
    
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
    def validate_session_format(session_data: str) -> Tuple[bool, Optional[Dict]]:
        """Valide le format des données de session"""
        if not session_data or "::" not in session_data:
            return False, None
        
        parts = session_data.split("::", 2)
        if len(parts) != 3:
            return False, None
        
        username, date_str, entity = parts
        
        # Valider la date
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, None
        
        return True, {
            "username": username.strip(),
            "date": date_str.strip(),
            "entity": entity.strip()
        }
    
    # === Fonctions de génération ===
    
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
    
    # === Fonctions de validation d'interface ===
    
    @staticmethod
    def validate_qlineedit_text(qlineedit: QLineEdit, 
                                validator_type: str = "any",
                                min_length: int = 0,
                                max_length: int = 1000) -> Tuple[bool, str]:
        """Valide le texte d'un QLineEdit"""
        text = qlineedit.text().strip()
        
        if not text and min_length > 0:
            return False, "Ce champ est obligatoire"
        
        if len(text) < min_length:
            return False, f"Minimum {min_length} caractères requis"
        
        if len(text) > max_length:
            return False, f"Maximum {max_length} caractères autorisés"
        
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
    
    @staticmethod
    def parse_random_range(text: str, default: int = 0) -> int:
        """Parse une chaîne représentant un nombre ou une plage"""
        try:
            if ',' in text:
                min_val, max_val = map(int, text.split(','))
                return random.randint(min_val, max_val)
            return int(text)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_and_correct_qlineedit(qlineedit: QLineEdit, 
                                      default_value: str = "50,50") -> None:
        """Valide et corrige automatiquement un QLineEdit"""
        text = qlineedit.text().strip()
        
        if not text:
            qlineedit.setText(default_value)
            ValidationUtils._apply_error_style(qlineedit, "Valeur par défaut appliquée")
            return
        
        valid, range_values = ValidationUtils.validate_numeric_range(text)
        
        if not valid:
            qlineedit.setText(default_value)
            ValidationUtils._apply_error_style(qlineedit, "Format invalide. Utilisez: nombre ou min,max")
        elif range_values:
            min_val, max_val = range_values
            if min_val > max_val:
                qlineedit.setText(f"{max_val},{min_val}")
                ValidationUtils._apply_error_style(qlineedit, "Min > Max corrigé")
            else:
                ValidationUtils._remove_error_style(qlineedit)
    
    @staticmethod
    def _apply_error_style(qlineedit: QLineEdit, tooltip: str = "") -> None:
        """Applique un style d'erreur à un QLineEdit"""
        old_style = qlineedit.styleSheet()
        new_style = old_style + "border: 2px solid #d32f2f;"
        qlineedit.setStyleSheet(new_style)
        qlineedit.setToolTip(tooltip)
    
    @staticmethod
    def _remove_error_style(qlineedit: QLineEdit) -> None:
        """Supprime le style d'erreur d'un QLineEdit"""
        old_style = qlineedit.styleSheet()
        # Supprime les styles de bordure
        new_style = re.sub(r'border\s*:\s*[^;]+;', '', old_style)
        qlineedit.setStyleSheet(new_style.strip())
        qlineedit.setToolTip("")
    
    # === Validation de scénario ===
    
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
        valid_browsers = ["chrome", "firefox", "edge", "comodo", "icedragon"]
        
        if browser.lower() not in valid_browsers:
            return False, f"Navigateur non supporté: {browser}. Options: {', '.join(valid_browsers)}"
        
        return True, "Navigateur valide"
    
    @staticmethod
    def validate_isp_selection(isp: str) -> Tuple[bool, str]:
        """Valide la sélection du fournisseur de service"""
        valid_isps = ["Gmail", "Hotmail", "Yahoo", "Others"]
        
        if isp not in valid_isps:
            return False, f"ISP non supporté: {isp}. Options: {', '.join(valid_isps)}"
        
        return True, "ISP valide"
    
    # === Utilitaires de débogage ===
    
    @staticmethod
    def log_validation_error(context: str, error: Exception) -> None:
        """Log une erreur de validation"""
        error_msg = f"[VALIDATION ERROR] {context}: {str(error)}"
        print(error_msg)
        traceback.print_exc()
    
    @staticmethod
    def create_validation_report(validations: List[Tuple[bool, str]]) -> Dict:
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

# Instance globale pour une utilisation facile
ValidationUtils = ValidationUtils()