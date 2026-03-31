import os
import base64
import hashlib
import traceback
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from config.settings import settings


# =========================================================
# 🔒 EncryptionService (AES-CBC, AES-GCM, Fernet)
# =========================================================
class EncryptionService:

    # =========================
    # 🔹 AES-CBC decrypt unified
    # =========================
    @staticmethod
    def decrypt_message(base64_data: str, key) -> str:
        """
        🔓 AES-CBC decrypt (PKCS7) unified
        - base64_data: النص المشفر Base64
        - key: str أو bytes
        """
        # تحويل المفتاح إلى bytes إذا كان str
        if isinstance(key, str):
            key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
        elif isinstance(key, bytes):
            key_bytes = key
        else:
            raise ValueError("المفتاح يجب أن يكون str أو bytes")

        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.WRITE_LOG_DEV_FILE("Invalid AES key length", level="ERROR")
            raise ValueError("Invalid AES key length")

        try:
            raw = base64.b64decode(base64_data)
            iv = raw[:settings.AES_IV_LENGTH_CBC]
            ciphertext = raw[settings.AES_IV_LENGTH_CBC:]

            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # PKCS7 unpadding
            unpadder = padding.PKCS7(settings.AES_BLOCK_SIZE).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"AES-CBC decryption failed: {e}\n{traceback.format_exc()}", level="ERROR")
            raise Exception(f"AES-CBC decryption failed: {e}")

    # =========================
    # 🔑 Key derivation (PBKDF2)
    # =========================
    @staticmethod
    def Derive_Key(password: str, salt: bytes) -> bytes:
        if len(salt) != settings.AES_SALT_LENGTH:
            raise ValueError(
                f"Invalid salt length: {len(salt)} (expected {settings.AES_SALT_LENGTH})"
            )
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS
            )
            return kdf.derive(password.encode("utf-8"))
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"Key derivation failed: {e}\n{traceback.format_exc()}", level="ERROR")
            raise Exception(f"Key derivation failed: {e}")

    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.WRITE_LOG_DEV_FILE("Invalid AES key length", level="ERROR")
            raise ValueError("Invalid AES key length")
        try:
            padder = padding.PKCS7(settings.AES_BLOCK_SIZE).padder()
            padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

            iv = os.urandom(settings.AES_IV_LENGTH_CBC)
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()

            return base64.b64encode(iv + ciphertext).decode("utf-8")
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"AES-CBC encryption failed: {e}\n{traceback.format_exc()}", level="ERROR")
            raise Exception(f"AES-CBC encryption failed: {e}")

    # =========================
    # 🔐 AES-GCM Encrypt
    # =========================
    @staticmethod
    def encrypt_aes_gcm(password: str, plaintext: str) -> str:
        try:
            salt = os.urandom(settings.AES_SALT_LENGTH)
            key = EncryptionService.Derive_Key(password, salt)
            iv = os.urandom(settings.AES_IV_LENGTH_GCM)

            aesgcm = AESGCM(key)
            ciphertext_and_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

            payload = salt + iv + ciphertext_and_tag
            return payload.hex()
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"AES-GCM encryption failed: {e}\n{traceback.format_exc()}", level="ERROR")
            raise Exception(f"AES-GCM encryption failed: {e}")

    # =========================
    # 🔑 Verify Fernet Key
    # =========================
    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        try:
            fernet = Fernet(secret_key.encode())
            decrypted = fernet.decrypt(encrypted_key.encode())
            return decrypted == b"authorized"
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(f"Key verification failed: {e}\n{traceback.format_exc()}", level="ERROR")
            return False

    # =========================
    # 🔑 Generate Fernet Encrypted Key
    # =========================
    @staticmethod
    def generate_encrypted_key():
        secret_key = Fernet.generate_key()
        fernet = Fernet(secret_key)
        encrypted_message = fernet.encrypt(b"authorized")
        return encrypted_message.decode(), secret_key.decode()


# =========================
# 🔹 Instance
# =========================
EncryptionService = EncryptionService()