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
    from config import Settings
except ImportError as e:
    print(f"❌ Erreur d'importation  dans file {__file__}: {e}")
    sys.exit(1)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class ValidationUtils:
    # Regex centralisés dans Settings pour éviter les constantes dupliquées
    _PATTERN_EMAIL = re.compile(Settings.VALIDATION_CONFIG["EMAIL"])
    _PATTERN_NUMERIC_RANGE = re.compile(Settings.VALIDATION_CONFIG["NUMERIC_RANGE"])
    _PATTERN_IP = re.compile(Settings.VALIDATION_CONFIG["IP_ADDRESS"])
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
        # print("🔵 [START] process_user_input")
        Settings.write_log_event("user_input_validation_started", "INFO")

        # Default result structure
        result: Dict[str, Any] = {
            "success": False,
            "data_list": None,
            "entered_number": None,
            "error_title": "",
            "error_message": "",
            "error_type": "critical",
        }

        # --------------------
        # 1️⃣ Basic input validation
        # --------------------
        if not input_data or not input_data.strip():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": "No input data was detected. Please provide the required data to proceed with processing.",
                }
            )
            return result

        if not entered_number_text or not entered_number_text.strip():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": "The number of rows to process is missing. Please specify a valid number.",
                }
            )
            return result

        if not entered_number_text.isdigit():
            result.update(
                {
                    "error_title": "Input Validation Failed",
                    "error_message": "The entered number is invalid. Please provide a positive integer value.",
                }
            )
            return result

        entered_number = int(entered_number_text)
        # print(f"✅ Entered number is valid: {entered_number}")
        Settings.write_log_event("user_input_row_limit_validated", "INFO", requested_rows=entered_number)

        # --------------------
        # 2️⃣ Parse input lines
        # --------------------
        try:
            lines = [line.strip() for line in input_data.split("\n") if line.strip()]
            if len(lines) < 2:
                result.update(
                    {
                        "error_title": "Data Structure Error",
                        "error_message": "The input data contains a header but no data rows were found. Please ensure your data includes both header and content rows.",
                    }
                )
                return result

            raw_header = [k.strip() for k in lines[0].split(";")]
            header = [
                ValidationUtils._INPUT_HEADER_ALIASES.get(column, column)
                for column in raw_header
            ]
            data_lines = lines[1:]
            Settings.write_log_event("user_input_parsing_started", "INFO", column_count=len(header), row_count=len(data_lines))

            if len(set(header)) != len(header):
                duplicate_columns = sorted({column for column in header if header.count(column) > 1}  )
                result.update(
                    {
                        "error_title": "Column Validation Failed",
                        "error_message": (
                            "Duplicate columns were detected after normalization: "
                            f"{', '.join(duplicate_columns)}. Please keep only one column per field."
                        ),
                    }
                )
                return result

            # --------------------
            # 3️⃣ Validate required keys
            # --------------------
            mandatory_patterns = [["email", "passwordEmail", "ipAddress", "port"]]

            optional_patterns = [["login", "password", "recoveryEmail", "new_recovery_email"]]

            all_valid_keys = set(
                k for pat in mandatory_patterns + optional_patterns for k in pat
            )

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
                        "error_message": "Mandatory columns are missing from the input data. Please ensure the header includes all required fields in one of the supported formats.",
                    }
                )
                return result

            invalid_keys = [k for k in header if k not in all_valid_keys]
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
                        "error_message": f"The following columns are not recognized: {', '.join(invalid_keys)}. Please verify and correct the header format.",
                    }
                )
                return result

            # --------------------
            # 4️⃣ Convert lines to dictionaries
            # --------------------
            data_list: List[Dict[str, str]] = []
            for index, line in enumerate(data_lines, start=1):
                values = [v.strip() for v in line.split(";")]
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
                            "error_message": f"Row {index} does not match the expected column count. Please ensure all rows have the correct number of columns.",
                        }
                    )
                    return result
                data_list.append(dict(zip(header, values)))

            # --------------------
            # 5️⃣ Validate entered number range
            # --------------------
            if entered_number > len(data_list):
                result.update(
                    {
                        "error_title": "Range Validation Failed",
                        "error_message": f"The specified number ({entered_number}) exceeds the available data rows ({len(data_list)}). Please enter a number within the valid range.",
                    }
                )
                return result

            # --------------------
            # 6️⃣ Success
            # --------------------
            result.update(
                {
                    "success": True,
                    "data_list": data_list,
                    "entered_number": entered_number,
                    "error_title": "Validation Successful",
                    "error_message": "Input data has been successfully validated and is ready for processing.",
                    "error_type": "success",
                }
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Unexpected error during data processing: {traceback.format_exc()}",
                "ERROR",
            )
            result.update(
                {
                    "error_title": "Processing Error",
                    "error_message": "An unexpected error occurred during data processing. Please verify your input and try again. If the issue persists, contact technical support.",
                }
            )

        # print("🔵 [END] process_user_input")
        Settings.write_log_event(
            "user_input_validation_completed",
            "INFO",
            success=bool(result.get("success")),
            row_count=len(result.get("data_list") or []),
        )
        return result

    @staticmethod
    def generateUserInputData(window) -> Dict[str, Any]:
        """Parse, validate and prepare user input from the main UI window."""
        try:
            input_data = window.textEdit_3.toPlainText().strip()
            entered_number_text = window.textEdit_4.toPlainText().strip()

            Settings.write_log_event(
                "user_input_received",
                "INFO",
                input_length=len(input_data),
                input_line_count=len(input_data.splitlines()),
                has_requested_row_count=bool(entered_number_text),
            )

            validation = ValidationUtils.process_user_input(
                input_data, entered_number_text
            )
            if not validation["success"]:
                Settings.write_log_dev_file(
                    f"Validation failed: {validation['error_message']}", "ERROR"
                )
                return {"valid": False, "data": None, "entered_number": None, "error": f"{validation['error_title']}:{validation['error_message']}"}

            data_list = validation["data_list"]
            entered_number = validation["entered_number"]
            Settings.write_log_event(
                "user_input_validated",
                "INFO",
                row_count=len(data_list),
                requested_rows=entered_number,
            )

            ports_result = ValidationUtils.processPorts(data_list)
            if not ports_result["valid"]:
                Settings.write_log_dev_file( f"Ports processing failed: {ports_result['error_message']}", "ERROR" )
                Settings.write_log_event("port_processing_failed",  "ERROR", error_type=type(ports_result.get("error")).__name__, )
                return {"valid": False, "data": ports_result.get("data"), "entered_number": entered_number, "error": f"{ports_result['error_title']}:{ports_result['error_message']}"}

            filtered_accounts = ports_result["data"]["filtered"]
            Settings.write_log_dev_file(f"Ports processed - filtered count: {len(filtered_accounts)}", "INFO" )

            ip_result = ValidationUtils.collect_unique_proxy_addresses( filtered_accounts )
            if not ip_result["valid"]:
                Settings.write_log_dev_file( f"IP extraction failed: {ip_result['error']}", "ERROR")
                return {"valid": False, "data": None, "entered_number": entered_number, "error": f"{ip_result['error_title']}:{ip_result['error_message']}"}

            unique_ips = ip_result["data"]
            Settings.write_log_dev_file( f"Unique IPs extracted: {len(unique_ips)}", "INFO")
            Settings.write_log_dev_file("Unique IP values intentionally omitted from logs", "DEBUG"  )

            from core import SessionManager
            from api import API_MANAGER

            session_info = SessionManager.check_session()
            if not session_info["valid"]:
                Settings.write_log_dev_file(
                    f"Invalid session: {session_info.get('error', 'Unknown error')}",
                    "ERROR",
                )
                Settings.write_log_event(
                    "session_validation_failed",
                    "ERROR",
                    error_code=session_info.get("error", "unknown"),
                )
                return {"valid": False, "data": None, "entered_number": entered_number, "error": "Your session is invalid. Please log in again."}

            entity_used = session_info.get("p_entity_Nouveau", "UNKNOWN")
            Settings.write_log_dev_file(
                f"Session valide - Entity: {entity_used}", "INFO"
            )
            Settings.write_log_event(
                "session_validation_succeeded",
                "INFO",
                has_entity=bool(entity_used and entity_used != "UNKNOWN"),
            )

            api_result = API_MANAGER.fetchProxyConfiguration(unique_ips, entity_used)
            if not api_result["valid"]:
                api_error = api_result.get("error", "Unknown API error")
                Settings.write_log_dev_file(f"API call failed: {api_error}", "ERROR")
                Settings.write_log_event(
                    "proxy_configuration_failed",
                    "ERROR",
                    error_type=type(api_result.get("error")).__name__,
                )
                return {"valid": False, "data": None, "entered_number": entered_number, "error": api_error}

            Settings.write_log_dev_file(
                f"API call success - returned entries: {len(api_result['data']) if api_result.get('data') else 0}",
                "INFO",
            )

            merge_result = ValidationUtils.mergeValidatedData(
                api_result["data"], data_list
            )
            if not merge_result["valid"]:
                merge_error = merge_result["error"]
                Settings.write_log_event(
                    "validated_data_merge_failed",
                    "ERROR",
                    error=merge_error,
                )
                return {"valid": False, "data": None, "entered_number": entered_number, "error": merge_error}

            final_data = merge_result["data"]
            Settings.write_log_dev_file(
                f"Merge success - final records: {len(final_data)}", "INFO"
            )
            Settings.write_log_dev_file(
                "Final data sample intentionally omitted from logs",
                "DEBUG",
            )
            Settings.write_log_dev_file(
                "========== REQUEST COMPLETED SUCCESSFULLY ==========", "INFO"
            )

            return {"valid": True, "data": final_data, "entered_number": entered_number, "error": None}

        except Exception as e:
            Settings.write_log_dev_file(
                f"Unexpected error in generate_user_input_data: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )
            Settings.write_log_dev_file(
                "========== REQUEST FAILED WITH EXCEPTION ==========", "ERROR"
            )
            return {"valid": False, "data": None, "entered_number": None, "error": "An unexpected error occurred. Please try again later."}

    @staticmethod
    def getValueSafely(item: dict, key: str, default=None):
        return item.get(key, default) if isinstance(item, dict) else default

    @staticmethod
    def normalizeIpAddress(raw_ip: str) -> Dict[str, Any]:
        """
        Safely format IP → IP#PORT if exists
        """
        try:
            if not raw_ip:
                Settings.write_log_dev_file("Empty IP provided", "ERROR")
                return {"valid": False, "data": None, "error": "Empty IP"}

            parts = raw_ip.split(";")

            if len(parts) >= 3:
                Settings.write_log_event(
                    "proxy_address_with_port_detected", "INFO"
                )
                formatted = parts[2].replace(":", "#")
            else:
                Settings.write_log_event(
                    "proxy_address_without_port_detected", "INFO"
                )
                formatted = raw_ip

            if "#" in formatted:
                ip_parts = formatted.split("#")

                if len(ip_parts) != 2:
                    Settings.write_log_event(
                        "proxy_address_invalid", "ERROR", reason="malformed_format"
                    )
                    return {"valid": False, "data": None, "error": f"Malformed IP: {formatted}"}

                ip, port = ip_parts

                if not port.isdigit():
                    Settings.write_log_event(
                        "proxy_address_invalid", "ERROR", reason="invalid_port"
                    )
                    return {"valid": False, "data": None, "error": f"Invalid port in IP: {formatted}"}

            Settings.write_log_event("proxy_address_normalized", "INFO")
            return {"valid": True, "data": formatted, "error": None}

        except Exception as e:
            Settings.write_log_dev_file(
                f"Unexpected error during IP formatting: {traceback.format_exc()}",
                "ERROR",
            )
            Settings.write_log_dev_file(
                f"Error formatting IP: {e}\n{traceback.format_exc()}", "ERROR"
            )
            return {"valid": False, "data": None, "error": str(e)}

    @staticmethod
    def processPorts(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes and validates port and IP address data from a list of accounts.

        Validates each account for:
        - Valid data structure
        - Presence of port
        - Authorized port values
        - Valid IP address format
        - Suspicious port patterns

        Returns a dictionary with validation results and any filtered data.
        """
        try:
            if not data_list:
                Settings.write_log_dev_file(
                    "No data provided for port processing", "WARNING"
                )
                return {
                    "valid": True,
                    "data": {"filtered": [], "invalid": [], "suspicious": []},
                    "error": None,
                    "error_title": "No Data",
                    "error_message": "No account data was provided for port processing.",
                }

            valid_accounts = []
            invalid_accounts = []
            suspicious_accounts = []

            for index, item in enumerate(data_list):
                if not isinstance(item, dict):
                    Settings.write_log_dev_file(
                        f"Data integrity error at index {index}: Not a dictionary",
                        "ERROR",
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Data integrity error",
                        "error_title": "Data Integrity Error",
                        "error_message": f"Item {index + 1} is not a valid data structure. Please ensure all entries are formatted as dictionaries.",
                    }

                port = str(ValidationUtils.getValueSafely(item, "port", "")).strip()
                if not port:
                    Settings.write_log_dev_file(
                        f"Missing port at index {index}", "ERROR"
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing port",
                        "error_title": "Port Validation Failed",
                        "error_message": f"Port information is missing for item {index + 1}. All accounts must include a valid port number.",
                    }

                ip = str(ValidationUtils.getValueSafely(item, "ipAddress", "")).strip()
                if not ip:
                    Settings.write_log_dev_file(
                        f"Missing IP address at index {index}", "ERROR"
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Missing IP",
                        "error_title": "IP Validation Failed",
                        "error_message": f"IP address is missing for item {index + 1}. All accounts must include a valid IP address.",
                    }

                if not ValidationUtils.validate_ip(ip):
                    Settings.write_log_dev_file(
                        f"Invalid IP address format at index {index}: {ip}", "ERROR"
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Invalid IP format",
                        "error_title": "IP Validation Failed",
                        "error_message": f"IP address '{ip}' for item {index + 1} is not in a valid IPv4 format. Use e.g. 192.168.1.1.",
                    }

                # ❌ Ports outside the two-port proxy validation flow
                if port not in Settings.PROXY_VALIDATION_PORTS:
                    invalid_accounts.append(item)
                    continue

                valid_accounts.append(item)

                # ⚠️ Suspicious ports
                if port in Settings.PROXY_VALIDATION_PORTS:
                    suspicious_accounts.append(item)

            # ❌ Stop if invalid accounts exist
            if invalid_accounts:
                msg = (
                    f"Port validation failed for {len(invalid_accounts)} account(s). "
                    "Only ports 0000 and 1111 are authorized for this operation. "
                    "Please review the port value and try again."
                )
                Settings.write_log_dev_file(
                    f"Validation failed: {len(invalid_accounts)} invalid accounts",
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

            Settings.write_log_dev_file(
                f"Suspicious ports count: {len(suspicious_accounts)}", "INFO"
            )

            return {
                "valid": True,
                "data": {
                    "filtered": valid_accounts,
                    "invalid": [],
                    "suspicious": suspicious_accounts,
                },
                "error": None,
                "error_title": "Port Processing Successful",
                "error_message": "All ports and IP addresses were validated successfully.",
            }

        except Exception as e:
            Settings.write_log_dev_file(
                f"Unexpected error during data processing: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return {
                "valid": False,
                "data": None,
                "error": "Unexpected processing error",
                "error_title": "Processing Error",
                "error_message": "An unexpected system error occurred during port processing. Please contact technical support for assistance.",
            }

    # =========================================================
    # 🔄 MERGE DATA (User-friendly messages)
    # =========================================================
    @staticmethod
    def mergeValidatedData(api_data: dict, data_list: list) -> Dict[str, Any]:
        try:
            final_list = []
            api_map = {k.split("#")[0]: v for k, v in api_data.items()}

            for item in data_list:
                raw_ip = ValidationUtils.getValueSafely(item, "ipAddress")
                result = ValidationUtils.normalizeIpAddress(raw_ip)

                if not result["valid"]:
                    Settings.write_log_event(
                        "validated_data_merge_failed",
                        "ERROR",
                        reason="invalid_proxy_address",
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "There is an invalid IP address. Please check your data.",
                    }

                formatted_ip = result["data"]
                ip_only = formatted_ip.split("#")[0]

                api_info = api_map.get(ip_only)
                if not api_info:
                    Settings.write_log_event(
                        "validated_data_merge_failed",
                        "ERROR",
                        reason="proxy_configuration_missing",
                    )
                    return {
                        "valid": False,
                        "data": None,
                        "error": "Service data is missing for some IP addresses.",
                    }

                final_list.append(
                    {
                        "email": ValidationUtils.getValueSafely(item, "email"),
                        "password_email": ValidationUtils.getValueSafely(
                            item, "passwordEmail"
                        ),
                        "ip_address": formatted_ip,
                        "port": api_info.get("port"),
                        "login": api_info.get("login"),
                        "password": api_info.get("pass"),
                        "recovery_email": ValidationUtils.getValueSafely(
                            item, "recoveryEmail"
                        ),
                        "new_recovery_email": ValidationUtils.getValueSafely(
                            item, "new_recovery_email"
                        ),
                    }
                )

            Settings.write_log_event(
                "validated_data_merge_completed",
                "INFO",
                input_row_count=len(data_list),
                output_row_count=len(final_list),
            )
            return {"valid": True, "data": final_list, "error": None}

        except Exception as e:
            Settings.write_log_dev_file(
                f"Error merging data: {e}\n{traceback.format_exc()}", "ERROR"
            )
            return {
                "valid": False,
                "data": None,
                "error": "An error occurred while merging the data.",
            }

    # ==================== VALIDATION DE FICHIERS ET CHEMINS ====================

    @staticmethod
    def validate_path(path: str, must_exist: bool = True, is_file: bool = False) -> bool:
        # print(f"[DEBUG] Checking path: {path}")
        Settings.write_log_dev_file(f"Validating path: {path}", "INFO")

        if not path or not isinstance(path, str):
            # print("[ERROR] Path is invalid or not a string")
            Settings.write_log_dev_file("Path is invalid or not a string", "ERROR")
            return False

        if must_exist and not os.path.exists(path):
            # print(f"[ERROR] Path does not exist: {path}")
            Settings.write_log_dev_file(f"Path does not exist: {path}", "ERROR")
            return False

        try:
            if must_exist:
                if is_file and not os.path.isfile(path):
                    # print(f"[ERROR] Path is not a file: {path}")
                    Settings.write_log_dev_file(f"Path is not a file: {path}", "ERROR")
                    return False
                elif not is_file and not os.path.isdir(path):
                    # print(f"[ERROR] Path is not a directory: {path}")
                    Settings.write_log_dev_file(
                        f"Path is not a directory: {path}", "ERROR"
                    )
                    return False

            # print(f"[DEBUG] Normalized path: {os.path.normpath(path)}")
            Settings.write_log_dev_file(
                f"Normalized path: {os.path.normpath(path)}", "INFO"
            )
            return True

        except Exception as e:
            # print(f"[EXCEPTION] validate_path error: {e}\n{traceback.format_exc()}")
            Settings.write_log_dev_file(
                f"Exception in validate_path: {e}\n{traceback.format_exc()}", "ERROR"
            )
            return False

    @staticmethod
    def ensurePathExists(path: str, is_file: bool = True) -> bool:
        # print(f"[DEBUG] Ensuring path exists: {path}")
        Settings.write_log_dev_file(f"Ensuring path exists: {path}", "INFO")

        try:
            if is_file:
                directory = os.path.dirname(path)

                if directory and not os.path.exists(directory):
                    # print(f"[DEBUG] Creating directory: {directory}")
                    Settings.write_log_dev_file(
                        f"Creating directory: {directory}", "INFO"
                    )
                    os.makedirs(directory, exist_ok=True)

                if not os.path.exists(path):
                    # print(f"[DEBUG] Creating file: {path}")
                    Settings.write_log_dev_file(f"Creating file: {path}", "INFO")
                    open(path, "a", encoding="utf-8").close()
                else:
                    # print(f"[DEBUG] File already exists: {path}")
                    Settings.write_log_dev_file(f"File already exists: {path}", "INFO")

            else:
                if not os.path.exists(path):
                    # print(f"[DEBUG] Creating directory: {path}")
                    Settings.write_log_dev_file(f"Creating directory: {path}", "INFO")
                    os.makedirs(path, exist_ok=True)
                else:
                    # print(f"[DEBUG] Directory already exists: {path}")
                    Settings.write_log_dev_file(
                        f"Directory already exists: {path}", "INFO"
                    )

            return True

        except Exception as e:
            Settings.write_log_dev_file(
                f"Exception in ensure_path_exists: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            # print(f"[EXCEPTION] ensure_path_exists error: {e}")
            return False

    @staticmethod
    def pathExists(path: str) -> bool:
        exists = os.path.exists(path)
        # print(f"[DEBUG] Path exists check: {path} -> {exists}")
        Settings.write_log_dev_file(f"Path exists check: {path} -> {exists}", "INFO")
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

        username, password, date_str, entityOriginal, entityNew, Id_User = parts

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
            "Id_User": Id_User.strip(),
        }

    # ==================== VALIDATION D'INTERFACE UTILISATEUR ====================

    @staticmethod
    def validate_qlineedit_text(input_data: Union[QLineEdit, str], validator_type: str = "any", min_length: int = 0, max_length: int = 1000) -> Tuple[bool, str]:

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
            Settings.write_log_dev_file(
                f"Exception in validate_qlineedit_text: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def parse_random_range(text: str, default: int = 0) -> int:
        try:
            if "," in text:
                min_val, max_val = map(int, text.split(","))
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
                    qlineedit.setToolTip(
                        "La valeur Min est supérieure à Max. Correction appliquée."
                    )

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
                qlineedit.setToolTip(
                    "Veuillez entrer une valeur sous la forme 'Min,Max' ou un seul nombre."
                )

            QTimer.singleShot(0, apply_error)

    @staticmethod
    def validate_qlineedit_with_range(qlineedit: QLineEdit, default_value: str = "50,50", callback: Optional[Callable] = None) -> Tuple[bool, Optional[Tuple[int, int]]]:

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
            appended = (
                old_style
                + f"""
            QLineEdit {{
                {border_line}
            }}"""
            )
            return appended

    @staticmethod
    def remove_border_from_style(style: str) -> str:
        cleaned_style = re.sub(r"border\s*:\s*[^;]+;", "", style, flags=re.IGNORECASE)
        return cleaned_style.strip()

    # ==================== FONCTIONS DE GÉNÉRATION ====================

    @staticmethod
    def generateSessionId(length: int = 5) -> str:
        if length <= 0:
            raise ValueError("La longueur doit être un entier positif")
        return str(uuid.uuid4()).replace("-", "")[:length]

    @staticmethod
    def generateSecurePassword(length: int = 12) -> str:
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

        return "".join(password)

    # ==================== UTILITAIRES DE DÉBOGAGE ====================

    @staticmethod
    def getValueFromDictionary(data_dict: Dict, possible_keys: List[str]) -> str:
        for key in possible_keys:
            if key in data_dict:
                if not data_dict[key]:
                    return key
                return data_dict[key]
        return possible_keys[0] if possible_keys else ""

    @staticmethod
    def extractEmailFromLogFile(file_name):
        file_name = os.path.basename(file_name)
        match = re.search(
            r"log_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z_([\w.+-]+@[\w.-]+\.[a-zA-Z]{2,6})\.txt",
            file_name,
        )
        if match:
            # print(f"   - Email extrait : {match.group(1)}")
            email = match.group(1)
            return email
        else:
            # print(f"[Email Extraction] Aucun email trouvé dans {file_name}")
            return None

    @staticmethod
    def collect_unique_proxy_addresses(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            if not data_list:
                Settings.write_log_dev_file(
                    "No account data provided for proxy address collection", "WARNING"
                )
                return {
                    "valid": True,
                    "data": set(),
                    "error": None,
                    "error_title": "No Data",
                    "error_message": "No account entries were provided for proxy address collection.",
                }

            unique_ips: set = set()

            for index, item in enumerate(data_list):
                ip = ValidationUtils.getValueSafely(item, "ipAddress")

                if ip:
                    unique_ips.add(str(ip))
                else:
                    Settings.write_log_dev_file(
                        f"Missing ipAddress at index {index}", "WARNING"
                    )

            Settings.write_log_dev_file(
                f"Proxy addresses collected - total: {len(unique_ips)}", "INFO"
            )

            return {
                "valid": True,
                "data": unique_ips,
                "error": None,
                "error_title": "Proxy Address Collection Successful",
                "error_message": f"Collected {len(unique_ips)} unique proxy address(es) from provided account data.",
            }

        except Exception as e:
            Settings.write_log_dev_file(
                f"Error collecting unique proxy addresses: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return {
                "valid": False,
                "data": None,
                "error": str(e),
                "error_title": "Proxy Address Collection Error",
                "error_message": "An error occurred while collecting proxy addresses. Please verify data format and retry.",
            }


# Instance globale pour une utilisation facile
ValidationUtils = ValidationUtils()
