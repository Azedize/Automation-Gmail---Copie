import os
import base64
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
import sys



class EncryptionError(Exception):
    pass


class EncryptionService:

  
    
    

    # =========================
    # 🔑 Key Derivation (PBKDF2)
    # =========================
    @staticmethod
    def Derive_Key(password: str, salt: bytes) -> bytes:
        try:
            if len(salt) != 16:
                raise EncryptionError(
                    f"Invalid salt length: {len(salt)} "
                    f"(expected {16})"
                )

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100_000,
            )
            return kdf.derive(password.encode("utf-8"))

        except Exception as e:
            raise EncryptionError(f"Key derivation failed: {e}")

    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        try:
            if len(key_bytes) != 32:
                raise EncryptionError("Invalid AES key length")

            padder = padding.PKCS7(128).padder()
            padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

            iv = os.urandom(16)

            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv)
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()

            return base64.b64encode(iv + ciphertext).decode("utf-8")

        except Exception as e:
            raise EncryptionError(f"AES-CBC encryption failed: {e}")

    # =========================
    # 🔓 AES-CBC Decrypt
    # =========================
    @staticmethod
    def decrypt_message(base64_data: str, key_bytes: bytes) -> str:
        try:
            if len(key_bytes) != 32:
                raise EncryptionError("Invalid AES key length")

            raw = base64.b64decode(base64_data)

            iv = raw[:16]
            ciphertext = raw[16:]

            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv)
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext.decode("utf-8")

        except Exception as e:
            raise EncryptionError(f"AES-CBC decryption failed: {e}")

    # =========================
    # 🔐 AES-GCM Encrypt
    # =========================
    @staticmethod
    def encrypt_aes_gcm(password: str, plaintext: str) -> str:
        try:
            salt = os.urandom(16)
            key = EncryptionService.Derive_Key(password, salt)

            iv = os.urandom(12)
            aesgcm = AESGCM(key)

            ciphertext_and_tag = aesgcm.encrypt(
                iv,
                plaintext.encode("utf-8"),
                None
            )

            payload = salt + iv + ciphertext_and_tag
            return payload.hex()

        except Exception as e:
            raise EncryptionError(f"AES-GCM encryption failed: {e}")


    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        try:
            fernet = Fernet(secret_key.encode())
            decrypted = fernet.decrypt(encrypted_key.encode())
            if decrypted == b"authorized":
                return True
            else:
                return False
        except Exception as e:
            return False


    @staticmethod
    def generate_encrypted_key():
        """Génère une clé chiffrée pour l'authentification"""
        from cryptography.fernet import Fernet
        
        secret_key = Fernet.generate_key()
        fernet = Fernet(secret_key)
        encrypted_message = fernet.encrypt(b"authorized")
        
        return encrypted_message.decode(), secret_key.decode()


EncryptionService = EncryptionService()