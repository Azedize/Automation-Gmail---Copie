import os
import base64
import time
import traceback

from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet

from config.settings import settings
from Log import DevLogger


# =========================
# ❌ Custom Exception
# =========================
class EncryptionError(Exception):
    pass


# =========================
# 🔐 Encryption Service
# =========================
class EncryptionService:

    # =========================
    # 🔑 Key Derivation (PBKDF2)
    # =========================
    @staticmethod
    def Derive_Key(password: str, salt: bytes) -> bytes:
        start = time.perf_counter()
        DevLogger.debug("🔑 Derive_Key() started")

        try:
            if len(salt) != settings.AES_SALT_LENGTH:
                raise EncryptionError(
                    f"Invalid salt length: {len(salt)} "
                    f"(expected {settings.AES_SALT_LENGTH})"
                )

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS,
            )

            key = kdf.derive(password.encode("utf-8"))
            DevLogger.debug("✅ Key derived successfully")

            return key

        except Exception as e:
            DevLogger.error(
                f"❌ Derive_Key failed: {e}\n{traceback.format_exc()}"
            )
            raise EncryptionError(f"Key derivation failed: {e}")

        finally:
            DevLogger.debug(
                f"⏱️ Derive_Key execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        start = time.perf_counter()
        DevLogger.debug("🔒 encrypt_message() started")

        try:
            if len(key_bytes) != settings.AES_KEY_LENGTH:
                raise EncryptionError("Invalid AES key length")

            padder = padding.PKCS7(settings.AES_BLOCK_SIZE).padder()
            padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

            iv = os.urandom(settings.AES_IV_LENGTH_CBC)

            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv)
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()

            result = base64.b64encode(iv + ciphertext).decode("utf-8")
            DevLogger.debug("✅ AES-CBC encryption successful")

            return result

        except Exception as e:
            DevLogger.error(
                f"❌ encrypt_message failed: {e}\n{traceback.format_exc()}"
            )
            raise EncryptionError(f"AES-CBC encryption failed: {e}")

        finally:
            DevLogger.debug(
                f"⏱️ encrypt_message execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # =========================
    # 🔓 AES-CBC Decrypt
    # =========================
    @staticmethod
    def decrypt_message(base64_data: str, key_bytes: bytes) -> str:
        start = time.perf_counter()
        DevLogger.debug("🔓 decrypt_message() started")

        try:
            if len(key_bytes) != settings.AES_KEY_LENGTH:
                raise EncryptionError("Invalid AES key length")

            raw = base64.b64decode(base64_data)
            iv = raw[:settings.AES_IV_LENGTH_CBC]
            ciphertext = raw[settings.AES_IV_LENGTH_CBC:]

            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv)
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            unpadder = padding.PKCS7(settings.AES_BLOCK_SIZE).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            DevLogger.debug("✅ AES-CBC decryption successful")
            return plaintext.decode("utf-8")

        except Exception as e:
            DevLogger.error(
                f"❌ decrypt_message failed: {e}\n{traceback.format_exc()}"
            )
            raise EncryptionError(f"AES-CBC decryption failed: {e}")

        finally:
            DevLogger.debug(
                f"⏱️ decrypt_message execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # =========================
    # 🔐 AES-GCM Encrypt
    # =========================
    @staticmethod
    def encrypt_aes_gcm(password: str, plaintext: str) -> str:
        start = time.perf_counter()
        DevLogger.debug("🔐 encrypt_aes_gcm() started")

        try:
            salt = os.urandom(settings.AES_SALT_LENGTH)
            key = EncryptionService.Derive_Key(password, salt)

            iv = os.urandom(settings.AES_IV_LENGTH_GCM)
            aesgcm = AESGCM(key)

            ciphertext_and_tag = aesgcm.encrypt(
                iv,
                plaintext.encode("utf-8"),
                None
            )

            payload = salt + iv + ciphertext_and_tag
            DevLogger.debug("✅ AES-GCM encryption successful")

            return payload.hex()

        except Exception as e:
            DevLogger.error(
                f"❌ encrypt_aes_gcm failed: {e}\n{traceback.format_exc()}"
            )
            raise EncryptionError(f"AES-GCM encryption failed: {e}")

        finally:
            DevLogger.debug(
                f"⏱️ encrypt_aes_gcm execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # =========================
    # 🔍 Verify Fernet Key
    # =========================
    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        start = time.perf_counter()
        DevLogger.debug("🔍 verify_key() started")

        try:
            fernet = Fernet(secret_key.encode())
            decrypted = fernet.decrypt(encrypted_key.encode())

            is_valid = decrypted == b"authorized"
            DevLogger.debug(f"🔐 Key verification result: {is_valid}")

            return is_valid

        except Exception as e:
            DevLogger.error(
                f"❌ verify_key failed: {e}\n{traceback.format_exc()}"
            )
            return False

        finally:
            DevLogger.debug(
                f"⏱️ verify_key execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )

    # =========================
    # 🔑 Generate Encrypted Key
    # =========================
    @staticmethod
    def generate_encrypted_key():
        start = time.perf_counter()
        DevLogger.debug("🔑 generate_encrypted_key() started")

        try:
            secret_key = Fernet.generate_key()
            fernet = Fernet(secret_key)
            encrypted_message = fernet.encrypt(b"authorized")

            DevLogger.debug("✅ Encrypted key generated successfully")
            return encrypted_message.decode(), secret_key.decode()

        except Exception as e:
            DevLogger.error(
                f"❌ generate_encrypted_key failed: {e}\n{traceback.format_exc()}"
            )
            raise

        finally:
            DevLogger.debug(
                f"⏱️ generate_encrypted_key execution time: "
                f"{time.perf_counter() - start:.4f}s"
            )


# =========================
# 🌍 Global Instance
# =========================
EncryptionService = EncryptionService()
