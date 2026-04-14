# ==========================================================
# checkV3_IMPROVED.py
# ==========================================================
# IMPROVED VERSION WITH COMPREHENSIVE DOCUMENTATION
# AND PROPER ERROR HANDLING
# ==========================================================

import os
import sys
import shutil
import zipfile
import importlib
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TypeVar, Generic, Dict, Any, Tuple, Union
import tempfile
import io
import datetime
import traceback

# ==========================================================
# 🔹 STANDARDIZED RESULT & ERROR HANDLING
# ==========================================================

class BootstrapErrorCode(Enum):
    """
    Standardized error codes for checkV3 operations.
    Format: PREFIX_NNN (e.g., ENC_001, UPD_002, NET_003)
    """
    # Encryption Errors
    ENCRYPTION_FAILED = "ENC_001"
    ENCRYPTION_INVALID_KEY = "ENC_002"
    ENCRYPTION_INVALID_INPUT = "ENC_003"
    
    # Version/Update Errors
    VERSION_FILE_NOT_FOUND = "UPD_001"
    VERSION_FILE_CORRUPTED = "UPD_002"
    VERSION_FILE_READ_FAILED = "UPD_003"
    UPDATE_DOWNLOAD_FAILED = "UPD_004"
    UPDATE_EXTRACT_FAILED = "UPD_005"
    UPDATE_ALREADY_LATEST = "UPD_006"
    
    # Network Errors
    NETWORK_CONNECTION_FAILED = "NET_001"
    NETWORK_TIMEOUT = "NET_002"
    NETWORK_INVALID_RESPONSE = "NET_003"
    
    # Dependency Errors
    DEPENDENCY_INSTALLATION_FAILED = "DEP_001"
    DEPENDENCY_IMPORT_FAILED = "DEP_002"
    DEPENDENCY_POSTINSTALL_FAILED = "DEP_003"
    PYWIN32_NOT_FOUND = "DEP_004"
    
    # Environment Errors
    PYTHONW_NOT_FOUND = "ENV_001"
    PYTHON_EXECUTABLE_INVALID = "ENV_002"
    
    # Logging Errors
    LOG_WRITE_FAILED = "LOG_001"
    LOG_PATH_INVALID = "LOG_002"
    
    # General Errors
    UNKNOWN_ERROR = "GEN_001"
    OPERATION_TIMEOUT = "GEN_002"

T = TypeVar('T')

@dataclass
class BootstrapResult(Generic[T]):
    success: bool
    data: Optional[T] = None
    error_code: Optional[BootstrapErrorCode] = None
    error_msg: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __bool__(self) -> bool:
        return self.success
    
    def __str__(self) -> str:
        if self.success:
            return f"BootstrapResult(success={self.data})"
        return f"BootstrapResult(error={self.error_code}: {self.error_msg})"
    
    @classmethod
    def ok(cls, data: T, details: Dict[str, Any] = None) -> "BootstrapResult[T]":
        return cls(success=True, data=data, details=details or {})
    
    @classmethod
    def error( cls, error_code: BootstrapErrorCode,  error_msg: str, details: Dict[str, Any] = None) -> "BootstrapResult[T]":
        return cls( success=False,error_code=error_code, error_msg=error_msg,  details=details or {} )





# ==========================================================
# 🔹 GLOBAL CONFIGURATION
# ==========================================================

TOOLS_DIR = Path("Tools")
EXTENSIONS_DIR_TEMPLETE = TOOLS_DIR / "extensions Templete"
LOG_DEV_FILE = os.path.abspath(os.path.join("Log/LogDev/my_project.log"))

# AES-256 Key (32 bytes)
KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
KEY = bytes.fromhex(KEY_HEX)

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}



ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SCRIPT_DIR = Path(__file__).resolve().parent


# ==========================================================
# 🔹 LOGGING SYSTEM
# ==========================================================

def WRITE_LOG_DEV_FILE( message: str, level: str = "INFO", error_code: Optional[BootstrapErrorCode] = None) -> BootstrapResult[bool]:
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build log line with error code if present
        if error_code:
            log_line = f"[{timestamp}] [{level}] [{error_code.value}] {message}\n"
        else:
            log_line = f"[{timestamp}] [{level}] {message}\n"
        
        # Validate parameters
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in valid_levels:
            return BootstrapResult.error( BootstrapErrorCode.LOG_WRITE_FAILED , f"Invalid log level: {level}. Must be one of {valid_levels}" )
        
        if not isinstance(message, str):
            return BootstrapResult.error(  BootstrapErrorCode.LOG_WRITE_FAILED,  f"Message must be string, got {type(message).__name__}")
        
        # Ensure log directory exists
        log_path = Path(LOG_DEV_FILE)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            return BootstrapResult.error( BootstrapErrorCode.LOG_PATH_INVALID,  f"Permission denied creating log directory: {str(e)}", details={"log_dir": str(log_path.parent)})
        except Exception as e:
            return BootstrapResult.error(
                BootstrapErrorCode.LOG_PATH_INVALID,  f"Error creating log directory: {str(e)}" )
        
        # Write log line
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
                f.flush()  # Ensure written to disk
            return BootstrapResult.ok(True)
        
        except IOError as e:
            return BootstrapResult.error(
                BootstrapErrorCode.LOG_WRITE_FAILED,
                f"IO error writing to log: {str(e)}"
            )
        except Exception as e:
            return BootstrapResult.error(
                BootstrapErrorCode.LOG_WRITE_FAILED,
                f"Unexpected error writing to log: {str(e)}"
            )
    
    except Exception as e:
        # Last-resort error handler (shouldn't be reached)
        return BootstrapResult.error(
            BootstrapErrorCode.LOG_WRITE_FAILED,
            f"Unknown error in WRITE_LOG_DEV_FILE: {str(e)}"
        )


def clear_log() -> BootstrapResult[bool]:
    try:
        log_path = Path(LOG_DEV_FILE)
        
        if not log_path.exists():
            # No-op if file doesn't exist (still success)
            return BootstrapResult.ok(True, {"note": "Log file did not exist"})
        
        try:
            # Truncate file to zero size
            with open(log_path, "w", encoding="utf-8") as f:
                pass
            
            return BootstrapResult.ok(True, {"path": str(log_path)})
        
        except PermissionError as e:
            return BootstrapResult.error(
                BootstrapErrorCode.LOG_WRITE_FAILED,
                f"Permission denied clearing log file: {str(e)}",
                details={"log_path": str(log_path)}
            )
        except Exception as e:
            return BootstrapResult.error(
                BootstrapErrorCode.LOG_WRITE_FAILED,
                f"Error clearing log file: {str(e)}"
            )
    
    except Exception as e:
        return BootstrapResult.error(
            BootstrapErrorCode.UNKNOWN_ERROR,
            f"Unexpected error in clear_log: {str(e)}"
        )


# ==========================================================
# 🔹 ENCRYPTION UTILITIES
# ==========================================================

def generate_encrypted_key() -> BootstrapResult[Tuple[str, str]]:
    try:
        from cryptography.fernet import Fernet
        
        # Generate random key
        secret_key = Fernet.generate_key()
        fernet = Fernet(secret_key)
        
        # Encrypt marker message
        encrypted_message = fernet.encrypt(b"authorized")
        
        return BootstrapResult.ok(
            (encrypted_message.decode(), secret_key.decode()),
            {"note": "Key pair generated successfully"}
        )
    
    except ImportError as e:
        WRITE_LOG_DEV_FILE(
            f"cryptography library not available: {str(e)}",
            "ERROR",
            BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED
        )
        return BootstrapResult.error(
            BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED,
            "cryptography library required but not installed"
        )
    except Exception as e:
        WRITE_LOG_DEV_FILE(
            f"Error generating encrypted key: {str(e)}",
            "ERROR",
            BootstrapErrorCode.ENCRYPTION_FAILED
        )
        return BootstrapResult.error(
            BootstrapErrorCode.ENCRYPTION_FAILED,
            f"Failed to generate encrypted key: {str(e)}"
        )


def encrypt_message( plaintext: str, key_bytes: bytes) -> BootstrapResult[str]:
    try:
        import os
        import base64
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        
        # ===== INPUT VALIDATION =====
        
        # Validate plaintext
        if not isinstance(plaintext, str):
            return BootstrapResult.error(
                BootstrapErrorCode.ENCRYPTION_INVALID_INPUT,
                f"plaintext must be string, got {type(plaintext).__name__}"
            )
        
        if not plaintext:
            return BootstrapResult.error(
                BootstrapErrorCode.ENCRYPTION_INVALID_INPUT,
                "plaintext cannot be empty"
            )
        
        if len(plaintext) > 1_000_000:  # 1MB limit
            return BootstrapResult.error(
                BootstrapErrorCode.ENCRYPTION_INVALID_INPUT,
                f"plaintext too large ({len(plaintext)} bytes, max 1MB)"
            )
        
        # Validate key
        if not isinstance(key_bytes, bytes):
            return BootstrapResult.error(
                BootstrapErrorCode.ENCRYPTION_INVALID_KEY,
                f"key_bytes must be bytes, got {type(key_bytes).__name__}"
            )
        
        if len(key_bytes) != 32:
            return BootstrapResult.error(
                BootstrapErrorCode.ENCRYPTION_INVALID_KEY,
                f"AES-256 requires 32-byte key, got {len(key_bytes)} bytes"
            )
        
        # ===== ENCRYPTION =====
        
        # Pad plaintext to AES block size (128-bit)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
        
        # Generate random IV (16 bytes)
        iv = os.urandom(16)
        
        # Create cipher and encrypt
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        
        # Encode as base64 (IV + ciphertext)
        encrypted = base64.b64encode(iv + ciphertext).decode("utf-8")
        
        return BootstrapResult.ok(
            encrypted,
            {
                "plaintext_len": len(plaintext),
                "ciphertext_len": len(encrypted),
                "key_size_bits": len(key_bytes) * 8,
                "cipher_mode": "AES-256-CBC"
            }
        )
    
    except ImportError as e:
        WRITE_LOG_DEV_FILE(
            f"cryptography library not available: {str(e)}",
            "ERROR",
            BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED
        )
        return BootstrapResult.error(
            BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED,
            "cryptography library required for encryption"
        )
    except Exception as e:
        WRITE_LOG_DEV_FILE(
            f"AES-256-CBC encryption failed: {traceback.format_exc()}",
            "ERROR",
            BootstrapErrorCode.ENCRYPTION_FAILED
        )
        return BootstrapResult.error(
            BootstrapErrorCode.ENCRYPTION_FAILED,
            f"Encryption failed: {str(e)}"
        )


# ==========================================================
# 🔹 ENVIRONMENT DETECTION
# ==========================================================

def find_pythonw() -> BootstrapResult[Path]:
    try:
        # Try current Python's directory first
        base_dir = os.path.dirname(sys.executable)
        candidate = Path(base_dir) / "pythonw.exe"
        
        if candidate.is_file():
            WRITE_LOG_DEV_FILE(
                f"Found pythonw.exe at: {candidate}",
                "INFO"
            )
            return BootstrapResult.ok(
                candidate,
                {"method": "same_directory_as_python"}
            )
        
        # Search PATH environment variable
        path_env = os.environ.get("PATH", "")
        if not path_env:
            WRITE_LOG_DEV_FILE(
                "PATH environment variable is empty or unset",
                "WARNING"
            )
            return BootstrapResult.error(
                BootstrapErrorCode.PYTHONW_NOT_FOUND,
                "pythonw.exe not found in any location (PATH is empty)"
            )
        
        for path_dir in path_env.split(os.pathsep):
            path_dir = path_dir.strip('"')  # Remove quotes if present
            if not path_dir:
                continue
            
            candidate = Path(path_dir) / "pythonw.exe"
            try:
                if candidate.is_file():
                    WRITE_LOG_DEV_FILE(
                        f"Found pythonw.exe at: {candidate}",
                        "INFO"
                    )
                    return BootstrapResult.ok(
                        candidate,
                        {"method": "found_in_PATH", "path_index": path_env.split(os.pathsep).index(path_dir)}
                    )
            except (OSError, PermissionError) as e:
                # Can't access this directory, continue to next
                continue
        
        # Not found anywhere
        WRITE_LOG_DEV_FILE("pythonw.exe not found in system", "ERROR", BootstrapErrorCode.PYTHONW_NOT_FOUND)
        return BootstrapResult.error( BootstrapErrorCode.PYTHONW_NOT_FOUND,"pythonw.exe not found in any location. Install Python correctly.",  details={"searched_locations": ["Python dir", "PATH"]} )
    
    except Exception as e:
        WRITE_LOG_DEV_FILE(
            f"Error searching for pythonw.exe: {str(e)}",
            "ERROR",
            BootstrapErrorCode.UNKNOWN_ERROR
        )
        return BootstrapResult.error(
            BootstrapErrorCode.UNKNOWN_ERROR,
            f"Unexpected error finding pythonw.exe: {str(e)}"
        )


# ==========================================================
# 🔹 DEPENDENCY MANAGEMENT
# ==========================================================

class DependencyManager:
    """
    Manages installation and verification of Python dependencies.
    
    Responsibilities:
        - Check if packages are installed
        - Install missing packages via pip
        - Handle installation failures gracefully
        - Verify installations completed successfully
    """
    
    @staticmethod
    def install_and_verify_pywin32() -> BootstrapResult[bool]:
        try:
            # Check if already installed
            spec = importlib.util.find_spec("win32api")
            if spec:
                WRITE_LOG_DEV_FILE("pywin32 already installed", "INFO")
                return BootstrapResult.ok(True, {"status": "already_installed"})
            
            WRITE_LOG_DEV_FILE("pywin32 not found, installing...", "INFO")
            
            python_exe = sys.executable
            site_packages = Path(python_exe).parent / "Lib" / "site-packages"
            
            # Clean up old installations
            folders_to_remove = ["win32", "pywin32_system32"]
            for folder in folders_to_remove:
                folder_path = site_packages / folder
                if folder_path.exists():
                    try:
                        shutil.rmtree(folder_path)
                        WRITE_LOG_DEV_FILE(
                            f"Removed old installation: {folder}",
                            "INFO"
                        )
                    except PermissionError:
                        WRITE_LOG_DEV_FILE(
                            f"Cannot remove {folder} (in use). Close other Python instances.",
                            "WARNING"
                        )
                        return BootstrapResult.error(
                            BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED,
                            f"Cannot remove old {folder} installation (in use)",
                            details={"folder": folder, "reason": "Permission denied"}
                        )
            
            # Install pywin32
            try:
                subprocess.run(
                    [python_exe, "-m", "pip", "install", "--force-reinstall", "pywin32==305"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=300  # 5 minutes
                )
                WRITE_LOG_DEV_FILE("pywin32 installed successfully", "INFO")
            except subprocess.TimeoutExpired:
                WRITE_LOG_DEV_FILE("pywin32 installation timed out", "ERROR", BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED)
                return BootstrapResult.error( BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED,   "pywin32 installation timed out (>5 minutes)")
            except subprocess.CalledProcessError as e:
                WRITE_LOG_DEV_FILE( f"pip installation failed: {str(e)}","ERROR",  BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED )
                return BootstrapResult.error(  BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED, f"pip failed to install pywin32: {str(e)}")
            
            # Run post-install script
            postinstall_script = Path(python_exe).parent / "Scripts" / "pywin32_postinstall.py"
            if postinstall_script.exists():
                try:
                    subprocess.run(
                        [python_exe, str(postinstall_script), "-install"],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=60
                    )
                    WRITE_LOG_DEV_FILE("pywin32 post-installation completed", "INFO")
                except subprocess.TimeoutExpired:
                    WRITE_LOG_DEV_FILE(  "pywin32 post-install timed out",  "WARNING" )
                    # Don't fail, might still work
                except subprocess.CalledProcessError as e:
                    WRITE_LOG_DEV_FILE( f"pywin32 post-install failed: {str(e)}","WARNING")
                    # Don't fail, might still work
            
            return BootstrapResult.ok(True, {"status": "installed_and_verified"})
        
        except Exception as e:
            WRITE_LOG_DEV_FILE( f"Error installing pywin32: {traceback.format_exc()}", "ERROR", BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED)
            return BootstrapResult.error( BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED, f"Failed to install pywin32: {str(e)}")
    
    
    @staticmethod
    def install_and_import( package: str, module_name: Optional[str] = None,  required_import: Optional[str] = None, version: Optional[str] = None ) -> BootstrapResult[Any]:
        try:
            module_to_import = module_name or package
            install_spec = f"{package}=={version}" if version else package
            
            # Try to import
            try:
                module = importlib.import_module(module_to_import)
                
                # Verify submodule if specified
                if required_import:
                    try:
                        importlib.import_module(f"{module_to_import}.{required_import}")
                    except ImportError:
                        WRITE_LOG_DEV_FILE(
                            f"Submodule {required_import} not found in {module_to_import}",
                            "WARNING"
                        )
                        # Continue anyway, module might still work
                
                WRITE_LOG_DEV_FILE(
                    f"{package} already installed",
                    "INFO"
                )
                return BootstrapResult.ok(module, {"status": "already_installed"})
            
            except (ModuleNotFoundError, ImportError):
                # Not installed, proceed to install
                pass
            
            # Install package
            WRITE_LOG_DEV_FILE(  f"Installing {install_spec}...",  "INFO" )
            
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", install_spec],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                WRITE_LOG_DEV_FILE(
                    f"{install_spec} installed successfully",
                    "INFO"
                )
            except subprocess.TimeoutExpired:
                WRITE_LOG_DEV_FILE(
                    f"Installation of {package} timed out",
                    "ERROR",
                    BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED
                )
                return BootstrapResult.error(
                    BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED,
                    f"Installation of {package} timed out (>5 minutes)"
                )
            except subprocess.CalledProcessError as e:
                WRITE_LOG_DEV_FILE(
                    f"Failed to install {package}: {str(e)}",
                    "ERROR",
                    BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED
                )
                return BootstrapResult.error(
                    BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED,
                    f"pip failed to install {package}: {str(e)}"
                )
            
            # Import module after installation
            try:
                module = importlib.import_module(module_to_import)
                
                # Verify submodule if specified
                if required_import:
                    try:
                        importlib.import_module(f"{module_to_import}.{required_import}")
                    except ImportError:
                        WRITE_LOG_DEV_FILE(
                            f"Submodule {required_import} still not available",
                            "ERROR"
                        )
                        return BootstrapResult.error(
                            BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED,
                            f"Submodule {required_import} not found after installation"
                        )
                
                return BootstrapResult.ok(module, {"status": "installed_and_imported"})
            
            except ImportError as e:
                WRITE_LOG_DEV_FILE(
                    f"Failed to import {module_to_import} after installation: {str(e)}",
                    "ERROR",
                    BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED
                )
                return BootstrapResult.error(
                    BootstrapErrorCode.DEPENDENCY_IMPORT_FAILED,
                    f"Cannot import {module_to_import} after installation: {str(e)}"
                )
        
        except Exception as e:
            WRITE_LOG_DEV_FILE(
                f"Unexpected error in install_and_import: {traceback.format_exc()}",
                "ERROR",
                BootstrapErrorCode.UNKNOWN_ERROR
            )
            return BootstrapResult.error(
                BootstrapErrorCode.UNKNOWN_ERROR,
                f"Unexpected error installing {package}: {str(e)}"
            )


# ==========================================================
# 🔹 UPDATE MANAGEMENT
# ==========================================================

class UpdateManager:
    
    @staticmethod
    def _read_local_version(path: Optional[Path]) -> BootstrapResult[str]:
        try:
            # Validate path parameter
            if path is None:
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_NOT_FOUND,
                    "Version file path is None"
                )
            
            path = Path(path)
            
            # Check if file exists
            if not path.exists():
                WRITE_LOG_DEV_FILE(
                    f"Version file not found: {path}",
                    "INFO"
                )
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_NOT_FOUND,
                    f"Version file not found: {path}"
                )
            
            # Check if it's a file (not directory)
            if not path.is_file():
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_CORRUPTED,
                    f"Path is not a file: {path}"
                )
            
            # Read file
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                if not content:
                    return BootstrapResult.error(
                        BootstrapErrorCode.VERSION_FILE_CORRUPTED,
                        f"Version file is empty: {path}"
                    )
                
                return BootstrapResult.ok(content, {"file": str(path)})
            
            except PermissionError:
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_READ_FAILED,
                    f"Permission denied reading version file: {path}"
                )
            except UnicodeDecodeError as e:
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_CORRUPTED,
                    f"Version file encoding error: {str(e)}"
                )
            except IOError as e:
                return BootstrapResult.error(
                    BootstrapErrorCode.VERSION_FILE_READ_FAILED,
                    f"IO error reading version file: {str(e)}"
                )
        
        except Exception as e:
            WRITE_LOG_DEV_FILE(
                f"Unexpected error reading version: {traceback.format_exc()}",
                "ERROR"
            )
            return BootstrapResult.error(
                BootstrapErrorCode.UNKNOWN_ERROR,
                f"Unexpected error reading version file: {str(e)}"
            )
    
    
    @staticmethod
    def _download_and_extract( zip_url: str, target_dir: Union[str, Path], clean_target: bool = False,  extract_subdir: Optional[str] = None) -> BootstrapResult[bool]:
        try:
            import requests
            
            # Convert to Path if string (defensive programming)
            target_dir = Path(target_dir) if isinstance(target_dir, str) else target_dir
            
            WRITE_LOG_DEV_FILE(
                f"Downloading update from: {zip_url}",
                "INFO"
            )
            
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "update.zip"
                
                # Download file
                try:
                    response = requests.get(zip_url, stream=True,  headers=HTTP_HEADERS,  timeout=300   )
                    response.raise_for_status()
                    
                    # Write downloaded content
                    with open(zip_path, "wb") as f:
                        for chunk in response.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    
                    WRITE_LOG_DEV_FILE(
                        f"Downloaded {zip_path.stat().st_size} bytes",
                        "INFO"
                    )
                
                except requests.exceptions.Timeout:
                    WRITE_LOG_DEV_FILE(
                        "Download timed out",
                        "ERROR",
                        BootstrapErrorCode.NETWORK_TIMEOUT
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.NETWORK_TIMEOUT,
                        "Download timed out (>5 minutes)"
                    )
                except requests.exceptions.ConnectionError as e:
                    WRITE_LOG_DEV_FILE(
                        f"Network connection failed: {str(e)}",
                        "ERROR",
                        BootstrapErrorCode.NETWORK_CONNECTION_FAILED
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.NETWORK_CONNECTION_FAILED,
                        f"Cannot connect to server: {str(e)}"
                    )
                except requests.exceptions.HTTPError as e:
                    WRITE_LOG_DEV_FILE(
                        f"Server returned error: HTTP {e.response.status_code}",
                        "ERROR",
                        BootstrapErrorCode.NETWORK_INVALID_RESPONSE
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.NETWORK_INVALID_RESPONSE,
                        f"Server error (HTTP {e.response.status_code})"
                    )
                
                # Clean target if requested
                if clean_target and target_dir.exists():
                    try:
                        shutil.rmtree(target_dir)
                        WRITE_LOG_DEV_FILE(
                            f"Cleaned target directory: {target_dir}",
                            "INFO"
                        )
                    except Exception as e:
                        WRITE_LOG_DEV_FILE(
                            f"Cannot clean target directory: {str(e)}",
                            "WARNING"
                        )
                        # Don't fail, might still work
                
                # Extract ZIP
                try:
                    with zipfile.ZipFile(zip_path, "r") as z:
                        z.extractall(tmpdir)
                    
                    WRITE_LOG_DEV_FILE(
                        "ZIP extraction completed",
                        "INFO"
                    )
                
                except zipfile.BadZipFile:
                    WRITE_LOG_DEV_FILE(
                        "Downloaded file is not a valid ZIP",
                        "ERROR",
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED,
                        "Downloaded file is corrupted or not a ZIP file"
                    )
                except Exception as e:
                    WRITE_LOG_DEV_FILE(
                        f"ZIP extraction error: {str(e)}",
                        "ERROR",
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED,
                        f"Cannot extract ZIP: {str(e)}"
                    )
                
                # Find extracted directory
                extracted_items = [d for d in Path(tmpdir).iterdir() if d.name != "update.zip"]
                if not extracted_items:
                    return BootstrapResult.error(
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED,
                        "ZIP file is empty"
                    )
                
                extracted_root = extracted_items[0]
                extracted_dir = extracted_root
                
                # Use subdirectory if specified
                if extract_subdir:
                    candidate = extracted_root / extract_subdir
                    if candidate.exists():
                        extracted_dir = candidate
                        WRITE_LOG_DEV_FILE(
                            f"Using subdirectory: {extract_subdir}",
                            "INFO"
                        )
                    else:
                        WRITE_LOG_DEV_FILE(
                            f"Subdirectory not found: {extract_subdir}",
                            "WARNING"
                        )
                
                # Copy extracted files to target
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    for item in extracted_dir.iterdir():
                        target_item = target_dir / item.name
                        if item.is_dir():
                            if target_item.exists():
                                shutil.rmtree(target_item)
                            shutil.move(str(item), str(target_item))
                        else:
                            shutil.move(str(item), str(target_item))
                    
                    WRITE_LOG_DEV_FILE(
                        f"Extraction completed to: {target_dir}",
                        "INFO"
                    )
                    return BootstrapResult.ok(True, {"target": str(target_dir)})
                
                except shutil.Error as e:
                    WRITE_LOG_DEV_FILE(
                        f"File operation error: {str(e)}",
                        "ERROR",
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED
                    )
                    return BootstrapResult.error(
                        BootstrapErrorCode.UPDATE_EXTRACT_FAILED,
                        f"Cannot copy extracted files: {str(e)}"
                    )
        
        except Exception as e:
            WRITE_LOG_DEV_FILE(
                f"Unexpected error in download_and_extract: {traceback.format_exc()}",
                "ERROR"
            )
            return BootstrapResult.error(
                BootstrapErrorCode.UNKNOWN_ERROR,
                f"Unexpected error downloading/extracting: {str(e)}"
            )

    
    @staticmethod
    def check_and_update() -> BootstrapResult[bool]:
        try:
            import requests
            
            WRITE_LOG_DEV_FILE(
                "Checking for updates",
                "INFO"
            )
            
            # Encrypt current date
            date_plain = datetime.datetime.now().strftime("%Y-%m-%d")
            date_result = encrypt_message(date_plain, KEY)
            
            if not date_result.success:
                WRITE_LOG_DEV_FILE(
                    f"Date encryption failed: {date_result.error_msg}",
                    "ERROR",
                    BootstrapErrorCode.ENCRYPTION_FAILED
                )
                return BootstrapResult.error(
                    BootstrapErrorCode.ENCRYPTION_FAILED,
                    f"Cannot encrypt date for update check: {date_result.error_msg}"
                )
            
            date_encrypted = date_result.data
            
            # Build URLs
            url = (
                f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
                f"nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"
            )
            download_url = (
                f"https://reporting.nrb-apps.com/APP_R/redirect.php?"
                f"nv=1&rv4=1&event=download&type=V4&ext=Script&k={date_encrypted}"
            )
            
            # Try to get version info from server (with retries)
            max_attempts = 3
            version_data = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    WRITE_LOG_DEV_FILE(
                        f"Attempt {attempt}: Checking version on server",
                        "DEBUG"
                    )
                    
                    response = requests.get(
                        url,
                        headers=HTTP_HEADERS,
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        WRITE_LOG_DEV_FILE(
                            f"Attempt {attempt}: Server returned HTTP {response.status_code}",
                            "WARNING"
                        )
                        if attempt < max_attempts:
                            time.sleep(2)
                            continue
                        return BootstrapResult.error(
                            BootstrapErrorCode.NETWORK_INVALID_RESPONSE,
                            f"Server returned HTTP {response.status_code} after {max_attempts} attempts"
                        )
                    
                    version_data = response.json()
                    break
                
                except requests.exceptions.Timeout:
                    WRITE_LOG_DEV_FILE(
                        f"Attempt {attempt}: Server connection timed out",
                        "WARNING"
                    )
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    return BootstrapResult.error(
                        BootstrapErrorCode.NETWORK_TIMEOUT,
                        f"Server not responding after {max_attempts} attempts"
                    )
                
                except requests.exceptions.ConnectionError as e:
                    WRITE_LOG_DEV_FILE( f"Attempt {attempt}: Connection error: {str(e)}",  "WARNING" )
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    return BootstrapResult.error( BootstrapErrorCode.NETWORK_CONNECTION_FAILED,  f"Cannot reach server after {max_attempts} attempts" )
                
                except ValueError as e:
                    WRITE_LOG_DEV_FILE( f"Attempt {attempt}: Invalid JSON response: {str(e)}", "WARNING")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    return BootstrapResult.error(  BootstrapErrorCode.NETWORK_INVALID_RESPONSE,"Server returned invalid JSON")
            
            if not version_data:
                return BootstrapResult.error( BootstrapErrorCode.NETWORK_CONNECTION_FAILED,   "Failed to retrieve version information")
            
            # Extract versions from server response
            server_program = version_data.get("version")
            server_ext = version_data.get("version_Extention")
            
            if not server_program or not server_ext:
                WRITE_LOG_DEV_FILE( "Server response missing version fields",  "ERROR",  BootstrapErrorCode.NETWORK_INVALID_RESPONSE)
                return BootstrapResult.error( BootstrapErrorCode.NETWORK_INVALID_RESPONSE, "Server response missing version information")
            
            # Read local versions
            local_program_result = UpdateManager._read_local_version( Path("config") / "version.txt")
            local_ext_result = UpdateManager._read_local_version(EXTENSIONS_DIR_TEMPLETE / "version.txt")
            
            local_program = local_program_result.data if local_program_result.success else None
            local_ext = local_ext_result.data if local_ext_result.success else None
            
            # Check if updates needed
            update_done = False
            
            # Program update
            if not local_program or local_program != server_program:
                WRITE_LOG_DEV_FILE(  f"Program update needed: {local_program} → {server_program}", "INFO")
                download_result = UpdateManager._download_and_extract(  download_url,  ROOT_DIR,  clean_target=False)
                if not download_result.success:
                    return download_result  # Return error
                update_done = True
            
            # Extension update
            if not local_ext or local_ext != server_ext:
                WRITE_LOG_DEV_FILE( f"Extension update needed: {local_ext} → {server_ext}",  "INFO")
                tools_dir = TOOLS_DIR
                tools_dir.mkdir(parents=True, exist_ok=True)
                
                download_result = UpdateManager._download_and_extract( download_url, tools_dir, clean_target=True,  extract_subdir="tools")
                if not download_result.success:
                    return download_result  # Return error
                update_done = True
            
            # Report status
            if not update_done:
                WRITE_LOG_DEV_FILE( "Application already up-to-date",  "INFO" )
                return BootstrapResult.ok( False,  {"status": "up-to-date", "program": server_program, "extensions": server_ext})
            else:
                WRITE_LOG_DEV_FILE( "Updates completed successfully",  "INFO" )
                return BootstrapResult.ok( True,     {"status": "updated", "program": server_program, "extensions": server_ext} )
        
        except Exception as e:
            WRITE_LOG_DEV_FILE(  f"Unexpected error in check_and_update: {traceback.format_exc()}", "ERROR",  BootstrapErrorCode.UNKNOWN_ERROR )
            return BootstrapResult.error( BootstrapErrorCode.UNKNOWN_ERROR, f"Unexpected error checking for updates: {str(e)}" )


# ==========================================================
# 🔹 INITIALIZATION & MAIN
# ==========================================================

def initialize_dependencies() -> BootstrapResult[bool]:
    """
    Initialize all required Python dependencies.
    
    Returns:
        BootstrapResult[bool]: Success status
    
    Side Effects:
        - Installs packages via pip if needed
        - Installs pywin32 with post-installation script
        - Disables urllib3 warnings
        - Sets global module references
    
    Scenarios:
        ✓ All installed: Quick return
        ✓ Partial missing: Installs missing packages
        ✗ Any installation fails: Returns error (caller can decide to exit)
    
    Example:
        >>> result = initialize_dependencies()
        >>> if result:
        ...     print("All dependencies ready")
        ... else:
        ...     print(f"Setup failed: {result.error_msg}")
        ...     sys.exit(1)
    """
    try:
        WRITE_LOG_DEV_FILE(  "Initializing dependencies",  "INFO" )
        
        # Install pywin32 (Windows-specific)
        pywin32_result = DependencyManager.install_and_verify_pywin32()
        if not pywin32_result.success:
            # Log but don't fail completely (might not be needed on all systems)
            WRITE_LOG_DEV_FILE(
                f"Warning: pywin32 setup failed: {pywin32_result.error_msg}",
                "WARNING"
            )
        
        # Install other dependencies
        packages = [
            ("requests", None, None, None),
            ("urllib3", None, None, "2.2.3"),
            ("PyQt6", None, "QtCore", "6.7.0"),
            ("cryptography", None, None, "3.3.2"),
            ("psutil", None, None, None),
            ("pytz", None, None, None),
            ("tqdm", None, None, None),
            ("platformdirs", None, None, None),
            ("selenium", None, "webdriver", "4.27.1"),
            ("colorama", None, None, None)
        ]
        
        failed_packages = []
        
        for package, module_name, required_import, version in packages:
            result = DependencyManager.install_and_import(
                package,
                module_name=module_name,
                required_import=required_import,
                version=version
            )
            if not result.success:
                failed_packages.append((package, result.error_msg))
        
        if failed_packages:
            error_details = "\n".join(
                [f"  - {pkg}: {msg}" for pkg, msg in failed_packages]
            )
            WRITE_LOG_DEV_FILE(
                f"Failed to install: {error_details}",
                "ERROR"
            )
            return BootstrapResult.error(
                BootstrapErrorCode.DEPENDENCY_INSTALLATION_FAILED,
                f"Failed to install {len(failed_packages)} packages",
                details={"failed": [p[0] for p in failed_packages]}
            )
        
        # Disable SSL warnings from urllib3
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception as e:
            WRITE_LOG_DEV_FILE( f"Could not disable urllib3 warnings: {str(e)}", "DEBUG" )
        
        WRITE_LOG_DEV_FILE( "All dependencies initialized successfully", "INFO")
        return BootstrapResult.ok(True, {"status": "all_dependencies_ready"})
    
    except Exception as e:
        WRITE_LOG_DEV_FILE( f"Unexpected error initializing dependencies: {traceback.format_exc()}", "ERROR")
        return BootstrapResult.error(  BootstrapErrorCode.UNKNOWN_ERROR,   f"Unexpected error initializing dependencies: {str(e)}" )


def main() -> int:
    """
    Main entry point for checkV3 bootstrap script.
    
    This function:
      1. Hides console window (Windows only)
      2. Clears previous logs
      3. Initializes dependencies
      4. Finds pythonw.exe
      5. Checks for updates
      6. Launches main application (AppV2.py)
    
    Returns:
        int: Exit code (0=success, >0=error)
    
    Exit Codes:
        0: Application started successfully
        1: Dependency initialization failed
        2: pythonw.exe not found
        3: Update check/application failed
        Other: Unexpected error
    
    Side Effects:
        - Hides console window
        - Clears log file
        - Creates dependencies
        - Spawns subprocess for main application
    
    Scenarios:
        ✓ Normal flow: All checks pass, app launched, returns 0
        ✗ Bad dependencies: Returns 1
        ✗ pythonw.exe missing: Returns 2
        ✗ Update check fails: Continues anyway (non-blocking)
        ✗ App launch fails: Returns 3
        ✗ Unexpected error: Logs and returns 1
    """
    try:
        # Hide console window on Windows
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.kernel32.GetConsoleWindow(),
                    0  # SW_HIDE
                )
            except Exception as e:
                # Not critical, continue anyway
                pass
        
        # Clear previous log
        clear_log_result = clear_log()
        if not clear_log_result.success:
            # Not critical, continue
            pass
        
        WRITE_LOG_DEV_FILE("=== APPLICATION BOOTSTRAP STARTED ===", "INFO")
        WRITE_LOG_DEV_FILE(f"Python: {sys.version}", "INFO")
        WRITE_LOG_DEV_FILE(f"Platform: {sys.platform}", "INFO")
        
        # Initialize dependencies
        WRITE_LOG_DEV_FILE("Step 1: Initializing dependencies", "INFO")
        dep_result = initialize_dependencies()
        if not dep_result.success:
            WRITE_LOG_DEV_FILE(
                f"Dependency initialization failed: {dep_result.error_msg}",
                "CRITICAL"
            )
            return 1  # Exit with error code
        
        # Find pythonw.exe
        WRITE_LOG_DEV_FILE("Step 2: Locating pythonw.exe", "INFO")
        pythonw_result = find_pythonw()
        if not pythonw_result.success:
            WRITE_LOG_DEV_FILE(
                f"pythonw.exe not found: {pythonw_result.error_msg}",
                "CRITICAL"
            )
            return 2  # Specific error code
        
        pythonw_path = pythonw_result.data
        WRITE_LOG_DEV_FILE(f"Found pythonw.exe at: {pythonw_path}", "INFO")
        
        # Check for updates (non-blocking - continue even if fails)
        WRITE_LOG_DEV_FILE("Step 3: Checking for updates", "INFO")
        if len(sys.argv) == 1:  # Normal launch
            update_result = UpdateManager.check_and_update()
            if update_result.success:
                if update_result.data:  # Updates were applied
                    WRITE_LOG_DEV_FILE(
                        "Updates applied - restarting application",
                        "INFO"
                    )
                else:  # Already up-to-date
                    WRITE_LOG_DEV_FILE("Application is up-to-date", "INFO")
            else:
                WRITE_LOG_DEV_FILE(
                    f"Update check failed (non-blocking): {update_result.error_msg}",
                    "WARNING"
                )
                # Continue anyway
        
        # Generate encryption keys
        WRITE_LOG_DEV_FILE("Step 4: Generating encryption keys", "INFO")
        key_result = generate_encrypted_key()
        if not key_result.success:
            WRITE_LOG_DEV_FILE(
                f"Encryption key generation failed: {key_result.error_msg}",
                "ERROR"
            )
            return 3
        
        encrypted_key, secret_key = key_result.data
        
        # Launch main application
        if len(sys.argv) == 1:  # Normal launch
            WRITE_LOG_DEV_FILE("Step 5: Launching main application", "INFO")
            script_path = SCRIPT_DIR / "src" / "AppV2.pyc"
            
            if not script_path.exists():
                WRITE_LOG_DEV_FILE(
                    f"Main application not found: {script_path}",
                    "CRITICAL"
                )
                return 3
            
            try:
                subprocess.run(
                    [str(pythonw_path), str(script_path), encrypted_key, secret_key],
                    check=False,  # Don't raise on non-zero exit
                    timeout=None   # No timeout
                )
                WRITE_LOG_DEV_FILE("Main application launched successfully", "INFO")
            except subprocess.TimeoutExpired:
                WRITE_LOG_DEV_FILE(
                    "Main application launch timed out",
                    "ERROR"
                )
                return 3
            except Exception as e:
                WRITE_LOG_DEV_FILE(
                    f"Error launching main application: {str(e)}",
                    "ERROR"
                )
                return 3
        
        WRITE_LOG_DEV_FILE("=== APPLICATION BOOTSTRAP COMPLETED ===", "INFO")
        return 0  # Success
    
    except KeyboardInterrupt:
        WRITE_LOG_DEV_FILE("Bootstrap interrupted by user", "WARNING")
        return 1
    
    except Exception as e:
        error_trace = traceback.format_exc()
        WRITE_LOG_DEV_FILE(
            f"Unexpected error in bootstrap: {error_trace}",
            "CRITICAL"
        )
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

