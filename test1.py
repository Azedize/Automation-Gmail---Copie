from datetime import datetime
import json
import base64
import os
import requests

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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
    if len(key_bytes) != AES_KEY_LENGTH:
        raise ValueError("Invalid AES key length")

    padder = padding.PKCS7(AES_BLOCK_SIZE).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()

    iv = os.urandom(AES_IV_LENGTH_CBC)

    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.CBC(iv),
    )

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(iv + ciphertext).decode()

# =====================================================
# 🔓 DECRYPT (DEBUG)
# =====================================================

def decrypt_message(encrypted_b64: str, key_bytes: bytes) -> str:
    raw = base64.b64decode(encrypted_b64)

    iv = raw[:AES_IV_LENGTH_CBC]
    ciphertext = raw[AES_IV_LENGTH_CBC:]

    cipher = Cipher(
        algorithms.AES(key_bytes),
        modes.CBC(iv),
    )

    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(AES_BLOCK_SIZE).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()

    return plaintext.decode()

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

    # JSON
    json_payload = json.dumps(DATA_AUTH)
    print("\n🔹 JSON original:")
    print(json_payload)

    # Encrypt
    encrypted_value = encrypt_message(json_payload, KEY)
    print("\n🔹 Donnée chiffrée:")
    print(encrypted_value)

    # DEBUG decrypt
    print("\n🔓 Décryptage test:")
    print(decrypt_message(encrypted_value, KEY))

    # Date encryption
    try:
        date_plain = datetime.now().strftime("%Y-%m-%d")
        date_encrypted = encrypt_message(date_plain, KEY)

    except Exception as e:
        print("❌ Erreur encryption date:", e)
        return

    # URL
    CHECK_URL_EX3 = (
        "https://reporting.nrb-apps.com/APP_R/redirect.php?"
        f"nv=1&rv4=1&event=check&type=V4&ext=Script&k={date_encrypted}"
    )

    print("\n🔹 URL finale:")
    print(CHECK_URL_EX3)

    # Request
    try:
        print("\n📡 Envoi requête GET...")

        response = requests.get(CHECK_URL_EX3, timeout=30)

        print("\n================ RESPONSE =================")
        print("Status Code:", response.status_code)

        print("\nResponse Text:")
        print(response.text)

        try:
            print("\nJSON:")
            print(response.json())
        except:
            print("\n⚠️ Not JSON")

    except Exception as e:
        print("❌ Erreur requête:", e)

# =====================================================
# ▶ RUN
# =====================================================

if __name__ == "__main__":
    test_api()





