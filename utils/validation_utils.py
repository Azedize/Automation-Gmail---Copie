# utils/validation_utils.py
import os
import json
import re
import random
import string
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
from urllib.parse import urlparse
from PyQt6.QtWidgets import QLineEdit, QMessageBox, QApplication
from PyQt6.QtCore import QTimer
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)



class ValidationUtils:

    
    # Patterns regex pré-compilés pour meilleure performance
    _PATTERN_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    _PATTERN_NUMERIC_RANGE = re.compile(r'^\s*(\d+)(?:\s*,\s*(\d+))?\s*$')
    
    
    
    
    @staticmethod
    def validate_email(email: str) -> bool:
        if not email or not isinstance(email, str):
            return False
        return ValidationUtils._PATTERN_EMAIL.match(email) is not None
    
   
    

    

    

    
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
    def process_user_input(input_data: str, entered_number_text: str) -> Dict[str, Any]:
        """
        Processes and validates user input data.

        Returns a structured dictionary with:
            - success (bool): True if validation passed, False otherwise
            - data_list (List[Dict[str, str]] | None): Parsed data rows
            - entered_number (int | None): Validated entered number
            - error_title (str): Short title of the error or success
            - error_message (str): Detailed message
            - error_type (str): 'critical' for errors, 'success' for success
        """
        print("🔵 [START] process_user_input")

        # Default result structure
        result: Dict[str, Any] = {
            "success": False,
            "data_list": None,
            "entered_number": None,
            "error_title": "",
            "error_message": "",
            "error_type": "critical"
        }

        # --------------------
        # 1️⃣ Basic input validation
        # --------------------
        if not input_data or not input_data.strip():
            result.update({
                "error_title": "No Data Provided",
                "error_message": "No input was detected. Please enter the required data to continue."
            })
            return result

        if not entered_number_text or not entered_number_text.strip():
            result.update({
                "error_title": "Missing Number",
                "error_message": "Please enter the number of rows you want to process."
            })
            return result

        if not entered_number_text.isdigit():
            result.update({
                "error_title": "Invalid Number",
                "error_message": "The number entered is not valid. Please enter a positive integer."
            })
            return result

        entered_number = int(entered_number_text)
        print(f"✅ Entered number is valid: {entered_number}")

        # --------------------
        # 2️⃣ Parse input lines
        # --------------------
        try:
            lines = [line.strip() for line in input_data.split("\n") if line.strip()]
            if len(lines) < 2:
                result.update({
                    "error_title": "No Data Rows",
                    "error_message": "The input contains a header but no data rows were found."
                })
                return result

            header = [k.strip() for k in lines[0].split(";")]
            data_lines = lines[1:]

            # --------------------
            # 3️⃣ Validate required keys
            # --------------------
            mandatory_patterns = [
                ["email", "passwordEmail", "ipAddress", "port"],
                ["Email", "password_email", "ip_address", "port"]
            ]

            optional_patterns = [
                ["login", "password", "recoveryEmail", "newrecoveryEmail"],
                ["login", "password", "recovery_email", "New_recovery_email"]
            ]

            all_valid_keys = set(k for pat in mandatory_patterns + optional_patterns for k in pat)

            if not any(set(pat).issubset(header) for pat in mandatory_patterns):
                result.update({
                    "error_title": "Required Columns Missing",
                    "error_message": (
                        "Some mandatory columns are missing in your input. "
                        "Please make sure the header matches one of the supported formats."
                    )
                })
                return result

            invalid_keys = [k for k in header if k not in all_valid_keys]
            if invalid_keys:
                result.update({
                    "error_title": "Unrecognized Columns",
                    "error_message": (
                        f"The following columns are not recognized: {', '.join(invalid_keys)}. "
                        "Please correct your header."
                    )
                })
                return result

            # --------------------
            # 4️⃣ Convert lines to dictionaries
            # --------------------
            data_list: List[Dict[str, str]] = []
            for index, line in enumerate(data_lines, start=1):
                values = [v.strip() for v in line.split(";")]
                if len(values) != len(header):
                    result.update({
                        "error_title": "Row Format Error",
                        "error_message": (
                            f"Row {index} does not match the expected format. "
                            "Please ensure all columns are filled correctly."
                        )
                    })
                    return result
                data_list.append(dict(zip(header, values)))

            # --------------------
            # 5️⃣ Validate entered number range
            # --------------------
            if entered_number > len(data_list):
                result.update({
                    "error_title": "Number Out of Range",
                    "error_message": (
                        f"The number entered exceeds the available rows ({len(data_list)}). "
                        "Please enter a valid number within the range."
                    )
                })
                return result

            # --------------------
            # 6️⃣ Success
            # --------------------
            result.update({
                "success": True,
                "data_list": data_list,
                "entered_number": entered_number,
                "error_title": "Success",
                "error_message": "Input data has been successfully validated.",
                "error_type": "success"
            })

        except Exception as e:
            result.update({
                "error_title": "Processing Error",
                "error_message": (
                    f"An unexpected error occurred while processing your data. "
                    "Please try again or contact support.\n\nError details: {str(e)}"
                )
            })

        print("🔵 [END] process_user_input")
        return result








    
  
    
    @staticmethod
    def _get_email_key(keys: List[str]) -> Optional[str]:
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
    def validate_path(path: str, must_exist: bool = True, is_file: bool = False) -> bool:
        print(f"[DEBUG] Checking path: {path}")

        if not path or not isinstance(path, str):
            print("[ERROR] Path is invalid or not a string")
            return False

        if must_exist and not os.path.exists(path):
            print(f"[ERROR] Path does not exist: {path}")
            return False

        try:
            if must_exist:
                if is_file and not os.path.isfile(path):
                    print(f"[ERROR] Path is not a file: {path}")
                    return False
                elif not is_file and not os.path.isdir(path):
                    print(f"[ERROR] Path is not a directory: {path}")
                    return False

            print(f"[DEBUG] Normalized path: {os.path.normpath(path)}")
            return True

        except Exception as e:
            print(f"[EXCEPTION] validate_path error: {e}")
            return False
        

    @staticmethod
    def ensure_path_exists(path: str, is_file: bool = True) -> bool:
        print(f"[DEBUG] Ensuring path exists: {path}")

        try:
            if is_file:
                directory = os.path.dirname(path)

                if directory and not os.path.exists(directory):
                    print(f"[DEBUG] Creating directory: {directory}")
                    os.makedirs(directory, exist_ok=True)

                if not os.path.exists(path):
                    print(f"[DEBUG] Creating file: {path}")
                    open(path, "a", encoding="utf-8").close()
                else:
                    print(f"[DEBUG] File already exists: {path}")

            else:
                if not os.path.exists(path):
                    print(f"[DEBUG] Creating directory: {path}")
                    os.makedirs(path, exist_ok=True)
                else:
                    print(f"[DEBUG] Directory already exists: {path}")

            return True

        except Exception as e:
            print(f"[EXCEPTION] ensure_path_exists error: {e}")
            return False

    @staticmethod
    def path_exists(path: str) -> bool:
        exists = os.path.exists(path)
        print(f"[DEBUG] Path exists check: {path} -> {exists}")
        return exists
    

    # ==================== VALIDATION JSON ET STRUCTURES ====================
    
    
    @staticmethod
    def validate_session_format(session_data: str) -> Tuple[bool, Optional[Dict]]:
        """Valide le format des données de session"""
        if not session_data or "::" not in session_data:
            return False, None
        
        parts = session_data.split("::")
        if len(parts) != 5:
            return False, None
        
        username, password ,date_str , entity ,Id_User= parts
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, None
        
        return True, {
            "username": username.strip(),
            "password": password.strip(),
            "date": date_str.strip(),
            "entity": entity.strip(),
            "Id_User":Id_User.strip()
        }
    
    # ==================== VALIDATION D'INTERFACE UTILISATEUR ====================

    @staticmethod
    def validate_qlineedit_text(input_data: Union[QLineEdit, str],   validator_type: str = "any",  min_length: int = 0, max_length: int = 1000) -> Tuple[bool, str]:

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
        try:
            if ',' in text:
                min_val, max_val = map(int, text.split(','))
                return random.randint(min_val, max_val)
            return int(text)
        except (ValueError, TypeError):
            return default




    @staticmethod
    def validate_and_correct_qlineedit(qlineedit: QLineEdit, default_value: str = "50,50") -> None:
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
    def validate_qlineedit_with_range(  qlineedit: QLineEdit,   default_value: str = "50,50",  callback: Optional[Callable] = None ) -> Tuple[bool, Optional[Tuple[int, int]]]:
 
        
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
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        return random.randint(min_val, max_val)
    




    @staticmethod
    def generate_timestamp_filename(prefix: str = "", extension: str = "txt") -> str:
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
    

    
    
    
    @staticmethod
    def get_email_from_log_file(file_name):
        file_name = os.path.basename(file_name)
        match = re.search(r"log_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z_([\w.+-]+@[\w.-]+\.[a-zA-Z]{2,6})\.txt", file_name)
        if match:
            #print(f"   - Email extrait : {match.group(1)}")
            email = match.group(1)
            return email
        else:
            #print(f"[Email Extraction] Aucun email trouvé dans {file_name}")
            return None


# Instance globale pour une utilisation facile
ValidationUtils = ValidationUtils()