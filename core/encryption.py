# ==========================================================
# encryption_service.py
# Service de chiffrement sécurisé
# ==========================================================

import os
import base64
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
from config.settings import settings
from Log import DevLogger


class EncryptionError(Exception):
    """Exception custom pour erreurs de chiffrement"""
    pass


class EncryptionService:

    # =========================
    # 🔑 Key Derivation (PBKDF2)
    # =========================
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        try:
            if len(salt) != settings.AES_SALT_LENGTH:
                raise EncryptionError(
                    f"Longueur du sel invalide : {len(salt)} "
                    f"(attendu {settings.AES_SALT_LENGTH})"
                )

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS,
            )
            key = kdf.derive(password.encode("utf-8"))
            return key
        except Exception as e:
            DevLogger.error(f"Échec dérivation clé : {e}")
            raise EncryptionError(f"Dérivation clé échouée: {e}")

    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        try:
            if len(key_bytes) != settings.AES_KEY_LENGTH:
                raise EncryptionError("Longueur clé AES invalide")

            padder = padding.PKCS7(settings.AES_BLOCK_SIZE).padder()
            padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

            iv = os.urandom(settings.AES_IV_LENGTH_CBC)
            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            return base64.b64encode(iv + ciphertext).decode("utf-8")
        except Exception as e:
            DevLogger.error(f"AES-CBC encryption failed")
            raise EncryptionError(f"AES-CBC encryption échouée: {e}")

    # =========================
    # 🔓 AES-CBC Decrypt
    # =========================
    @staticmethod
    def decrypt_message(base64_data: str, key_bytes: bytes) -> str:
        try:
            if len(key_bytes) != settings.AES_KEY_LENGTH:
                raise EncryptionError("Longueur clé AES invalide")

            raw = base64.b64decode(base64_data)
            iv = raw[:settings.AES_IV_LENGTH_CBC]
            ciphertext = raw[settings.AES_IV_LENGTH_CBC:]

            cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            unpadder = padding.PKCS7(settings.AES_BLOCK_SIZE).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            return plaintext.decode("utf-8")
        except Exception as e:
            DevLogger.error(f"AES-CBC decryption failed")
            raise EncryptionError(f"AES-CBC decryption échouée: {e}")

    # =========================
    # 🔐 AES-GCM Encrypt
    # =========================
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
        except Exception as e:
            DevLogger.error("AES-GCM encryption failed")
            raise EncryptionError(f"AES-GCM encryption échouée: {e}")

    # =========================
    # 🔑 Génération / Vérification clé Fernet
    # =========================
    @staticmethod
    def generate_encrypted_key() -> tuple[str, str]:
        """Génère une clé secrète et un message chiffré"""
        secret_key = Fernet.generate_key()
        fernet = Fernet(secret_key)
        encrypted_message = fernet.encrypt(b"authorized")
        DevLogger.debug("Clé chiffrée générée (ne pas logger le contenu)")
        return encrypted_message.decode(), secret_key.decode()

    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        try:
            fernet = Fernet(secret_key.encode())
            decrypted = fernet.decrypt(encrypted_key.encode())
            return decrypted == b"authorized"
        except Exception:
            DevLogger.warning("Échec vérification clé")
            return False


# ==========================================================
# Instance globale
# ==========================================================
EncryptionService = EncryptionService()
