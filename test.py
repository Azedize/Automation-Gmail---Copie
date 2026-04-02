import requests
import json
import time
import traceback

def send_status_debug():
    url = "http://reporting.nrb-apps.com:8585/rep/pub/email_status.php"

    params = {
        "k": "mP5Q2XYrK9E67Y1",
        "rID": "1",
        "rv4": "1"
    }

    data = {
        "id": "877499259",
        "login": "rep.test",
        "status": "❌ NotOK",
        "error": "password_changed"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    start_time = time.time()

    try:
        print("\n" + "="*70)
        print("🚀 START DEBUG API REQUEST")
        print("="*70)

        prepared_url = requests.Request('POST', url, params=params).prepare().url
        print(f"\n🔗 URL: {prepared_url}")
        print(f"📡 Method: POST")

        print("\n📤 URL Params:")
        print(json.dumps(params, indent=4))

        print("\n📤 Body Data:")
        print(json.dumps(data, indent=4, ensure_ascii=False))

        print("\n📝 Headers:")
        print(json.dumps(headers, indent=4))

        print("\n🌐 Sending request...")
        response = requests.post(url, params=params, data=data, headers=headers, timeout=30)

        elapsed = time.time() - start_time

        print("\n" + "-"*70)
        print("📥 RESPONSE")
        print("-"*70)

        print(f"✅ Status Code: {response.status_code}")
        print("\n📄 Response Headers:")
        for k, v in response.headers.items():
            print(f"   {k}: {v}")

        print("\n📄 Raw Response Text (first 1000 chars):")
        print(response.text[:1000])

        text = response.text.strip()

        # تحليل JSON
        print("\n🔍 Attempt JSON Decode:")
        try:
            json_resp = response.json()
            print("✅ JSON Decode Success:")
            print(json.dumps(json_resp, indent=4))
        except Exception as e:
            print("❌ Not JSON:", str(e))

        # محاولة تحليل PHP serialized
        if text.startswith("a:"):
            try:
                import phpserialize
                parsed = phpserialize.loads(text.encode())
                print("\n⚠️ PHP Serialized Detected and Parsed:")
                print(parsed)
            except Exception as e:
                print("\n❌ Failed to parse PHP serialized:", str(e))

        # ======================================
        # 🔹 Logic: success par défaut
        # ======================================
        if "error" in text.lower():
            print("\n❌ ERROR detected in response")
            result = 0
        else:
            print("\n✅ No error detected → consider SUCCESS")
            result = 1

        print(f"\n⏱️ Execution time: {elapsed:.3f}s")
        print("\n✅ END DEBUG")
        print("="*70 + "\n")

        return result

    except Exception as e:
        print("\n" + "="*70)
        print("💥 EXCEPTION OCCURRED")
        print("="*70)
        print(f"Exception: {e}")
        print(traceback.format_exc())
        elapsed = time.time() - start_time
        print(f"\n⏱️ Time before crash: {elapsed:.3f}s")
        print("="*70 + "\n")
        return 0


if __name__ == "__main__":
    final_result = send_status_debug()
    print(f"\n🎯 Final Result: {final_result}")