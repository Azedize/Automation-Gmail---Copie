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
try:
    from config.settings import Settings
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)



class ValidationUtils:

    
    # Patterns regex pré-compilés pour meilleure performance
    _PATTERN_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    _PATTERN_NUMERIC_RANGE = re.compile(r'^\s*(\d+)(?:\s*,\s*(\d+))?\s*$')
    _PATTERN_IP = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    
    
    
    
    @staticmethod
    def validate_email(email: str) -> bool:
        if not email or not isinstance(email, str):
            return False
        return ValidationUtils._PATTERN_EMAIL.match(email) is not None
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        if not ip or not isinstance(ip, str):
            return False
        return ValidationUtils._PATTERN_IP.match(ip) is not None
    
   
    

    

    

    
    @staticmethod
    def validate_numeric_range(text: str) -> Tuple[bool, Optional[Tuple[int, int]]]:

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
                "error_title": "Input Validation Failed",
                "error_message": "No input data was detected. Please provide the required data to proceed with processing."
            })
            return result

        if not entered_number_text or not entered_number_text.strip():
            result.update({
                "error_title": "Input Validation Failed",
                "error_message": "The number of rows to process is missing. Please specify a valid number."
            })
            return result

        if not entered_number_text.isdigit():
            result.update({
                "error_title": "Input Validation Failed",
                "error_message": "The entered number is invalid. Please provide a positive integer value."
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
                    "error_title": "Data Structure Error",
                    "error_message": "The input data contains a header but no data rows were found. Please ensure your data includes both header and content rows."
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
                    "error_title": "Column Validation Failed",
                    "error_message": "Mandatory columns are missing from the input data. Please ensure the header includes all required fields in one of the supported formats."
                })
                return result

            invalid_keys = [k for k in header if k not in all_valid_keys]
            if invalid_keys:
                result.update({
                    "error_title": "Column Validation Failed",
                    "error_message": f"The following columns are not recognized: {', '.join(invalid_keys)}. Please verify and correct the header format."
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
                        "error_title": "Data Format Error",
                        "error_message": f"Row {index} does not match the expected column count. Please ensure all rows have the correct number of columns."
                    })
                    return result
                data_list.append(dict(zip(header, values)))

            # --------------------
            # 5️⃣ Validate entered number range
            # --------------------
            if entered_number > len(data_list):
                result.update({
                    "error_title": "Range Validation Failed",
                    "error_message": f"The specified number ({entered_number}) exceeds the available data rows ({len(data_list)}). Please enter a number within the valid range."
                })
                return result

            # --------------------
            # 6️⃣ Success
            # --------------------
            result.update({
                "success": True,
                "data_list": data_list,
                "entered_number": entered_number,
                "error_title": "Validation Successful",
                "error_message": "Input data has been successfully validated and is ready for processing.",
                "error_type": "success"
            })

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Unexpected error during data processing: {traceback.format_exc()}", "ERROR")
            result.update({
                "error_title": "Processing Error",
                "error_message": "An unexpected error occurred during data processing. Please verify your input and try again. If the issue persists, contact technical support."
            })

        print("🔵 [END] process_user_input")
        return result








    @staticmethod
    def safe_get(item: dict, key: str, default=None):
        return item.get(key, default) if isinstance(item, dict) else default

    
    
    
    @staticmethod
    def format_ip(raw_ip: str) -> Dict[str, Any]:
        """
        Safely format IP → IP#PORT if exists
        """
        try:
            if not raw_ip:
                Settings.WRITE_LOG_DEV_FILE("Empty IP provided", "ERROR")
                return {"valid": False, "data": None, "error": "Empty IP"}

            parts = raw_ip.split(';')

            if len(parts) >= 3:
                Settings.WRITE_LOG_DEV_FILE(f"IP with port detected: {raw_ip}", "INFO")
                formatted = parts[2].replace(':', '#')
            else:
                Settings.WRITE_LOG_DEV_FILE(f"IP without port detected: {raw_ip}", "INFO")
                formatted = raw_ip

            if '#' in formatted:
                Settings.WRITE_LOG_DEV_FILE(f"Validating IP with port: {formatted}", "INFO")
                ip_parts = formatted.split('#')

                if len(ip_parts) != 2:
                    Settings.WRITE_LOG_DEV_FILE(f"Malformed IP: {formatted}", "ERROR")
                    return {"valid": False, "data": None, "error": f"Malformed IP: {formatted}"}

                ip, port = ip_parts

                if not port.isdigit():
                    Settings.WRITE_LOG_DEV_FILE(f"Invalid port in IP: {formatted}", "ERROR")
                    return {"valid": False, "data": None, "error": f"Invalid port in IP: {formatted}"}
                
            Settings.WRITE_LOG_DEV_FILE(f"Formatted IP: {formatted}", "INFO")
            return {"valid": True, "data": formatted, "error": None}

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Unexpected error during IP formatting: {traceback.format_exc()}", "ERROR")
            Settings.WRITE_LOG_DEV_FILE(f"Error formatting IP: {e}\n{traceback.format_exc()}", "ERROR")
            return {"valid": False, "data": None, "error": str(e)}





    @staticmethod
    def process_ports(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes and validates port and IP address data from a list of accounts.
        
        Validates each account for:
        - Valid data structure
        - Presence of port
        - Authorized port values
        - Valid IP address format
        - Suspicious port patterns
        
        Returns a dictionary with validation results and any filtered data. tset
        """
        try:
            if not data_list:
                Settings.WRITE_LOG_DEV_FILE("No data provided for port processing", "WARNING")
                return {
                    "valid": True,
                    "data": {"filtered": [], "invalid": []},
                    "error": None,
                    "error_title": "No Data",
                    "error_message": "No account data was provided for port processing."
                }

            all_ports = []
            invalid_accounts = []
            suspicious_accounts = []

            for index, item in enumerate(data_list):
                if not isinstance(item, dict):
                    Settings.WRITE_LOG_DEV_FILE(f"Data integrity error at index {index}: Not a dictionary", "ERROR")
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Data integrity error",
                        "error_title": "Data Integrity Error",
                        "error_message": f"Item {index + 1} is not a valid data structure. Please ensure all entries are formatted as dictionaries."
                    }

                port = str(ValidationUtils.safe_get(item, "port", "")).strip()
                if not port:
                    Settings.WRITE_LOG_DEV_FILE(f"Missing port at index {index}", "ERROR")
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing port",
                        "error_title": "Port Validation Failed",
                        "error_message": f"Port information is missing for item {index + 1}. All accounts must include a valid port number."
                    }

                ip = str(ValidationUtils.safe_get(item, "ipAddress", "")).strip()
                if not ip:
                    Settings.WRITE_LOG_DEV_FILE(f"Missing IP address at index {index}", "ERROR")
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing IP",
                        "error_title": "IP Validation Failed",
                        "error_message": f"IP address is missing for item {index + 1}. All accounts must include a valid IP address."
                    }

                if not ValidationUtils.validate_ip(ip):
                    Settings.WRITE_LOG_DEV_FILE(f"Invalid IP address format at index {index}: {ip}", "ERROR")
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Invalid IP format",
                        "error_title": "IP Validation Failed",
                        "error_message": f"IP address '{ip}' for item {index + 1} is not in a valid IPv4 format. Use e.g. 192.168.1.1."
                    }

                all_ports.append(port)

                # ❌ Unauthorized ports
                if port not in Settings.AUTHORISED_PORTS:
                    invalid_accounts.append(item)

                # ⚠️ Suspicious ports
                if port in ['0000', '1111']:
                    suspicious_accounts.append(item)

            # ❌ Stop if invalid accounts exist
            if invalid_accounts:
                msg = f"Security and validation policy violation: {len(invalid_accounts)} account(s) contain invalid IP addresses or unauthorized port numbers. Please verify all configurations against approved settings."
                Settings.WRITE_LOG_DEV_FILE(f"Validation failed: {len(invalid_accounts)} invalid accounts", "ERROR")
                return {
                    "valid": False,
                    "data": invalid_accounts,
                    "error": msg,
                    "error_title": "Validation Failed",
                    "error_message": msg
                }

            Settings.WRITE_LOG_DEV_FILE(f"Suspicious ports count: {len(suspicious_accounts)}", "INFO")

            return {
                "valid": True,
                "data": {
                    "filtered": suspicious_accounts,
                    "invalid": []
                },
                "error": None,
                "error_title": "Port Processing Successful",
                "error_message": "All ports and IP addresses were validated successfully."
            }

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Unexpected error during data processing: {e}\n{traceback.format_exc()}", "ERROR")
            return {
                "valid": False,
                "data": None,
                "error": "Unexpected processing error",
                "error_title": "Processing Error",
                "error_message": "An unexpected system error occurred during port processing. Please contact technical support for assistance."
            }






        
    # =========================================================
    # 🔄 MERGE DATA (User-friendly messages)
    # =========================================================
    @staticmethod
    def merge_data(api_data: dict, data_list: list) -> Dict[str, Any]:
        try:
            final_list = []
            api_map = {k.split('#')[0]: v for k, v in api_data.items()}

            for item in data_list:
                raw_ip = ValidationUtils.safe_get(item, "ipAddress")
                result = ValidationUtils.format_ip(raw_ip)

                if not result["valid"]:
                    Settings.WRITE_LOG_DEV_FILE(f"Invalid IP format: {raw_ip}", "ERROR")
                    return {"valid": False, "data": None, "error": "There is an invalid IP address. Please check your data."}

                formatted_ip = result["data"]
                ip_only = formatted_ip.split('#')[0]

                api_info = api_map.get(ip_only)
                if not api_info:
                    Settings.WRITE_LOG_DEV_FILE(f"No API data for {ip_only}", "ERROR")
                    return {"valid": False, "data": None, "error": "Service data is missing for some IP addresses."}

                final_list.append({
                    "email": ValidationUtils.safe_get(item, "email"),
                    "password_email": ValidationUtils.safe_get(item, "passwordEmail"),
                    "ip_address": formatted_ip,
                    "port": api_info.get("port"),
                    "login": api_info.get("login"),
                    "password": api_info.get("pass"),
                    "recovery_email": ValidationUtils.safe_get(item, "recoveryEmail"),
                    "new_recovery_email": ValidationUtils.safe_get(item, "new_recovery_email"),
                })

            Settings.WRITE_LOG_DEV_FILE("Merged data successfully", "INFO")
            return {"valid": True, "data": final_list, "error": None}

        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(f"Error merging data: {e}\n{traceback.format_exc()}", "ERROR")
            return {"valid": False, "data": None, "error": "An error occurred while merging the data."}

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
            print(f"[EXCEPTION] validate_path error: {e}\n{traceback.format_exc()}")
            Settings.WRITE_LOG_DEV_FILE(f"Exception in validate_path: {e}\n{traceback.format_exc()}", "ERROR")
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
            Settings.WRITE_LOG_DEV_FILE(f"Exception in ensure_path_exists: {e}\n{traceback.format_exc()}", "ERROR")
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
        if len(parts) != 6:
            return False, None
        
        username, password ,date_str , entityOriginal , entityNew ,Id_User= parts
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, None
        
        return True, {
            "username": username.strip(),
            "password": password.strip(),
            "date": date_str.strip(),
            "p_entity_Origine": entityOriginal.strip(),
            "p_entity_Nouveau": entityNew.strip(),
            "Id_User":Id_User.strip()
        }
    
    # ==================== VALIDATION D'INTERFACE UTILISATEUR ====================


    @staticmethod
    def validate_qlineedit_text( input_data: Union[QLineEdit, str], validator_type: str = "any", min_length: int = 0,  max_length: int = 1000 ) -> Tuple[bool, str]:

        try:
            # Get the text
            if hasattr(input_data, "text"):
                text = input_data.text().strip()
            else:
                text = str(input_data).strip()
            
            # Basic validation
            if not text and min_length > 0:
                return False, "This field is required"
            
            if len(text) < min_length:
                return False, f"Minimum {min_length} characters required"
            
            if len(text) > max_length:
                return False, f"Maximum {max_length} characters allowed"
            
            # Type-specific validation
            if validator_type == "email":
                if not ValidationUtils.validate_email(text):
                    return False, "Invalid email format"
            
            elif validator_type == "numeric":
                if not text.isdigit():
                    return False, "Numeric value required"
            
            elif validator_type == "numeric_range":
                valid, _ = ValidationUtils.validate_numeric_range(text)
                if not valid:
                    return False, "Invalid format. Use: number or min,max"
            
            return True, "Valid text"
        
        except Exception as e:
            Settings.WRITE_LOG_DEV_FILE(
                f"Exception in validate_qlineedit_text: {e}\n{traceback.format_exc()}",
                "ERROR"
            )
            return False, f"Validation error: {str(e)}"





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