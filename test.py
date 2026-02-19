# ==========================================
# test_api_debug_apiaccess.py
# ==========================================

import requests
import socket
import json
import traceback
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===========================
# 🔹 Configuration
# ===========================
API_ENDPOINTS = {
    "_APIACCESS_API": "https://reporting.nrb-apps.com/pub/chk_usr1.php?rv4=1"
}

# le programme is runi

USERNAME = "rep.test"
PASSWORD = "zsGEnntKD5q2Brp68yxT"

PAYLOAD = {
    "rID": "1",
    "u": USERNAME,
    "p": PASSWORD,
    "k": "mP5QXYrK9E67Y",
    "l": "1"
}

TIMEOUT = 10
MAX_ATTEMPTS = 3

# ===========================
# 🔹 Helper: Debug Separator
# ===========================
def print_sep(title="DEBUG"):
    print("\n" + "="*10 + f" {title} " + "="*10 + "\n")

# ===========================
# 🔹 DNS & Local IP Check
# ===========================
try:
    url = API_ENDPOINTS["_APIACCESS_API"]
    domain = url.split("//")[1].split("/")[0]
    domain_ip = socket.gethostbyname(domain)
    print_sep("DNS Check")
    print(f"[INFO] Domain: {domain}")
    print(f"[INFO] Resolved IP: {domain_ip}")
except Exception as e:
    print_sep("DNS ERROR")
    print(f"[ERROR] DNS resolution failed: {e}")

try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print_sep("Local IP")
    print(f"[INFO] Hostname: {hostname}")
    print(f"[INFO] Local IP: {local_ip}")
except Exception as e:
    print(f"[WARN] Could not get local IP: {e}")

# ===========================
# 🔹 Attempt Requests
# ===========================
session = requests.Session()
session.verify = False  # تجاهل SSL warnings
session.headers.update({
    "User-Agent": "Python-Test-API/1.0"
})

for attempt in range(1, MAX_ATTEMPTS + 1):
    print_sep(f"Attempt {attempt}/{MAX_ATTEMPTS}")
    try:
        print(f"[DEBUG] Sending POST request to {url}")
        print(f"[DEBUG] Payload: {PAYLOAD}")

        response = session.post(url, data=PAYLOAD, timeout=TIMEOUT)
        # عرض response object
        print(f"[DEBUG] Response :\n{response}")

        # عرض النص كامل (أو أول 500 حرف)
        print(f"[DEBUG] Response Text (first 500 chars):\n{response.text[:500]}")

        # محاولة تحويل JSON وعرضه كامل إذا كان dict
        try:
            response_json = response.json()
            print("[DEBUG] Response JSON complet :")
            print(json.dumps(response_json, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"[WARN] Réponse n'est pas JSON ou parsing échoué : {e}")
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Headers: {dict(response.headers)}")
        print(f"[DEBUG] Response Text (first 500 chars):\n{response.text}")

        # Try parse JSON
        try:
            data = response.json()
            print(f"[DEBUG] JSON Parsed Response:\n{json.dumps(data, indent=4)}")
        except json.JSONDecodeError:
            print("[WARN] Response is not JSON")

        if response.status_code == 200:
            print("[SUCCESS] Request successful")
            break

    except requests.exceptions.SSLError as ssl_err:
        print(f"[ERROR] SSL Error: {ssl_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"[ERROR] Connection Error: {conn_err}")
    except requests.exceptions.Timeout:
        print("[ERROR] Request Timeout")
    except Exception as e:
        print(f"[CRITICAL] Unexpected Exception: {e}")
        traceback.print_exc()

    if attempt < MAX_ATTEMPTS:
        print(f"[INFO] Retrying in 2 seconds...\n")
        time.sleep(2)
    else:
        print("[ERROR] All attempts failed.")




