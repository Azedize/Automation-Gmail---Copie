# test_decrypt.py

import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# --- Settings ---
ENCRYPTION_KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"

AES_BLOCK_SIZE = 128  # bits
AES_KEY_LENGTH = 32   # bytes
AES_IV_LENGTH_CBC = 16  # bytes

KEY = bytes.fromhex(ENCRYPTION_KEY_HEX)

def WRITE_LOG_DEV_FILE(message, level="INFO"):
    # Simple logger pour test
    print(f"[{level}] {message}")

# --- Fonction de décryptage ---
def decrypt_message(base64_data: str, key_bytes: bytes) -> str:
    if len(key_bytes) != AES_KEY_LENGTH:
        WRITE_LOG_DEV_FILE("Invalid AES key length", level="ERROR")
        raise ValueError("Invalid AES key length")

    try:
        raw = base64.b64decode(base64_data)
        iv = raw[:AES_IV_LENGTH_CBC]
        ciphertext = raw[AES_IV_LENGTH_CBC:]

        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode("utf-8")
    except Exception as e:
        WRITE_LOG_DEV_FILE(f"AES-CBC decryption failed: {e}", level="ERROR")
        raise Exception(f"AES-CBC decryption failed: {e}")

# --- Exemple de test ---
if __name__ == "__main__":
    # Exemple de message chiffré (base64) généré avec AES-CBC et la même clé et IV
    # Pour tester, tu peux créer un message chiffré toi-même avec la même clé.
    encrypted_example = "/tqNhbwyQrTeB8Ddaz/D8TNm+askIgYcyA3ZeRG9OYY="

    try:
        decrypted = decrypt_message(encrypted_example, KEY)
        print("Message décrypté :", decrypted)
    except Exception as e:
        print("Erreur lors du décryptage :", e)