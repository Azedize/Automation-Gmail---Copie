import os
import base64
import hashlib
import sys
import traceback
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
import sys








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
    def decrypt_message(base64_data: str, key) -> str:
        """
        🔓 AES-CBC decrypt (PKCS7) unified
        - base64_data: النص المشفر Base64
        - key: str أو bytes
        """
        
        if isinstance(key, str):
            key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
        elif isinstance(key, bytes):
            key_bytes = key
        else:
            msg = f"❌ ERREUR DÉCRYPTAGE: La clé doit être str ou bytes. Type reçu: {type(key)}\nTraceback complet: {traceback.format_exc()}"
            settings.WRITE_LOG_DEV_FILE(msg, level="ERROR")
            # print(msg)
            settings.WRITE_LOG_DEV_FILE(msg, level="ERROR")
            sys.exit(1)

        if len(key_bytes) != settings.AES_KEY_LENGTH:
            msg = f"❌ ERREUR DÉCRYPTAGE: Longueur de clé AES invalide. Attendu: {settings.AES_KEY_LENGTH}, Reçu: {len(key_bytes)}\nTraceback complet: {traceback.format_exc()}"
            settings.WRITE_LOG_DEV_FILE(msg, level="ERROR")
            # print(msg)
            settings.WRITE_LOG_DEV_FILE(msg, level="ERROR")
            sys.exit(1)

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
            error_msg = f"❌ ERREUR DÉCRYPTAGE AES-CBC: {str(e)}\nDonnées: {base64_data[:50]}...\nTraceback complet:\n{traceback.format_exc()}"
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            sys.exit(1)






    # =========================
    # 🔑 Key derivation (PBKDF2)
    # =========================
    @staticmethod
    def Derive_Key(password: str, salt: bytes) -> bytes:
        if len(salt) != settings.AES_SALT_LENGTH:
            error_msg = f"❌ ERREUR DÉRIVATION CLÉ: Longueur de salt invalide. Attendu: {settings.AES_SALT_LENGTH}, Reçu: {len(salt)}\nTraceback complet: {traceback.format_exc()}"
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            sys.exit(1)
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS
            )
            return kdf.derive(password.encode("utf-8"))
        except Exception as e:
            error_msg = f"❌ ERREUR DÉRIVATION CLÉ PBKDF2: {str(e)}\nMot de passe length: {len(password)}\nTraceback complet:\n{traceback.format_exc()}"
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            sys.exit(1)




    # =========================
    # 🔒 AES-CBC Encrypt
    # =========================
    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        if len(key_bytes) != settings.AES_KEY_LENGTH:
            # settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(f"❌ ERREUR CHIFFRAGE: Longueur de clé AES invalide. Attendu: {settings.AES_KEY_LENGTH}, Reçu: {len(key_bytes)}\nTraceback complet: {traceback.format_exc()}", level="ERROR")
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
            settings.WRITE_LOG_DEV_FILE(f"❌ ERREUR CHIFFRAGE AES-CBC: {str(e)}\nTexte plaintext length: {len(plaintext)}\nTraceback complet:\n{traceback.format_exc()}", level="ERROR")
            # print(error_msg)
            # settings.WRITE_LOG_DEV_FILE(error_msg, level="ERROR")
            sys.exit(1)






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
        except SystemExit:
            raise
        except Exception as e:
            
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(f"❌ ERREUR CHIFFRAGE AES-GCM: {str(e)}\nMot de passe length: {len(password)}, Plaintext length: {len(plaintext)}\nTraceback complet:\n{traceback.format_exc()}", level="ERROR")
            sys.exit(1)




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
            settings.WRITE_LOG_DEV_FILE( f"❌ ERREUR VÉRIFICATION CLÉ FERNET: {str(e)}\nEncrypted key length: {len(encrypted_key)}, Secret key length: {len(secret_key)}\nTraceback complet:\n{traceback.format_exc()}", level="ERROR")
            # print(error_msg)
            sys.exit(1)




    # =========================
    # 🔑 Generate Fernet Encrypted Key
    # =========================
    @staticmethod
    def generate_encrypted_key():
        try:
            secret_key = Fernet.generate_key()
            fernet = Fernet(secret_key)
            encrypted_message = fernet.encrypt(b"authorized")
            return encrypted_message.decode(), secret_key.decode()
        except Exception as e:
            # print(error_msg)
            settings.WRITE_LOG_DEV_FILE(f"❌ ERREUR GÉNÉRATION CLÉ FERNET: {str(e)}\nTraceback complet:\n{traceback.format_exc()}", level="ERROR")
            sys.exit(1)



# =========================
# 🔹 Instance
# =========================
EncryptionService = EncryptionService()



