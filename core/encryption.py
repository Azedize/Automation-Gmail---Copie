import os
import base64
import hashlib
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


try:
    from config.settings import settings
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__} : {e}")
    sys.exit(1)


# =========================================================
# 🔒 EncryptionService (AES-CBC, AES-GCM, Fernet)
# =========================================================


class EncryptionService:
    # =========================
    # 🔹 AES-CBC decrypt unified
    # =========================
    @staticmethod
    def decryptMessage(base64_data: str, key) -> str:
        return EncryptionService.decrypt_message(base64_data, key)

    @staticmethod
    def decrypt_message(base64_data: str, key) -> str:
        """
        🔓 AES-CBC decrypt (PKCS7) unified
        - base64_data: النص المشفر Base64
        - key: str أو bytes
        """

        if isinstance(key, str):
            key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
        elif isinstance(key, bytes):
            key_bytes = key
        else:
            settings.write_log_event(
                "decryption_key_invalid",
                "ERROR",
                key_type=type(key).__name__,
            )
            sys.exit(1)

        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.write_log_event(
                "decryption_key_invalid",
                "ERROR",
                expected_length=settings.AES_KEY_LENGTH,
                received_length=len(key_bytes),
            )
            sys.exit(1)

        try:
            if not isinstance(base64_data, str) or not base64_data.strip():
                raise ValueError(
                    f"Le texte chiffré doit être une chaîne Base64 non vide. "
                    f"Valeur reçue: {repr(base64_data)}"
                )

            try:
                raw = base64.b64decode(base64_data)
            except Exception as e:
                raise ValueError(f"Impossible de décoder Base64: {e}") from e

            if len(raw) < settings.AES_IV_LENGTH_CBC:
                raise ValueError(
                    f"Payload chiffré invalide : longueur insuffisante. "
                    f"Attendu au moins {settings.AES_IV_LENGTH_CBC} octets pour l'IV, reçu {len(raw)}."
                )

            iv = raw[: settings.AES_IV_LENGTH_CBC]
            ciphertext = raw[settings.AES_IV_LENGTH_CBC :]

            if len(iv) != settings.AES_IV_LENGTH_CBC:
                raise ValueError(
                    f"Invalid IV size ({len(iv)}) for CBC. Expected {settings.AES_IV_LENGTH_CBC}."
                )
            if len(ciphertext) == 0:
                raise ValueError("Ciphertext is empty after extracting IV.")

            cipher = Cipher(
                algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # PKCS7 unpadding
            unpadder = padding.PKCS7(settings.AES_BLOCK_SIZE).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            settings.write_log_event(
                "aes_cbc_decryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                payload_length=len(base64_data) if isinstance(base64_data, str) else 0,
            )
            sys.exit(1)

    # =========================
    # 🔑 Key derivation (PBKDF2)
    # =========================
    @staticmethod
    def deriveKey(password: str, salt: bytes) -> bytes:
        return EncryptionService.derive_key(password, salt)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        if len(salt) != settings.AES_SALT_LENGTH:
            settings.write_log_event(
                "pbkdf2_key_derivation_failed",
                "ERROR",
                expected_salt_length=settings.AES_SALT_LENGTH,
                received_salt_length=len(salt),
            )
            sys.exit(1)
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS,
            )
            return kdf.derive(password.encode("utf-8"))
        except Exception as e:
            settings.write_log_event(
                "pbkdf2_key_derivation_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                password_length=len(password),
            )
            sys.exit(1)

    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encryptMessage(plaintext: str, key_bytes: bytes) -> str:
        return EncryptionService.encrypt_message(plaintext, key_bytes)

    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.write_log_event(
                "aes_cbc_encryption_failed",
                "ERROR",
                expected_length=settings.AES_KEY_LENGTH,
                received_length=len(key_bytes),
            )
            sys.exit(1)
        try:
            padder = padding.PKCS7(settings.AES_BLOCK_SIZE).padder()
            padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

            iv = os.urandom(settings.AES_IV_LENGTH_CBC)
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()

            return base64.b64encode(iv + ciphertext).decode("utf-8")
        except Exception as e:
            settings.write_log_event(
                "aes_cbc_encryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                plaintext_length=len(plaintext),
            )
            sys.exit(1)

    # =========================
    # 🔐 AES-GCM Encrypt
    # =========================
    @staticmethod
    def encryptAesGcm(password: str, plaintext: str) -> str:
        return EncryptionService.encrypt_aes_gcm(password, plaintext)

    @staticmethod
    def encrypt_aes_gcm(password: str, plaintext: str) -> str:
        try:
            salt = os.urandom(settings.AES_SALT_LENGTH)
            key = EncryptionService.derive_key(password, salt)
            iv = os.urandom(settings.AES_IV_LENGTH_GCM)

            aesgcm = AESGCM(key)
            ciphertext_and_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

            payload = salt + iv + ciphertext_and_tag
            return payload.hex()
        except SystemExit:
            raise
        except Exception as e:
            settings.write_log_event(
                "aes_gcm_encryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                password_length=len(password),
                plaintext_length=len(plaintext),
            )
            sys.exit(1)

    # =========================
    # 🔑 Verify Fernet Key
    # =========================
    @staticmethod
    def verifyKey(encrypted_key: str, secret_key: str) -> bool:
        return EncryptionService.verify_key(encrypted_key, secret_key)

    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        try:
            fernet = Fernet(secret_key.encode())
            decrypted = fernet.decrypt(encrypted_key.encode())
            return decrypted == b"authorized"
        except Exception as e:
            settings.write_log_event(
                "fernet_key_verification_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                encrypted_key_length=len(encrypted_key),
                secret_key_length=len(secret_key),
            )
            sys.exit(1)

    # =========================
    # 🔑 Generate Fernet Encrypted Key
    # =========================
    @staticmethod
    def generateEncryptedKey():
        return EncryptionService.generate_encrypted_key()

    @staticmethod
    def generate_encrypted_key():
        try:
            secret_key = Fernet.generate_key()
            fernet = Fernet(secret_key)
            encrypted_message = fernet.encrypt(b"authorized")
            return encrypted_message.decode(), secret_key.decode()
        except Exception as e:
            settings.write_log_event(
                "fernet_key_generation_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
            )
            sys.exit(1)


# =========================
# 🔹 Instance
# =========================
EncryptionService = EncryptionService()
