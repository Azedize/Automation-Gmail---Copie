import base64
import json
import requests

from datetime import datetime

# 🔐 نفس المفتاح (HEX)
KEY_HEX = "f564292a5740af4fc4819c6e22f64765232ad35f56079854a0ad3996c68ee7a2"
KEY = bytes.fromhex(KEY_HEX)

API_URL = "http://localhost/auth-api/get_scenarios.php"  # عدّل الرابط



# 📌 بيانات الاختبار
username = "admin"
password = "123456"
date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

payload_text = f"{username}::{password}::{date_str}"

print("📤 Plain text :", payload_text)



# 📦 JSON المرسل
payload = {
    "encrypted": "XREPqNslf8ScKTpJ3pWth4HFu2jHZNiVRmFlTQN9uaixKRdqbp2sbGbEGjmIng8AtUndMS0Ir6U/uRZ7+C0xxt8o8txnimyQUstkWVmBupk="
}

response = requests.post(API_URL, json=payload, timeout=10)

print("📥 Status Code:", response.status_code)
print("📥 Response JSON:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
