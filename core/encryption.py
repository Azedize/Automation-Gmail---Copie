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
    # Importe la configuration centralisée utilisée par le service de chiffrement
    from config.settings import settings
except ImportError as e:
    # Affiche l'erreur d'importation avant d'arrêter l'application
    print(f"Failed to import settings from {__file__}: {e}")
    sys.exit(1)


class EncryptionService:

    @staticmethod
    def decryptMessage(base64_data: str, key) -> str:
        # Conserve la compatibilité avec l'ancien nom de méthode en redirigeant
        # l'appel vers l'implémentation principale en snake_case
        return EncryptionService.decrypt_message(base64_data, key)

    @staticmethod
    def decrypt_message(base64_data: str, key) -> str:
        # Convertit la clé en bytes lorsqu'elle est fournie sous forme de chaîne
        # SHA-256 produit une clé de 32 octets adaptée à AES-256
        if isinstance(key, str):
            key_bytes = hashlib.sha256(key.encode("utf-8")).digest()

        # Utilise directement la clé lorsqu'elle est déjà fournie sous forme de bytes
        elif isinstance(key, bytes):
            key_bytes = key

        else:
            # Enregistre uniquement le type de clé afin de ne jamais exposer sa valeur
            settings.write_log_event(
                "decryption_key_invalid",
                "ERROR",
                key_type=type(key).__name__,
            )
            sys.exit(1)

        # Vérifie que la clé possède exactement la longueur attendue par AES
        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.write_log_event(
                "decryption_key_invalid",
                "ERROR",
                expected_length=settings.AES_KEY_LENGTH,
                received_length=len(key_bytes),
            )
            sys.exit(1)

        try:
            # Vérifie que le payload chiffré est une chaîne Base64 non vide
            if not isinstance(base64_data, str) or not base64_data.strip():
                raise ValueError(
                    "Encrypted data must be a non-empty Base64 string."
                )

            try:
                # Décode le contenu Base64 afin de récupérer les données binaires
                raw = base64.b64decode(base64_data)

            except Exception as e:
                # Transforme l'erreur de décodage en erreur de validation explicite
                raise ValueError(
                    f"Unable to decode Base64 data: {e}"
                ) from e

            # Vérifie que le payload contient au minimum l'IV attendu
            if len(raw) < settings.AES_IV_LENGTH_CBC:
                raise ValueError(
                    "Invalid encrypted payload length. "
                    f"Expected at least {settings.AES_IV_LENGTH_CBC} bytes "
                    f"for the IV, received {len(raw)}."
                )

            # Extrait l'IV placé au début du payload
            iv = raw[:settings.AES_IV_LENGTH_CBC]

            # Extrait le ciphertext situé après l'IV
            ciphertext = raw[settings.AES_IV_LENGTH_CBC:]

            # Vérifie une nouvelle fois que la taille de l'IV est correcte
            if len(iv) != settings.AES_IV_LENGTH_CBC:
                raise ValueError(
                    f"Invalid IV size ({len(iv)}) for CBC. "
                    f"Expected {settings.AES_IV_LENGTH_CBC}."
                )

            # Vérifie qu'un ciphertext est bien présent après l'IV
            if len(ciphertext) == 0:
                raise ValueError(
                    "Ciphertext is empty after extracting the IV."
                )

            # Initialise AES avec le mode CBC et l'IV extrait du payload
            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv),
                backend=default_backend(),
            )

            # Crée le déchiffreur AES-CBC
            decryptor = cipher.decryptor()

            # Déchiffre le ciphertext et récupère les données encore paddées
            padded_plaintext = (
                decryptor.update(ciphertext)
                + decryptor.finalize()
            )

            # Prépare le décompresseur PKCS7 utilisé lors du chiffrement
            unpadder = padding.PKCS7(
                settings.AES_BLOCK_SIZE
            ).unpadder()

            # Supprime le padding ajouté avant le chiffrement
            plaintext_bytes = (
                unpadder.update(padded_plaintext)
                + unpadder.finalize()
            )

            # Convertit les données déchiffrées UTF-8 en chaîne de caractères
            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            # Enregistre uniquement les informations nécessaires au diagnostic
            # sans enregistrer la clé ou le contenu déchiffré
            settings.write_log_event(
                "aes_cbc_decryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                payload_length=(
                    len(base64_data)
                    if isinstance(base64_data, str)
                    else 0
                ),
            )
            sys.exit(1)

    @staticmethod
    def deriveKey(password: str, salt: bytes) -> bytes:
        # Conserve la compatibilité avec l'ancien nom de méthode
        return EncryptionService.derive_key(password, salt)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        # Vérifie que le salt possède la longueur attendue
        if len(salt) != settings.AES_SALT_LENGTH:
            settings.write_log_event(
                "pbkdf2_key_derivation_failed",
                "ERROR",
                expected_salt_length=settings.AES_SALT_LENGTH,
                received_salt_length=len(salt),
            )
            sys.exit(1)

        try:
            # Configure PBKDF2 avec SHA-256 pour dériver une clé AES
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=settings.AES_KEY_LENGTH,
                salt=salt,
                iterations=settings.PBKDF2_ITERATIONS,
            )

            # Transforme le mot de passe en bytes puis dérive la clé finale
            return kdf.derive(password.encode("utf-8"))

        except Exception as e:
            # Enregistre le type d'erreur et la longueur du mot de passe
            # sans enregistrer le mot de passe lui-même
            settings.write_log_event(
                "pbkdf2_key_derivation_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                password_length=len(password),
            )
            sys.exit(1)

    @staticmethod
    def encryptMessage(plaintext: str, key_bytes: bytes) -> str:
        # Conserve la compatibilité avec l'ancien nom de méthode
        return EncryptionService.encrypt_message(plaintext, key_bytes)

    @staticmethod
    def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
        # Vérifie que la clé possède la longueur attendue par AES
        if len(key_bytes) != settings.AES_KEY_LENGTH:
            settings.write_log_event(
                "aes_cbc_encryption_failed",
                "ERROR",
                expected_length=settings.AES_KEY_LENGTH,
                received_length=len(key_bytes),
            )
            sys.exit(1)

        try:
            # Prépare le padding PKCS7 nécessaire au fonctionnement d'AES-CBC
            padder = padding.PKCS7(
                settings.AES_BLOCK_SIZE
            ).padder()

            # Convertit le texte en UTF-8 puis ajoute le padding
            padded = (
                padder.update(plaintext.encode("utf-8"))
                + padder.finalize()
            )

            # Génère un IV aléatoire pour cette opération de chiffrement
            iv = os.urandom(settings.AES_IV_LENGTH_CBC)

            # Initialise AES avec le mode CBC et l'IV généré
            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.CBC(iv),
            )

            # Crée l'objet responsable du chiffrement
            encryptor = cipher.encryptor()

            # Chiffre les données paddées
            ciphertext = (
                encryptor.update(padded)
                + encryptor.finalize()
            )

            # Concatène l'IV et le ciphertext puis encode le résultat en Base64
            return base64.b64encode(
                iv + ciphertext
            ).decode("utf-8")

        except Exception as e:
            # Enregistre les informations de diagnostic sans exposer le plaintext
            settings.write_log_event(
                "aes_cbc_encryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                plaintext_length=len(plaintext),
            )
            sys.exit(1)

    @staticmethod
    def encryptAesGcm(password: str, plaintext: str) -> str:
        # Conserve la compatibilité avec l'ancien nom de méthode
        return EncryptionService.encrypt_aes_gcm(password, plaintext)

    @staticmethod
    def encrypt_aes_gcm(password: str, plaintext: str) -> str:
        try:
            # Génère un salt aléatoire utilisé pour dériver la clé AES
            salt = os.urandom(settings.AES_SALT_LENGTH)

            # Dérive une clé AES à partir du mot de passe et du salt
            key = EncryptionService.derive_key(password, salt)

            # Génère un IV aléatoire spécifique à AES-GCM
            iv = os.urandom(settings.AES_IV_LENGTH_GCM)

            # Initialise AES-GCM avec la clé dérivée
            aesgcm = AESGCM(key)

            # Chiffre le plaintext et génère automatiquement le tag
            # d'authentification utilisé pour vérifier l'intégrité des données
            ciphertext_and_tag = aesgcm.encrypt(
                iv,
                plaintext.encode("utf-8"),
                None,
            )

            # Construit le payload final : salt + IV + ciphertext + tag
            payload = salt + iv + ciphertext_and_tag

            # Convertit le payload binaire en chaîne hexadécimale
            return payload.hex()

        except SystemExit:
            # Laisse passer les SystemExit générés par les fonctions internes
            raise

        except Exception as e:
            # Enregistre uniquement les informations nécessaires au diagnostic
            # sans exposer le mot de passe ou le contenu original
            settings.write_log_event(
                "aes_gcm_encryption_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                password_length=len(password),
                plaintext_length=len(plaintext),
            )
            sys.exit(1)

    @staticmethod
    def verifyKey(encrypted_key: str, secret_key: str) -> bool:
        # Conserve la compatibilité avec l'ancien nom de méthode
        return EncryptionService.verify_key(encrypted_key, secret_key)

    @staticmethod
    def verify_key(encrypted_key: str, secret_key: str) -> bool:
        try:
            # Crée une instance Fernet à partir de la clé secrète
            fernet = Fernet(secret_key.encode())

            # Déchiffre le message reçu avec la clé secrète
            decrypted = fernet.decrypt(encrypted_key.encode())

            # Vérifie que le contenu déchiffré correspond exactement
            # à la valeur attendue pour autoriser la clé
            return decrypted == b"authorized"

        except Exception as e:
            # Enregistre uniquement les longueurs et le type d'erreur
            # afin de ne pas exposer les clés dans les logs
            settings.write_log_event(
                "fernet_key_verification_failed",
                "ERROR",
                exception_type=type(e).__name__,
                error=str(e),
                encrypted_key_length=len(encrypted_key),
                secret_key_length=len(secret_key),
            )
            sys.exit(1)

    @staticmethod
    def generateEncryptedKey():
        # Conserve la compatibilité avec l'ancien nom de méthode
        return EncryptionService.generate_encrypted_key()

    @staticmethod
    def generate_encrypted_key():
        try:
            # Génère une nouvelle clé secrète Fernet aléatoire
            secret_key = Fernet.generate_key()

            # Crée l'objet Fernet qui utilisera cette clé
            fernet = Fernet(secret_key)

            # Chiffre la valeur de validation utilisée pour vérifier la clé
            encrypted_message = fernet.encrypt(b"authorized")

            # Retourne le message chiffré et la clé sous forme de chaînes
            return encrypted_message.decode(), secret_key.decode()

        except Exception as e:
            # Enregistre uniquement les informations techniques de l'erreur
            # sans exposer la clé secrète ou le message chiffré
            settings.write_log_event(  "fernet_key_generation_failed", "ERROR",  exception_type=type(e).__name__, error=str(e))
            sys.exit(1)


# Instancie le service afin de conserver l'utilisation actuelle
# du module sous la forme EncryptionService.method(...)
EncryptionService = EncryptionService()