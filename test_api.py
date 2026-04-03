#!/usr/bin/env python3
"""
Script de test pour l'API handle_save_scenario
Teste l'endpoint de sauvegarde de scénario
"""

import requests
import json
import urllib3

# Désactiver les avertissements SSL (comme dans votre code)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_save_scenario_api():
    """
    Test de l'API de sauvegarde de scénario
    """

    # 🔗 URL de l'API (avec le paramètre l dans l'URL)
    api_url = "https://reporting.nrb-apps.com/pub/ReportingV4/senario.php?rv4=1&entity=IT&action=add&l=WsWSwmgXwQfGTY89CZQAN1EL5TcHjkxrkiWCkCpbHK1bA8C+ngdEmkCRx0T0FpmieI+CKkgP6hmF3cvE2Ul5+g=="

    # 📦 Payload (form-data)
    payload = {
        "user_id": "3895",
        "encrypted": "WsWSwmgXwQfGTY89CZQAN1EL5TcHjkxrkiWCkCpbHK1bA8C+ngdEmkCRx0T0FpmieI+CKkgP6hmF3cvE2Ul5+g==",
        "name": "eeeeeeeeeee", # name unique pour chaque scénario
        "state": json.dumps({
            "id": "mark_as_important",
            "label": "Mark As Important",
            "actions": ["spamSelectMarkAsRead", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
            "Template": "Template2"
        }),
        "state_stack": json.dumps([
            {
                "id": "open_spam",
                "label": "Open Spam",
                "showOnInit": True,
                "actions": ["spamOpenMessage", "spamSelectAll"],
                "Template": "Template1"
            },
            {
                "id": "select_all",
                "label": "Select All",
                "actions": ["spamSelectMarkAsRead", "spamSelectMarkAsImportant", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
                "Template": "Template2"
            },
            {
                "id": "mark_as_important",
                "label": "Mark As Important",
                "actions": ["spamSelectMarkAsRead", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
                "Template": "Template2"
            }
        ])
    }

    # 📝 Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("🚀 [TEST] Démarrage du test API handle_save_scenario")
    print(f"🔗 [TEST] URL: {api_url}")
    print(f"📋 [TEST] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print(f"📝 [TEST] Headers: {headers}")

    try:
        # 📡 Envoi de la requête
        print("\n📡 [TEST] Envoi de la requête POST...")
        response = requests.post(
            api_url,
            data=payload,
            headers=headers,
            verify=False,  # SSL désactivé
            timeout=30
        )
        
        print(json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text
        }, indent=2, ensure_ascii=False))

        print(f"➡️ [TEST] Status Code: {response.status_code}")
        print(f"📄 [TEST] Headers Response: {dict(response.headers)}")
        print(f"📄 [TEST] Response Text: {response.text}")

        # 🔍 Tentative de parsing JSON
        try:
            json_response = response.json()
            print(f"✅ [TEST] JSON Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("⚠️ [TEST] Réponse non-JSON")

        # 📊 Analyse du résultat
        if response.status_code == 200:
            print("✅ [TEST] Requête réussie (HTTP 200)")
            if 'status' in response.text.lower():
                if '"status":true' in response.text or '"status":"true"' in response.text:
                    print("🎉 [TEST] Scénario sauvegardé avec succès !")
                elif '"status":false' in response.text or '"status":"false"' in response.text:
                    print("❌ [TEST] Échec de la sauvegarde du scénario")
                else:
                    print("🤔 [TEST] Statut inconnu dans la réponse")
        else:
            print(f"❌ [TEST] Erreur HTTP: {response.status_code}")

    except requests.RequestException as e:
        print(f"🔥 [TEST] Exception lors de la requête: {e}")
    except Exception as e:
        print(f"💥 [TEST] Exception générale: {e}")

    print("\n🏁 [TEST] Fin du test API")

if __name__ == "__main__":
    test_save_scenario_api()