import json
import base64
import os
import requests

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# =====================================================
# 🔐 CONFIGURATION
# =====================================================

ENCRYPTION_KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"

AES_BLOCK_SIZE = 128
AES_KEY_LENGTH = 32
AES_IV_LENGTH_CBC = 16

KEY = bytes.fromhex(ENCRYPTION_KEY_HEX)


# =====================================================
# 🔐 AES-CBC ENCRYPTION
# =====================================================

def encrypt_message(plaintext: str, key_bytes: bytes) -> str:
    """
    Encrypt using AES-256-CBC + PKCS7
    Return Base64(iv + ciphertext)
    """

    if len(key_bytes) != AES_KEY_LENGTH:
        raise ValueError("Invalid AES key length")

    # Padding PKCS7
    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    # Generate IV
    iv = os.urandom(AES_IV_LENGTH_CBC)

    # Create cipher
    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.CBC(iv),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Return Base64(iv + ciphertext)
    encrypted = base64.b64encode(iv + ciphertext).decode("utf-8")

    return encrypted


# =====================================================
# 🔓 AES-CBC DECRYPTION (OPTIONAL DEBUG)
# =====================================================

def decrypt_message(encrypted_b64: str, key_bytes: bytes) -> str:
    """
    Decrypt Base64(iv + ciphertext)
    """

    raw = base64.b64decode(encrypted_b64)

    iv = raw[:AES_IV_LENGTH_CBC]
    ciphertext = raw[AES_IV_LENGTH_CBC:]

    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.CBC(iv),
        backend=default_backend()
    )

    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext.decode("utf-8")


# =====================================================
# 📦 DATA AUTH
# =====================================================

DATA_AUTH = {
    "login": "rep.test",
    "password": "zsGEnntKD5q2Brp68yxT"
}


# =====================================================
# 🚀 TEST API
# =====================================================

def test_api():

    print("===================================================")
    print("🔐 AES-256 CBC API TEST")
    print("===================================================")

    # Convert to JSON
    json_payload = json.dumps(DATA_AUTH)

    print("\n🔹 JSON original:")
    print(json_payload)

    # Encrypt
    encrypted_value = encrypt_message(json_payload, KEY)

    print("\n🔹 Donnée chiffrée (Base64):")
    print(encrypted_value)

    # DEBUG: Decrypt locally
    decrypted_test = decrypt_message(encrypted_value, KEY)

    print("\n🔓 Vérification déchiffrement local:")
    print(decrypted_test)

    # Build URL
    CHECK_URL_EX3 = (
        f"https://reporting.nrb-apps.com/APP_R/redirect.php"
        f"?nv=1&rv4=1&event=check&type=V4&ext=Ext3&k={encrypted_value}"
    )

    print("\n🔹 URL finale:")
    print(CHECK_URL_EX3)

    try:
        print("\n📡 Envoi requête GET...")

        response = requests.get(CHECK_URL_EX3, timeout=30)

        print("\n================ RESPONSE =================")
        print("Status Code:", response.status_code)
        print("\nHeaders:")
        print(response.headers)

        print("\nResponse Text:")
        print(response.text)

        try:
            print("\nJSON décodé:")
            print(response.json())
        except:
            print("\n⚠️ Réponse non JSON")

    except Exception as e:
        print("❌ Erreur requête:", e)


# =====================================================
# ▶ EXECUTION
# =====================================================

if __name__ == "__main__":
    test_api()
